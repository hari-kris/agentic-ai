# Module 7 — RAG and Agentic Memory
## Pre-Read: Retrieval-Augmented Generation and Agentic Memory Systems

---

## Introduction: Why Memory and Knowledge Ground Agents

A language model's parametric knowledge is fixed at training time. It cannot know what happened after its cutoff date, what your organisation's internal documents say, or what you told it three conversations ago. Two mechanisms address this:

1. **RAG (Retrieval-Augmented Generation)**: Extends the model's knowledge with retrieved documents at inference time — the model reads the documents as context and answers from them.
2. **Memory systems**: Extend the model's awareness across turns and sessions — short-term (conversation history) and long-term (persisted facts about users, goals, and preferences).

Without these mechanisms, agents hallucinate facts, forget context, and treat every user as a stranger. With them, agents become domain-grounded, context-aware, and personalised.

---

## Part 1 — RAG Fundamentals

### Why Language Models Hallucinate

Language models generate text by predicting the most probable next token given the context. When asked about domain-specific facts not well-represented in training data, the model will still produce fluent text — but the facts it produces may be invented. This is hallucination: confident, fluent, wrong output.

Hallucination is not a bug to be fixed with better prompting. It is a consequence of the fundamental mechanism of text generation. The solution is to ground the model in retrieved, verifiable documents.

### The RAG Architecture: Retrieve, Then Generate

The canonical RAG pipeline has four stages:

1. **Query**: The user's question arrives.
2. **Retrieve**: A retriever scores all documents in the knowledge base against the query and returns the top-K most relevant chunks.
3. **Augment**: The retrieved chunks are prepended to the prompt as context.
4. **Generate**: The LLM reads the context + query and produces an answer grounded in the retrieved documents.

The key invariant: the retriever does not generate text. The LLM does not retrieve documents. These two roles must remain strictly separated.

### Document Chunking Strategies

Knowledge bases contain documents that may be too long to fit in a prompt. Chunking splits documents into smaller pieces for retrieval. Common strategies:

- **Fixed-size chunks**: Split every N tokens. Simple but may cut mid-sentence.
- **Sentence-level chunks**: Split on sentence boundaries. Preserves semantic units.
- **Paragraph-level chunks**: Split on blank lines. Natural for structured text.
- **Sliding window**: Overlapping chunks ensure context is not lost at boundaries.

The choice of chunk size affects retrieval quality: chunks too large dilute relevance scoring; chunks too small lose contextual coherence.

### TF-IDF: Strengths, Limitations, and When to Use It

TF-IDF (Term Frequency-Inverse Document Frequency) assigns a weight to each word in a document:
- **TF (Term Frequency)**: How often the word appears in this document.
- **IDF (Inverse Document Frequency)**: Penalises words that appear in many documents (reducing the weight of "the", "is", "and").
- **TF-IDF score**: TF × IDF — high for words that are frequent in this document but rare across the corpus.

To retrieve documents for a query:
1. Represent the query as a TF-IDF vector.
2. Represent each document as a TF-IDF vector.
3. Compute cosine similarity between the query vector and each document vector.
4. Return the documents with the highest similarity scores.

**Strengths:**
- No embedding model required — runs entirely in Python with scikit-learn
- Fast on small corpora (hundreds of documents)
- Interpretable — you can inspect which words drove the similarity score

**Limitations:**
- Does not capture semantic meaning ("automobile" and "car" are unrelated in TF-IDF space)
- Sensitive to vocabulary mismatch between query and document
- Performs poorly on broad, general queries

### Vector Embeddings and Semantic Search: The Alternative

Embedding models (such as `text-embedding-3-small`) convert text into dense vectors in a high-dimensional space where semantically similar texts are geometrically close. "The car broke down" and "The vehicle malfunctioned" produce similar vectors despite sharing no keywords.

Semantic search with embeddings:
1. Embed all documents at indexing time (run once).
2. Embed the query at retrieval time.
3. Compute cosine similarity between query and document embeddings.
4. Return top-K documents.

Embeddings require an external model (API call or local inference), adding cost and latency. For this course, TF-IDF is used to demonstrate the retrieval concept without introducing an external dependency.

### Cosine Similarity: What the Number Means

