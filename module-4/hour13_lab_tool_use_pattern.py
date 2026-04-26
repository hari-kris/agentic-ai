"""
Hour 13 Lab — Tool Use Pattern
Module 4 | Core Agentic Patterns I

Claude decides when to call tools, your code executes them, and Claude synthesises the result.
Labs: (1) tool schema explorer, (2) calculator tool, (3) knowledge search, (4) multi-tool agent.

Run: streamlit run module-4/hour13_lab_tool_use_pattern.py
"""

import ast
import json
import operator
import streamlit as st
from claude_client import chat_with_tools

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 13 — Tool Use Pattern", page_icon="🔧", layout="wide")
st.title("🔧 Hour 13 — Tool Use Pattern")
st.caption("Module 4 | Core Agentic Patterns I")

st.markdown("""
The **Tool Use Pattern** extends an agent's capabilities beyond its training data.
Claude reads your tool schemas, decides when to call a tool, and your Python code
executes it — then Claude uses the result to answer.

This lab covers:
1. **Tool schema explorer** — read the JSON schemas Claude receives
2. **Calculator tool** — watch Claude hand off maths to Python
3. **Knowledge search tool** — Claude retrieves facts from a local knowledge base
4. **Multi-tool agent** — both tools available; Claude picks what it needs
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 13 Guide")
    st.markdown("""
**Sections in this lab:**
1. **Schema explorer** — understand what Claude sees
2. **Calculator** — safe expression evaluation via tool
3. **Knowledge search** — retrieval over a small KB
4. **Multi-tool** — Claude picks tools autonomously

**What to observe:**
- When Claude calls a tool vs answers directly
- The `tool_use` block structure in the trace
- How the `tool_result` is injected back
- The two-call pattern: initial call + finalise call
""")
    st.divider()
    st.markdown("**Experiment ideas:**")
    st.markdown("- Ask a maths question Claude should know — does it still use the calculator?")
    st.markdown("- Ask about something NOT in the knowledge base — what does Claude do?")
    st.markdown("- Ask a compound question requiring both tools")
    st.divider()
    st.info("**Key principle:** The model reads `description` fields to decide which tool to call. Well-written descriptions are the most important part of tool design.")

# ── Tool Implementations ───────────────────────────────────────────────────────

def safe_calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely using AST parsing."""
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
        ast.FloorDiv, ast.USub, ast.UAdd,
    )
    try:
        tree = ast.parse(expression.strip(), mode="eval")
        for node in ast.walk(tree):
            if not isinstance(node, allowed_nodes):
                return f"Error: disallowed operation '{type(node).__name__}' in expression."
        result = eval(compile(tree, "<string>", "eval"))  # noqa: S307 — AST-validated
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


