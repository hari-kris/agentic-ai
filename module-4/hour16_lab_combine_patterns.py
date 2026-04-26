"""
Hour 16 Lab — Combine Patterns
Module 4 | Core Agentic Patterns I

Capstone lab: a research assistant that uses all four patterns together.
Pipeline: Planning → Tool Use (search) → Prompt Chaining (draft) → Reflection (critique + refine)

Run: streamlit run module-4/hour16_lab_combine_patterns.py
"""

import json
import streamlit as st
from claude_client import chat, chat_with_tools

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 16 — Combine Patterns", page_icon="🧩", layout="wide")
st.title("🧩 Hour 16 — Combine Patterns")
st.caption("Module 4 | Core Agentic Patterns I — Capstone Lab")

st.markdown("""
This lab combines all four patterns from Module 4 into one **Research Assistant** pipeline.

| Pattern | What it does here |
|---------|------------------|
| 📋 Planning | Breaks the research goal into 3 focused sub-questions |
| 🔧 Tool Use | Searches a knowledge base for facts on each sub-question |
| ⛓️ Prompt Chaining | Chains plan + search results → draft |
| 🔁 Reflection | Critiques the draft and produces a final improved report |
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 16 Guide")
    st.markdown("""
**Full pipeline:**
1. **Planner** — 3 sub-questions from your goal
2. **Searcher × 3** — one search per sub-question
3. **Drafter** — full report from plan + facts
4. **Critic** — JSON quality scores
5. **Refiner** — improved final report

**What to observe:**
- How Planning shapes what gets searched
- How Tool Use grounds the draft in retrieved facts
- How Chaining transforms plan + facts → narrative
- How Reflection catches issues the Drafter missed
- The total token cost of combining all four patterns
""")
    st.divider()
    st.markdown("**Experiment ideas:**")
    st.markdown("- Try a topic NOT in the knowledge base — how does the draft change?")
    st.markdown("- Compare the draft vs the refined report — what changed?")
    st.markdown("- Count how many LLM calls the full pipeline makes")
    st.divider()
    st.info("**Key principle:** Patterns compose. Each one solves a specific quality problem. Together they produce output that no single call can match.")

# ── Knowledge Base ─────────────────────────────────────────────────────────────
KNOWLEDGE_BASE = [
    {"id": "KB-001", "title": "Remote work productivity research", "content": "A 2021 Stanford study found remote workers are 13% more productive than office workers, primarily due to fewer interruptions and no commute time. However, a 2023 Microsoft study found collaboration and spontaneous innovation declined when teams went fully remote."},
    {"id": "KB-002", "title": "Remote work mental health", "content": "Remote work reduces commute stress and offers schedule flexibility, but 27% of remote workers report loneliness as a significant challenge (Buffer 2023). Isolation and lack of clear work-life boundaries are the top two wellbeing concerns."},
    {"id": "KB-003", "title": "Remote work infrastructure costs", "content": "Companies save an average of $11,000 per remote employee per year in real estate and overhead. Employees save $2,000–$4,000 annually by eliminating commuting costs. However, companies spend 30–40% more on IT security when staff work from home."},
    {"id": "KB-004", "title": "Electric vehicles — how they work", "content": "Battery electric vehicles (BEVs) use lithium-ion battery packs to store energy. An electric motor converts electrical energy to mechanical energy via electromagnetic induction. Regenerative braking captures kinetic energy when decelerating and converts it back to electricity."},
    {"id": "KB-005", "title": "EV range and charging", "content": "Modern EVs average 250–400 miles per charge. DC fast chargers can charge to 80% in 20–40 minutes. Level 2 home chargers take 6–12 hours for a full charge. Tesla Superchargers deliver up to 250 kW. Charging infrastructure coverage in the UK has grown 45% since 2021."},
    {"id": "KB-006", "title": "EV environmental impact", "content": "EVs produce zero direct emissions but manufacturing the battery pack generates 70–80% more CO₂ than making a petrol car. However, over a vehicle's lifetime, an EV emits 50–70% fewer total greenhouse gases, depending on the electricity grid's carbon intensity."},
    {"id": "KB-007", "title": "Internet history — origins", "content": "ARPANET, funded by the US Department of Defense, went live in 1969 with 4 nodes. The TCP/IP protocol, standardised in 1983, enabled different networks to communicate. Tim Berners-Lee invented the World Wide Web in 1989 as a hypertext system for CERN researchers."},
    {"id": "KB-008", "title": "Internet infrastructure", "content": "The internet backbone consists of high-bandwidth fibre optic cables, including 400+ submarine cables carrying 95% of international internet traffic. Data passes through routers that use the Border Gateway Protocol (BGP) to find the fastest path between networks."},
    {"id": "KB-009", "title": "Internet scale statistics", "content": "As of 2024, 5.4 billion people (67% of the world's population) use the internet. Global internet traffic exceeds 600 exabytes per month. Google processes approximately 8.5 billion searches per day. About 350 million emails are sent every minute."},
    {"id": "KB-010", "title": "AI history and milestones", "content": "The term 'artificial intelligence' was coined by John McCarthy in 1956 at the Dartmouth Conference. Deep learning breakthroughs arrived in 2012 when AlexNet won ImageNet. GPT-3 (2020) demonstrated emergent few-shot learning. ChatGPT (2022) reached 100 million users in 2 months, the fastest consumer app adoption in history."},
    {"id": "KB-011", "title": "Large language models", "content": "Large language models (LLMs) are transformer-based neural networks trained on vast text corpora using self-supervised learning. GPT-4 has an estimated 1.8 trillion parameters. LLMs generate text by predicting the next token given a context window. Context windows now range from 32k to 2M tokens."},
    {"id": "KB-012", "title": "AI economic impact", "content": "McKinsey Global Institute estimates AI could add $13–22 trillion to the global economy annually by 2030. Goldman Sachs estimates generative AI could automate 25% of work tasks in advanced economies. AI investment reached $91.9 billion globally in 2022, a 2.5x increase from 2020."},
]


def search_knowledge(query: str, max_results: int = 3) -> str:
    query_lower = query.lower()
    scored = []
    for item in KNOWLEDGE_BASE:
        score = 0
        text = (item["title"] + " " + item["content"]).lower()
        for word in query_lower.split():
            if len(word) > 2 and word in text:
                score += 1
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_results]
    if not top:
        return "No relevant results found in the knowledge base."
    return "\n\n".join(f"[{i['id']}] {i['title']}\n{i['content']}" for _, i in top)


SEARCH_TOOL = {
    "name": "search_knowledge",
    "description": "Search the research knowledge base for facts on a topic. Use this to find statistics, definitions, and evidence to support the research report.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keywords or a question describing the topic to search."},
            "max_results": {"type": "integer", "description": "Max number of results. Default 3.", "default": 3},
        },
        "required": ["query"],
    },
}

TOOL_REGISTRY = {"search_knowledge": lambda **kw: search_knowledge(kw["query"], kw.get("max_results", 3))}

# ── System Prompts ─────────────────────────────────────────────────────────────
PLANNER_SYSTEM = """\
You are a research planning agent. Given a research goal, decompose it into exactly 3
focused sub-questions that together cover the topic fully.

Each sub-question should address a distinct aspect of the topic — no overlap.
Sub-questions should be specific enough to guide a targeted search.

Return ONLY valid JSON:
{"sub_questions": ["...", "...", "..."], "rationale": "one sentence"}\
"""

SEARCHER_SYSTEM = """\
You are a research retrieval agent. Given a sub-question, use the search_knowledge tool
to find relevant facts from the knowledge base.
After receiving the search results, summarise the most relevant information in 2–3 sentences.
Be factual — only include information from the search results.\
"""

DRAFTER_SYSTEM = """\
You are a professional research writer. Given a research goal, a set of 3 sub-questions,
and the facts gathered for each, write a coherent 3-paragraph research summary.

Each paragraph should address one sub-question using the facts provided.
Use precise language. Do not invent statistics.
Do not add a title — start with the first paragraph.\
"""

CRITIC_SYSTEM = """\
You are a research quality evaluator. Score the provided research summary on four criteria
from 1 to 5:
- factual_accuracy (1=guesses/inventions, 5=all claims supported by evidence)
- coverage (1=major gaps, 5=all three aspects thoroughly addressed)
- clarity (1=hard to follow, 5=clear and well-structured)
- depth (1=surface-level, 5=specific details and evidence throughout)

Return ONLY valid JSON:
{"factual_accuracy": N, "coverage": N, "clarity": N, "depth": N, "feedback": "one specific improvement"}\
"""

REFINER_SYSTEM = """\
You are a professional editor improving a research summary.
You receive the original summary, a critique with scores, and specific feedback.
Rewrite the summary to address the feedback. Keep the 3-paragraph structure.
Do not add a title. Do not add commentary — just the improved text.\
"""


def run_search_agent(sub_question: str) -> tuple[str, int, int]:
    """Run one search agent for a sub-question. Returns (facts_summary, in_tokens, out_tokens)."""
    messages = [{"role": "user", "content": f"Sub-question: {sub_question}\n\nSearch for relevant facts and summarise them."}]
    total_in, total_out = 0, 0

    for _ in range(3):
        blocks, usage = chat_with_tools(SEARCHER_SYSTEM, messages, [SEARCH_TOOL], max_tokens=500)
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]

        tool_calls = [b for b in blocks if b["type"] == "tool_use"]
        text_blocks = [b for b in blocks if b["type"] == "text"]

        if not tool_calls:
            return text_blocks[0]["text"] if text_blocks else "", total_in, total_out

        assistant_content = []
        for b in blocks:
            if b["type"] == "text":
                assistant_content.append({"type": "text", "text": b["text"]})
            elif b["type"] == "tool_use":
                assistant_content.append({"type": "tool_use", "id": b["id"], "name": b["name"], "input": b["input"]})
        messages.append({"role": "assistant", "content": assistant_content})

        tool_results = []
        for tc in tool_calls:
            fn = TOOL_REGISTRY.get(tc["name"])
            result = fn(**tc["input"]) if fn else f"Unknown tool: {tc['name']}"
            tool_results.append({"type": "tool_result", "tool_use_id": tc["id"], "content": result})
        messages.append({"role": "user", "content": tool_results})

    return "", total_in, total_out


# ── Section 1: Architecture ────────────────────────────────────────────────────
st.divider()
st.subheader("1 — Research Assistant Architecture")

arch_html = """
<div style='background:#FAFAFA;border:1px solid #E0E0E0;border-radius:8px;padding:20px;font-family:monospace;font-size:0.85em;line-height:1.9;'>
<span style='color:#888;'>User research goal</span><br>
<span style='color:#888;'>        │</span><br>
<span style='color:#888;'>        ▼</span><br>
<span style='background:#F3E5F5;color:#8E24AA;padding:2px 8px;border-radius:4px;'>📋 [PLANNER]</span>
<span style='color:#888;'> ─── 3 sub-questions ──────────────────────────────────────────────┐</span><br>
<span style='color:#888;'>        │                                                              │</span><br>
<span style='color:#888;'>        ▼                                                              │</span><br>
<span style='background:#FFF3E0;color:#FB8C00;padding:2px 8px;border-radius:4px;'>🔧 [SEARCHER ×3]</span>
<span style='color:#888;'> (Tool Use) ─── facts per sub-question ──────────────────┐      │</span><br>
<span style='color:#888;'>        │                                                  │      │</span><br>
<span style='color:#888;'>        ▼                                                  ▼      ▼</span><br>
<span style='background:#E3F2FD;color:#1E88E5;padding:2px 8px;border-radius:4px;'>✍️ [DRAFTER]</span>
<span style='color:#888;'> (Chaining: plan + facts → draft) ─── draft ──────────────────────►</span><br>
<span style='color:#888;'>        │                                                              │</span><br>
<span style='color:#888;'>        ▼                                                              │</span><br>
<span style='background:#FFEBEE;color:#E53935;padding:2px 8px;border-radius:4px;'>🔍 [CRITIC]</span>
<span style='color:#888;'> (Reflection) ─── JSON critique ──────────────────────────────────►</span><br>
<span style='color:#888;'>        │</span><br>
<span style='color:#888;'>        ▼</span><br>
<span style='background:#F3E5F5;color:#8E24AA;padding:2px 8px;border-radius:4px;'>✨ [REFINER]</span>
<span style='color:#888;'> ─── final report</span>
</div>
"""
st.markdown(arch_html, unsafe_allow_html=True)

pattern_cols = st.columns(4)
patterns = [
    ("📋", "Planning", "#8E24AA", "#F3E5F5", "Planner breaks goal into 3 sub-questions"),
    ("🔧", "Tool Use", "#FB8C00", "#FFF3E0", "Searchers retrieve facts via tool calls"),
    ("⛓️", "Chaining", "#1E88E5", "#E3F2FD", "Facts + plan feed Drafter sequentially"),
    ("🔁", "Reflection", "#E53935", "#FFEBEE", "Critic scores; Refiner improves the draft"),
]
for col, (icon, name, color, bg, desc) in zip(pattern_cols, patterns):
    with col:
        st.markdown(
            f"<div style='border-top:3px solid {color};background:{bg};"
            f"border-radius:6px;padding:10px;text-align:center;min-height:100px;'>"
            f"<div style='font-size:1.5em;'>{icon}</div>"
            f"<div style='font-weight:bold;color:{color};font-size:0.88em;'>{name}</div>"
            f"<div style='font-size:0.78em;color:#555;margin-top:4px;'>{desc}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ── Section 2: Run the Pipeline ────────────────────────────────────────────────
st.divider()
st.subheader("2 — Run the Research Assistant")

RESEARCH_PRESETS = [
    "Custom goal — type below",
    "The impact of remote work on productivity and wellbeing",
    "How electric vehicles work and their environmental impact",
    "The history of the internet and how it functions today",
    "The rise of artificial intelligence and its economic implications",
]

sel = st.selectbox("Pick a research goal or write your own:", RESEARCH_PRESETS, key="ra_preset")
research_goal = st.text_area(
    "Research goal:",
    value="" if sel == RESEARCH_PRESETS[0] else sel,
    placeholder="e.g. The state of renewable energy and its challenges",
    height=70,
    key="ra_goal",
)

if st.button("▶ Run Research Assistant", type="primary", disabled=not research_goal.strip()):
    pipeline_results = {}
    token_ledger = {}
    total_in, total_out = 0, 0

    # Stage 1: Planning
    progress = st.progress(0, text="📋 Planning — breaking goal into sub-questions…")
    with st.spinner("Planner working…"):
        raw_plan, u_plan = chat(PLANNER_SYSTEM, f"Research goal: {research_goal.strip()}", max_tokens=300, temperature=0.2)
    total_in += u_plan["input_tokens"]
    total_out += u_plan["output_tokens"]
    token_ledger["planner"] = u_plan

    try:
        clean = raw_plan.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        plan_data = json.loads(clean)
        sub_questions = plan_data.get("sub_questions", [])
    except json.JSONDecodeError:
        st.error("Planner returned unexpected output:")
        st.code(raw_plan)
        st.stop()

    pipeline_results["plan"] = plan_data
    progress.progress(15, text="🔧 Tool Use — searching knowledge base for each sub-question…")

    # Stage 2: Tool Use (one search agent per sub-question)
    search_results = []
    token_ledger["searchers"] = []
    for i, sq in enumerate(sub_questions[:3]):
        with st.spinner(f"Searcher {i + 1}/3: {sq[:60]}…"):
            facts, si, so = run_search_agent(sq)
        search_results.append({"sub_question": sq, "facts": facts})
        token_ledger["searchers"].append({"input_tokens": si, "output_tokens": so})
        total_in += si
        total_out += so
    pipeline_results["search"] = search_results
    progress.progress(50, text="⛓️ Chaining — Drafter composing report from plan + facts…")

    # Stage 3: Prompt Chaining — Drafter
    facts_block = "\n\n".join(
        f"Sub-question {i + 1}: {r['sub_question']}\nFacts found:\n{r['facts']}"
        for i, r in enumerate(search_results)
    )
    drafter_user = (
        f"Research goal: {research_goal.strip()}\n\n"
        f"Sub-questions:\n" + "\n".join(f"{i+1}. {sq}" for i, sq in enumerate(sub_questions[:3])) +
        f"\n\nFacts gathered:\n{facts_block}\n\n"
        "Write the 3-paragraph research summary."
    )
    with st.spinner("Drafter writing…"):
        draft, u_draft = chat(DRAFTER_SYSTEM, drafter_user, max_tokens=800, temperature=0.6)
    total_in += u_draft["input_tokens"]
    total_out += u_draft["output_tokens"]
    token_ledger["drafter"] = u_draft
    pipeline_results["draft"] = draft
    progress.progress(70, text="🔁 Reflection — Critic scoring the draft…")

    # Stage 4: Reflection — Critic
    with st.spinner("Critic evaluating draft…"):
        raw_crit, u_crit = chat(CRITIC_SYSTEM, f"Research summary:\n\n{draft}", max_tokens=300, temperature=0.2)
    total_in += u_crit["input_tokens"]
    total_out += u_crit["output_tokens"]
    token_ledger["critic"] = u_crit

    try:
        clean = raw_crit.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        critique = json.loads(clean)
    except json.JSONDecodeError:
        critique = {"factual_accuracy": 3, "coverage": 3, "clarity": 3, "depth": 3, "feedback": "Unable to parse critique."}
    pipeline_results["critique"] = critique
    progress.progress(85, text="🔁 Reflection — Refiner improving the draft…")

    # Stage 5: Reflection — Refiner
    refiner_user = (
        f"Original research summary:\n{draft}\n\n"
        f"Quality scores:\n"
        f"  Factual accuracy: {critique.get('factual_accuracy')}/5\n"
        f"  Coverage: {critique.get('coverage')}/5\n"
        f"  Clarity: {critique.get('clarity')}/5\n"
        f"  Depth: {critique.get('depth')}/5\n"
        f"  Feedback: {critique.get('feedback')}\n\n"
        "Rewrite the summary to address the feedback."
    )
    with st.spinner("Refiner improving…"):
        final_report, u_refine = chat(REFINER_SYSTEM, refiner_user, max_tokens=900, temperature=0.5)
    total_in += u_refine["input_tokens"]
    total_out += u_refine["output_tokens"]
    token_ledger["refiner"] = u_refine
    pipeline_results["final"] = final_report
    progress.progress(100, text="Pipeline complete.")

    st.session_state["ra_results"] = pipeline_results
    st.session_state["ra_ledger"] = token_ledger
    st.session_state["ra_totals"] = (total_in, total_out)

# ── Section 3: Stage-by-Stage Results ─────────────────────────────────────────
if "ra_results" in st.session_state:
    results = st.session_state["ra_results"]
    ledger = st.session_state["ra_ledger"]
    total_in, total_out = st.session_state["ra_totals"]

    st.divider()
    st.subheader("3 — Stage-by-Stage Results")

    tab_plan, tab_search, tab_draft, tab_crit, tab_final = st.tabs(
        ["📋 Plan", "🔧 Search Results", "✍️ Draft", "🔍 Critique", "✨ Final Report"]
    )

    with tab_plan:
        plan_data = results.get("plan", {})
        st.markdown("**3 sub-questions generated by the Planner:**")
        for i, sq in enumerate(plan_data.get("sub_questions", []), 1):
            st.markdown(
                f"<div style='border-left:4px solid #8E24AA;background:#F3E5F5;"
                f"padding:8px 14px;margin:6px 0;border-radius:4px;'>"
                f"<strong style='color:#8E24AA;'>Q{i}:</strong> {sq}</div>",
                unsafe_allow_html=True,
            )
        st.caption(f"Rationale: {plan_data.get('rationale', '')}")
        u = ledger.get("planner", {})
        st.metric("Planner tokens (in / out)", f"{u.get('input_tokens', 0)} / {u.get('output_tokens', 0)}")

    with tab_search:
        for i, sr in enumerate(results.get("search", []), 1):
            with st.expander(f"Sub-question {i}: {sr['sub_question'][:60]}…", expanded=(i == 1)):
                st.markdown(
                    f"<div style='border-left:4px solid #FB8C00;padding:8px 12px;'>"
                    f"<strong style='color:#FB8C00;'>🔧 Facts retrieved:</strong></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(sr["facts"])
                if i <= len(ledger.get("searchers", [])):
                    su = ledger["searchers"][i - 1]
                    st.caption(f"Searcher {i} tokens: {su.get('input_tokens', 0)} in / {su.get('output_tokens', 0)} out")

    with tab_draft:
        st.markdown(
            "<div style='border-left:4px solid #1E88E5;padding:4px 10px;margin-bottom:8px;'>"
            "<strong style='color:#1E88E5;'>✍️ [DRAFTER] — Initial Report</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(results.get("draft", ""))
        u = ledger.get("drafter", {})
        st.caption(f"Drafter tokens: {u.get('input_tokens', 0)} in / {u.get('output_tokens', 0)} out")

    with tab_crit:
        critique = results.get("critique", {})
        st.markdown(
            "<div style='border-left:4px solid #E53935;padding:4px 10px;margin-bottom:8px;'>"
            "<strong style='color:#E53935;'>🔍 [CRITIC] Scores</strong></div>",
            unsafe_allow_html=True,
        )
        crit_cols = st.columns(4)
        crit_keys = [
            ("factual_accuracy", "Factual Accuracy"),
            ("coverage", "Coverage"),
            ("clarity", "Clarity"),
            ("depth", "Depth"),
        ]
        for col, (key, label) in zip(crit_cols, crit_keys):
            score = critique.get(key, 0)
            col.metric(label, f"{score}/5")
            col.progress(score / 5)
        st.info(f"**Feedback:** {critique.get('feedback', '')}")
        u = ledger.get("critic", {})
        st.caption(f"Critic tokens: {u.get('input_tokens', 0)} in / {u.get('output_tokens', 0)} out")

    with tab_final:
        st.markdown(
            "<div style='border-left:4px solid #8E24AA;padding:4px 10px;margin-bottom:8px;'>"
            "<strong style='color:#8E24AA;'>✨ [REFINER] — Final Report</strong></div>",
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown(results.get("final", ""))
        u = ledger.get("refiner", {})
        st.caption(f"Refiner tokens: {u.get('input_tokens', 0)} in / {u.get('output_tokens', 0)} out")

    # ── Section 4: Pattern Attribution ─────────────────────────────────────────
    st.divider()
    st.subheader("4 — Pattern Attribution")

    st.markdown("Each part of this pipeline is driven by one of the four Module 4 patterns.")

    attr_data = [
        ("📋 Planning", "#8E24AA", "#F3E5F5", "Planner", "Broke the research goal into 3 focused sub-questions. Without this, the search would be unfocused."),
        ("🔧 Tool Use", "#FB8C00", "#FFF3E0", "Searcher ×3", "Each sub-question triggered a search tool call. The Drafter's facts came from retrieval, not Claude's training data."),
        ("⛓️ Prompt Chaining", "#1E88E5", "#E3F2FD", "Drafter", "Received the plan AND the search results as chained input. Two prior outputs combined into one new output."),
        ("🔁 Reflection", "#E53935", "#FFEBEE", "Critic + Refiner", "Critic scored the draft on 4 criteria. Refiner used the feedback to produce the improved final report."),
    ]

    for icon_label, color, bg, agent, explanation in attr_data:
        st.markdown(
            f"<div style='border-left:4px solid {color};background:{bg};"
            f"padding:10px 16px;border-radius:4px;margin:8px 0;'>"
            f"<strong style='color:{color};'>{icon_label}</strong> — "
            f"<em>{agent}</em><br>"
            f"<span style='font-size:0.9em;color:#444;'>{explanation}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Section 5: Token Ledger ─────────────────────────────────────────────────
    st.divider()
    st.subheader("5 — Token Ledger")

    searcher_in = sum(s.get("input_tokens", 0) for s in ledger.get("searchers", []))
    searcher_out = sum(s.get("output_tokens", 0) for s in ledger.get("searchers", []))

    ledger_rows = [
        ("📋 Planner", ledger.get("planner", {}).get("input_tokens", 0), ledger.get("planner", {}).get("output_tokens", 0), "Planning"),
        ("🔧 Searchers (×3)", searcher_in, searcher_out, "Tool Use"),
        ("✍️ Drafter", ledger.get("drafter", {}).get("input_tokens", 0), ledger.get("drafter", {}).get("output_tokens", 0), "Prompt Chaining"),
        ("🔍 Critic", ledger.get("critic", {}).get("input_tokens", 0), ledger.get("critic", {}).get("output_tokens", 0), "Reflection"),
        ("✨ Refiner", ledger.get("refiner", {}).get("input_tokens", 0), ledger.get("refiner", {}).get("output_tokens", 0), "Reflection"),
    ]

    for agent, tin, tout, pattern in ledger_rows:
        lc1, lc2, lc3, lc4 = st.columns([3, 2, 2, 2])
        lc1.markdown(f"**{agent}**")
        lc2.metric("Input tokens", tin)
        lc3.metric("Output tokens", tout)
        lc4.caption(pattern)

    st.divider()
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Total LLM calls", 5 + len(results.get("search", [])))
    tc2.metric("Total input tokens", total_in)
    tc3.metric("Total output tokens", total_out)
    st.caption("The Searchers each make 2 calls (initial + tool result), so the true call count is higher than 5.")