Cosine similarity measures the angle between two vectors:
- **1.0**: Identical direction — the documents are maximally similar.
- **0.5**: 60° angle — moderate similarity.
- **0.0**: Perpendicular — completely unrelated.
- **Negative**: Only possible with dense embeddings (not TF-IDF).

A TF-IDF cosine similarity of 0.3 on a specific query is strong. A score of 0.05 on a broad query is expected — many documents partially match broad queries, diluting individual scores.

### Top-K Retrieval and Score Thresholds

Returning the top-K documents by similarity score is the default strategy. Two design decisions:

1. **K (number of documents)**: More documents = more context = higher input token cost. Typical values: K=3 for focused queries, K=5 for broad research.
2. **Score threshold**: Optionally, discard documents below a minimum similarity score (e.g., 0.05). This prevents retrieving documents that are technically "most similar" but still largely irrelevant.

### Citation Design: How Agents Reference Sources

A grounded answer must cite its sources so readers can verify claims. Two common citation formats:

- **Inline citations**: `"Agents operate in observe-plan-act loops [Doc 1]."` — citation immediately follows the claim.
- **Footnote citations**: All claims first, citations listed at the end.

Inline citations are preferred in agentic systems because the LLM can be instructed to cite at the point of each claim, making it easy to trace specific assertions back to specific documents.

System prompt instruction: `"Cite sources using the format [Doc N] where N is the document ID. Include at least one citation per factual claim."`

### Retrieval Evaluation: Precision, Recall, and MRR

How do you know if your retriever is working? Key metrics:

- **Precision@K**: Of the K retrieved documents, what fraction are actually relevant? (Measures noise.)
- **Recall@K**: Of all relevant documents, what fraction were retrieved in the top K? (Measures coverage.)
- **MRR (Mean Reciprocal Rank)**: Average of 1/rank for the first relevant document. MRR=1.0 means the most relevant document is always ranked first.

In production RAG systems, retrieval evaluation is done with a labelled test set: for each query, a human annotates which documents are relevant. In this course, we observe retrieval quality qualitatively.

---

## Part 2 — Agentic RAG

### The Problem with Always Retrieving

Standard RAG applies retrieval to every query. This creates unnecessary overhead for:

- **General knowledge queries**: "What is the capital of France?" does not benefit from retrieving documents about AI agents.
- **Conversational queries**: "Thanks, that helps!" — retrieval adds latency and cost with zero quality benefit.
- **Simple math or formatting requests**: "Convert 5km to miles" — no document retrieval needed.

For knowledge-base-specific queries, retrieval is essential. For everything else, it is waste.

### The RAG Router: Routing Queries to Retrieve or Direct

Agentic RAG inserts a router agent before the retriever:

```
Query → [ROUTER] → RETRIEVE → [RETRIEVER] → [GENERATOR] → Grounded Answer
                 ↘ DIRECT  →              → [GENERATOR] → Direct Answer
```

The router is a classifier. Its only job is to decide: does this query require retrieval? It reads the query and the knowledge base coverage (described in its system prompt) and returns a routing decision — typically as JSON:

```json
{"route": "RETRIEVE", "reason": "Query about RAG is covered in the knowledge base", "confidence": 0.92}
```

### Designing the Router's Knowledge Base Coverage

The router must know what topics are in the knowledge base. The simplest approach: list them explicitly in the router's system prompt.

```
Your knowledge base contains documents about:
- AI agents and agentic systems
- RAG and retrieval methods
- Multi-agent architectures
```

If the query matches a listed topic → RETRIEVE. Otherwise → DIRECT.

This approach requires the router to be updated when the knowledge base changes. More sophisticated approaches use embeddings to dynamically assess whether the query is likely covered in the knowledge base.

### Grounded vs Ungrounded Responses: How to Compare

When comparing grounded (RAG) and ungrounded (direct) responses to the same query, look for:

| Signal | Grounded Response | Ungrounded Response |
|--------|------------------|---------------------|
| Citations | `[Doc N]` references present | No citations |
| Specificity | Uses exact terminology from documents | Uses general terminology |
| Uncertainty | "The document states…" | "I believe…", "Typically…" |
| Scope | Bounded by what documents say | May extrapolate beyond documents |
| Accuracy on domain | High (anchored to documents) | Variable (depends on training data) |

