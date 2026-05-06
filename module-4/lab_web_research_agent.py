"""
Web Research Agent — Module 4 Bonus Lab
Module 4 | Core Agentic Patterns I

An agent that researches any topic by querying multiple real web sources.
Students observe which sites Claude chooses, what is retrieved, and how the
findings are synthesised into a final summary.

Run: streamlit run module-4/lab_web_research_agent.py
"""

import json
import re
import xml.etree.ElementTree as ET

import requests
import streamlit as st
import wikipedia as wiki_lib

from claude_client import chat_with_tools

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Web Research Agent", page_icon="🌐", layout="wide")
st.title("🌐 Web Research Agent")
st.caption("Module 4 | Core Agentic Patterns I — Bonus Lab")

st.markdown("""
A **web research agent** that autonomously queries multiple real internet sources,
then synthesises findings into a structured summary.

**What you'll see in this lab:**
1. Which **source types** the agent can search (Wikipedia, arXiv, Hacker News, DuckDuckGo)
2. How Claude **decides** which sources suit the topic
3. What each source **returns** — shown in a colour-coded trace
4. The **synthesised summary** that cites all sources used
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Lab Guide")
    st.markdown("""
**Research pipeline:**
1. You enter a topic
2. The agent calls 2–5 search tools autonomously
3. Each tool queries a real website
4. Claude synthesises all results into a final report

**What to observe:**
- Which sources Claude picks for different topic types
- How many searches it makes before synthesising
- Whether results differ across sources on the same topic
- Token cost of a multi-source research task
""")
    st.divider()
    st.markdown("**Topic ideas to try:**")
    st.markdown("- *Quantum computing* — mixes science + community + general")
    st.markdown("- *Remote work productivity* — news-heavy, opinion-rich")
    st.markdown("- *Transformer neural networks* — deep arXiv + HN territory")
    st.markdown("- *History of the internet* — Wikipedia-first topic")
    st.markdown("- *Python performance optimisation* — HN + web practical")
    st.divider()
    st.info(
        "**Key principle:** The agent selects sources strategically. "
        "Watch how a science topic triggers arXiv, a tech topic triggers Hacker News, "
        "and a historical topic leads with Wikipedia."
    )

# ── Source colour palette (follows course convention) ─────────────────────────
SOURCE_STYLES = {
    "search_wikipedia":   {"color": "#1E88E5", "label": "Wikipedia",   "icon": "📖"},
    "search_arxiv":       {"color": "#8E24AA", "label": "arXiv",       "icon": "🎓"},
    "search_hackernews":  {"color": "#FB8C00", "label": "Hacker News", "icon": "💬"},
    "search_duckduckgo":  {"color": "#43A047", "label": "DuckDuckGo",  "icon": "🔍"},
}

# ── Tool Implementations ───────────────────────────────────────────────────────

def search_wikipedia(query: str, sentences: int = 4) -> str:
    """Fetch a Wikipedia article summary for the query."""
    try:
        results = wiki_lib.search(query, results=3)
        if not results:
            return f"No Wikipedia articles found for '{query}'."
        # Try the top result; fall back if disambiguation
        for title in results:
            try:
                summary = wiki_lib.summary(title, sentences=sentences, auto_suggest=False)
                url = wiki_lib.page(title, auto_suggest=False).url
                return f"[Wikipedia — {title}]\nURL: {url}\n\n{summary}"
            except wiki_lib.exceptions.DisambiguationError:
                continue
            except wiki_lib.exceptions.PageError:
                continue
        return f"No usable Wikipedia page found for '{query}'."
    except Exception as exc:
        return f"Wikipedia search error: {exc}"


def search_arxiv(query: str, max_results: int = 3) -> str:
    """Search arXiv for recent research papers on the query."""
    try:
        safe_query = re.sub(r"[^\w\s]", " ", query)
        url = (
            f"https://export.arxiv.org/api/query"
            f"?search_query=all:{requests.utils.quote(safe_query)}"
            f"&start=0&max_results={max_results}"
            f"&sortBy=relevance&sortOrder=descending"
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
    """Search Hacker News for community discussions on the query."""
    try:
        url = (
            f"https://hn.algolia.com/api/v1/search"
            f"?query={requests.utils.quote(query)}"
            f"&tags=story&hitsPerPage={max_results}"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", [])
        if not hits:
            return f"No Hacker News discussions found for '{query}'."

        items = []
        for h in hits:
            title   = h.get("title", "Untitled")
            points  = h.get("points", 0)
            comments = h.get("num_comments", 0)
            hn_url  = f"https://news.ycombinator.com/item?id={h.get('objectID','')}"
            items.append(f"• {title}  [{points} pts, {comments} comments]\n  {hn_url}")

        return (
            f"[Hacker News — top {len(items)} stories for '{query}']\n\n"
            + "\n\n".join(items)
        )
    except Exception as exc:
        return f"Hacker News search error: {exc}"


def search_duckduckgo(query: str) -> str:
    """Query the DuckDuckGo Instant Answer API for a structured overview."""
    try:
        url = "https://api.duckduckgo.com/"
        params = {"q": query, "format": "json", "no_html": "1", "skip_disambig": "1"}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        parts = []
        abstract = data.get("AbstractText", "").strip()
        if abstract:
            parts.append(f"Abstract: {abstract[:500]}")
            parts.append(f"Source: {data.get('AbstractURL', '')}")

        # Related topics
        related = data.get("RelatedTopics", [])[:4]
        if related:
            topics = []
            for t in related:
                text = t.get("Text", "")
                if text:
                    topics.append(f"  – {text[:120]}")
            if topics:
                parts.append("Related topics:\n" + "\n".join(topics))

        if not parts:
            return (
                f"DuckDuckGo returned no instant-answer data for '{query}'. "
                "Try a more specific query or use another source."
            )

        return f"[DuckDuckGo Instant Answer — '{query}']\n\n" + "\n\n".join(parts)
    except Exception as exc:
        return f"DuckDuckGo search error: {exc}"


# ── Tool Schemas ───────────────────────────────────────────────────────────────
WIKIPEDIA_TOOL = {
    "name": "search_wikipedia",
    "description": (
        "Search Wikipedia for factual background, definitions, history, and encyclopaedic "
        "overviews. Best for: foundational concepts, historical events, well-established science, "
        "notable people or organisations. Always start here for topics that have a solid factual base."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The topic or concept to look up on Wikipedia.",
            },
            "sentences": {
                "type": "integer",
                "description": "Number of summary sentences to return (default 4, max 8).",
                "default": 4,
            },
        },
        "required": ["query"],
    },
}

ARXIV_TOOL = {
    "name": "search_arxiv",
    "description": (
        "Search arXiv for peer-reviewed research papers and preprints. Best for: "
        "cutting-edge science, AI/ML research, physics, mathematics, computer science, "
        "or any topic where academic depth matters. Use when the user wants research findings "
        "or when a topic is evolving rapidly in academic literature."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keywords or a short phrase describing the research topic.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of papers to return (default 3).",
                "default": 3,
            },
        },
        "required": ["query"],
    },
}

HACKERNEWS_TOOL = {
    "name": "search_hackernews",
    "description": (
        "Search Hacker News for tech community discussions, practitioner opinions, and recent "
        "industry conversations. Best for: software engineering topics, startup trends, tools & "
        "frameworks, developer experience, tech industry news. Use when you want real-world "
        "practitioner perspectives rather than academic or encyclopaedic views."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Keywords describing the topic to search in Hacker News stories.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of stories to return (default 4).",
                "default": 4,
            },
        },
        "required": ["query"],
    },
}

DUCKDUCKGO_TOOL = {
    "name": "search_duckduckgo",
    "description": (
        "Search the web via DuckDuckGo Instant Answers for general current information, "
        "practical guides, and structured topic summaries not covered by the other tools. "
        "Best for: recent events, product comparisons, how-to topics, and any query where "
        "you need a broad current-web perspective."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A search query as you would type it into a web search engine.",
            }
        },
        "required": ["query"],
    },
}

ALL_TOOLS = [WIKIPEDIA_TOOL, ARXIV_TOOL, HACKERNEWS_TOOL, DUCKDUCKGO_TOOL]

TOOL_REGISTRY = {
    "search_wikipedia":  lambda **kw: search_wikipedia(kw["query"], kw.get("sentences", 4)),
    "search_arxiv":      lambda **kw: search_arxiv(kw["query"], kw.get("max_results", 3)),
    "search_hackernews": lambda **kw: search_hackernews(kw["query"], kw.get("max_results", 4)),
    "search_duckduckgo": lambda **kw: search_duckduckgo(kw["query"]),
}

# ── Agent System Prompt ────────────────────────────────────────────────────────
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
2. Choose sources that match the topic: a science topic warrants arXiv; \
a tech tool warrants Hacker News; a historical topic warrants Wikipedia first.
3. After gathering results, write a structured summary with these sections:
   - **Overview** (2–3 sentences)
   - **Key findings** (bullet list, one per source used)
   - **Sources consulted** (list each tool + the URL/link returned)
4. Be objective and cite which source provided which information.
5. If a source returns no useful data, note that and move on.\
"""


# ── Run Agent ──────────────────────────────────────────────────────────────────

def run_research_agent(topic: str) -> tuple[str, list, list, int, int]:
    """Run the research agent loop. Returns (summary, messages, all_blocks, in_tokens, out_tokens)."""
    messages = [{"role": "user", "content": f"Research this topic thoroughly: {topic}"}]
    total_in, total_out = 0, 0
    all_blocks: list = []
    final_answer = ""

    for _ in range(8):  # allow up to 8 tool-call rounds
        blocks, usage = chat_with_tools(RESEARCH_SYSTEM, messages, ALL_TOOLS, max_tokens=1500)
        total_in  += usage["input_tokens"]
        total_out += usage["output_tokens"]
        all_blocks.extend(blocks)

        tool_calls = [b for b in blocks if b["type"] == "tool_use"]
        text_blocks = [b for b in blocks if b["type"] == "text"]

        if not tool_calls:
            final_answer = text_blocks[0]["text"] if text_blocks else ""
            break

        # Append assistant turn
        assistant_content = []
        for b in blocks:
            if b["type"] == "text":
                assistant_content.append({"type": "text", "text": b["text"]})
            elif b["type"] == "tool_use":
                assistant_content.append(
                    {"type": "tool_use", "id": b["id"], "name": b["name"], "input": b["input"]}
                )
        messages.append({"role": "assistant", "content": assistant_content})

        # Execute tool calls
        tool_results = []
        for tc in tool_calls:
            fn = TOOL_REGISTRY.get(tc["name"])
            result = fn(**tc["input"]) if fn else f"Unknown tool: {tc['name']}"
            tool_results.append({"type": "tool_result", "tool_use_id": tc["id"], "content": result})
        messages.append({"role": "user", "content": tool_results})

    return final_answer, messages, all_blocks, total_in, total_out


# ── Render Research Trace ──────────────────────────────────────────────────────

def render_research_trace(messages: list, all_blocks: list, summary: str):
    """Render colour-coded trace of sources queried and results received."""
    st.markdown("### Research trace")

    sources_used: list[str] = []

    with st.container(border=True):
        for block in all_blocks:
            if block["type"] == "text" and block["text"].strip():
                st.markdown(
                    f"<div style='background:#E3F2FD;border-left:4px solid #1E88E5;"
                    f"padding:8px 12px;border-radius:4px;margin:6px 0;'>"
                    f"<strong style='color:#1E88E5;'>🤖 Agent thinking</strong><br>"
                    f"<span style='font-size:0.9em;'>{block['text']}</span></div>",
                    unsafe_allow_html=True,
                )
            elif block["type"] == "tool_use":
                style = SOURCE_STYLES.get(block["name"], {"color": "#555", "label": block["name"], "icon": "🔎"})
                sources_used.append(block["name"])
                query_display = block["input"].get("query", json.dumps(block["input"]))
                st.markdown(
                    f"<div style='background:#FAFAFA;border-left:4px solid {style['color']};"
                    f"padding:8px 12px;border-radius:4px;margin:6px 0;'>"
                    f"<strong style='color:{style['color']};'>{style['icon']} Searching {style['label']}</strong>"
                    f"<br><code style='font-size:0.85em;'>query: \"{query_display}\"</code></div>",
                    unsafe_allow_html=True,
                )

        # Tool results from message history
        for msg in messages:
            if msg.get("role") == "user":
                for content in msg.get("content", []):
                    if isinstance(content, dict) and content.get("type") == "tool_result":
                        result_text = (content.get("content", "") or "")[:600]
                        result_preview = result_text.replace("\n", "<br>")
                        st.markdown(
                            f"<div style='background:#F1F8E9;border-left:4px solid #43A047;"
                            f"padding:8px 12px;border-radius:4px;margin:6px 0;font-size:0.82em;'>"
                            f"<strong style='color:#43A047;'>✅ Result received</strong><br>"
                            f"{result_preview}…</div>",
                            unsafe_allow_html=True,
                        )

    # Sources banner
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

    # Final summary
    if summary:
        st.markdown("### Research summary")
        st.markdown(
            f"<div style='background:#F3E5F5;border-left:4px solid #8E24AA;"
            f"padding:12px 16px;border-radius:6px;'>"
            f"<strong style='color:#8E24AA;'>📝 Synthesised report</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(summary)

    return sources_used


# ── Section 1: Source Explorer ─────────────────────────────────────────────────
st.divider()
st.subheader("1 — Available Sources")

st.markdown("""
The agent has four tools, each representing a different kind of web source.
Claude reads the **description** field to decide which source suits the topic.
""")

tab_wiki, tab_arxiv, tab_hn, tab_ddg = st.tabs(
    ["📖 Wikipedia", "🎓 arXiv", "💬 Hacker News", "🔍 DuckDuckGo"]
)
with tab_wiki:
    st.code(json.dumps(WIKIPEDIA_TOOL, indent=2), language="json")
    st.info("Best for: definitions, history, established science, overviews. Always a solid starting point.")
with tab_arxiv:
    st.code(json.dumps(ARXIV_TOOL, indent=2), language="json")
    st.info("Best for: AI/ML papers, physics, maths, computer science — any topic with active academic research.")
with tab_hn:
    st.code(json.dumps(HACKERNEWS_TOOL, indent=2), language="json")
    st.info("Best for: developer opinions, software tools, startup trends, real-world usage reports.")
with tab_ddg:
    st.code(json.dumps(DUCKDUCKGO_TOOL, indent=2), language="json")
    st.info("Best for: recent events, general-purpose queries, practical how-tos, product comparisons.")

# ── Section 2: How It Works ────────────────────────────────────────────────────
st.divider()
st.subheader("2 — How It Works")

st.markdown("""
This section walks through **every layer of the lab** so you can follow the data
from the moment you type a topic to the moment a report appears on screen.
""")

# ── Architecture ──────────────────────────────────────────────────────────────
with st.expander("🗺️  Architecture — end-to-end data flow", expanded=True):
    st.markdown("### End-to-end data flow")
    st.markdown(
        "Every research run passes through **five layers**. "
        "Each arrow shows what data moves between layers."
    )

    _ARROW = "<div style='text-align:center;font-size:1.4em;color:#888;margin:2px 0;'>▼</div>"
    _BOX = (
        "<div style='background:{bg};border-left:5px solid {border};"
        "border-radius:6px;padding:10px 16px;margin:4px 0;'>"
        "<strong style='color:{border};'>{icon} {title}</strong>"
        "<br><span style='font-size:0.88em;color:#444;'>{body}</span></div>"
    )

    st.markdown(
        _BOX.format(
            bg="#E3F2FD", border="#1E88E5", icon="1️⃣",
            title="User Input",
            body="You type a topic (e.g. <em>Quantum computing</em>). "
                 "It becomes the first <code>user</code> message in the message list.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_ARROW, unsafe_allow_html=True)
    st.markdown(
        _BOX.format(
            bg="#F3E5F5", border="#8E24AA", icon="2️⃣",
            title="Claude API — chat_with_tools()",
            body="The topic + system prompt + all four tool schemas are sent to Claude. "
                 "Claude reads the tool <code>description</code> fields and decides which "
                 "tool(s) to call next. It returns either a <code>tool_use</code> block "
                 "(more searching needed) or a plain <code>text</code> block (ready to summarise).",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_ARROW, unsafe_allow_html=True)
    st.markdown(
        _BOX.format(
            bg="#FFF3E0", border="#FB8C00", icon="3️⃣",
            title="Tool Registry — Python dispatch",
            body="When Claude returns a <code>tool_use</code> block the agent loop looks up "
                 "the tool name in <code>TOOL_REGISTRY</code> and calls the matching Python "
                 "function (<code>search_wikipedia</code>, <code>search_arxiv</code>, …). "
                 "Each function makes a real HTTP request to the corresponding website.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_ARROW, unsafe_allow_html=True)
    st.markdown(
        _BOX.format(
            bg="#E8F5E9", border="#43A047", icon="4️⃣",
            title="Live Web APIs — real HTTP responses",
            body="<strong>Wikipedia REST API</strong> → article summary text &amp; URL<br>"
                 "<strong>arXiv Atom API</strong> → paper titles, abstracts, links<br>"
                 "<strong>HN Algolia API</strong> → story titles, points, comment counts<br>"
                 "<strong>DuckDuckGo Instant Answer API</strong> → structured overview &amp; related topics<br>"
                 "Results are injected back into the message list as <code>tool_result</code> blocks.",
        ),
        unsafe_allow_html=True,
    )
    st.markdown(_ARROW, unsafe_allow_html=True)
    st.markdown(
        _BOX.format(
            bg="#FCE4EC", border="#E53935", icon="5️⃣",
            title="Final Synthesis — Claude writes the report",
            body="Once Claude decides it has enough information it returns a text block "
                 "(no more tool calls). That text is the structured summary: "
                 "<strong>Overview</strong>, <strong>Key findings</strong> (one per source), "
                 "and <strong>Sources consulted</strong> with links.",
        ),
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown("#### Component map")
    st.markdown(
        "<div style='font-family:monospace;font-size:0.85em;"
        "background:#F8F8F8;border:1px solid #ddd;border-radius:6px;"
        "padding:14px 18px;line-height:1.9;'>"
        "lab_web_research_agent.py<br>"
        "│<br>"
        "├── <strong>RESEARCH_SYSTEM</strong>  ← system prompt that tells Claude the source strategy<br>"
        "├── <strong>ALL_TOOLS</strong>  ← list of 4 tool schema dicts sent to every API call<br>"
        "├── <strong>TOOL_REGISTRY</strong>  ← dict mapping tool name → Python function<br>"
        "│<br>"
        "├── <strong>search_wikipedia()</strong>  → wikipedia Python lib → Wikipedia REST API<br>"
        "├── <strong>search_arxiv()</strong>  → requests → export.arxiv.org Atom feed<br>"
        "├── <strong>search_hackernews()</strong>  → requests → hn.algolia.com JSON API<br>"
        "├── <strong>search_duckduckgo()</strong>  → requests → api.duckduckgo.com JSON API<br>"
        "│<br>"
        "├── <strong>run_research_agent()</strong>  ← orchestrates the tool-call loop<br>"
        "└── <strong>render_research_trace()</strong>  ← renders colour-coded UI trace</div>",
        unsafe_allow_html=True,
    )

# ── Agent Loop ────────────────────────────────────────────────────────────────
with st.expander("🔄  Agent Loop — the tool-call cycle"):
    st.markdown("### The tool-call loop inside `run_research_agent()`")
    st.markdown(
        "The loop runs **up to 8 rounds**. Each round is one Claude API call. "
        "Claude stops when it returns a response with no `tool_use` blocks — "
        "that is its signal that it has enough information to write the final report."
    )

    st.code(
        """\
def run_research_agent(topic):
    # Step 1 — seed the message list with the user's topic
    messages = [{"role": "user", "content": f"Research this topic: {topic}"}]

    for round_number in range(8):          # ← hard cap: max 8 API calls

        # Step 2 — call Claude with the full tool schemas
        blocks, usage = chat_with_tools(
            RESEARCH_SYSTEM,   # ← source-selection strategy instructions
            messages,          # ← full conversation history so far
            ALL_TOOLS,         # ← 4 tool schemas Claude can choose from
            max_tokens=1500,
        )

        # Step 3 — separate tool calls from any thinking text
        tool_calls  = [b for b in blocks if b["type"] == "tool_use"]
        text_blocks = [b for b in blocks if b["type"] == "text"]

        # Step 4 — if no tool calls, Claude is done → capture the summary
        if not tool_calls:
            final_answer = text_blocks[0]["text"]
            break                         # ← exit the loop

        # Step 5 — append Claude's turn to the message history
        messages.append({"role": "assistant", "content": blocks})

        # Step 6 — execute every tool call Claude requested
        tool_results = []
        for tc in tool_calls:
            fn     = TOOL_REGISTRY[tc["name"]]   # ← look up the Python function
            result = fn(**tc["input"])            # ← call the real web API
            tool_results.append({
                "type":        "tool_result",
                "tool_use_id": tc["id"],          # ← must match the tool_use id
                "content":     result,            # ← raw text from the web API
            })

        # Step 7 — inject results back as a user message → next round starts
        messages.append({"role": "user", "content": tool_results})

    return final_answer, messages, blocks, total_in, total_out
""",
        language="python",
    )

    st.markdown("#### Why does the loop need a hard cap?")
    st.markdown(
        "Without a cap an agent could keep searching indefinitely. "
        "8 rounds is generous — typical runs use 3–5. "
        "If Claude still hasn't summarised after 8 rounds the function returns "
        "whatever text Claude produced in the last round."
    )

    st.markdown("#### What makes Claude stop searching?")
    st.markdown(
        "The **system prompt** says: *'Make at least 2 searches across DIFFERENT sources "
        "before synthesising.'* Claude honours this by continuing to emit `tool_use` blocks "
        "until it is satisfied it has enough breadth. Once it decides to write the report "
        "it emits only a `text` block — that absence of `tool_use` is what triggers the `break`."
    )

# ── Message History ───────────────────────────────────────────────────────────
with st.expander("💬  Message History — how the messages list builds up"):
    st.markdown("### How the message list grows")
    st.markdown(
        "Claude is stateless — it has no memory between API calls. "
        "The entire conversation is rebuilt and resent on every round. "
        "This is how multi-turn tool use works under the hood."
    )

    st.markdown("#### Round 1 — initial request")
    st.code(
        """\
messages = [
    {
        "role": "user",
        "content": "Research this topic thoroughly: Quantum computing"
    }
]
# → sent to Claude with 4 tool schemas
# ← Claude returns: [tool_use: search_wikipedia(query="quantum computing")]
""",
        language="python",
    )

    st.markdown("#### After round 1 — assistant turn appended")
    st.code(
        """\
messages = [
    {"role": "user",      "content": "Research this topic: Quantum computing"},
    {
        "role": "assistant",
        "content": [
            {
                "type":  "tool_use",
                "id":    "toolu_01XYZ",           # ← unique ID for this call
                "name":  "search_wikipedia",
                "input": {"query": "quantum computing"}
            }
        ]
    }
]
""",
        language="python",
    )

    st.markdown("#### After tool execution — tool_result injected as user turn")
    st.code(
        """\
messages = [
    {"role": "user",      "content": "Research this topic: Quantum computing"},
    {"role": "assistant", "content": [{"type": "tool_use", "id": "toolu_01XYZ", ...}]},
    {
        "role": "user",
        "content": [
            {
                "type":        "tool_result",
                "tool_use_id": "toolu_01XYZ",     # ← must match the tool_use id above
                "content":     "[Wikipedia — Quantum computing]\\nURL: https://...\\n\\n
                                 Quantum computing is a type of computation that ..."
            }
        ]
    }
]
# → entire list resent to Claude → Claude now has the Wikipedia result in context
# ← Claude may call another tool, or write the final summary
""",
        language="python",
    )

    st.markdown("#### Key rule: roles must alternate")
    st.markdown(
        "The Anthropic API requires messages to alternate `user` → `assistant` → `user`. "
        "Tool results are always wrapped in a `user` message. "
        "If you break the alternation the API raises a `400 Bad Request`."
    )

    st.markdown("#### Why does this matter for token cost?")
    st.markdown(
        "Every round resends the entire history. After 4 tool calls the input to Claude "
        "contains the original question, all 4 assistant turns, and all 4 tool results. "
        "This is why the **Input tokens** metric grows significantly across rounds — "
        "you pay for context growth, not just new text."
    )

# ── Tool Execution ────────────────────────────────────────────────────────────
with st.expander("🔧  Tool Execution — from tool_use block to HTTP request"):
    st.markdown("### From `tool_use` block → HTTP request → `tool_result`")
    st.markdown(
        "When Claude emits a `tool_use` block your Python code is responsible for "
        "actually running the tool. Claude never touches the internet itself — "
        "it only decides *what* to call and *with what arguments*."
    )

    st.markdown("#### Step A — Claude's output block")
    st.code(
        """\
# What chat_with_tools() returns when Claude wants to search arXiv:
{
    "type":  "tool_use",
    "id":    "toolu_02ABC",
    "name":  "search_arxiv",           # ← name must match a key in TOOL_REGISTRY
    "input": {
        "query":       "quantum error correction",
        "max_results": 3               # ← optional param from the tool schema
    }
}
""",
        language="json",
    )

    st.markdown("#### Step B — Tool registry dispatch")
    st.code(
        """\
# TOOL_REGISTRY maps every tool name to a Python lambda
TOOL_REGISTRY = {
    "search_wikipedia":  lambda **kw: search_wikipedia(kw["query"], kw.get("sentences", 4)),
    "search_arxiv":      lambda **kw: search_arxiv(kw["query"], kw.get("max_results", 3)),
    "search_hackernews": lambda **kw: search_hackernews(kw["query"], kw.get("max_results", 4)),
    "search_duckduckgo": lambda **kw: search_duckduckgo(kw["query"]),
}

# Dispatch in the loop:
fn     = TOOL_REGISTRY[tc["name"]]   # tc["name"] == "search_arxiv"
result = fn(**tc["input"])           # calls search_arxiv(query=..., max_results=3)
""",
        language="python",
    )

    st.markdown("#### Step C — Inside `search_arxiv()`: the HTTP request")
    st.code(
        """\
def search_arxiv(query, max_results=3):
    url = (
        f"https://export.arxiv.org/api/query"
        f"?search_query=all:{requests.utils.quote(query)}"
        f"&start=0&max_results={max_results}"
        f"&sortBy=relevance"
    )
    resp = requests.get(url, timeout=10)      # ← real HTTP GET to arXiv
    resp.raise_for_status()

    root = ET.fromstring(resp.text)           # ← arXiv returns XML (Atom feed)
    entries = root.findall("atom:entry", ns)

    # Build a plain-text result string for Claude to read
    papers = []
    for entry in entries:
        title   = entry.findtext("atom:title", "", ns).strip()
        summary = entry.findtext("atom:summary", "", ns).strip()[:300]
        link    = entry.findtext("atom:id", "", ns).strip()
        papers.append(f"• {title}\\n  {link}\\n  {summary}…")

    return f"[arXiv — top {len(papers)} papers]\\n\\n" + "\\n\\n".join(papers)
    # ↑ plain text — Claude reads this in the next round as a tool_result
""",
        language="python",
    )

    st.markdown("#### Step D — Result injected back into messages")
    st.code(
        """\
tool_results.append({
    "type":        "tool_result",
    "tool_use_id": tc["id"],      # ← ties result back to the specific tool_use call
    "content":     result,        # ← the plain-text string search_arxiv() returned
})
messages.append({"role": "user", "content": tool_results})
# Claude reads this in the very next API call
""",
        language="python",
    )

    st.markdown("#### Why plain text, not JSON?")
    st.markdown(
        "`tool_result` content just needs to be a string that Claude can read. "
        "Plain text with clear formatting (`[Source — query]`, bullets, URLs) "
        "is easier for Claude to parse and cite in the final summary than nested JSON."
    )

# ── Synthesis ─────────────────────────────────────────────────────────────────
with st.expander("📝  Synthesis — how gathered results become the final report"):
    st.markdown("### How gathered results become the final report")
    st.markdown(
        "After 2–5 tool calls the message history contains the original question "
        "plus all retrieved source texts. Claude's final API call sees the entire "
        "conversation and writes a structured synthesis."
    )

    st.markdown("#### What Claude sees at synthesis time")
    st.code(
        """\
# Simplified view of what the messages list looks like at the final API call:

[
  # ── Original request ──
  {"role": "user",      "content": "Research this topic: Quantum computing"},

  # ── Round 1: Wikipedia ──
  {"role": "assistant", "content": [{"type": "tool_use", "name": "search_wikipedia", ...}]},
  {"role": "user",      "content": [{"type": "tool_result", "content": "[Wikipedia] Quantum computing is..."}]},

  # ── Round 2: arXiv ──
  {"role": "assistant", "content": [{"type": "tool_use", "name": "search_arxiv", ...}]},
  {"role": "user",      "content": [{"type": "tool_result", "content": "[arXiv] • Quantum error correction..."}]},

  # ── Round 3: Hacker News ──
  {"role": "assistant", "content": [{"type": "tool_use", "name": "search_hackernews", ...}]},
  {"role": "user",      "content": [{"type": "tool_result", "content": "[Hacker News] • Ask HN: Quantum..."}]},
]
# Claude now writes the final text — no more tool_use blocks
""",
        language="python",
    )

    st.markdown("#### The system prompt's synthesis instructions")
    st.code(
        """\
RESEARCH_SYSTEM = \"\"\"
...
After gathering results, write a structured summary with these sections:
  - **Overview** (2–3 sentences)
  - **Key findings** (bullet list, one per source used)
  - **Sources consulted** (list each tool + the URL/link returned)

Be objective and cite which source provided which information.
If a source returns no useful data, note that and move on.
\"\"\"
""",
        language="python",
    )

    st.markdown("#### Why structure the output this way?")
    st.markdown("""
| Section | Purpose |
|---------|---------|
| **Overview** | Quick mental model — 2-3 sentences so the reader knows the territory |
| **Key findings** | One bullet per source — forces Claude to use *all* retrieved data, not just the first result |
| **Sources consulted** | Transparency — students can click through and verify every claim independently |
""")

    st.markdown("#### Token cost reality check")
    st.markdown(
        "At synthesis time, Claude's input includes **every tool result in full**. "
        "A 3-source run typically sends 1,500–3,000 input tokens. "
        "That is why the Input tokens metric is much larger than the Output tokens — "
        "the work of research is paid for in context, not generation."
    )

# ── Section 3: Run the Research Agent ─────────────────────────────────────────
st.divider()
st.subheader("3 — Research a Topic")

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

sel_topic = st.selectbox("Choose a preset topic or enter your own:", TOPIC_PRESETS, key="topic_preset")
topic_input = st.text_input(
    "Research topic:",
    value="" if sel_topic == TOPIC_PRESETS[0] else sel_topic,
    placeholder="e.g. Quantum computing, Remote work, Transformer models…",
    key="topic_input",
)

col_run, col_hint = st.columns([1, 3])
with col_run:
    run_btn = st.button("▶ Run Research Agent", type="primary", disabled=not topic_input.strip())
with col_hint:
    st.caption("The agent will autonomously choose which sources to search (2–5 queries) then synthesise a report.")

if run_btn and topic_input.strip():
    with st.spinner(f"Researching '{topic_input}'… (making real web requests)"):
        summary, messages, all_blocks, tin, tout = run_research_agent(topic_input.strip())

    sources_used = render_research_trace(messages, all_blocks, summary)

    st.divider()
    tool_calls_made = [b for b in all_blocks if b["type"] == "tool_use"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sources queried", len(tool_calls_made))
    c2.metric("Unique sources", len(set(b["name"] for b in tool_calls_made)))
    c3.metric("Input tokens",  tin)
    c4.metric("Output tokens", tout)

    # Per-source breakdown
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
