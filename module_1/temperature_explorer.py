"""
Temperature Explorer
Module 1 | Bonus Lab — Understanding LLM Temperature

A single prompt is sent to Claude multiple times, each with a different
temperature. Results appear side-by-side so students can compare how
temperature affects creativity, consistency, and randomness.

Temperature range for Claude: 0.0 (deterministic) → 1.0 (most creative)

Run: streamlit run temperature_explorer.py
"""

import time
import streamlit as st
from claude_client import chat


# ── Helper ────────────────────────────────────────────────────────────────────

def temp_label(t: float) -> tuple[str, str]:
    """Return a human label and hex colour for a given temperature value."""
    if t <= 0.1:
        return "Deterministic", "#1E88E5"
    elif t <= 0.4:
        return "Focused", "#43A047"
    elif t <= 0.65:
        return "Balanced", "#FB8C00"
    else:
        return "Creative", "#E53935"


# ── Page header ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Temperature Explorer",
    page_icon="🌡️",
    layout="wide",
)

st.title("🌡️ Temperature Explorer")
st.caption("Module 1 Bonus Lab | Agentic AI Foundations")

st.markdown(
    """
**Temperature** controls how random Claude's output is.

| Temperature | Behaviour | Best for |
|---|---|---|
| **0.0** | Nearly deterministic — same prompt → nearly same answer | Facts, classification, structured output |
| **0.3 – 0.5** | Balanced — coherent with slight variation | Summarisation, Q&A, code |
| **0.7 – 1.0** | Creative — varied, exploratory, sometimes surprising | Brainstorming, storytelling, marketing copy |

Set temperatures for each panel, enter a prompt, and hit **Run All Panels** to compare.
"""
)

st.divider()

# ── System prompt (shared across all panels) ──────────────────────────────────

with st.expander("Optional: customise the system prompt (same for all panels)", expanded=False):
    system_prompt = st.text_area(
        "System prompt:",
        value="You are a helpful assistant. Respond concisely.",
        height=80,
        key="system_prompt",
    )

# Read back the value (widget always executes even when expander is collapsed)
system_prompt = st.session_state.get("system_prompt", "You are a helpful assistant. Respond concisely.")

# ── User prompt ───────────────────────────────────────────────────────────────

EXAMPLE_PROMPTS = [
    "Custom prompt — type below",
    "Write a one-sentence tagline for an AI startup.",
    "Explain what a neural network is in exactly two sentences.",
    "Give me three unique names for a productivity app.",
    "What is the capital of France? Answer in one word.",
    "Write the opening sentence of a mystery novel set in Tokyo.",
    "List one unexpected use case for a large language model.",
]

selected = st.selectbox("Try an example prompt:", EXAMPLE_PROMPTS)
user_prompt = st.text_area(
    "Prompt (sent to every panel):",
    value="" if selected == EXAMPLE_PROMPTS[0] else selected,
    height=90,
    placeholder="Enter your prompt here...",
)

# ── Panel count ───────────────────────────────────────────────────────────────

st.divider()

num_panels = st.radio(
    "Number of comparison panels:",
    options=[2, 3, 4],
    index=1,
    horizontal=True,
    help="Each panel runs the same prompt at a different temperature.",
)

DEFAULT_TEMPS = {
    2: [0.0, 1.0],
    3: [0.0, 0.5, 1.0],
    4: [0.0, 0.3, 0.7, 1.0],
}

# ── Temperature sliders (one per panel) ───────────────────────────────────────

st.subheader("Set temperatures")
slider_cols = st.columns(num_panels)
temperatures: list[float] = []

for i, col in enumerate(slider_cols):
    with col:
        temp = st.slider(
            f"Panel {i + 1}",
            min_value=0.0,
            max_value=1.0,
            value=float(DEFAULT_TEMPS[num_panels][i]),
            step=0.05,
            key=f"temp_{i}",
        )
        temperatures.append(temp)
        label, color = temp_label(temp)
        st.markdown(
            f"<div style='text-align:center;font-weight:bold;color:{color};'>{label}</div>",
            unsafe_allow_html=True,
        )

st.divider()

# ── Run button ────────────────────────────────────────────────────────────────

