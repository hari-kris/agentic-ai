# Module 6 — Multi-Agent Systems

**Course:** Agentic AI — A Professional 30-Hour Course  
**Module:** 6 of 9 | Duration: 3 hours (Hours 22–24)

---

## Before You Start — API Key Setup

Create a `.env` file inside the `module-6/` folder:

```
module-6/
├── .env        ← create this file
├── claude_client.py
├── hour22_lab_multiagent_basics.py
├── hour23_lab_orchestrator_workers.py
└── hour24_lab_agent_handoffs.py
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

---

### `hour22_lab_multiagent_basics.py` — Multi-Agent Basics

**Hour 22.** Three specialist agents independently analyse the same news headline in a flat system.
An orchestrator then reads all three outputs and writes a coordinated synthesis — demonstrating the
difference between flat (independent, potentially contradictory) and hierarchical (coordinated, resolved) architectures.

**The agents:**

| Agent | Colour | Role |
|-------|--------|------|
| Summarizer | Blue | Returns JSON: `{analysis, confidence, key_points}` |
| Fact-Checker | Red | Returns JSON: `{analysis, confidence, key_points}` |
| Implications Analyst | Orange | Returns JSON: `{analysis, confidence, key_points}` |
| Orchestrator | Purple | Reads all three outputs, writes coordinated prose synthesis |

**What students do:**
1. View the flat vs hierarchical architecture diagram side by side
2. **Flat system** — choose a preset headline; observe three independent outputs which may contradict each other; see confidence scores per agent
3. **Hierarchical system** — run the orchestrator on the same outputs; observe how contradictions are resolved into one coherent view
4. Compare total LLM calls and coordination quality between flat (3 calls) and hierarchical (4 calls)

**Key observations:**
- Flat agents may contradict each other on the same headline — this is expected and is the teaching point
- The orchestrator resolves conflicts without repeating raw agent output verbatim
- Hierarchical costs one extra LLM call but eliminates fragmentation
- Confidence scores reveal which agents are most uncertain about the same headline

```bash
streamlit run module-6/hour22_lab_multiagent_basics.py
```

---

### `hour23_lab_orchestrator_workers.py` — Orchestrator-Workers Architecture

**Hour 23.** A central orchestrator decomposes a complex goal into a four-task list (one per typed worker),
each worker executes its task independently, and the orchestrator synthesises all results into an executive brief.

**The agents:**

| Agent | Colour | Role |
|-------|--------|------|
| Goal Decomposer | Purple | Returns JSON task list: `{goal_summary, tasks[{id, worker, instruction, priority}]}` |
| Research Worker | Green | Concrete facts, data points, market context (180–220 words) |
| Analysis Worker | Blue | Structured analysis, patterns, feasibility (180–220 words) |
| Writing Worker | Orange | Professional written deliverables, messaging (150–200 words) |
| Risk Worker | Red | 3–5 risks with severity and mitigation (180–220 words) |
| Synthesiser | Purple | Executive brief with `## Goal`, `## Key Findings`, `## Next Steps`, `## Feasibility Assessment` |

**What students do:**
1. View the orchestrator-workers architecture diagram (orchestrator → 4 workers → executive brief)
2. **Goal decomposition** — enter a complex goal; see orchestrator return a 4-task JSON list with priorities
3. **Worker execution** — each task dispatched to the appropriate typed worker; outputs shown in expanders
4. **Executive brief** — orchestrator synthesises all four worker outputs into a structured brief; token ledger displayed

**Key observations:**
- The orchestrator's output is a task list — not the answer itself
- Workers receive only their own task instruction, not the full goal or other workers' outputs
- The synthesiser must read all four outputs — context grows as pipeline progresses
- Token cost scales linearly: decomposer + 4 workers + synthesiser = 6 LLM calls total

```bash
streamlit run module-6/hour23_lab_orchestrator_workers.py
```

---

### `hour24_lab_agent_handoffs.py` — Agent Communication and Handoffs

