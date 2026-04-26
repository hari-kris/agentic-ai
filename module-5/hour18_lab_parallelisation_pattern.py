"""
Hour 18 Lab — Parallelisation Pattern
Module 5 | Core Agentic Patterns II

Fan-out sends the same input to multiple agents simultaneously, then aggregates.
Voting sends the same task to N agents and tallies agreement.

Run: streamlit run module-5/hour18_lab_parallelisation_pattern.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 18 — Parallelisation", page_icon="⚡", layout="wide")
st.title("⚡ Hour 18 — Parallelisation Pattern")
st.caption("Module 5 | Core Agentic Patterns II")

st.markdown("""
The **Parallelisation Pattern** sends the same input to multiple agents simultaneously.
Two sub-types:

- **Fan-out (sectioning):** Each agent analyses a *different aspect* of the same input.
  Results are aggregated into one comprehensive output.
- **Voting (consensus):** The same task is sent to multiple instances of the same agent.
  Results are compared and a consensus is formed. Used when reliability matters most.

This lab shows:
1. **Fan-out document analysis** — 3 specialists each analyse a document from a different angle
2. **Code review fan-out** — 3 reviewers analyse the same code simultaneously
3. **Voting consensus** — 3 agents answer the same question; compare agreement rates
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 18 Guide")
    st.markdown("""
**Sections in this lab:**
1. **Architecture diagram** — fan-out structure
2. **Document fan-out** — Summarizer, Risk Analyst, Opportunity Analyst
3. **Code review fan-out** — Security, Performance, Readability reviewers
4. **Voting consensus** — 3 agents, one question, tally agreement

**What to observe:**
- Each specialist produces deeper output than a single generalist would
- The aggregator catches conflicts between specialists
- Voting agreement rate is a confidence signal
- Token cost: N specialist calls + 1 aggregator call
""")
    st.divider()
    st.markdown("**Experiment ideas:**")
    st.markdown("- Submit a document with clear risks AND opportunities — see if specialists agree")
    st.markdown("- Try voting on a controversial question — do agents agree?")
    st.markdown("- Compare the aggregated output to what a single generalist would say")
    st.divider()
    st.info("**Key principle:** Fan-out specialists each go deep. A generalist that covers everything shallowly misses what a focused reviewer catches.")

# ── System Prompts ─────────────────────────────────────────────────────────────
SUMMARIZER_SYSTEM = """\
You are a document summariser. Extract the key points from the provided document.
Return a clear, structured bullet list of the 4–6 most important points.
Focus on facts, claims, and stated intentions — not your interpretation.
Do not write an introduction. Start directly with the first bullet.\
"""

RISK_ANALYST_SYSTEM = """\
You are a risk analyst. Read the provided document and identify risks, challenges,
concerns, weaknesses, or negative implications.
Return 3–5 specific, concrete risks as a bullet list.
Each bullet should name the specific risk and briefly explain why it matters.
Do not write an introduction. Start directly with the first bullet.\
"""

OPPORTUNITY_ANALYST_SYSTEM = """\
You are an opportunity analyst. Read the provided document and identify strengths,
opportunities, positive signals, or favourable implications.
Return 3–5 specific, concrete opportunities as a bullet list.
Each bullet should name the opportunity and briefly explain why it is significant.
Do not write an introduction. Start directly with the first bullet.\
"""

DOC_AGGREGATOR_SYSTEM = """\
You are a synthesis analyst. You will receive three specialist analyses of the same document:
a summary, a risk analysis, and an opportunity analysis.

Your job is to write a comprehensive 200–250 word assessment that:
1. Leads with the most important overall finding
2. Integrates the risks and opportunities — including any tensions between them
3. Ends with a single actionable recommendation

Write in flowing prose, not bullets. Do not label sections.\
"""

SECURITY_REVIEWER_SYSTEM = """\
You are a security code reviewer. Analyse the provided code for security vulnerabilities,
unsafe patterns, or risks. Be specific: name the vulnerable line or pattern and explain the risk.
Return 3–5 findings as a bullet list. If no issues are found, say so explicitly.\
"""

