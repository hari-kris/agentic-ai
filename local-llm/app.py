import streamlit as st
import requests
import json
import time

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Ollama Chat",
    page_icon="🦙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;800&display=swap');

/* Root variables */
:root {
    --bg:        #0d0f14;
    --surface:   #151820;
    --border:    #252a35;
    --accent:    #7c6af7;
    --accent2:   #3ecfcf;
    --text:      #e2e8f0;
    --muted:     #6b7280;
    --user-bg:   #1a1f2e;
    --bot-bg:    #111420;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: 'Syne', sans-serif;
    color: var(--text);
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.4rem;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1.5rem;
}

/* Selectbox, sliders */
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label,
[data-testid="stTextArea"] label {
    color: var(--muted) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* Chat messages container */
.chat-container {
    max-width: 820px;
    margin: 0 auto;
    padding: 1rem 0 6rem;
}

/* Individual message bubbles */
.msg {
    display: flex;
    gap: 0.75rem;
    margin-bottom: 1.25rem;
    animation: fadeUp 0.3s ease;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

.msg-avatar {
    width: 34px;
    height: 34px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
    margin-top: 2px;
}
.msg-avatar.user { background: linear-gradient(135deg, #4f46e5, var(--accent)); }
.msg-avatar.bot  { background: linear-gradient(135deg, #0f766e, var(--accent2)); }

.msg-body {
    flex: 1;
    background: var(--user-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    line-height: 1.65;
    font-size: 0.95rem;
}
.msg-body.bot { background: var(--bot-bg); }

.msg-body pre {
    background: #0a0c12;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    overflow-x: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    margin: 0.5rem 0;
}

.msg-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.68rem;
    color: var(--muted);
    margin-top: 0.4rem;
}

/* Title bar */
.title-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1.25rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.title-bar h1 {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.6rem;
    margin: 0;
    background: linear-gradient(135deg, var(--accent), var(--accent2));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--accent2);
    box-shadow: 0 0 6px var(--accent2);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* Thinking indicator */
.thinking {
    display: flex; align-items: center; gap: 0.5rem;
    color: var(--muted);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    padding: 0.5rem 0;
}
.dot { animation: blink 1.2s infinite; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes blink { 0%,80%,100%{opacity:0;} 40%{opacity:1;} }

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }

/* Button override */
[data-testid="stButton"] button {
    background: linear-gradient(135deg, var(--accent), #5b52d1) !important;
    border: none !important;
    color: white !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.4rem 1.2rem !important;
    transition: opacity 0.2s !important;
}
[data-testid="stButton"] button:hover { opacity: 0.85 !important; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
OLLAMA_BASE = "http://localhost:11434"

def get_models():
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=4)
        r.raise_for_status()
        return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        return []

def stream_chat(model, messages, temperature, max_tokens):
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    with requests.post(
        f"{OLLAMA_BASE}/api/chat", json=payload, stream=True, timeout=120
    ) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line)
                delta = chunk.get("message", {}).get("content", "")
                if delta:
                    yield delta
                if chunk.get("done"):
                    break

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🦙 Ollama Chat")

    models = get_models()
    if not models:
        st.warning("⚠️ Ollama not detected.\nMake sure `ollama serve` is running on port 11434.")
        models = ["(no models found)"]

    selected_model = st.selectbox("Model", models)

    st.divider()
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.05)
    max_tokens  = st.slider("Max tokens", 128, 4096, 1024, 128)
    system_prompt = st.text_area(
        "System prompt",
        value="You are a helpful, concise assistant.",
        height=100,
    )

    st.divider()
    if st.button("🗑 Clear chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown(
        "<p style='font-size:0.7rem;color:#4b5563;font-family:JetBrains Mono,monospace;"
        "margin-top:2rem;'>Ollama · localhost:11434</p>",
        unsafe_allow_html=True,
    )

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ── Main area ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="title-bar">'
    '<div class="status-dot"></div>'
    '<h1>Ollama Chat</h1>'
    '</div>',
    unsafe_allow_html=True,
)

# Render history
chat_html = '<div class="chat-container">'
for msg in st.session_state.messages:
    role   = msg["role"]
    avatar = "👤" if role == "user" else "🤖"
    cls    = "user" if role == "user" else "bot"
    content_escaped = (
        msg["content"]
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    chat_html += (
        f'<div class="msg">'
        f'  <div class="msg-avatar {cls}">{avatar}</div>'
        f'  <div class="msg-body {cls}"><pre style="white-space:pre-wrap;background:transparent;border:none;padding:0;margin:0;">{content_escaped}</pre></div>'
        f'</div>'
    )
chat_html += "</div>"
st.markdown(chat_html, unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────────────────────
user_input = st.chat_input("Message…")

if user_input and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})

    api_messages = [{"role": "system", "content": system_prompt}] + [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.spinner(""):
        st.markdown(
            '<div class="thinking">🤖 <span class="dot">●</span>'
            '<span class="dot">●</span><span class="dot">●</span>'
            ' thinking…</div>',
            unsafe_allow_html=True,
        )

    response_placeholder = st.empty()
    full_response = ""
    t0 = time.time()

    try:
        for token in stream_chat(selected_model, api_messages, temperature, max_tokens):
            full_response += token
            response_placeholder.markdown(
                f'<div class="msg">'
                f'  <div class="msg-avatar bot">🤖</div>'
                f'  <div class="msg-body bot"><pre style="white-space:pre-wrap;background:transparent;border:none;padding:0;margin:0;">{full_response}▌</pre></div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        elapsed = round(time.time() - t0, 1)
        response_placeholder.markdown(
            f'<div class="msg">'
            f'  <div class="msg-avatar bot">🤖</div>'
            f'  <div class="msg-body bot">'
            f'    <pre style="white-space:pre-wrap;background:transparent;border:none;padding:0;margin:0;">{full_response}</pre>'
            f'    <div class="msg-meta">{selected_model} · {elapsed}s</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to Ollama. Is `ollama serve` running?")
    except Exception as e:
        st.error(f"❌ Error: {e}")