KNOWLEDGE_BASE = [
    {"id": "KB-001", "title": "Python GIL", "content": "The Global Interpreter Lock (GIL) in CPython prevents multiple threads from executing Python bytecode simultaneously. It simplifies memory management but limits CPU-bound multi-threading. Use multiprocessing or async I/O to work around it."},
    {"id": "KB-002", "title": "REST vs GraphQL", "content": "REST APIs use fixed endpoints and HTTP verbs. GraphQL uses a single endpoint where clients specify exactly the data shape they need. GraphQL reduces over-fetching but adds schema complexity."},
    {"id": "KB-003", "title": "Docker containers", "content": "Docker containers package an application with all its dependencies into a standardised unit. Unlike VMs, containers share the host OS kernel, making them lightweight and fast to start. docker run starts a container; docker build creates an image."},
    {"id": "KB-004", "title": "SQL vs NoSQL", "content": "SQL databases store data in tables with fixed schemas and support ACID transactions. NoSQL databases (MongoDB, DynamoDB) offer flexible schemas and horizontal scaling. Choose SQL for structured relational data; NoSQL for unstructured or high-volume workloads."},
    {"id": "KB-005", "title": "CI/CD pipelines", "content": "Continuous Integration (CI) automatically tests code on every push. Continuous Delivery (CD) automates deployment to staging or production. Popular tools include GitHub Actions, Jenkins, and GitLab CI. A green pipeline means the build and tests passed."},
    {"id": "KB-006", "title": "HTTP status codes", "content": "200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests, 500 Internal Server Error, 503 Service Unavailable. 2xx = success, 4xx = client error, 5xx = server error."},
    {"id": "KB-007", "title": "Asymptotic complexity", "content": "Big O notation describes algorithm performance as input grows. O(1) is constant time; O(log n) logarithmic; O(n) linear; O(n log n) linearithmic; O(n²) quadratic. Prefer lower complexity for large datasets."},
    {"id": "KB-008", "title": "JWT authentication", "content": "JSON Web Tokens (JWT) encode claims as a signed Base64 string: header.payload.signature. The server issues a JWT after login; clients send it in the Authorization header. Tokens are stateless — the server verifies the signature without a database lookup."},
    {"id": "KB-009", "title": "Microservices architecture", "content": "Microservices split an application into small, independently deployable services that communicate over APIs. Benefits: independent scaling, technology diversity, fault isolation. Drawbacks: network latency, distributed debugging complexity, operational overhead."},
    {"id": "KB-010", "title": "LLM temperature", "content": "Temperature controls the randomness of LLM output. At temperature 0 the model picks the highest-probability token at each step (deterministic). At temperature 1 it samples proportionally. Higher temperatures produce more creative but less consistent output. Use low temperature for structured tasks like JSON generation."},
]


def search_knowledge(query: str, max_results: int = 2) -> str:
    """Simple keyword-based search over the knowledge base."""
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
    results = scored[:max_results]

    if not results:
        return "No relevant results found in the knowledge base."

    output = []
    for _, item in results:
        output.append(f"[{item['id']}] {item['title']}\n{item['content']}")
    return "\n\n".join(output)


# ── Tool Schemas ───────────────────────────────────────────────────────────────
CALCULATOR_TOOL = {
    "name": "calculate",
    "description": "Evaluate a mathematical expression and return the numeric result. Use this whenever a precise calculation is required — do not try to compute numbers in your head.",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A mathematical expression using standard operators: + - * / ** % //. Examples: '17 * 43', '(100 / 3) ** 2', '2 ** 10'.",
            }
        },
        "required": ["expression"],
    },
}

SEARCH_TOOL = {
    "name": "search_knowledge",
    "description": "Search the internal software engineering knowledge base for technical information. Use this when the user asks about programming concepts, tools, architectures, or protocols that may be documented in the knowledge base.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "A keyword phrase or question describing the topic to search for.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return. Default 2.",
                "default": 2,
            },
        },
        "required": ["query"],
    },
}

TOOL_REGISTRY = {
    "calculate": lambda **kwargs: safe_calculate(kwargs["expression"]),
    "search_knowledge": lambda **kwargs: search_knowledge(kwargs["query"], kwargs.get("max_results", 2)),
}

AGENT_SYSTEM = """\
You are a helpful technical assistant with access to tools.
Use the calculate tool for any arithmetic that requires precision.
Use the search_knowledge tool to look up software engineering concepts, tools, and architectures.
If neither tool is needed, answer directly from your knowledge.
Be concise and accurate.\
"""


