"""
Hour 24 Lab — Agent Communication and Handoffs
Module 6 | Multi-Agent Systems

A handoff package grows as it passes through a sequential agent pipeline.
Each agent reads the full package so far, adds its contribution, and passes it on.
Section 2: Document Review Pipeline (Legal → Risk → Recommendation).
Section 3: Bidirectional clarification handoff.

Run: streamlit run module-6/hour24_lab_agent_handoffs.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 24 — Agent Handoffs", page_icon="🔗", layout="wide")
st.title("🔗 Hour 24 — Agent Communication and Handoffs")
st.caption("Module 6 | Multi-Agent Systems")

st.markdown("""
State passing and handoff logic are the mechanics that make multi-agent pipelines coherent.
Each agent does not repeat the full computation — it reads the **accumulated state** and adds its own layer.
The **handoff package** is the shared memory of the pipeline: it starts empty and grows richer at every stage.
By the time it reaches the final agent, it contains the complete intelligence of every upstream agent.
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 24 Guide")
    st.markdown("""
**Sections in this lab:**
1. Sequential handoff architecture diagram
2. Document Review Pipeline — Legal → Risk → Recommendation
3. Bidirectional handoff — clarification loop between two agents

**What to observe:**
- Each agent adds new fields to the handoff package — it never overwrites prior work
- The Risk agent reads the Legal findings before assessing risk
- The Recommendation agent has the full picture of both prior stages
- Clarification can be back-and-forth before the final task completes
""")
    st.divider()
    st.markdown("""
**Experiment ideas:**
- Paste a contract with ambiguous jurisdiction — see how the Legal agent flags it
- Try the employment contract with the non-compete clause — check the risk score
- In Section 3, phrase a request as vaguely as possible and watch the clarification trigger
""")
    st.divider()
    st.info("**Key principle:** The handoff package is the pipeline's shared memory. Each agent enriches it — by the time it reaches the final agent, it contains the full accumulated intelligence of every upstream agent.")

# ── System Prompts ─────────────────────────────────────────────────────────────
LEGAL_AGENT_SYSTEM = """\
You are a legal document analyst. You are the first agent in a review pipeline.
Read the contract text, extract the key clauses, and identify the governing jurisdiction.

Return ONLY valid JSON — no markdown fences, no commentary:
{"clauses": [{"title": "clause name", "summary": "one sentence summary", "notable": true}, {"title": "clause name", "summary": "one sentence summary", "notable": false}], "jurisdiction": "governing law or jurisdiction identified, or Not specified", "legal_notes": "2-3 sentences on legal risks or items needing attention"}\
"""

RISK_AGENT_SYSTEM = """\
You are a risk assessment agent. You are the second agent in a document review pipeline.
You receive the original contract text AND the legal analysis from the first agent.

Read both the contract and the legal findings, then add a risk assessment layer.
Build on the legal agent's clause extraction — do not repeat it.

Return ONLY valid JSON — no markdown fences, no commentary:
{"risks": [{"risk": "risk name", "description": "one sentence", "severity": "high"}, {"risk": "risk name", "description": "one sentence", "severity": "medium"}], "risk_score": 3, "risk_notes": "2-3 sentences explaining the overall risk posture and primary concerns"}

risk_score is 1 (minimal risk) to 5 (severe risk). Include 3 to 5 risks.\
"""

RECOMMENDATION_AGENT_SYSTEM = """\
You are a final recommendation agent. You are the third agent in a document review pipeline.
You receive the original contract text, the legal analysis, and the risk assessment.

All prior analysis is in the handoff package — do not repeat what earlier agents said.
Your job is to produce a final recommendation and a short action item list.

Write in clear professional prose using this exact structure:

## Recommendation
[APPROVE / APPROVE WITH CONDITIONS / REJECT] — one sentence justification.

## Rationale
2-3 sentences integrating the legal and risk findings.

## Action Items
- Action 1
- Action 2
- Action 3\
"""

