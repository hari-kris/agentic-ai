"""
Hour 6 Lab — Zero-Shot vs Few-Shot + Task Decomposition
Module 2 | Prompt Fundamentals

Part A: Students write (or use pre-filled) zero-shot and few-shot classification
prompts. Both run on 10 customer feedback samples. Results appear in a comparison
table with consistency scores and disagreement highlighting.

Part B: A task decomposition pipeline where students can set the goal, edit the
planner prompt, and watch the plan execute step-by-step with context passing.

Run: streamlit run hour6_lab_zero_shot_vs_fewshot.py
"""

import re
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Zero-Shot vs Few-Shot", page_icon="⚗️", layout="wide")
st.title("⚗️ Hour 6 — Zero-Shot vs Few-Shot + Decomposition")
st.caption("Module 2 | Prompt Fundamentals")

tab_a, tab_b = st.tabs(["Part A — Zero-Shot vs Few-Shot", "Part B — Task Decomposition"])

# ═════════════════════════════════════════════════════════════════════════════
# PART A — ZERO-SHOT vs FEW-SHOT
# ═════════════════════════════════════════════════════════════════════════════

FEEDBACK_SAMPLES = [
    "The app is fantastic but I wish I could export data to CSV.",
    "Every time I try to log in from my phone it crashes immediately.",
    "This tool has genuinely changed how my team works. Thank you!",
    "It would be amazing if the dashboard could show weekly trends.",
    "The reports load slowly when there are more than 1000 rows.",
    "I love the clean interface. Very intuitive design.",
    "Dark mode would make this perfect for late-night working sessions.",
    "The search doesn't return results for special characters like # or @.",
    "Been using this for 2 years — still the best tool in this space.",
    "Notifications stopped working after the last update.",
]

VALID_LABELS = {"FEATURE_REQUEST", "BUG_REPORT", "GENERAL_PRAISE"}

DEFAULT_ZERO_SHOT = """\
Classify the following customer feedback into exactly one of these categories:
- FEATURE_REQUEST: The user wants a new feature or capability added
- BUG_REPORT: The user is reporting something broken or not working
- GENERAL_PRAISE: The user is expressing satisfaction without a specific request

Constraints:
- Return ONLY the category label. No explanation.
- If the feedback contains both a request and praise, classify by primary intent.

Feedback: {feedback}\
"""

DEFAULT_FEW_SHOT = """\
Classify customer feedback into: FEATURE_REQUEST, BUG_REPORT, or GENERAL_PRAISE.
Return ONLY the label.

Feedback: "I wish I could share dashboards with external clients."
Category: FEATURE_REQUEST

Feedback: "Would love a mobile app version of this."
Category: FEATURE_REQUEST

Feedback: "The sync button doesn't work when offline."
Category: BUG_REPORT

Feedback: "Files over 50MB cause the upload to fail silently."
Category: BUG_REPORT

Feedback: "Best project management tool I've used in 10 years."
Category: GENERAL_PRAISE

Feedback: "The customer support team is incredibly responsive."
Category: GENERAL_PRAISE

Feedback: {feedback}
Category:\
"""

def extract_label(text: str) -> str:
    text = text.strip().upper()
    for label in VALID_LABELS:
        if label in text:
            return label
    return "UNKNOWN"


