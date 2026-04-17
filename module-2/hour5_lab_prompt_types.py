"""
Hour 5 Lab — Prompt Type Classifier Quiz
Module 2 | Prompt Fundamentals

A 10-question quiz game. Each round shows one prompt; the student selects
the type, then Claude reveals its classification with a reason. A score
counter tracks performance. Bonus: write your own prompt and let Claude
validate whether it matches the intended type.

The 6 prompt types:
  instruction — directs the model to perform a task
  role        — establishes model identity or persona
  planning    — asks the model to decompose a goal into steps
  tool_use    — tells the model it has access to external tools
  routing     — classifies input and returns a label
  evaluation  — judges quality against criteria

Run: streamlit run hour5_lab_prompt_types.py
"""

import json
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Prompt Type Quiz", page_icon="🎯", layout="wide")
st.title("🎯 Hour 5 — Prompt Type Classifier Quiz")
st.caption("Module 2 | Prompt Fundamentals")

# ── Quiz data ─────────────────────────────────────────────────────────────────

QUIZ = [
    {
        "prompt": "You are a legal assistant specialising in UK contract review.",
        "answer": "role",
        "reason": "Pure identity definition. There is no task, no output. Its only job is to define who the model is.",
    },
    {
        "prompt": "Summarise the key points from this meeting transcript in 5 bullet points.",
        "answer": "instruction",
        "reason": "Clear action verb ('summarise'), specific task, specific output format. The model is told to do something, not to become something.",
    },
    {
        "prompt": "Break this goal into subtasks: Launch a product blog for our SaaS platform.",
        "answer": "planning",
        "reason": "'Break into subtasks' is the signal. This primes the model to produce a plan, not to execute the goal.",
    },
    {
        "prompt": "You have access to a calculator. Use it to compute compound interest on £10,000 at 5% over 3 years.",
        "answer": "tool_use",
        "reason": "'You have access to a [tool]' is the signature. The model is told which tool exists and instructed to use it.",
    },
    {
        "prompt": "Determine whether this support ticket is: BILLING, TECHNICAL, or ACCOUNT. Return only the label.",
        "answer": "routing",
        "reason": "Fixed set of output labels, classify-and-return pattern. The model routes input to one of a predefined set of categories.",
    },
    {
        "prompt": "Score this product description from 1–10 on persuasiveness and clarity. Give specific feedback.",
        "answer": "evaluation",
        "reason": "Scoring against named criteria + feedback = evaluation. The model is judging something, not doing it.",
    },
    {
        "prompt": "Extract all named entities from this article and return them as a JSON array.",
        "answer": "instruction",
        "reason": "Action verb ('extract'), specific output format (JSON array). Extraction is a task, not a classification.",
    },
    {
        "prompt": "What steps would I need to take to set up a RAG system from scratch?",
        "answer": "planning",
        "reason": "'What steps' primes a plan. Even phrased as a question, the expected output is a decomposed sequence of actions.",
    },
    {
        "prompt": "Is this customer complaint urgent? Respond with YES, NO, or UNCLEAR only.",
        "answer": "routing",
        "reason": "Binary/ternary label output only. The model routes the input to one of three fixed labels.",
    },
    {
        "prompt": "Review this Python function and identify any bugs, anti-patterns, or performance issues.",
        "answer": "evaluation",
        "reason": "'Review and identify issues' = judging quality against criteria. The model evaluates, not executes.",
    },
]

TYPES = ["instruction", "role", "planning", "tool_use", "routing", "evaluation"]

TYPE_COLORS = {
    "instruction": "#1E88E5",
    "role":        "#8E24AA",
    "planning":    "#43A047",
    "tool_use":    "#FB8C00",
    "routing":     "#00897B",
    "evaluation":  "#E53935",
}