run_clicked = st.button(
    "▶  Run All Panels",
    type="primary",
    disabled=not user_prompt.strip(),
)

# ── Output panels ─────────────────────────────────────────────────────────────

if run_clicked and user_prompt.strip():

    results: list[dict] = []
    status_bar = st.empty()
    output_cols = st.columns(num_panels)
    panel_slots = [col.empty() for col in output_cols]

    for i in range(num_panels):
        temp = temperatures[i]
        label, color = temp_label(temp)

        status_bar.info(
            f"Running Panel {i + 1} / {num_panels}  —  temperature {temp:.2f}  ({label})..."
        )

        t_start = time.perf_counter()
        response, usage = chat(
            system=system_prompt,
            user=user_prompt.strip(),
            max_tokens=600,
            temperature=temp,
        )
        elapsed = time.perf_counter() - t_start

        results.append(
            {
                "temp": temp,
                "label": label,
                "color": color,
                "response": response,
                "usage": usage,
                "elapsed": elapsed,
            }
        )

        # Render immediately — students see panels fill in one by one
        with panel_slots[i].container():
            st.markdown(
                f"<div style='border-top:4px solid {color}; padding:10px 0 4px 0;'>"
                f"<strong style='color:{color}; font-size:1.05em;'>"
                f"Panel {i + 1} — {label}"
                f"</strong>"
                f"<span style='float:right; color:#888; font-size:0.85em;'>🌡️ {temp:.2f}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(response)
            st.markdown(
                f"<div style='font-size:0.8em; color:#888; margin-top:8px;'>"
                f"⬆ {usage['input_tokens']} in &nbsp;|&nbsp; "
                f"⬇ {usage['output_tokens']} out &nbsp;|&nbsp; "
                f"⏱ {elapsed:.1f}s"
                f"</div>",
                unsafe_allow_html=True,
            )

    status_bar.success(f"All {num_panels} panels complete. Try running again — do outputs change?")

    # ── Observation prompts ───────────────────────────────────────────────────
    st.divider()
    st.subheader("What to observe")
    temps_sorted = sorted(temperatures)
    min_t, max_t = temps_sorted[0], temps_sorted[-1]

    st.markdown(
        f"""
- **Consistency:** Hit *Run All Panels* again with the same prompt. Does the **{min_t:.2f}** panel produce nearly identical output? Does the **{max_t:.2f}** panel vary?
- **Word choice:** Does the high-temperature panel use more unusual or expressive language?
- **Factual prompts:** Try *"What is the capital of France?"* — all panels should say *Paris*, but style and wording may differ.
- **Creative prompts:** Try *"Write an opening sentence of a mystery novel"* — high temperature should feel distinct each run.
- **Agentic relevance:** In an agentic pipeline, which component (Planner, Executor, Evaluator) would you run at low vs. high temperature, and why?
"""
    )

    with st.expander("Raw responses — all panels"):
        for r in results:
            st.markdown(f"**Panel — Temperature {r['temp']:.2f} ({r['label']})**")
            st.code(r["response"], language="text")

# ── Deep-dive (always visible) ────────────────────────────────────────────────

st.divider()
with st.expander("How temperature works under the hood"):
    st.markdown(
        """
When Claude generates text it predicts the next token by computing a probability
distribution over its entire vocabulary. Temperature is applied as a divisor to the
raw logit scores **before** the softmax step:

```
adjusted_logit = raw_logit / temperature
```

- **Temperature → 0** — the highest-probability token is always chosen (greedy decoding).
  Output is nearly deterministic.
- **Temperature = 1** — logits are unchanged; sampling follows the model's natural distribution.
- **Temperature → max** — logits are scaled down, flattening the distribution. Lower-probability
  tokens become more likely. Output becomes more varied and sometimes incoherent.

**Practical rules for agentic systems:**

| Component | Recommended temperature | Reason |
|---|---|---|
| Planner | 0.0 – 0.3 | Plans must be reliable and structured |
| Executor (factual) | 0.2 – 0.5 | Accuracy matters more than creativity |
| Executor (creative) | 0.7 – 1.0 | Variety is the goal |
| Evaluator | 0.0 – 0.2 | Consistent, reproducible scoring |
"""
    )