def render_trace(messages: list, blocks: list, final_text: str):
    """Render a formatted tool call trace."""
    st.markdown("**Tool call trace:**")
    with st.container(border=True):
        for block in blocks:
            if block["type"] == "text" and block["text"].strip():
                st.markdown(
                    f"<div style='background:#E3F2FD;border-left:4px solid #1E88E5;"
                    f"padding:8px 12px;border-radius:4px;margin:4px 0;'>"
                    f"<strong style='color:#1E88E5;'>🤖 Assistant (thinking)</strong><br>{block['text']}</div>",
                    unsafe_allow_html=True,
                )
            elif block["type"] == "tool_use":
                st.markdown(
                    f"<div style='background:#FFF3E0;border-left:4px solid #FB8C00;"
                    f"padding:8px 12px;border-radius:4px;margin:4px 0;'>"
                    f"<strong style='color:#FB8C00;'>🔧 Tool call: {block['name']}</strong><br>"
                    f"<code>{json.dumps(block['input'], indent=2)}</code></div>",
                    unsafe_allow_html=True,
                )

        for msg in messages:
            if msg.get("role") == "user":
                for content in msg.get("content", []):
                    if isinstance(content, dict) and content.get("type") == "tool_result":
                        result_text = content.get("content", "")[:500]
                        st.markdown(
                            f"<div style='background:#E8F5E9;border-left:4px solid #43A047;"
                            f"padding:8px 12px;border-radius:4px;margin:4px 0;'>"
                            f"<strong style='color:#43A047;'>✅ Tool result</strong><br>"
                            f"<code>{result_text}</code></div>",
                            unsafe_allow_html=True,
                        )

        if final_text:
            st.markdown(
                f"<div style='background:#F3E5F5;border-left:4px solid #8E24AA;"
                f"padding:8px 12px;border-radius:4px;margin:4px 0;'>"
                f"<strong style='color:#8E24AA;'>💬 Final answer</strong><br>{final_text}</div>",
                unsafe_allow_html=True,
            )


def run_tool_agent(user_question: str, tools: list) -> tuple[str, list, int, int]:
    """Run the tool use loop. Returns (final_answer, messages, total_in, total_out)."""
    messages = [{"role": "user", "content": user_question}]
    total_in, total_out = 0, 0
    all_blocks = []
    final_answer = ""

    for _ in range(5):  # max 5 tool call rounds
        blocks, usage = chat_with_tools(AGENT_SYSTEM, messages, tools, max_tokens=600)
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]
        all_blocks.extend(blocks)

        tool_calls = [b for b in blocks if b["type"] == "tool_use"]
        text_blocks = [b for b in blocks if b["type"] == "text"]

        if not tool_calls:
            final_answer = text_blocks[0]["text"] if text_blocks else ""
            break

        # Build assistant message from all blocks
        assistant_content = []
        for b in blocks:
            if b["type"] == "text":
                assistant_content.append({"type": "text", "text": b["text"]})
            elif b["type"] == "tool_use":
                assistant_content.append({"type": "tool_use", "id": b["id"], "name": b["name"], "input": b["input"]})
        messages.append({"role": "assistant", "content": assistant_content})

        # Execute all tool calls and collect results
        tool_results = []
        for tc in tool_calls:
            fn = TOOL_REGISTRY.get(tc["name"])
            result = fn(**tc["input"]) if fn else f"Unknown tool: {tc['name']}"
            tool_results.append({"type": "tool_result", "tool_use_id": tc["id"], "content": result})

        messages.append({"role": "user", "content": tool_results})

    return final_answer, messages, all_blocks, total_in, total_out


# ── Section 1: Tool Schema Explorer ───────────────────────────────────────────
st.divider()
st.subheader("1 — Tool Schema Explorer")

st.markdown("""
Before any code runs, Claude reads these schemas to understand what tools exist and
when to use them. The **description** field is the most important — it tells the model
when this tool is appropriate.
""")

tab_calc, tab_search = st.tabs(["🔢 calculate", "🔍 search_knowledge"])
with tab_calc:
    st.code(json.dumps(CALCULATOR_TOOL, indent=2), language="json")
    st.info("Notice: the `description` explicitly says *'do not try to compute numbers in your head'* — this nudges Claude to use the tool even for calculations it could approximate.")
with tab_search:
    st.code(json.dumps(SEARCH_TOOL, indent=2), language="json")
    with st.expander("See the knowledge base (10 items)"):
        for item in KNOWLEDGE_BASE:
            st.markdown(f"**[{item['id']}] {item['title']}** — {item['content'][:80]}…")

# ── Section 2: Calculator Tool ────────────────────────────────────────────────
st.divider()
st.subheader("2 — Calculator Tool")

st.markdown("Ask a maths question. Claude will call `calculate(expression)` rather than computing the answer itself.")