TYPE_DESCRIPTIONS = {
    "instruction": "Directs the model to perform a specific task — has an action verb and expected output",
    "role":        "Establishes the model's identity or persona — defines WHO it is, not what to do",
    "planning":    "Asks the model to decompose a goal — output is a list of subtasks, not the result",
    "tool_use":    "Tells the model it has access to external tools and instructs it to use them",
    "routing":     "Asks the model to classify input into a fixed set of predefined labels",
    "evaluation":  "Asks the model to judge or score something against named criteria",
}

CLASSIFIER_SYSTEM = """\
You are a prompt engineering expert who classifies prompts precisely.
You always choose exactly one type and explain your reasoning concisely.\
"""

CLASSIFIER_PROMPT = """\
Classify this prompt into exactly one type:
- instruction: directs the model to perform a specific task
- role: establishes model identity or persona
- planning: asks the model to decompose a goal into subtasks
- tool_use: tells the model it has access to external tools
- routing: classifies input and returns a fixed label
- evaluation: judges/scores something against criteria

Prompt: "{prompt}"

Return ONLY valid JSON:
{{"type": "one_of_the_six_types", "reason": "one concise sentence explaining the classification"}}\
"""

# ── Session state init ────────────────────────────────────────────────────────

if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "answers" not in st.session_state:
    st.session_state.answers = {}
if "revealed" not in st.session_state:
    st.session_state.revealed = {}

# ── Score header ──────────────────────────────────────────────────────────────

idx = st.session_state.quiz_index
total_q = len(QUIZ)
answered = len(st.session_state.answers)

hdr_left, hdr_right = st.columns([3, 1])
with hdr_left:
    st.progress(answered / total_q, text=f"Question {min(idx + 1, total_q)} of {total_q}")
with hdr_right:
    st.metric("Score", f"{st.session_state.score} / {answered}" if answered else "—")

st.divider()

# ── Quiz complete screen ──────────────────────────────────────────────────────

if idx >= total_q:
    score = st.session_state.score
    st.subheader(f"Quiz complete! Final score: {score} / {total_q}")

    pct = score / total_q
    if pct == 1.0:
        st.success("Perfect score! You have a strong grasp of all six prompt types.")
    elif pct >= 0.7:
        st.info("Good work! Review the types you missed below.")
    else:
        st.warning("Keep practising. Review the type descriptions and run the quiz again.")

    st.divider()
    st.subheader("Results Review")
    for i, q in enumerate(QUIZ):
        your_ans = st.session_state.answers.get(i, "—")
        correct  = q["answer"]
        is_right = your_ans == correct
        icon     = "✅" if is_right else "❌"
        color    = TYPE_COLORS[correct]
        st.markdown(
            f"{icon} **Q{i+1}:** _{q['prompt'][:80]}{'…' if len(q['prompt']) > 80 else ''}_  \n"
            f"Your answer: **{your_ans}** | Correct: "
            f"<span style='color:{color};font-weight:bold;'>{correct}</span>  \n"
            f"<span style='color:#666;font-size:0.9em;'>{q['reason']}</span>",
            unsafe_allow_html=True,
        )
        st.write("")

    if st.button("🔄 Restart Quiz", type="primary"):
        st.session_state.quiz_index = 0
        st.session_state.score = 0
        st.session_state.answers = {}
        st.session_state.revealed = {}
        st.rerun()

