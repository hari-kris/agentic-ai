"""
Hour 19 Lab — Orchestrator-Subagents Pattern
Module 5 | Core Agentic Patterns II

An orchestrator dynamically decides which subagents to spawn and how to coordinate them.
Unlike fixed fan-out, the orchestrator reads the task and assembles the right team.

Run: streamlit run module-5/hour19_lab_orchestrator_subagents.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 19 — Orchestrator-Subagents", page_icon="🎯", layout="wide")
st.title("🎯 Hour 19 — Orchestrator-Subagents Pattern")
st.caption("Module 5 | Core Agentic Patterns II")

st.markdown("""
The **Orchestrator-Subagents Pattern** uses a coordinator agent that *dynamically* decides
which subagents to spawn, what tasks to assign each, and how to synthesise their outputs.

Unlike parallelisation (which fans out to a *fixed* set of agents), an orchestrator:
- Reads the goal and decides the best team composition
- Issues tailored task briefs to each subagent
- Checks output quality and re-delegates if needed
- Synthesises all results into a final output

This lab explores:
1. **Dynamic research orchestrator** — decomposes a question into sub-questions, assigns researchers, synthesises
2. **Document processing orchestrator** — detects document type, selects appropriate specialists
3. **Quality-gated orchestration** — orchestrator re-delegates if a subagent output is too weak
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 19 Guide")
    st.markdown("""
**Sections in this lab:**
1. **Architecture diagram** — orchestrator and dynamic subagent team
2. **Research orchestrator** — decomposes question → research subagents → synthesis
3. **Document processor** — detects type → assigns specialists → processes
4. **Quality-gated** — orchestrator checks quality and re-delegates on failure

**What to observe:**
- The orchestrator's decomposition shapes the quality of the final output
- Each subagent receives only what it needs — no unnecessary context
- Re-delegation adds cost but improves quality when needed
- Token cost is higher than a single call — the orchestrator pays for itself through quality
""")
    st.divider()
    st.markdown("**Experiment ideas:**")
    st.markdown("- Submit a multi-part research question — see how the orchestrator decomposes it")
    st.markdown("- Paste different document types (code, legal text, news article) — does the orchestrator pick different specialists?")
    st.markdown("- Lower the quality threshold to trigger more re-delegations")
    st.divider()
    st.info("**Key principle:** The orchestrator does not do the work — it delegates, coordinates, and synthesises. If it is doing detailed research itself, you need subagents.")

# ── System Prompts ─────────────────────────────────────────────────────────────
RESEARCH_ORCHESTRATOR_SYSTEM = """\
You are a research orchestrator. Given a research question, decompose it into exactly
2–3 focused sub-questions that together fully answer the original question.

Rules:
- Each sub-question should be independently answerable
- Sub-questions should be complementary — together they cover the full topic
- Keep sub-questions specific and concrete

Return ONLY valid JSON — no markdown fences:
{
  "sub_questions": ["sub-question 1", "sub-question 2", "sub-question 3"],
  "rationale": "one sentence explaining the decomposition logic"
}\
"""

RESEARCHER_SUBAGENT_SYSTEM = """\
You are a focused researcher. Answer the specific sub-question you are given accurately
and concisely. Provide concrete facts, examples, and data where available.
Write 2–4 focused sentences. Do not pad your answer.\
"""

RESEARCH_SYNTHESISER_SYSTEM = """\
You are a research synthesiser. You will receive a main research question and findings
from 2–3 focused sub-researchers.

Write a comprehensive 200–280 word research summary that:
1. Directly answers the main research question
2. Integrates the sub-findings coherently
3. Notes any tensions or trade-offs between findings
4. Ends with a clear takeaway

Write in clear professional prose. Do not number sections.\
"""

DOC_TYPE_ROUTER_SYSTEM = """\
You are a document type classifier. Given a document, identify its type so appropriate
processing specialists can be assigned.

Document types:
- TECHNICAL_SPEC: technical specification, API documentation, engineering design document
- BUSINESS_MEMO: business proposal, meeting notes, policy document, executive memo
- NEWS_ARTICLE: news report, press release, journalistic content
- LEGAL_TEXT: contract, terms of service, compliance document, legal agreement
- ACADEMIC: research paper, academic article, scientific report

Return ONLY valid JSON — no markdown fences:
{
  "doc_type": "TECHNICAL_SPEC|BUSINESS_MEMO|NEWS_ARTICLE|LEGAL_TEXT|ACADEMIC",
  "confidence": 0.0,
  "key_features": "one sentence describing what makes this document that type"
}\
"""