CALC_PRESETS = [
    "Custom question — type below",
    "What is 17 multiplied by 43?",
    "If I invest £5,000 at 6.5% annual interest for 10 years with compound interest, what is the final value? (use the formula 5000 * (1.065 ** 10))",
    "What is the square root of 144, then add 7 and multiply by 3?",
    "What is 2 to the power of 20?",
]

sel_calc = st.selectbox("Pick a preset:", CALC_PRESETS, key="calc_preset")
calc_q = st.text_area(
    "Your question:",
    value="" if sel_calc == CALC_PRESETS[0] else sel_calc,
    height=60,
    key="calc_q",
)

if st.button("▶ Run Calculator Agent", type="primary", disabled=not calc_q.strip()):
    with st.spinner("Agent running…"):
        answer, msgs, blocks, tin, tout = run_tool_agent(calc_q.strip(), [CALCULATOR_TOOL])

    render_trace(msgs, blocks, answer)
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Input tokens", tin)
    c2.metric("Output tokens", tout)

# ── Section 3: Knowledge Search Tool ──────────────────────────────────────────
st.divider()
st.subheader("3 — Knowledge Search Tool")

st.markdown("Ask a technical question. Claude will search the knowledge base before answering.")

SEARCH_PRESETS = [
    "Custom question — type below",
    "What is the GIL in Python and how do I work around it?",
    "Explain the difference between REST and GraphQL.",
    "How does JWT authentication work?",
    "What HTTP status code should I return when a user isn't logged in?",
]

sel_srch = st.selectbox("Pick a preset:", SEARCH_PRESETS, key="srch_preset")
srch_q = st.text_area(
    "Your question:",
    value="" if sel_srch == SEARCH_PRESETS[0] else sel_srch,
    height=60,
    key="srch_q",
)

if st.button("▶ Run Search Agent", type="primary", disabled=not srch_q.strip()):
    with st.spinner("Agent running…"):
        answer, msgs, blocks, tin, tout = run_tool_agent(srch_q.strip(), [SEARCH_TOOL])

    render_trace(msgs, blocks, answer)
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Input tokens", tin)
    c2.metric("Output tokens", tout)

# ── Section 4: Multi-Tool Agent ────────────────────────────────────────────────
st.divider()
st.subheader("4 — Multi-Tool Agent")

st.markdown("""
Both tools are now active. Ask a compound question — the agent picks which tool(s) to call.
Try questions that require both computation **and** knowledge retrieval.
""")

MULTI_PRESETS = [
    "Custom question — type below",
    "I have 3 microservices each making 150 API calls per second. What is the total calls per minute, and briefly explain what microservices are?",
    "What is 2 to the power of 10, and what does Big O O(n²) mean in comparison to O(log n)?",
    "If a Docker container uses 256 MB RAM and I run 12 of them, how many GB is that total? Also, what is Docker?",
    "What is the difference between JWT and session-based auth, and how much is 365 * 24 * 60 * 60 seconds in a year?",
]

sel_multi = st.selectbox("Pick a preset:", MULTI_PRESETS, key="multi_preset")
multi_q = st.text_area(
    "Your question:",
    value="" if sel_multi == MULTI_PRESETS[0] else sel_multi,
    height=80,
    key="multi_q",
)

if st.button("▶ Run Multi-Tool Agent", type="primary", disabled=not multi_q.strip()):
    with st.spinner("Agent running…"):
        answer, msgs, blocks, tin, tout = run_tool_agent(multi_q.strip(), [CALCULATOR_TOOL, SEARCH_TOOL])

    tools_used = [b["name"] for b in blocks if b["type"] == "tool_use"]
    if tools_used:
        st.markdown(
            f"<div style='background:#FFF3E0;border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
            f"<strong style='color:#FB8C00;'>🔧 Tools called: {', '.join(tools_used)}</strong></div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("Claude answered directly without calling any tools.")

    render_trace(msgs, blocks, answer)
    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Tool calls made", len(tools_used))
    c2.metric("Input tokens", tin)
    c3.metric("Output tokens", tout)
