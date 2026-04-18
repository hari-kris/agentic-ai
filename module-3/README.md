# Module 3 — Agent Types and Components

**Course:** Agentic AI — A Professional 30-Hour Course  
**Module:** 3 of 9 | Duration: 4 hours (Hours 8–11)

---

## Before You Start — API Key Setup

Create a `.env` file inside the `module-3/` folder:

```
module-3/
├── .env        ← create this file
├── claude_client.py
├── hour8_lab_agent_components.py
├── hour9_lab_agent_types_i.py
├── hour10_lab_agent_types_ii.py
└── hour11_lab_implement_two_agents.py
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

Shared helper used by all four labs. Not run directly.

- Loads `ANTHROPIC_API_KEY` from `.env`
- Exposes `chat(system, user, max_tokens, temperature)` → `(text, usage_dict)`
- Model: `claude-sonnet-4-6`

---

### `hour8_lab_agent_components.py` — Agent Components Workshop

**Hour 8.** Every agent is built from four core components. This lab makes each one tangible and testable.

**The four components:**

| Component | Colour | What it is | Maps to |
|-----------|--------|-----------|---------|
| Persona | Blue | Who the agent is — identity, expertise, constraints | `system` parameter |
| Knowledge | Green | What the agent knows — injected context, retrieved data | Context in `user` message |
| Tools | Orange | What the agent can do — external functions it can call | `tools` parameter |
| Interaction Layer | Purple | How the agent communicates — output format and style | Format instructions in system prompt |

**What students do:**
1. Read the component gallery — one card per component with definition and code mapping
2. **Annotate an agent** — a real agent config is split into 4 segments; students label each one (guess-then-reveal with scoring)
3. **Build your own agent** — fill in all four components as editable text areas; click Assemble & Run to see the assembled system prompt sent to Claude

**Key learning:** Every agentic framework (LangChain, LangGraph, raw API) uses these same four components under different names. Recognising them lets you read any agent code immediately.

```bash
streamlit run module-3/hour8_lab_agent_components.py
```

---

### `hour9_lab_agent_types_i.py` — Agent Types I: Router, Planner, Executor, Critic

**Hour 9.** Four fundamental agent types — each with a single, distinct role.

**The four types:**

| Type | Colour | Role | Input → Output |
|------|--------|------|----------------|
| Router | Teal | Classifies input, directs to correct handler | Request → Label |
| Planner | Purple | Decomposes goals into ordered steps | Goal → Step list |
| Executor | Blue | Carries out a single concrete task | Task → Result |
| Critic | Red | Evaluates output against criteria | Output → Scores + Feedback |

**What students do:**
1. Read the agent type gallery — definition, analogy, I/O shape, and when to use each
2. **Live comparison** — enter any input; click Run All Four to send it to all four agent types simultaneously and see how each agent's role shapes its response differently
3. **Task mapping quiz** — 5 real-world task descriptions; pick the correct agent type and write a justification; Claude evaluates both the selection and the reasoning

**Key learning:** Each agent type is describable in one sentence starting with a verb. If your description needs two verbs and "and", you have two agents masquerading as one.

```bash
streamlit run module-3/hour9_lab_agent_types_i.py
```

---

### `hour10_lab_agent_types_ii.py` — Agent Types II: Retriever, Orchestrator, Specialist

**Hour 10.** Three more agent types that connect and extend the first four.

**The three types:**

| Type | Colour | Analogy | Role |
|------|--------|---------|------|
| Retriever | Green | Librarian | Searches a knowledge base; returns relevant context — does not answer |
| Orchestrator | Purple | Project manager | Coordinates specialists, delegates sub-tasks, synthesises results |
| Specialist | Orange | Domain expert consultant | Deep, focused work in a narrow domain — high quality, limited scope |

**What students do:**
1. Read the type overview cards
2. **Retriever demo** — query a 6-chunk knowledge base about a fictional SaaS product (Nexara); watch the Retriever select relevant chunks and pass only those to an Answerer agent
3. **Orchestrator demo** — enter a document analysis task; watch a 4-stage pipeline: Orchestrator → Summariser specialist → Risk Analyst specialist → Synthesiser
4. **Team designer** — fill in role cards for a 3-agent team (name, type, responsibilities, receives, outputs); Claude validates completeness, role clarity, and output coherence (scores 1–5 each)

**Key learning:** A Specialist outperforms a Generalist on its domain tasks because its system prompt, context, and output format are all tuned for one problem. The Orchestrator pays for itself by making each Specialist better.

```bash
streamlit run module-3/hour10_lab_agent_types_ii.py
```

---

### `hour11_lab_implement_two_agents.py` — Implement Two Agent Types

**Hour 11.** The capstone lab for Module 3. Students build and test a Router agent and a Critic agent from scratch — both with editable system prompts and structured test cases.

**Tab A — Router Agent**

Build a router that classifies support requests into TECHNICAL / BILLING / GENERAL and activates the appropriate specialist.

Pipeline:
```
User Input → [ROUTER] → Route label → [SPECIALIST] → Final response
```

What students do:
- Edit the Router system prompt (pre-filled with a working default)
- Click Run All 3 Preset Inputs — each runs the full chain: router decision → specialist response
- Test a custom input of their own
- Read the results summary: route label, confidence %, token counts per stage

Key observations:
- The Router returns JSON — machine-readable routes, not prose
- Confidence < 0.6 signals an ambiguous input that should escalate or fall back
- The specialist never sees the routing logic — only its own task

**Tab B — Critic Agent**

Build a generator-critic-rewriter pipeline with 4 evaluation criteria.

Pipeline:
```
Topic → [GENERATOR] → Draft → [CRITIC] → Scores + Feedback → [REWRITER] → Improved draft
```

What students do:
- Pick content type (blog post, email, code explanation, etc.) and target audience
- Edit the Generator, Critic, and Rewriter system prompts (pre-filled with strong defaults)
- Click Run — all three stages execute in sequence
- See scores for accuracy / clarity / tone / completeness (each 1–5) as colour-coded cards with progress bars
- Compare original draft vs rewritten draft side-by-side

Key observations:
- The Critic returns JSON — scores must be machine-readable to trigger a conditional rewrite
- Feedback quality drives rewrite quality — vague feedback → generic changes
- A critic without structured output cannot be composed with other agents

```bash
streamlit run module-3/hour11_lab_implement_two_agents.py
```

---

## Quick Start

```bash
# 1. Install dependencies (once, from repo root)
pip install -r requirements.txt