CLARIFIER_SYSTEM = """\
You are an agent that needs clarification before completing a task.
Read the task request. If the request is ambiguous or missing critical information,
ask ONE specific clarifying question. If the request is clear and complete, say so.

Return ONLY valid JSON — no markdown fences, no commentary:
{"needs_clarification": true, "question": "your specific clarifying question", "reason": "why you need this information"}

Or if no clarification is needed:
{"needs_clarification": false, "question": "", "reason": "why the request is sufficiently clear"}\
"""

CLARIFICATION_RESPONDER_SYSTEM = """\
You are a clarification provider. You receive a task request and a clarifying question
from an agent. Provide a direct, specific answer to the question.
Keep your response to 1–3 sentences. Be concrete.\
"""

TASK_COMPLETER_SYSTEM = """\
You are a task completion agent. You receive an original task request and a clarification
answer that resolved an ambiguity. Now complete the task using both pieces of information.
Write a focused, professional response in 150–200 words.\
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_json(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


SERVICE_CONTRACT = """\
SERVICE AGREEMENT

This Agreement is entered into between Acme Corp ("Service Provider") and Beta Ltd ("Client") \
on January 15, 2025. Governing law: State of Delaware, USA.

1. SERVICES: Provider will deliver software development consulting services as specified in \
Exhibit A, to be completed within 90 days of the Effective Date.

2. PAYMENT: Client shall pay $15,000 per month. Payment is due within 30 days of invoice. \
Late payments incur 1.5% monthly interest.

3. INTELLECTUAL PROPERTY: All work product created under this Agreement is owned by Provider \
until full payment is received, at which point ownership transfers to Client.

4. TERMINATION: Either party may terminate with 30 days written notice. Client is liable for \
work completed up to termination date.

5. LIMITATION OF LIABILITY: Provider liability is capped at fees paid in the preceding 3 months.\
"""

EMPLOYMENT_CONTRACT = """\
EMPLOYMENT CONTRACT

This Employment Agreement is made between TechStartup Inc ("Employer") and [Employee Name] \
("Employee") effective March 1, 2025.

1. POSITION: Senior Software Engineer, reporting to the CTO.

2. COMPENSATION: Annual salary of $145,000, paid bi-weekly. Performance bonus eligibility up \
to 15% of base salary at Employer discretion.

3. NON-COMPETE: Employee agrees not to work for any direct competitor for 24 months following \
employment termination. Geographic scope: North America.

4. IP ASSIGNMENT: All inventions created during employment are assigned to Employer, including \
work done outside business hours if related to Employer's business.