with tab_a:
    st.markdown(
        """
The **same 10 feedback samples** are classified using two prompt strategies:
- **Zero-shot:** Instructions only. No examples. The model uses its own understanding.
- **Few-shot:** Instructions plus 6 worked examples. The model learns YOUR definition from the examples.

Observe where they agree and where they diverge — disagreements reveal ambiguous cases.
"""
    )
    st.divider()

    col_zs, col_fs = st.columns(2)

    with col_zs:
        st.markdown("**Zero-Shot Prompt Template**")
        st.caption("Instructions only — no examples. The `{feedback}` placeholder is replaced at runtime.")
        zs_prompt = st.text_area(
            "Zero-shot template:",
            value=DEFAULT_ZERO_SHOT,
            height=200,
            key="zs_prompt",
            label_visibility="collapsed",
        )
        if st.button("Reset to default", key="reset_zs"):
            st.session_state["zs_prompt"] = DEFAULT_ZERO_SHOT
            st.rerun()

    with col_fs:
        st.markdown("**Few-Shot Prompt Template**")
        st.caption("6 worked examples instill your definition. The `{feedback}` placeholder is at the end.")
        fs_prompt = st.text_area(
            "Few-shot template:",
            value=DEFAULT_FEW_SHOT,
            height=200,
            key="fs_prompt",
            label_visibility="collapsed",
        )
        if st.button("Reset to default", key="reset_fs"):
            st.session_state["fs_prompt"] = DEFAULT_FEW_SHOT
            st.rerun()

    st.divider()
    run_ab = st.button("▶  Run Both on All 10 Samples", type="primary")

    if run_ab:
        zs_results: list[str] = []
        fs_results: list[str] = []
        progress = st.progress(0, text="Starting...")

        for i, feedback in enumerate(FEEDBACK_SAMPLES):
            progress.progress((i * 2) / (len(FEEDBACK_SAMPLES) * 2), text=f"Zero-shot: sample {i+1}/10...")
            zs_raw, _ = chat(system="", user=zs_prompt.format(feedback=feedback), max_tokens=20, temperature=0.0)
            zs_results.append(extract_label(zs_raw))

            progress.progress((i * 2 + 1) / (len(FEEDBACK_SAMPLES) * 2), text=f"Few-shot: sample {i+1}/10...")
            fs_raw, _ = chat(system="", user=fs_prompt.format(feedback=feedback), max_tokens=20, temperature=0.0)
            fs_results.append(extract_label(fs_raw))

        progress.empty()

        # ── Results table ─────────────────────────────────────────────────────
        st.subheader("Results")

        LABEL_COLORS = {
            "FEATURE_REQUEST": "#1E88E5",
            "BUG_REPORT":      "#E53935",
            "GENERAL_PRAISE":  "#43A047",
            "UNKNOWN":         "#888",
        }

        table_rows = []
        disagreements = 0
        for i, (fb, zs, fs) in enumerate(zip(FEEDBACK_SAMPLES, zs_results, fs_results), 1):
            agree = zs == fs
            if not agree:
                disagreements += 1
            table_rows.append((i, fb, zs, fs, agree))

        # Render as HTML table for colour coding
        rows_html = ""
        for i, fb, zs, fs, agree in table_rows:
            zs_color = LABEL_COLORS.get(zs, "#888")
            fs_color = LABEL_COLORS.get(fs, "#888")
            bg = "#fffbe6" if not agree else "white"
            rows_html += (
                f"<tr style='background:{bg};'>"
                f"<td style='padding:6px;color:#555;'>{i}</td>"
                f"<td style='padding:6px;'>{fb[:60]}{'…' if len(fb) > 60 else ''}</td>"
                f"<td style='padding:6px;font-weight:bold;color:{zs_color};'>{zs}</td>"
                f"<td style='padding:6px;font-weight:bold;color:{fs_color};'>{fs}</td>"
                f"<td style='padding:6px;text-align:center;'>{'✅' if agree else '🔶'}</td>"
                f"</tr>"
            )

        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;font-size:0.9em;'>"
            f"<thead><tr style='background:#f0f0f0;'>"
            f"<th style='padding:6px;text-align:left;'>#</th>"
            f"<th style='padding:6px;text-align:left;'>Feedback</th>"
            f"<th style='padding:6px;text-align:left;'>Zero-Shot</th>"
            f"<th style='padding:6px;text-align:left;'>Few-Shot</th>"
            f"<th style='padding:6px;text-align:left;'>Agree?</th>"
            f"</tr></thead><tbody>{rows_html}</tbody></table>",
            unsafe_allow_html=True,
        )

        agreements = len(FEEDBACK_SAMPLES) - disagreements
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Agreements", f"{agreements}/10")
        c2.metric("Disagreements", f"{disagreements}/10", delta=f"{'🔶 ' if disagreements else ''}ambiguous cases")
        c3.metric("Consistency rate", f"{agreements*10}%")

        if disagreements:
            st.markdown(
                f"**{disagreements} disagreement{'s' if disagreements > 1 else ''} found.** "
                "These are the ambiguous samples — the ones where the prompt's *implicit* definition "
                "(zero-shot) differs from your *explicit* definition (few-shot). "
                "Few-shot examples are most valuable precisely at these boundaries."
            )


# ═════════════════════════════════════════════════════════════════════════════
# PART B — TASK DECOMPOSITION PIPELINE
# ═════════════════════════════════════════════════════════════════════════════

DEFAULT_PLANNER = """\
You are a strategic planning agent. Given a goal, produce a numbered list of
exactly 4 concrete, specific subtasks that, executed in sequence, will achieve the goal.

Rules for each subtask:
- Must begin with an action verb (Research, Identify, Compare, Analyse, Draft, Write, etc.)
- Must produce a specific, nameable output
- Must be executable by a language model from its training data
- Must build logically on the previous step

Return a numbered list of exactly 4 subtasks. No preamble, no commentary.\
"""

DEFAULT_EXECUTOR = """\
You are an executor agent running one step of a multi-step pipeline.
Execute the given subtask concisely and completely.
Do not plan — produce the actual output.
Maximum 200 words per step.\
"""

