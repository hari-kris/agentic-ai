"""
Hour 4 Lab — Prompt Anatomy Workshop
Module 2 | Prompt Fundamentals

Students pick a broken prompt, see which of the 6 elements are missing,
fill in each element interactively, then compare broken vs structured output
side-by-side. An LLM judge scores the structured prompt on all 6 dimensions.

The 6-element framework:
  ① ROLE          — who the model is
  ② TASK          — what to do (action verb)
  ③ CONTEXT       — background the model needs
  ④ CONSTRAINTS   — what to/not to do
  ⑤ OUTPUT FORMAT — exact shape of the response
  ⑥ EXAMPLES      — show, don't tell (optional but powerful)

Run: streamlit run hour4_lab_prompt_anatomy.py
"""

import json
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Prompt Anatomy Workshop", page_icon="🔬", layout="wide")
st.title("🔬 Hour 4 — Prompt Anatomy Workshop")
st.caption("Module 2 | Prompt Fundamentals")

st.markdown(
    "Every effective prompt is built from **six elements**. "
    "Diagnose what's missing from a broken prompt, rebuild it element by element, "
    "then compare the outputs side-by-side."
)

# ── Element metadata ──────────────────────────────────────────────────────────

ELEMENTS = [
    ("role",          "① Role",          "#8E24AA", "Who the model is pretending to be"),
    ("task",          "② Task",          "#1E88E5", "What it must do (starts with an action verb)"),
    ("context",       "③ Context",       "#43A047", "Background it needs that it can't assume"),
    ("constraints",   "④ Constraints",   "#FB8C00", "What it must or must not do"),
    ("output_format", "⑤ Output Format", "#00897B", "The exact shape of the expected response"),
    ("examples",      "⑥ Examples",      "#E53935", "Show, don't tell — at least one worked example"),
]

# ── Broken prompt examples ────────────────────────────────────────────────────

BROKEN_PROMPTS = {
    "Tell me about machine learning.": {
        "missing": ["role", "context", "constraints", "output_format"],
        "hint": "Audience? What aspect of ML? Length? Format?",
    },
    "Summarise this document.": {
        "missing": ["role", "context", "constraints", "output_format"],
        "hint": "There's no document! Context is missing completely.",
    },
    "Write some Python code.": {
        "missing": ["role", "task", "context", "constraints", "output_format"],
        "hint": "Code for what? What language version? What style? What does it return?",
    },
    "Give me feedback on my writing.": {
        "missing": ["role", "context", "constraints", "output_format"],
        "hint": "What writing? What kind of feedback? How harsh? What format?",
    },
}

JUDGE_SYSTEM = """\
You are a strict prompt engineering expert. Evaluate prompts against the 6-element framework.
Be precise — partial credit only when an element is genuinely present but weak.\
"""

JUDGE_PROMPT = """\
Evaluate this prompt against the six-element framework.

Score each element: 1 = present and strong, 0.5 = present but weak, 0 = missing.

Elements:
1. role: Does it specify who the model is?
2. task: Does it begin with a clear action verb?
3. context: Does it provide necessary background or input data?
4. constraints: Does it specify what to or not to do?
5. output_format: Does it specify the shape/format of the response?
6. examples: Does it include at least one worked example?

Prompt to evaluate:
{prompt}

Return ONLY valid JSON (no markdown):
{{"role": 0, "task": 0, "context": 0, "constraints": 0, "output_format": 0, "examples": 0,
  "total": 0.0, "feedback": "one sentence of specific improvement advice"}}\
"""

# ── UI ────────────────────────────────────────────────────────────────────────

st.divider()

selected_broken = st.selectbox(
    "Choose a broken prompt to fix:",
    list(BROKEN_PROMPTS.keys()),
)
broken_info = BROKEN_PROMPTS[selected_broken]

# Show the broken prompt with missing-element badges
st.markdown(f"**Broken prompt:** `{selected_broken}`")
st.caption(f"💡 Hint: {broken_info['hint']}")

badge_cols = st.columns(6)
for col, (key, label, color, _) in zip(badge_cols, ELEMENTS):
    with col:
        is_missing = key in broken_info["missing"]
        bg    = "#eee" if is_missing else color
        fg    = "#999" if is_missing else "white"
        icon  = "❌" if is_missing else "✅"
        st.markdown(
            f"<div style='text-align:center;padding:4px 6px;border-radius:4px;"
            f"background:{bg};color:{fg};"
            f"font-size:0.8em;border:1px solid {color};'>"
            f"{icon} {label}</div>",
            unsafe_allow_html=True,
        )

st.divider()

# ── 6-element builder ─────────────────────────────────────────────────────────

st.subheader("Build the structured prompt")
st.caption("Fill in as many elements as possible. At minimum: Role, Task, Context, Constraints, and Output Format.")

filled: dict[str, str] = {}

cols_a = st.columns(2)
cols_b = st.columns(2)
cols_c = st.columns(2)
col_pairs = [cols_a, cols_b, cols_c]

