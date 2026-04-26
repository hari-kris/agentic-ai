"""
Hour 12 Lab — Reflection Pattern
Module 4 | Core Agentic Patterns I

An agent generates a draft, a critic scores it, and a refiner improves it.
This lab shows a single reflection round and a multi-round loop with score tracking.

Run: streamlit run module-4/hour12_lab_reflection_pattern.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 12 — Reflection Pattern", page_icon="🔁", layout="wide")
st.title("🔁 Hour 12 — Reflection Pattern")
st.caption("Module 4 | Core Agentic Patterns I")

st.markdown("""
The **Reflection Pattern** closes the loop between generation and quality.
Instead of trusting a single LLM call to produce the best possible output, a separate
**Critic** agent evaluates the draft, and a **Refiner** agent improves it.

This lab walks through:
1. **Pipeline overview** — the three roles and how they connect
2. **Single round** — run one Generator → Critic → Refiner cycle, see before/after
3. **Multi-round loop** — run up to 3 rounds and watch scores improve
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 12 Guide")
    st.markdown("""
**Sections in this lab:**
1. **Pipeline diagram** — see the three agents and data flow
2. **Single round** — run one full reflection cycle
3. **Multi-round loop** — iterate up to 3 times with score tracking

**What to observe:**
- How the Critic JSON shapes the Refiner's prompt
- Which criteria improve most between rounds
- When scores plateau — and why
- The token cost of each extra round
""")
    st.divider()
    st.markdown("**Experiment ideas:**")
    st.markdown("- Try a poorly written task description and see how fast it improves")
    st.markdown("- Set rounds to 1 vs 3 for the same input — compare final quality")
    st.markdown("- Change the max_tokens on the Generator and see if the Critic scores shift")
    st.divider()
    st.info("**Key principle:** A separate critic with structured output finds flaws that a combined generate+critique prompt misses.")

# ── System Prompts ─────────────────────────────────────────────────────────────
GENERATOR_SYSTEM = """\
You are a professional writer. Given a writing task, produce a clear, accurate, and
well-structured response. Write naturally — do not add disclaimers, meta-commentary,
or instructions. Just produce the content.\
"""

CRITIC_SYSTEM = """\
You are a quality evaluator for written content. Score the provided text on four criteria,
each from 1 to 5:

- clarity (1 = confusing or hard to follow, 5 = crystal clear)
- accuracy (1 = factually wrong or vague, 5 = precise and correct)
- tone (1 = inappropriate for the audience, 5 = perfectly suited)
- completeness (1 = major gaps, 5 = thorough and nothing missing)

Be strict. Reserve 5 for genuinely excellent work.

Return ONLY valid JSON — no markdown fences, no commentary:
{"clarity": N, "accuracy": N, "tone": N, "completeness": N, "feedback": "one specific, actionable improvement sentence"}\
"""

REFINER_SYSTEM = """\
You are a professional editor. You receive a draft and a structured critique.
Your job is to rewrite the draft to address the specific feedback given.
Do not add meta-commentary like "As suggested..." — just produce the improved text.
Keep the same general scope and length as the original.\
"""

# ── Section 1: Pipeline Diagram ────────────────────────────────────────────────
st.divider()
st.subheader("1 — The Reflection Pipeline")

cols = st.columns(5, gap="small")

cards = [
    ("#1E88E5", "#E3F2FD", "✍️", "[GENERATOR]", "Writes the initial draft from the user's task description."),
    ("#757575", "#F5F5F5", "→", "", ""),
    ("#E53935", "#FFEBEE", "🔍", "[CRITIC]", "Reads the draft and returns JSON scores on clarity, accuracy, tone, completeness."),
    ("#757575", "#F5F5F5", "→", "", ""),
    ("#8E24AA", "#F3E5F5", "✨", "[REFINER]", "Takes the draft + critique and rewrites to address the specific feedback."),
]

for col, (color, bg, icon, label, desc) in zip(cols, cards):
    with col:
        if label:
            st.markdown(
                f"<div style='border-top:4px solid {color};background:{bg};"
                f"border-radius:6px;padding:14px;min-height:160px;text-align:center;'>"
                f"<div style='font-size:2em;'>{icon}</div>"
                f"<div style='font-weight:bold;color:{color};font-size:0.95em;margin:6px 0;'>{label}</div>"
                f"<div style='font-size:0.82em;color:#444;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='display:flex;align-items:center;justify-content:center;"
                "height:160px;font-size:1.8em;color:#999;'>→</div>",
                unsafe_allow_html=True,
            )

