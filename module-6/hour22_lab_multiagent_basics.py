"""
Hour 22 Lab — Multi-Agent Basics
Module 6 | Multi-Agent Systems

Flat vs hierarchical multi-agent systems. Three specialist agents independently
analyse a news headline, then an orchestrator agent reads all three outputs and
writes a coordinated synthesis.

Run: streamlit run module-6/hour22_lab_multiagent_basics.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 22 — Multi-Agent Basics", page_icon="🤝", layout="wide")
st.title("🤝 Hour 22 — Multi-Agent Basics")
st.caption("Module 6 | Multi-Agent Systems")

st.markdown("""
In a **flat multi-agent system**, agents operate independently — each processes the same input
but produces its own output with no shared state and no coordination. They may contradict each other.
In a **hierarchical system**, those same agents feed into an **orchestrator** that reads all outputs
and produces a single, resolved synthesis. The key insight: coordination does not come free —
it costs one extra LLM call — but it delivers a coherent view that no flat system can guarantee.
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 22 Guide")
    st.markdown("""
**Sections in this lab:**
1. Flat vs Hierarchical architecture diagram
2. Flat system — three independent specialist agents
3. Hierarchical — orchestrator synthesises all three outputs

**What to observe:**
- Flat agents may contradict each other on the same headline
- The orchestrator resolves conflicts into one coherent view
- Hierarchical costs one extra LLM call but eliminates fragmentation
- Confidence scores reveal where specialists disagree
""")
    st.divider()
    st.markdown("""
**Experiment ideas:**
- Paste a headline with mixed signals (e.g., a tech layoff that also signals AI investment)
- Pick a headline where the fact-checker would flag something — see how the orchestrator handles it
- Compare the word count of three flat outputs vs the single orchestrated synthesis
""")
    st.divider()
    st.info("**Key principle:** Flat agents work in isolation. A hierarchy adds a coordination layer that reads all outputs and resolves conflicts — a single synthesised view beats three disconnected opinions.")

# ── System Prompts ─────────────────────────────────────────────────────────────
SUMMARIZER_SYSTEM = """\
You are a news summariser agent. Given a news headline, produce a concise factual summary
of what the headline reports. Focus on the who, what, when, and where.

Return ONLY valid JSON — no markdown fences, no commentary:
{"analysis": "2-3 sentence factual summary of what the headline reports", "confidence": 0.0, "key_points": ["point 1", "point 2", "point 3"]}\
"""

FACT_CHECKER_SYSTEM = """\
You are a fact-checking agent. Given a news headline, assess its factual claims.
Identify what can be verified, what is ambiguous, and what claims require scrutiny.
Do not look up the web — assess based on plausibility and internal consistency.

Return ONLY valid JSON — no markdown fences, no commentary:
{"analysis": "2-3 sentences on factual reliability and claims that need verification", "confidence": 0.0, "key_points": ["verifiable claim or concern 1", "verifiable claim or concern 2", "concern 3"]}\
"""

IMPLICATIONS_SYSTEM = """\
You are an implications analyst. Given a news headline, analyse the broader consequences:
economic, political, social, or technological. Think beyond the immediate event.

Return ONLY valid JSON — no markdown fences, no commentary:
{"analysis": "2-3 sentences on the broader implications and second-order effects", "confidence": 0.0, "key_points": ["implication 1", "implication 2", "implication 3"]}\
"""