**Hour 24.** A handoff package grows as it passes through three specialist agents in a Document Review Pipeline.
Section 3 demonstrates bidirectional clarification: an agent asks a clarifying question, a second agent answers,
and the first agent then completes the task with full context.

**The agents:**

| Agent | Colour | Role |
|-------|--------|------|
| Legal Agent | Blue | Extracts `clauses[]`, `jurisdiction`, `legal_notes` |
| Risk Agent | Red | Adds `risks[]`, `risk_score` (1–5), `risk_notes` |
| Recommendation Agent | Purple | Writes APPROVE / APPROVE WITH CONDITIONS / REJECT + rationale + action items |
| Clarifier | Teal | Returns JSON: `{needs_clarification, question, reason}` |
| Clarification Responder | Orange | Answers the clarifying question (1–3 sentences) |
| Task Completer | Blue | Completes the task using original request + clarification answer |

**What students do:**
1. View the sequential handoff pipeline diagram with growing state annotations per stage
2. **Document Review Pipeline** — paste a contract; see handoff package grow across Legal → Risk → Recommendation; expanders show state at each stage
3. **Bidirectional handoff** — enter a vague task; Clarifier decides if clarification is needed; if yes, Responder answers; Completer finishes with full context

**Key observations:**
- Each agent adds new fields to the handoff package — it never overwrites prior stages
- The Risk agent reads the Legal findings before assessing risk (builds on prior work)
- The Recommendation agent has the full picture of both prior stages
- Vague tasks trigger clarification; clear tasks complete without it (2 vs 3 LLM calls)

```bash
streamlit run module-6/hour24_lab_agent_handoffs.py
```

---

## Quick Start

```bash
# Install dependencies (from repo root)
python -m venv env
source env/bin/activate
pip install -r requirements.txt

# Create your API key file
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > module-6/.env

# Run any lab
streamlit run module-6/hour22_lab_multiagent_basics.py
streamlit run module-6/hour23_lab_orchestrator_workers.py
streamlit run module-6/hour24_lab_agent_handoffs.py
```

---

## Module 6 Concept Map

| Hour | Lab | Core concept | Agentic connection |
|------|-----|-------------|-------------------|
| 22 | Multi-Agent Basics | Flat vs hierarchical; coordination layer | Without a hierarchy, agents contradict each other — hierarchy resolves this by design |
| 23 | Orchestrator-Workers | Goal decomposition; typed workers; synthesis | The orchestrator's output is a task list, not the answer |
| 24 | Agent Handoffs | Growing state package; bidirectional clarification | Each agent enriches the package — the last agent has all prior intelligence |

---

## Colour Convention

| Colour | Hex | Used for |
|--------|-----|----------|
| Blue | `#1E88E5` | Executor / Technical / Generator |
| Orange | `#FB8C00` | Tools / Specialist / Worker |
| Green | `#43A047` | Memory / Retriever / Knowledge |
| Purple | `#8E24AA` | Planner / Orchestrator / Synthesiser |
| Teal | `#00897B` | Router / Classifier |
| Red | `#E53935` | Critic / Evaluator / Risk |

---

## Troubleshooting

- **AuthenticationError** → check that `module-6/.env` exists and contains `ANTHROPIC_API_KEY=sk-ant-...`
- **Hour 22: flat agents contradict each other** → this is expected and is the teaching point; run Section 3 to see the orchestrator resolve it
- **Hour 23: orchestrator assigns wrong worker type** → the goal decomposer may misroute on unusual goals; try a standard business goal from the presets
- **Hour 24: Legal agent returns incomplete JSON** → contract text may be too short; use a preset contract which provides enough clause content
- **Hour 24: clarification loop does not trigger** → a clear, specific task request will not trigger clarification; try a deliberately vague task like "write the report"
- **ModuleNotFoundError: claude_client** → run from the repo root with `streamlit run module-6/hour22_lab_multiagent_basics.py`, not from inside the `module-6/` folder
