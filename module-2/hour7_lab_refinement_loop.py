"""
Hour 7 Lab — Iterative Refinement Loop
Module 2 | Prompt Fundamentals

Students configure a Generator → Critic → Rewriter loop that runs for up to
N rounds, stopping early when all quality scores exceed a threshold.

Each round appears as a live container as it runs. A score progression chart
shows improvement across rounds. The final output is compared to Round 1.

Loop architecture:
    output = generate(topic)
    while round < MAX_ROUNDS:
        scores, feedback = evaluate(output)
        if all scores >= THRESHOLD: break
        output = rewrite(output, feedback)
        round += 1

Run: streamlit run hour7_lab_refinement_loop.py
"""

import json
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Refinement Loop", page_icon="🔁", layout="wide")
st.title("🔁 Hour 7 — Iterative Refinement Loop")
st.caption("Module 2 | Prompt Fundamentals")

st.markdown(
    """
A **refinement loop** runs the same content through Generate → Critique → Rewrite
until quality meets a threshold — or runs out of rounds.

This is the **Reflection pattern**: the model reviews its own output and improves it.
It's one of the most powerful patterns in agentic AI.
"""
)

# ── Default prompts ───────────────────────────────────────────────────────────

DEFAULT_GENERATOR = """\
You are a senior technology writer who writes compelling, specific blog introductions
for software engineering audiences.

Write a 3-sentence blog introduction about: {topic}

Requirements:
- Sentence 1 (Hook): Challenge a common assumption or state a surprising fact
- Sentence 2 (Problem): Establish the specific gap or cost the reader faces
- Sentence 3 (Promise): Hint at what the reader will gain by continuing

Constraints:
- Do not use generic phrases like "In today's world" or "AI is transforming"
- Use concrete, specific language
- Maximum 80 words
- Return ONLY the introduction\
"""

DEFAULT_CRITIC = """\
You are a harsh editor whose job is to find weaknesses — not praise strengths.
Evaluate the following blog introduction on three criteria.

Criteria (score 1–5 each):
1. hook_strength: Does sentence 1 genuinely surprise or challenge the reader?
   1 = generic/forgettable, 5 = immediately stops the scroll
2. clarity: Is the problem and promise clearly communicated in one reading?
   1 = confusing, 5 = crystal clear
3. specificity: Are concrete details used instead of vague generalities?
   1 = pure abstraction, 5 = specific facts/numbers/scenarios

Introduction:
{introduction}

Return ONLY valid JSON (no markdown, no other text):
{{"hook_strength": 0, "clarity": 0, "specificity": 0,
  "feedback": "Quote the 2 most important phrases that need changing and say exactly what to do."}}\
"""

DEFAULT_REWRITER = """\
You are a senior technology writer doing a surgical revision of a blog introduction.

Rewrite the introduction below, fixing ONLY the specific issues in the feedback.
Do not change what is already working.

Original introduction:
{introduction}

Issues to fix:
{feedback}

Constraints:
- Keep the 3-sentence structure (Hook / Problem / Promise)
- Maximum 80 words
- Return ONLY the rewritten introduction\
"""

CRITERIA = ["hook_strength", "clarity", "specificity"]
CRITERIA_ICONS = {"hook_strength": "🪝", "clarity": "💡", "specificity": "🎯"}

# ── Helpers ───────────────────────────────────────────────────────────────────

