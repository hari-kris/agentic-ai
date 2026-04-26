"""
Hour 21 Lab — Combine Patterns II (Capstone)
Module 5 | Core Agentic Patterns II

Combines all four Module 5 patterns in a single pipeline:
  [ROUTER] → content type detection
  [SPECIALISTS × 3] → parallel fan-out analysis
  [ORCHESTRATOR] → synthesises specialist outputs into draft
  [EVALUATOR-OPTIMIZER] → improves draft until quality threshold

Run: streamlit run module-5/hour21_lab_combine_patterns.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 21 — Combine Patterns II", page_icon="🏗️", layout="wide")
st.title("🏗️ Hour 21 — Combine Patterns II")
st.caption("Module 5 | Core Agentic Patterns II — Capstone")

st.markdown("""
This capstone lab combines all four Module 5 patterns in a **Smart Content Analysis Pipeline**:

1. **Routing** — classifies the input content type
2. **Parallelisation** — fans out to 3 domain-matched specialists
3. **Orchestrator-Subagents** — an orchestrator synthesises all specialist outputs into a structured draft
4. **Evaluator-Optimizer** — improves the draft until quality meets the threshold

Each stage's output becomes the next stage's input. The pipeline adapts to the content type —
a technical document gets technical specialists; a business memo gets business specialists.
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 21 Guide")
    st.markdown("""
**Pipeline stages:**
1. 🔀 Router → classifies content type
2. ⚡ Specialists × 3 → parallel fan-out
3. 🎯 Orchestrator → synthesises draft
4. 🔄 Evaluator-Optimizer → improves draft

**Sections:**
1. Architecture diagram
2. Run the pipeline (preset inputs)
3. Stage-by-stage results (tabbed)
4. Pattern attribution panel
5. Token ledger

**What to observe:**
- Each pattern handles a different structural concern
- The router's decision shapes which specialists run
- The evaluator-optimizer adds quality assurance on top
- Total token cost vs output quality trade-off
""")
    st.divider()
    st.info("**Key principle:** The patterns are not additive in cost alone — they are additive in quality. Each pattern removes a specific class of failure.")

# ── System Prompts ─────────────────────────────────────────────────────────────

# 1. Router
CONTENT_ROUTER_SYSTEM = """\
You are a content type classifier. Analyse the provided text and classify it.

Types:
- TECHNICAL: code, API docs, architecture specs, technical guides, engineering content
- BUSINESS: business proposals, strategy documents, market analysis, executive memos
- NEWS: news articles, press releases, current events, announcements
- SCIENTIFIC: research papers, academic articles, scientific reports, studies

Return ONLY valid JSON — no markdown fences:
{"content_type": "TECHNICAL|BUSINESS|NEWS|SCIENTIFIC", "confidence": 0.0, "reason": "one sentence"}\
"""

# 2. Specialists — 3 per content type
TECH_SPECIALISTS = {
    "architecture": (
        "You are a systems architecture analyst. Analyse the technical content for: "
        "(1) key system components or design decisions, "
        "(2) technical trade-offs or constraints, "
        "(3) potential weaknesses or improvement areas. "
        "Return structured analysis in 150 words.",
        "⚙️ Architecture", "#1E88E5", "#E3F2FD",
    ),
    "security": (
        "You are a security analyst. Analyse the technical content for: "
        "(1) security-relevant components or patterns, "
        "(2) potential vulnerabilities or risks, "
        "(3) security best practices that are followed or missing. "
        "Return structured analysis in 150 words.",
        "🔒 Security", "#E53935", "#FFEBEE",
    ),
    "implementation": (
        "You are an implementation quality reviewer. Analyse the technical content for: "
        "(1) implementation clarity and completeness, "
        "(2) edge cases or error handling coverage, "
        "(3) suggested improvements. "
        "Return structured analysis in 150 words.",
        "🔧 Implementation", "#43A047", "#E8F5E9",
    ),
}