### Confidence and the Routing Decision

The router returns a confidence score (0.0–1.0) alongside the routing decision. Confidence encodes uncertainty:

- **High confidence (>0.8)**: The router is certain about the route.
- **Low confidence (<0.5)**: The router is uncertain — the query may be ambiguous.

A threshold-based system can escalate low-confidence routing decisions for human review or default to RETRIEVE (safer) when uncertain.

### Hybrid Strategies: Retrieve + Generate with Fallback

A common production pattern:
1. Always attempt retrieval.
2. If top retrieved document score is below threshold (e.g., 0.05), fall back to direct generation.
3. If score is above threshold, use retrieved context.

This avoids the router LLM call entirely but requires a score threshold to be set empirically. The trade-off: simpler architecture, but less precise routing.

### When Agentic RAG Beats Standard RAG (and When It Doesn't)

Agentic RAG wins when:
- A large proportion of queries are general knowledge (outside the knowledge base)
- Latency is critical and retrieval adds unacceptable delay
- Token cost is a concern and retrieval adds significant context overhead

Standard RAG wins when:
- Nearly all queries are domain-specific (retrieval is almost always beneficial)
- The router LLM call costs more (latency, tokens) than the saved retrieval calls
- Routing errors (sending a KB-specific query to DIRECT) would cause harm

---

## Part 3 — Memory and State

### Two Kinds of Memory: In-Context vs In-Storage

| | Short-Term (In-Context) | Long-Term (In-Storage) |
|---|---|---|
| Location | LLM context window (message list) | External store (database, file, session state) |
| Lifetime | Current session | Persists across sessions |
| Access | Automatic — always in prompt | Requires retrieval or injection |
| Reset | Cleared when session ends | Cleared only explicitly |
| Size limit | Context window (e.g., 200K tokens) | Unbounded (bounded by storage) |

### Short-Term Memory: The Conversation Window

Short-term memory is the message history passed to the LLM on every turn. In the Claude API, this is the `messages` parameter:

```python
messages = [
    {"role": "user", "content": "My name is Alex"},
    {"role": "assistant", "content": "Hello, Alex!"},
    {"role": "user", "content": "What's my name?"},
]
# Claude receives all three messages and can reference turn 1 in its response to turn 3
```

Every token in the message history counts against the context window and is charged as input tokens. A 10-turn conversation with 200 tokens per turn uses 2,000 input tokens on turn 10 — paid on every API call.

### Managing Context Window Limits in Long Conversations

When conversations grow long, options include:

1. **Sliding window**: Keep only the last N turns. Older context is lost.
2. **Summarisation**: Compress older turns into a summary that replaces them. The summary is added to the context as a "compressed prior conversation" block.
3. **Selective retention**: Keep only turns that contain important information (user preferences, decisions made). Discard small-talk turns.
4. **Hierarchical memory**: Move older turns to long-term memory (extracted facts) and retrieve them only when relevant.

The right strategy depends on whether exact recall of earlier turns is needed, or whether a high-level summary is sufficient.

### Long-Term Memory: User Profiles and Persistent Facts

Long-term memory survives session resets. The simplest implementation:

1. After each turn, run a memory extractor agent that reads the turn and returns any new facts about the user.
2. Store the facts in a persistent store (database, JSON file, or in this course, session state).
3. On the next turn (or in future sessions), inject the stored facts into the system prompt.

```python
system_prompt = f"""
You are a helpful assistant.

Known facts about this user:
- Name: Alex
- Job: Software Engineer
- Location: Berlin
- Preferred response style: detailed with code examples

Use these facts to personalise your responses when relevant.
"""
```

The LLM now responds as if it already knows the user — without the user having to re-introduce themselves.

### Memory Extraction: How Agents Learn from Interactions

A memory extractor agent reads a conversation turn and extracts explicit facts. Key design decisions:

1. **Extract only explicit facts**: Don't infer. If the user says "I work in tech," extract `job_domain: tech`. Don't infer `job_title: software engineer`.
2. **Structured output**: Return JSON `{facts: [{key, value}]}` for reliable programmatic processing.
3. **Idempotency**: If the user provides the same fact twice, update rather than duplicate.
4. **Null case**: If no facts are present in the turn, return `{facts: []}`. Run the extractor every turn regardless.

