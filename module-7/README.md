# Module 7 — RAG and Agentic Memory

**Course:** Agentic AI — A Professional 30-Hour Course  
**Module:** 7 of 9 | Duration: 3 hours (Hours 25–27)

---

## Before You Start — API Key Setup

Create a `.env` file inside the `module-7/` folder:

```
module-7/
├── .env        ← create this file
├── claude_client.py
├── hour25_lab_rag_fundamentals.py
├── hour26_lab_agentic_rag.py
└── hour27_lab_memory_and_state.py
```

Add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

Get your key from [console.anthropic.com](https://console.anthropic.com).

> **Important:** Never commit your `.env` file to git. It contains a secret key.

---

## File Reference

### `claude_client.py` — Shared API Wrapper

Shared helper used by all three labs. Not run directly.

- Loads `ANTHROPIC_API_KEY` from `.env`
- Exposes `chat(system, user, max_tokens, temperature)` → `(text, usage_dict)`
- Exposes `chat_with_tools(system, messages, tools, max_tokens)` → `(content_blocks, usage_dict)`
- Model: `claude-sonnet-4-6`

> **Hour 27 note:** `chat_with_tools` is used for multi-turn conversation by passing the full `chat_history` list as the `messages` argument and `tools=[]`. This is valid — the function accepts any message list, not just tool-use conversations.

---

### `hour25_lab_rag_fundamentals.py` — RAG Fundamentals

**Hour 25.** TF-IDF retrieval from a hardcoded 15-document knowledge base, grounded generation with citations,
and a side-by-side comparison of answers generated with and without retrieved context.

**Components:**

| Component | Colour | Role |
|-----------|--------|------|
| TF-IDF Retriever | Green | Scores all 15 docs; returns top-K with cosine similarity scores |
| Grounded Generator | Green | Answers using retrieved context; cites with `[Doc N]` format |
| Direct Generator | Blue | Answers from parametric knowledge only; no citations |

**Knowledge base:** 15 hardcoded documents covering AI agents, RAG, TF-IDF, vector embeddings, multi-agent architectures, memory systems, and agent patterns.

**What students do:**
1. View the 4-stage RAG pipeline diagram: Query → Retriever → Context → Generator
2. **Retrieval demo** — enter a query; TF-IDF returns top-K chunks with similarity scores displayed as progress bars
3. **Grounded generation** — retrieved chunks injected into Claude's prompt; Claude answers with `[Doc N]` citations
4. **Comparison** — same query runs both without context (direct) and with retrieved context side by side

**Key observations:**
- Similarity scores drop sharply for queries not covered in the knowledge base
- The grounded generator cites specific `[Doc N]` references; the direct generator does not
- Grounded prompts are larger (context added) — observe the input token difference in Section 4
- TF-IDF matches on keywords; semantically similar but different-vocabulary queries may score lower

```bash
streamlit run module-7/hour25_lab_rag_fundamentals.py
```

---

### `hour26_lab_agentic_rag.py` — Agentic RAG

**Hour 26.** A RAG Router agent classifies each query as RETRIEVE (use the knowledge base) or DIRECT
(answer from model knowledge). The appropriate path executes and the answer is displayed with path attribution.
A force-comparison mode runs both paths on the same query for direct contrast.

**Components:**

| Component | Colour | Role |
|-----------|--------|------|
| RAG Router | Teal | Returns JSON: `{route: "RETRIEVE\|DIRECT", reason, confidence}` |
| TF-IDF Retriever | Green | Activated only on RETRIEVE path; same index as Hour 25 |
| Grounded Generator | Green | Answer with `[Doc N]` citations (RETRIEVE path) |
| Direct Generator | Blue | Answer from parametric knowledge (DIRECT path) |

**What students do:**
1. View the agentic RAG architecture diagram with branching RETRIEVE and DIRECT paths
2. **Main demo** — run queries; see routing decision card (route + confidence + reason), path taken, and final answer
3. **Force comparison** — run same query through both paths regardless of router; compare grounded vs direct outputs

**Key observations:**
- In-KB queries (agents, RAG, memory, patterns) route to RETRIEVE; out-of-KB queries route to DIRECT
- The router's confidence indicates how clearly the query maps to the knowledge base
- RETRIEVE path answers contain `[Doc N]` citations; DIRECT path answers do not
- Force comparison shows the cost and quality difference between paths on the same query

```bash
streamlit run module-7/hour26_lab_agentic_rag.py
```

---

### `hour27_lab_memory_and_state.py` — Memory and State

**Hour 27.** Two sections: (1) short-term conversation memory — multi-turn chat with growing history showing
how agents recall earlier turns, and (2) long-term memory — a user profile extracted from each interaction
and injected into the system prompt to personalise future responses.

**Components:**

| Component | Colour | Role |
|-----------|--------|------|
| Chat Agent (Section 1) | Green | Multi-turn conversation using full message history |
| Memory Extractor | Purple | Reads each turn; extracts explicit user facts as JSON `{facts[]}` |
| Personalised Chat (Section 2) | Green | Same chat agent, but profile injected into system prompt |

**What students do:**
1. **Short-term memory** — chat with the agent; reference earlier messages ("what did I say?"); reset conversation and verify the agent forgets; observe context token count growing in real time
2. **Long-term memory** — chat and reveal personal facts; watch the user profile panel update after each turn; reset the conversation (profile persists); start a new conversation (agent still knows facts); reset the profile (agent truly forgets)

**Key observations:**
- Short-term memory is exactly the message list passed to Claude — resetting it erases all context
- The memory extractor runs after every turn, even when no new facts are present
- Profile injection happens at the system prompt level — the agent uses facts naturally without being prompted
- Resetting the conversation in Section 2 clears messages but NOT the profile — the agent remains personalised

```bash
streamlit run module-7/hour27_lab_memory_and_state.py
```

---

## Quick Start

```bash
# Install dependencies (from repo root)
python -m venv env
source env/bin/activate
pip install -r requirements.txt

# Create your API key file
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > module-7/.env

# Run any lab
streamlit run module-7/hour25_lab_rag_fundamentals.py
streamlit run module-7/hour26_lab_agentic_rag.py
streamlit run module-7/hour27_lab_memory_and_state.py
```

---

## Module 7 Concept Map

| Hour | Lab | Core concept | Agentic connection |
|------|-----|-------------|-------------------|
| 25 | RAG Fundamentals | TF-IDF retrieval; similarity scores; grounded generation | The retriever selects; the LLM generates — never conflate these two roles |
| 26 | Agentic RAG | Router decides RETRIEVE vs DIRECT; force comparison | Not every query benefits from retrieval — routing saves cost and reduces latency |
| 27 | Memory and State | Short-term = in-context; long-term = in-storage + injected | Short-term memory disappears on reset; long-term memory survives session resets |

---

## Colour Convention

| Colour | Hex | Used for |
|--------|-----|----------|
| Blue | `#1E88E5` | Executor / Technical / Direct Generator |
| Orange | `#FB8C00` | Tools / Specialist / Context Injector |
| Green | `#43A047` | Memory / Retriever / Knowledge / Grounded Generator |
| Purple | `#8E24AA` | Planner / Orchestrator / Memory Extractor |
| Teal | `#00897B` | Router / Classifier |
| Red | `#E53935` | Critic / Evaluator |

---

## Troubleshooting

- **AuthenticationError** → check that `module-7/.env` exists and contains `ANTHROPIC_API_KEY=sk-ant-...`
- **ModuleNotFoundError: sklearn** → run `pip install -r requirements.txt` from the repo root; `scikit-learn` is listed in requirements
- **TF-IDF returns low similarity scores** → expected for queries not well-covered in the knowledge base; a top score of 0.15–0.30 on a broad query is normal for TF-IDF
- **Hour 26 router always routes to RETRIEVE** → broad AI queries may always score above the router's threshold; try clearly out-of-domain queries ("What is photosynthesis?") to see DIRECT routing
- **Hour 27: chat_with_tools with empty tools list** → this is correct usage; `chat_with_tools` accepts any message list with `tools=[]` for multi-turn chat without tool use
- **Hour 27: memory extractor extracts nothing** → the extractor only extracts explicit stated facts; vague messages ("that's interesting") produce empty extractions — say your name or job title explicitly
- **ModuleNotFoundError: claude_client** → run from the repo root with `streamlit run module-7/hour25_lab_rag_fundamentals.py`, not from inside the `module-7/` folder