st.markdown("")
with st.expander("See system prompts"):
    tab1, tab2, tab3 = st.tabs(["Generator", "Critic", "Refiner"])
    with tab1:
        st.code(GENERATOR_SYSTEM, language="text")
    with tab2:
        st.code(CRITIC_SYSTEM, language="text")
    with tab3:
        st.code(REFINER_SYSTEM, language="text")

# ── Section 2: Single Round ────────────────────────────────────────────────────
st.divider()
st.subheader("2 — Single Reflection Round")

st.markdown("Enter a writing task. The lab runs one Generator → Critic → Refiner cycle and shows you the before/after side by side.")

PRESET_TASKS = [
    "Custom task — type below",
    "Explain what machine learning is in 3 sentences for a non-technical manager.",
    "Write a brief email declining a meeting invitation politely.",
    "Describe what the internet is to someone who has never used it.",
    "Summarise the pros and cons of remote work in 4 bullet points.",
]

selected = st.selectbox("Pick a preset task or write your own:", PRESET_TASKS, key="s2_preset")
task_input = st.text_area(
    "Writing task:",
    value="" if selected == PRESET_TASKS[0] else selected,
    placeholder="e.g. Explain quantum entanglement to a 12-year-old in two paragraphs.",
    height=80,
    key="s2_task",
)