BUSINESS_SPECIALISTS = {
    "strategy": (
        "You are a business strategy analyst. Analyse the business content for: "
        "(1) the core strategic objective, "
        "(2) competitive or market implications, "
        "(3) strategic risks or gaps. "
        "Return structured analysis in 150 words.",
        "📈 Strategy", "#8E24AA", "#F3E5F5",
    ),
    "financial": (
        "You are a financial analyst. Analyse the business content for: "
        "(1) financial implications or metrics mentioned, "
        "(2) cost/benefit signals, "
        "(3) financial risks or dependencies. "
        "Return structured analysis in 150 words.",
        "💰 Financial", "#43A047", "#E8F5E9",
    ),
    "stakeholder": (
        "You are a stakeholder analyst. Analyse the business content for: "
        "(1) key stakeholders mentioned or implied, "
        "(2) their interests and potential conflicts, "
        "(3) change management or communication needs. "
        "Return structured analysis in 150 words.",
        "👥 Stakeholder", "#FB8C00", "#FFF3E0",
    ),
}

NEWS_SPECIALISTS = {
    "facts": (
        "You are a fact extractor. From the news content, extract: "
        "(1) verifiable core facts (who, what, when, where), "
        "(2) key figures or organisations involved, "
        "(3) any claims that appear to need verification. "
        "Return structured analysis in 150 words.",
        "📋 Facts", "#1E88E5", "#E3F2FD",
    ),
    "impact": (
        "You are an impact analyst. From the news content, assess: "
        "(1) short-term implications of the event, "
        "(2) longer-term consequences or trends this connects to, "
        "(3) who is most affected and how. "
        "Return structured analysis in 150 words.",
        "📊 Impact", "#E53935", "#FFEBEE",
    ),
    "context": (
        "You are a context analyst. From the news content, provide: "
        "(1) relevant background that helps understand the story, "
        "(2) connections to broader trends or related events, "
        "(3) what is missing from the story. "
        "Return structured analysis in 150 words.",
        "🌐 Context", "#43A047", "#E8F5E9",
    ),
}

SCIENTIFIC_SPECIALISTS = {
    "methodology": (
        "You are a research methodology reviewer. Analyse the scientific content for: "
        "(1) the research methodology or approach used, "
        "(2) potential methodological strengths and limitations, "
        "(3) reproducibility or generalisability concerns. "
        "Return structured analysis in 150 words.",
        "🔬 Methodology", "#1E88E5", "#E3F2FD",
    ),
    "findings": (
        "You are a findings analyst. From the scientific content, extract: "
        "(1) key findings or conclusions, "
        "(2) statistical significance or evidence strength, "
        "(3) what remains uncertain or unexplained. "
        "Return structured analysis in 150 words.",
        "📊 Findings", "#8E24AA", "#F3E5F5",
    ),
    "implications": (
        "You are a research implications analyst. From the scientific content, assess: "
        "(1) practical implications of the findings, "
        "(2) implications for the field or adjacent fields, "
        "(3) future research directions suggested. "
        "Return structured analysis in 150 words.",
        "🌱 Implications", "#43A047", "#E8F5E9",
    ),
}

SPECIALIST_SETS = {
    "TECHNICAL": TECH_SPECIALISTS,
    "BUSINESS": BUSINESS_SPECIALISTS,
    "NEWS": NEWS_SPECIALISTS,
    "SCIENTIFIC": SCIENTIFIC_SPECIALISTS,
}

# 3. Orchestrator synthesiser
ORCHESTRATOR_SYSTEM = """\
You are a senior analyst and report writer. You receive three specialist analyses of the same content.
Your job is to synthesise them into a comprehensive 250–350 word structured report.

Format:
## Overall Assessment
[2–3 sentence executive summary]

## Key Findings
[4–6 bullet points integrating the most important insights across all analyses]

## Areas of Concern
[2–3 bullet points covering risks, gaps, or issues raised by specialists]

## Recommended Actions
[2–3 concrete, actionable next steps]

Write clearly and specifically. Do not list the specialist names. Integrate their insights.\
"""

# 4. Evaluator and Optimizer
REPORT_EVALUATOR_SYSTEM = """\
You are a report quality assessor. Evaluate the provided analysis report on four criteria (1–5):

- accuracy: are claims specific and grounded in the source content? (1=vague, 5=specific and verifiable)
- completeness: does the report cover all key aspects? (1=major gaps, 5=comprehensive)
- clarity: is the report well-written and easy to follow? (1=confusing, 5=crystal clear)
- actionability: are the recommendations concrete and useful? (1=vague advice, 5=specific and actionable)

Be strict. Reserve 5 for genuinely excellent reports.

Return ONLY valid JSON — no markdown fences:
{"accuracy": N, "completeness": N, "clarity": N, "actionability": N, "feedback": "one specific improvement"}\
"""

