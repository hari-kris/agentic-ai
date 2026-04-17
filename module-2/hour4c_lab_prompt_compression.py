"""
Hour 4C Lab — Prompt Compression Lab
Module 2 | Prompt Fundamentals

Start with a fully-structured 6-element prompt. Toggle each element off
one at a time. After each configuration, run the prompt and an LLM judge
scores the output quality (1–5 per criterion).

A history table and chart track: elements included → token count → quality.
Students discover the minimum viable prompt for their specific task.

Key insight: every removed element saves tokens but risks quality.
The optimal prompt is the shortest one that maintains acceptable quality.

Run: streamlit run hour4c_lab_prompt_compression.py
"""

import json
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Prompt Compression Lab", page_icon="🗜️", layout="wide")
st.title("🗜️ Hour 4C — Prompt Compression Lab")
st.caption("Module 2 | Prompt Fundamentals")

st.markdown(
    """
Start with a **fully-structured 6-element prompt**. Toggle elements off and re-run.
An LLM judge scores each version. The history chart reveals where quality degrades.

**The question:** Which elements are load-bearing? Which can you remove without losing quality?
"""
)

# ── Element definitions ───────────────────────────────────────────────────────

ELEMENTS = {
    "role": {
        "label": "① Role",
        "color": "#8E24AA",
        "default": (
            "You are an experienced engineering hiring manager at a fintech startup "
            "with 10 years of recruiting senior Python engineers."
        ),
    },
    "task": {
        "label": "② Task",
        "color": "#1E88E5",
        "default": (
            "Write a job description for a Senior Python Engineer position."
        ),
    },
    "context": {
        "label": "③ Context",
        "color": "#43A047",
        "default": (
            "The company is a 3-year-old fintech startup with 50 engineers. "
            "The stack is Python 3.11, FastAPI, PostgreSQL, Redis, AWS. "
            "The team works in 2-week sprints. "
            "The role reports to the Head of Engineering."
        ),
    },
    "constraints": {
        "label": "④ Constraints",
        "color": "#FB8C00",
        "default": (
            "Use inclusive, gender-neutral language. "
            "Total length: 200–300 words. "
            "Do not mention salary. "
            "Avoid buzzwords like 'rockstar', 'ninja', 'unicorn'."
        ),
    },
    "output_format": {
        "label": "⑤ Output Format",
        "color": "#00897B",
        "default": (
            "Structure the description with these exact sections:\n"
            "1. About the Role (1 short paragraph)\n"
            "2. What You'll Do (4–5 bullet points)\n"
            "3. What We're Looking For (4–5 bullet points)\n"
            "4. Nice to Have (2–3 bullet points)"
        ),
    },
    "examples": {
        "label": "⑥ Examples",
        "color": "#E53935",
        "default": (
            "Example of a good bullet point:\n"
            "✓ 'Design and own end-to-end features across the full stack, from API design to database schema'\n"
            "Example of a bad bullet point:\n"
            "✗ 'Work on interesting technical challenges in a fast-paced environment'"
        ),
    },
}

JUDGE_SYSTEM = "You are a strict hiring content evaluator. Score objectively."
JUDGE_PROMPT = """\
Evaluate this job description for a Senior Python Engineer role.

Score each criterion 1–5:
1. specificity: Does it use concrete details (tech stack, team size, role level)?
   1=generic boilerplate, 5=specific to this company and role
2. structure: Is it clearly organised into distinct sections?
   1=wall of text, 5=perfectly structured and scannable
3. actionability: Do the bullet points describe real work, not vague attributes?
   1=vague adjectives, 5=concrete, ownable tasks

Return ONLY valid JSON:
{{"specificity": 0, "structure": 0, "actionability": 0, "total": 0, "note": "one sentence"}}\

Job description:
{output}\
"""

CRITERIA = ["specificity", "structure", "actionability"]
CRITERIA_ICONS = {"specificity": "🎯", "structure": "📐", "actionability": "⚡"}

