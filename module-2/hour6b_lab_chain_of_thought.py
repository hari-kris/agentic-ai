"""
Hour 6B Lab — Chain-of-Thought Explorer
Module 2 | Prompt Fundamentals

The same reasoning problem is sent to Claude three ways simultaneously:
  1. Direct         — just answer, no reasoning instruction
  2. Zero-shot CoT  — "think step by step" added to the prompt
  3. Few-shot CoT   — 2 worked examples with full reasoning chains

A judge call checks each answer for correctness and rates reasoning quality.
Students observe where and why CoT makes a measurable difference.

Key insight: CoT externalises the working memory the model needs for
multi-step problems. It's not a trick — it changes what the model "sees"
at each generation step.

Run: streamlit run hour6b_lab_chain_of_thought.py
"""

import json
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Chain-of-Thought Explorer", page_icon="🧠", layout="wide")
st.title("🧠 Hour 6B — Chain-of-Thought Explorer")
st.caption("Module 2 | Prompt Fundamentals")

st.markdown(
    """
The **same problem** is answered three ways. The only difference is the prompting strategy.

| Strategy | What changes |
|---|---|
| **Direct** | No instructions — just answer |
| **Zero-shot CoT** | "Think step by step" added — model reasons before answering |
| **Few-shot CoT** | 2 worked examples show the reasoning pattern — model follows the template |
"""
)

# ── Problems ──────────────────────────────────────────────────────────────────

PROBLEMS = {
    "Bridge Crossing (Logic)": {
        "question": (
            "Five people need to cross a bridge at night with one torch. "
            "The bridge holds at most 2 people. When two cross, they go at the slower pace.\n"
            "Times: Alice=1 min, Bob=2 min, Carlos=5 min, Diana=8 min, Eve=10 min.\n"
            "What is the minimum total time for all 5 to cross?"
        ),
        "answer": "25 minutes",
        "few_shot_examples": [
            {
                "q": "Three people cross a bridge: X=1 min, Y=2 min, Z=5 min. One torch, max 2 at once. Minimum time?",
                "a": (
                    "Step 1: X and Y cross together → 2 min. Total: 2\n"
                    "Step 2: X returns with torch → 1 min. Total: 3\n"
                    "Step 3: X and Z cross together → 5 min. Total: 8\n"
                    "Answer: 8 minutes"
                ),
            },
            {
                "q": "Four people: A=1, B=2, C=7, D=10. Same rules. Minimum time?",
                "a": (
                    "Step 1: A and B cross → 2 min. Total: 2\n"
                    "Step 2: A returns → 1 min. Total: 3\n"
                    "Step 3: C and D cross → 10 min. Total: 13\n"
                    "Step 4: B returns → 2 min. Total: 15\n"
                    "Step 5: A and B cross → 2 min. Total: 17\n"
                    "Answer: 17 minutes"
                ),
            },
        ],
    },
    "Marble Logic": {
        "question": (
            "Tom has twice as many marbles as Jerry. "
            "Sarah has 5 more than Tom. "
            "Together the three of them have 61 marbles. "
            "How many does Sarah have?"
        ),
        "answer": "27",
        "few_shot_examples": [
            {
                "q": "Ann has 3 times as many coins as Bob. Together they have 48. How many does Ann have?",
                "a": (
                    "Let Bob = b, Ann = 3b.\n"
                    "3b + b = 48 → 4b = 48 → b = 12.\n"
                    "Ann = 3 × 12 = 36.\n"
                    "Answer: 36"
                ),
            },
            {
                "q": "Mia has 4 more books than Leo. Together they have 20. How many does Mia have?",
                "a": (
                    "Let Leo = l, Mia = l + 4.\n"
                    "l + (l + 4) = 20 → 2l = 16 → l = 8.\n"
                    "Mia = 8 + 4 = 12.\n"
                    "Answer: 12"
                ),
            },
        ],
    },
    "Probability Puzzle": {
        "question": (
            "A bag contains 4 red balls and 6 blue balls. "
            "You draw 2 balls without replacement. "
            "What is the probability that both balls are the same colour? "
            "Give your answer as a fraction."
        ),
        "answer": "7/15",
        "few_shot_examples": [
            {
                "q": "A bag has 3 red and 3 blue balls. Draw 2 without replacement. P(both same colour)?",
                "a": (
                    "P(both red) = 3/6 × 2/5 = 6/30 = 1/5\n"
                    "P(both blue) = 3/6 × 2/5 = 6/30 = 1/5\n"
                    "P(same colour) = 1/5 + 1/5 = 2/5\n"
                    "Answer: 2/5"
                ),
            },
            {
                "q": "Bag has 2 red, 4 blue. Draw 2 without replacement. P(both same colour)?",
                "a": (
                    "P(both red) = 2/6 × 1/5 = 2/30 = 1/15\n"
                    "P(both blue) = 4/6 × 3/5 = 12/30 = 2/5\n"
                    "P(same colour) = 1/15 + 2/5 = 1/15 + 6/15 = 7/15\n"
                    "Answer: 7/15"
                ),
            },
        ],
    },
    "Set Theory": {
        "question": (
            "In a class of 40 students: 18 play football, 16 play basketball, "
            "5 play both sports. "
            "How many students play neither sport?"
        ),
        "answer": "11",
        "few_shot_examples": [
            {
                "q": "30 people: 12 speak French, 18 speak English, 6 speak both. How many speak neither?",
                "a": (
                    "Using inclusion-exclusion:\n"
                    "Speak at least one = 12 + 18 - 6 = 24\n"
                    "Neither = 30 - 24 = 6\n"
                    "Answer: 6"
                ),
            },
            {
                "q": "50 students: 20 study maths, 25 study science, 8 study both. How many study neither?",
                "a": (
                    "Study at least one = 20 + 25 - 8 = 37\n"
                    "Neither = 50 - 37 = 13\n"
                    "Answer: 13"
                ),
            },
        ],
    },
}

