"""
Hour 15 Lab — Prompt Chaining Pattern
Module 4 | Core Agentic Patterns I

Each LLM call's output becomes the next call's input.
Lab: 3-stage content pipeline — Researcher → Outliner → Drafter.

Run: streamlit run module-4/hour15_lab_prompt_chaining.py
"""

import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 15 — Prompt Chaining", page_icon="⛓️", layout="wide")
st.title("⛓️ Hour 15 — Prompt Chaining Pattern")
st.caption("Module 4 | Core Agentic Patterns I")

st.markdown("""
The **Prompt Chaining Pattern** passes the output of one LLM call as input to the next.
Each stage transforms information into a form more useful for the stage that follows.

This lab runs a 3-stage content creation pipeline:
1. **Chain diagram** — see how data flows between stages
2. **3-stage pipeline** — Research → Outline → Draft on a topic you choose
3. **Chain inspection** — compare each stage's input vs output side by side
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 15 Guide")
    st.markdown("""
**Sections in this lab:**
1. **Pipeline diagram** — visualise the three agents
2. **3-stage pipeline** — run Researcher → Outliner → Drafter
3. **Chain inspection** — see what each stage received vs produced

**What to observe:**
- How each stage narrows and transforms information
- How the Drafter's input grows longer than the Researcher's
- Token cost progression: each stage is more expensive than the last
- What the Outliner adds that the raw facts cannot provide
""")
    st.divider()
    st.markdown("**Experiment ideas:**")
    st.markdown("- Compare a 1-stage (direct) prompt to the 3-stage chain output quality")
    st.markdown("- Try a technical topic vs a general interest topic")
    st.markdown("- Change the Drafter's max_tokens and see what gets cut off")
    st.divider()
    st.info("**Key principle:** Chaining lets each stage focus on one transformation. The Researcher should not care about prose style; the Drafter should not care about fact-gathering.")

# ── System Prompts ─────────────────────────────────────────────────────────────
RESEARCHER_SYSTEM = """\
You are a research agent. Given a topic, extract the 6–8 most important facts,
statistics, concepts, or examples that someone writing about this topic needs to know.

Rules:
- Be specific and concrete — avoid vague generalisations
- Include at least one statistic or measurable fact where relevant
- Each bullet should be a standalone, usable fact
- Do not organise into sections — return a flat bullet list only
- Do not add introductory sentences or summaries

Format: return ONLY a markdown bullet list, one fact per bullet.\
"""

OUTLINER_SYSTEM = """\
You are a content outliner. Given a topic and a list of key facts, produce a clear
article outline: a logical structure with H2 headings and brief subpoints under each.

Rules:
- Use 3–4 H2 headings that flow logically from introduction to conclusion
- Under each heading, list 2–3 specific subpoints that should be covered
- Each subpoint should map to one or more of the provided facts
- Do not write prose — only headings and bullet subpoints
- The outline should cover all the provided facts without duplication

Format: return ONLY the outline in markdown (## headings + bullet subpoints).\
"""

DRAFTER_SYSTEM = """\
You are a professional writer. Given a topic, an outline, and a set of key facts,
write a well-structured article following the outline exactly.

Rules:
- Write clear, engaging prose — no padding or filler
- Use the facts to support each section; do not invent statistics
- Follow the outline structure: use the H2 headings as section markers
- Keep the tone informative and accessible for a general professional audience
- Do not add a title — start directly with the first section
- Aim for approximately 300–400 words total

Write the complete article now.\
"""

# ── Section 1: Pipeline Diagram ────────────────────────────────────────────────
st.divider()
st.subheader("1 — The Prompt Chaining Pipeline")

diagram_cols = st.columns([2, 0.4, 2, 0.4, 2])

stage_cards = [
    ("#43A047", "#E8F5E9", "🔬", "[RESEARCHER]", "Green", "Reads the topic. Outputs bullet-point facts."),
    ("#8E24AA", "#F3E5F5", "📑", "[OUTLINER]", "Purple", "Reads topic + facts. Outputs structured outline."),
    ("#1E88E5", "#E3F2FD", "✍️", "[DRAFTER]", "Blue", "Reads topic + facts + outline. Outputs full article."),
]

for i, col in enumerate(diagram_cols):
    with col:
        if i % 2 == 0:
            idx = i // 2
            color, bg, icon, label, _, desc = stage_cards[idx]
            st.markdown(
                f"<div style='border-top:4px solid {color};background:{bg};"
                f"border-radius:6px;padding:14px;min-height:150px;text-align:center;'>"
                f"<div style='font-size:2em;'>{icon}</div>"
                f"<div style='font-weight:bold;color:{color};font-size:0.95em;margin:6px 0;'>{label}</div>"
                f"<div style='font-size:0.82em;color:#444;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='display:flex;align-items:center;justify-content:center;"
                "height:150px;font-size:1.8em;color:#999;'>→</div>",
                unsafe_allow_html=True,
            )

st.markdown("")
st.markdown("""
**How information flows:**
- Stage 1 → Stage 2: the bullet facts are injected into Stage 2's user prompt
- Stage 2 → Stage 3: the outline AND the facts are both injected into Stage 3's user prompt
- Each stage's context grows as it receives more prior output
""")

with st.expander("See system prompts"):
    t1, t2, t3 = st.tabs(["Researcher", "Outliner", "Drafter"])
    with t1:
        st.code(RESEARCHER_SYSTEM, language="text")
    with t2:
        st.code(OUTLINER_SYSTEM, language="text")
    with t3:
        st.code(DRAFTER_SYSTEM, language="text")

# ── Section 2: 3-Stage Pipeline ────────────────────────────────────────────────
st.divider()
st.subheader("2 — Run the 3-Stage Pipeline")

TOPIC_PRESETS = [
    "Custom topic — type below",
    "How the internet works",
    "The impact of sleep deprivation on cognitive performance",
    "How electric vehicles work",
    "The history and future of artificial intelligence",
    "How containerisation changed software deployment",
]

sel = st.selectbox("Pick a topic or write your own:", TOPIC_PRESETS, key="topic_preset")
topic = st.text_area(
    "Topic:",
    value="" if sel == TOPIC_PRESETS[0] else sel,
    placeholder="e.g. The science behind climate change",
    height=60,
    key="topic_input",
)

if st.button("▶ Run 3-Stage Pipeline", type="primary", disabled=not topic.strip()):
    stage_results = {}
    total_in, total_out = 0, 0

    progress = st.progress(0, text="Stage 1/3 — Researcher gathering facts…")
    with st.spinner("Researcher working…"):
        facts, u1 = chat(RESEARCHER_SYSTEM, f"Topic: {topic.strip()}", max_tokens=500, temperature=0.3)
    total_in += u1["input_tokens"]
    total_out += u1["output_tokens"]
    stage_results["researcher"] = {"output": facts, "usage": u1}
    progress.progress(33, text="Stage 2/3 — Outliner structuring content…")

    outliner_user = f"Topic: {topic.strip()}\n\nKey facts:\n{facts}\n\nCreate the article outline."
    with st.spinner("Outliner working…"):
        outline, u2 = chat(OUTLINER_SYSTEM, outliner_user, max_tokens=500, temperature=0.2)
    total_in += u2["input_tokens"]
    total_out += u2["output_tokens"]
    stage_results["outliner"] = {"output": outline, "usage": u2, "user_prompt": outliner_user}
    progress.progress(66, text="Stage 3/3 — Drafter writing article…")

    drafter_user = (
        f"Topic: {topic.strip()}\n\n"
        f"Key facts:\n{facts}\n\n"
        f"Outline:\n{outline}\n\n"
        "Write the complete article following the outline."
    )
    with st.spinner("Drafter writing…"):
        article, u3 = chat(DRAFTER_SYSTEM, drafter_user, max_tokens=1000, temperature=0.7)
    total_in += u3["input_tokens"]
    total_out += u3["output_tokens"]
    stage_results["drafter"] = {"output": article, "usage": u3, "user_prompt": drafter_user}
    progress.progress(100, text="Pipeline complete.")

    st.session_state["chain_results"] = stage_results
    st.session_state["chain_topic"] = topic.strip()
    st.session_state["chain_totals"] = (total_in, total_out)

if "chain_results" in st.session_state:
    stage_results = st.session_state["chain_results"]
    total_in, total_out = st.session_state["chain_totals"]

    stage_defs = [
        ("researcher", "🔬 Stage 1 — [RESEARCHER]", "#43A047"),
        ("outliner", "📑 Stage 2 — [OUTLINER]", "#8E24AA"),
        ("drafter", "✍️ Stage 3 — [DRAFTER]", "#1E88E5"),
    ]

    for key, label, color in stage_defs:
        data = stage_results.get(key, {})
        with st.expander(label, expanded=(key == "drafter")):
            st.markdown(
                f"<div style='border-left:4px solid {color};padding:4px 10px;margin-bottom:8px;'>"
                f"<strong style='color:{color};'>{label}</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown(data.get("output", ""))
            u = data.get("usage", {})
            st.caption(f"Input tokens: {u.get('input_tokens', 0)} | Output tokens: {u.get('output_tokens', 0)}")

    st.markdown("**Final article:**")
    with st.container(border=True):
        st.markdown(stage_results["drafter"]["output"])

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM calls", 3)
    c2.metric("Total input tokens", total_in)
    c3.metric("Total output tokens", total_out)

# ── Section 3: Chain Inspection ────────────────────────────────────────────────
st.divider()
st.subheader("3 — Chain Inspection")

st.markdown("""
See exactly what each stage **received** versus what it **produced**.
This makes the information transformation at each stage visible.
""")

if "chain_results" not in st.session_state:
    st.info("Run the pipeline in Section 2 first to populate the chain inspection.")
else:
    stage_results = st.session_state["chain_results"]
    topic_val = st.session_state.get("chain_topic", "")

    inspections = [
        {
            "stage": "Stage 1 — Researcher",
            "color": "#43A047",
            "input_label": "Input (topic only):",
            "input_text": f"Topic: {topic_val}",
            "output_label": "Output (facts):",
            "output_text": stage_results["researcher"]["output"],
            "transform": "Expansion — one sentence → 6–8 specific facts",
        },
        {
            "stage": "Stage 2 — Outliner",
            "color": "#8E24AA",
            "input_label": "Input (topic + facts):",
            "input_text": stage_results["outliner"].get("user_prompt", ""),
            "output_label": "Output (outline):",
            "output_text": stage_results["outliner"]["output"],
            "transform": "Organisation — unordered facts → logical hierarchy",
        },
        {
            "stage": "Stage 3 — Drafter",
            "color": "#1E88E5",
            "input_label": "Input (topic + facts + outline):",
            "input_text": stage_results["drafter"].get("user_prompt", ""),
            "output_label": "Output (article):",
            "output_text": stage_results["drafter"]["output"],
            "transform": "Composition — structure + facts → flowing prose",
        },
    ]

    for ins in inspections:
        with st.expander(f"{ins['stage']} — {ins['transform']}", expanded=False):
            la, lb = st.columns(2)
            with la:
                st.markdown(
                    f"<div style='border-top:3px solid {ins['color']};padding:4px 0 6px;'>"
                    f"<strong style='color:{ins['color']};'>{ins['input_label']}</strong></div>",
                    unsafe_allow_html=True,
                )
                st.text_area(
                    label="",
                    value=ins["input_text"],
                    height=220,
                    disabled=True,
                    key=f"in_{ins['stage']}",
                    label_visibility="collapsed",
                )
            with lb:
                st.markdown(
                    f"<div style='border-top:3px solid {ins['color']};padding:4px 0 6px;'>"
                    f"<strong style='color:{ins['color']};'>{ins['output_label']}</strong></div>",
                    unsafe_allow_html=True,
                )
                st.text_area(
                    label="",
                    value=ins["output_text"],
                    height=220,
                    disabled=True,
                    key=f"out_{ins['stage']}",
                    label_visibility="collapsed",
                )
            st.info(f"**Transformation:** {ins['transform']}")

    u1 = stage_results["researcher"]["usage"]
    u2 = stage_results["outliner"]["usage"]
    u3 = stage_results["drafter"]["usage"]

    st.markdown("**Token cost per stage:**")
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Stage 1 input tokens", u1["input_tokens"])
    tc2.metric("Stage 2 input tokens", u2["input_tokens"])
    tc3.metric("Stage 3 input tokens", u3["input_tokens"])
    st.caption("Notice how Stage 3 receives far more input tokens — it inherits all prior outputs.")