# ── Session state: history ────────────────────────────────────────────────────

if "compression_history" not in st.session_state:
    st.session_state.compression_history = []

# ── Sidebar: toggles ──────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Element Toggles")
    st.caption("Turn off elements to compress the prompt. Re-run after each change.")
    active: dict[str, bool] = {}
    for key, meta in ELEMENTS.items():
        active[key] = st.checkbox(
            meta["label"],
            value=True,
            key=f"active_{key}",
        )
    st.divider()
    elements_on = sum(active.values())
    st.metric("Elements active", f"{elements_on} / 6")
    if st.button("🔄 Reset history"):
        st.session_state.compression_history = []
        st.rerun()

# ── Build prompt preview ──────────────────────────────────────────────────────

st.subheader("Current prompt preview")

parts = []
for key, meta in ELEMENTS.items():
    if active[key]:
        parts.append(f"[{meta['label'].split(' ', 1)[1].upper()}]\n{meta['default']}")

assembled = "\n\n".join(parts) if parts else "(all elements disabled)"
token_estimate = len(assembled.split()) * 1.3  # rough estimate

col_prev, col_stats = st.columns([3, 1])
with col_prev:
    st.code(assembled, language="text")
with col_stats:
    st.metric("Elements active", f"{elements_on} / 6")
    st.metric("~Token estimate", f"~{int(token_estimate)}")
    active_labels = [ELEMENTS[k]["label"] for k, v in active.items() if v]
    missing_labels = [ELEMENTS[k]["label"] for k, v in active.items() if not v]
    if missing_labels:
        st.caption(f"**Removed:** {', '.join(missing_labels)}")

st.divider()
run = st.button("▶  Run This Version + Score It", type="primary", disabled=not any(active.values()))

# ── Run and judge ─────────────────────────────────────────────────────────────

