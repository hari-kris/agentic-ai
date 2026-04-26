"""
Hour 17 Lab — Routing Pattern
Module 5 | Core Agentic Patterns II

A classifier agent reads each input and dispatches it to the most appropriate
sub-pipeline. This lab shows domain routing, complexity-based routing, and
confidence-based fallback.

Run: streamlit run module-5/hour17_lab_routing_pattern.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 17 — Routing Pattern", page_icon="🔀", layout="wide")
st.title("🔀 Hour 17 — Routing Pattern")
st.caption("Module 5 | Core Agentic Patterns II")

st.markdown("""
The **Routing Pattern** uses a classifier agent to direct each incoming request to the
most appropriate sub-pipeline. Unlike prompt chaining (always linear), routing creates
**branching**: different inputs follow entirely different paths.

This lab covers three routing variants:
1. **Domain router** — classifies by subject area and routes to a matching specialist
2. **Complexity router** — routes based on question difficulty (fast path vs deep path)
3. **Confidence-based fallback** — low-confidence routing decisions escalate rather than guess
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 17 Guide")
    st.markdown("""
**Sections in this lab:**
1. **Architecture diagram** — router and specialist pipelines
2. **Domain router** — 5 domains, JSON routing decision
3. **Complexity router** — simple vs complex path
4. **Confidence fallback** — uncertain inputs escalate

**What to observe:**
- The router's output is JSON, not prose — machine-readable for Python dispatch
- `confidence` is the signal that drives fallback logic
- The specialist never sees the routing decision — only its own task
- Token cost: routing call + specialist call vs one combined call
""")
    st.divider()
    st.markdown("**Experiment ideas:**")
    st.markdown("- Submit an ambiguous question that could fit two domains — watch confidence drop")
    st.markdown("- Try a simple factual question vs a multi-part analysis — see path diverge")
    st.markdown("- Lower the confidence threshold to 0.8 and see more fallbacks")
    st.divider()
    st.info("**Key principle:** The router's only job is classification. It must not answer the question. That separation is what makes pipelines composable.")

# ── System Prompts ─────────────────────────────────────────────────────────────
DOMAIN_ROUTER_SYSTEM = """\
You are a request classifier. Given a user question, identify the most appropriate domain.

Domains:
- TECH: software, hardware, programming, networking, data science, IT systems
- MEDICAL: health, medicine, symptoms, treatments, anatomy, mental health
- FINANCE: money, investing, taxes, budgets, markets, personal finance
- LEGAL: laws, contracts, rights, regulations, compliance, court procedures
- GENERAL: anything that does not clearly fit one of the above domains

Rules:
- Choose exactly one domain
- Be strict: only use GENERAL when no other domain fits clearly
- Confidence 0.9+ means you are almost certain; 0.5 means roughly even between two domains

Return ONLY valid JSON — no markdown fences, no commentary:
{"route": "TECH|MEDICAL|FINANCE|LEGAL|GENERAL", "confidence": 0.0, "reason": "one sentence"}\
"""

TECH_SYSTEM = """\
You are a technical expert. Answer technology and software questions accurately and concisely.
Use specific terminology and concrete examples. Keep your answer under 180 words.\
"""

MEDICAL_SYSTEM = """\
You are a medical information assistant. Provide clear, accurate health information grounded
in established medical knowledge. Always note that this is general information and not a
substitute for professional medical advice. Keep your answer under 180 words.\
"""

FINANCE_SYSTEM = """\
You are a financial information assistant. Provide clear, accurate financial and investment
information. Note that this is general information and not personalised financial advice.
Keep your answer under 180 words.\
"""

LEGAL_SYSTEM = """\
You are a legal information assistant. Explain legal concepts clearly and accurately.
Always note that this is general information and not professional legal advice.
Keep your answer under 180 words.\
"""

GENERAL_SYSTEM = """\
You are a knowledgeable, helpful assistant. Answer questions clearly and concisely.
Keep your answer under 180 words.\
"""

COMPLEXITY_ROUTER_SYSTEM = """\
You are a question complexity classifier. Determine whether a question requires a brief
direct answer or a thorough analytical response.

- simple: factual questions, definitions, short "how to" procedures — answerable in 1–3 sentences
- complex: multi-part questions, comparisons, open-ended analysis, "why" or "should I" questions

Return ONLY valid JSON — no markdown fences, no commentary:
{"complexity": "simple|complex", "reason": "one sentence explaining the classification"}\
"""

