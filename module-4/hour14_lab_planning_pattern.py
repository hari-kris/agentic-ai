"""
Hour 14 Lab — Planning Pattern
Module 4 | Core Agentic Patterns I

A planner decomposes a goal into structured subtasks. This lab shows sequential planning,
parallel vs sequential comparison, and plan critique.

Run: streamlit run module-4/hour14_lab_planning_pattern.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 14 — Planning Pattern", page_icon="📋", layout="wide")
st.title("📋 Hour 14 — Planning Pattern")
st.caption("Module 4 | Core Agentic Patterns I")

st.markdown("""
The **Planning Pattern** separates *what to do* from *how to do it*.
A Planner agent takes a high-level goal and returns a structured task list.
Executor agents then carry out each task — often independently, sometimes in parallel.

This lab explores:
1. **Sequential planner** — produces a numbered task list with effort estimates
2. **Sequential vs parallel** — the same goal planned two ways; see the structural difference
3. **Plan critique** — a Critic reviews the plan for gaps and risks before any execution
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 14 Guide")
    st.markdown("""
**Sections in this lab:**
1. **Sequential planner** — 5-step plan with effort tags
2. **Parallel comparison** — same goal, parallel grouping shown
3. **Plan critique** — gaps and risks identified before execution

**What to observe:**
- The difference between a vague vs specific step description
- Which steps the planner marks as independent (parallel)
- What a plan critic catches that the planner missed
- Token cost of a planning + critique pair vs executing blindly
""")
    st.divider()
    st.markdown("**Experiment ideas:**")
    st.markdown("- Run the same goal in sequential and parallel mode and compare")
    st.markdown("- Try a very vague goal — does the plan quality drop?")
    st.markdown("- Run the plan critic and see if it catches real problems")
    st.divider()
    st.info("**Key principle:** A planner that cannot produce machine-readable JSON is unusable. Strict output format instructions are not optional.")

# ── System Prompts ─────────────────────────────────────────────────────────────
SEQUENTIAL_PLANNER_SYSTEM = """\
You are a planning agent. Given a goal, decompose it into exactly 5 concrete, specific,
actionable subtasks that together fully achieve the goal.

Rules:
- Each step must be independently executable
- Steps must be ordered from foundation to completion (each step may depend on the previous)
- Write step titles as imperative verbs (e.g. "Research competitors", "Draft the proposal")
- Step descriptions must be specific enough that someone could act on them without further clarification
- Estimate effort: low (under 30 minutes), medium (30–90 minutes), high (over 90 minutes)

Return ONLY valid JSON — no markdown fences, no commentary:
{
  "steps": [
    {"id": 1, "title": "...", "description": "...", "effort": "low|medium|high"},
    ...
  ],
  "rationale": "one sentence explaining the decomposition logic"
}\
"""

PARALLEL_PLANNER_SYSTEM = """\
You are a planning agent. Given a goal, decompose it into exactly 5 concrete, specific,
actionable subtasks and identify which ones can run in parallel.

Rules:
- Each step must be independently executable by a separate agent
- Identify parallel groups: steps with no dependency on each other can run simultaneously
- Write step titles as imperative verbs
- Step descriptions must be specific enough to act on without clarification
- Estimate effort: low (under 30 minutes), medium (30–90 minutes), high (over 90 minutes)

Return ONLY valid JSON — no markdown fences, no commentary:
{
  "steps": [
    {"id": 1, "title": "...", "description": "...", "effort": "low|medium|high"},
    ...
  ],
  "parallel_groups": [[1], [2, 3], [4, 5]],
  "rationale": "one sentence explaining which steps are independent and why"
}\
"""

PLAN_CRITIC_SYSTEM = """\
You are a plan quality auditor. Given a goal and a proposed plan, identify weaknesses.

Evaluate:
- Are any necessary steps missing?
- Are any steps too vague to execute?
- Are there risks or assumptions that could block execution?
- Is the ordering logical?

Return ONLY valid JSON — no markdown fences, no commentary:
{
  "gaps": ["missing step or coverage gap", ...],
  "risks": ["assumption or blocker that could fail", ...],
  "suggestion": "the single most important improvement to make to this plan"
}\
"""

# ── Helpers ────────────────────────────────────────────────────────────────────
EFFORT_COLOURS = {"low": "#43A047", "medium": "#FB8C00", "high": "#E53935"}
EFFORT_BG = {"low": "#E8F5E9", "medium": "#FFF3E0", "high": "#FFEBEE"}


