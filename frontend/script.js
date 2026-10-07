// ==========================================================
// College Enquiry Chatbot - Frontend
// ==========================================================

console.log("[Chatbot] script.js loaded");

const API_URL = '/api/chat';

const chatBox   = document.getElementById('chatBox');
const chatForm  = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendBtn   = document.getElementById('sendBtn');
const clearBtn  = document.getElementById('clearBtn');

// -------- Auto-scroll helper --------
function scrollToBottom(smooth = true) {
  requestAnimationFrame(() => {
    chatBox.scrollTo({
      top: chatBox.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    });
  });
}

// -------- Timestamp --------
function now() {
  return new Date().toLocaleTimeString('en-IN', {
    hour: '2-digit', minute: '2-digit'
  });
}

// -------- Add message bubble --------
function addMessage(text, sender) {
  const msg = document.createElement('div');
  msg.className = 'message ' + sender;

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.innerHTML = text;

  const time = document.createElement('div');
  time.className = 'time';
  time.textContent = now();

  msg.appendChild(bubble);
  msg.appendChild(time);
  chatBox.appendChild(msg);

  scrollToBottom();
  return msg;
}

// -------- Typing indicator --------
function showTyping() {
  const msg = document.createElement('div');
  msg.className = 'message bot';
  msg.id = 'typingIndicator';
  msg.innerHTML =
    '<div class="bubble typing"><span></span><span></span><span></span></div>';
  chatBox.appendChild(msg);
  scrollToBottom();
}

function hideTyping() {
  const t = document.getElementById('typingIndicator');
  if (t) t.remove();
}

// -------- Send --------
async function sendMessage(text) {
  text = (text || '').trim();
  if (!text) return;

  addMessage(text, 'user');
  userInput.value = '';
  userInput.focus();
  sendBtn.disabled = true;
  showTyping();

  try {
    const res = await fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });

    if (!res.ok) throw new Error('HTTP ' + res.status);

    const data = await res.json();
    hideTyping();
    addMessage(data.response || "No response.", 'bot');
    console.log(`[Bot] intent=${data.intent} conf=${data.confidence}`);

  } catch (err) {
    console.error('[Chatbot] Error:', err);
    hideTyping();
    addMessage(
      '⚠️ Cannot reach the server.<br>Make sure <code>python app.py</code> is running.',
      'bot'
    );
  } finally {
    sendBtn.disabled = false;
    userInput.focus();
  }
}

// -------- Events --------
chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  sendMessage(userInput.value);
});

document.querySelectorAll('.qa-btn').forEach((btn) => {
  btn.addEventListener('click', () => {
    const q = btn.dataset.q;
    if (q) sendMessage(q);
  });
});

clearBtn.addEventListener('click', () => {
  chatBox.innerHTML = '';
  addMessage(
    'Hello! 👋 I\'m the Sanjivani College Enquiry Assistant.<br>' +
    'Ask me about <b>admissions, courses, fees, placements, scholarships, hostel, events</b> and more!',
    'bot'
  );
});

// Auto-focus + first scroll
window.addEventListener('load', () => {
  userInput.focus();
  scrollToBottom(false);
});