"""
Hour 25 Lab — RAG Fundamentals
Module 7 | RAG and Agentic Memory

TF-IDF retrieval from a hardcoded knowledge base. Shows similarity search,
top-k retrieved chunks with scores, grounded generation with citations, and
a side-by-side comparison of with-context vs without-context generation.

Run: streamlit run module-7/hour25_lab_rag_fundamentals.py
"""

import json
import numpy as np
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 25 — RAG Fundamentals", page_icon="📚", layout="wide")
st.title("📚 Hour 25 — RAG Fundamentals")
st.caption("Module 7 | RAG and Agentic Memory")

st.markdown("""
**RAG (Retrieval-Augmented Generation)** combines a retrieval system with a language model.
Instead of answering from parametric memory alone, the model receives retrieved document chunks as context.
This **grounds** the answer in specific, verifiable documents and dramatically reduces hallucination on
domain-specific topics. The retriever's job is *selection* — the LLM's job is *generation*. Never conflate
these two roles.
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 25 Guide")
    st.markdown("""
**Sections in this lab:**
1. The RAG pipeline architecture
2. Retrieval demo — TF-IDF similarity search over 15 documents
3. Grounded generation with citations
4. Grounded vs ungrounded comparison (side by side)

**What to observe:**
- Similarity scores drop for queries not well-covered in the knowledge base
- The grounded generator uses [Doc N] citations; the direct generator does not
- Grounded answers stay closer to what the documents actually say
- The grounded prompt is larger — retrieval adds token cost
""")
    st.divider()
    st.markdown("""
**Experiment ideas:**
- Try a very specific technical query — see how few chunks match
- Try a broad query — see if the top chunk score drops
- In Section 4, compare how often Claude says "I believe" vs cites a document
""")
    st.divider()
    st.info("**Key principle:** The retriever selects; the LLM generates. Keep these roles strictly separated. A retriever that answers is not a retriever — it is an agent.")

# ── Knowledge Base ─────────────────────────────────────────────────────────────
KNOWLEDGE_BASE = [
    {
        "id": 1,
        "title": "What is an AI Agent?",
        "text": "An AI agent is a software system that perceives its environment, makes decisions, and takes actions to achieve goals. Unlike a simple API call, an agent operates in a loop: observe, plan, act, observe again. Agents can use tools, call external APIs, read files, browse the web, and interact with other agents. The defining characteristic is autonomy — the agent decides what steps to take, in what order, and when to stop.",
    },
    {
        "id": 2,
        "title": "Retrieval-Augmented Generation (RAG)",
        "text": "RAG combines a retrieval system with a language model. When a query arrives, a retriever selects the most relevant documents from a knowledge base. These documents are appended to the prompt as context, and the LLM generates an answer grounded in that context. RAG reduces hallucination by anchoring the model in specific, verifiable text. It also allows the knowledge base to be updated without retraining the model.",
    },
    {
        "id": 3,
        "title": "Vector Embeddings for Semantic Search",
        "text": "Vector embeddings represent text as dense numerical vectors in a high-dimensional space. Semantically similar texts produce vectors that are close together in this space. Embedding models convert a sentence or paragraph into a fixed-size vector. Similarity between two pieces of text is then computed as the cosine similarity between their vectors — a value from 0 (unrelated) to 1 (identical meaning). This enables semantic search: finding documents that mean the same thing even if they use different words.",
    },
    {
        "id": 4,
        "title": "TF-IDF: Term Frequency-Inverse Document Frequency",
        "text": "TF-IDF is a classical text retrieval method. TF measures how often a word appears in a document. IDF penalises words that appear in many documents, reducing the weight of common words like 'the'. The product gives each word a score indicating its importance to a specific document relative to the corpus. Cosine similarity between a query TF-IDF vector and document vectors identifies the best-matching documents. TF-IDF does not capture semantic meaning but is fast, requires no embedding model, and works well for keyword-rich queries.",
    },
    {
        "id": 5,
        "title": "Agentic RAG: Routing Queries to Retrieval or Direct Generation",
        "text": "Standard RAG always retrieves, even when the query is a general question the LLM can answer from parametric memory. Agentic RAG adds a router agent that decides whether to retrieve before answering. If the query is about information in the knowledge base, the router sends it to the retriever. If the query is general knowledge or conversational, the router sends it directly to the LLM. This two-path design reduces unnecessary retrieval calls and keeps latency low for simple queries.",
    },
    {
        "id": 6,
        "title": "Short-Term Memory in Agent Systems",
        "text": "Short-term memory in an agent system is the conversation history — the list of messages exchanged between user and agent in the current session. As the conversation grows, the agent has context about earlier turns: what the user said, what it replied, what decisions were made. This is implemented by passing the full message list to the LLM on every turn. Short-term memory is ephemeral — it resets when the session ends. Its size is bounded by the LLM's context window.",
    },
    {
        "id": 7,
        "title": "Long-Term Memory and User Profiles",
        "text": "Long-term memory persists beyond a single session. An agent with long-term memory can remember that a user prefers detailed explanations, works in a specific domain, or has a history of particular interests. Implementation approaches include: storing key facts in a database and injecting them into the system prompt, using a vector store to retrieve relevant memories based on the current query, or maintaining a structured user profile updated after each interaction. Long-term memory enables personalised, context-aware agents.",
    },
    {
        "id": 8,
        "title": "The Orchestrator-Workers Pattern",
        "text": "The orchestrator-workers pattern uses a central orchestrator agent to assign subtasks to specialised worker agents. The orchestrator holds the high-level goal, decomposes it into discrete tasks, and dispatches each task to the most appropriate worker. Workers receive only their own task brief — not the full goal or other workers' outputs. The orchestrator collects all results and synthesises them into a final deliverable. This pattern maps directly to how human manager-team structures work.",
    },
    {
        "id": 9,
        "title": "Multi-Agent Handoffs and State Passing",
        "text": "In a multi-agent pipeline, agents pass state to each other via handoff packages — structured data objects that accumulate information as they move through the pipeline. The first agent adds its findings to the package. The second agent reads the full package so far and adds its own layer. By the final agent, the package contains the accumulated intelligence of every upstream agent. Handoffs enable sequential specialisation: each agent builds on what came before without repeating it.",
    },
    {
        "id": 10,
        "title": "Flat vs Hierarchical Multi-Agent Systems",
        "text": "A flat multi-agent system has agents that operate independently — each processes the same input but produces its own output with no coordination. A hierarchical system adds a coordination layer: an orchestrator reads all agent outputs and produces a single, integrated result. Flat systems are simpler but produce fragmented, potentially contradictory outputs. Hierarchical systems are more expensive (one extra orchestrator call) but deliver a coherent synthesis. The choice depends on whether downstream consumers need one view or many views.",
    },
    {
        "id": 11,
        "title": "Prompt Chaining and Sequential Pipelines",
        "text": "Prompt chaining passes the output of one LLM call as the input to the next. Each step is specialised: the first step might extract structure, the second might analyse it, the third might produce a formatted report. The chain is linear and deterministic — the same sequence runs for every input. Chaining is the simplest multi-step pattern and the foundation for more complex orchestration patterns. Its main limitation is that it does not branch — every input follows the same path regardless of content.",
    },
    {
        "id": 12,
        "title": "Tool Use in Agentic Systems",
        "text": "Tool use extends an LLM's capabilities beyond text generation. The LLM is given descriptions of available tools (functions). When the LLM determines a tool is needed, it returns a structured tool call rather than a final answer. The application executes the tool and returns the result. The LLM then continues with this new information. Common tools include: web search, code execution, database queries, file reading, and API calls. Tool use transforms a passive text generator into an active agent that can affect the world.",
    },
    {
        "id": 13,
        "title": "The Reflection Pattern",
        "text": "The reflection pattern uses a critic agent to evaluate a generator agent's output. The generator creates a draft. The critic scores it on specific criteria and provides targeted feedback. A refiner rewrites the draft to address the feedback. This cycle can run multiple times. Reflection improves output quality by separating generation from evaluation — the critic applies more rigorous standards than a combined generate-and-critique prompt. The pattern is particularly effective when quality criteria are explicit and measurable.",
    },
    {
        "id": 14,
        "title": "Parallelisation: Fan-out and Voting",
        "text": "Parallelisation sends the same input to multiple agents simultaneously. In fan-out, each agent analyses a different aspect of the input — a summariser, a risk analyst, and an opportunity analyst might all process the same document. An aggregator then synthesises the three outputs. In voting, the same agent runs multiple times with different seeds; results are compared for consensus. Fan-out improves coverage; voting improves reliability. Both increase token cost proportionally to the number of agents.",
    },
    {
        "id": 15,
        "title": "Context Window Management in Long Pipelines",
        "text": "As agent pipelines grow longer, accumulated context can exceed the LLM's context window. Strategies for managing this include: summarisation (replacing older messages with a compressed summary), selective retention (keeping only the most relevant prior turns), chunking (splitting long documents into smaller pieces before retrieval or processing), and hierarchical memory (moving older context to long-term storage and retrieving it only when relevant). Context window management is essential for agents that run long conversations or process large documents.",
    },
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
GROUNDED_GENERATOR_SYSTEM = """\
You are a knowledgeable assistant that answers questions using the provided context documents.
You MUST cite sources using the format [Doc N] where N is the document ID number.
Include at least one citation per factual claim. If the context does not contain enough
information to answer confidently, say so clearly rather than speculating.
Keep your answer to 200–250 words.\
"""

DIRECT_GENERATOR_SYSTEM = """\
You are a knowledgeable assistant. Answer the question from your general knowledge.
Do not mention any documents or sources — just answer naturally.
Keep your answer to 200–250 words.\
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
RANK_COLORS = ["#43A047", "#FB8C00", "#1E88E5", "#8E24AA", "#E53935"]
RANK_BGS    = ["#E8F5E9", "#FFF3E0", "#E3F2FD", "#F3E5F5", "#FFEBEE"]

PRESET_QUERIES = [
    "Custom query — type below",
    "How do agents use tools to interact with the world?",
    "What is the difference between flat and hierarchical multi-agent systems?",
    "How does RAG reduce hallucination?",
    "What is TF-IDF and how does it differ from vector embeddings?",
    "How do agents manage long conversations?",
    "What is short-term vs long-term memory in an agent?",
]

# ── Section 1 — Architecture Diagram ──────────────────────────────────────────
st.markdown("---")
st.subheader("1 — The RAG Pipeline")

pipe_cols = st.columns([1.2, 0.2, 1.5, 0.2, 1.5, 0.2, 1.5])
stages = [
    ("#00897B", "#E0F2F1", "❓", "QUERY", "User's question enters the pipeline."),
    ("#43A047", "#E8F5E9", "🔍", "RETRIEVER", "TF-IDF similarity search.\nReturns top-K chunks with scores."),
    ("#FB8C00", "#FFF3E0", "📄", "CONTEXT", "Retrieved chunks prepended to the Claude prompt."),
    ("#1E88E5", "#E3F2FD", "🤖", "GENERATOR", "LLM produces answer grounded in context.\nCites [Doc N]."),
]
for i, (color, bg, icon, label, desc) in enumerate(stages):
    col_idx = i * 2
    with pipe_cols[col_idx]:
        st.markdown(
            f"<div style='border-top:4px solid {color};background:{bg};border-radius:8px;"
            f"padding:14px;text-align:center;min-height:150px;'>"
            f"<div style='font-size:1.6em;'>{icon}</div>"
            f"<div style='font-weight:bold;color:{color};margin:4px 0;'>[{label}]</div>"
            f"<div style='font-size:0.75em;color:#444;white-space:pre-line;'>{desc}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    if i < 3:
        with pipe_cols[col_idx + 1]:
            st.markdown("<div style='text-align:center;font-size:1.5em;margin-top:55px;'>→</div>", unsafe_allow_html=True)

st.markdown(
    "<div style='background:#F5F5F5;border-radius:6px;padding:10px 14px;margin-top:10px;font-size:0.85em;'>"
    "<strong>Similarity:</strong> cosine_sim(query_vector, doc_vector) ∈ [0.0, 1.0] &nbsp;|&nbsp; "
    "<strong>Citation format:</strong> <code>[Doc N]</code> where N is the document ID"
    "</div>",
    unsafe_allow_html=True,
)

with st.expander("See system prompts"):
    tabs = st.tabs(["Grounded Generator", "Direct Generator"])
    for tab, prompt in zip(tabs, [GROUNDED_GENERATOR_SYSTEM, DIRECT_GENERATOR_SYSTEM]):
        with tab:
            st.code(prompt, language="text")

# ── Section 2 — Retrieval Demo ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("2 — Retrieval Demo")
st.markdown("Enter a query. The TF-IDF retriever scores all 15 knowledge base documents and returns the top matches.")

top_k = st.slider("Number of chunks to retrieve:", 1, 5, 3, key="s2_top_k")
s2_preset = st.selectbox("Choose a preset query or write your own:", PRESET_QUERIES, key="s2_query_preset")
s2_query_val = "" if s2_preset == PRESET_QUERIES[0] else s2_preset
s2_query = st.text_input("Query:", value=s2_query_val, key="s2_query", placeholder="Enter your query…")

if st.button("▶ Retrieve", type="primary", disabled=not s2_query.strip()):
    results = retrieve(s2_query.strip(), top_k)
    st.session_state["retrieval_results"] = results
    st.session_state["s2_query_text"] = s2_query.strip()

if "retrieval_results" in st.session_state:
    results = st.session_state["retrieval_results"]
    for r in results:
        rank = r["rank"]
        color = RANK_COLORS[rank - 1] if rank <= len(RANK_COLORS) else "#8E24AA"
        bg = RANK_BGS[rank - 1] if rank <= len(RANK_BGS) else "#F3E5F5"
        doc = r["doc"]
        score = r["score"]

        st.markdown(
            f"<div style='border-top:4px solid {color};background:{bg};"
            f"border-radius:6px;padding:10px 14px;margin-bottom:6px;'>"
            f"<strong style='color:{color};'>Rank {rank} — [Doc {doc['id']}] {doc['title']}</strong></div>",
            unsafe_allow_html=True,
        )
        rc1, rc2 = st.columns([1, 4])
        with rc1:
            st.metric("Similarity score", f"{score:.4f}")
            st.progress(min(score, 1.0))
        with rc2:
            st.text_area("Document text:", value=doc["text"], height=100, key=f"s2_doc_{doc['id']}_{rank}", disabled=True)

    st.caption(f"Maximum possible similarity: 1.0 | Documents searched: {len(KNOWLEDGE_BASE)} | Query: \"{st.session_state['s2_query_text']}\"")

# ── Section 3 — Grounded Generation ───────────────────────────────────────────
st.markdown("---")
st.subheader("3 — Grounded Generation with Citations")
st.markdown("The retrieved chunks are injected into the prompt as context. Claude answers using these documents and must cite them with `[Doc N]`.")

if "retrieval_results" not in st.session_state:
    st.info("Run Section 2 first to retrieve documents.")
else:
    retrieved = st.session_state["retrieval_results"]
    doc_list = ", ".join(f"[Doc {r['doc']['id']}] {r['doc']['title']}" for r in retrieved)
    with st.expander(f"Using retrieved documents: {doc_list}"):
        for r in retrieved:
            st.markdown(f"**[Doc {r['doc']['id']}] {r['doc']['title']}** (score: {r['score']:.4f})")
            st.markdown(r["doc"]["text"])

    if st.button("▶ Generate Grounded Answer", type="primary"):
        context = "\n\n".join(
            f"[Doc {r['doc']['id']}] {r['doc']['title']}\n{r['doc']['text']}"
            for r in retrieved
        )
        user_msg = f"Context documents:\n\n{context}\n\nQuestion: {st.session_state['s2_query_text']}"
        with st.spinner("Generating grounded answer…"):
            answer, usage = chat(GROUNDED_GENERATOR_SYSTEM, user_msg, max_tokens=500, temperature=0.3)
        st.session_state["grounded_answer"] = answer
        st.session_state["grounded_usage"] = usage
        st.session_state["grounded_docs_used"] = len(retrieved)

    if "grounded_answer" in st.session_state:
        st.markdown(
            "<div style='border-top:4px solid #43A047;background:#E8F5E9;"
            "border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
            "<strong style='color:#43A047;'>🔍 [GROUNDED GENERATOR] Answer with Citations</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state["grounded_answer"])
        u = st.session_state["grounded_usage"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Input tokens", u.get("input_tokens", 0))
        m2.metric("Output tokens", u.get("output_tokens", 0))
        m3.metric("Documents used", st.session_state["grounded_docs_used"])

# ── Section 4 — Comparison ────────────────────────────────────────────────────
st.markdown("---")
st.subheader("4 — Grounded vs Ungrounded Generation")
st.markdown("The same query runs twice — once without retrieval context (parametric knowledge only) and once with retrieved context. Compare the answers.")

s4_preset = st.selectbox("Choose a preset query or write your own:", PRESET_QUERIES, key="s4_query_preset")
s4_query_val = "" if s4_preset == PRESET_QUERIES[0] else s4_preset
s4_query = st.text_input("Query:", value=s4_query_val, key="s4_query", placeholder="Enter a query to compare both paths…")

if st.button("▶ Compare Grounded vs Direct", type="primary", disabled=not s4_query.strip()):
    q = s4_query.strip()
    with st.spinner("Running direct generation (no retrieval)…"):
        direct_answer, u_direct = chat(DIRECT_GENERATOR_SYSTEM, q, max_tokens=500, temperature=0.4)
    with st.spinner("Running retrieval + grounded generation…"):
        s4_retrieved = retrieve(q, 3)
        context = "\n\n".join(f"[Doc {r['doc']['id']}] {r['doc']['title']}\n{r['doc']['text']}" for r in s4_retrieved)
        user_msg_grounded = f"Context documents:\n\n{context}\n\nQuestion: {q}"
        grounded_answer, u_grounded = chat(GROUNDED_GENERATOR_SYSTEM, user_msg_grounded, max_tokens=500, temperature=0.3)
    st.session_state["s4_direct"] = direct_answer
    st.session_state["s4_u_direct"] = u_direct
    st.session_state["s4_grounded"] = grounded_answer
    st.session_state["s4_u_grounded"] = u_grounded
    st.session_state["s4_retrieved"] = s4_retrieved
    st.session_state["s4_query"] = q

if "s4_direct" in st.session_state:
    cmp_cols = st.columns(2)
    with cmp_cols[0]:
        st.markdown(
            "<div style='border-top:4px solid #1E88E5;background:#E3F2FD;"
            "border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
            "<strong style='color:#1E88E5;'>🤖 [DIRECT] No Retrieval Context</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state["s4_direct"])
        u = st.session_state["s4_u_direct"]
        st.caption(f"In: {u.get('input_tokens', 0)} | Out: {u.get('output_tokens', 0)} tokens")

    with cmp_cols[1]:
        st.markdown(
            "<div style='border-top:4px solid #43A047;background:#E8F5E9;"
            "border-radius:6px;padding:10px 14px;margin-bottom:8px;'>"
            "<strong style='color:#43A047;'>🔍 [GROUNDED] With Retrieved Context (Top 3 Docs)</strong></div>",
            unsafe_allow_html=True,
        )
        retrieved_s4 = st.session_state.get("s4_retrieved", [])
        s4_doc_ids = ", ".join("[Doc " + str(r["doc"]["id"]) + "]" for r in retrieved_s4)
        with st.expander(f"Retrieved: {s4_doc_ids}"):
            for r in retrieved_s4:
                st.markdown(f"**[Doc {r['doc']['id']}] {r['doc']['title']}** (score: {r['score']:.4f})")
        st.markdown(st.session_state["s4_grounded"])
        u = st.session_state["s4_u_grounded"]
        st.caption(f"In: {u.get('input_tokens', 0)} | Out: {u.get('output_tokens', 0)} tokens (higher — context added)")

    st.markdown("""
> **Observe:** Does the grounded answer cite specific documents with `[Doc N]`?
> Does the direct answer express uncertainty ("I believe…", "typically…")?
> Which answer stays closer to documented facts vs general AI knowledge?
""")