TECHNICAL_PROCESSOR_SYSTEM = """\
You are a technical documentation analyst. Analyse the technical document and extract:
1. Core technical components or systems described
2. Key technical requirements or specifications
3. Any ambiguities or missing information that should be clarified
Return as a structured analysis in 150–200 words.\
"""

BUSINESS_PROCESSOR_SYSTEM = """\
You are a business document analyst. Analyse the business document and extract:
1. The main objective or decision being proposed
2. Key stakeholders and their interests
3. Risks or dependencies that need attention
Return as a structured analysis in 150–200 words.\
"""

NEWS_PROCESSOR_SYSTEM = """\
You are a news analysis specialist. Analyse the news content and extract:
1. The core event or development being reported
2. Key facts (who, what, when, where)
3. Implications or significance of the news
Return as a structured analysis in 150–200 words.\
"""

LEGAL_PROCESSOR_SYSTEM = """\
You are a legal document analyst. Analyse the legal document and extract:
1. The key obligations or rights being established
2. Any notable restrictions or conditions
3. Potential areas of ambiguity or concern
Note: This is a structural analysis, not legal advice.
Return as a structured analysis in 150–200 words.\
"""

ACADEMIC_PROCESSOR_SYSTEM = """\
You are an academic document analyst. Analyse the academic content and extract:
1. The research question or thesis being addressed
2. Key findings or arguments presented
3. Limitations or areas for further research noted
Return as a structured analysis in 150–200 words.\
"""

QUALITY_ASSESSOR_SYSTEM = """\
You are a quality assessor for research outputs. Evaluate the provided research answer
on two criteria (1–5 scale):

- depth: does it provide specific facts, evidence, and concrete details? (1=vague, 5=specific)
- completeness: does it fully answer the question asked? (1=partial, 5=thorough)

Return ONLY valid JSON — no markdown fences:
{"depth": N, "completeness": N, "feedback": "one specific improvement needed"}\
"""

DOC_PROCESSORS = {
    "TECHNICAL_SPEC": (TECHNICAL_PROCESSOR_SYSTEM, "#1E88E5", "#E3F2FD", "⚙️"),
    "BUSINESS_MEMO": (BUSINESS_PROCESSOR_SYSTEM, "#8E24AA", "#F3E5F5", "💼"),
    "NEWS_ARTICLE": (NEWS_PROCESSOR_SYSTEM, "#FB8C00", "#FFF3E0", "📰"),
    "LEGAL_TEXT": (LEGAL_PROCESSOR_SYSTEM, "#E53935", "#FFEBEE", "⚖️"),
    "ACADEMIC": (ACADEMIC_PROCESSOR_SYSTEM, "#43A047", "#E8F5E9", "🎓"),
}