5. AT-WILL: Employment is at-will and may be terminated by either party at any time. \
Employer will provide 2 weeks severance upon termination without cause.\
"""

CONTRACT_PRESETS = {
    "Custom contract — paste below": "",
    "Service Agreement (Acme Corp / Beta Ltd)": SERVICE_CONTRACT,
    "Employment Contract (TechStartup Inc)": EMPLOYMENT_CONTRACT,
}

VAGUE_TASK_PRESETS = [
    "Custom task — type below",
    "Prepare a report on recent performance",
    "Write a summary for the meeting",
    "Update the documentation",
    "Draft the proposal for the new initiative",
]

# ── Section 1 — Architecture Diagram ──────────────────────────────────────────
st.markdown("---")
st.subheader("1 — Sequential Handoff Pipeline")

arch_cols = st.columns([2, 0.7, 2, 0.7, 2])

with arch_cols[0]:
    st.markdown(
        "<div style='border-top:4px solid #1E88E5;background:#E3F2FD;border-radius:8px;"
        "padding:14px;text-align:center;min-height:180px;'>"
        "<div style='font-size:1.6em;'>⚖️</div>"
        "<div style='font-weight:bold;color:#1E88E5;margin:6px 0;'>[LEGAL AGENT]</div>"
        "<div style='font-size:0.75em;color:#444;'>Reads contract.<br>Extracts clauses.<br>Identifies jurisdiction.<br>Adds legal_notes.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with arch_cols[1]:
    st.markdown(
        "<div style='text-align:center;margin-top:60px;'>"
        "<div style='font-size:1.3em;'>→</div>"
        "<div style='font-size:0.65em;color:#1E88E5;font-weight:bold;margin-top:4px;'>+ clauses<br>+ jurisdiction<br>+ legal_notes</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with arch_cols[2]:
    st.markdown(
        "<div style='border-top:4px solid #E53935;background:#FFEBEE;border-radius:8px;"
        "padding:14px;text-align:center;min-height:180px;'>"
        "<div style='font-size:1.6em;'>⚠️</div>"
        "<div style='font-weight:bold;color:#E53935;margin:6px 0;'>[RISK AGENT]</div>"
        "<div style='font-size:0.75em;color:#444;'>Reads contract + legal findings.<br>Scores overall risk (1–5).<br>Adds risks list<br>and risk_notes.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with arch_cols[3]:
    st.markdown(
        "<div style='text-align:center;margin-top:60px;'>"
        "<div style='font-size:1.3em;'>→</div>"
        "<div style='font-size:0.65em;color:#E53935;font-weight:bold;margin-top:4px;'>+ risks<br>+ risk_score<br>+ risk_notes</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with arch_cols[4]:
    st.markdown(
        "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;border-radius:8px;"
        "padding:14px;text-align:center;min-height:180px;'>"
        "<div style='font-size:1.6em;'>📋</div>"
        "<div style='font-weight:bold;color:#8E24AA;margin:6px 0;'>[RECOMMENDATION]</div>"
        "<div style='font-size:0.75em;color:#444;'>Reads full package.<br>Writes APPROVE / CONDITIONS / REJECT.<br>Adds rationale<br>and action items.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with st.expander("See system prompts"):
    tabs = st.tabs(["Legal Agent", "Risk Agent", "Recommendation Agent", "Clarifier", "Clarification Responder", "Task Completer"])
    for tab, prompt in zip(tabs, [LEGAL_AGENT_SYSTEM, RISK_AGENT_SYSTEM, RECOMMENDATION_AGENT_SYSTEM, CLARIFIER_SYSTEM, CLARIFICATION_RESPONDER_SYSTEM, TASK_COMPLETER_SYSTEM]):
        with tab:
            st.code(prompt, language="text")

# ── Section 2 — Document Review Pipeline ──────────────────────────────────────
st.markdown("---")
st.subheader("2 — Document Review Pipeline")
st.markdown("Paste a contract or agreement. The handoff package grows as it passes through three specialist agents.")

preset_key = st.selectbox("Choose a preset contract or paste your own:", list(CONTRACT_PRESETS.keys()), key="s2_contract_preset")
contract_val = CONTRACT_PRESETS[preset_key]
contract = st.text_area("Contract text:", value=contract_val, height=200, key="s2_contract",
                          placeholder="Paste a contract or agreement here…")

if st.button("▶ Run Document Review Pipeline", type="primary", disabled=not contract.strip()):
    contract_text = contract.strip()

    # Stage 1 — Legal
    with st.spinner("Stage 1 — Legal Agent extracting clauses…"):
        raw_legal, u_legal = chat(LEGAL_AGENT_SYSTEM, f"Contract text:\n\n{contract_text}", max_tokens=600, temperature=0.2)
    legal_findings = parse_json(raw_legal)
    if legal_findings is None:
        st.error("Legal agent returned unexpected output. Showing raw:")
        st.code(raw_legal)
        st.stop()

    # Stage 2 — Risk
    risk_user = (
        f"Contract text:\n\n{contract_text}\n\n"
        f"[LEGAL AGENT FINDINGS]\n{json.dumps(legal_findings, indent=2)}"
    )
    with st.spinner("Stage 2 — Risk Agent assessing risks…"):
        raw_risk, u_risk = chat(RISK_AGENT_SYSTEM, risk_user, max_tokens=500, temperature=0.2)
    risk_findings = parse_json(raw_risk)
    if risk_findings is None:
        st.error("Risk agent returned unexpected output. Showing raw:")
        st.code(raw_risk)
        st.stop()

    # Stage 3 — Recommendation
    rec_user = (
        f"Contract text:\n\n{contract_text}\n\n"
        f"[LEGAL ANALYSIS]\n{json.dumps(legal_findings, indent=2)}\n\n"
        f"[RISK ASSESSMENT]\n{json.dumps(risk_findings, indent=2)}"
    )
    with st.spinner("Stage 3 — Recommendation Agent writing final recommendation…"):
        recommendation, u_rec = chat(RECOMMENDATION_AGENT_SYSTEM, rec_user, max_tokens=500, temperature=0.4)

    st.session_state["legal_findings"] = legal_findings
    st.session_state["risk_findings"] = risk_findings
    st.session_state["recommendation"] = recommendation
    st.session_state["u_legal"] = u_legal
    st.session_state["u_risk"] = u_risk
    st.session_state["u_rec"] = u_rec
    st.session_state["pipeline_contract"] = contract_text

if "legal_findings" in st.session_state:
    legal_findings = st.session_state["legal_findings"]
    risk_findings = st.session_state["risk_findings"]
    recommendation = st.session_state["recommendation"]
    u_legal = st.session_state["u_legal"]
    u_risk = st.session_state["u_risk"]
    u_rec = st.session_state["u_rec"]
    contract_text = st.session_state["pipeline_contract"]

    # Stage 1 display
    st.markdown(
        "<div style='border-top:4px solid #1E88E5;background:#E3F2FD;border-radius:6px;"
        "padding:10px 14px;margin:12px 0 8px;'>"
        "<strong style='color:#1E88E5;'>⚖️ [LEGAL AGENT] Stage 1 Findings</strong></div>",
        unsafe_allow_html=True,
    )
    clauses = legal_findings.get("clauses", [])
    if clauses:
        clause_data = [{"Title": c.get("title", ""), "Summary": c.get("summary", ""), "Notable": "✓" if c.get("notable") else "—"} for c in clauses]
        import pandas as pd
        st.dataframe(pd.DataFrame(clause_data), use_container_width=True, hide_index=True)
    jur = legal_findings.get("jurisdiction", "Not specified")
    st.metric("Jurisdiction", jur)
    st.info(f"**Legal notes:** {legal_findings.get('legal_notes', '')}")
    with st.expander("Handoff package after Stage 1"):
        st.code(json.dumps({"legal_analysis": legal_findings}, indent=2), language="json")
    st.caption(f"Legal Agent — In: {u_legal.get('input_tokens', 0)} | Out: {u_legal.get('output_tokens', 0)} tokens")

    st.markdown("---")

    # Stage 2 display
    st.markdown(
        "<div style='border-top:4px solid #E53935;background:#FFEBEE;border-radius:6px;"
        "padding:10px 14px;margin:12px 0 8px;'>"
        "<strong style='color:#E53935;'>⚠️ [RISK AGENT] Stage 2 Findings</strong></div>",
        unsafe_allow_html=True,
    )
    risk_score = risk_findings.get("risk_score", 3)
    score_color = "#43A047" if risk_score <= 2 else ("#FB8C00" if risk_score == 3 else "#E53935")
    st.markdown(
        f"<div style='border-top:4px solid {score_color};background:#FAFAFA;border-radius:6px;"
        f"padding:12px;text-align:center;display:inline-block;margin-bottom:10px;'>"
        f"<div style='font-size:0.78em;color:{score_color};font-weight:bold;'>OVERALL RISK SCORE</div>"
        f"<div style='font-size:2.5em;font-weight:bold;color:{score_color};'>{risk_score}/5</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    sev_colors = {"high": "#E53935", "medium": "#FB8C00", "low": "#43A047"}
    for r in risk_findings.get("risks", []):
        sev = r.get("severity", "medium")
        sc = sev_colors.get(sev, "#8E24AA")
        st.markdown(
            f"<div style='border-left:3px solid {sc};padding:6px 12px;margin-bottom:6px;background:#FAFAFA;border-radius:0 4px 4px 0;'>"
            f"<span style='background:{sc};color:white;border-radius:3px;padding:1px 6px;font-size:0.75em;font-weight:bold;'>{sev.upper()}</span> "
            f"<strong>{r.get('risk', '')}</strong> — {r.get('description', '')}</div>",
            unsafe_allow_html=True,
        )
    note_fn = st.warning if risk_score >= 3 else st.info
    note_fn(f"**Risk notes:** {risk_findings.get('risk_notes', '')}")
    with st.expander("Handoff package after Stage 2"):
        st.code(json.dumps({"legal_analysis": legal_findings, "risk_assessment": risk_findings}, indent=2), language="json")
    st.caption(f"Risk Agent — In: {u_risk.get('input_tokens', 0)} | Out: {u_risk.get('output_tokens', 0)} tokens")

    st.markdown("---")

    # Stage 3 display
    st.markdown(
        "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;border-radius:6px;"
        "padding:10px 14px;margin:12px 0 8px;'>"
        "<strong style='color:#8E24AA;'>📋 [RECOMMENDATION AGENT] Final Recommendation</strong></div>",
        unsafe_allow_html=True,
    )
    st.markdown(recommendation)
    with st.expander("Full handoff package (complete pipeline state)"):
        display_pkg = {
            "legal_analysis": legal_findings,
            "risk_assessment": risk_findings,
            "recommendation": recommendation[:200] + "…",
        }
        st.code(json.dumps(display_pkg, indent=2), language="json")
    st.caption(f"Recommendation Agent — In: {u_rec.get('input_tokens', 0)} | Out: {u_rec.get('output_tokens', 0)} tokens")

    st.markdown("**Token ledger:**")
    import pandas as pd
    ledger = pd.DataFrame([
        {"Agent": "⚖️ Legal Agent", "Stage": 1, "Input Tokens": u_legal.get("input_tokens", 0), "Output Tokens": u_legal.get("output_tokens", 0)},
        {"Agent": "⚠️ Risk Agent", "Stage": 2, "Input Tokens": u_risk.get("input_tokens", 0), "Output Tokens": u_risk.get("output_tokens", 0)},
        {"Agent": "📋 Recommendation Agent", "Stage": 3, "Input Tokens": u_rec.get("input_tokens", 0), "Output Tokens": u_rec.get("output_tokens", 0)},
    ])
    ledger["Total"] = ledger["Input Tokens"] + ledger["Output Tokens"]
    total_row = pd.DataFrame([{"Agent": "**TOTAL**", "Stage": "", "Input Tokens": ledger["Input Tokens"].sum(), "Output Tokens": ledger["Output Tokens"].sum(), "Total": ledger["Total"].sum()}])
    st.dataframe(pd.concat([ledger, total_row], ignore_index=True), use_container_width=True, hide_index=True)

# ── Section 3 — Bidirectional Handoff ─────────────────────────────────────────
st.markdown("---")
st.subheader("3 — Bidirectional Handoff: Clarification Loop")
st.markdown("""
Agent A receives a task. If the request is ambiguous, Agent A asks a clarifying question.
Agent B answers. Agent A then completes the task with full context.
This is a back-and-forth handoff — not strictly sequential.
""")

st.markdown(
    "<div style='background:#F8F8F8;border-radius:6px;padding:10px 14px;font-size:0.85em;text-align:center;margin-bottom:12px;'>"
    "Task → <strong style='color:#00897B;'>[Clarifier A]</strong> → Clarifying question → "
    "<strong style='color:#FB8C00;'>[Responder B]</strong> → Answer → "
    "<strong style='color:#1E88E5;'>[Completer A]</strong> → Final output"
    "</div>",
    unsafe_allow_html=True,
)

preset_task = st.selectbox("Choose a vague preset task or write your own:", VAGUE_TASK_PRESETS, key="s3_task_preset")
task_val = "" if preset_task == VAGUE_TASK_PRESETS[0] else preset_task
task_input = st.text_area("Task request:", value=task_val, height=70, key="s3_task",
                            placeholder="Enter a task request — vague requests trigger clarification…")

if st.button("▶ Run Clarification Handoff", type="primary", disabled=not task_input.strip()):
    task = task_input.strip()

    with st.spinner("Clarifier assessing task clarity…"):
        raw_clar, u_clar = chat(CLARIFIER_SYSTEM, f"Task request: {task}", max_tokens=200, temperature=0.2)
    clar = parse_json(raw_clar)
    if clar is None:
        clar = {"needs_clarification": False, "question": "", "reason": "Could not parse response."}

    clarification_answer = None
    u_resp = {}
    u_complete = {}

    if clar.get("needs_clarification"):
        with st.spinner("Clarification Responder answering the question…"):
            clarification_answer, u_resp = chat(
                CLARIFICATION_RESPONDER_SYSTEM,
                f"Original task: {task}\nClarifying question: {clar['question']}",
                max_tokens=200, temperature=0.5,
            )
        with st.spinner("Task Completer finishing the task with full context…"):
            final_output, u_complete = chat(
                TASK_COMPLETER_SYSTEM,
                f"Original task: {task}\nClarification received: {clarification_answer}",
                max_tokens=400, temperature=0.5,
            )
    else:
        with st.spinner("Task Completer handling clear request directly…"):
            final_output, u_complete = chat(
                TASK_COMPLETER_SYSTEM,
                f"Task: {task}",
                max_tokens=400, temperature=0.5,
            )

    st.session_state["s3_result"] = {
        "needs_clarification": clar.get("needs_clarification", False),
        "question": clar.get("question", ""),
        "reason": clar.get("reason", ""),
        "clarification_answer": clarification_answer,
        "final_output": final_output,
        "u_clar": u_clar,
        "u_resp": u_resp,
        "u_complete": u_complete,
    }

if "s3_result" in st.session_state:
    r = st.session_state["s3_result"]
    needed = r["needs_clarification"]

    # Step 1 card
    clar_color = "#E53935" if needed else "#43A047"
    clar_bg = "#FFEBEE" if needed else "#E8F5E9"
    clar_label = "CLARIFICATION NEEDED" if needed else "TASK IS CLEAR"
    st.markdown(
        f"<div style='border-top:4px solid {clar_color};background:{clar_bg};"
        f"border-radius:6px;padding:10px 14px;margin-bottom:10px;'>"
        f"<strong style='color:{clar_color};'>🔍 [CLARIFIER — Step 1] {clar_label}</strong><br>"
        f"<span style='font-size:0.88em;color:#555;'>{r['reason']}</span></div>",
        unsafe_allow_html=True,
    )

    if needed:
        # Step 2 — bidirectional exchange
        ex_cols = st.columns(2)
        with ex_cols[0]:
            st.markdown(
                "<div style='border-top:4px solid #00897B;background:#E0F2F1;border-radius:6px;padding:10px 14px;'>"
                "<strong style='color:#00897B;font-size:0.85em;'>🤖 Agent A asks:</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown(r["question"])
        with ex_cols[1]:
            st.markdown(
                "<div style='border-top:4px solid #FB8C00;background:#FFF3E0;border-radius:6px;padding:10px 14px;'>"
                "<strong style='color:#FB8C00;font-size:0.85em;'>💬 Agent B answers:</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown(r["clarification_answer"])

    # Step 3 — final output
    st.markdown(
        "<div style='border-top:4px solid #1E88E5;background:#E3F2FD;border-radius:6px;"
        "padding:10px 14px;margin-top:10px;'>"
        "<strong style='color:#1E88E5;'>✅ [COMPLETER — Final Output]</strong></div>",
        unsafe_allow_html=True,
    )
    st.markdown(r["final_output"])

    llm_calls = 3 if needed else 2
    st.caption(f"LLM calls: {llm_calls} ({'clarifier + responder + completer' if needed else 'clarifier + completer'})")