REPORT_OPTIMIZER_SYSTEM = """\
You are a senior report editor. You receive an analysis report and a quality critique.
Rewrite the report to address the specific feedback, maintaining what scores well.
Keep the same structure (## sections) and similar length (250–350 words).
Return only the improved report.\
"""

CONTENT_PRESETS = [
    "Custom content — paste below",
    """GraphQL API Design Specification v1.4
Authentication uses JWT tokens with 1-hour expiration. Refresh tokens valid for 30 days.
Query depth is limited to 10 levels. Mutations require explicit transaction boundaries.
Rate limiting: 1000 queries/hour per client. Introspection disabled in production.
Error handling: all errors return {"errors": [{"message": "...", "code": "..."}]}.
Schema validation runs on every deploy. Breaking changes require 3-month deprecation notice.
N+1 query protection via DataLoader is mandatory for all list resolvers.""",
    """Strategy Memo: Market Expansion to Southeast Asia
We have identified Vietnam and Indonesia as primary target markets for Q2 2025.
Both markets show 28% year-over-year growth in our product category. Total addressable
market is estimated at $840M. Recommended entry strategy is partnership-first, using local
distribution partners before establishing direct presence. Investment required: $3.2M over
18 months. Key risk: two established local competitors hold 60% combined market share.
Our differentiation is pricing (15% below market) and support quality. Regulatory approval
in both markets is expected within 60-90 days based on our legal team's preliminary review.""",
    """Breakthrough in Room-Temperature Superconductivity Claims Under Scrutiny
A South Korean research team has published a paper claiming to have created a material,
LK-99, that exhibits superconductivity at room temperature and ambient pressure. If verified,
this would be one of the most significant physics discoveries in decades, enabling lossless
power transmission, magnetically levitated transport, and vastly more efficient computing.
However, multiple independent replication attempts have produced mixed results. Three labs
report seeing the Meissner effect — a key indicator of superconductivity — while five others
could not replicate the findings. The original researchers have not yet responded to requests
for their raw data. The physics community is cautiously sceptical, citing the extraordinary
nature of the claims and the inconsistent replication record.""",
]