PERFORMANCE_REVIEWER_SYSTEM = """\
You are a performance code reviewer. Analyse the provided code for inefficiencies,
suboptimal algorithms, or unnecessary resource usage. Be specific: name the line or
pattern and explain the performance impact.
Return 3–5 findings as a bullet list. If no issues are found, say so explicitly.\
"""

READABILITY_REVIEWER_SYSTEM = """\
You are a code readability reviewer. Analyse the provided code for clarity, naming conventions,
code structure, and maintainability. Be specific about what is unclear and how to improve it.
Return 3–5 findings as a bullet list. If no issues are found, say so explicitly.\
"""

CODE_AGGREGATOR_SYSTEM = """\
You are a lead code reviewer. You will receive three specialist reviews of the same code:
security, performance, and readability.

Write a consolidated code review of 150–200 words that:
1. States the most critical issue to address first
2. Integrates all three perspectives without duplication
3. Ends with the top 2–3 specific changes to make in priority order

Write in flowing prose. Do not label sections by reviewer.\
"""

VOTING_AGENT_SYSTEM = """\
You are a direct-answer assistant. Answer the question as accurately and concisely as possible.
For questions with a definitive answer, give it in 1–2 sentences.
For questions with a range of valid answers, pick the most defensible single answer and state it.\
"""

VOTE_CLASSIFIER_SYSTEM = """\
You are a voting analyst. You will receive a question and three independent answers from three agents.
Analyse the answers and determine:
1. Whether the answers agree, partially agree, or disagree
2. The majority position (if any)
3. What the disagreements are about

Return ONLY valid JSON — no markdown fences:
{
  "agreement": "full|partial|none",
  "majority_answer": "the most common or most defensible answer in one sentence",
  "agreement_count": 3,
  "disagreement_notes": "what the agents disagree about, or empty string if full agreement"
}\
"""


# ── Section 1: Architecture Diagram ───────────────────────────────────────────
st.divider()
st.subheader("1 — The Parallelisation Pipeline")

st.markdown("""
**Fan-out structure:** one input, multiple specialist agents, one aggregator.
All specialists receive the same input simultaneously.
""")

# Fan-out diagram
fa_cols = st.columns([1.2, 0.3, 2.5, 0.3, 1.2])