ORCHESTRATOR_SYSTEM = """\
You are a synthesis orchestrator. You receive three independent specialist analyses of
the same news headline: a factual summary, a fact-check assessment, and an implications analysis.

Your job is to write a coordinated synthesis that:
1. Integrates the key points from all three specialists
2. Resolves any contradictions or tensions between them
3. Presents a unified, coherent interpretation in 200–250 words

Write clear professional prose. Do not use bullet points. Do not use section headers.
Do not mention "the three agents" or "the specialists" directly — just synthesise their findings naturally.\
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_json(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


def agent_card(color: str, bg: str, icon: str, label: str) -> None:
    st.markdown(
        f"<div style='border-top:4px solid {color};background:{bg};"
        f"border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
        f"<strong style='color:{color};font-size:0.9em;'>{icon} {label}</strong></div>",
        unsafe_allow_html=True,
    )


PRESET_HEADLINES = [
    "Custom headline — type below",
    "OpenAI announces GPT-5, claiming 10x improvement over GPT-4 on all benchmarks",
    "Federal Reserve raises interest rates by 0.5%, citing persistent inflation",
    "Scientists discover new antibiotic effective against drug-resistant bacteria",
    "European Union passes sweeping AI regulation requiring human oversight of all high-risk systems",
    "Tech layoffs continue: Google cuts 12,000 jobs amid AI investment pivot",
]

AGENTS = [
    ("summarizer",   SUMMARIZER_SYSTEM,   "#1E88E5", "#E3F2FD", "📋", "SUMMARIZER"),
    ("fact_checker", FACT_CHECKER_SYSTEM,  "#E53935", "#FFEBEE", "🔍", "FACT-CHECKER"),
    ("implications", IMPLICATIONS_SYSTEM,  "#FB8C00", "#FFF3E0", "🔮", "IMPLICATIONS"),
]

# ── Section 1 — Architecture Diagram ──────────────────────────────────────────
st.markdown("---")
st.subheader("1 — Flat vs Hierarchical Architecture")

arch_left, arch_right = st.columns(2)

with arch_left:
    st.markdown(
        "<div style='border:2px dashed #90A4AE;border-radius:8px;padding:16px;background:#FAFAFA;'>"
        "<div style='text-align:center;font-weight:bold;color:#546E7A;margin-bottom:12px;'>FLAT SYSTEM — No Coordination</div>",
        unsafe_allow_html=True,
    )
    for _, _, color, bg, icon, label in AGENTS:
        st.markdown(
            f"<div style='border-top:4px solid {color};background:{bg};border-radius:6px;"
            f"padding:8px 12px;margin-bottom:6px;text-align:center;'>"
            f"<strong style='color:{color};font-size:0.85em;'>{icon} [{label}]</strong></div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<div style='text-align:center;font-size:0.78em;color:#90A4AE;margin-top:8px;'>"
        "Three independent outputs — user must reconcile</div></div>",
        unsafe_allow_html=True,
    )

with arch_right:
    st.markdown(
        "<div style='border:2px solid #8E24AA;border-radius:8px;padding:16px;background:#FAFAFA;'>"
        "<div style='text-align:center;font-weight:bold;color:#8E24AA;margin-bottom:12px;'>HIERARCHICAL SYSTEM — Coordination Layer</div>",
        unsafe_allow_html=True,
    )
    for _, _, color, bg, icon, label in AGENTS:
        st.markdown(
            f"<div style='border-top:4px solid {color};background:{bg};border-radius:6px;"
            f"padding:8px 12px;margin-bottom:6px;text-align:center;'>"
            f"<strong style='color:{color};font-size:0.85em;'>{icon} [{label}]</strong></div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<div style='text-align:center;font-size:1.2em;margin:4px 0;'>↓</div>"
        "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;border-radius:6px;"
        "padding:8px 12px;text-align:center;'>"
        "<strong style='color:#8E24AA;font-size:0.85em;'>🎯 [ORCHESTRATOR] — Coordinated Synthesis</strong></div>"
        "<div style='text-align:center;font-size:0.78em;color:#8E24AA;margin-top:8px;'>"
        "One resolved, coherent view</div></div>",
        unsafe_allow_html=True,
    )

with st.expander("See system prompts"):
    tabs = st.tabs(["Summarizer", "Fact-Checker", "Implications", "Orchestrator"])
    for tab, prompt in zip(tabs, [SUMMARIZER_SYSTEM, FACT_CHECKER_SYSTEM, IMPLICATIONS_SYSTEM, ORCHESTRATOR_SYSTEM]):
        with tab:
            st.code(prompt, language="text")

# ── Section 2 — Flat System ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("2 — Flat System: Three Independent Agents")
st.markdown("Three agents receive the same headline simultaneously. They do not see each other's output.")

preset_choice = st.selectbox("Choose a preset headline or write your own:", PRESET_HEADLINES, key="s2_preset")
headline_val = "" if preset_choice == PRESET_HEADLINES[0] else preset_choice
headline = st.text_area("News headline:", value=headline_val, height=70, key="s2_headline",
                         placeholder="Paste or type a news headline here…")

if st.button("▶ Run Flat System", type="primary", disabled=not headline.strip()):
    parsed = {}
    usages = {}
    with st.spinner("Running three independent agents…"):
        for key, system, color, bg, icon, label in AGENTS:
            raw, usage = chat(system, f"News headline: {headline.strip()}", max_tokens=300, temperature=0.4)
            result = parse_json(raw)
            if result is None:
                result = {"analysis": raw, "confidence": 0.5, "key_points": []}
            parsed[key] = result
            usages[key] = usage
    st.session_state["flat_headline"] = headline.strip()
    st.session_state["flat_parsed"] = parsed
    st.session_state["flat_usages"] = usages

if "flat_parsed" in st.session_state:
    parsed = st.session_state["flat_parsed"]
    usages = st.session_state["flat_usages"]
    cols = st.columns(3)
    agent_meta = [
        ("summarizer",   "#1E88E5", "#E3F2FD", "📋", "SUMMARIZER"),
        ("fact_checker", "#E53935", "#FFEBEE", "🔍", "FACT-CHECKER"),
        ("implications", "#FB8C00", "#FFF3E0", "🔮", "IMPLICATIONS"),
    ]
    for col, (key, color, bg, icon, label) in zip(cols, agent_meta):
        with col:
            agent_card(color, bg, icon, f"[{label}]")
            d = parsed.get(key, {})
            st.markdown(d.get("analysis", ""))
            conf = float(d.get("confidence", 0.5))
            st.progress(conf, text=f"Confidence: {conf:.0%}")
            kp = d.get("key_points", [])
            if kp:
                st.markdown("**Key points:**")
                for pt in kp:
                    st.markdown(f"- {pt}")
            u = usages.get(key, {})
            st.caption(f"In: {u.get('input_tokens', 0)} | Out: {u.get('output_tokens', 0)} tokens")

    total_in = sum(u.get("input_tokens", 0) for u in usages.values())
    total_out = sum(u.get("output_tokens", 0) for u in usages.values())
    m1, m2, m3 = st.columns(3)
    m1.metric("LLM calls", 3)
    m2.metric("Total input tokens", total_in)
    m3.metric("Total output tokens", total_out)
    st.info("These three agents operated independently. They may contradict each other. There is no shared view — run Section 3 to see how the orchestrator resolves this.")

# ── Section 3 — Hierarchical System ───────────────────────────────────────────
st.markdown("---")
st.subheader("3 — Hierarchical System: Orchestrated Synthesis")
st.markdown("Using the same three flat agent outputs, the orchestrator reads all three and writes a coordinated synthesis.")

if "flat_parsed" not in st.session_state:
    st.info("Run Section 2 first to populate the flat agent outputs.")
else:
    if st.button("▶ Run Orchestrator Synthesis", type="primary"):
        parsed = st.session_state["flat_parsed"]
        headline_stored = st.session_state["flat_headline"]

        summ = parsed.get("summarizer", {})
        fact = parsed.get("fact_checker", {})
        impl = parsed.get("implications", {})

        orch_user = (
            f"News headline: {headline_stored}\n\n"
            f"[SUMMARIZER] {summ.get('analysis', '')}\n"
            f"Key points: {', '.join(summ.get('key_points', []))}\n\n"
            f"[FACT-CHECKER] {fact.get('analysis', '')}\n"
            f"Key points: {', '.join(fact.get('key_points', []))}\n\n"
            f"[IMPLICATIONS] {impl.get('analysis', '')}\n"
            f"Key points: {', '.join(impl.get('key_points', []))}"
        )

        with st.spinner("Orchestrator synthesising all three outputs…"):
            synthesis, usage = chat(ORCHESTRATOR_SYSTEM, orch_user, max_tokens=500, temperature=0.5)

        st.session_state["hierarchical_synthesis"] = synthesis
        st.session_state["hierarchical_usage"] = usage

    if "hierarchical_synthesis" in st.session_state:
        synthesis = st.session_state["hierarchical_synthesis"]
        usage = st.session_state["hierarchical_usage"]

        st.markdown(
            "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;"
            "border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
            "<strong style='color:#8E24AA;'>🎯 [ORCHESTRATOR] Coordinated Synthesis</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(synthesis)

        st.markdown("**Flat vs Hierarchical — comparison:**")
        cmp_left, cmp_right = st.columns(2)
        with cmp_left:
            st.markdown(
                "<div style='border-top:4px solid #90A4AE;background:#FAFAFA;border-radius:6px;padding:12px;'>"
                "<strong style='color:#546E7A;'>Flat System</strong>"
                "<ul style='margin-top:8px;font-size:0.88em;'>"
                "<li>3 LLM calls</li><li>Outputs are independent</li>"
                "<li>No shared context between agents</li><li>User must reconcile contradictions</li>"
                "</ul></div>",
                unsafe_allow_html=True,
            )
        with cmp_right:
            st.markdown(
                "<div style='border-top:4px solid #8E24AA;background:#F3E5F5;border-radius:6px;padding:12px;'>"
                "<strong style='color:#8E24AA;'>Hierarchical System</strong>"
                "<ul style='margin-top:8px;font-size:0.88em;'>"
                "<li>4 LLM calls (3 + orchestrator)</li><li>Orchestrator resolves contradictions</li>"
                "<li>All outputs feed into one view</li><li>Single coherent result for downstream use</li>"
                "</ul></div>",
                unsafe_allow_html=True,
            )

        m1, m2, m3 = st.columns(3)
        m1.metric("Orchestrator input tokens", usage.get("input_tokens", 0))
        m2.metric("Orchestrator output tokens", usage.get("output_tokens", 0))
        m3.metric("Total LLM calls (full pipeline)", 4)