for i, (key, label, color, description) in enumerate(ELEMENTS):
    col = col_pairs[i // 2][i % 2]
    with col:
        st.markdown(
            f"<span style='color:{color};font-weight:bold;'>{label}</span> "
            f"<span style='color:#888;font-size:0.85em;'>— {description}</span>",
            unsafe_allow_html=True,
        )
        val = st.text_area(
            label,
            key=f"elem_{key}",
            height=90,
            placeholder=f"Enter the {label.split(' ', 1)[1].lower()} here...",
            label_visibility="collapsed",
        )
        filled[key] = val.strip()

# ── Live preview ──────────────────────────────────────────────────────────────

st.divider()

elements_filled = sum(1 for v in filled.values() if v)
st.progress(elements_filled / 6, text=f"Elements filled: {elements_filled} / 6")

assembled_parts = []
for key, label, color, _ in ELEMENTS:
    if filled.get(key):
        assembled_parts.append(f"[{label.split(' ', 1)[1].upper()}]\n{filled[key]}")

assembled_prompt = "\n\n".join(assembled_parts) if assembled_parts else "(fill in at least one element above)"

with st.expander("Preview assembled prompt", expanded=elements_filled >= 3):
    st.code(assembled_prompt, language="text")

# ── Comparison ────────────────────────────────────────────────────────────────

st.divider()
compare_disabled = elements_filled < 3

if compare_disabled:
    st.info("Fill in at least 3 elements to enable comparison.")

col_run, col_score = st.columns([2, 1])
run_comparison = col_run.button("▶  Compare: Broken vs Structured", type="primary", disabled=compare_disabled)
run_score      = col_score.button("🧑‍⚖️  Score My Prompt", disabled=compare_disabled)

if run_comparison:
    left, right = st.columns(2)

    with left:
        st.markdown(
            "<div style='border-top:4px solid #E53935;padding:6px 0;'>"
            "<strong style='color:#E53935;'>🔴 Broken Prompt Output</strong></div>",
            unsafe_allow_html=True,
        )
        with st.spinner("Running broken prompt..."):
            broken_out, broken_usage = chat(
                system="You are a helpful assistant.",
                user=selected_broken,
                max_tokens=500,
                temperature=0.7,
            )
        st.markdown(broken_out)
        st.caption(f"⬆ {broken_usage['input_tokens']} in | ⬇ {broken_usage['output_tokens']} out")

    with right:
        st.markdown(
            "<div style='border-top:4px solid #43A047;padding:6px 0;'>"
            "<strong style='color:#43A047;'>🟢 Structured Prompt Output</strong></div>",
            unsafe_allow_html=True,
        )
        with st.spinner("Running structured prompt..."):
            struct_out, struct_usage = chat(
                system="You are a helpful assistant.",
                user=assembled_prompt,
                max_tokens=700,
                temperature=0.7,
            )
        st.markdown(struct_out)
        st.caption(f"⬆ {struct_usage['input_tokens']} in | ⬇ {struct_usage['output_tokens']} out")

    st.markdown(
        "> **Observe:** The structured prompt gives a longer system prompt but produces a more "
        "targeted, actionable response. The extra tokens in the prompt pay for themselves in output quality."
    )

if run_score:
    with st.spinner("LLM Judge scoring your prompt..."):
        raw, _ = chat(
            system=JUDGE_SYSTEM,
            user=JUDGE_PROMPT.format(prompt=assembled_prompt),
            max_tokens=400,
            temperature=0.1,
        )

    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        scores = json.loads(clean)

        st.subheader("LLM Judge Score")
        total = scores.get("total", 0)
        st.progress(total / 6, text=f"Total score: {total:.1f} / 6")

        score_cols = st.columns(6)
        for col, (key, label, color, _) in zip(score_cols, ELEMENTS):
            val = scores.get(key, 0)
            icon = "✅" if val >= 1 else ("⚡" if val == 0.5 else "❌")
            col.metric(label.split(" ", 1)[1], f"{icon} {val}")

        st.info(f"💬 {scores.get('feedback', '')}")
    except (json.JSONDecodeError, KeyError):
        st.warning("Could not parse judge output. Raw response:")
        st.code(raw)

# ── Reference ─────────────────────────────────────────────────────────────────

st.divider()
with st.expander("6-element framework — quick reference"):
    st.markdown(
        """
| Element | Question it answers | Example |
|---|---|---|
| ① Role | Who are you? | "You are a senior Python engineer..." |
| ② Task | What must you do? | "Review this function for bugs and anti-patterns." |
| ③ Context | What do you need to know? | "The codebase uses Python 3.11, follows PEP8..." |
| ④ Constraints | What are the rules? | "Do not suggest external libraries. Max 200 words." |
| ⑤ Output Format | What should the response look like? | "Return a JSON list with {issue, severity, fix}." |
| ⑥ Examples | What does good look like? | "Example: {issue: 'bare except', severity: 'high', fix: '...'}" |

The most commonly missing elements in real prompts are **constraints** and **output format** —
these are what prevent the model from writing a 500-word essay when you wanted a bullet list.
"""
    )