if st.button("▶ Run One Reflection Round", type="primary", disabled=not task_input.strip()):
    total_in, total_out = 0, 0

    with st.spinner("Generator writing draft…"):
        draft, u1 = chat(GENERATOR_SYSTEM, task_input.strip(), max_tokens=600, temperature=0.7)
    total_in += u1["input_tokens"]
    total_out += u1["output_tokens"]

    critic_user = f"Draft to evaluate:\n\n{draft}"
    with st.spinner("Critic scoring draft…"):
        raw_critique, u2 = chat(CRITIC_SYSTEM, critic_user, max_tokens=300, temperature=0.2)
    total_in += u2["input_tokens"]
    total_out += u2["output_tokens"]

    try:
        clean = raw_critique.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        critique = json.loads(clean)
    except json.JSONDecodeError:
        st.error("Critic returned unexpected output. Showing raw:")
        st.code(raw_critique)
        st.stop()

    refiner_user = (
        f"Original task: {task_input.strip()}\n\n"
        f"Draft:\n{draft}\n\n"
        f"Critique:\n"
        f"  Clarity: {critique.get('clarity')}/5\n"
        f"  Accuracy: {critique.get('accuracy')}/5\n"
        f"  Tone: {critique.get('tone')}/5\n"
        f"  Completeness: {critique.get('completeness')}/5\n"
        f"  Feedback: {critique.get('feedback')}\n\n"
        "Rewrite the draft to address the feedback."
    )
    with st.spinner("Refiner improving draft…"):
        refined, u3 = chat(REFINER_SYSTEM, refiner_user, max_tokens=700, temperature=0.5)
    total_in += u3["input_tokens"]
    total_out += u3["output_tokens"]

    st.markdown("---")
    left, right = st.columns(2)

    with left:
        st.markdown(
            "<div style='border-top:4px solid #1E88E5;padding:4px 0 8px;'>"
            "<strong style='color:#1E88E5;'>✍️ [GENERATOR] — Initial Draft</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(draft)

    with right:
        st.markdown(
            "<div style='border-top:4px solid #8E24AA;padding:4px 0 8px;'>"
            "<strong style='color:#8E24AA;'>✨ [REFINER] — Improved Draft</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(refined)

    with st.container(border=True):
        st.markdown(
            "<strong style='color:#E53935;'>🔍 [CRITIC] Scores</strong>",
            unsafe_allow_html=True,
        )
        crit_cols = st.columns(4)
        criteria = [
            ("clarity", "#1E88E5"),
            ("accuracy", "#43A047"),
            ("tone", "#8E24AA"),
            ("completeness", "#E53935"),
        ]
        for col, (key, color) in zip(crit_cols, criteria):
            score = critique.get(key, 0)
            col.metric(key.capitalize(), f"{score}/5")
            col.progress(score / 5)

        st.info(f"**Feedback:** {critique.get('feedback', '')}")

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM calls", 3)
    c2.metric("Total input tokens", total_in)
    c3.metric("Total output tokens", total_out)

# ── Section 3: Multi-Round Loop ────────────────────────────────────────────────
st.divider()
st.subheader("3 — Multi-Round Reflection Loop")

st.markdown("""
Run up to 3 rounds of reflection on the same task. Each round feeds the previous
refined output back through the Critic and Refiner. Watch how scores change.
""")

PRESET_TASKS_3 = [
    "Custom task — type below",
    "Write a one-paragraph introduction to neural networks for a software developer.",
    "Explain why sleep is important in three clear sentences.",
    "Write a short product description for a noise-cancelling headset.",
]

selected3 = st.selectbox("Pick a preset task or write your own:", PRESET_TASKS_3, key="s3_preset")
task3 = st.text_area(
    "Writing task:",
    value="" if selected3 == PRESET_TASKS_3[0] else selected3,
    placeholder="e.g. Describe the water cycle in plain language.",
    height=80,
    key="s3_task",
)
num_rounds = st.slider("Number of reflection rounds:", min_value=1, max_value=3, value=2)

if st.button("▶ Run Multi-Round Reflection", type="primary", disabled=not task3.strip()):
    total_in, total_out = 0, 0
    rounds_data = []

    with st.spinner("Generator writing initial draft…"):
        current_draft, u0 = chat(GENERATOR_SYSTEM, task3.strip(), max_tokens=600, temperature=0.7)
    total_in += u0["input_tokens"]
    total_out += u0["output_tokens"]

    for round_num in range(1, num_rounds + 1):
        with st.spinner(f"Round {round_num}: Critic scoring…"):
            raw_crit, uc = chat(CRITIC_SYSTEM, f"Draft to evaluate:\n\n{current_draft}", max_tokens=300, temperature=0.2)
        total_in += uc["input_tokens"]
        total_out += uc["output_tokens"]

        try:
            clean = raw_crit.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            critique = json.loads(clean)
        except json.JSONDecodeError:
            st.error(f"Round {round_num}: Critic returned unexpected output.")
            st.code(raw_crit)
            break

        avg_score = sum(critique.get(k, 0) for k in ["clarity", "accuracy", "tone", "completeness"]) / 4

        with st.spinner(f"Round {round_num}: Refiner improving…"):
            refiner_msg = (
                f"Original task: {task3.strip()}\n\n"
                f"Draft:\n{current_draft}\n\n"
                f"Critique:\n"
                f"  Clarity: {critique.get('clarity')}/5\n"
                f"  Accuracy: {critique.get('accuracy')}/5\n"
                f"  Tone: {critique.get('tone')}/5\n"
                f"  Completeness: {critique.get('completeness')}/5\n"
                f"  Feedback: {critique.get('feedback')}\n\n"
                "Rewrite the draft to address the feedback."
            )
            refined, ur = chat(REFINER_SYSTEM, refiner_msg, max_tokens=700, temperature=0.5)
        total_in += ur["input_tokens"]
        total_out += ur["output_tokens"]

        rounds_data.append({
            "round": round_num,
            "draft": current_draft,
            "critique": critique,
            "refined": refined,
            "avg": avg_score,
        })

        current_draft = refined

    st.markdown("---")
    for rd in rounds_data:
        with st.expander(f"Round {rd['round']} — avg score {rd['avg']:.1f}/5", expanded=(rd["round"] == 1)):
            ra, rb = st.columns(2)
            with ra:
                st.markdown(f"**Input draft (to Critic):**")
                st.markdown(rd["draft"])
            with rb:
                st.markdown("**Refined output:**")
                st.markdown(rd["refined"])

            crit_cols = st.columns(4)
            for col, key in zip(crit_cols, ["clarity", "accuracy", "tone", "completeness"]):
                score = rd["critique"].get(key, 0)
                col.metric(key.capitalize(), f"{score}/5")
                col.progress(score / 5)
            st.info(f"**Feedback:** {rd['critique'].get('feedback', '')}")

    if len(rounds_data) > 1:
        st.markdown("**Score progression across rounds:**")
        score_cols = st.columns(len(rounds_data))
        for col, rd in zip(score_cols, rounds_data):
            col.metric(
                f"Round {rd['round']}",
                f"{rd['avg']:.1f}/5",
                delta=f"+{rd['avg'] - rounds_data[0]['avg']:.1f}" if rd["round"] > 1 else None,
            )

    st.markdown("**Final output:**")
    with st.container(border=True):
        st.markdown(current_draft)

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM calls", 1 + num_rounds * 2)
    c2.metric("Total input tokens", total_in)
    c3.metric("Total output tokens", total_out)