def render_step_card(step: dict):
    effort = step.get("effort", "medium")
    color = EFFORT_COLOURS.get(effort, "#8E24AA")
    bg = EFFORT_BG.get(effort, "#F3E5F5")
    st.markdown(
        f"<div style='border-left:4px solid #8E24AA;background:#F3E5F5;"
        f"border-radius:6px;padding:12px 16px;margin:6px 0;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
        f"<strong style='color:#8E24AA;'>Step {step['id']}: {step['title']}</strong>"
        f"<span style='background:{color};color:white;padding:2px 8px;"
        f"border-radius:10px;font-size:0.78em;'>{effort}</span></div>"
        f"<div style='color:#555;font-size:0.9em;margin-top:6px;'>{step['description']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def parse_plan(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


# ── Section 1: Sequential Planner ─────────────────────────────────────────────
st.divider()
st.subheader("1 — Sequential Planner")

st.markdown("Enter a goal and the planner returns 5 ordered subtasks with effort estimates.")

GOAL_PRESETS = [
    "Custom goal — type below",
    "Launch a simple Python web API for a todo list app",
    "Conduct a user research study to understand customer pain points",
    "Set up a CI/CD pipeline for a new software project",
    "Write and publish a technical blog post about microservices",
    "Build a data dashboard showing weekly sales metrics",
]

sel1 = st.selectbox("Pick a preset goal or write your own:", GOAL_PRESETS, key="s1_preset")
goal1 = st.text_area(
    "Goal:",
    value="" if sel1 == GOAL_PRESETS[0] else sel1,
    placeholder="e.g. Create a marketing strategy for a new mobile app",
    height=70,
    key="s1_goal",
)

if st.button("▶ Generate Sequential Plan", type="primary", disabled=not goal1.strip()):
    with st.spinner("Planner generating plan…"):
        raw, usage = chat(SEQUENTIAL_PLANNER_SYSTEM, f"Goal: {goal1.strip()}", max_tokens=800, temperature=0.3)

    plan = parse_plan(raw)
    if not plan:
        st.error("Planner returned unexpected output. Showing raw:")
        st.code(raw)
        st.stop()

    st.session_state["s1_plan"] = plan
    st.session_state["s1_goal_val"] = goal1.strip()
    st.session_state["s1_usage"] = usage

if "s1_plan" in st.session_state:
    plan = st.session_state["s1_plan"]
    usage = st.session_state["s1_usage"]

    for step in plan.get("steps", []):
        render_step_card(step)

    st.info(f"**Planner rationale:** {plan.get('rationale', '')}")
    with st.expander("Raw JSON output"):
        st.code(json.dumps(plan, indent=2), language="json")

    c1, c2 = st.columns(2)
    c1.metric("Input tokens", usage["input_tokens"])
    c2.metric("Output tokens", usage["output_tokens"])

# ── Section 2: Sequential vs Parallel ─────────────────────────────────────────
st.divider()
st.subheader("2 — Sequential vs Parallel Planning")

st.markdown("""
The same goal planned in two ways. The **parallel planner** identifies which steps
have no dependency on each other and can run simultaneously — reducing wall-clock time
when executor agents are available.
""")

GOAL_PRESETS_2 = [
    "Custom goal — type below",
    "Analyse customer feedback from last quarter and produce an executive summary",
    "Migrate a PostgreSQL database to a new server",
    "Prepare a product demo for an investor meeting next week",
    "Audit the security of a web application",
]

sel2 = st.selectbox("Pick a preset goal:", GOAL_PRESETS_2, key="s2_preset")
goal2 = st.text_area(
    "Goal:",
    value="" if sel2 == GOAL_PRESETS_2[0] else sel2,
    placeholder="e.g. Build a competitor analysis report",
    height=70,
    key="s2_goal",
)

if st.button("▶ Compare Sequential vs Parallel", type="primary", disabled=not goal2.strip()):
    col_seq, col_par = st.columns(2)

    with col_seq:
        with st.spinner("Sequential planner…"):
            raw_seq, u_seq = chat(SEQUENTIAL_PLANNER_SYSTEM, f"Goal: {goal2.strip()}", max_tokens=800, temperature=0.3)
        plan_seq = parse_plan(raw_seq)

    with col_par:
        with st.spinner("Parallel planner…"):
            raw_par, u_par = chat(PARALLEL_PLANNER_SYSTEM, f"Goal: {goal2.strip()}", max_tokens=900, temperature=0.3)
        plan_par = parse_plan(raw_par)

    col_seq, col_par = st.columns(2)

    with col_seq:
        st.markdown(
            "<div style='border-top:4px solid #1E88E5;padding:4px 0 8px;'>"
            "<strong style='color:#1E88E5;'>🔵 Sequential Plan</strong></div>",
            unsafe_allow_html=True,
        )
        if plan_seq:
            for step in plan_seq.get("steps", []):
                render_step_card(step)
            st.caption(f"Rationale: {plan_seq.get('rationale', '')}")
        else:
            st.error("Parse error")
            st.code(raw_seq)

    with col_par:
        st.markdown(
            "<div style='border-top:4px solid #8E24AA;padding:4px 0 8px;'>"
            "<strong style='color:#8E24AA;'>🟣 Parallel Plan (with groups)</strong></div>",
            unsafe_allow_html=True,
        )
        if plan_par:
            groups = plan_par.get("parallel_groups", [])
            steps_by_id = {s["id"]: s for s in plan_par.get("steps", [])}

            for gi, group in enumerate(groups):
                if len(group) == 1:
                    step = steps_by_id.get(group[0])
                    if step:
                        render_step_card(step)
                else:
                    st.markdown(
                        f"<div style='border:2px dashed #8E24AA;border-radius:6px;"
                        f"padding:8px;margin:8px 0;background:#FAF0FF;'>"
                        f"<span style='font-size:0.78em;color:#8E24AA;'>⚡ Parallel group {gi + 1}</span></div>",
                        unsafe_allow_html=True,
                    )
                    for sid in group:
                        step = steps_by_id.get(sid)
                        if step:
                            render_step_card(step)

            st.caption(f"Rationale: {plan_par.get('rationale', '')}")
        else:
            st.error("Parse error")
            st.code(raw_par)

    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Seq input tokens", u_seq["input_tokens"])
    c2.metric("Seq output tokens", u_seq["output_tokens"])
    c3.metric("Par input tokens", u_par["input_tokens"])
    c4.metric("Par output tokens", u_par["output_tokens"])

# ── Section 3: Plan Critique ───────────────────────────────────────────────────
st.divider()
st.subheader("3 — Plan Critique")

st.markdown("""
A **Plan Critic** reviews the plan before execution begins — catching gaps, vague steps,
and hidden risks. This costs one extra API call but prevents executing a flawed plan.
""")

if "s1_plan" in st.session_state:
    st.info("Using the plan from Section 1. Run Section 1 first to populate it, or enter a goal below.")

GOAL_PRESETS_3 = [
    "Custom goal — type below",
    "Launch a simple Python web API for a todo list app",
    "Analyse customer feedback from last quarter and produce an executive summary",
    "Set up a CI/CD pipeline for a new software project",
]

sel3 = st.selectbox("Goal to plan and critique:", GOAL_PRESETS_3, key="s3_preset")
goal3 = st.text_area(
    "Goal:",
    value="" if sel3 == GOAL_PRESETS_3[0] else sel3,
    placeholder="e.g. Deploy a machine learning model to production",
    height=70,
    key="s3_goal",
)

if st.button("▶ Plan + Critique", type="primary", disabled=not goal3.strip()):
    with st.spinner("Planner generating plan…"):
        raw_plan, u_plan = chat(SEQUENTIAL_PLANNER_SYSTEM, f"Goal: {goal3.strip()}", max_tokens=800, temperature=0.3)
    plan3 = parse_plan(raw_plan)

    if not plan3:
        st.error("Planner returned unexpected output:")
        st.code(raw_plan)
        st.stop()

    critic_user = (
        f"Goal: {goal3.strip()}\n\n"
        f"Proposed plan:\n{json.dumps(plan3, indent=2)}"
    )
    with st.spinner("Critic reviewing plan…"):
        raw_crit, u_crit = chat(PLAN_CRITIC_SYSTEM, critic_user, max_tokens=400, temperature=0.2)

    try:
        clean = raw_crit.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        critique3 = json.loads(clean)
    except json.JSONDecodeError:
        critique3 = None

    left, right = st.columns([3, 2])

    with left:
        st.markdown("**📋 Generated Plan:**")
        for step in plan3.get("steps", []):
            render_step_card(step)
        st.caption(f"Rationale: {plan3.get('rationale', '')}")

    with right:
        st.markdown(
            "<div style='border-top:4px solid #E53935;padding:4px 0 8px;'>"
            "<strong style='color:#E53935;'>🔍 Plan Critique</strong></div>",
            unsafe_allow_html=True,
        )
        if critique3:
            gaps = critique3.get("gaps", [])
            risks = critique3.get("risks", [])
            suggestion = critique3.get("suggestion", "")

            if gaps:
                st.markdown("**Gaps identified:**")
                for g in gaps:
                    st.markdown(f"- {g}")
            else:
                st.success("No gaps found.")

            if risks:
                st.markdown("**Risks:**")
                for r in risks:
                    st.markdown(f"- ⚠️ {r}")
            else:
                st.success("No risks identified.")

            if suggestion:
                st.warning(f"**Top improvement:** {suggestion}")
        else:
            st.error("Critic parse error. Raw output:")
            st.code(raw_crit)

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM calls", 2)
    c2.metric("Total input tokens", u_plan["input_tokens"] + u_crit["input_tokens"])
    c3.metric("Total output tokens", u_plan["output_tokens"] + u_crit["output_tokens"])
