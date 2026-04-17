"""
Hour 3 Lab — Your First Agentic Pipeline
Module 1 | Agentic AI Foundations

A visible two-step agentic pipeline: Planner → (State parse) → Executor.
Each LLM call is shown as a labelled, bordered block so students can see
exactly how state flows between components.

Exercises (controlled via the sidebar):
  Ex 1 — Run as-is: observe 2 separate LLM calls
  Ex 2 — Set "Steps to execute" to 2: adds a third LLM call, passes context
  Ex 3 — Enable Evaluator: adds a fourth LLM call that critiques the output

Run: streamlit run hour3_lab_agentic_pipeline.py
"""

import streamlit as st
from claude_client import chat

st.set_page_config(
    page_title="Hour 3 — Agentic Pipeline",
    page_icon="⚙️",
    layout="wide",
)
st.title("Hour 3 Lab — Your First Agentic Pipeline")
st.caption("Module 1 | Agentic AI Foundations")

st.markdown(
    """
This lab runs a minimal agentic pipeline with Claude:

1. **[PLANNER]** — LLM call 1: generates a numbered plan from your goal
2. **[STATE]** — Python parses the plan (no LLM call)
3. **[EXECUTOR]** — LLM call 2+: executes step(s) from the plan
4. **[EVALUATOR]** — optional LLM call: critiques the final output *(Exercise 3)*
"""
)

# ── Prompts ──────────────────────────────────────────────────────────────────

PLANNER_SYSTEM = """\
You are a planning agent. Given a goal, return a numbered list of exactly 4 concrete,
specific, actionable steps to achieve it. Each step must be unambiguous — someone
could carry it out without further clarification.
Return ONLY the numbered list, one step per line, no preamble.\
"""

EXECUTOR_SYSTEM = """\
You are an executor agent. You receive a specific task and carry it out immediately.
Produce a concrete, detailed, useful output — do not plan, do not list further steps,
just produce the actual result for this one task.\
"""

EVALUATOR_SYSTEM = """\
You are a quality evaluator. You receive an original goal and the output produced by
an executor agent. Identify ONE specific, concrete improvement that would make the
output better serve the goal. Be brief and precise — one short paragraph maximum.\
"""

# ── Sidebar: exercise controls ────────────────────────────────────────────────

with st.sidebar:
    st.header("Exercise Controls")
    execute_steps = st.slider(
        "Steps to execute (Ex 1 = 1, Ex 2 = 2)",
        min_value=1,
        max_value=3,
        value=1,
        help="Exercise 2: increase to 2 to add a second executor call with context passing.",
    )
    use_evaluator = st.checkbox(
        "Add Evaluator — Exercise 3",
        value=False,
        help="Adds a third LLM call that critiques the final executor output.",
    )
    st.divider()
    st.markdown("**What to observe:**")
    st.markdown("- Each coloured block = one component")
    st.markdown("- Each spinner = one live LLM call")
    st.markdown("- State passes *between* blocks as plain text")
    st.markdown("- Token counters show the real cost of each call")

# ── Goal input ────────────────────────────────────────────────────────────────

EXAMPLE_GOALS = [
    "Custom goal — type below",
    "Research and write a 3-paragraph summary of quantum computing for developers new to the topic.",
    "Create a beginner's 30-day study plan for learning Python from scratch.",
    "Draft a proposal for introducing AI productivity tools into a 10-person marketing team.",
    "Outline a unit-testing strategy for a REST API with authentication and CRUD endpoints.",
]

selected = st.selectbox("Choose an example goal:", EXAMPLE_GOALS)
goal = st.text_area(
    "Goal:",
    value="" if selected == EXAMPLE_GOALS[0] else selected,
    height=80,
    placeholder="Describe a goal for the agent to plan and execute...",
)

run = st.button("Run Pipeline", type="primary", disabled=not goal.strip())

# ── Pipeline ──────────────────────────────────────────────────────────────────