else:
    # ── Current question ──────────────────────────────────────────────────────
    q = QUIZ[idx]
    already_answered = idx in st.session_state.answers

    st.subheader(f"Question {idx + 1}")
    st.markdown(
        f"<div style='background:#f4f4f8;border-left:5px solid #aaa;"
        f"padding:14px 18px;border-radius:4px;font-size:1.1em;'>"
        f"<em>\"{q['prompt']}\"</em></div>",
        unsafe_allow_html=True,
    )

    st.markdown("**What type of prompt is this?**")

    # Type reference strip
    ref_cols = st.columns(6)
    for col, t in zip(ref_cols, TYPES):
        col.markdown(
            f"<div style='text-align:center;background:{TYPE_COLORS[t]}18;"
            f"border:1px solid {TYPE_COLORS[t]};border-radius:4px;padding:4px;"
            f"font-size:0.78em;color:{TYPE_COLORS[t]};font-weight:bold;'>{t}</div>",
            unsafe_allow_html=True,
        )
    st.caption("Hover over each type above for a reminder of what each means.")

    st.write("")
    guess = st.radio(
        "Your answer:",
        TYPES,
        horizontal=True,
        key=f"guess_{idx}",
        disabled=already_answered,
    )

    btn_cols = st.columns([1, 1, 3])

    if not already_answered:
        if btn_cols[0].button("Submit Answer", type="primary"):
            st.session_state.answers[idx] = guess
            is_correct = guess == q["answer"]
            if is_correct:
                st.session_state.score += 1

            # Get Claude's classification
            with st.spinner("Claude is classifying..."):
                raw, _ = chat(
                    system=CLASSIFIER_SYSTEM,
                    user=CLASSIFIER_PROMPT.format(prompt=q["prompt"]),
                    max_tokens=200,
                    temperature=0.1,
                )
            try:
                clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                parsed = json.loads(clean)
                st.session_state.revealed[idx] = parsed
            except json.JSONDecodeError:
                st.session_state.revealed[idx] = {"type": q["answer"], "reason": q["reason"]}
            st.rerun()
    else:
        # Show reveal
        your_ans = st.session_state.answers[idx]
        is_correct = your_ans == q["answer"]
        revealed   = st.session_state.revealed.get(idx, {})
        claude_type = revealed.get("type", q["answer"])
        color = TYPE_COLORS.get(q["answer"], "#333")

        if is_correct:
            st.success(f"✅ Correct! **{your_ans}**")
        else:
            st.error(
                f"❌ You said **{your_ans}** — correct answer is "
                f"**{q['answer']}**"
            )

        st.markdown(
            f"<div style='border-left:4px solid {color};padding:10px 14px;"
            f"background:#f9f9f9;border-radius:4px;margin-top:8px;'>"
            f"<strong style='color:{color};'>Claude says: {claude_type}</strong><br>"
            f"<span style='font-size:0.9em;'>{revealed.get('reason', q['reason'])}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"📖 {TYPE_DESCRIPTIONS[q['answer']]}")

        if btn_cols[0].button("Next →", type="primary"):
            st.session_state.quiz_index += 1
            st.rerun()

# ── Bonus: classify your own prompt ──────────────────────────────────────────

st.divider()
with st.expander("Bonus — Classify your own prompt"):
    st.markdown(
        "Write a prompt that you intend to be a specific type. "
        "Claude will classify it and tell you if it matches your intent."
    )
    bonus_col1, bonus_col2 = st.columns([3, 1])
    with bonus_col1:
        custom_prompt = st.text_area("Your prompt:", height=80, placeholder="Write a prompt here...")
    with bonus_col2:
        intended_type = st.selectbox("Intended type:", TYPES)
        run_bonus = st.button("Classify It", type="primary")

    if run_bonus and custom_prompt.strip():
        with st.spinner("Classifying..."):
            raw, _ = chat(
                system=CLASSIFIER_SYSTEM,
                user=CLASSIFIER_PROMPT.format(prompt=custom_prompt.strip()),
                max_tokens=200,
                temperature=0.1,
            )
        try:
            clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            result = json.loads(clean)
            detected = result["type"]
            color = TYPE_COLORS.get(intended_type, "#333")
            if detected == intended_type:
                st.success(f"✅ Claude classified it as **{detected}** — matches your intent!")
            else:
                st.warning(
                    f"⚠️ Claude classified it as **{detected}**, not **{intended_type}**.\n\n"
                    f"Reason: {result['reason']}\n\n"
                    f"Try revising your prompt to make the **{intended_type}** pattern clearer."
                )
        except json.JSONDecodeError:
            st.code(raw)