JUDGE_SYSTEM = "You are a precise evaluator of mathematical and logical reasoning."
JUDGE_PROMPT = """\
Evaluate this response to the following problem.

Problem: {question}
Correct answer: {answer}
Model response: {response}

Check:
1. Is the final answer correct? (yes/no)
2. Rate reasoning quality 1-5 (1=no reasoning shown, 5=clear logical steps)

Return ONLY valid JSON:
{{"correct": true, "reasoning_score": 3, "note": "one sentence"}}\
"""

# ── Prompts ───────────────────────────────────────────────────────────────────

def make_direct_prompt(question: str) -> str:
    return f"Answer this question. Give only the final answer, no working.\n\n{question}"


def make_zero_shot_cot(question: str) -> str:
    return f"Think step by step, then give the final answer clearly at the end.\n\n{question}"


def make_few_shot_cot(question: str, examples: list[dict]) -> str:
    shots = ""
    for ex in examples:
        shots += f"Q: {ex['q']}\nA: {ex['a']}\n\n"
    return f"{shots}Q: {question}\nA:"


# ── UI ────────────────────────────────────────────────────────────────────────

st.divider()

selected = st.selectbox("Choose a reasoning problem:", list(PROBLEMS.keys()))
problem  = PROBLEMS[selected]

with st.expander("Problem statement", expanded=True):
    st.markdown(f"**{problem['question']}**")
    st.caption(f"Expected answer: ||{problem['answer']}|| (revealed after you run)")

run = st.button("▶  Run All Three Strategies", type="primary")

# ── Side-by-side results ──────────────────────────────────────────────────────

STRATEGIES = [
    ("direct",        "⚡ Direct",        "#E53935",
     "No reasoning instruction. Model answers immediately."),
    ("zero_shot_cot", "🔗 Zero-Shot CoT", "#FB8C00",
     "\"Think step by step\" appended. No examples."),
    ("few_shot_cot",  "📚 Few-Shot CoT",  "#43A047",
     "Two worked examples show the expected reasoning pattern."),
]