if run and any(active.values()):
    with st.spinner("Running prompt..."):
        output, usage = chat(
            system="You are a helpful writing assistant.",
            user=assembled,
            max_tokens=600,
            temperature=0.5,
        )

    with st.spinner("Judge scoring..."):
        raw_j, _ = chat(
            system=JUDGE_SYSTEM,
            user=JUDGE_PROMPT.format(output=output),
            max_tokens=200,
            temperature=0.0,
        )

    scores = None
    try:
        clean = raw_j.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        start, end = clean.find("{"), clean.rfind("}") + 1
        scores = json.loads(clean[start:end])
    except (json.JSONDecodeError, ValueError):
        st.warning("Judge parse error — raw response shown below.")
        st.code(raw_j)

    if scores:
        total = scores.get("total", sum(scores.get(c, 0) for c in CRITERIA))

        # Show output + scores side by side
        out_col, score_col = st.columns([3, 1])
        with out_col:
            st.markdown("**Output:**")
            st.markdown(output)
        with score_col:
            st.markdown("**Scores:**")
            for crit in CRITERIA:
                val = scores.get(crit, 0)
                icon = CRITERIA_ICONS[crit]
                color = "#43A047" if val >= 4 else ("#FB8C00" if val >= 3 else "#E53935")
                st.markdown(
                    f"<div style='padding:6px;margin-bottom:6px;border-radius:4px;"
                    f"background:{'#e8f5e9' if val >= 4 else '#fff3e0' if val >= 3 else '#ffebee'};'>"
                    f"{icon} **{crit.replace('_',' ').title()}**<br>"
                    f"<span style='font-size:1.3em;color:{color};font-weight:bold;'>{val}/5</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.metric("Total", f"{total}/15")
            st.caption(scores.get("note", ""))

        # Save to history
        st.session_state.compression_history.append({
            "elements": elements_on,
            "active_labels": active_labels[:],
            "token_est": int(token_estimate),
            "specificity": scores.get("specificity", 0),
            "structure":   scores.get("structure",   0),
            "actionability": scores.get("actionability", 0),
            "total": total,
            "usage_in": usage["input_tokens"],
        })
        st.caption(f"⬆ {usage['input_tokens']} input tokens (actual API count)")

# ── History table and chart ───────────────────────────────────────────────────

if st.session_state.compression_history:
    st.divider()
    st.subheader("Compression History")
    st.caption("Each row = one run. Toggle elements and re-run to add more rows.")

    import pandas as pd
    hist = st.session_state.compression_history

    df = pd.DataFrame([
        {
            "Run": i + 1,
            "Elements": h["elements"],
            "Active": ", ".join(h["active_labels"]),
            "Input Tokens": h["usage_in"],
            "Specificity": h["specificity"],
            "Structure":   h["structure"],
            "Actionability": h["actionability"],
            "Total /15": h["total"],
        }
        for i, h in enumerate(hist)
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

    if len(hist) >= 2:
        st.subheader("Quality vs Compression")
        chart_df = pd.DataFrame({
            "Total Score (/15)":  [h["total"]    for h in hist],
            "Input Tokens":       [h["usage_in"] for h in hist],
        }, index=[f"Run {i+1} ({h['elements']}el)" for i, h in enumerate(hist)])

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.markdown("**Score across runs**")
            st.line_chart(chart_df["Total Score (/15)"], color="#1E88E5", y_label="Score /15")
        with col_chart2:
            st.markdown("**Token count across runs**")
            st.line_chart(chart_df["Input Tokens"], color="#E53935", y_label="Input Tokens")

        # Find quality cliff
        scores_list = [h["total"] for h in hist]
        if len(scores_list) >= 2:
            best_score = max(scores_list)
            threshold = best_score * 0.8
            viable = [h for h in hist if h["total"] >= threshold]
            if viable:
                min_token_viable = min(viable, key=lambda h: h["usage_in"])
                st.success(
                    f"**Minimum viable configuration (≥80% of peak quality):** "
                    f"{min_token_viable['elements']} elements active "
                    f"({min_token_viable['usage_in']} input tokens, "
                    f"score {min_token_viable['total']}/15)"
                )

# ── Suggested experiment sequence ─────────────────────────────────────────────

st.divider()
st.subheader("Suggested experiment sequence")
st.markdown(
    """
Run these versions in order to build your compression curve:

| Step | Elements active | What you're testing |
|---|---|---|
| 1 | All 6 | Baseline — maximum quality |
| 2 | Remove ⑥ Examples | Does removing examples hurt quality? |
| 3 | Remove ① Role | Does the model know how to write JDs without being told who it is? |
| 4 | Remove ③ Context | Without company context, how generic does it get? |
| 5 | Remove ④ Constraints | Without constraints, does length/language drift? |
| 6 | Remove ⑤ Output Format | Without structure, does it still produce sections? |
| 7 | Task only | Absolute minimum — what does the model produce with zero guidance? |

The point where quality drops sharply is the **load-bearing element** for this task.
"""
)

# ── Reference ─────────────────────────────────────────────────────────────────

st.divider()
with st.expander("Prompt compression in agentic systems — why it matters"):
    st.markdown(
        """
In a multi-step agentic pipeline, prompt tokens are paid **on every call**.
A 10-step pipeline with a 2,000-token system prompt costs 20,000 input tokens
per run — before any user input or tool results.

**Practical compression strategies:**

| Element | Compressible? | How |
|---|---|---|
| Role | Often | 1 sentence instead of 3; role is implicit if the task is clear |
| Task | Never | The task is the prompt |
| Context | Sometimes | Include only what changes the output; test without |
| Constraints | Mostly | Keep only what the model violates without them |
| Output Format | Rarely | Format instructions prevent parse failures — always worth the tokens |
| Examples | Sometimes | Use 1 example instead of 3; remove if zero-shot works |

**The rule:** Run the compression lab for every prompt in your pipeline.
Remove each element, test quality, restore if quality drops.
The minimum viable prompt is the right prompt.
"""
    )