# 2. Create .env inside module-3/
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > module-3/.env

# 3. Run any lab
streamlit run module-3/hour8_lab_agent_components.py
streamlit run module-3/hour9_lab_agent_types_i.py
streamlit run module-3/hour10_lab_agent_types_ii.py
streamlit run module-3/hour11_lab_implement_two_agents.py
```

---

## Module 3 Concept Map

| Hour | Lab | Core concept | Agentic connection |
|------|-----|-------------|-------------------|
| 8 | Agent Components | Persona · Knowledge · Tools · Interaction Layer | These four components are present in every agent regardless of framework |
| 9 | Agent Types I | Router · Planner · Executor · Critic | One agent, one role — composability comes from specialisation |
| 10 | Agent Types II | Retriever · Orchestrator · Specialist | Multi-agent teams delegate; specialists go deep where generalists cannot |
| 11 | Implement Two Agents | Router + Critic end-to-end | Structured output (JSON) is what makes agents composable in a pipeline |

---

## Colour Convention (consistent across all modules)

| Colour | Hex | Used for |
|--------|-----|----------|
| Blue | `#1E88E5` | Executor / Technical / Persona component |
| Orange | `#FB8C00` | Tools / Specialist / tool-use |
| Green | `#43A047` | Memory / Retriever / Knowledge component |
| Purple | `#8E24AA` | Planner / Orchestrator / Interaction Layer |
| Teal | `#00897B` | Router |
| Red | `#E53935` | Critic / Evaluator |

---

## Troubleshooting

**`AuthenticationError`** → Check `.env` is inside `module-3/` and the key starts with `sk-ant-`

**Hour 9 or 10 quiz evaluation fails** → The quiz evaluator calls Claude with a structured prompt. If it returns a parse error, the app falls back to a direct comparison. Check your internet connection and API key.

**Hour 10 Orchestrator returns parse error** → The Orchestrator prompt returns JSON. If Claude adds markdown fences, the app strips them automatically. If it still fails, check you have not edited the Orchestrator system prompt to remove the JSON format instruction.

**Hour 11 Critic scores all 0** → The Critic prompt must return valid JSON with the exact keys (`accuracy`, `clarity`, `tone`, `completeness`, `feedback`). If you edited the Critic prompt, check the return format instruction is intact.

**Hour 11 Router always routes to GENERAL** → Check the Router system prompt lists all three categories (TECHNICAL, BILLING, GENERAL) in uppercase exactly as shown. The Python code matches on `.upper()` of the returned route label.

---

*Module 3 of 9 | Agentic AI — A Professional 30-Hour Course*