with fa_cols[0]:
    st.markdown(
        "<div style='border-top:4px solid #00897B;background:#E0F2F1;border-radius:6px;"
        "padding:14px;text-align:center;min-height:160px;'>"
        "<div style='font-size:2em;'>📄</div>"
        "<div style='font-weight:bold;color:#00897B;margin:6px 0;'>Input</div>"
        "<div style='font-size:0.82em;color:#444;'>Document, code, text — sent to all specialists</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with fa_cols[1]:
    st.markdown(
        "<div style='display:flex;align-items:center;justify-content:center;"
        "height:160px;font-size:1.8em;color:#999;'>→</div>",
        unsafe_allow_html=True,
    )

with fa_cols[2]:
    sp_cols = st.columns(3)
    specialists_info = [
        ("#1E88E5", "#E3F2FD", "📊", "SUMMARIZER", "Key points"),
        ("#E53935", "#FFEBEE", "⚠️", "RISK ANALYST", "Risks & challenges"),
        ("#43A047", "#E8F5E9", "✅", "OPPORTUNITY", "Strengths & gains"),
    ]
    for sp_col, (color, bg, icon, label, desc) in zip(sp_cols, specialists_info):
        with sp_col:
            st.markdown(
                f"<div style='border-top:4px solid {color};background:{bg};"
                f"border-radius:6px;padding:10px;text-align:center;min-height:120px;'>"
                f"<div style='font-size:1.5em;'>{icon}</div>"
                f"<div style='font-weight:bold;color:{color};font-size:0.8em;margin:4px 0;'>{label}</div>"
                f"<div style='font-size:0.75em;color:#555;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

with fa_cols[3]:
    st.markdown(
        "<div style='display:flex;align-items:center;justify-content:center;"
        "height:160px;font-size:1.8em;color:#999;'>→</div>",
        unsafe_allow_html=True,
    )

with fa_cols[4]:
    st.markdown(
        "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;border-radius:6px;"
        "padding:14px;text-align:center;min-height:160px;'>"
        "<div style='font-size:2em;'>🔗</div>"
        "<div style='font-weight:bold;color:#8E24AA;margin:6px 0;'>AGGREGATOR</div>"
        "<div style='font-size:0.82em;color:#444;'>Synthesises all specialist outputs</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with st.expander("See system prompts"):
    tabs = st.tabs(["Summarizer", "Risk Analyst", "Opportunity", "Doc Aggregator", "Security", "Performance", "Readability", "Code Aggregator"])
    prompts = [
        SUMMARIZER_SYSTEM, RISK_ANALYST_SYSTEM, OPPORTUNITY_ANALYST_SYSTEM, DOC_AGGREGATOR_SYSTEM,
        SECURITY_REVIEWER_SYSTEM, PERFORMANCE_REVIEWER_SYSTEM, READABILITY_REVIEWER_SYSTEM, CODE_AGGREGATOR_SYSTEM,
    ]
    for tab, prompt in zip(tabs, prompts):
        with tab:
            st.code(prompt, language="text")

# ── Section 2: Document Fan-Out ────────────────────────────────────────────────
st.divider()
st.subheader("2 — Document Fan-Out Analysis")

st.markdown("""
Paste a document (article, report, proposal, announcement). Three specialists analyse it
simultaneously from different angles, then an aggregator synthesises their outputs.
""")

DOC_PRESETS = [
    "Custom document — paste below",
    """TechCorp Q3 Update: We are expanding our AI product line and hiring 200 engineers over the next six months. Revenue grew 34% year-over-year, driven by enterprise contracts. However, our largest customer, representing 22% of revenue, has signalled they may switch to a competitor offering lower pricing. Our new AI assistant product launches next quarter, though regulatory approval in the EU is still pending. We are also entering the healthcare vertical, a market we have no prior experience in. Cash reserves stand at $45M with a burn rate of $8M per month.""",
    """City Council Notice: The downtown area will undergo a 24-month road reconstruction starting January 2025. All vehicle access to Main Street between 3rd and 7th Avenue will be restricted to residents only, 7am–7pm Monday through Saturday. Construction noise is expected. Business owners on affected streets will receive a $500/month subsidy. Foot traffic in the area is projected to drop 40%. The project will add 200 new parking spaces and dedicated cycling lanes upon completion. Property values in adjacent streets are expected to rise 8–12% post-completion based on comparable projects.""",
]

sel_doc = st.selectbox("Pick a preset document or paste your own:", DOC_PRESETS, key="doc_preset")
doc_text = st.text_area(
    "Document:",
    value="" if sel_doc == DOC_PRESETS[0] else sel_doc,
    height=130,
    key="doc_input",
)

if st.button("▶ Run Fan-Out Analysis", type="primary", disabled=not doc_text.strip()):
    total_in, total_out = 0, 0
    specialist_outputs = {}

    progress = st.progress(0, text="Running 3 specialists in parallel…")

    for i, (key, sys_prompt, label) in enumerate([
        ("summary", SUMMARIZER_SYSTEM, "Summarizer"),
        ("risk", RISK_ANALYST_SYSTEM, "Risk Analyst"),
        ("opportunity", OPPORTUNITY_ANALYST_SYSTEM, "Opportunity Analyst"),
    ]):
        with st.spinner(f"{label} analysing…"):
            output, usage = chat(sys_prompt, doc_text.strip(), max_tokens=400, temperature=0.3)
        specialist_outputs[key] = {"output": output, "usage": usage}
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]
        progress.progress((i + 1) * 25, text=f"{label} done…")

    aggregator_user = (
        f"Document summary:\n{specialist_outputs['summary']['output']}\n\n"
        f"Risk analysis:\n{specialist_outputs['risk']['output']}\n\n"
        f"Opportunity analysis:\n{specialist_outputs['opportunity']['output']}"
    )
    with st.spinner("Aggregator synthesising…"):
        agg_output, agg_usage = chat(DOC_AGGREGATOR_SYSTEM, aggregator_user, max_tokens=500, temperature=0.5)
    total_in += agg_usage["input_tokens"]
    total_out += agg_usage["output_tokens"]
    progress.progress(100, text="Complete.")

    specialist_outputs["aggregated"] = {"output": agg_output, "usage": agg_usage}
    st.session_state["doc_fan_results"] = specialist_outputs
    st.session_state["doc_fan_totals"] = (total_in, total_out)

if "doc_fan_results" in st.session_state:
    r = st.session_state["doc_fan_results"]
    total_in, total_out = st.session_state["doc_fan_totals"]

    spec_cols = st.columns(3)
    spec_defs = [
        ("summary", "📊 Summarizer", "#1E88E5", "#E3F2FD"),
        ("risk", "⚠️ Risk Analyst", "#E53935", "#FFEBEE"),
        ("opportunity", "✅ Opportunity Analyst", "#43A047", "#E8F5E9"),
    ]

    for col, (key, label, color, bg) in zip(spec_cols, spec_defs):
        with col:
            st.markdown(
                f"<div style='border-top:4px solid {color};background:{bg};"
                f"border-radius:6px;padding:10px 12px;'>"
                f"<strong style='color:{color};font-size:0.9em;'>{label}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(r[key]["output"])
            u = r[key]["usage"]
            st.caption(f"Input: {u['input_tokens']} | Output: {u['output_tokens']} tokens")

    st.markdown("**🔗 Aggregated Assessment:**")
    with st.container(border=True):
        st.markdown(r["aggregated"]["output"])
    u_agg = r["aggregated"]["usage"]
    st.caption(f"Aggregator — Input: {u_agg['input_tokens']} | Output: {u_agg['output_tokens']} tokens")

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM calls", 4)
    c2.metric("Total input tokens", total_in)
    c3.metric("Total output tokens", total_out)

# ── Section 3: Code Review Fan-Out ────────────────────────────────────────────
st.divider()
st.subheader("3 — Code Review Fan-Out")

st.markdown("Paste Python code. Three specialists review it from security, performance, and readability angles simultaneously.")

CODE_PRESETS = [
    "Custom code — paste below",
    """\
import sqlite3

def get_user(username):
    conn = sqlite3.connect("users.db")
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()
    return result

def process_data(items):
    result = []
    for i in range(len(items)):
        for j in range(len(items)):
            if items[i] == items[j] and i != j:
                result.append(items[i])
    return list(set(result))
""",
    """\
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def find_max(lst):
    m = lst[0]
    for x in lst:
        if x > m:
            m = x
    return m

passwords = ["hunter2", "password123", "letmein"]
API_KEY = "sk-1234567890abcdef"
""",
]

sel_code = st.selectbox("Pick a preset or paste your own:", CODE_PRESETS, key="code_preset")
code_text = st.text_area(
    "Python code:",
    value="" if sel_code == CODE_PRESETS[0] else sel_code,
    height=150,
    key="code_input",
)

if st.button("▶ Run Code Review Fan-Out", type="primary", disabled=not code_text.strip()):
    code_total_in, code_total_out = 0, 0
    code_results = {}
    code_progress = st.progress(0, text="Running 3 code reviewers…")

    for i, (key, sys_prompt, label) in enumerate([
        ("security", SECURITY_REVIEWER_SYSTEM, "Security Reviewer"),
        ("performance", PERFORMANCE_REVIEWER_SYSTEM, "Performance Reviewer"),
        ("readability", READABILITY_REVIEWER_SYSTEM, "Readability Reviewer"),
    ]):
        with st.spinner(f"{label} reviewing…"):
            output, usage = chat(sys_prompt, f"Code to review:\n\n{code_text.strip()}", max_tokens=400, temperature=0.2)
        code_results[key] = {"output": output, "usage": usage}
        code_total_in += usage["input_tokens"]
        code_total_out += usage["output_tokens"]
        code_progress.progress((i + 1) * 25, text=f"{label} done…")

    code_agg_user = (
        f"Security review:\n{code_results['security']['output']}\n\n"
        f"Performance review:\n{code_results['performance']['output']}\n\n"
        f"Readability review:\n{code_results['readability']['output']}"
    )
    with st.spinner("Lead reviewer aggregating…"):
        code_agg, code_agg_usage = chat(CODE_AGGREGATOR_SYSTEM, code_agg_user, max_tokens=400, temperature=0.4)
    code_total_in += code_agg_usage["input_tokens"]
    code_total_out += code_agg_usage["output_tokens"]
    code_progress.progress(100, text="Complete.")

    code_results["aggregated"] = {"output": code_agg, "usage": code_agg_usage}
    st.session_state["code_fan_results"] = code_results
    st.session_state["code_fan_totals"] = (code_total_in, code_total_out)

if "code_fan_results" in st.session_state:
    cr = st.session_state["code_fan_results"]
    code_total_in, code_total_out = st.session_state["code_fan_totals"]

    cr_cols = st.columns(3)
    cr_defs = [
        ("security", "🔒 Security", "#E53935", "#FFEBEE"),
        ("performance", "⚡ Performance", "#FB8C00", "#FFF3E0"),
        ("readability", "📖 Readability", "#1E88E5", "#E3F2FD"),
    ]

    for col, (key, label, color, bg) in zip(cr_cols, cr_defs):
        with col:
            st.markdown(
                f"<div style='border-top:4px solid {color};background:{bg};"
                f"border-radius:6px;padding:10px 12px;'>"
                f"<strong style='color:{color};'>{label}</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(cr[key]["output"])
            u = cr[key]["usage"]
            st.caption(f"Input: {u['input_tokens']} | Output: {u['output_tokens']} tokens")

    st.markdown("**🔗 Lead Reviewer — Consolidated Review:**")
    with st.container(border=True):
        st.markdown(cr["aggregated"]["output"])

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM calls", 4)
    c2.metric("Total input tokens", code_total_in)
    c3.metric("Total output tokens", code_total_out)

# ── Section 4: Voting Consensus ────────────────────────────────────────────────
st.divider()
st.subheader("4 — Voting Consensus")

st.markdown("""
Three separate agents answer the same question independently. A vote classifier then
analyses their agreement. High agreement → high confidence. Disagreement → signal
to dig deeper or consult a specialist.
""")

VOTE_PRESETS = [
    "Custom question — type below",
    "Is Python an interpreted or compiled language?",
    "What is the most important factor when choosing a database for a new application?",
    "Should you use tabs or spaces in Python code?",
    "Is recursion better than iteration for most problems?",
    "What is the best way to handle errors in a REST API?",
]

sel_vote = st.selectbox("Pick a preset question or write your own:", VOTE_PRESETS, key="vote_preset")
vote_q = st.text_area(
    "Question:",
    value="" if sel_vote == VOTE_PRESETS[0] else sel_vote,
    height=70,
    key="vote_question",
)

TEMPERATURES = [0.1, 0.5, 0.9]

if st.button("▶ Run Voting (3 agents)", type="primary", disabled=not vote_q.strip()):
    vote_answers = []
    vote_usages = []
    vote_prog = st.progress(0, text="Agent 1 of 3 answering…")

    for i, temp in enumerate(TEMPERATURES):
        with st.spinner(f"Agent {i+1} (temperature={temp}) answering…"):
            ans, u = chat(VOTING_AGENT_SYSTEM, vote_q.strip(), max_tokens=150, temperature=temp)
        vote_answers.append(ans)
        vote_usages.append(u)
        vote_prog.progress((i + 1) * 28, text=f"Agent {i+1} done…")

    classifier_user = (
        f"Question: {vote_q.strip()}\n\n"
        f"Agent 1 answer: {vote_answers[0]}\n\n"
        f"Agent 2 answer: {vote_answers[1]}\n\n"
        f"Agent 3 answer: {vote_answers[2]}"
    )
    with st.spinner("Vote classifier analysing agreement…"):
        raw_vote, u_vote = chat(VOTE_CLASSIFIER_SYSTEM, classifier_user, max_tokens=300, temperature=0.1)
    vote_prog.progress(100, text="Voting complete.")

    vote_result = None
    try:
        clean = raw_vote.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        vote_result = json.loads(clean)
    except json.JSONDecodeError:
        pass

    st.session_state["vote_answers"] = vote_answers
    st.session_state["vote_usages"] = vote_usages
    st.session_state["vote_result"] = vote_result
    st.session_state["vote_raw"] = raw_vote
    st.session_state["vote_u"] = u_vote

if "vote_answers" in st.session_state:
    answers = st.session_state["vote_answers"]
    usages = st.session_state["vote_usages"]
    vote_result = st.session_state.get("vote_result")
    u_vote = st.session_state.get("vote_u", {})

    agent_cols = st.columns(3)
    agent_colors = ["#1E88E5", "#8E24AA", "#43A047"]
    for col, (ans, u, temp, color) in zip(agent_cols, zip(answers, usages, TEMPERATURES, agent_colors)):
        with col:
            st.markdown(
                f"<div style='border-top:4px solid {color};background:#FAFAFA;"
                f"border-radius:6px;padding:10px 12px;'>"
                f"<strong style='color:{color};'>Agent (temp={temp})</strong>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.markdown(ans)
            st.caption(f"Output tokens: {u.get('output_tokens', 0)}")

    st.markdown("**Vote Classifier Result:**")
    if vote_result:
        agreement = vote_result.get("agreement", "unknown")
        majority = vote_result.get("majority_answer", "")
        count = vote_result.get("agreement_count", 0)
        notes = vote_result.get("disagreement_notes", "")

        agree_color = {"full": "#43A047", "partial": "#FB8C00", "none": "#E53935"}.get(agreement, "#8E24AA")
        agree_bg = {"full": "#E8F5E9", "partial": "#FFF3E0", "none": "#FFEBEE"}.get(agreement, "#F3E5F5")

        vote_cols = st.columns([1, 2])
        with vote_cols[0]:
            st.markdown(
                f"<div style='border-top:4px solid {agree_color};background:{agree_bg};"
                f"border-radius:6px;padding:14px;text-align:center;'>"
                f"<div style='font-size:0.78em;color:{agree_color};font-weight:bold;'>AGREEMENT</div>"
                f"<div style='font-size:1.6em;font-weight:bold;color:{agree_color};'>{agreement.upper()}</div>"
                f"<div style='font-size:0.85em;color:#555;'>{count}/3 agents aligned</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with vote_cols[1]:
            st.info(f"**Majority answer:** {majority}")
            if notes:
                st.warning(f"**Disagreement:** {notes}")
            else:
                st.success("All agents are in full agreement.")
    else:
        st.error("Vote classifier parse error. Raw output:")
        st.code(st.session_state.get("vote_raw", ""))

    total_vote_in = sum(u.get("input_tokens", 0) for u in usages) + u_vote.get("input_tokens", 0)
    total_vote_out = sum(u.get("output_tokens", 0) for u in usages) + u_vote.get("output_tokens", 0)
    c1, c2, c3 = st.columns(3)
    c1.metric("LLM calls", 4)
    c2.metric("Total input tokens", total_vote_in)
    c3.metric("Total output tokens", total_vote_out)
