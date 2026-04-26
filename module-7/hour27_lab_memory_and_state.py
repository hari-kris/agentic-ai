"""
Hour 27 Lab — Memory and State
Module 7 | RAG and Agentic Memory

Short-term conversation memory (multi-turn chat with growing history) and
long-term memory (a user profile extracted from each interaction and injected
into future system prompts for personalisation).

Run: streamlit run module-7/hour27_lab_memory_and_state.py
"""

import json
import streamlit as st
from claude_client import chat, chat_with_tools

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 27 — Memory and State", page_icon="🧠", layout="wide")
st.title("🧠 Hour 27 — Memory and State")
st.caption("Module 7 | RAG and Agentic Memory")

st.markdown("""
Agents without memory treat every turn as the first. **Short-term memory** is the conversation
history passed to the LLM on every turn — the agent can refer back to what was said in this session.
**Long-term memory** persists across resets: facts extracted from conversations are stored in a user
profile and injected into the system prompt of future conversations, making the agent personalised.
The key distinction: **in-context** (short-term, resets with session) vs **in-storage** (long-term, survives resets).
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 27 Guide")
    st.markdown("""
**Sections in this lab:**
1. Short-term memory — multi-turn conversation with growing history
2. Long-term memory — user profile extracted and injected into system prompt

**What to observe:**
- Section 1: the agent remembers earlier turns within the session
- Section 1 Reset: clears history — the agent forgets everything
- Section 2: profile persists after resetting the conversation
- Section 2 Profile Reset: simulates a new user — agent forgets permanently
""")
    st.divider()
    st.markdown("""
**Experiment ideas:**
- Section 1: say "my name is [name]" then ask "what's my name?" three turns later
- Section 1: reference a topic from turn 1 in turn 4 — verify the agent recalls it
- Section 2: say your job title and location, reset the chat, start new — agent still knows
- Section 2: tell the agent two contradictory facts and see how the extractor handles it
""")
    st.divider()
    st.info("**Key principle:** Short-term memory is in-context — bounded by the context window and reset with the session. Long-term memory is in-storage — it survives session resets and is injected into future prompts.")

# ── System Prompts ─────────────────────────────────────────────────────────────
CHAT_SYSTEM = """\
You are a helpful, attentive assistant. You have access to the full conversation history.
When the user references something from earlier in the conversation, use that context.
Be concise: 2–4 sentences per response unless the user asks for more detail.\
"""

PERSONALIZED_CHAT_SYSTEM_TEMPLATE = """\
You are a helpful, attentive assistant. You have access to the full conversation history.

Known facts about this user:
{profile_facts}

Use these facts to personalise your responses when relevant.
Do not explicitly say "I know that you…" unless asked — just respond naturally and in context.
Be concise: 2–4 sentences per response unless the user asks for more detail.\
"""

MEMORY_EXTRACTOR_SYSTEM = """\
You are a memory extraction agent. You read a single conversation turn (user message + assistant response)
and extract any new factual information about the user.

Extract only clear, explicit facts — not inferences or assumptions. Examples of extractable facts:
- Name, job title, location, industry
- Preferences stated ("I prefer X to Y", "I like…")
- Goals mentioned ("I am trying to…", "I want to…")
- Technologies or tools they use
- Skills or expertise they explicitly mention

Return ONLY valid JSON — no markdown fences, no commentary:
{"facts": [{"key": "fact category", "value": "fact value"}, {"key": "another category", "value": "another value"}]}

Return an empty list if no new explicit facts are present:
{"facts": []}\
"""

# ── Session State Initialisation (module level) ────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "s1_turn_count" not in st.session_state:
    st.session_state["s1_turn_count"] = 0
if "user_profile" not in st.session_state:
    st.session_state["user_profile"] = []
if "profile_chat_history" not in st.session_state:
    st.session_state["profile_chat_history"] = []
if "s2_extraction_log" not in st.session_state:
    st.session_state["s2_extraction_log"] = []

# ── Section 1 — Short-Term Memory ─────────────────────────────────────────────
st.markdown("---")
st.subheader("1 — Short-Term Memory: Conversation History")
st.markdown(
    "Each turn is appended to the conversation history. The **full history** is sent to Claude on every turn — "
    "this is what allows the agent to reference earlier messages. Reset clears all history."
)

s1_left, s1_right = st.columns([2, 1])

with s1_left:
    # Display chat history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input_s1 = st.chat_input("Type a message…", key="s1_chat_input")
    if user_input_s1:
        st.session_state["chat_history"].append({"role": "user", "content": user_input_s1})
        # Use chat_with_tools with empty tools list for multi-turn conversation
        blocks, _ = chat_with_tools(
            system=CHAT_SYSTEM,
            messages=st.session_state["chat_history"],
            tools=[],
            max_tokens=400,
        )
        response_text = next((b["text"] for b in blocks if b["type"] == "text"), "")
        st.session_state["chat_history"].append({"role": "assistant", "content": response_text})
        st.session_state["s1_turn_count"] += 1
        st.rerun()

    if st.button("🗑 Reset Conversation", key="s1_reset"):
        st.session_state["chat_history"] = []
        st.session_state["s1_turn_count"] = 0
        st.rerun()

with s1_right:
    st.markdown(
        "<div style='border-top:4px solid #43A047;background:#E8F5E9;"
        "border-radius:6px;padding:12px;margin-bottom:10px;'>"
        "<strong style='color:#43A047;'>📊 Conversation State</strong></div>",
        unsafe_allow_html=True,
    )
    turn_count = st.session_state["s1_turn_count"]
    msg_count = len(st.session_state["chat_history"])
    approx_tokens = int(sum(len(m["content"].split()) * 1.3 for m in st.session_state["chat_history"]))
    m1, m2 = st.columns(2)
    m1.metric("Turns", turn_count)
    m2.metric("Messages", msg_count)
    st.metric("Approx. context tokens", approx_tokens)

    with st.expander("View conversation history (raw)"):
        if not st.session_state["chat_history"]:
            st.caption("No messages yet.")
        for i, msg in enumerate(st.session_state["chat_history"]):
            preview = msg["content"][:200] + ("…" if len(msg["content"]) > 200 else "")
            st.markdown(f"**{msg['role'].upper()}:** {preview}")

    st.info("Short-term memory resets when you click Reset Conversation. The agent forgets everything.")

# ── Section 2 — Long-Term Memory ──────────────────────────────────────────────
st.markdown("---")
st.subheader("2 — Long-Term Memory: User Profile")
st.markdown(
    "After each message, a Memory Extractor agent reads the turn and extracts facts about the user. "
    "Facts accumulate in a user profile. On the next turn, the profile is injected into the system "
    "prompt — the agent uses facts from previous interactions to personalise its responses."
)


def build_personalized_system() -> str:
    profile = st.session_state["user_profile"]
    if not profile:
        return CHAT_SYSTEM
    facts_text = "\n".join(f"- {f['key']}: {f['value']}" for f in profile)
    return PERSONALIZED_CHAT_SYSTEM_TEMPLATE.format(profile_facts=facts_text)


def parse_json(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


s2_left, s2_mid, s2_right = st.columns([2, 1, 1])

with s2_left:
    st.markdown("**Personalised Chat** *(profile injected into system prompt)*")

    for msg in st.session_state["profile_chat_history"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input_s2 = st.chat_input("Type a message…", key="s2_chat_input")
    if user_input_s2:
        st.session_state["profile_chat_history"].append({"role": "user", "content": user_input_s2})

        # Respond with personalised system prompt
        blocks, _ = chat_with_tools(
            system=build_personalized_system(),
            messages=st.session_state["profile_chat_history"],
            tools=[],
            max_tokens=400,
        )
        response_text = next((b["text"] for b in blocks if b["type"] == "text"), "")
        st.session_state["profile_chat_history"].append({"role": "assistant", "content": response_text})

        # Extract new facts from this turn
        raw_extract, _ = chat(
            MEMORY_EXTRACTOR_SYSTEM,
            f"User said: {user_input_s2}\nAssistant responded: {response_text}",
            max_tokens=200,
            temperature=0.1,
        )
        extracted = parse_json(raw_extract)
        new_facts = extracted.get("facts", []) if extracted else []

        # Update profile — merge by key
        profile = st.session_state["user_profile"]
        existing_keys = {f["key"]: i for i, f in enumerate(profile)}
        added = 0
        for fact in new_facts:
            k = fact.get("key", "")
            v = fact.get("value", "")
            if not k or not v:
                continue
            if k in existing_keys:
                profile[existing_keys[k]]["value"] = v
            else:
                profile.append({"key": k, "value": v})
                existing_keys[k] = len(profile) - 1
                added += 1
        st.session_state["user_profile"] = profile
        st.session_state["s2_extraction_log"].append({"facts": new_facts, "count": len(new_facts)})

        st.rerun()

    if st.button("🗑 Reset Conversation (profile persists)", key="s2_reset_chat"):
        st.session_state["profile_chat_history"] = []
        st.rerun()

with s2_mid:
    st.markdown(
        "<div style='border-top:4px solid #43A047;background:#E8F5E9;"
        "border-radius:6px;padding:12px;margin-bottom:10px;'>"
        "<strong style='color:#43A047;'>🧠 User Profile<br>(Long-Term Memory)</strong></div>",
        unsafe_allow_html=True,
    )
    profile = st.session_state["user_profile"]
    if not profile:
        st.info("No facts extracted yet. Tell the agent your name, job, or preferences.")
    else:
        for fact in profile:
            st.markdown(f"**{fact['key']}:** {fact['value']}")

    if st.button("🗑 Reset Profile (new user)", key="s2_reset_profile"):
        st.session_state["user_profile"] = []
        st.session_state["s2_extraction_log"] = []
        st.rerun()

    st.caption("Resetting profile simulates a new user. Resetting conversation above simulates a new session.")

with s2_right:
    st.markdown(
        "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;"
        "border-radius:6px;padding:12px;margin-bottom:10px;'>"
        "<strong style='color:#8E24AA;'>📋 Extraction Log</strong></div>",
        unsafe_allow_html=True,
    )
    log = st.session_state["s2_extraction_log"]
    if not log:
        st.caption("No extractions yet.")
    else:
        for i, entry in enumerate(reversed(log)):
            turn_num = len(log) - i
            count = entry.get("count", 0)
            if count > 0:
                st.markdown(
                    f"<div style='border-top:3px solid #43A047;background:#E8F5E9;"
                    f"border-radius:4px;padding:5px 10px;margin-bottom:4px;font-size:0.82em;'>"
                    f"<strong style='color:#43A047;'>Turn {turn_num}:</strong> {count} fact(s) extracted</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.caption(f"Turn {turn_num}: no new facts")

    with st.expander("Raw extraction JSON"):
        if not log:
            st.caption("No extractions yet.")
        else:
            st.code(json.dumps(log, indent=2), language="json")

    st.info("The extractor runs after every turn — even when no new facts are found.")

# ── Observation callout ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
**Try this sequence to see the memory distinction clearly:**

1. In Section 2, start chatting — say your name, job title, and a preference
2. Click **Reset Conversation (profile persists)** — the chat clears, but the profile stays
3. Start a new conversation — the agent still knows your name and job without being told again
4. Click **Reset Profile (new user)** — now the agent truly forgets

Compare this to Section 1: Reset Conversation there clears *everything* — there is no persistent profile.
""")