def parse_json(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


# ── Section 1: Architecture Diagram ───────────────────────────────────────────
st.divider()
st.subheader("1 — Smart Content Analysis Pipeline")

st.markdown(
    "<div style='background:#F8F9FA;border-radius:8px;padding:16px;'>"
    "<div style='display:flex;align-items:center;gap:10px;flex-wrap:wrap;'>"

    "<div style='border:2px solid #00897B;border-radius:6px;padding:8px 14px;background:#E0F2F1;text-align:center;min-width:100px;'>"
    "<div style='font-size:0.75em;color:#00897B;font-weight:bold;'>STAGE 1</div>"
    "<div style='font-size:1.3em;'>🔀</div>"
    "<div style='font-size:0.8em;font-weight:bold;color:#00897B;'>ROUTER</div>"
    "<div style='font-size:0.7em;color:#555;'>Routing Pattern</div>"
    "</div>"

    "<div style='font-size:1.6em;color:#999;'>→</div>"

    "<div style='border:2px solid #1E88E5;border-radius:6px;padding:8px 14px;background:#E3F2FD;text-align:center;min-width:120px;'>"
    "<div style='font-size:0.75em;color:#1E88E5;font-weight:bold;'>STAGE 2</div>"
    "<div style='font-size:1.3em;'>⚡</div>"
    "<div style='font-size:0.8em;font-weight:bold;color:#1E88E5;'>SPECIALISTS × 3</div>"
    "<div style='font-size:0.7em;color:#555;'>Parallelisation</div>"
    "</div>"

    "<div style='font-size:1.6em;color:#999;'>→</div>"

    "<div style='border:2px solid #8E24AA;border-radius:6px;padding:8px 14px;background:#F3E5F5;text-align:center;min-width:120px;'>"
    "<div style='font-size:0.75em;color:#8E24AA;font-weight:bold;'>STAGE 3</div>"
    "<div style='font-size:1.3em;'>🎯</div>"
    "<div style='font-size:0.8em;font-weight:bold;color:#8E24AA;'>ORCHESTRATOR</div>"
    "<div style='font-size:0.7em;color:#555;'>Orch-Subagents</div>"
    "</div>"

    "<div style='font-size:1.6em;color:#999;'>→</div>"

    "<div style='border:2px solid #E53935;border-radius:6px;padding:8px 14px;background:#FFEBEE;text-align:center;min-width:120px;'>"
    "<div style='font-size:0.75em;color:#E53935;font-weight:bold;'>STAGE 4</div>"
    "<div style='font-size:1.3em;'>🔄</div>"
    "<div style='font-size:0.8em;font-weight:bold;color:#E53935;'>EVAL-OPTIMIZER</div>"
    "<div style='font-size:0.7em;color:#555;'>Eval-Optimizer</div>"
    "</div>"

    "<div style='font-size:1.6em;color:#999;'>→</div>"

    "<div style='border:2px solid #43A047;border-radius:6px;padding:8px 14px;background:#E8F5E9;text-align:center;min-width:100px;'>"
    "<div style='font-size:1.3em;'>✅</div>"
    "<div style='font-size:0.8em;font-weight:bold;color:#43A047;'>FINAL REPORT</div>"
    "</div>"

    "</div></div>",
    unsafe_allow_html=True,
)

with st.expander("See all system prompts"):
    all_tabs = st.tabs(["Router", "Tech Specs", "Business Specs", "News Specs", "Science Specs", "Orchestrator", "Evaluator", "Optimizer"])
    with all_tabs[0]:
        st.code(CONTENT_ROUTER_SYSTEM, language="text")
    with all_tabs[1]:
        for key, (sys, label, _, _) in TECH_SPECIALISTS.items():
            st.markdown(f"**{label}**")
            st.code(sys, language="text")
    with all_tabs[2]:
        for key, (sys, label, _, _) in BUSINESS_SPECIALISTS.items():
            st.markdown(f"**{label}**")
            st.code(sys, language="text")
    with all_tabs[3]:
        for key, (sys, label, _, _) in NEWS_SPECIALISTS.items():
            st.markdown(f"**{label}**")
            st.code(sys, language="text")
    with all_tabs[4]:
        for key, (sys, label, _, _) in SCIENTIFIC_SPECIALISTS.items():
            st.markdown(f"**{label}**")
            st.code(sys, language="text")
    with all_tabs[5]:
        st.code(ORCHESTRATOR_SYSTEM, language="text")
    with all_tabs[6]:
        st.code(REPORT_EVALUATOR_SYSTEM, language="text")
    with all_tabs[7]:
        st.code(REPORT_OPTIMIZER_SYSTEM, language="text")

# ── Section 2: Run the Pipeline ────────────────────────────────────────────────
st.divider()
st.subheader("2 — Run the Pipeline")

EVAL_THRESHOLD = st.slider("Evaluator-Optimizer threshold (all criteria must reach this):", 2, 4, 3, key="eval_threshold")
MAX_OPT_ROUNDS = st.slider("Maximum optimization rounds:", 1, 3, 2, key="max_opt_rounds")

sel_content = st.selectbox("Pick a preset input or paste your own:", CONTENT_PRESETS, key="content_preset")
content_input = st.text_area(
    "Content to analyse:",
    value="" if sel_content == CONTENT_PRESETS[0] else sel_content,
    height=150,
    key="content_input",
)

if st.button("▶ Run Smart Content Pipeline", type="primary", disabled=not content_input.strip()):
    pipeline_results = {}
    token_ledger = {}
    total_in, total_out = 0, 0

    # ── Stage 1: Router ────────────────────────────────────────────────────────
    progress = st.progress(0, text="Stage 1/4 — Router classifying content…")
    with st.spinner("Router classifying…"):
        raw_route, u_route = chat(CONTENT_ROUTER_SYSTEM, content_input.strip(), max_tokens=200, temperature=0.1)
    total_in += u_route["input_tokens"]
    total_out += u_route["output_tokens"]
    token_ledger["router"] = u_route

    routing = parse_json(raw_route)
    if not routing:
        st.error("Router parse error:")
        st.code(raw_route)
        st.stop()

    content_type = routing.get("content_type", "BUSINESS")
    route_conf = routing.get("confidence", 0.0)
    route_reason = routing.get("reason", "")
    pipeline_results["routing"] = routing
    progress.progress(15, text=f"Content type: {content_type} ({route_conf:.0%} confidence)")

    # ── Stage 2: Specialist Fan-Out ────────────────────────────────────────────
    specialist_set = SPECIALIST_SETS.get(content_type, BUSINESS_SPECIALISTS)
    specialist_outputs = {}
    progress.progress(20, text="Stage 2/4 — Running 3 specialists in parallel…")

    spec_token_total_in, spec_token_total_out = 0, 0
    for i, (key, (sys_prompt, label, color, bg)) in enumerate(specialist_set.items()):
        with st.spinner(f"{label} analysing…"):
            s_output, u_spec = chat(
                sys_prompt,
                f"Content to analyse:\n\n{content_input.strip()}",
                max_tokens=350,
                temperature=0.3,
            )
        specialist_outputs[key] = {"output": s_output, "label": label, "color": color, "bg": bg, "usage": u_spec}
        total_in += u_spec["input_tokens"]
        total_out += u_spec["output_tokens"]
        spec_token_total_in += u_spec["input_tokens"]
        spec_token_total_out += u_spec["output_tokens"]
        progress.progress(20 + (i + 1) * 12, text=f"{label} done…")

    token_ledger["specialists"] = {"input_tokens": spec_token_total_in, "output_tokens": spec_token_total_out}
    pipeline_results["specialists"] = specialist_outputs

    # ── Stage 3: Orchestrator Synthesis ────────────────────────────────────────
    progress.progress(56, text="Stage 3/4 — Orchestrator synthesising…")
    spec_items = list(specialist_outputs.values())
    orch_user = "\n\n".join(
        f"{sp['label']} analysis:\n{sp['output']}"
        for sp in spec_items
    )
    with st.spinner("Orchestrator synthesising draft…"):
        draft, u_orch = chat(ORCHESTRATOR_SYSTEM, orch_user, max_tokens=700, temperature=0.5)
    total_in += u_orch["input_tokens"]
    total_out += u_orch["output_tokens"]
    token_ledger["orchestrator"] = u_orch
    pipeline_results["draft"] = draft
    progress.progress(66, text="Stage 4/4 — Evaluator-Optimizer running…")

    # ── Stage 4: Evaluator-Optimizer Loop ─────────────────────────────────────
    current_draft = draft
    opt_rounds = []
    eval_token_in, eval_token_out = 0, 0

    for round_num in range(1, MAX_OPT_ROUNDS + 1):
        with st.spinner(f"Evaluator (round {round_num})…"):
            raw_eval, u_eval = chat(REPORT_EVALUATOR_SYSTEM, current_draft, max_tokens=300, temperature=0.1)
        eval_token_in += u_eval["input_tokens"]
        eval_token_out += u_eval["output_tokens"]
        total_in += u_eval["input_tokens"]
        total_out += u_eval["output_tokens"]

        eval_result = parse_json(raw_eval)
        if not eval_result:
            break

        REPORT_CRITERIA = ["accuracy", "completeness", "clarity", "actionability"]
        scores = {k: eval_result.get(k, 0) for k in REPORT_CRITERIA}
        avg = sum(scores.values()) / len(scores)
        feedback = eval_result.get("feedback", "")
        below = [k for k in REPORT_CRITERIA if scores.get(k, 0) < EVAL_THRESHOLD]
        passed = len(below) == 0

        opt_rounds.append({
            "round": round_num,
            "draft": current_draft,
            "scores": scores,
            "avg": avg,
            "feedback": feedback,
            "passed": passed,
        })

        progress.progress(66 + round_num * 10, text=f"Eval round {round_num}: avg {avg:.1f}/5…")

        if passed:
            break

        if round_num < MAX_OPT_ROUNDS:
            opt_user = (
                f"Report to improve:\n{current_draft}\n\n"
                f"Scores: {', '.join(f'{k}={scores[k]}/5' for k in REPORT_CRITERIA)}\n"
                f"Feedback: {feedback}\n\n"
                f"Below threshold: {', '.join(below)}"
            )
            with st.spinner(f"Optimizer (round {round_num})…"):
                improved, u_opt = chat(REPORT_OPTIMIZER_SYSTEM, opt_user, max_tokens=700, temperature=0.4)
            eval_token_in += u_opt["input_tokens"]
            eval_token_out += u_opt["output_tokens"]
            total_in += u_opt["input_tokens"]
            total_out += u_opt["output_tokens"]
            current_draft = improved

    token_ledger["eval_optimizer"] = {"input_tokens": eval_token_in, "output_tokens": eval_token_out}
    pipeline_results["opt_rounds"] = opt_rounds
    pipeline_results["final_report"] = current_draft
    pipeline_results["total_calls"] = 1 + 3 + 1 + len(opt_rounds) * 2
    progress.progress(100, text="Pipeline complete.")

    st.session_state["pipeline_results"] = pipeline_results
    st.session_state["token_ledger"] = token_ledger
    st.session_state["pipeline_totals"] = (total_in, total_out)
    st.session_state["content_type"] = content_type

# ── Section 3: Stage-by-Stage Results ─────────────────────────────────────────
if "pipeline_results" in st.session_state:
    pr = st.session_state["pipeline_results"]
    ledger = st.session_state["token_ledger"]
    total_in, total_out = st.session_state["pipeline_totals"]
    content_type = st.session_state["content_type"]

    st.divider()
    st.subheader("3 — Stage-by-Stage Results")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔀 1. Router",
        "⚡ 2. Specialists",
        "🎯 3. Orchestrator Draft",
        "🔄 4. Evaluator Loop",
        "✅ Final Report",
    ])

    with tab1:
        routing = pr.get("routing", {})
        r_cols = st.columns(3)
        r_cols[0].metric("Content Type", routing.get("content_type", "—"))
        r_cols[1].metric("Confidence", f"{routing.get('confidence', 0):.0%}")
        r_cols[2].metric("LLM Calls", 1)
        st.info(f"**Router reason:** {routing.get('reason', '')}")
        st.markdown("**Raw routing JSON:**")
        st.code(json.dumps(routing, indent=2), language="json")

    with tab2:
        specs = pr.get("specialists", {})
        s_cols = st.columns(3)
        for col, (key, spec) in zip(s_cols, specs.items()):
            with col:
                st.markdown(
                    f"<div style='border-top:4px solid {spec['color']};background:{spec['bg']};"
                    f"border-radius:6px;padding:10px 12px;'>"
                    f"<strong style='color:{spec['color']};'>{spec['label']}</strong>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(spec["output"])
                u = spec["usage"]
                st.caption(f"Input: {u['input_tokens']} | Output: {u['output_tokens']} tokens")

    with tab3:
        st.markdown("**Orchestrator synthesised draft:**")
        with st.container(border=True):
            st.markdown(pr.get("draft", ""))
        u_o = ledger.get("orchestrator", {})
        st.caption(f"Orchestrator — Input: {u_o.get('input_tokens', 0)} | Output: {u_o.get('output_tokens', 0)} tokens")

    with tab4:
        opt_rounds = pr.get("opt_rounds", [])
        REPORT_CRITERIA = ["accuracy", "completeness", "clarity", "actionability"]
        CRIT_COLORS = {"accuracy": "#1E88E5", "completeness": "#43A047", "clarity": "#8E24AA", "actionability": "#E53935"}

        for rd in opt_rounds:
            passed = rd["passed"]
            with st.expander(
                f"Round {rd['round']} — avg {rd['avg']:.1f}/5 {'✅ ACCEPTED' if passed else '🔁 OPTIMIZED'}",
                expanded=(rd["round"] == len(opt_rounds)),
            ):
                score_cols = st.columns(4)
                for col, crit in zip(score_cols, REPORT_CRITERIA):
                    s = rd["scores"].get(crit, 0)
                    col.metric(crit.capitalize(), f"{s}/5")
                    col.progress(s / 5)
                if rd["feedback"]:
                    st.info(f"**Feedback:** {rd['feedback']}")

        if len(opt_rounds) > 1:
            st.markdown("**Score progression:**")
            prog_cols = st.columns(len(opt_rounds))
            for col, rd in zip(prog_cols, opt_rounds):
                delta = f"+{rd['avg'] - opt_rounds[0]['avg']:.1f}" if rd["round"] > 1 else None
                col.metric(f"Round {rd['round']}", f"{rd['avg']:.1f}/5", delta=delta)

    with tab5:
        st.markdown("**Final Report:**")
        with st.container(border=True):
            st.markdown(pr.get("final_report", ""))

# ── Section 4: Pattern Attribution ────────────────────────────────────────────
if "pipeline_results" in st.session_state:
    st.divider()
    st.subheader("4 — Pattern Attribution")

    st.markdown("Each stage of the pipeline is driven by a different Module 5 pattern.")

    attr_cols = st.columns(4)
    attr_items = [
        ("#00897B", "#E0F2F1", "🔀", "Routing", "Stage 1", "The router classifies the content type and selects the appropriate specialist set. Without routing, every document would get the same generic specialists."),
        ("#1E88E5", "#E3F2FD", "⚡", "Parallelisation", "Stage 2", "Three specialists analyse the same content simultaneously from different angles. Each goes deep in its domain rather than shallow across all."),
        ("#8E24AA", "#F3E5F5", "🎯", "Orchestrator-Subagents", "Stage 3", "The orchestrator receives all specialist outputs and synthesises them into a structured draft. It coordinates without doing the research itself."),
        ("#E53935", "#FFEBEE", "🔄", "Evaluator-Optimizer", "Stage 4", "The evaluator scores the draft against four criteria. If any fall below the threshold, the optimizer improves the draft. Quality assurance is automated."),
    ]

    for col, (color, bg, icon, pattern, stage, desc) in zip(attr_cols, attr_items):
        with col:
            st.markdown(
                f"<div style='border-top:4px solid {color};background:{bg};"
                f"border-radius:6px;padding:12px;min-height:220px;'>"
                f"<div style='font-size:1.8em;text-align:center;'>{icon}</div>"
                f"<div style='font-weight:bold;color:{color};text-align:center;margin:6px 0;font-size:0.95em;'>{pattern}</div>"
                f"<div style='font-size:0.78em;color:#00897B;text-align:center;font-weight:bold;margin-bottom:6px;'>{stage}</div>"
                f"<div style='font-size:0.8em;color:#444;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

# ── Section 5: Token Ledger ────────────────────────────────────────────────────
if "pipeline_results" in st.session_state:
    st.divider()
    st.subheader("5 — Token Ledger")

    pr = st.session_state["pipeline_results"]
    ledger = st.session_state["token_ledger"]
    total_in, total_out = st.session_state["pipeline_totals"]

    ledger_cols = st.columns(4)
    ledger_items = [
        ("🔀 Router", ledger.get("router", {})),
        ("⚡ Specialists (×3)", ledger.get("specialists", {})),
        ("🎯 Orchestrator", ledger.get("orchestrator", {})),
        ("🔄 Eval-Optimizer", ledger.get("eval_optimizer", {})),
    ]

    for col, (label, usage) in zip(ledger_cols, ledger_items):
        in_t = usage.get("input_tokens", 0)
        out_t = usage.get("output_tokens", 0)
        col.metric(label, f"{in_t + out_t:,} tokens")
        col.caption(f"In: {in_t:,} | Out: {out_t:,}")

    st.divider()
    summary_cols = st.columns(4)
    summary_cols[0].metric("Total LLM calls", pr.get("total_calls", 0))
    summary_cols[1].metric("Total input tokens", f"{total_in:,}")
    summary_cols[2].metric("Total output tokens", f"{total_out:,}")
    summary_cols[3].metric("Combined patterns", 4)

    st.caption(
        "Token cost breakdown: Router (cheapest — small input/output) → "
        "Specialists (moderate × 3 calls) → Orchestrator (expensive — large input from 3 specialists) → "
        "Eval-Optimizer (variable — depends on rounds). "
        "The Orchestrator is the costliest single call because it receives all specialist outputs as context."
    )
