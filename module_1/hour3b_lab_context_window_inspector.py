"""
Hour 3B Lab — Context Window Inspector: Memory Made Visible
Module 1 | Agentic AI Foundations

Runs the same 3-step pipeline as Hour 3, but exposes the exact messages array
sent to Claude at every step. Students can see short-term memory (the context
window) as a scrollable JSON object, watch the fill bar grow, and toggle between
"Isolated calls" (each step is fresh) vs "Chain context" (each step receives all
prior outputs).

Key insight: short-term memory IS the messages list. It is not abstract.
It is a Python list of dicts that grows with every step.

Run: streamlit run hour3b_lab_context_window_inspector.py
"""

import os
import json
import time
import anthropic
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"
CONTEXT_WINDOW_LIMIT = 200_000  # Claude's context window (tokens)

# ── Raw API call (bypasses claude_client.py intentionally) ────────────────────
# This lab needs to capture the messages list BEFORE the call so we can display it.

def raw_chat(system: str, messages: list[dict], max_tokens: int = 700) -> tuple[str, dict]:
    """Call Claude with a full messages list. Returns (text, usage_dict)."""
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }
    return response.content[0].text, usage


# ── Prompts ───────────────────────────────────────────────────────────────────

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

# ── Page ──────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Context Window Inspector",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 Context Window Inspector")
st.caption("Hour 3B | Agentic AI Foundations")

st.markdown(
    """
Every LLM call receives a **messages array** — the conversation history so far.
This is short-term memory. It is not abstract: it is a Python list of dicts.

This lab runs a 3-step pipeline and shows you the **exact JSON** sent to Claude at each step.
Toggle **Chain context** to see how the messages list grows as prior outputs are appended.
"""
)

st.divider()

# ── Controls ──────────────────────────────────────────────────────────────────

col_ctrl1, col_ctrl2 = st.columns([2, 1])

with col_ctrl1:
    EXAMPLES = [
        "Custom goal — type below",
        "Write a summary of quantum computing for software developers.",
        "Create a beginner's 30-day study plan for learning Python.",
        "Outline a unit-testing strategy for a REST API with authentication.",
    ]
    selected = st.selectbox("Choose an example goal:", EXAMPLES)
    goal = st.text_area(
        "Goal:",
        value="" if selected == EXAMPLES[0] else selected,
        height=80,
        placeholder="Enter a goal...",
    )

with col_ctrl2:
    st.markdown("**Memory mode**")
    chain_context = st.toggle(
        "Chain context between steps",
        value=True,
        help=(
            "ON: each executor call receives all prior outputs in its messages list. "
            "Context grows. Token count grows. This is how memory works.\n\n"
            "OFF: each executor call receives only the current step. "
            "Fresh context each time. Token count stays low."
        ),
    )
    st.caption(
        "**Chained** — prior outputs added to each call" if chain_context
        else "**Isolated** — each call is fresh, no memory of prior steps"
    )

run = st.button("▶  Run Pipeline", type="primary", disabled=not goal.strip())

# ── Helpers ───────────────────────────────────────────────────────────────────

def render_messages_expander(messages: list[dict], system: str, usage_in: int, label: str, color: str):
    """Render the messages-inspector expander for one pipeline step."""
    fill_pct = min(usage_in / CONTEXT_WINDOW_LIMIT, 1.0)
    with st.expander(
        f"📨 Messages sent to Claude — {label} ({usage_in:,} / {CONTEXT_WINDOW_LIMIT:,} tokens)",
        expanded=False,
    ):
        st.markdown(f"**System prompt** (defines the role — not part of messages array):")
        st.code(system, language="text")
        st.markdown(f"**Messages array** ({len(messages)} message{'s' if len(messages) > 1 else ''}):")
        st.json(messages)
        st.markdown("**Context window usage:**")
        st.progress(
            fill_pct,
            text=f"{usage_in:,} tokens used ({fill_pct*100:.2f}% of {CONTEXT_WINDOW_LIMIT:,} limit)",
        )


def extract_steps(plan: str) -> list[str]:
    lines = [ln.strip() for ln in plan.split("\n") if ln.strip()]
    steps = [ln for ln in lines if ln and (ln[0].isdigit() or ln.lower().startswith("step"))]
    return steps if steps else lines


# ── Pipeline ──────────────────────────────────────────────────────────────────