if run and goal.strip():

    total_in, total_out, llm_call_count = 0, 0, 0

    # ── PLANNER ──────────────────────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("### 🟣 \[PLANNER\] — LLM Call 1")
        st.caption("System prompt instructs Claude to plan, not act.")

        with st.expander("System prompt"):
            st.code(PLANNER_SYSTEM, language="text")

        with st.spinner("Planner generating steps..."):
            plan, u1 = chat(PLANNER_SYSTEM, goal.strip())

        llm_call_count += 1
        total_in += u1["input_tokens"]
        total_out += u1["output_tokens"]

        st.markdown("**Plan:**")
        st.markdown(plan)
        c1, c2 = st.columns(2)
        c1.metric("Input tokens", u1["input_tokens"])
        c2.metric("Output tokens", u1["output_tokens"])

    # ── STATE PARSING ─────────────────────────────────────────────────────────
    lines = [ln.strip() for ln in plan.split("\n") if ln.strip()]
    steps = [ln for ln in lines if ln and (ln[0].isdigit() or ln.lower().startswith("step"))]
    if not steps:
        steps = lines  # fallback: use all non-empty lines

    with st.container(border=True):
        st.markdown("### ⚙️ \[STATE\] — Python parses the plan")
        st.caption("No LLM call. Plain Python extracts step text to pass to the executor.")
        st.markdown(f"Found **{len(steps)}** steps. Will execute **{min(execute_steps, len(steps))}**.")

    # ── EXECUTOR(S) ───────────────────────────────────────────────────────────
    executor_outputs: list[str] = []

    for i in range(min(execute_steps, len(steps))):
        step_text = steps[i]

        with st.container(border=True):
            st.markdown(f"### 🟢 \[EXECUTOR\] — LLM Call {i + 2}")
            st.caption(f"Executing: *{step_text}*")

            with st.expander("System prompt"):
                st.code(EXECUTOR_SYSTEM, language="text")

            # Pass prior output as context for step 2+
            user_msg = step_text
            if i > 0 and executor_outputs:
                user_msg = (
                    f"Context from the previous step:\n{executor_outputs[-1]}\n\n"
                    f"Now execute this step: {step_text}"
                )
                st.caption("Context from the previous step is included in this call.")

            with st.spinner(f"Executor running step {i + 1}..."):
                output, u2 = chat(EXECUTOR_SYSTEM, user_msg, max_tokens=1200)

            executor_outputs.append(output)
            llm_call_count += 1
            total_in += u2["input_tokens"]
            total_out += u2["output_tokens"]

            st.markdown("**Output:**")
            st.markdown(output)
            c1, c2 = st.columns(2)
            c1.metric("Input tokens", u2["input_tokens"])
            c2.metric("Output tokens", u2["output_tokens"])

    # ── EVALUATOR (Exercise 3) ────────────────────────────────────────────────
    if use_evaluator and executor_outputs:
        final_output = executor_outputs[-1]
        eval_msg = f"ORIGINAL GOAL:\n{goal.strip()}\n\nOUTPUT TO EVALUATE:\n{final_output}"

        with st.container(border=True):
            st.markdown("### 🔴 \[EVALUATOR\] — Exercise 3")
            st.caption("Reviews the final executor output against the original goal.")

            with st.expander("System prompt"):
                st.code(EVALUATOR_SYSTEM, language="text")

            with st.spinner("Evaluator reviewing output..."):
                critique, u3 = chat(EVALUATOR_SYSTEM, eval_msg, max_tokens=400)

            llm_call_count += 1
            total_in += u3["input_tokens"]
            total_out += u3["output_tokens"]

            st.markdown("**Improvement suggestion:**")
            st.info(critique)
            c1, c2 = st.columns(2)
            c1.metric("Input tokens", u3["input_tokens"])
            c2.metric("Output tokens", u3["output_tokens"])

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Pipeline Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total LLM calls", llm_call_count)
    c2.metric("Total input tokens", total_in)
    c3.metric("Total output tokens", total_out)

    st.markdown(
        "> **Key observation:** each coloured block is one component. "
        "The data flowing between blocks is *state*. "
        "This pattern — Planner → State → Executor → Evaluator — "
        "is the kernel that every agentic framework (LangChain, LangGraph, CrewAI) builds on."
    )