def parse_json(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


# ── Section 1: Architecture Diagram ───────────────────────────────────────────
st.divider()
st.subheader("1 — The Orchestrator-Subagents Pipeline")

diag_cols = st.columns([1.5, 0.3, 2.5, 0.3, 1.5])

with diag_cols[0]:
    st.markdown(
        "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;border-radius:6px;"
        "padding:14px;text-align:center;min-height:180px;'>"
        "<div style='font-size:2em;'>🎯</div>"
        "<div style='font-weight:bold;color:#8E24AA;margin:6px 0;'>[ORCHESTRATOR]</div>"
        "<div style='font-size:0.82em;color:#444;'>Reads the goal.<br/>Decides team composition.<br/>Issues task briefs.<br/>Synthesises results.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with diag_cols[1]:
    st.markdown(
        "<div style='display:flex;align-items:center;justify-content:center;"
        "height:180px;font-size:1.8em;color:#999;'>⇄</div>",
        unsafe_allow_html=True,
    )

with diag_cols[2]:
    sub_cols = st.columns(3)
    for i, (col, (label, color, icon)) in enumerate(zip(sub_cols, [
        ("SUBAGENT 1", "#1E88E5", "🔵"),
        ("SUBAGENT 2", "#43A047", "🟢"),
        ("SUBAGENT 3", "#E53935", "🔴"),
    ])):
        with col:
            st.markdown(
                f"<div style='border-top:4px solid {color};background:#FAFAFA;"
                f"border-radius:6px;padding:10px;text-align:center;min-height:130px;'>"
                f"<div style='font-size:1.5em;'>{icon}</div>"
                f"<div style='font-weight:bold;color:{color};font-size:0.8em;margin:4px 0;'>{label}</div>"
                f"<div style='font-size:0.75em;color:#555;'>Focused task.<br/>One responsibility.<br/>Structured output.</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

with diag_cols[3]:
    st.markdown(
        "<div style='display:flex;align-items:center;justify-content:center;"
        "height:180px;font-size:1.8em;color:#999;'>→</div>",
        unsafe_allow_html=True,
    )

with diag_cols[4]:
    st.markdown(
        "<div style='border-top:4px solid #00897B;background:#E0F2F1;border-radius:6px;"
        "padding:14px;text-align:center;min-height:180px;'>"
        "<div style='font-size:2em;'>✅</div>"
        "<div style='font-weight:bold;color:#00897B;margin:6px 0;'>Final Output</div>"
        "<div style='font-size:0.82em;color:#444;'>Synthesised from all subagent outputs.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown("""
**Key difference from parallelisation:** The orchestrator decides *which* subagents to use
and *what* to tell each one. In parallelisation, the agent set is fixed before the input arrives.
""")

with st.expander("See system prompts"):
    tabs = st.tabs(["Research Orchestrator", "Researcher Sub", "Synthesiser", "Doc Type Router", "Tech Processor", "Business Processor", "Quality Assessor"])
    for tab, prompt in zip(tabs, [
        RESEARCH_ORCHESTRATOR_SYSTEM, RESEARCHER_SUBAGENT_SYSTEM, RESEARCH_SYNTHESISER_SYSTEM,
        DOC_TYPE_ROUTER_SYSTEM, TECHNICAL_PROCESSOR_SYSTEM, BUSINESS_PROCESSOR_SYSTEM, QUALITY_ASSESSOR_SYSTEM,
    ]):
        with tab:
            st.code(prompt, language="text")

# ── Section 2: Dynamic Research Orchestrator ──────────────────────────────────
st.divider()
st.subheader("2 — Dynamic Research Orchestrator")

st.markdown("""
The orchestrator decomposes your research question into 2–3 sub-questions,
assigns each to a focused researcher subagent, then synthesises the findings.
""")

RESEARCH_PRESETS = [
    "Custom research question — type below",
    "How do large language models work and what are their main limitations?",
    "What are the environmental impacts of cryptocurrency mining?",
    "How does sleep deprivation affect cognitive performance and long-term health?",
    "What caused the 2008 financial crisis and what reforms followed?",
    "How do vaccines work and why do some people experience side effects?",
]

sel_research = st.selectbox("Pick a preset research question or write your own:", RESEARCH_PRESETS, key="research_preset")
research_q = st.text_area(
    "Research question:",
    value="" if sel_research == RESEARCH_PRESETS[0] else sel_research,
    height=70,
    key="research_question",
)

if st.button("▶ Run Research Orchestrator", type="primary", disabled=not research_q.strip()):
    total_in, total_out = 0, 0

    progress = st.progress(0, text="Orchestrator decomposing question…")
    with st.spinner("Orchestrator planning…"):
        raw_plan, u_orch = chat(RESEARCH_ORCHESTRATOR_SYSTEM, research_q.strip(), max_tokens=400, temperature=0.3)
    total_in += u_orch["input_tokens"]
    total_out += u_orch["output_tokens"]

    plan = parse_json(raw_plan)
    if not plan:
        st.error("Orchestrator returned unexpected output:")
        st.code(raw_plan)
        st.stop()

    sub_questions = plan.get("sub_questions", [])
    rationale = plan.get("rationale", "")
    progress.progress(20, text=f"Orchestrator created {len(sub_questions)} sub-questions…")

    subagent_results = []
    for i, sub_q in enumerate(sub_questions):
        with st.spinner(f"Researcher subagent {i+1}/{len(sub_questions)}…"):
            sub_answer, u_sub = chat(
                RESEARCHER_SUBAGENT_SYSTEM,
                f"Research sub-question: {sub_q}",
                max_tokens=250,
                temperature=0.4,
            )
        total_in += u_sub["input_tokens"]
        total_out += u_sub["output_tokens"]
        subagent_results.append({"question": sub_q, "answer": sub_answer, "usage": u_sub})
        progress.progress(20 + (i + 1) * 22, text=f"Subagent {i+1} done…")

    synth_user = (
        f"Main research question: {research_q.strip()}\n\n"
        + "\n\n".join(
            f"Sub-question {i+1}: {r['question']}\nFindings: {r['answer']}"
            for i, r in enumerate(subagent_results)
        )
    )
    with st.spinner("Synthesiser compiling final report…"):
        synthesis, u_synth = chat(RESEARCH_SYNTHESISER_SYSTEM, synth_user, max_tokens=500, temperature=0.5)
    total_in += u_synth["input_tokens"]
    total_out += u_synth["output_tokens"]
    progress.progress(100, text="Research complete.")

    st.session_state["research_results"] = {
        "plan": plan,
        "rationale": rationale,
        "sub_questions": sub_questions,
        "subagents": subagent_results,
        "synthesis": synthesis,
        "u_synth": u_synth,
        "totals": (total_in, total_out),
    }

if "research_results" in st.session_state:
    rr = st.session_state["research_results"]
    total_in, total_out = rr["totals"]

    st.markdown(
        f"<div style='border-left:4px solid #8E24AA;background:#F3E5F5;"
        f"padding:8px 14px;border-radius:4px;margin-bottom:12px;'>"
        f"<strong style='color:#8E24AA;'>Orchestrator decomposition:</strong> {rr['rationale']}"
        f"</div>",
        unsafe_allow_html=True,
    )

    sub_colors = ["#1E88E5", "#43A047", "#E53935"]
    for i, (sub, color) in enumerate(zip(rr["subagents"], sub_colors)):
        with st.expander(f"Subagent {i+1} — {sub['question']}", expanded=False):
            st.markdown(
                f"<div style='border-left:4px solid {color};padding:6px 12px;'>"
                f"<strong style='color:{color};'>Task:</strong> {sub['question']}"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(sub["answer"])
            u = sub["usage"]
            st.caption(f"Input: {u['input_tokens']} | Output: {u['output_tokens']} tokens")

    st.markdown("**🔗 Synthesised Research Report:**")
    with st.container(border=True):
        st.markdown(rr["synthesis"])

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM calls", 1 + len(rr["subagents"]) + 1)
    c2.metric("Total input tokens", total_in)
    c3.metric("Total output tokens", total_out)

# ── Section 3: Document Processing Orchestrator ────────────────────────────────
st.divider()
st.subheader("3 — Document Processing Orchestrator")

st.markdown("""
The orchestrator detects the document type and routes to the matching specialist processor.
Different document types need fundamentally different processing strategies.
""")

DOC_PROC_PRESETS = [
    "Custom document — paste below",
    """API Authentication Specification v2.1
All endpoints require Bearer token authentication via Authorization header.
Tokens expire after 3600 seconds. Refresh tokens via POST /auth/refresh.
Rate limits: 100 requests/minute per API key. Excess returns HTTP 429.
Error format: {"error": {"code": "string", "message": "string", "details": []}}
Required headers: Content-Type: application/json, X-API-Version: 2.1""",
    """Internal Memo: Q4 Budget Reallocation
To: Department Heads  From: CFO  Date: Nov 15, 2024
We are reallocating $2.4M from the infrastructure budget to the AI initiatives programme.
This is effective immediately. The infrastructure team will need to defer the server
upgrade planned for December. All department heads should resubmit their Q4 spend plans
by Nov 22 reflecting this change. Questions should go to finance@company.com.""",
    """Scientists at MIT have developed a new battery technology that can charge to 80% capacity
in under 5 minutes, three times faster than current lithium-ion batteries. The research,
published in Nature Energy, demonstrates an energy density of 340 Wh/kg. Commercial
production is expected to begin in 2026. The technology could enable electric vehicles with
ranges exceeding 600 miles. Lead researcher Dr. Sarah Chen said the breakthrough
addresses the single biggest barrier to EV adoption.""",
]

sel_doc_proc = st.selectbox("Pick a preset document or paste your own:", DOC_PROC_PRESETS, key="doc_proc_preset")
doc_proc_text = st.text_area(
    "Document:",
    value="" if sel_doc_proc == DOC_PROC_PRESETS[0] else sel_doc_proc,
    height=130,
    key="doc_proc_input",
)

if st.button("▶ Detect Type and Process", type="primary", disabled=not doc_proc_text.strip()):
    with st.spinner("Orchestrator detecting document type…"):
        raw_type, u_type = chat(DOC_TYPE_ROUTER_SYSTEM, doc_proc_text.strip(), max_tokens=200, temperature=0.1)

    doc_type_decision = parse_json(raw_type)
    if not doc_type_decision:
        st.error("Type detector parse error:")
        st.code(raw_type)
        st.stop()

    doc_type = doc_type_decision.get("doc_type", "BUSINESS_MEMO")
    doc_conf = doc_type_decision.get("confidence", 0.0)
    doc_features = doc_type_decision.get("key_features", "")

    processor_sys, color, bg, icon = DOC_PROCESSORS.get(doc_type, DOC_PROCESSORS["BUSINESS_MEMO"])
    with st.spinner(f"Running {doc_type} processor subagent…"):
        proc_output, u_proc = chat(
            processor_sys,
            f"Document to process:\n\n{doc_proc_text.strip()}",
            max_tokens=400,
            temperature=0.3,
        )

    st.session_state["doc_proc_result"] = {
        "doc_type": doc_type,
        "confidence": doc_conf,
        "features": doc_features,
        "output": proc_output,
        "color": color,
        "bg": bg,
        "icon": icon,
        "u_type": u_type,
        "u_proc": u_proc,
    }

if "doc_proc_result" in st.session_state:
    dp = st.session_state["doc_proc_result"]

    st.markdown("**Orchestrator Type Detection:**")
    dt_cols = st.columns([1, 1, 3])
    with dt_cols[0]:
        st.markdown(
            f"<div style='border-top:4px solid {dp['color']};background:{dp['bg']};"
            f"border-radius:6px;padding:12px;text-align:center;'>"
            f"<div style='font-size:1.5em;'>{dp['icon']}</div>"
            f"<div style='font-weight:bold;color:{dp['color']};font-size:0.9em;margin:4px 0;'>{dp['doc_type']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with dt_cols[1]:
        conf_color = "#43A047" if dp["confidence"] >= 0.7 else "#FB8C00"
        st.markdown(
            f"<div style='border-top:4px solid {conf_color};background:#FAFAFA;"
            f"border-radius:6px;padding:12px;text-align:center;'>"
            f"<div style='font-size:0.78em;color:{conf_color};font-weight:bold;'>CONFIDENCE</div>"
            f"<div style='font-size:1.5em;font-weight:bold;color:{conf_color};'>{dp['confidence']:.0%}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with dt_cols[2]:
        st.markdown(
            f"<div style='border-top:4px solid #8E24AA;background:#F3E5F5;"
            f"border-radius:6px;padding:12px;'>"
            f"<div style='font-size:0.78em;color:#8E24AA;font-weight:bold;'>KEY FEATURES</div>"
            f"<div style='font-size:0.9em;margin-top:4px;'>{dp['features']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div style='border-top:4px solid {dp['color']};background:{dp['bg']};"
        f"border-radius:6px;padding:12px 16px;margin-top:12px;'>"
        f"<strong style='color:{dp['color']};'>{dp['icon']} [{dp['doc_type']} PROCESSOR] Analysis</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(dp["output"])

    u_t = dp["u_type"]
    u_p = dp["u_proc"]
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM calls", 2)
    c2.metric("Type detector tokens", u_t.get("input_tokens", 0) + u_t.get("output_tokens", 0))
    c3.metric("Processor output tokens", u_p.get("output_tokens", 0))

# ── Section 4: Quality-Gated Orchestration ────────────────────────────────────
st.divider()
st.subheader("4 — Quality-Gated Re-Delegation")

st.markdown("""
The orchestrator assesses subagent output quality before accepting it.
If quality falls below the threshold, it re-assigns the task with improved instructions.
""")

QUALITY_THRESHOLD = st.slider("Quality threshold (depth + completeness average, /5):", 2.0, 4.5, 3.0, 0.5, key="q_threshold")

GATE_PRESETS = [
    "Custom question — type below",
    "Explain how transformer neural networks process text",
    "What is the significance of the Turing test in AI?",
    "Describe the key differences between TCP and UDP protocols",
]

sel_gate = st.selectbox("Pick a preset or write your own:", GATE_PRESETS, key="gate_preset")
gate_q = st.text_area(
    "Research question:",
    value="" if sel_gate == GATE_PRESETS[0] else sel_gate,
    height=70,
    key="gate_question",
)

if st.button("▶ Run Quality-Gated Orchestration", type="primary", disabled=not gate_q.strip()):
    gate_total_in, gate_total_out = 0, 0
    rounds = []

    for attempt in range(1, 4):
        task = gate_q.strip() if attempt == 1 else f"{gate_q.strip()}\n\nImportant: Be MORE specific. Include concrete examples, statistics, or technical details. The previous answer was too vague."

        with st.spinner(f"Attempt {attempt}: Subagent researching…"):
            answer, u_a = chat(RESEARCHER_SUBAGENT_SYSTEM, task, max_tokens=250, temperature=0.4 + attempt * 0.05)
        gate_total_in += u_a["input_tokens"]
        gate_total_out += u_a["output_tokens"]

        with st.spinner(f"Attempt {attempt}: Quality assessor evaluating…"):
            quality_user = f"Question: {gate_q.strip()}\n\nAnswer to evaluate:\n{answer}"
            raw_quality, u_q = chat(QUALITY_ASSESSOR_SYSTEM, quality_user, max_tokens=200, temperature=0.1)
        gate_total_in += u_q["input_tokens"]
        gate_total_out += u_q["output_tokens"]

        quality = None
        try:
            clean = raw_quality.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            quality = json.loads(clean)
        except json.JSONDecodeError:
            pass

        depth = quality.get("depth", 0) if quality else 0
        completeness = quality.get("completeness", 0) if quality else 0
        avg_score = (depth + completeness) / 2
        feedback = quality.get("feedback", "") if quality else ""

        rounds.append({
            "attempt": attempt,
            "answer": answer,
            "depth": depth,
            "completeness": completeness,
            "avg": avg_score,
            "feedback": feedback,
        })

        if avg_score >= QUALITY_THRESHOLD:
            break

    st.session_state["gate_results"] = rounds
    st.session_state["gate_totals"] = (gate_total_in, gate_total_out)
    st.session_state["gate_threshold"] = QUALITY_THRESHOLD

if "gate_results" in st.session_state:
    rounds = st.session_state["gate_results"]
    gate_total_in, gate_total_out = st.session_state["gate_totals"]
    threshold = st.session_state["gate_threshold"]

    for rd in rounds:
        accepted = rd["avg"] >= threshold
        status = "✅ ACCEPTED" if accepted else "🔁 RE-DELEGATED"
        status_color = "#43A047" if accepted else "#FB8C00"

        with st.expander(
            f"Attempt {rd['attempt']} — avg score {rd['avg']:.1f}/5 — {status}",
            expanded=(rd["attempt"] == len(rounds)),
        ):
            st.markdown(rd["answer"])
            qa_cols = st.columns(3)
            qa_cols[0].metric("Depth", f"{rd['depth']}/5")
            qa_cols[1].metric("Completeness", f"{rd['completeness']}/5")
            qa_cols[2].metric("Average", f"{rd['avg']:.1f}/5")
            if rd["feedback"]:
                st.info(f"**Quality feedback:** {rd['feedback']}")

            gate_bg = "#E8F5E9" if accepted else "#FFF3E0"
            gate_msg = f" — threshold {threshold:.1f} met" if accepted else f" — below threshold {threshold:.1f}, re-delegating with richer instructions"
            st.markdown(
                f"<div style='background:{gate_bg};"
                f"border-left:4px solid {status_color};padding:8px 12px;border-radius:4px;'>"
                f"<strong style='color:{status_color};'>{status}</strong>"
                f"{gate_msg}</div>",
                unsafe_allow_html=True,
            )

    c1, c2, c3 = st.columns(3)
    c1.metric("Attempts", len(rounds))
    c2.metric("Total input tokens", gate_total_in)
    c3.metric("Total output tokens", gate_total_out)
