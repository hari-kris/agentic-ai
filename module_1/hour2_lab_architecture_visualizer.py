"""
Hour 2 Lab — Architecture Visualizer
Module 1 | Agentic AI Foundations

Students describe a system in plain English. Claude returns structured JSON
identifying which of the six core components are present and how each works.
Streamlit renders the result as colour-coded component cards.

Run: streamlit run hour2_lab_architecture_visualizer.py
"""

import json
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Hour 2 — Architecture Visualizer", page_icon="🏗️", layout="wide")
st.title("Hour 2 Lab — Architecture Visualizer")
st.caption("Module 1 | Agentic AI Foundations")

st.markdown(
    "Describe an agentic system in plain English. Claude identifies which of the "
    "**six core components** are present and returns a structured breakdown."
)

SYSTEM_PROMPT = """\
You are an expert agentic AI architect.

The six core components of any agentic system are:
1. Model     — the LLM that reasons and generates output (the brain)
2. Tools     — Python functions or external APIs the model can call (the hands)
3. Memory    — short-term (context window) or long-term (vector store) persistence (the notebook)
4. Planner   — decomposes a high-level goal into concrete subtasks (the strategist)
5. Executor  — carries out individual subtasks and produces intermediate outputs (the worker)
6. Evaluator — reviews output quality and triggers revision loops if needed (the judge)

Given a system description, identify which components are present and describe how each is implemented.

Return ONLY valid JSON — no markdown fences, no explanation, just the JSON object:
{
  "system_name": "a short descriptive name for this system",
  "model":     {"present": true,  "description": "how the model is used"},
  "tools":     {"present": false, "description": null},
  "memory":    {"present": true,  "description": "how memory works"},
  "planner":   {"present": true,  "description": "how planning works"},
  "executor":  {"present": true,  "description": "how execution works"},
  "evaluator": {"present": false, "description": null},
  "agentic_score": 4
}
Use null for description when a component is absent. agentic_score is the count of components where present is true.\
"""

EXAMPLE = (
    "A research agent that takes a topic from the user, searches the web using a search API, "
    "reads the top 5 articles, stores key facts in a local database, drafts a 3-paragraph summary, "
    "then checks whether all claims in the summary are supported by the sources and rewrites any "
    "unsupported claims before returning the final output."
)

COMPONENTS = ["model", "tools", "memory", "planner", "executor", "evaluator"]

COMPONENT_META = {
    "model":     {"label": "Model (Brain)",       "color": "#1E88E5", "icon": "🧠"},
    "tools":     {"label": "Tools (Hands)",       "color": "#FB8C00", "icon": "🔧"},
    "memory":    {"label": "Memory (Notebook)",   "color": "#43A047", "icon": "📓"},
    "planner":   {"label": "Planner (Strategist)","color": "#8E24AA", "icon": "📋"},
    "executor":  {"label": "Executor (Worker)",   "color": "#00897B", "icon": "⚙️"},
    "evaluator": {"label": "Evaluator (Judge)",   "color": "#E53935", "icon": "🔴"},
}

description = st.text_area(
    "System description:",
    value=EXAMPLE,
    height=160,
)

if st.button("Identify Components", type="primary"):
    if not description.strip():
        st.warning("Enter a system description first.")
    else:
        with st.spinner("Claude is analysing the architecture..."):
            raw, usage = chat(SYSTEM_PROMPT, description.strip(), max_tokens=800)

        # Strip markdown fences if Claude added them despite instructions
        clean = raw.strip()
        for fence in ("```json", "```"):
            clean = clean.removeprefix(fence).removesuffix("```").strip()

        try:
            data = json.loads(clean)
        except json.JSONDecodeError:
            st.error("Claude returned unexpected output. Showing raw response:")
            st.code(raw)
            st.stop()

        st.divider()
        score = data.get("agentic_score", 0)
        st.subheader(f"System: {data.get('system_name', 'Unnamed')}")
        st.progress(score / 6, text=f"Agentic completeness: {score} / 6 components present")

        st.subheader("Component Breakdown")
        cols = st.columns(2)

        for i, comp in enumerate(COMPONENTS):
            meta = COMPONENT_META[comp]
            comp_data = data.get(comp, {})
            present = comp_data.get("present", False)
            desc = comp_data.get("description") or "_Not present in this system._"
            color = meta["color"]
            icon = meta["icon"]
            status = "✅" if present else "❌"

            with cols[i % 2]:
                st.markdown(
                    f"""<div style="border-left:5px solid {color};padding:10px 14px;
                    margin-bottom:12px;background:#f9f9f9;border-radius:5px;">
                    <strong style="color:{color};">{icon} {status} {meta['label']}</strong><br>
                    <span style="font-size:0.9em;">{desc}</span></div>""",
                    unsafe_allow_html=True,
                )

        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("Input tokens", usage["input_tokens"])
        c2.metric("Output tokens", usage["output_tokens"])

        with st.expander("Raw JSON from Claude"):
            st.json(data)

        with st.expander("View the system prompt sent to Claude"):
            st.code(SYSTEM_PROMPT, language="text")

st.divider()
with st.expander("Six components — colour reference (matches course board)"):
    st.markdown(
        """
| Colour | Component | Role |
|---|---|---|
| 🔵 Blue | Model | The LLM brain that reasons and generates |
| 🟠 Orange | Tools | External functions the model can call |
| 🟢 Green | Memory | Short-term context or long-term vector store |
| 🟣 Purple | Planner | Breaks the goal into concrete subtasks |
| 🩵 Teal | Executor | Carries out individual subtasks |
| 🔴 Red | Evaluator | Reviews quality and triggers revision |
"""
    )
