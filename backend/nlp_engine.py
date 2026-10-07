import json
import random
import nltk
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

# ---------------------------------------------------------------
# NLTK resource downloader (handles punkt_tab for NLTK 3.8.2+)
# ---------------------------------------------------------------
REQUIRED_NLTK_DATA = [
    ('tokenizers/punkt', 'punkt'),
    ('tokenizers/punkt_tab', 'punkt_tab'),
    ('corpora/wordnet', 'wordnet'),
    ('corpora/omw-1.4', 'omw-1.4'),
]

for path, pkg in REQUIRED_NLTK_DATA:
    try:
        nltk.data.find(path)
    except LookupError:
        print(f"[NLTK] Downloading {pkg}...")
        nltk.download(pkg, quiet=True)

lemmatizer = WordNetLemmatizer()


# ---------------------------------------------------------------
# Simple synonym normalizer to boost matching
# ---------------------------------------------------------------
SYNONYMS = {
    'fee': ['fees', 'charge', 'charges', 'cost', 'price', 'payment', 'tuition'],
    'admission': ['admissions', 'enroll', 'enrollment', 'enrol', 'apply', 'application'],
    'course': ['courses', 'program', 'programs', 'branch', 'branches', 'stream'],
    'placement': ['placements', 'job', 'jobs', 'recruit', 'recruitment', 'hiring'],
    'hostel': ['accommodation', 'boarding', 'dorm', 'dormitory'],
    'college': ['institute', 'university', 'campus', 'sanjivani'],
    'contact': ['phone', 'number', 'email', 'mail', 'reach', 'call'],
    'location': ['address', 'located', 'where', 'place'],
    'scholarship': ['scholarships', 'financial', 'aid', 'waiver'],
    'exam': ['exams', 'examination', 'test', 'tests'],
}


class NLPEngine:
    def __init__(self, intents_path, kb_path):
        with open(intents_path, 'r', encoding='utf-8') as f:
            self.intents = json.load(f)['intents']
        with open(kb_path, 'r', encoding='utf-8') as f:
            self.kb = json.load(f)

        self.patterns = []
        self.tags = []
        self.responses = {}

        for intent in self.intents:
            for pattern in intent['patterns']:
                self.patterns.append(self._preprocess(pattern))
                self.tags.append(intent['tag'])
            self.responses[intent['tag']] = intent['responses']

        # Add extra synonym variants for each pattern
        extra_patterns, extra_tags = [], []
        for i, pattern in enumerate(self.patterns):
            tag = self.tags[i]
            for word, syns in SYNONYMS.items():
                if word in pattern:
                    for syn in syns:
                        variant = pattern.replace(word, syn)
                        extra_patterns.append(variant)
                        extra_tags.append(tag)
        self.patterns.extend(extra_patterns)
        self.tags.extend(extra_tags)

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2))
        self.tfidf_matrix = self.vectorizer.fit_transform(self.patterns)

        print(f"[NLP] Loaded {len(set(self.tags))} intents, {len(self.patterns)} patterns.")

    # ---------------------------------------------------------
    def _preprocess(self, text):
        tokens = nltk.word_tokenize(text.lower())
        cleaned = [lemmatizer.lemmatize(t) for t in tokens if t.isalnum()]
        return ' '.join(cleaned)

    # ---------------------------------------------------------
    def _resolve_kb_path(self, path_str):
        """Resolve __KB__a.b.c into the nested KB value."""
        parts = path_str.split('.')
        node = self.kb
        for p in parts:
            if isinstance(node, dict) and p in node:
                node = node[p]
            else:
                return None
        return node

    # ---------------------------------------------------------
    def _resolve_response(self, intent_tag):
        responses = self.responses.get(intent_tag, [])
        if not responses:
            return "Sorry, I couldn't find information on that."

        chosen = random.choice(responses)

        if chosen.startswith("__KB__"):
            kb_path = chosen.replace("__KB__", "")
            data = self._resolve_kb_path(kb_path)
            if data is None:
                return "I don't have that information right now."
            if isinstance(data, dict):
                # Join all sub-fields
                parts = [str(v) for v in data.values()]
                return " ".join(parts)
            return str(data)
        return chosen

    # ---------------------------------------------------------
    def get_response(self, user_input, threshold=0.20):
        if not user_input or not user_input.strip():
            return {
                "response": "Please type a question. 😊",
                "intent": "unknown",
                "confidence": 0.0
            }

        processed = self._preprocess(user_input)
        user_vec = self.vectorizer.transform([processed])
        similarities = cosine_similarity(user_vec, self.tfidf_matrix).flatten()

        best_idx = int(np.argmax(similarities))
        confidence = float(similarities[best_idx])

        # Fallback if too weak
        if confidence < threshold:
            return {
                "response": (
                    "Hmm, I'm not sure about that. 🤔<br><br>"
                    "Try asking about:<br>"
                    "• <b>Courses</b> - B.Tech / M.Tech programs<br>"
                    "• <b>Admissions</b> - Process, eligibility<br>"
                    "• <b>Fees</b> - Tuition, hostel<br>"
                    "• <b>Placements</b> - Companies, packages<br>"
                    "• <b>Scholarships</b> - Government aid<br>"
                    "• <b>Contact</b> - Phone, email, address<br>"
                    "• <b>Hostel</b>, <b>Library</b>, <b>Events</b> and more"
                ),
                "intent": "fallback",
                "confidence": confidence
            }

        intent_tag = self.tags[best_idx]
        return {
            "response": self._resolve_response(intent_tag),
            "intent": intent_tag,
            "confidence": round(confidence, 3)
        }