if run and goal.strip():

    token_history = []  # [(step_label, input_tokens)] for the bar chart at the end

    # ── STEP 1: PLANNER ───────────────────────────────────────────────────────
    st.divider()
    with st.container(border=True):
        st.markdown(
            "<strong style='color:#8E24AA;'>🟣 PLANNER — LLM Call 1</strong>",
            unsafe_allow_html=True,
        )

        planner_messages = [{"role": "user", "content": goal.strip()}]

        with st.spinner("Planner running..."):
            t0 = time.perf_counter()
            plan, plan_usage = raw_chat(PLANNER_SYSTEM, planner_messages)
            plan_elapsed = time.perf_counter() - t0

        token_history.append(("Planner", plan_usage["input_tokens"]))

        # Show the output first, then the messages inspector
        st.markdown("**Plan:**")
        st.markdown(plan)

        c1, c2, c3 = st.columns(3)
        c1.metric("Input tokens", plan_usage["input_tokens"])
        c2.metric("Output tokens", plan_usage["output_tokens"])
        c3.metric("Time", f"{plan_elapsed:.1f}s")

        render_messages_expander(
            planner_messages, PLANNER_SYSTEM,
            plan_usage["input_tokens"], "Planner", "#8E24AA",
        )

    # ── STATE PARSE ───────────────────────────────────────────────────────────
    steps = extract_steps(plan)
    num_steps = min(len(steps), 2)  # run 2 steps to show context growth

    with st.container(border=True):
        st.markdown("**⚙️ STATE — Python parses the plan (no LLM call)**")
        st.caption(f"Extracted {len(steps)} steps. Running first {num_steps} through the executor.")

    # ── STEP 2 & 3: EXECUTOR(S) ───────────────────────────────────────────────
    executor_outputs: list[str] = []
    step_labels = []

    for i in range(num_steps):
        step_text = steps[i]
        call_num = i + 2

        with st.container(border=True):
            st.markdown(
                f"<strong style='color:#00897B;'>🩵 EXECUTOR — LLM Call {call_num}</strong> "
                f"<span style='color:#888;font-size:0.9em;'>| Step {i+1}: {step_text[:80]}{'…' if len(step_text) > 80 else ''}</span>",
                unsafe_allow_html=True,
            )

            # Build the messages array
            if chain_context and executor_outputs:
                # Chain: include all prior executor outputs as assistant turns
                exec_messages: list[dict] = []
                for j, prior_output in enumerate(executor_outputs):
                    exec_messages.append({"role": "user",      "content": steps[j]})
                    exec_messages.append({"role": "assistant", "content": prior_output})
                exec_messages.append({"role": "user", "content": step_text})
            else:
                # Isolated: fresh context, only the current step
                exec_messages = [{"role": "user", "content": step_text}]

            with st.spinner(f"Executor running step {i + 1}..."):
                t_exec = time.perf_counter()
                exec_out, exec_usage = raw_chat(EXECUTOR_SYSTEM, exec_messages)
                exec_elapsed = time.perf_counter() - t_exec

            executor_outputs.append(exec_out)
            token_history.append((f"Executor {i+1}", exec_usage["input_tokens"]))
            step_labels.append(f"Step {i+1}")

            st.markdown("**Output:**")
            st.markdown(exec_out)

            c1, c2, c3 = st.columns(3)
            c1.metric("Input tokens", exec_usage["input_tokens"])
            c2.metric("Output tokens", exec_usage["output_tokens"])
            c3.metric("Time", f"{exec_elapsed:.1f}s")

            if chain_context and i > 0:
                st.caption(
                    f"↑ Input tokens includes {i} prior step output(s) in the messages list — "
                    f"that's why token count grew from the previous executor call."
                )

            render_messages_expander(
                exec_messages, EXECUTOR_SYSTEM,
                exec_usage["input_tokens"], f"Executor {i+1}", "#00897B",
            )

    # ── CONTEXT GROWTH SUMMARY ────────────────────────────────────────────────
    st.divider()
    st.subheader("Context Growth Across Calls")

    labels  = [row[0] for row in token_history]
    amounts = [row[1] for row in token_history]

    # Simple bar chart using st.bar_chart (data as dict)
    import pandas as pd
    df = pd.DataFrame({"Input tokens (context window used)": amounts}, index=labels)
    st.bar_chart(df, color="#1E88E5")

    if chain_context:
        growth = amounts[-1] - amounts[0] if len(amounts) > 1 else 0
        st.markdown(
            f"Context grew by **{growth:,} tokens** from the first call to the last. "
            f"In a long pipeline this adds up — and is why context summarisation strategies matter."
        )
    else:
        st.markdown(
            "In **Isolated** mode each call starts fresh — token count stays low "
            "but the executor has no memory of prior steps. Try toggling to **Chain context** to compare."
        )

    # ── Observation prompts ───────────────────────────────────────────────────
    st.divider()
    st.subheader("What to observe")
    st.markdown(
        """
- **Open the "Messages sent to Claude" expanders** — this is exactly what the API receives. Nothing is hidden.
- **Compare Executor 1 vs Executor 2 in Chain mode** — the second call's messages array is longer. That longer array costs more tokens on every call.
- **Toggle "Chain context" off and re-run** — token counts shrink but the Executor loses its prior context. Which outputs suffer?
- **Watch the context window fill bar** — for this short pipeline it barely moves. What would happen after 20 steps? 50?
- **The Planner's messages array has 1 message.** The chained Executor's array has 3 or more. This is memory accumulation in practice.
"""
    )

    with st.expander("Short-term vs long-term memory — the distinction"):
        st.markdown(
            """
**Short-term memory** is the messages array you just saw — the conversation history
passed to the model on each API call. It lives in RAM, resets when the process ends,
and costs tokens on every call. This is the *only* memory Claude has by default.

**Long-term memory** is implemented *outside* the model — a vector database, a key-value
store, or a file. The agent writes summaries or embeddings to this store and retrieves
relevant content at the start of each call, injecting it into the messages array.
This is how agents remember across sessions.

In this lab, you saw short-term memory. The module on memory (later in the course)
will show you how to add long-term memory using vector stores.
"""
        )
