"""
Hour 26 Lab — Agentic RAG
Module 7 | RAG and Agentic Memory

A router agent decides whether to retrieve from the knowledge base or answer directly.
Demonstrates the routing decision, the two execution paths, and a force-comparison mode.

Run: streamlit run module-7/hour26_lab_agentic_rag.py
"""

import json
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 26 — Agentic RAG", page_icon="🔍", layout="wide")
st.title("🔍 Hour 26 — Agentic RAG")
st.caption("Module 7 | RAG and Agentic Memory")

st.markdown("""
Standard RAG **always retrieves** — even when the query is a general question the LLM can answer
from parametric memory. **Agentic RAG** is smarter: a router agent reads the query and decides
whether retrieval will actually help. Factual questions about agents, RAG, or memory get sent to
the retriever. General conversational questions get answered directly. This two-path design reduces
latency and token cost for queries that don't benefit from retrieval.
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 26 Guide")
    st.markdown("""
**Sections in this lab:**
1. Agentic RAG architecture with routing branch
2. Run queries — router decides the path, answer is generated
3. Force comparison — same query through both paths regardless of router

**What to observe:**
- The router returns JSON with route, reason, and confidence
- In-KB queries route to RETRIEVE; out-of-KB queries route to DIRECT
- The RETRIEVE path produces citations; the DIRECT path does not
- Force comparison shows when the paths diverge most
""")
    st.divider()
    st.markdown("""
**Experiment ideas:**
- Ask "What is photosynthesis?" — see it routes to DIRECT (not in knowledge base)
- Ask "How does RAG reduce hallucination?" — should route to RETRIEVE
- Try edge cases: "What do you know about agents?" — broad, may route either way
""")
    st.divider()
    st.info("**Key principle:** Not every query benefits from retrieval. A good RAG router knows when to retrieve and when to trust the model's parametric knowledge.")

# ── Knowledge Base (identical to hour25) ──────────────────────────────────────
KNOWLEDGE_BASE = [
    {"id": 1, "title": "What is an AI Agent?", "text": "An AI agent is a software system that perceives its environment, makes decisions, and takes actions to achieve goals. Unlike a simple API call, an agent operates in a loop: observe, plan, act, observe again. Agents can use tools, call external APIs, read files, browse the web, and interact with other agents. The defining characteristic is autonomy — the agent decides what steps to take, in what order, and when to stop."},
    {"id": 2, "title": "Retrieval-Augmented Generation (RAG)", "text": "RAG combines a retrieval system with a language model. When a query arrives, a retriever selects the most relevant documents from a knowledge base. These documents are appended to the prompt as context, and the LLM generates an answer grounded in that context. RAG reduces hallucination by anchoring the model in specific, verifiable text. It also allows the knowledge base to be updated without retraining the model."},
    {"id": 3, "title": "Vector Embeddings for Semantic Search", "text": "Vector embeddings represent text as dense numerical vectors in a high-dimensional space. Semantically similar texts produce vectors that are close together in this space. Embedding models convert a sentence or paragraph into a fixed-size vector. Similarity between two pieces of text is then computed as the cosine similarity between their vectors — a value from 0 (unrelated) to 1 (identical meaning). This enables semantic search: finding documents that mean the same thing even if they use different words."},
    {"id": 4, "title": "TF-IDF: Term Frequency-Inverse Document Frequency", "text": "TF-IDF is a classical text retrieval method. TF measures how often a word appears in a document. IDF penalises words that appear in many documents, reducing the weight of common words like 'the'. The product gives each word a score indicating its importance to a specific document relative to the corpus. Cosine similarity between a query TF-IDF vector and document vectors identifies the best-matching documents. TF-IDF does not capture semantic meaning but is fast, requires no embedding model, and works well for keyword-rich queries."},
    {"id": 5, "title": "Agentic RAG: Routing Queries to Retrieval or Direct Generation", "text": "Standard RAG always retrieves, even when the query is a general question the LLM can answer from parametric memory. Agentic RAG adds a router agent that decides whether to retrieve before answering. If the query is about information in the knowledge base, the router sends it to the retriever. If the query is general knowledge or conversational, the router sends it directly to the LLM. This two-path design reduces unnecessary retrieval calls and keeps latency low for simple queries."},
    {"id": 6, "title": "Short-Term Memory in Agent Systems", "text": "Short-term memory in an agent system is the conversation history — the list of messages exchanged between user and agent in the current session. As the conversation grows, the agent has context about earlier turns: what the user said, what it replied, what decisions were made. This is implemented by passing the full message list to the LLM on every turn. Short-term memory is ephemeral — it resets when the session ends. Its size is bounded by the LLM's context window."},
    {"id": 7, "title": "Long-Term Memory and User Profiles", "text": "Long-term memory persists beyond a single session. An agent with long-term memory can remember that a user prefers detailed explanations, works in a specific domain, or has a history of particular interests. Implementation approaches include: storing key facts in a database and injecting them into the system prompt, using a vector store to retrieve relevant memories based on the current query, or maintaining a structured user profile updated after each interaction. Long-term memory enables personalised, context-aware agents."},
    {"id": 8, "title": "The Orchestrator-Workers Pattern", "text": "The orchestrator-workers pattern uses a central orchestrator agent to assign subtasks to specialised worker agents. The orchestrator holds the high-level goal, decomposes it into discrete tasks, and dispatches each task to the most appropriate worker. Workers receive only their own task brief — not the full goal or other workers' outputs. The orchestrator collects all results and synthesises them into a final deliverable. This pattern maps directly to how human manager-team structures work."},
    {"id": 9, "title": "Multi-Agent Handoffs and State Passing", "text": "In a multi-agent pipeline, agents pass state to each other via handoff packages — structured data objects that accumulate information as they move through the pipeline. The first agent adds its findings to the package. The second agent reads the full package so far and adds its own layer. By the final agent, the package contains the accumulated intelligence of every upstream agent. Handoffs enable sequential specialisation: each agent builds on what came before without repeating it."},
    {"id": 10, "title": "Flat vs Hierarchical Multi-Agent Systems", "text": "A flat multi-agent system has agents that operate independently — each processes the same input but produces its own output with no coordination. A hierarchical system adds a coordination layer: an orchestrator reads all agent outputs and produces a single, integrated result. Flat systems are simpler but produce fragmented, potentially contradictory outputs. Hierarchical systems are more expensive (one extra orchestrator call) but deliver a coherent synthesis. The choice depends on whether downstream consumers need one view or many views."},
    {"id": 11, "title": "Prompt Chaining and Sequential Pipelines", "text": "Prompt chaining passes the output of one LLM call as the input to the next. Each step is specialised: the first step might extract structure, the second might analyse it, the third might produce a formatted report. The chain is linear and deterministic — the same sequence runs for every input. Chaining is the simplest multi-step pattern and the foundation for more complex orchestration patterns. Its main limitation is that it does not branch — every input follows the same path regardless of content."},
    {"id": 12, "title": "Tool Use in Agentic Systems", "text": "Tool use extends an LLM's capabilities beyond text generation. The LLM is given descriptions of available tools (functions). When the LLM determines a tool is needed, it returns a structured tool call rather than a final answer. The application executes the tool and returns the result. The LLM then continues with this new information. Common tools include: web search, code execution, database queries, file reading, and API calls. Tool use transforms a passive text generator into an active agent that can affect the world."},
    {"id": 13, "title": "The Reflection Pattern", "text": "The reflection pattern uses a critic agent to evaluate a generator agent's output. The generator creates a draft. The critic scores it on specific criteria and provides targeted feedback. A refiner rewrites the draft to address the feedback. This cycle can run multiple times. Reflection improves output quality by separating generation from evaluation — the critic applies more rigorous standards than a combined generate-and-critique prompt. The pattern is particularly effective when quality criteria are explicit and measurable."},
    {"id": 14, "title": "Parallelisation: Fan-out and Voting", "text": "Parallelisation sends the same input to multiple agents simultaneously. In fan-out, each agent analyses a different aspect of the input — a summariser, a risk analyst, and an opportunity analyst might all process the same document. An aggregator then synthesises the three outputs. In voting, the same agent runs multiple times with different seeds; results are compared for consensus. Fan-out improves coverage; voting improves reliability. Both increase token cost proportionally to the number of agents."},
    {"id": 15, "title": "Context Window Management in Long Pipelines", "text": "As agent pipelines grow longer, accumulated context can exceed the LLM's context window. Strategies for managing this include: summarisation (replacing older messages with a compressed summary), selective retention (keeping only the most relevant prior turns), chunking (splitting long documents into smaller pieces before retrieval or processing), and hierarchical memory (moving older context to long-term storage and retrieving it only when relevant). Context window management is essential for agents that run long conversations or process large documents."},
]

# ── TF-IDF Retriever ──────────────────────────────────────────────────────────
@st.cache_resource
def build_tfidf_index():
    texts = [doc["text"] for doc in KNOWLEDGE_BASE]
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(texts)
    return vectorizer, tfidf_matrix


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    vectorizer, tfidf_matrix = build_tfidf_index()
    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, tfidf_matrix)[0]
    top_indices = np.argsort(scores)[::-1][:top_k]
    return [{"doc": KNOWLEDGE_BASE[i], "score": float(scores[i]), "rank": r + 1} for r, i in enumerate(top_indices)]


# ── System Prompts ─────────────────────────────────────────────────────────────
RAG_ROUTER_SYSTEM = """\
You are a query router for a RAG system. Your knowledge base contains documents about:
- AI agents and agentic systems (what they are, how they work)
- Retrieval-Augmented Generation (RAG) and TF-IDF
- Multi-agent architectures (flat, hierarchical, orchestrator-workers, handoffs)
- Agent memory (short-term session memory, long-term user profiles)
- Agent patterns (reflection, tool use, planning, chaining, routing, parallelisation)
- Context window management in long pipelines

Decision rules:
- RETRIEVE if the query specifically asks about any topic listed above
- DIRECT if the query is general knowledge, conversational, or about topics not in the knowledge base

Return ONLY valid JSON — no markdown fences, no commentary:
{"route": "RETRIEVE", "reason": "one sentence explaining the routing decision", "confidence": 0.0}\
"""

GROUNDED_SYSTEM = """\
You are a knowledgeable assistant answering questions using provided context documents.
Cite sources using [Doc N] format. Include at least one citation per factual claim.
If context does not fully answer the question, say so. Keep answer to 200–250 words.\
"""

DIRECT_SYSTEM = """\
You are a knowledgeable assistant. Answer the question from your general knowledge.
Be clear, accurate, and concise. Keep answer to 200–250 words.\
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
def parse_json(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


PRESET_QUERIES = [
    "Custom query — type below",
    "What is Agentic RAG and how does it differ from standard RAG?",
    "How do multi-agent handoffs work?",
    "What causes thunderstorms?",
    "Explain the orchestrator-workers pattern",
    "What is the capital of France?",
    "How does context window management work in long pipelines?",
    "What is the GDP of Germany?",
]

# ── Section 1 — Architecture Diagram ──────────────────────────────────────────
st.markdown("---")
st.subheader("1 — Agentic RAG Architecture")

st.markdown(
    "<div style='background:#FAFAFA;border-radius:8px;padding:16px;'>"
    "<div style='display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px;'>"
    "<div style='border-top:3px solid #00897B;background:#E0F2F1;border-radius:6px;padding:10px 14px;text-align:center;min-width:100px;'>"
    "<div style='font-size:1.2em;'>❓</div><strong style='color:#00897B;font-size:0.8em;'>QUERY</strong></div>"
    "<div style='font-size:1.5em;'>→</div>"
    "<div style='border-top:3px solid #00897B;background:#E0F2F1;border-radius:6px;padding:10px 14px;text-align:center;min-width:120px;'>"
    "<div style='font-size:1.2em;'>🔀</div><strong style='color:#00897B;font-size:0.8em;'>[ROUTER]</strong>"
    "<div style='font-size:0.7em;color:#555;'>returns JSON<br>RETRIEVE or DIRECT</div></div>"
    "</div>",
    unsafe_allow_html=True,
)

b_cols = st.columns(2)
with b_cols[0]:
    st.markdown(
        "<div style='border:2px solid #43A047;border-radius:8px;padding:12px;background:#F1F8E9;text-align:center;'>"
        "<strong style='color:#43A047;'>RETRIEVE path</strong><br>"
        "<div style='font-size:0.8em;margin-top:6px;'>"
        "→ 🔍 [RETRIEVER] top-K docs<br>→ 📄 [CONTEXT] prepend to prompt<br>→ 🤖 [GENERATOR] grounded answer with [Doc N] citations"
        "</div></div>",
        unsafe_allow_html=True,
    )
with b_cols[1]:
    st.markdown(
        "<div style='border:2px solid #1E88E5;border-radius:8px;padding:12px;background:#E8F4FD;text-align:center;'>"
        "<strong style='color:#1E88E5;'>DIRECT path</strong><br>"
        "<div style='font-size:0.8em;margin-top:6px;'>"
        "→ 🤖 [GENERATOR] parametric knowledge<br>&nbsp;<br>→ answer (no citations)"
        "</div></div>",
        unsafe_allow_html=True,
    )

with st.expander("See system prompts"):
    tabs = st.tabs(["RAG Router", "Grounded Generator", "Direct Generator"])
    for tab, prompt in zip(tabs, [RAG_ROUTER_SYSTEM, GROUNDED_SYSTEM, DIRECT_SYSTEM]):
        with tab:
            st.code(prompt, language="text")

# ── Section 2 — Agentic RAG ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("2 — Run Queries Through the Router")
st.markdown("The router decides the path. You see the routing decision, the path taken, and the final answer.")

top_k = st.slider("Chunks to retrieve if routed to RETRIEVE:", 1, 5, 3, key="s2_top_k")
s2_preset = st.selectbox("Choose a preset query or write your own:", PRESET_QUERIES, key="s2_query_preset")
s2_val = "" if s2_preset == PRESET_QUERIES[0] else s2_preset
s2_query = st.text_input("Query:", value=s2_val, key="s2_query", placeholder="Enter your query…")

if st.button("▶ Route and Answer", type="primary", disabled=not s2_query.strip()):
    q = s2_query.strip()

    with st.spinner("Router classifying query…"):
        raw_route, u_router = chat(RAG_ROUTER_SYSTEM, f"Query: {q}", max_tokens=200, temperature=0.1)
    routing = parse_json(raw_route)
    if routing is None:
        routing = {"route": "DIRECT", "reason": "Could not parse routing decision.", "confidence": 0.5}

    route = routing.get("route", "DIRECT")
    reason = routing.get("reason", "")
    confidence = float(routing.get("confidence", 0.5))

    if route == "RETRIEVE":
        with st.spinner("Retrieving documents…"):
            docs = retrieve(q, top_k)
        context = "\n\n".join(f"[Doc {r['doc']['id']}] {r['doc']['title']}\n{r['doc']['text']}" for r in docs)
        user_msg = f"Context documents:\n\n{context}\n\nQuestion: {q}"
        with st.spinner("Generating grounded answer…"):
            answer, u_answer = chat(GROUNDED_SYSTEM, user_msg, max_tokens=500, temperature=0.3)
    else:
        docs = []
        with st.spinner("Generating direct answer…"):
            answer, u_answer = chat(DIRECT_SYSTEM, q, max_tokens=500, temperature=0.4)

    st.session_state["s2_routing"] = routing
    st.session_state["s2_route"] = route
    st.session_state["s2_reason"] = reason
    st.session_state["s2_confidence"] = confidence
    st.session_state["s2_docs"] = docs
    st.session_state["s2_answer"] = answer
    st.session_state["s2_u_router"] = u_router
    st.session_state["s2_u_answer"] = u_answer
    st.session_state["s2_query_text"] = q

if "s2_route" in st.session_state:
    route = st.session_state["s2_route"]
    reason = st.session_state["s2_reason"]
    confidence = st.session_state["s2_confidence"]
    docs = st.session_state["s2_docs"]
    answer = st.session_state["s2_answer"]
    u_router = st.session_state["s2_u_router"]
    u_answer = st.session_state["s2_u_answer"]

    # Routing decision card
    rd_cols = st.columns([1, 2, 3])
    route_color = "#43A047" if route == "RETRIEVE" else "#1E88E5"
    with rd_cols[0]:
        st.markdown(
            f"<div style='border-top:4px solid #00897B;background:#E0F2F1;border-radius:6px;padding:12px;text-align:center;'>"
            f"<div style='font-size:0.75em;color:#00897B;font-weight:bold;'>ROUTE</div>"
            f"<div style='font-size:1.5em;font-weight:bold;color:{route_color};'>{route}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with rd_cols[1]:
        st.markdown(
            f"<div style='border-top:4px solid {'#43A047' if confidence >= 0.6 else '#FB8C00'};background:#FAFAFA;border-radius:6px;padding:12px;text-align:center;'>"
            f"<div style='font-size:0.75em;font-weight:bold;color:#555;'>CONFIDENCE</div>"
            f"<div style='font-size:1.5em;font-weight:bold;'>{confidence:.0%}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.progress(confidence)
    with rd_cols[2]:
        st.markdown(
            f"<div style='border-top:4px solid #8E24AA;background:#F3E5F5;border-radius:6px;padding:12px;'>"
            f"<div style='font-size:0.75em;color:#8E24AA;font-weight:bold;'>REASON</div>"
            f"<div style='font-size:0.88em;color:#333;margin-top:4px;'>{reason}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Path indicator
    if route == "RETRIEVE":
        st.markdown(
            f"<div style='background:#E8F5E9;border-radius:6px;padding:8px 14px;text-align:center;margin:8px 0;'>"
            f"<strong style='color:#43A047;'>↓ RETRIEVE path taken — {len(docs)} document(s) retrieved</strong></div>",
            unsafe_allow_html=True,
        )
        if docs:
            with st.expander("Retrieved documents"):
                for r in docs:
                    st.markdown(f"**[Doc {r['doc']['id']}] {r['doc']['title']}** (score: {r['score']:.4f})")
        st.markdown(
            "<div style='border-top:4px solid #43A047;background:#E8F5E9;border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
            "<strong style='color:#43A047;'>🔍 [GROUNDED ANSWER — via RETRIEVE path]</strong></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='background:#E3F2FD;border-radius:6px;padding:8px 14px;text-align:center;margin:8px 0;'>"
            "<strong style='color:#1E88E5;'>↓ DIRECT path taken — no retrieval</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div style='border-top:4px solid #1E88E5;background:#E3F2FD;border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
            "<strong style='color:#1E88E5;'>🤖 [DIRECT ANSWER — via DIRECT path]</strong></div>",
            unsafe_allow_html=True,
        )
    st.markdown(answer)

    m1, m2, m3 = st.columns(3)
    m1.metric("Router tokens", u_router.get("input_tokens", 0) + u_router.get("output_tokens", 0))
    m2.metric("Answer tokens (in + out)", u_answer.get("input_tokens", 0) + u_answer.get("output_tokens", 0))
    m3.metric("Path taken", route)

# ── Section 3 — Force Comparison ──────────────────────────────────────────────
st.markdown("---")
st.subheader("3 — Force Comparison: Same Query, Both Paths")
st.markdown("Force the same query through both paths regardless of the router's decision. Compare how the answers differ.")

s3_preset = st.selectbox("Choose a preset query or write your own:", PRESET_QUERIES, key="s3_query_preset")
s3_val = "" if s3_preset == PRESET_QUERIES[0] else s3_preset
s3_query = st.text_input("Query:", value=s3_val, key="s3_query", placeholder="Enter a query to compare both paths…")

if st.button("▶ Compare Both Paths", type="primary", disabled=not s3_query.strip()):
    q3 = s3_query.strip()
    with st.spinner("Running RETRIEVE path…"):
        s3_docs = retrieve(q3, 3)
        context3 = "\n\n".join(f"[Doc {r['doc']['id']}] {r['doc']['title']}\n{r['doc']['text']}" for r in s3_docs)
        retrieve_answer, u_retrieve = chat(GROUNDED_SYSTEM, f"Context documents:\n\n{context3}\n\nQuestion: {q3}", max_tokens=500, temperature=0.3)
    with st.spinner("Running DIRECT path…"):
        direct_answer, u_direct = chat(DIRECT_SYSTEM, q3, max_tokens=500, temperature=0.4)
    st.session_state["s3_retrieve_answer"] = retrieve_answer
    st.session_state["s3_direct_answer"] = direct_answer
    st.session_state["s3_docs"] = s3_docs
    st.session_state["s3_u_retrieve"] = u_retrieve
    st.session_state["s3_u_direct"] = u_direct
    st.session_state["s3_query"] = q3

if "s3_retrieve_answer" in st.session_state:
    cmp_cols = st.columns(2)
    with cmp_cols[0]:
        st.markdown(
            "<div style='border-top:4px solid #43A047;background:#E8F5E9;"
            "border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
            "<strong style='color:#43A047;'>🔍 [RETRIEVE PATH] — Top 3 Docs Retrieved</strong></div>",
            unsafe_allow_html=True,
        )
        s3_docs = st.session_state["s3_docs"]
        s3_doc_ids = ", ".join("[Doc " + str(r["doc"]["id"]) + "]" for r in s3_docs)
        s3_scores = ", ".join(f"{r['score']:.3f}" for r in s3_docs)
        with st.expander(f"Retrieved: {s3_doc_ids} (scores: {s3_scores})"):
            for r in s3_docs:
                st.markdown(f"**[Doc {r['doc']['id']}]** {r['doc']['title']}")
        st.markdown(st.session_state["s3_retrieve_answer"])
        u = st.session_state["s3_u_retrieve"]
        st.caption(f"In: {u.get('input_tokens', 0)} | Out: {u.get('output_tokens', 0)} tokens (higher — context added)")

    with cmp_cols[1]:
        st.markdown(
            "<div style='border-top:4px solid #1E88E5;background:#E3F2FD;"
            "border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
            "<strong style='color:#1E88E5;'>🤖 [DIRECT PATH] — No Retrieval</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state["s3_direct_answer"])
        u = st.session_state["s3_u_direct"]
        st.caption(f"In: {u.get('input_tokens', 0)} | Out: {u.get('output_tokens', 0)} tokens")

    st.markdown("""
> **Observe:** Which answer uses specific terminology from the documents?
> Which answer makes general statements? When would you trust the DIRECT path over RETRIEVE?
> If the query is not in the knowledge base, does the RETRIEVE path still produce citations?
""")