if run:
    cols = st.columns(3)
    headers = {}
    output_slots = {}
    judge_slots  = {}

    for col, (key, label, color, desc) in zip(cols, STRATEGIES):
        with col:
            st.markdown(
                f"<div style='border-top:4px solid {color};padding:8px 0 4px 0;'>"
                f"<strong style='color:{color};font-size:1.05em;'>{label}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.caption(desc)
            output_slots[key] = st.empty()
            judge_slots[key]  = st.empty()

    responses = {}

    # ── Fire all 3 calls sequentially (fills columns live) ───────────────────
    prompts = {
        "direct":        make_direct_prompt(problem["question"]),
        "zero_shot_cot": make_zero_shot_cot(problem["question"]),
        "few_shot_cot":  make_few_shot_cot(problem["question"], problem["few_shot_examples"]),
    }

    for key, label, color, _ in STRATEGIES:
        with output_slots[key]:
            with st.spinner(f"Running {label}..."):
                resp, usage = chat(
                    system="You are a helpful reasoning assistant.",
                    user=prompts[key],
                    max_tokens=500,
                    temperature=0.0,
                )
        responses[key] = resp

        with output_slots[key].container():
            st.markdown(resp)
            st.markdown(
                f"<div style='font-size:0.8em;color:#888;margin-top:6px;'>"
                f"⬆ {usage['input_tokens']} in | ⬇ {usage['output_tokens']} out"
                f"</div>",
                unsafe_allow_html=True,
            )

    # ── Judge all 3 ───────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Judge Evaluation")
    judge_cols = st.columns(3)

    for col, (key, label, color, _) in zip(judge_cols, STRATEGIES):
        with col:
            with st.spinner("Judging..."):
                raw_j, _ = chat(
                    system=JUDGE_SYSTEM,
                    user=JUDGE_PROMPT.format(
                        question=problem["question"],
                        answer=problem["answer"],
                        response=responses[key],
                    ),
                    max_tokens=150,
                    temperature=0.0,
                )
            try:
                clean = raw_j.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                j = json.loads(clean)
                correct = j.get("correct", False)
                rscore  = j.get("reasoning_score", 0)
                note    = j.get("note", "")
                st.markdown(
                    f"<div style='border:1px solid {color};border-radius:6px;padding:10px;'>"
                    f"<strong style='color:{color};'>{label}</strong><br>"
                    f"{'✅ Correct' if correct else '❌ Incorrect'}<br>"
                    f"Reasoning: {'★' * rscore}{'☆' * (5 - rscore)} {rscore}/5<br>"
                    f"<small>{note}</small>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            except (json.JSONDecodeError, KeyError):
                st.code(raw_j)

    # ── Prompt comparison ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("What was actually sent to Claude")
    p_cols = st.columns(3)
    for col, (key, label, color, _) in zip(p_cols, STRATEGIES):
        with col:
            with st.expander(f"{label} prompt"):
                st.code(prompts[key], language="text")

    st.subheader("What to observe")
    st.markdown(
        """
- **Did Direct get it right?** For easy problems it often does. For multi-step problems it frequently fails.
- **What did Zero-shot CoT add?** Look for "Let me think..." or numbered steps in the response. The model reasons *before* committing to an answer.
- **What did Few-shot CoT add over Zero-shot?** The examples install a *specific reasoning format* — the model mirrors the template, not just "some reasoning."
- **Token count:** Few-shot CoT has a much larger input (the examples are included). Is the quality gain worth the token cost?
- **For agentic systems:** The Planner component almost always uses CoT — decomposing a goal into steps IS chain-of-thought reasoning applied to planning.
"""
    )

# ── Reference ─────────────────────────────────────────────────────────────────

st.divider()
with st.expander("Why CoT works — the technical explanation"):
    st.markdown(
        """
An LLM generates tokens one at a time. When it answers directly, it must compress
all reasoning into the hidden state before the first output token.

When it reasons step-by-step, each reasoning token becomes part of the context
for the *next* token. The model effectively uses its output as working memory.

This is why CoT helps most on problems that require multiple reasoning steps
(arithmetic chains, logic puzzles, multi-constraint optimisation) and helps least
on factual lookups where no intermediate steps are needed.

**Zero-shot vs Few-shot CoT:**
- Zero-shot CoT (`think step by step`) activates a general reasoning mode
- Few-shot CoT installs a *specific reasoning template* — the model mirrors
  your examples' format and depth

In production agents, CoT is used selectively: always in the Planner,
often in the Evaluator, rarely in routing (where speed matters more than depth).
"""
    )
