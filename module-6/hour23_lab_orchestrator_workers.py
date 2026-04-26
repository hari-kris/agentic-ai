"""
Hour 23 Lab — Orchestrator-Workers Architecture
Module 6 | Multi-Agent Systems

A central orchestrator receives a complex goal, decomposes it into a prioritised
task list for four typed workers, each worker executes its task, and the orchestrator
synthesises an executive brief from all results.

Run: streamlit run module-6/hour23_lab_orchestrator_workers.py
"""

import json
import streamlit as st
import pandas as pd
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 23 — Orchestrator-Workers", page_icon="🏭", layout="wide")
st.title("🏭 Hour 23 — Orchestrator-Workers Architecture")
st.caption("Module 6 | Multi-Agent Systems")

st.markdown("""
The **orchestrator-workers** architecture is the "manager-team" pattern. One orchestrator holds the
goal and assigns discrete subtasks to specialised workers. Workers are **typed** — each only handles
the work that matches its role. The orchestrator then collects all results and produces a unified
executive brief. The critical insight: **the orchestrator's output is a task list, not the answer.**
If the orchestrator is writing paragraphs of analysis, you need a Worker for that.
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 23 Guide")
    st.markdown("""
**Sections in this lab:**
1. Architecture diagram
2. Goal decomposition — orchestrator → task list JSON
3. Worker execution — 4 typed workers run their tasks
4. Executive brief — orchestrator synthesises all results

**What to observe:**
- The orchestrator assigns work it cannot do itself
- Workers receive only their own task instruction
- The synthesiser reads all four worker outputs
- Token cost scales linearly with number of workers
""")
    st.divider()
    st.markdown("""
**Experiment ideas:**
- Try a B2B SaaS launch goal — observe which workers get the longest tasks
- Try a cost-cutting initiative — does the Risk worker flag more concerns?
- Compare the goal_summary the orchestrator generates vs the raw goal you typed
""")
    st.divider()
    st.info("**Key principle:** The orchestrator assigns work it cannot do itself. The orchestrator's output is a task list — not the answer.")

# ── Worker Types ───────────────────────────────────────────────────────────────
WORKER_TYPES = {
    "RESEARCHER": {
        "color": "#43A047", "bg": "#E8F5E9", "icon": "🔬", "label": "Research Worker",
        "system": """\
You are a research worker. Your job is to answer the specific research task you are given
with concrete facts, data points, market context, and relevant examples.
Write 180–220 words. Be specific — no vague generalisations. Use clear paragraphs.\
""",
    },
    "ANALYST": {
        "color": "#1E88E5", "bg": "#E3F2FD", "icon": "📊", "label": "Analysis Worker",
        "system": """\
You are an analysis worker. Your job is to produce structured analysis for the specific
task you are given: identify patterns, quantify where possible, and draw conclusions.
Write 180–220 words. Use clear structure with concise paragraphs.\
""",
    },
    "WRITER": {
        "color": "#FB8C00", "bg": "#FFF3E0", "icon": "✍️", "label": "Writing Worker",
        "system": """\
You are a writing worker. Your job is to produce clear, professional written content
for the specific task you are given. Focus on clarity and professional tone.
Write 150–200 words. Prioritise readability.\
""",
    },
    "RISK": {
        "color": "#E53935", "bg": "#FFEBEE", "icon": "⚠️", "label": "Risk Worker",
        "system": """\
You are a risk analysis worker. Your job is to identify, assess, and frame the risks
relevant to the specific task you are given. Identify 3–5 specific risks.
For each: name the risk, explain why it matters, and suggest a mitigation.
Write 180–220 words.\
""",
    },
}

# ── System Prompts ─────────────────────────────────────────────────────────────
GOAL_DECOMPOSER_SYSTEM = """\
You are a project orchestrator. Given a complex business or product goal, decompose it
into a prioritised task list for your team of four typed workers.

Worker types available:
- RESEARCHER: market research, fact-finding, competitive analysis, data gathering
- ANALYST: data analysis, pattern identification, feasibility assessment, metrics
- WRITER: producing written deliverables, messaging, documentation, communications
- RISK: identifying risks, failure modes, compliance concerns, mitigation strategies

Rules:
- Create exactly 4 tasks — one per worker type, in that order: RESEARCHER, ANALYST, WRITER, RISK
- Each task instruction must be specific and actionable — one clear instruction per task
- priority must be "high", "medium", or "low"

Return ONLY valid JSON — no markdown fences, no commentary:
{"goal_summary": "one sentence restating the goal", "tasks": [{"id": 1, "worker": "RESEARCHER", "instruction": "...", "priority": "high"}, {"id": 2, "worker": "ANALYST", "instruction": "...", "priority": "high"}, {"id": 3, "worker": "WRITER", "instruction": "...", "priority": "medium"}, {"id": 4, "worker": "RISK", "instruction": "...", "priority": "medium"}]}\
"""

SYNTHESISER_SYSTEM = """\
You are a senior project orchestrator. You have received completed work from four specialist workers.
Write a 300–350 word executive brief using the following markdown structure:

## Goal
One sentence stating the objective.

## Key Findings
Summarise the key findings from each worker (Research, Analysis, Writing, Risk) in 2–3 sentences each.

## Next Steps
List the top 3 actionable next steps as bullet points.

## Feasibility Assessment
One paragraph (3–4 sentences) assessing overall feasibility and confidence level.\
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_json(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


def priority_badge(priority: str) -> str:
    colors = {"high": "#E53935", "medium": "#FB8C00", "low": "#43A047"}
    color = colors.get(priority.lower(), "#8E24AA")
    return f"<span style='background:{color};color:white;border-radius:4px;padding:2px 8px;font-size:0.78em;font-weight:bold;'>{priority.upper()}</span>"


PRESET_GOALS = [
    "Custom goal — type below",
    "Launch a B2B SaaS project management tool targeting mid-size engineering teams",
    "Expand our e-commerce business into the German market within 12 months",
    "Build an internal AI assistant for our legal team to speed up contract review",
    "Reduce customer churn by 25% for our subscription fitness app",
    "Develop a sustainability reporting programme for our manufacturing company",
]

# ── Section 1 — Architecture Diagram ──────────────────────────────────────────
st.markdown("---")
st.subheader("1 — Orchestrator-Workers Architecture")

d_cols = st.columns([1.8, 0.2, 2.2, 0.2, 1.8])

with d_cols[0]:
    st.markdown(
        "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;border-radius:8px;"
        "padding:16px;text-align:center;min-height:220px;'>"
        "<div style='font-size:1.8em;'>🎯</div>"
        "<div style='font-weight:bold;color:#8E24AA;margin:6px 0;'>[ORCHESTRATOR]</div>"
        "<div style='font-size:0.78em;color:#555;margin-top:8px;'>"
        "Receives goal.<br>Returns task list JSON.<br>Assigns one task per worker.<br>Does NOT do the work itself.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with d_cols[1]:
    st.markdown("<div style='text-align:center;font-size:1.5em;margin-top:80px;'>→</div>", unsafe_allow_html=True)

with d_cols[2]:
    wt_rows = st.columns(2)
    worker_list = list(WORKER_TYPES.items())
    for i, (wtype, meta) in enumerate(worker_list):
        col = wt_rows[i % 2]
        with col:
            st.markdown(
                f"<div style='border-top:4px solid {meta['color']};background:{meta['bg']};"
                f"border-radius:6px;padding:10px;text-align:center;margin-bottom:8px;'>"
                f"<div style='font-size:1.3em;'>{meta['icon']}</div>"
                f"<div style='font-weight:bold;color:{meta['color']};font-size:0.78em;'>{wtype}</div>"
                f"<div style='font-size:0.72em;color:#555;'>{meta['label']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

with d_cols[3]:
    st.markdown("<div style='text-align:center;font-size:1.5em;margin-top:80px;'>→</div>", unsafe_allow_html=True)

with d_cols[4]:
    st.markdown(
        "<div style='border-top:4px solid #00897B;background:#E0F2F1;border-radius:8px;"
        "padding:16px;text-align:center;min-height:220px;'>"
        "<div style='font-size:1.8em;'>📋</div>"
        "<div style='font-weight:bold;color:#00897B;margin:6px 0;'>Executive Brief</div>"
        "<div style='font-size:0.78em;color:#555;margin-top:8px;'>"
        "Synthesised from all four worker outputs.<br>Produced by the orchestrator<br>in a second pass.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with st.expander("See system prompts"):
    tabs = st.tabs(["Goal Decomposer", "Research Worker", "Analysis Worker", "Writing Worker", "Risk Worker", "Synthesiser"])
    prompts = [GOAL_DECOMPOSER_SYSTEM] + [WORKER_TYPES[w]["system"] for w in ["RESEARCHER", "ANALYST", "WRITER", "RISK"]] + [SYNTHESISER_SYSTEM]
    for tab, prompt in zip(tabs, prompts):
        with tab:
            st.code(prompt, language="text")

# ── Section 2 — Goal Decomposition ────────────────────────────────────────────
st.markdown("---")
st.subheader("2 — Goal Decomposition")
st.markdown("The orchestrator reads the goal and returns a prioritised task list — one task per worker type.")

preset_goal = st.selectbox("Choose a preset goal or write your own:", PRESET_GOALS, key="s2_goal_preset")
goal_val = "" if preset_goal == PRESET_GOALS[0] else preset_goal
goal = st.text_area("Business or product goal:", value=goal_val, height=80, key="s2_goal",
                     placeholder="Describe a complex business or product goal…")

if st.button("▶ Decompose Goal", type="primary", disabled=not goal.strip()):
    with st.spinner("Orchestrator decomposing goal into task list…"):
        raw, usage = chat(GOAL_DECOMPOSER_SYSTEM, goal.strip(), max_tokens=600, temperature=0.3)
    task_list = parse_json(raw)
    if task_list is None:
        st.error("Failed to parse task list JSON. Showing raw output:")
        st.code(raw)
        st.stop()
    st.session_state["task_list"] = task_list
    st.session_state["goal_text"] = goal.strip()
    st.session_state["decomposer_usage"] = usage

if "task_list" in st.session_state:
    task_list = st.session_state["task_list"]
    dec_usage = st.session_state["decomposer_usage"]

    st.markdown(
        f"<div style='border-top:4px solid #8E24AA;background:#F3E5F5;border-radius:6px;padding:10px 14px;margin-bottom:12px;'>"
        f"<strong style='color:#8E24AA;'>🎯 Goal Summary:</strong> {task_list.get('goal_summary', '')}</div>",
        unsafe_allow_html=True,
    )

    for task in task_list.get("tasks", []):
        wtype = task.get("worker", "")
        meta = WORKER_TYPES.get(wtype, {"color": "#8E24AA", "bg": "#F3E5F5", "icon": "🔧", "label": wtype})
        t_cols = st.columns([1.2, 4, 1, 0.5])
        with t_cols[0]:
            st.markdown(
                f"<div style='border-top:3px solid {meta['color']};background:{meta['bg']};"
                f"border-radius:4px;padding:6px 10px;text-align:center;'>"
                f"<span style='font-size:1.1em;'>{meta['icon']}</span> "
                f"<strong style='color:{meta['color']};font-size:0.78em;'>{wtype}</strong></div>",
                unsafe_allow_html=True,
            )
        with t_cols[1]:
            st.markdown(task.get("instruction", ""))
        with t_cols[2]:
            st.markdown(priority_badge(task.get("priority", "medium")), unsafe_allow_html=True)
        with t_cols[3]:
            st.markdown(f"<div style='text-align:center;color:#90A4AE;font-size:0.85em;'>#{task.get('id', '')}</div>", unsafe_allow_html=True)

    with st.expander("Raw task JSON"):
        st.code(json.dumps(task_list, indent=2), language="json")

    m1, m2 = st.columns(2)
    m1.metric("Decomposer input tokens", dec_usage.get("input_tokens", 0))
    m2.metric("Decomposer output tokens", dec_usage.get("output_tokens", 0))

# ── Section 3 — Worker Execution ──────────────────────────────────────────────
st.markdown("---")
st.subheader("3 — Worker Execution")
st.markdown("Each task is dispatched to its assigned worker. Workers receive only their own task instruction — not the full goal or other workers' outputs.")

if "task_list" not in st.session_state:
    st.info("Run Section 2 first to generate the task list.")
else:
    if st.button("▶ Run All Workers", type="primary"):
        task_list = st.session_state["task_list"]
        goal_text = st.session_state["goal_text"]
        results = []
        for task in task_list.get("tasks", []):
            wtype = task.get("worker", "")
            meta = WORKER_TYPES.get(wtype, {})
            system = meta.get("system", "")
            user_msg = f"Your task: {task['instruction']}\n\nProject context: {goal_text}"
            with st.spinner(f"Running {wtype} worker (Task {task['id']})…"):
                output, usage = chat(system, user_msg, max_tokens=400, temperature=0.4)
            results.append({
                "task_id": task["id"],
                "worker": wtype,
                "instruction": task["instruction"],
                "output": output,
                "usage": usage,
            })
        st.session_state["worker_results"] = results

    if "worker_results" in st.session_state:
        results = st.session_state["worker_results"]
        for r in results:
            wtype = r["worker"]
            meta = WORKER_TYPES.get(wtype, {"color": "#8E24AA", "bg": "#F3E5F5", "icon": "🔧", "label": wtype})
            with st.expander(f"Worker {r['task_id']} — {meta['label']} ({wtype})"):
                st.markdown(
                    f"<div style='border-top:4px solid {meta['color']};background:{meta['bg']};"
                    f"border-radius:6px;padding:8px 14px;margin-bottom:10px;'>"
                    f"<strong style='color:{meta['color']};'>{meta['icon']} [{wtype}] {meta['label']}</strong><br>"
                    f"<span style='font-size:0.82em;color:#555;'>Task: {r['instruction']}</span></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(r["output"])
                u = r["usage"]
                st.caption(f"Input: {u.get('input_tokens', 0)} | Output: {u.get('output_tokens', 0)} tokens")

        # Token ledger
        dec_usage = st.session_state.get("decomposer_usage", {})
        rows = [{"Agent": "🎯 Goal Decomposer", "Role": "Orchestration", "Input Tokens": dec_usage.get("input_tokens", 0), "Output Tokens": dec_usage.get("output_tokens", 0)}]
        for r in results:
            meta = WORKER_TYPES.get(r["worker"], {})
            rows.append({
                "Agent": f"{meta.get('icon', '🔧')} {meta.get('label', r['worker'])}",
                "Role": r["worker"],
                "Input Tokens": r["usage"].get("input_tokens", 0),
                "Output Tokens": r["usage"].get("output_tokens", 0),
            })
        df = pd.DataFrame(rows)
        df["Total"] = df["Input Tokens"] + df["Output Tokens"]
        total_row = pd.DataFrame([{"Agent": "**TOTAL**", "Role": "", "Input Tokens": df["Input Tokens"].sum(), "Output Tokens": df["Output Tokens"].sum(), "Total": df["Total"].sum()}])
        df_display = pd.concat([df, total_row], ignore_index=True)
        st.markdown("**Token ledger:**")
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# ── Section 4 — Executive Brief ────────────────────────────────────────────────
st.markdown("---")
st.subheader("4 — Executive Brief")
st.markdown("The orchestrator reads all four worker outputs and synthesises them into an executive brief.")

if "worker_results" not in st.session_state:
    st.info("Run Section 3 first to execute the workers.")
else:
    if st.button("▶ Synthesise Executive Brief", type="primary"):
        results = st.session_state["worker_results"]
        goal_text = st.session_state.get("goal_text", "")

        synth_user = f"Project goal: {goal_text}\n\n"
        for r in results:
            synth_user += f"[{r['worker']} WORKER — Task {r['task_id']}]\n{r['output']}\n\n"

        with st.spinner("Orchestrator synthesising executive brief…"):
            brief, usage = chat(SYNTHESISER_SYSTEM, synth_user, max_tokens=700, temperature=0.5)

        st.session_state["executive_brief"] = brief
        st.session_state["brief_usage"] = usage

    if "executive_brief" in st.session_state:
        brief = st.session_state["executive_brief"]
        usage = st.session_state["brief_usage"]

        st.markdown(
            "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;"
            "border-radius:6px;padding:10px 14px;margin-bottom:12px;'>"
            "<strong style='color:#8E24AA;'>🎯 [ORCHESTRATOR] Executive Brief</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(brief)

        results = st.session_state.get("worker_results", [])
        total_in = (
            st.session_state.get("decomposer_usage", {}).get("input_tokens", 0)
            + sum(r["usage"].get("input_tokens", 0) for r in results)
            + usage.get("input_tokens", 0)
        )
        total_out = (
            st.session_state.get("decomposer_usage", {}).get("output_tokens", 0)
            + sum(r["usage"].get("output_tokens", 0) for r in results)
            + usage.get("output_tokens", 0)
        )
        m1, m2, m3 = st.columns(3)
        m1.metric("Total LLM calls", 6)
        m2.metric("Total input tokens", total_in)
        m3.metric("Total output tokens", total_out)