### Profile Injection: Personalising the System Prompt

Once facts are extracted and stored, they must be injected into the system prompt to be visible to the LLM on the next turn. The injection pattern:

```python
def build_personalised_system(profile: list[dict]) -> str:
    if not profile:
        return BASE_SYSTEM_PROMPT
    facts = "\n".join(f"- {f['key']}: {f['value']}" for f in profile)
    return f"{BASE_SYSTEM_PROMPT}\n\nKnown facts about this user:\n{facts}"
```

The profile is injected at the system prompt level (not as a user message). This keeps it structurally separate from the conversation and prevents the profile from being treated as a user utterance.

### Memory Update Strategies: Replace, Append, or Merge

When a new fact conflicts with a stored fact, three strategies exist:

1. **Replace**: The new fact overwrites the old one. ("My name is Alex" → extract → stored as `name: Alex`. Later: "Call me Alexander" → extract → stored as `name: Alexander`, replacing `Alex`.)
2. **Append with timestamp**: Both facts are stored. The system uses the most recent.
3. **Merge with LLM**: A dedicated agent reads both old and new facts and produces a merged profile. Most expensive but most nuanced.

For most applications, Replace is sufficient. Append-with-timestamp is valuable when the change itself is informative ("user changed their job title").

### Privacy and Memory: What Should Agents Remember?

Not all user-disclosed information should be persisted. Design considerations:

- **Explicit consent**: Users should know what the agent remembers and be able to delete it.
- **Relevance decay**: Facts about a user's project from six months ago may no longer be relevant.
- **Sensitivity**: Job titles and preferences are typically low-risk. Health information or financial details require stricter handling.
- **Forgetting mechanisms**: Systems must implement "forget" functionality — not just profile reset (clearing the stored facts) but also purging from any persistent store.

In this course, memory is stored in Streamlit session state and resets with the browser session, making privacy straightforward. Production systems require explicit data governance policies.

### Memory in Production: Database-Backed vs In-Memory Stores

| | In-Memory (session state) | Database-backed |
|---|---|---|
| Persistence | Session only | Across sessions and deployments |
| Implementation | Python dict | PostgreSQL, Redis, vector store |
| Retrieval | All facts always injected | Facts retrieved by relevance |
| Scale | One user at a time | Millions of users |
| Use in this course | ✓ | — |
| Use in production | Only for demos | Required for real users |

For production long-term memory, facts are typically stored in a database keyed by user ID. On each turn, the user's profile is fetched, relevant facts are selected (by recency or relevance), and the selected facts are injected into the system prompt.

---

## Summary: The Memory Hierarchy

```
Conversation History (short-term)
    └── Exists in: LLM context window
    └── Lifetime: current session
    └── Access: automatic (always passed to LLM)
    └── Reset: session end or explicit clear

User Profile (long-term)
    └── Exists in: database / session state
    └── Lifetime: across sessions
    └── Access: injected into system prompt
    └── Reset: explicit profile reset

Knowledge Base (RAG)
    └── Exists in: document store + retrieval index
    └── Lifetime: until documents are updated
    └── Access: retrieved on demand per query
    └── Reset: document deletion/re-indexing
```

---

## Checklist: Choosing the Right Memory Strategy

**Use short-term (conversation history) when:**
- [ ] The agent needs to refer back to earlier turns in the same session
- [ ] Context size is manageable (< 50 turns)
- [ ] Forgetting at session end is acceptable

**Use long-term (user profile) when:**
- [ ] The agent should personalise responses using facts from prior sessions
- [ ] Users would be frustrated at re-introducing themselves each session
- [ ] A structured fact store is acceptable (facts, not full conversation replay)

**Use RAG (retrieval-augmented generation) when:**
- [ ] Answers require knowledge from specific, versioned documents
- [ ] The knowledge base changes more frequently than the model can be retrained
- [ ] Citations and grounding are required for trust and verifiability

**Use Agentic RAG (with router) when:**
- [ ] A significant proportion of queries are outside the knowledge base
- [ ] Retrieval latency and token cost are concerns
- [ ] The knowledge base coverage can be described precisely in the router's system prompt