with tab_b:
    st.markdown(
        """
**Task decomposition** is the planning pattern at the heart of agentic systems.
A goal is broken into concrete subtasks, each executed in sequence with the prior
output passed as context.

Edit the Planner and Executor prompts, set your goal, and watch the pipeline run step-by-step.
"""
    )
    st.divider()

    bp_col, ep_col = st.columns(2)

    with bp_col:
        st.markdown("**Planner Prompt**")
        b_planner = st.text_area(
            "Planner:",
            value=DEFAULT_PLANNER,
            height=180,
            key="b_planner",
            label_visibility="collapsed",
        )
        if st.button("Reset", key="reset_planner"):
            st.session_state["b_planner"] = DEFAULT_PLANNER
            st.rerun()

    with ep_col:
        st.markdown("**Executor Prompt** *(shared across all steps)*")
        b_executor = st.text_area(
            "Executor:",
            value=DEFAULT_EXECUTOR,
            height=180,
            key="b_executor",
            label_visibility="collapsed",
        )
        if st.button("Reset", key="reset_executor"):
            st.session_state["b_executor"] = DEFAULT_EXECUTOR
            st.rerun()

    DECOMP_GOALS = [
        "Custom goal — type below",
        "Produce a competitive analysis of the top 3 project management tools for enterprise teams.",
        "Create a technical onboarding guide for a new backend engineer joining a Python/FastAPI team.",
        "Outline a content marketing strategy for a B2B SaaS product targeting HR professionals.",
        "Design a testing strategy for a REST API with authentication and CRUD endpoints.",
    ]
    selected_goal = st.selectbox("Example goals:", DECOMP_GOALS)
    decomp_goal = st.text_area(
        "Goal:",
        value="" if selected_goal == DECOMP_GOALS[0] else selected_goal,
        height=70,
        placeholder="Enter a goal for the agent to plan and execute...",
    )

    chain = st.checkbox("Pass prior step output as context to each subsequent step", value=True)
    run_decomp = st.button("▶  Run Decomposition Pipeline", type="primary", disabled=not decomp_goal.strip())

    if run_decomp and decomp_goal.strip():
        st.divider()

        # Step 1: Plan
        with st.container(border=True):
            st.markdown("<strong style='color:#8E24AA;'>🟣 PLANNER — LLM Call 1</strong>", unsafe_allow_html=True)
            with st.spinner("Planner generating subtasks..."):
                plan, p_usage = chat(
                    system=b_planner,
                    user=decomp_goal.strip(),
                    max_tokens=400,
                    temperature=0.3,
                )
            st.markdown("**Plan:**")
            st.markdown(plan)
            st.caption(f"⬆ {p_usage['input_tokens']} in | ⬇ {p_usage['output_tokens']} out")

        # Parse steps
        steps = re.findall(r'^\d+\.\s+(.+)$', plan, re.MULTILINE)
        if not steps:
            steps = [ln.strip() for ln in plan.split("\n") if ln.strip() and ln.strip()[0].isdigit()]

        with st.container(border=True):
            st.markdown(f"**⚙️ STATE** — Python parsed **{len(steps)}** subtasks (no LLM call)")

        # Step 2+: Execute
        prior_context = ""
        for i, step in enumerate(steps):
            with st.container(border=True):
                st.markdown(
                    f"<strong style='color:#00897B;'>🩵 EXECUTOR — LLM Call {i+2}</strong> "
                    f"<span style='color:#888;font-size:0.9em;'>| {step[:70]}{'…' if len(step) > 70 else ''}</span>",
                    unsafe_allow_html=True,
                )
                user_msg = step if not (chain and prior_context) else (
                    f"Context from previous steps:\n{prior_context}\n\nYour task: {step}"
                )
                with st.spinner(f"Executing step {i+1}..."):
                    output, e_usage = chat(
                        system=b_executor,
                        user=user_msg,
                        max_tokens=400,
                    )
                prior_context += f"\nStep {i+1}: {step}\n{output}\n"
                st.markdown(output)
                st.caption(
                    f"⬆ {e_usage['input_tokens']} in | ⬇ {e_usage['output_tokens']} out"
                    + ("  |  📎 includes prior context" if chain and i > 0 else "")
                )

        st.markdown(
            "> **Observe:** Each executor call receives the current step plus (optionally) all prior outputs. "
            "This is context accumulation — the same pattern you saw in the Context Window Inspector."
        )


# ── Reference ─────────────────────────────────────────────────────────────────

st.divider()
with st.expander("Zero-shot vs Few-shot — when to use each"):
    st.markdown(
        """
| Technique | When to use | Risk |
|---|---|---|
| **Zero-shot** | Well-defined categories with unambiguous meaning | Model uses its own definition of the labels |
| **Few-shot** | Ambiguous categories, domain-specific labels, strict output format | Examples must be representative — bad examples degrade performance |
| **Few-shot** | You need consistent output structure | Adding examples increases prompt token cost |

**The key insight:** Few-shot examples don't just help the model — they transfer *your* definition of the categories to the model. For domain-specific classification (e.g., internal ticket types), few-shot is almost always better.
"""
    )
