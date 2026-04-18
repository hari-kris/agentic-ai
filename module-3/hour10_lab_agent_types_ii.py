"""
Hour 10 Lab — Agent Types II: Retriever, Orchestrator, Specialist
Module 3 | Agent Types and Components

Three more agent types introduced in this hour:
  Retriever     — searches a knowledge base and returns relevant context
  Orchestrator  — coordinates multiple agents, delegates tasks, synthesises results
  Specialist    — performs deep work in a narrow domain (contrast with generalist)

Sections:
  1. Type overview      — three cards explaining each new type
  2. Retriever demo     — query a hard-coded knowledge base; watch context retrieval in action
  3. Orchestrator demo  — enter a task; watch Orchestrator → Specialist(s) → Synthesiser pipeline
  4. Team designer      — design a 3-agent team for a document analysis task; Claude validates it

Run: streamlit run hour10_lab_agent_types_ii.py
"""

import json
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Hour 10 — Agent Types II", page_icon="🏗️", layout="wide")
st.title("🏗️ Hour 10 — Agent Types II")
st.caption("Module 3 | Agent Types and Components")

st.markdown(
    """
Hour 9 introduced agents that act on individual tasks. This hour covers the agents that
**connect** those actors together: the Retriever that supplies context, the Orchestrator
that directs the team, and the Specialist that goes deep in a narrow domain.
"""
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Hour 10 Guide")
    st.markdown(
        """
**Four sections in this lab:**

1. **Type Overview** — Read the three new agent types and what distinguishes them.

2. **Retriever Demo** — Query the Nexara knowledge base. Watch the Retriever pick relevant chunks before the Answerer responds.

3. **Orchestrator Demo** — Enter a document task. Watch 4 stages: Orchestrator → Summariser → Risk Analyst → Synthesiser.

4. **Team Designer** — Design a 3-agent team from scratch and get Claude's validation.
"""
    )
    st.divider()
    st.markdown("**Try these Retriever queries:**")
    st.markdown("- `How much does the API cost?`")
    st.markdown("- `Where is my data stored?`")
    st.markdown("- `What integrations are available?`")
    st.markdown("- `What is the uptime SLA?`")
    st.divider()
    st.markdown("**Try these Orchestrator tasks:**")
    st.markdown("- A cloud hosting contract worth £500k")
    st.markdown("- A startup's 300% growth projection")
    st.markdown("- A new AI engineer job description")

# ── Type metadata ─────────────────────────────────────────────────────────────

NEW_TYPES = [
    {
        "name": "Retriever",
        "icon": "🔎",
        "color": "#43A047",
        "bg": "#E8F5E9",
        "analogy": "A librarian who finds the right book — not the one who reads it to you.",
        "definition": "Searches a knowledge base and returns the most relevant chunks of context for a given query. Does not answer — only retrieves.",
        "cannot_do": "Cannot generate answers or make decisions — only surface relevant source material.",
        "input": "A query or question",
        "output": "Ranked, relevant document chunks — raw context for another agent to use",
    },
    {
        "name": "Orchestrator",
        "icon": "🎼",
        "color": "#8E24AA",
        "bg": "#F3E5F5",
        "analogy": "A project manager who assigns work, tracks progress, and assembles the final deliverable.",
        "definition": "Coordinates multiple specialised agents. Receives a high-level goal, delegates sub-tasks to the right agents, and synthesises their outputs into a coherent result.",
        "cannot_do": "Cannot do the specialist work itself — its value is coordination and synthesis, not domain expertise.",
        "input": "A complex, multi-part goal",
        "output": "A plan of delegation + the synthesised final output",
    },
    {
        "name": "Specialist",
        "icon": "🎯",
        "color": "#FB8C00",
        "bg": "#FFF3E0",
        "analogy": "A domain expert consultant brought in for a specific problem — they go deep where a generalist cannot.",
        "definition": "Performs deep, focused work in a narrow domain. Its system prompt is highly specific to one skill set (e.g. legal review, SQL generation, financial modelling).",
        "cannot_do": "Cannot handle tasks outside its narrow domain well — that is intentional. Depth over breadth.",
        "input": "A specific sub-task within its domain",
        "output": "High-quality, domain-specific output",
    },
]

# ── Section 1: Type overview ──────────────────────────────────────────────────

st.subheader("Three New Agent Types")

type_cols = st.columns(3)
for col, agent in zip(type_cols, NEW_TYPES):
    with col:
        st.markdown(
            f"<div style='border-top:4px solid {agent['color']};background:{agent['bg']};"
            f"border-radius:6px;padding:16px;min-height:280px;'>"
            f"<div style='font-size:1.8em;'>{agent['icon']}</div>"
            f"<div style='font-weight:bold;font-size:1.1em;color:{agent['color']};margin:6px 0;'>{agent['name']}</div>"
            f"<div style='font-size:0.85em;margin-bottom:10px;'>{agent['definition']}</div>"
            f"<div style='font-size:0.78em;color:#555;border-top:1px solid {agent['color']}40;padding-top:8px;'>"
            f"<em>Analogy: {agent['analogy']}</em><br><br>"
            f"<strong>Cannot do:</strong> {agent['cannot_do']}"
            f"</div></div>",
            unsafe_allow_html=True,
        )

st.divider()

# ── Section 2: Retriever demo ─────────────────────────────────────────────────

st.subheader("Retriever Demo — Knowledge Base Search")
st.markdown(
    "The knowledge base below contains 6 chunks about a fictional SaaS product called **Nexara**. "
    "Enter a query and watch the Retriever agent select the most relevant chunks, then pass them "
    "as grounded context to an Answerer agent."
)

KNOWLEDGE_BASE = [
    {
        "id": "KB-001",
        "title": "Nexara Pricing Plans",
        "content": "Nexara offers three plans: Starter (£29/month, up to 5 users, 10GB storage), "
                   "Professional (£99/month, up to 25 users, 100GB storage, API access), and "
                   "Enterprise (custom pricing, unlimited users, dedicated support, SSO, on-premise option). "
                   "All plans include a 14-day free trial. Annual billing provides a 20% discount.",
    },
    {
        "id": "KB-002",
        "title": "Data Export and Portability",
        "content": "Nexara supports data export in CSV, JSON, and Parquet formats. Enterprise customers "
                   "can also export to S3 or Google Cloud Storage directly. Exports are scheduled or "
                   "on-demand. Data is retained for 90 days after account cancellation for recovery purposes.",
    },
    {
        "id": "KB-003",
        "title": "Nexara API Authentication",
        "content": "Nexara uses API keys for authentication. Keys are generated in Settings > Developer > API Keys. "
                   "Keys must be passed in the Authorization header as Bearer tokens. Rate limits: Starter 100 req/min, "
                   "Professional 1,000 req/min, Enterprise 10,000 req/min. OAuth 2.0 is supported on Professional and above.",
    },
    {
        "id": "KB-004",
        "title": "GDPR and Data Residency",
        "content": "Nexara is GDPR compliant. EU customer data is stored in Frankfurt (AWS eu-central-1) by default. "
                   "Enterprise customers can select US (us-east-1), UK (eu-west-2), or APAC (ap-southeast-1) regions. "
                   "A Data Processing Agreement (DPA) is available on request. Nexara acts as a data processor; "
                   "customers are data controllers.",
    },
    {
        "id": "KB-005",
        "title": "Integrations and Webhooks",
        "content": "Nexara integrates natively with Slack, Jira, GitHub, Salesforce, and HubSpot. "
                   "Webhooks are available on Professional and Enterprise plans. Webhook events include "
                   "record.created, record.updated, record.deleted, and user.invited. "
                   "A Zapier integration covers 500+ additional tools.",
    },
    {
        "id": "KB-006",
        "title": "Uptime SLA and Support",
        "content": "Nexara guarantees 99.9% uptime for Professional and 99.99% for Enterprise. "
                   "Support channels: Starter (community forum only), Professional (email, 48h response), "
                   "Enterprise (dedicated Slack channel, 2h response, named CSM). "
                   "Status page: status.nexara.io. Incidents are communicated via email and the status page.",
    },
]

RETRIEVER_SYSTEM = """\
You are a retrieval agent for a SaaS product knowledge base. Given a user query and a set of
knowledge base chunks, select the 1–3 most relevant chunks that would help answer the query.

Return ONLY valid JSON:
{"selected_ids": ["KB-XXX", ...], "reason": "one sentence explaining why these chunks are relevant"}\
"""

ANSWERER_SYSTEM = """\
You are a helpful customer support agent for Nexara, a SaaS product.
Answer the user's question using ONLY the provided knowledge base excerpts.
If the excerpts do not contain the answer, say so clearly.
Be concise and accurate.\
"""

kb_query = st.text_input(
    "Your query:",
    placeholder="e.g. How much does the API cost? / Can I export my data? / What's the uptime guarantee?",
)

with st.expander("View the full knowledge base (6 chunks)", expanded=False):
    for chunk in KNOWLEDGE_BASE:
        st.markdown(
            f"<div style='border-left:3px solid #43A047;padding:8px 12px;margin-bottom:8px;"
            f"background:#f9f9f9;border-radius:4px;'>"
            f"<strong style='color:#43A047;'>{chunk['id']}: {chunk['title']}</strong></div>",
            unsafe_allow_html=True,
        )
        st.caption(chunk["content"])

run_retriever = st.button("▶  Run Retriever → Answerer", type="primary", disabled=not kb_query.strip())

if run_retriever and kb_query.strip():
    kb_text = "\n\n".join(
        f"[{c['id']}] {c['title']}: {c['content']}" for c in KNOWLEDGE_BASE
    )
    retriever_user = f"Query: {kb_query.strip()}\n\nKnowledge base chunks:\n{kb_text}"

    with st.container(border=True):
        st.markdown("### 🔎 \[RETRIEVER\] — Selecting relevant chunks")
        with st.spinner("Retriever scanning knowledge base..."):
            raw_retrieval, r_usage = chat(
                system=RETRIEVER_SYSTEM,
                user=retriever_user,
                max_tokens=300,
                temperature=0.1,
            )

        try:
            clean = raw_retrieval.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            retrieval = json.loads(clean)
            selected_ids = retrieval.get("selected_ids", [])
            retrieval_reason = retrieval.get("reason", "")
        except json.JSONDecodeError:
            selected_ids = []
            retrieval_reason = raw_retrieval

        st.info(f"🔍 Selected: **{', '.join(selected_ids)}** — {retrieval_reason}")
        c1, c2 = st.columns(2)
        c1.metric("Input tokens", r_usage["input_tokens"])
        c2.metric("Output tokens", r_usage["output_tokens"])

        selected_chunks = [c for c in KNOWLEDGE_BASE if c["id"] in selected_ids]
        if not selected_chunks:
            selected_chunks = KNOWLEDGE_BASE
            st.warning("Retriever returned no specific chunks — passing full KB to Answerer.")
        else:
            st.markdown("**Retrieved chunks passed to Answerer:**")
            for chunk in selected_chunks:
                st.markdown(
                    f"<div style='border-left:3px solid #43A047;padding:6px 12px;"
                    f"background:#E8F5E9;border-radius:4px;margin-bottom:6px;'>"
                    f"<strong style='color:#43A047;'>{chunk['id']}: {chunk['title']}</strong></div>",
                    unsafe_allow_html=True,
                )
                st.caption(chunk["content"])

    with st.container(border=True):
        st.markdown("### ⚡ \[ANSWERER\] — Generating grounded response")
        context_text = "\n\n".join(
            f"[{c['id']}] {c['title']}: {c['content']}" for c in selected_chunks
        )
        answerer_user = f"Knowledge base context:\n{context_text}\n\nCustomer question: {kb_query.strip()}"

        with st.spinner("Answerer generating response..."):
            answer, a_usage = chat(
                system=ANSWERER_SYSTEM,
                user=answerer_user,
                max_tokens=400,
                temperature=0.3,
            )

        st.markdown(answer)
        c1, c2 = st.columns(2)
        c1.metric("Input tokens", a_usage["input_tokens"])
        c2.metric("Output tokens", a_usage["output_tokens"])

    st.info(
        "**What just happened:** The Retriever read the query, selected relevant chunks (not all 6), "
        "and passed only those to the Answerer. The Answerer never saw the full KB — only curated context. "
        "This is how RAG (Retrieval-Augmented Generation) works at the agent level."
    )

st.divider()

# ── Section 3: Orchestrator demo ──────────────────────────────────────────────

st.subheader("Orchestrator Demo — Multi-Agent Pipeline")
st.markdown(
    "Enter a document analysis task. The **Orchestrator** will delegate it to two **Specialist** agents, "
    "then a **Synthesiser** combines their outputs into a final report."
)

ORCHESTRATOR_SYSTEM = """\
You are an orchestrator agent managing a document analysis team. You receive a task and must
delegate it to exactly two specialists:
  - SUMMARISER: extracts the key facts and main points
  - RISK_ANALYST: identifies risks, gaps, or concerns

Return ONLY valid JSON:
{
  "summariser_task": "specific instruction for the summariser",
  "risk_analyst_task": "specific instruction for the risk analyst",
  "delegation_reason": "one sentence explaining your delegation logic"
}\
"""

SUMMARISER_SYSTEM = """\
You are a specialist summariser agent. You receive a document analysis task and produce
a clear, structured summary of the key facts and main points.
Be factual, concise, and well-organised. Use bullet points.\
"""

RISK_ANALYST_SYSTEM = """\
You are a specialist risk analysis agent. You receive a document analysis task and identify
the key risks, gaps, uncertainties, or concerns. Be specific — avoid generic observations.
Return 3–5 concrete risk points in bullet form.\
"""

SYNTHESISER_SYSTEM = """\
You are a synthesis agent. You receive a summary and a risk analysis, both produced by specialist agents,
and combine them into a single, coherent final report. The report should be balanced — neither
overly optimistic nor alarmist — and actionable.\
"""

PRESET_TASKS = [
    "Custom task — type below",
    "Analyse a proposed contract for a 2-year cloud hosting deal worth £500,000 with a new vendor.",
    "Review a startup's 12-month growth plan that projects 300% revenue increase.",
    "Evaluate a job description for a senior AI engineer role before posting it publicly.",
    "Assess a product launch plan for a new mobile app targeting the healthcare sector.",
]

selected_task = st.selectbox("Pick a preset task:", PRESET_TASKS)
orch_task = st.text_area(
    "Document analysis task:",
    value="" if selected_task == PRESET_TASKS[0] else selected_task,
    height=70,
    placeholder="Describe what document or proposal the agents should analyse...",
)

run_orch = st.button("▶  Run Orchestrator Pipeline", type="primary", disabled=not orch_task.strip())

if run_orch and orch_task.strip():
    total_in, total_out = 0, 0

    with st.container(border=True):
        st.markdown("### 🎼 \[ORCHESTRATOR\] — Delegation planning")
        with st.spinner("Orchestrator planning delegation..."):
            raw_plan, o_usage = chat(
                system=ORCHESTRATOR_SYSTEM,
                user=f"Task: {orch_task.strip()}",
                max_tokens=400,
                temperature=0.2,
            )
        total_in += o_usage["input_tokens"]
        total_out += o_usage["output_tokens"]

        try:
            clean = raw_plan.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            plan = json.loads(clean)
            sum_task = plan.get("summariser_task", orch_task.strip())
            risk_task = plan.get("risk_analyst_task", orch_task.strip())
            delegation_reason = plan.get("delegation_reason", "")
        except json.JSONDecodeError:
            sum_task = orch_task.strip()
            risk_task = orch_task.strip()
            delegation_reason = "Delegation plan could not be parsed — using original task."

        st.info(f"📋 Delegation logic: {delegation_reason}")
        d_cols = st.columns(2)
        d_cols[0].markdown(f"**→ Summariser task:**\n\n{sum_task}")
        d_cols[1].markdown(f"**→ Risk Analyst task:**\n\n{risk_task}")
        c1, c2 = st.columns(2)
        c1.metric("Input tokens", o_usage["input_tokens"])
        c2.metric("Output tokens", o_usage["output_tokens"])

    spec_cols = st.columns(2)

    with spec_cols[0]:
        with st.container(border=True):
            st.markdown("### 🎯 \[SUMMARISER\] — Specialist Agent")
            with st.spinner("Summariser extracting key points..."):
                summary, s_usage = chat(
                    system=SUMMARISER_SYSTEM,
                    user=sum_task,
                    max_tokens=500,
                    temperature=0.3,
                )
            total_in += s_usage["input_tokens"]
            total_out += s_usage["output_tokens"]
            st.markdown(summary)
            c1, c2 = st.columns(2)
            c1.metric("Input tokens", s_usage["input_tokens"])
            c2.metric("Output tokens", s_usage["output_tokens"])

    with spec_cols[1]:
        with st.container(border=True):
            st.markdown("### 🎯 \[RISK ANALYST\] — Specialist Agent")
            with st.spinner("Risk analyst identifying concerns..."):
                risks, r_usage = chat(
                    system=RISK_ANALYST_SYSTEM,
                    user=risk_task,
                    max_tokens=500,
                    temperature=0.3,
                )
            total_in += r_usage["input_tokens"]
            total_out += r_usage["output_tokens"]
            st.markdown(risks)
            c1, c2 = st.columns(2)
            c1.metric("Input tokens", r_usage["input_tokens"])
            c2.metric("Output tokens", r_usage["output_tokens"])

    with st.container(border=True):
        st.markdown("### 🔗 \[SYNTHESISER\] — Combining specialist outputs")
        synth_input = (
            f"Original task: {orch_task.strip()}\n\n"
            f"Summary from Summariser agent:\n{summary}\n\n"
            f"Risk analysis from Risk Analyst agent:\n{risks}"
        )
        with st.spinner("Synthesiser combining results..."):
            final_report, syn_usage = chat(
                system=SYNTHESISER_SYSTEM,
                user=synth_input,
                max_tokens=600,
                temperature=0.5,
            )
        total_in += syn_usage["input_tokens"]
        total_out += syn_usage["output_tokens"]
        st.markdown(final_report)
        c1, c2 = st.columns(2)
        c1.metric("Input tokens", syn_usage["input_tokens"])
        c2.metric("Output tokens", syn_usage["output_tokens"])

    st.divider()
    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("Total LLM calls", 4)
    pc2.metric("Total input tokens", total_in)
    pc3.metric("Total output tokens", total_out)

st.divider()

# ── Section 4: Team designer ──────────────────────────────────────────────────

st.subheader("Exercise — Design a 3-Agent Team")
st.markdown(
    "Design a 3-agent team to analyse a government policy brief on AI regulation. "
    "Fill in the role card for each agent. Claude will evaluate whether your team design "
    "is complete, coherent, and covers the task without gaps or overlaps."
)

st.markdown(
    "<div style='background:#FFF3E0;border-left:4px solid #FB8C00;padding:10px 14px;"
    "border-radius:4px;margin-bottom:16px;font-size:0.9em;'>"
    "📄 Task: <strong>Analyse a 40-page government policy brief on AI regulation and produce "
    "a briefing for our legal and product teams.</strong></div>",
    unsafe_allow_html=True,
)

TEAM_VALIDATOR_SYSTEM = """\
You are an expert in multi-agent system design. Evaluate a proposed 3-agent team design for a document analysis task.
Assess: completeness (does the team cover the full task?), clarity (are roles distinct?), coherence (do outputs connect logically?).
Return ONLY valid JSON.\
"""

TEAM_VALIDATOR_PROMPT = """\
Document analysis task: "Analyse a 40-page government policy brief on AI regulation and produce a briefing for our legal and product teams."

Proposed 3-agent team:
Agent 1 — Name: {name1}, Type: {type1}, Responsibilities: {resp1}, Receives: {receives1}, Outputs: {outputs1}
Agent 2 — Name: {name2}, Type: {type2}, Responsibilities: {resp2}, Receives: {receives2}, Outputs: {outputs2}
Agent 3 — Name: {name3}, Type: {type3}, Responsibilities: {resp3}, Receives: {receives3}, Outputs: {outputs3}

Evaluate this team design on:
- completeness: Does the team collectively cover the full task? (score 1–5)
- role_clarity: Are the three roles distinct with no significant overlap? (score 1–5)
- output_coherence: Do the outputs chain logically into the final deliverable? (score 1–5)

Return ONLY valid JSON:
{{"completeness": 0, "role_clarity": 0, "output_coherence": 0,
  "strengths": "one sentence on what works well",
  "improvements": "one concrete suggestion to strengthen the design"}}\
"""

ROLE_TYPES = ["Retriever", "Planner", "Executor", "Critic", "Orchestrator", "Specialist"]

AGENT_DEFAULTS = [
    {
        "name": "Policy Extractor",
        "type": "Retriever",
        "resp": "Find and extract the key policy clauses and regulatory requirements from the document.",
        "receives": "The full policy document",
        "outputs": "A structured list of relevant clauses and requirements",
    },
    {
        "name": "Legal Analyst",
        "type": "Specialist",
        "resp": "Interpret the regulatory requirements from a legal compliance perspective.",
        "receives": "Extracted clauses from the Policy Extractor",
        "outputs": "Legal risk assessment with compliance recommendations",
    },
    {
        "name": "Briefing Writer",
        "type": "Executor",
        "resp": "Combine the legal analysis into a clear, actionable briefing for both teams.",
        "receives": "Legal analysis from the Legal Analyst",
        "outputs": "Final two-section briefing document",
    },
]

BLANK_DEFAULTS = [
    {"name": "", "type": "Retriever", "resp": "", "receives": "", "outputs": ""},
    {"name": "", "type": "Executor", "resp": "", "receives": "", "outputs": ""},
    {"name": "", "type": "Specialist", "resp": "", "receives": "", "outputs": ""},
]

use_blank = st.checkbox("Start from blank (design the team yourself)", value=False)
defaults = BLANK_DEFAULTS if use_blank else AGENT_DEFAULTS

team_data = {}
for i, d in enumerate(defaults):
    agent_num = i + 1
    with st.container(border=True):
        st.markdown(f"**Agent {agent_num}**")
        top_cols = st.columns([2, 1])
        team_data[f"name{agent_num}"] = top_cols[0].text_input(
            f"Agent name", value=d["name"], key=f"tname{agent_num}",
            placeholder="e.g. Policy Extractor"
        )
        team_data[f"type{agent_num}"] = top_cols[1].selectbox(
            f"Agent type", ROLE_TYPES,
            index=ROLE_TYPES.index(d["type"]), key=f"ttype{agent_num}"
        )
        mid_cols = st.columns(3)
        team_data[f"resp{agent_num}"] = mid_cols[0].text_area(
            "Responsibilities", value=d["resp"], height=90, key=f"tresp{agent_num}",
            placeholder="What does this agent do?"
        )
        team_data[f"receives{agent_num}"] = mid_cols[1].text_area(
            "Receives", value=d["receives"], height=90, key=f"trec{agent_num}",
            placeholder="What input does it get?"
        )
        team_data[f"outputs{agent_num}"] = mid_cols[2].text_area(
            "Outputs", value=d["outputs"], height=90, key=f"tout{agent_num}",
            placeholder="What does it produce?"
        )

validate_team = st.button("▶  Validate Team Design", type="primary")

if validate_team:
    with st.spinner("Claude is evaluating your team design..."):
        raw_val, val_usage = chat(
            system=TEAM_VALIDATOR_SYSTEM,
            user=TEAM_VALIDATOR_PROMPT.format(**team_data),
            max_tokens=400,
            temperature=0.2,
        )

    try:
        clean = raw_val.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        val = json.loads(clean)
        v_cols = st.columns(3)
        for col, (criterion, label) in zip(v_cols, [
            ("completeness", "Completeness"),
            ("role_clarity", "Role Clarity"),
            ("output_coherence", "Output Coherence"),
        ]):
            score = val.get(criterion, 0)
            col.metric(label, f"{score}/5")

        if val.get("strengths"):
            st.success(f"✅ Strengths: {val['strengths']}")
        if val.get("improvements"):
            st.info(f"💡 Improvement: {val['improvements']}")
        c1, c2 = st.columns(2)
        c1.metric("Input tokens", val_usage["input_tokens"])
        c2.metric("Output tokens", val_usage["output_tokens"])
    except json.JSONDecodeError:
        st.code(raw_val)

st.divider()
with st.expander("Generalist vs Specialist — why it matters"):
    st.markdown(
        """
A **generalist agent** uses a broad system prompt and can handle many types of tasks — but at average depth.

A **specialist agent** has a narrow, domain-specific system prompt. Its knowledge base, tools, and persona
are all tuned for one problem type. It performs better on its specific tasks because:

1. The system prompt uses domain vocabulary that activates the model's specialised knowledge more reliably.
2. It receives only the context relevant to its domain — no noise.
3. Its output format is tailored for the next agent in the pipeline, not a human end-user.

**The trade-off:** specialists cost more to design and maintain. You need one per domain.
But in production systems where quality and reliability matter, specialists consistently outperform
a single "do everything" agent. The Orchestrator pays for itself by making each Specialist better.
"""
    )
