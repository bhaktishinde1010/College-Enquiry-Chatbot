from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from nlp_engine import NLPEngine

# ---------- Paths ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(ROOT_DIR, 'frontend')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

print(f"[Paths] ROOT     = {ROOT_DIR}")
print(f"[Paths] FRONTEND = {FRONTEND_DIR}")
print(f"[Paths] script.js exists? = {os.path.exists(os.path.join(FRONTEND_DIR, 'script.js'))}")

# ---------- App ----------
app = Flask(__name__, static_folder=None)
CORS(app)

# ---------- NLP engine ----------
engine = NLPEngine(
    intents_path=os.path.join(DATA_DIR, 'intents.json'),
    kb_path=os.path.join(DATA_DIR, 'knowledge_base.json')
)

# ---------- Static routes ----------
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# ---------- API ----------
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '')
    result = engine.get_response(message)
    return jsonify(result)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)