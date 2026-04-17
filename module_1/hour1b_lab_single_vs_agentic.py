"""
Hour 1B Lab — Single-Turn vs Agentic: Head-to-Head
Module 1 | Agentic AI Foundations

The same goal is handled two ways simultaneously:
  Left  — Single-Turn: one Claude call, direct answer, done.
  Right — Agentic:     Planner → Executor → Evaluator, filling in stage by stage.

A 4th Claude call then scores both outputs against the original goal so the
quality comparison is objective, not just visual.

Key insight: the agentic pipeline costs more (tokens, time, LLM calls) but
produces higher-quality, more structured output. Students see both empirically.

Run: streamlit run hour1b_lab_single_vs_agentic.py
"""

import time
import json
import streamlit as st
from claude_client import chat

st.set_page_config(
    page_title="Single-Turn vs Agentic",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Single-Turn vs Agentic")
st.caption("Hour 1B | Agentic AI Foundations")

st.markdown(
    """
The **same goal** is handled two ways. Watch both columns fill in, then compare the
objective quality scores at the bottom.

| | Single-Turn | Agentic Pipeline |
|---|---|---|
| LLM calls | 1 | 3 |
| Architecture | Prompt → Response | Planner → Executor → Evaluator |
| Cost | Low | Higher |
| Output | Immediate | Built across steps |
"""
)

st.divider()

# ── Prompts ───────────────────────────────────────────────────────────────────

SINGLE_TURN_SYSTEM = "You are a helpful assistant. Answer the user's request thoroughly and directly."

PLANNER_SYSTEM = (
    "You are a planning agent. Given a goal, return a numbered list of exactly 4 concrete, "
    "specific, actionable steps to achieve it. Each step must be unambiguous. "
    "Return ONLY the numbered list, one step per line, no preamble."
)

EXECUTOR_SYSTEM = (
    "You are an executor agent. You receive a specific task and carry it out immediately. "
    "Produce a concrete, detailed, useful output — do not plan, do not list further steps, "
    "just produce the actual result for this one task."
)

EVALUATOR_SYSTEM = (
    "You are a quality evaluator. You receive an original goal and two outputs that attempt "
    "to address it. Score each output from 1–10 against the goal on three dimensions: "
    "completeness, depth, and actionability. "
    "Return ONLY valid JSON (no markdown) in this exact format:\n"
    '{"single_turn": {"score": 7, "completeness": 6, "depth": 7, "actionability": 8, '
    '"strength": "one sentence", "weakness": "one sentence"}, '
    '"agentic": {"score": 9, "completeness": 9, "depth": 8, "actionability": 9, '
    '"strength": "one sentence", "weakness": "one sentence"}}'
)

# ── Goal input ────────────────────────────────────────────────────────────────

EXAMPLES = [
    "Custom goal — type below",
    "Write a summary of quantum computing for software developers who are new to the topic.",
    "Create a beginner's 30-day study plan for learning Python from scratch.",
    "Explain how to introduce AI tools into a 10-person marketing team.",
    "Describe the key differences between SQL and NoSQL databases for a non-technical manager.",
]

selected = st.selectbox("Choose an example goal:", EXAMPLES)
goal = st.text_area(
    "Goal (sent identically to both approaches):",
    value="" if selected == EXAMPLES[0] else selected,
    height=80,
    placeholder="Enter a goal or task...",
)

run = st.button("▶  Run Both", type="primary", disabled=not goal.strip())

# ── Side-by-side layout ───────────────────────────────────────────────────────

if run and goal.strip():

    left, right = st.columns(2)

    # Column headers
    with left:
        st.markdown(
            "<div style='border-top:4px solid #1E88E5;padding:8px 0 4px 0;'>"
            "<strong style='color:#1E88E5;font-size:1.1em;'>⚡ Single-Turn LLM</strong>"
            "<span style='float:right;font-size:0.85em;color:#888;'>1 LLM call</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        single_slot = st.empty()

    with right:
        st.markdown(
            "<div style='border-top:4px solid #43A047;padding:8px 0 4px 0;'>"
            "<strong style='color:#43A047;font-size:1.1em;'>🔄 Agentic Pipeline</strong>"
            "<span style='float:right;font-size:0.85em;color:#888;'>3 LLM calls</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        planner_slot  = st.empty()
        executor_slot = st.empty()
        evaluator_slot = st.empty()

    # ── Single-turn call ──────────────────────────────────────────────────────
    with single_slot:
        with st.spinner("Single-turn call in progress..."):
            t0 = time.perf_counter()
            single_response, single_usage = chat(
                system=SINGLE_TURN_SYSTEM,
                user=goal.strip(),
                max_tokens=600,
            )
            single_elapsed = time.perf_counter() - t0

    with single_slot.container():
        st.markdown(single_response)
        st.markdown(
            f"<div style='font-size:0.8em;color:#888;margin-top:6px;'>"
            f"⬆ {single_usage['input_tokens']} in &nbsp;|&nbsp; "
            f"⬇ {single_usage['output_tokens']} out &nbsp;|&nbsp; "
            f"⏱ {single_elapsed:.1f}s"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Agentic pipeline ──────────────────────────────────────────────────────
    # Stage 1: Planner
    with planner_slot:
        with st.spinner("🟣 Planner generating steps..."):
            t1 = time.perf_counter()
            plan, plan_usage = chat(
                system=PLANNER_SYSTEM,
                user=goal.strip(),
                max_tokens=400,
            )
            plan_elapsed = time.perf_counter() - t1

    with planner_slot.container():
        st.markdown(
            "<span style='color:#8E24AA;font-weight:bold;font-size:0.9em;'>🟣 PLANNER</span>",
            unsafe_allow_html=True,
        )
        st.markdown(plan)
        st.markdown(
            f"<div style='font-size:0.8em;color:#888;'>"
            f"⬆ {plan_usage['input_tokens']} in &nbsp;|&nbsp; "
            f"⬇ {plan_usage['output_tokens']} out &nbsp;|&nbsp; "
            f"⏱ {plan_elapsed:.1f}s"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Extract first step for the executor
    lines = [ln.strip() for ln in plan.split("\n") if ln.strip()]
    step1 = next(
        (ln for ln in lines if ln and (ln[0].isdigit() or ln.lower().startswith("step"))),
        lines[0] if lines else goal,
    )

    # Stage 2: Executor
    with executor_slot:
        with st.spinner("🩵 Executor running step 1..."):
            t2 = time.perf_counter()
            exec_response, exec_usage = chat(
                system=EXECUTOR_SYSTEM,
                user=step1,
                max_tokens=600,
            )
            exec_elapsed = time.perf_counter() - t2

    with executor_slot.container():
        st.markdown(
            "<span style='color:#00897B;font-weight:bold;font-size:0.9em;'>🩵 EXECUTOR</span>",
            unsafe_allow_html=True,
        )
        st.markdown(exec_response)
        st.markdown(
            f"<div style='font-size:0.8em;color:#888;'>"
            f"⬆ {exec_usage['input_tokens']} in &nbsp;|&nbsp; "
            f"⬇ {exec_usage['output_tokens']} out &nbsp;|&nbsp; "
            f"⏱ {exec_elapsed:.1f}s"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Stage 3: Evaluator (evaluates the executor output, not used for scoring yet)
    evaluator_prompt = (
        f"GOAL: {goal.strip()}\n\nOUTPUT TO EVALUATE:\n{exec_response}"
    )
    with evaluator_slot:
        with st.spinner("🔴 Evaluator reviewing..."):
            t3 = time.perf_counter()
            eval_response, eval_usage = chat(
                system=(
                    "You are a quality evaluator. Review the output against the goal. "
                    "Identify ONE specific, concrete improvement. Be brief."
                ),
                user=evaluator_prompt,
                max_tokens=200,
            )
            eval_elapsed = time.perf_counter() - t3

    with evaluator_slot.container():
        st.markdown(
            "<span style='color:#E53935;font-weight:bold;font-size:0.9em;'>🔴 EVALUATOR</span>",
            unsafe_allow_html=True,
        )
        st.info(eval_response)
        st.markdown(
            f"<div style='font-size:0.8em;color:#888;'>"
            f"⬆ {eval_usage['input_tokens']} in &nbsp;|&nbsp; "
            f"⬇ {eval_usage['output_tokens']} out &nbsp;|&nbsp; "
            f"⏱ {eval_elapsed:.1f}s"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Objective comparison ──────────────────────────────────────────────────
    st.divider()
    st.subheader("Objective Comparison")

    total_agentic_in  = plan_usage["input_tokens"]  + exec_usage["input_tokens"]  + eval_usage["input_tokens"]
    total_agentic_out = plan_usage["output_tokens"] + exec_usage["output_tokens"] + eval_usage["output_tokens"]
    total_elapsed = plan_elapsed + exec_elapsed + eval_elapsed

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("LLM calls — Single-Turn", 1)
    col2.metric("LLM calls — Agentic", 3, delta="+2 calls")
    col3.metric(
        "Tokens — Single-Turn",
        single_usage["input_tokens"] + single_usage["output_tokens"],
    )
    col4.metric(
        "Tokens — Agentic",
        total_agentic_in + total_agentic_out,
        delta=f"+{(total_agentic_in + total_agentic_out) - (single_usage['input_tokens'] + single_usage['output_tokens'])}",
    )

    col5, col6 = st.columns(2)
    col5.metric("Time — Single-Turn", f"{single_elapsed:.1f}s")
    col6.metric("Time — Agentic (sequential)", f"{total_elapsed:.1f}s", delta=f"+{total_elapsed - single_elapsed:.1f}s")

    # ── Dual quality scoring ──────────────────────────────────────────────────
    st.subheader("Quality Scores (objective — scored by Claude)")

    dual_user = (
        f"ORIGINAL GOAL:\n{goal.strip()}\n\n"
        f"OUTPUT A (Single-Turn):\n{single_response}\n\n"
        f"OUTPUT B (Agentic — executor step 1):\n{exec_response}"
    )

    with st.spinner("Scoring both outputs against the goal..."):
        raw_scores, _ = chat(
            system=EVALUATOR_SYSTEM,
            user=dual_user,
            max_tokens=400,
            temperature=0.1,
        )

    try:
        clean = raw_scores.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        scores = json.loads(clean)

        sc1, sc2 = st.columns(2)
        with sc1:
            s = scores["single_turn"]
            st.markdown(
                f"<div style='border-top:4px solid #1E88E5;padding:8px;background:#f9f9f9;border-radius:4px;'>"
                f"<strong style='color:#1E88E5;'>⚡ Single-Turn — Score: {s['score']}/10</strong><br>"
                f"Completeness: {s['completeness']}/10 &nbsp;|&nbsp; "
                f"Depth: {s['depth']}/10 &nbsp;|&nbsp; "
                f"Actionability: {s['actionability']}/10<br><br>"
                f"✅ {s['strength']}<br>⚠️ {s['weakness']}"
                f"</div>",
                unsafe_allow_html=True,
            )
        with sc2:
            a = scores["agentic"]
            st.markdown(
                f"<div style='border-top:4px solid #43A047;padding:8px;background:#f9f9f9;border-radius:4px;'>"
                f"<strong style='color:#43A047;'>🔄 Agentic — Score: {a['score']}/10</strong><br>"
                f"Completeness: {a['completeness']}/10 &nbsp;|&nbsp; "
                f"Depth: {a['depth']}/10 &nbsp;|&nbsp; "
                f"Actionability: {a['actionability']}/10<br><br>"
                f"✅ {a['strength']}<br>⚠️ {a['weakness']}"
                f"</div>",
                unsafe_allow_html=True,
            )
    except (json.JSONDecodeError, KeyError):
        st.warning("Could not parse quality scores. Raw response:")
        st.code(raw_scores)

    # ── Discussion ────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Discussion")
    st.markdown(
        """
- **When does the quality difference justify the cost?** For a one-off answer, probably not. For a task in a production workflow run thousands of times, maybe yes.
- **Notice the agentic right column didn't finish the whole task** — it executed only step 1 of the plan. A full agentic run would execute all 4 steps. What would the token cost look like then?
- **The evaluator at the bottom of the agentic column found one improvement** — in a real agent this would trigger a revision loop. The single-turn column has no such mechanism.
- **This is the trade-off at the heart of agentic AI:** more LLM calls, more tokens, more latency — in exchange for structured, iterative, self-improving output.
"""
    )