FAST_PATH_SYSTEM = """\
You are a concise assistant. Give a direct, factual answer in 1–3 sentences. No padding,
no preamble. Just the answer.\
"""

DEEP_PATH_SYSTEM = """\
You are a thorough analyst. Provide a comprehensive response with:
1. Context (why this matters)
2. Main explanation (the core answer with specifics)
3. Key considerations or trade-offs
4. Practical implication or next step

Aim for 250–350 words. Use clear structure.\
"""

SPECIALISTS = {
    "TECH": (TECH_SYSTEM, "#1E88E5", "#E3F2FD", "🔵"),
    "MEDICAL": (MEDICAL_SYSTEM, "#E53935", "#FFEBEE", "🔴"),
    "FINANCE": (FINANCE_SYSTEM, "#43A047", "#E8F5E9", "🟢"),
    "LEGAL": (LEGAL_SYSTEM, "#FB8C00", "#FFF3E0", "🟠"),
    "GENERAL": (GENERAL_SYSTEM, "#8E24AA", "#F3E5F5", "🟣"),
}


def parse_json(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


# ── Section 1: Architecture Diagram ───────────────────────────────────────────
st.divider()
st.subheader("1 — The Routing Pipeline")

st.markdown("""
The router reads the input and returns a routing decision. Python dispatches to
the appropriate specialist. The specialist never sees the routing logic — only its task.
""")

router_col, arrow_col, specialist_col = st.columns([1.2, 0.3, 2.5])

with router_col:
    st.markdown(
        "<div style='border-top:4px solid #00897B;background:#E0F2F1;border-radius:6px;"
        "padding:16px;text-align:center;min-height:180px;'>"
        "<div style='font-size:2em;'>🔀</div>"
        "<div style='font-weight:bold;color:#00897B;margin:6px 0;'>[ROUTER]</div>"
        "<div style='font-size:0.82em;color:#444;'>Reads the input.<br/>Returns JSON routing decision.<br/>Does NOT answer.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

with arrow_col:
    st.markdown(
        "<div style='display:flex;align-items:center;justify-content:center;"
        "height:180px;font-size:1.8em;color:#999;'>→</div>",
        unsafe_allow_html=True,
    )

with specialist_col:
    spec_cols = st.columns(5)
    for col, (route, (_, color, bg, icon)) in zip(spec_cols, SPECIALISTS.items()):
        with col:
            st.markdown(
                f"<div style='border-top:4px solid {color};background:{bg};"
                f"border-radius:6px;padding:8px;text-align:center;min-height:120px;'>"
                f"<div style='font-size:1.5em;'>{icon}</div>"
                f"<div style='font-weight:bold;color:{color};font-size:0.78em;margin:4px 0;'>{route}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

st.markdown("")
st.markdown("""
**Routing JSON:**
```json
{"route": "TECH", "confidence": 0.94, "reason": "Question is about Python package installation"}
```
The `confidence` field determines whether to use the route or fall back to an escalation handler.
""")

with st.expander("See system prompts"):
    tabs = st.tabs(["Router", "Tech", "Medical", "Finance", "Legal", "General"])
    prompts = [DOMAIN_ROUTER_SYSTEM, TECH_SYSTEM, MEDICAL_SYSTEM, FINANCE_SYSTEM, LEGAL_SYSTEM, GENERAL_SYSTEM]
    for tab, prompt in zip(tabs, prompts):
        with tab:
            st.code(prompt, language="text")

# ── Section 2: Domain Router ───────────────────────────────────────────────────
st.divider()
st.subheader("2 — Domain Router")

st.markdown("Enter a question. The router classifies it and dispatches to the correct specialist.")

CONFIDENCE_THRESHOLD = st.slider(
    "Confidence threshold (below this → ESCALATE):",
    min_value=0.4, max_value=0.9, value=0.6, step=0.05,
    key="domain_threshold"
)

DOMAIN_PRESETS = [
    "Custom question — type below",
    "How do I fix a Python ImportError when my module can't find a package?",
    "What are the early warning signs of type 2 diabetes?",
    "Should I invest in index funds or individual stocks for long-term growth?",
    "What is the difference between a contract and a memorandum of understanding?",
    "What causes the northern lights?",
    "Is it better to use microservices or a monolith for a startup?",
]

sel_domain = st.selectbox("Pick a preset question or write your own:", DOMAIN_PRESETS, key="domain_preset")
domain_q = st.text_area(
    "Question:",
    value="" if sel_domain == DOMAIN_PRESETS[0] else sel_domain,
    height=70,
    key="domain_question",
)

if st.button("▶ Route and Answer", type="primary", disabled=not domain_q.strip()):
    with st.spinner("Router classifying…"):
        raw_route, u_router = chat(DOMAIN_ROUTER_SYSTEM, domain_q.strip(), max_tokens=200, temperature=0.1)

    routing = parse_json(raw_route)
    if not routing:
        st.error("Router returned unexpected output. Showing raw:")
        st.code(raw_route)
        st.stop()

    route = routing.get("route", "GENERAL")
    confidence = routing.get("confidence", 0.0)
    reason = routing.get("reason", "")

    st.session_state["domain_routing"] = routing
    st.session_state["domain_q_val"] = domain_q.strip()
    st.session_state["domain_threshold_val"] = CONFIDENCE_THRESHOLD

    if confidence < CONFIDENCE_THRESHOLD:
        st.session_state["domain_answer"] = None
        st.session_state["domain_answer_usage"] = None
        st.session_state["domain_escalated"] = True
    else:
        specialist_system = SPECIALISTS.get(route, SPECIALISTS["GENERAL"])[0]
        with st.spinner(f"Routing to {route} specialist…"):
            answer, u_spec = chat(specialist_system, domain_q.strip(), max_tokens=350, temperature=0.4)
        st.session_state["domain_answer"] = answer
        st.session_state["domain_answer_usage"] = u_spec
        st.session_state["domain_router_usage"] = u_router
        st.session_state["domain_escalated"] = False

if "domain_routing" in st.session_state:
    routing = st.session_state["domain_routing"]
    route = routing.get("route", "GENERAL")
    confidence = routing.get("confidence", 0.0)
    reason = routing.get("reason", "")
    threshold = st.session_state.get("domain_threshold_val", 0.6)
    _, color, bg, icon = SPECIALISTS.get(route, SPECIALISTS["GENERAL"])

    st.markdown("**Routing Decision:**")
    dcols = st.columns([1.5, 1.5, 3])
    with dcols[0]:
        st.markdown(
            f"<div style='border-top:4px solid #00897B;background:#E0F2F1;"
            f"border-radius:6px;padding:12px;text-align:center;'>"
            f"<div style='font-size:0.78em;color:#00897B;font-weight:bold;'>ROUTE</div>"
            f"<div style='font-size:1.8em;font-weight:bold;color:{color};'>{icon} {route}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with dcols[1]:
        conf_color = "#43A047" if confidence >= threshold else "#E53935"
        st.markdown(
            f"<div style='border-top:4px solid {conf_color};background:#FAFAFA;"
            f"border-radius:6px;padding:12px;text-align:center;'>"
            f"<div style='font-size:0.78em;color:{conf_color};font-weight:bold;'>CONFIDENCE</div>"
            f"<div style='font-size:1.8em;font-weight:bold;color:{conf_color};'>{confidence:.0%}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with dcols[2]:
        st.markdown(
            f"<div style='border-top:4px solid #8E24AA;background:#F3E5F5;"
            f"border-radius:6px;padding:12px;'>"
            f"<div style='font-size:0.78em;color:#8E24AA;font-weight:bold;'>REASON</div>"
            f"<div style='font-size:0.9em;color:#333;margin-top:4px;'>{reason}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.progress(confidence, text=f"Confidence: {confidence:.0%} (threshold: {threshold:.0%})")

    if st.session_state.get("domain_escalated"):
        st.warning(
            f"**ESCALATED** — Confidence {confidence:.0%} is below threshold {threshold:.0%}. "
            "In a production system, this input would be routed to a human agent or a clarification step.",
            icon="⚠️",
        )
        st.info("**Suggested action:** Ask the user to clarify or provide more context before routing.")
    else:
        answer = st.session_state.get("domain_answer", "")
        u_spec = st.session_state.get("domain_answer_usage", {})
        u_router = st.session_state.get("domain_router_usage", {})

        st.markdown(
            f"<div style='border-top:4px solid {color};background:{bg};"
            f"border-radius:6px;padding:12px 16px;margin-top:12px;'>"
            f"<div style='font-weight:bold;color:{color};margin-bottom:6px;'>"
            f"{icon} [{route} SPECIALIST] Answer</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.markdown(answer)

        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Router input tokens", u_router.get("input_tokens", 0))
        c2.metric("Specialist input tokens", u_spec.get("input_tokens", 0))
        c3.metric("Total LLM calls", 2)

# ── Section 3: Complexity Router ──────────────────────────────────────────────
st.divider()
st.subheader("3 — Complexity Router")

st.markdown("""
The same question can be answered briefly (cheap, fast) or thoroughly (expensive, slower).
A complexity router decides which path to take based on the question's nature.
""")

path_cols = st.columns(2)
with path_cols[0]:
    st.markdown(
        "<div style='border-top:4px solid #43A047;background:#E8F5E9;"
        "border-radius:6px;padding:12px;text-align:center;'>"
        "<div style='font-weight:bold;color:#43A047;'>⚡ FAST PATH</div>"
        "<div style='font-size:0.85em;color:#444;margin-top:4px;'>1–3 sentences. Direct answer. Low cost.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
with path_cols[1]:
    st.markdown(
        "<div style='border-top:4px solid #1E88E5;background:#E3F2FD;"
        "border-radius:6px;padding:12px;text-align:center;'>"
        "<div style='font-weight:bold;color:#1E88E5;'>🔍 DEEP PATH</div>"
        "<div style='font-size:0.85em;color:#444;margin-top:4px;'>250–350 words. Structured analysis. Higher cost.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

COMPLEXITY_PRESETS = [
    "Custom question — type below",
    "What is a REST API?",
    "Should a startup use microservices or a monolith, and how should that decision evolve over time?",
    "What does HTTP 404 mean?",
    "What are the trade-offs between SQL and NoSQL databases for a high-traffic web application?",
    "What year was Python created?",
]

sel_cx = st.selectbox("Pick a preset question or write your own:", COMPLEXITY_PRESETS, key="cx_preset")
cx_q = st.text_area(
    "Question:",
    value="" if sel_cx == COMPLEXITY_PRESETS[0] else sel_cx,
    height=70,
    key="cx_question",
)

if st.button("▶ Route by Complexity", type="primary", disabled=not cx_q.strip()):
    with st.spinner("Complexity router analysing…"):
        raw_cx, u_cx_router = chat(COMPLEXITY_ROUTER_SYSTEM, cx_q.strip(), max_tokens=150, temperature=0.1)

    cx_decision = parse_json(raw_cx)
    if not cx_decision:
        st.error("Router returned unexpected output:")
        st.code(raw_cx)
        st.stop()

    complexity = cx_decision.get("complexity", "complex")
    cx_reason = cx_decision.get("reason", "")

    if complexity == "simple":
        path_system = FAST_PATH_SYSTEM
        path_label = "⚡ FAST PATH"
        path_color = "#43A047"
        path_bg = "#E8F5E9"
        max_tok = 150
    else:
        path_system = DEEP_PATH_SYSTEM
        path_label = "🔍 DEEP PATH"
        path_color = "#1E88E5"
        path_bg = "#E3F2FD"
        max_tok = 600

    with st.spinner(f"Running {complexity} path…"):
        cx_answer, u_cx_spec = chat(path_system, cx_q.strip(), max_tokens=max_tok, temperature=0.4)

    st.session_state["cx_result"] = {
        "complexity": complexity,
        "reason": cx_reason,
        "answer": cx_answer,
        "path_label": path_label,
        "path_color": path_color,
        "path_bg": path_bg,
        "u_router": u_cx_router,
        "u_spec": u_cx_spec,
    }

if "cx_result" in st.session_state:
    r = st.session_state["cx_result"]
    st.markdown(
        f"<div style='border-left:4px solid #00897B;background:#E0F2F1;"
        f"padding:8px 12px;border-radius:4px;margin-bottom:8px;'>"
        f"<strong style='color:#00897B;'>Router decision:</strong> "
        f"<code>{r['complexity'].upper()}</code> — {r['reason']}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='border-top:4px solid {r['path_color']};background:{r['path_bg']};"
        f"border-radius:6px;padding:12px 16px;'>"
        f"<strong style='color:{r['path_color']};'>{r['path_label']} Answer</strong>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.markdown(r["answer"])

    u_r = r["u_router"]
    u_s = r["u_spec"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Router tokens", u_r.get("input_tokens", 0) + u_r.get("output_tokens", 0))
    c2.metric("Specialist output tokens", u_s.get("output_tokens", 0))
    c3.metric("Path taken", r["complexity"].upper())

# ── Section 4: Confidence-Based Fallback ──────────────────────────────────────
st.divider()
st.subheader("4 — Routing Trace Inspector")

st.markdown("""
Test the full routing trace. Enter any question — including ambiguous or off-topic ones —
and see the complete routing chain: decision JSON, confidence, dispatch, and response.
""")

TRACE_PRESETS = [
    "Custom — type your own",
    "Can you recommend something? I'm not sure what I need.",
    "How do I appeal a parking ticket?",
    "What's the best way to store passwords securely in a Python app?",
    "My stomach has been hurting after eating — what could cause this?",
    "Is it a good time to buy a house right now?",
    "How do I set up a standing desk correctly?",
]

sel_trace = st.selectbox("Pick a preset or write your own:", TRACE_PRESETS, key="trace_preset")
trace_q = st.text_area(
    "Question:",
    value="" if sel_trace == TRACE_PRESETS[0] else sel_trace,
    height=70,
    key="trace_question",
)
trace_threshold = st.slider("Confidence threshold for this trace:", 0.4, 0.9, 0.65, 0.05, key="trace_threshold")

if st.button("▶ Show Routing Trace", type="primary", disabled=not trace_q.strip()):
    with st.spinner("Router classifying…"):
        raw_tr, u_tr = chat(DOMAIN_ROUTER_SYSTEM, trace_q.strip(), max_tokens=200, temperature=0.1)

    trace_routing = parse_json(raw_tr)
    if not trace_routing:
        st.error("Router parse error:")
        st.code(raw_tr)
        st.stop()

    tr_route = trace_routing.get("route", "GENERAL")
    tr_conf = trace_routing.get("confidence", 0.0)
    tr_reason = trace_routing.get("reason", "")
    escalated = tr_conf < trace_threshold

    if not escalated:
        spec_sys = SPECIALISTS.get(tr_route, SPECIALISTS["GENERAL"])[0]
        with st.spinner(f"Running {tr_route} specialist…"):
            tr_answer, u_tr_spec = chat(spec_sys, trace_q.strip(), max_tokens=350, temperature=0.4)
    else:
        tr_answer = None
        u_tr_spec = {}

    st.session_state["trace_result"] = {
        "routing": trace_routing,
        "route": tr_route,
        "confidence": tr_conf,
        "reason": tr_reason,
        "escalated": escalated,
        "answer": tr_answer,
        "threshold": trace_threshold,
        "u_router": u_tr,
        "u_spec": u_tr_spec,
    }

if "trace_result" in st.session_state:
    t = st.session_state["trace_result"]

    st.markdown("**Step 1 — Router output (raw JSON):**")
    st.code(json.dumps(t["routing"], indent=2), language="json")

    conf_ok = t["confidence"] >= t["threshold"]
    st.markdown(
        f"**Step 2 — Confidence gate:** {t['confidence']:.0%} {'≥' if conf_ok else '<'} "
        f"threshold {t['threshold']:.0%} → "
        + (f"✅ **DISPATCH to {t['route']}**" if conf_ok else "❌ **ESCALATE**")
    )

    if t["escalated"]:
        st.warning(
            f"**ESCALATED** — Confidence {t['confidence']:.0%} is below threshold {t['threshold']:.0%}.\n\n"
            "The input is ambiguous or out-of-scope. A production system would:\n"
            "- Ask the user for clarification, OR\n"
            "- Route to a human agent, OR\n"
            "- Try multiple specialists and let a synthesiser decide.",
            icon="⚠️",
        )
    else:
        _, color, bg, icon = SPECIALISTS.get(t["route"], SPECIALISTS["GENERAL"])
        st.markdown(f"**Step 3 — {icon} [{t['route']} SPECIALIST] responds:**")
        st.markdown(
            f"<div style='border-left:4px solid {color};background:{bg};"
            f"padding:10px 14px;border-radius:4px;'>{t['answer']}</div>",
            unsafe_allow_html=True,
        )
        u_r = t["u_router"]
        u_s = t["u_spec"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Router input tokens", u_r.get("input_tokens", 0))
        c2.metric("Router output tokens", u_r.get("output_tokens", 0))
        c3.metric("Specialist input tokens", u_s.get("input_tokens", 0))
        c4.metric("Total LLM calls", 2)
