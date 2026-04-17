"""
Hour 2B Lab — System Prompt Role Lab: Same Model, Three Identities
Module 1 | Agentic AI Foundations

The same Claude model is sent the same user message three times.
The ONLY difference is the system prompt — which defines the role.
Students can edit each system prompt and observe how the output transforms.

Key insight: system prompt = agent identity. The model is not the agent; the
system prompt is what makes it a Planner, an Executor, or an Evaluator.

Run: streamlit run hour2b_lab_system_prompt_roles.py
"""

import streamlit as st
from claude_client import chat

st.set_page_config(
    page_title="System Prompt Role Lab",
    page_icon="🎭",
    layout="wide",
)

st.title("🎭 System Prompt Role Lab")
st.caption("Hour 2B | Agentic AI Foundations")

st.markdown(
    """
The **same Claude model** will receive the **same user message** three times.
The only difference is the **system prompt** — which defines the role.

Edit any system prompt and hit **Send to All Three Roles** to see how the output transforms.
"""
)

st.divider()

# ── Canonical system prompts (from hour3_lab_agentic_pipeline.py) ─────────────

DEFAULT_PROMPTS = {
    "planner": (
        "You are a planning agent. Given a goal, return a numbered list of exactly 4 concrete, "
        "specific, actionable steps to achieve it. Each step must be unambiguous — someone "
        "could carry it out without further clarification. "
        "Return ONLY the numbered list, one step per line, no preamble."
    ),
    "executor": (
        "You are an executor agent. You receive a specific task and carry it out immediately. "
        "Produce a concrete, detailed, useful output — do not plan, do not list further steps, "
        "just produce the actual result for this one task."
    ),
    "evaluator": (
        "You are a quality evaluator. You receive a task or goal and an output. "
        "Score the output from 1–10 against the goal. "
        "Identify ONE specific, concrete improvement. "
        "Be brief: one score line, one improvement sentence."
    ),
}

ROLE_META = {
    "planner":  {"label": "Planner",  "color": "#8E24AA", "icon": "🟣"},
    "executor": {"label": "Executor", "color": "#00897B", "icon": "🩵"},
    "evaluator":{"label": "Evaluator","color": "#E53935", "icon": "🔴"},
}

# ── User message input ────────────────────────────────────────────────────────

EXAMPLE_MESSAGES = [
    "Custom — type your own below",
    "Write a 3-paragraph summary of quantum computing for software developers.",
    "Create a beginner's 30-day study plan for learning Python.",
    "Draft a proposal for introducing AI tools into a small marketing team.",
]

selected = st.selectbox("Choose an example user message:", EXAMPLE_MESSAGES)
user_message = st.text_area(
    "User message (sent identically to all three roles):",
    value="" if selected == EXAMPLE_MESSAGES[0] else selected,
    height=80,
    placeholder="Enter the task or goal...",
)

st.divider()

# ── System prompt editors — one per role ──────────────────────────────────────

st.subheader("Edit system prompts")
st.caption("These define what role Claude plays. Change them and observe how the output transforms.")

editor_cols = st.columns(3)
system_prompts = {}

for col, role in zip(editor_cols, ["planner", "executor", "evaluator"]):
    meta = ROLE_META[role]
    with col:
        st.markdown(
            f"<div style='border-top:4px solid {meta['color']};padding:6px 0 2px 0;'>"
            f"<strong style='color:{meta['color']};'>{meta['icon']} {meta['label']}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )

        # Initialise session state defaults
        key = f"sysprompt_{role}"
        if key not in st.session_state:
            st.session_state[key] = DEFAULT_PROMPTS[role]

        prompt_text = st.text_area(
            "System prompt:",
            value=st.session_state[key],
            height=200,
            key=key,
            label_visibility="collapsed",
        )
        system_prompts[role] = prompt_text

        if st.button(f"Reset to default", key=f"reset_{role}"):
            st.session_state[key] = DEFAULT_PROMPTS[role]
            st.rerun()

        # Show a badge if the prompt has been modified
        if prompt_text.strip() != DEFAULT_PROMPTS[role].strip():
            st.caption("✏️ Modified from default")
        else:
            st.caption("✓ Using default")

st.divider()

# ── Run button ────────────────────────────────────────────────────────────────

run = st.button(
    "▶  Send to All Three Roles",
    type="primary",
    disabled=not user_message.strip(),
)

# ── Output columns ────────────────────────────────────────────────────────────

if run and user_message.strip():

    output_cols = st.columns(3)
    slots = {role: col.empty() for role, col in zip(["planner", "executor", "evaluator"], output_cols)}
    status = st.empty()

    for role in ["planner", "executor", "evaluator"]:
        meta = ROLE_META[role]
        status.info(f"Calling Claude as **{meta['label']}**...")

        response, usage = chat(
            system=system_prompts[role],
            user=user_message.strip(),
            max_tokens=700,
        )

        with slots[role].container():
            st.markdown(
                f"<div style='border-top:4px solid {meta['color']};padding:8px 0 4px 0;'>"
                f"<strong style='color:{meta['color']};font-size:1.05em;'>"
                f"{meta['icon']} {meta['label']} output"
                f"</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown(response)
            st.markdown(
                f"<div style='font-size:0.8em;color:#888;margin-top:6px;'>"
                f"⬆ {usage['input_tokens']} in &nbsp;|&nbsp; ⬇ {usage['output_tokens']} out"
                f"</div>",
                unsafe_allow_html=True,
            )

    status.success("All three roles complete.")

    # ── Reflection prompts ────────────────────────────────────────────────────
    st.divider()
    st.subheader("What to observe")
    st.markdown(
        """
- **Same model, same message, different outputs** — the only variable was the system prompt. This is how agent roles are defined.
- **Try swapping roles:** Paste the Planner's system prompt into the Executor column. What happens when you tell the Executor to produce a numbered list instead of executing?
- **Try blurring roles:** Remove all role instructions and replace with "You are a helpful assistant." How does the output change?
- **Word count:** Does the Planner produce shorter output than the Executor? Does the Evaluator produce the most structured output?
- **In an agentic system**, these three calls would be chained: the Planner's output feeds the Executor, and the Executor's output feeds the Evaluator. You just saw all three independently — Hour 3 shows them chained.
"""
    )

# ── Reference card ────────────────────────────────────────────────────────────

st.divider()
with st.expander("System prompt design principles — quick reference"):
    st.markdown(
        """
| Principle | Example |
|---|---|
| State the role explicitly | "You are a planning agent." |
| Constrain the output format | "Return ONLY a numbered list." |
| Prohibit out-of-role behaviour | "Do not plan — act." |
| Define the success criterion | "Each step must be unambiguous." |

The system prompt is the only mechanism that separates a Planner from an Executor from an Evaluator.
The model weights do not change between calls — the system prompt is the entire difference.
"""
    )
