"""
Web Research Agent with LLM Observability
llm-proxy-logging/web_research_agent.py

A web research agent that routes all Claude API calls through Requesty.ai,
surfacing per-call latency, token costs, and proxy status in the UI.

Run: streamlit run llm-proxy-logging/web_research_agent.py
"""

import json
import re
import time
import xml.etree.ElementTree as ET

import requests
import streamlit as st
import wikipedia as wiki_lib

from claude_client import chat_with_tools, REQUESTY_ACTIVE, MODEL

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Web Research Agent + LLM Observability", page_icon="📡", layout="wide")
st.title("📡 Web Research Agent")
st.caption("with Requesty.ai LLM Observability")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Observability Status")

    if REQUESTY_ACTIVE:
        st.markdown(
            "<div style='background:#FFF3E0;border:2px solid #FB8C00;padding:10px 14px;"
            "border-radius:8px;'>"
            "<strong style='color:#FB8C00;font-size:1.05em;'>📡 Routed via Requesty.ai</strong><br><br>"
            "Every Claude call is logged to your dashboard — "
            "traces, token costs, latency, and model usage.<br><br>"
            "<a href='https://app.requesty.ai' target='_blank'>"
            "→ Open Requesty Dashboard</a>"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='background:#F5F5F5;border:1px solid #BDBDBD;padding:10px 14px;"
            "border-radius:8px;color:#616161;'>"
            "🔌 <strong>Direct to Anthropic</strong><br><br>"
            "Latency is tracked locally in this UI, but calls are not "
            "logged to an external dashboard.<br><br>"
            "<em>To enable full observability, add<br>"
            "<code>REQUESTY_API_KEY=rq-...</code><br>"
            "to <code>llm-proxy-logging/.env</code> and restart.</em>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.header("What Requesty captures")
    st.markdown("""
- Full request & response trace
- Per-call latency
- Input + output token counts
- Cost breakdown by model
- Spend analytics (by day / user)
- Optional PII redaction
""")

    st.divider()
    st.header("How it works")
    st.markdown("""
One change in `claude_client.py`:

```python
anthropic.Anthropic(
    api_key=REQUESTY_API_KEY,
    base_url="https://router.requesty.ai/anthropic",
)
```

Requesty proxies the request to
Anthropic, logs the trace, and
returns the response unchanged.
""")

    st.divider()
    st.markdown(f"**Model:** `{MODEL}`")

# ── Source colour palette ──────────────────────────────────────────────────────
SOURCE_STYLES = {
    "search_wikipedia":  {"color": "#1E88E5", "label": "Wikipedia",   "icon": "📖"},
    "search_arxiv":      {"color": "#8E24AA", "label": "arXiv",       "icon": "🎓"},
    "search_hackernews": {"color": "#FB8C00", "label": "Hacker News", "icon": "💬"},
    "search_duckduckgo": {"color": "#43A047", "label": "DuckDuckGo",  "icon": "🔍"},
}

# ── Tool implementations ───────────────────────────────────────────────────────

def search_wikipedia(query: str, sentences: int = 4) -> str:
    try:
        results = wiki_lib.search(query, results=3)
        if not results:
            return f"No Wikipedia articles found for '{query}'."
        for title in results:
            try:
                summary = wiki_lib.summary(title, sentences=sentences, auto_suggest=False)
                url = wiki_lib.page(title, auto_suggest=False).url
                return f"[Wikipedia — {title}]\nURL: {url}\n\n{summary}"
            except (wiki_lib.exceptions.DisambiguationError, wiki_lib.exceptions.PageError):
                continue
        return f"No usable Wikipedia page found for '{query}'."
    except Exception as exc:
        return f"Wikipedia search error: {exc}"


def search_arxiv(query: str, max_results: int = 3) -> str:
    try:
        safe_query = re.sub(r"[^\w\s]", " ", query)
        url = (
            f"https://export.arxiv.org/api/query"
            f"?search_query=all:{requests.utils.quote(safe_query)}"
            f"&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(resp.text)
        entries = root.findall("atom:entry", ns)
        if not entries:
            return f"No arXiv papers found for '{query}'."
        papers = []
        for entry in entries:
            title   = (entry.findtext("atom:title",   "", ns) or "").strip().replace("\n", " ")
            summary = (entry.findtext("atom:summary", "", ns) or "").strip().replace("\n", " ")[:300]
            link    = (entry.findtext("atom:id",      "", ns) or "").strip()
            papers.append(f"• {title}\n  {link}\n  {summary}…")
        return f"[arXiv — top {len(papers)} papers for '{query}']\n\n" + "\n\n".join(papers)
    except Exception as exc:
        return f"arXiv search error: {exc}"


def search_hackernews(query: str, max_results: int = 4) -> str:
    try:
        url = (
            f"https://hn.algolia.com/api/v1/search"
            f"?query={requests.utils.quote(query)}&tags=story&hitsPerPage={max_results}"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        if not hits:
            return f"No Hacker News discussions found for '{query}'."
        items = []
        for h in hits:
            title    = h.get("title", "Untitled")
            points   = h.get("points", 0)
            comments = h.get("num_comments", 0)
            hn_url   = f"https://news.ycombinator.com/item?id={h.get('objectID','')}"
            items.append(f"• {title}  [{points} pts, {comments} comments]\n  {hn_url}")
        return f"[Hacker News — top {len(items)} stories for '{query}']\n\n" + "\n\n".join(items)
    except Exception as exc:
        return f"Hacker News search error: {exc}"


def search_duckduckgo(query: str) -> str:
    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        parts = []
        abstract = data.get("AbstractText", "").strip()
        if abstract:
            parts.append(f"Abstract: {abstract[:500]}")
            parts.append(f"Source: {data.get('AbstractURL', '')}")
        related = data.get("RelatedTopics", [])[:4]
        if related:
            topics = [f"  – {t.get('Text','')[:120]}" for t in related if t.get("Text")]
            if topics:
                parts.append("Related topics:\n" + "\n".join(topics))
        if not parts:
            return f"DuckDuckGo returned no instant-answer data for '{query}'."
        return f"[DuckDuckGo Instant Answer — '{query}']\n\n" + "\n\n".join(parts)
    except Exception as exc:
        return f"DuckDuckGo search error: {exc}"


# ── Tool schemas ───────────────────────────────────────────────────────────────
ALL_TOOLS = [
    {
        "name": "search_wikipedia",
        "description": (
            "Search Wikipedia for factual background, definitions, history, and encyclopaedic "
            "overviews. Best for foundational concepts, historical events, established science."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":     {"type": "string",  "description": "Topic to look up on Wikipedia."},
                "sentences": {"type": "integer", "description": "Summary sentences to return (default 4).", "default": 4},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_arxiv",
        "description": (
            "Search arXiv for peer-reviewed papers and preprints. Best for AI/ML research, "
            "physics, maths, computer science, and any topic with active academic literature."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string",  "description": "Research topic keywords."},
                "max_results": {"type": "integer", "description": "Max papers to return (default 3).", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_hackernews",
        "description": (
            "Search Hacker News for tech community discussions and practitioner opinions. "
            "Best for software engineering, tools, startup trends, developer experience."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string",  "description": "Topic to search in HN stories."},
                "max_results": {"type": "integer", "description": "Max stories to return (default 4).", "default": 4},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_duckduckgo",
        "description": (
            "Search the web via DuckDuckGo Instant Answers for general current information. "
            "Best for recent events, practical guides, and broad current-web perspective."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Web search query."},
            },
            "required": ["query"],
        },
    },
]

TOOL_REGISTRY = {
    "search_wikipedia":  lambda **kw: search_wikipedia(kw["query"], kw.get("sentences", 4)),
    "search_arxiv":      lambda **kw: search_arxiv(kw["query"], kw.get("max_results", 3)),
    "search_hackernews": lambda **kw: search_hackernews(kw["query"], kw.get("max_results", 4)),
    "search_duckduckgo": lambda **kw: search_duckduckgo(kw["query"]),
}

# ── System prompt ──────────────────────────────────────────────────────────────
RESEARCH_SYSTEM = """\
You are a web research agent. Your goal is to produce a thorough, accurate summary of \
any topic by searching multiple real internet sources before answering.

Source selection strategy:
- search_wikipedia  → foundational background, definitions, history, established facts
- search_arxiv      → academic papers, cutting-edge science, AI/ML, technical research
- search_hackernews → practitioner discussions, industry opinions, software/tech trends
- search_duckduckgo → general current web, practical guides, recent events, product info

Rules:
1. Make at least 2 searches across DIFFERENT sources before synthesising.
2. Choose sources that match the topic type.
3. After gathering results, write a structured summary:
   - **Overview** (2–3 sentences)
   - **Key findings** (one bullet per source used)
   - **Sources consulted** (each tool + URL returned)
4. Be objective and cite which source provided which information.\
"""


# ── Agent run + trace data ─────────────────────────────────────────────────────

def run_research_agent(topic: str):
    """Run the research agent loop.

    Returns:
        summary        — final synthesised text
        messages       — full conversation history
        all_blocks     — all content blocks from every round
        round_metrics  — list of per-round dicts: {round, input_tokens, output_tokens, latency_ms}
    """
    messages = [{"role": "user", "content": f"Research this topic thoroughly: {topic}"}]
    all_blocks: list = []
    round_metrics: list[dict] = []
    final_answer = ""

    for round_num in range(8):
        blocks, usage = chat_with_tools(RESEARCH_SYSTEM, messages, ALL_TOOLS, max_tokens=1500)

        round_metrics.append({
            "round":         round_num + 1,
            "input_tokens":  usage["input_tokens"],
            "output_tokens": usage["output_tokens"],
            "latency_ms":    usage["latency_ms"],
        })
        all_blocks.extend(blocks)

        tool_calls  = [b for b in blocks if b["type"] == "tool_use"]
        text_blocks = [b for b in blocks if b["type"] == "text"]

        if not tool_calls:
            final_answer = text_blocks[0]["text"] if text_blocks else ""
            break

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

    return final_answer, messages, all_blocks, round_metrics


# ── Render helpers ─────────────────────────────────────────────────────────────

def _card(bg: str, border: str, header_html: str, body_html: str = "") -> str:
    return (
        f"<div style='background:{bg};border-left:4px solid {border};"
        f"padding:8px 12px;border-radius:4px;margin:6px 0;'>"
        f"{header_html}"
        f"{'<br>' + body_html if body_html else ''}"
        f"</div>"
    )


def render_research_trace(messages: list, all_blocks: list, round_metrics: list) -> list:
    """Render the colour-coded research trace. Returns list of source names used."""
    st.markdown("### Research trace")
    sources_used: list[str] = []

    # Round-by-round observability timeline
    if round_metrics:
        st.markdown("#### Per-round API call metrics")
        header_cols = st.columns([1, 2, 2, 2, 2])
        header_cols[0].markdown("**Round**")
        header_cols[1].markdown("**In tokens**")
        header_cols[2].markdown("**Out tokens**")
        header_cols[3].markdown("**Latency**")
        header_cols[4].markdown("**Proxy**")
        for rm in round_metrics:
            cols = st.columns([1, 2, 2, 2, 2])
            cols[0].markdown(f"#{rm['round']}")
            cols[1].markdown(f"`{rm['input_tokens']:,}`")
            cols[2].markdown(f"`{rm['output_tokens']:,}`")
            cols[3].markdown(f"`{rm['latency_ms']:,} ms`")
            cols[4].markdown("📡 Requesty" if REQUESTY_ACTIVE else "🔌 Direct")

    st.markdown("#### Agent trace")
    with st.container(border=True):
        for block in all_blocks:
            if block["type"] == "text" and block["text"].strip():
                st.markdown(
                    _card(
                        "#E3F2FD", "#1E88E5",
                        "<strong style='color:#1E88E5;'>🤖 Agent thinking</strong>",
                        f"<span style='font-size:0.9em;'>{block['text']}</span>",
                    ),
                    unsafe_allow_html=True,
                )
            elif block["type"] == "tool_use":
                style = SOURCE_STYLES.get(block["name"], {"color": "#555", "label": block["name"], "icon": "🔎"})
                sources_used.append(block["name"])
                query_display = block["input"].get("query", json.dumps(block["input"]))
                st.markdown(
                    _card(
                        "#FAFAFA", style["color"],
                        f"<strong style='color:{style['color']};'>{style['icon']} Searching {style['label']}</strong>",
                        f"<code style='font-size:0.85em;'>query: \"{query_display}\"</code>",
                    ),
                    unsafe_allow_html=True,
                )

        for msg in messages:
            if msg.get("role") == "user":
                for content in msg.get("content", []):
                    if isinstance(content, dict) and content.get("type") == "tool_result":
                        preview = (content.get("content", "") or "")[:600].replace("\n", "<br>")
                        st.markdown(
                            _card(
                                "#F1F8E9", "#43A047",
                                "<strong style='color:#43A047;'>✅ Result received</strong>",
                                f"<span style='font-size:0.82em;'>{preview}…</span>",
                            ),
                            unsafe_allow_html=True,
                        )

    if sources_used:
        unique_sources = list(dict.fromkeys(sources_used))
        badges = " ".join(
            f"<span style='background:{SOURCE_STYLES[s]['color']};color:white;"
            f"padding:3px 10px;border-radius:12px;font-size:0.82em;margin:2px;'>"
            f"{SOURCE_STYLES[s]['icon']} {SOURCE_STYLES[s]['label']}</span>"
            for s in unique_sources
        )
        st.markdown(
            f"<div style='margin:10px 0;'><strong>Sources consulted:</strong> {badges}</div>",
            unsafe_allow_html=True,
        )

    return sources_used


# ── Section 1: Research a Topic ────────────────────────────────────────────────
st.divider()
st.subheader("Research a Topic")

TOPIC_PRESETS = [
    "Custom topic — type below",
    "Quantum computing",
    "Transformer neural networks",
    "Remote work productivity",
    "History of the internet",
    "Python performance optimisation",
    "Large language model hallucinations",
    "Renewable energy storage",
]

sel = st.selectbox("Choose a preset or enter your own:", TOPIC_PRESETS, key="topic_preset")
topic_input = st.text_input(
    "Research topic:",
    value="" if sel == TOPIC_PRESETS[0] else sel,
    placeholder="e.g. Quantum computing, Remote work, Transformer models…",
    key="topic_input",
)

col_run, col_hint = st.columns([1, 3])
with col_run:
    run_btn = st.button("▶ Run Research Agent", type="primary", disabled=not topic_input.strip())
with col_hint:
    proxy_note = "via Requesty.ai proxy" if REQUESTY_ACTIVE else "direct to Anthropic"
    st.caption(f"The agent autonomously selects sources, makes 2–5 queries, then synthesises a report — {proxy_note}.")

if run_btn and topic_input.strip():
    with st.spinner(f"Researching '{topic_input}'… (making real web requests)"):
        summary, messages, all_blocks, round_metrics = run_research_agent(topic_input.strip())

    sources_used = render_research_trace(messages, all_blocks, round_metrics)

    # Final summary
    if summary:
        st.markdown("### Research summary")
        st.markdown(
            "<div style='background:#F3E5F5;border-left:4px solid #8E24AA;"
            "padding:12px 16px;border-radius:6px;'>"
            "<strong style='color:#8E24AA;'>📝 Synthesised report</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(summary)

    # Aggregate metrics
    st.divider()
    total_in      = sum(r["input_tokens"]  for r in round_metrics)
    total_out     = sum(r["output_tokens"] for r in round_metrics)
    total_latency = sum(r["latency_ms"]    for r in round_metrics)
    tool_calls_made = [b for b in all_blocks if b["type"] == "tool_use"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Sources queried",  len(tool_calls_made))
    c2.metric("Unique sources",   len(set(b["name"] for b in tool_calls_made)))
    c3.metric("Input tokens",     f"{total_in:,}")
    c4.metric("Output tokens",    f"{total_out:,}")
    c5.metric("Total latency",    f"{total_latency:,} ms")

    # Per-source query breakdown
    if tool_calls_made:
        st.markdown("**Query breakdown by source:**")
        for tool_name, style in SOURCE_STYLES.items():
            calls = [b for b in tool_calls_made if b["name"] == tool_name]
            if calls:
                queries = ", ".join(f'"{b["input"].get("query","")}"' for b in calls)
                st.markdown(
                    f"<div style='display:inline-block;background:{style['color']}22;"
                    f"border:1px solid {style['color']};padding:4px 10px;border-radius:6px;"
                    f"margin:3px;font-size:0.88em;'>"
                    f"<strong style='color:{style['color']};'>{style['icon']} {style['label']}</strong>"
                    f" — {len(calls)} {'query' if len(calls)==1 else 'queries'}: {queries}</div>",
                    unsafe_allow_html=True,
                )

    if REQUESTY_ACTIVE:
        st.info(
            "📡 These calls were routed through Requesty.ai. "
            "Full traces, token costs, and latency breakdown are available in your "
            "[Requesty dashboard](https://app.requesty.ai).",
            icon="📡",
        )