def parse_scores(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        start, end = clean.find("{"), clean.rfind("}") + 1
        return json.loads(clean[start:end]) if start >= 0 and end > start else None
    except json.JSONDecodeError:
        return None


def score_bar(val: int, threshold: int, max_score: int = 5) -> str:
    filled = "█" * val
    empty  = "░" * (max_score - val)
    status = "✅" if val >= threshold else "❌"
    return f"{status} [{filled}{empty}] {val}/{max_score}"


# ── Sidebar configuration ─────────────────────────────────────────────────────

with st.sidebar:
    st.header("Loop Settings")
    max_rounds = st.slider("Max rounds", 1, 5, 3)
    threshold  = st.slider("Pass threshold (all criteria must reach this)", 1, 5, 4)
    st.divider()
    st.markdown("**How to use:**")
    st.markdown("1. Edit the three prompts (or use defaults)")
    st.markdown("2. Set a topic and hit Run")
    st.markdown("3. Watch each round fill in live")
    st.markdown("4. Observe where scores improve vs stagnate")
    st.divider()
    st.markdown("**Try these experiments:**")
    st.markdown("- Lower threshold to 2 — loop exits after round 1")
    st.markdown("- Remove the 'feedback' field from the Critic — Rewriter gets no guidance")
    st.markdown("- Make the Generator weak intentionally — see how many rounds it takes")

# ── Prompt editors ────────────────────────────────────────────────────────────

st.subheader("Configure the three prompts")

editor_tabs = st.tabs(["Generator", "Critic", "Rewriter"])

PROMPT_DEFAULTS = {
    "gen":   DEFAULT_GENERATOR,
    "crit":  DEFAULT_CRITIC,
    "rew":   DEFAULT_REWRITER,
}
for key, default in PROMPT_DEFAULTS.items():
    if f"prompt_{key}" not in st.session_state:
        st.session_state[f"prompt_{key}"] = default

with editor_tabs[0]:
    st.caption("Produces the initial content. `{topic}` is substituted at runtime.")
    gen_prompt = st.text_area("Generator prompt:", value=st.session_state["prompt_gen"],
                               height=220, key="prompt_gen", label_visibility="collapsed")
    if st.button("Reset Generator", key="rst_gen"):
        st.session_state["prompt_gen"] = DEFAULT_GENERATOR; st.rerun()

with editor_tabs[1]:
    st.caption("Scores the content on 3 criteria (1–5 each) and returns JSON + feedback. `{introduction}` is substituted.")
    crit_prompt = st.text_area("Critic prompt:", value=st.session_state["prompt_crit"],
                                height=220, key="prompt_crit", label_visibility="collapsed")
    if st.button("Reset Critic", key="rst_crit"):
        st.session_state["prompt_crit"] = DEFAULT_CRITIC; st.rerun()

with editor_tabs[2]:
    st.caption("Rewrites based on the feedback. `{introduction}` and `{feedback}` are substituted.")
    rew_prompt = st.text_area("Rewriter prompt:", value=st.session_state["prompt_rew"],
                               height=220, key="prompt_rew", label_visibility="collapsed")
    if st.button("Reset Rewriter", key="rst_rew"):
        st.session_state["prompt_rew"] = DEFAULT_REWRITER; st.rerun()

# ── Topic + run ───────────────────────────────────────────────────────────────

st.divider()

TOPICS = [
    "Custom topic — type below",
    "Why software engineers should learn to build agentic AI systems",
    "Why most AI projects fail before reaching production",
    "The hidden cost of technical debt in fast-moving startups",
    "Why every developer should understand how LLMs actually work",
]
selected_topic = st.selectbox("Choose a topic:", TOPICS)
topic = st.text_area(
    "Topic:",
    value="" if selected_topic == TOPICS[0] else selected_topic,
    height=60,
    placeholder="Enter a topic for the blog introduction...",
)

run = st.button("▶  Run Refinement Loop", type="primary", disabled=not topic.strip())

# ── Loop execution ────────────────────────────────────────────────────────────

if run and topic.strip():
    st.divider()

    round_history: list[dict] = []
    current_text = ""
    final_text   = ""
    status_bar   = st.empty()

    # ── Round 0: Generate ─────────────────────────────────────────────────────
    status_bar.info("🔵 Generating initial content...")
    gen_user = gen_prompt.replace("{topic}", topic.strip())
    current_text, gen_usage = chat(system="", user=gen_user, max_tokens=300, temperature=0.8)

    # ── Rounds ────────────────────────────────────────────────────────────────
    for rnd in range(1, max_rounds + 1):
        status_bar.info(f"Round {rnd} / {max_rounds} — evaluating...")

        with st.container(border=True):
            st.markdown(f"### Round {rnd}")

            # Show current text
            st.markdown("**Current text:**")
            text_slot = st.empty()
            text_slot.markdown(
                f"<div style='background:#f8f8f8;border-left:4px solid #aaa;"
                f"padding:12px;border-radius:4px;font-style:italic;'>{current_text}</div>",
                unsafe_allow_html=True,
            )

            # ── Critic ────────────────────────────────────────────────────────
            with st.spinner("Critic evaluating..."):
                crit_user = crit_prompt.replace("{introduction}", current_text)
                raw_scores, crit_usage = chat(system="", user=crit_user, max_tokens=300, temperature=0.1)

            scores = parse_scores(raw_scores)

            if scores is None:
                st.error("Critic returned unparseable output. Check that your Critic prompt returns valid JSON.")
                st.code(raw_scores)
                break

            # Display scores
            score_cols = st.columns(3)
            all_pass = True
            for col, crit in zip(score_cols, CRITERIA):
                val = scores.get(crit, 0)
                icon = CRITERIA_ICONS[crit]
                passing = val >= threshold
                if not passing:
                    all_pass = False
                col.markdown(
                    f"<div style='text-align:center;padding:8px;border-radius:6px;"
                    f"background:{'#e8f5e9' if passing else '#ffebee'};'>"
                    f"<div style='font-size:1.5em;'>{icon}</div>"
                    f"<div style='font-weight:bold;'>{crit.replace('_', ' ').title()}</div>"
                    f"<div style='font-size:1.2em;color:{'#43A047' if passing else '#E53935'};'>"
                    f"{val}/{5} {'✅' if passing else '❌'}"
                    f"</div></div>",
                    unsafe_allow_html=True,
                )

            feedback = scores.get("feedback", "")
            st.info(f"💬 Feedback: {feedback}")

            round_history.append({
                "round": rnd,
                "text":  current_text,
                "scores": {c: scores.get(c, 0) for c in CRITERIA},
                "feedback": feedback,
                "passed": all_pass,
            })

            # ── Early stop or Rewrite ─────────────────────────────────────────
            if all_pass:
                st.success(f"✅ All criteria ≥ {threshold} — threshold met. Stopping early at round {rnd}.")
                final_text = current_text
                break

            if rnd == max_rounds:
                st.warning(f"⏱ Max rounds ({max_rounds}) reached.")
                final_text = current_text
                break

            # Rewrite
            with st.spinner("Rewriter improving..."):
                rew_user = rew_prompt.replace("{introduction}", current_text).replace("{feedback}", feedback)
                current_text, rew_usage = chat(system="", user=rew_user, max_tokens=300, temperature=0.7)

            st.markdown("**Rewritten text:**")
            st.markdown(
                f"<div style='background:#f0f8f0;border-left:4px solid #43A047;"
                f"padding:12px;border-radius:4px;font-style:italic;'>{current_text}</div>",
                unsafe_allow_html=True,
            )

    else:
        final_text = current_text

    status_bar.success(f"Loop complete — {len(round_history)} round(s) run.")

    # ── Score progression chart ───────────────────────────────────────────────
    if len(round_history) > 1:
        st.divider()
        st.subheader("Score Progression")

        import pandas as pd
        chart_data = {
            crit.replace("_", " ").title(): [r["scores"][crit] for r in round_history]
            for crit in CRITERIA
        }
        df = pd.DataFrame(chart_data, index=[f"Round {r['round']}" for r in round_history])
        st.line_chart(df, y_label="Score (1–5)", x_label="Round", color=["#8E24AA", "#1E88E5", "#43A047"])

        # Numeric summary
        sc = st.columns(len(CRITERIA))
        for col, crit in zip(sc, CRITERIA):
            first = round_history[0]["scores"][crit]
            last  = round_history[-1]["scores"][crit]
            delta = last - first
            col.metric(
                crit.replace("_", " ").title(),
                f"{last}/5",
                delta=f"+{delta}" if delta > 0 else str(delta),
            )

    # ── Before / After ────────────────────────────────────────────────────────
    if round_history and final_text != round_history[0]["text"]:
        st.divider()
        st.subheader("Before vs After")
        ba_left, ba_right = st.columns(2)
        with ba_left:
            st.markdown("**Round 1 (initial):**")
            st.markdown(
                f"<div style='background:#ffebee;border-left:4px solid #E53935;"
                f"padding:12px;border-radius:4px;font-style:italic;'>{round_history[0]['text']}</div>",
                unsafe_allow_html=True,
            )
        with ba_right:
            st.markdown("**Final output:**")
            st.markdown(
                f"<div style='background:#e8f5e9;border-left:4px solid #43A047;"
                f"padding:12px;border-radius:4px;font-style:italic;'>{final_text}</div>",
                unsafe_allow_html=True,
            )

    # ── Observations ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("What to observe")
    st.markdown(
        f"""
- **Which criterion improved most across rounds?** Is the improvement consistent or does one plateau?
- **Did the loop stop early?** If not, what was the bottleneck criterion?
- **Try lowering the threshold to 2** — the loop exits after round 1. When is a single pass enough?
- **Try making the Generator weak** (remove the sentence requirements) — how many rounds does recovery take?
- **The feedback quality drives everything.** If the Critic says "improve the hook" without quoting the exact phrase, the Rewriter makes generic changes. Specific feedback → specific improvement.
- **In a production agentic system**, this loop would run on every executor output — not just once. The `max_rounds` cap prevents infinite loops.
"""
    )

# ── Reference ─────────────────────────────────────────────────────────────────

st.divider()
with st.expander("Reflection pattern — how it maps to agentic systems"):
    st.markdown(
        """
The refinement loop you just ran **is** the Evaluator-Optimizer pattern from agentic AI:

```
generate()   =  Executor (produces output)
evaluate()   =  Evaluator (scores against criteria, returns structured feedback)
rewrite()    =  Executor again (but with critique as additional context)
```

In production agents:
- The **Evaluator** uses a different system prompt from the Executor — same model, different role
- The **threshold** prevents infinite revision loops — cost and latency grow with every round
- The **feedback must be structured** (JSON with specific fields) so it can be passed programmatically
- A **max_rounds** cap is mandatory — without it, a poor Critic can trap the loop forever

The key design decision: how much is one extra revision worth in tokens and latency?
"""
    )
