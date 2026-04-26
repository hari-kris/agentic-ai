# Module 5 — Core Agentic Patterns II

**Course:** Agentic AI — A Professional 30-Hour Course  
**Module:** 5 of 9 | Duration: 5 hours (Hours 17–21)

---

## Before You Start — API Key Setup

Create a `.env` file inside the `module-5/` folder:

```
module-5/
├── .env        ← create this file
├── claude_client.py
├── hour17_lab_routing_pattern.py
├── hour18_lab_parallelisation_pattern.py
├── hour19_lab_orchestrator_subagents.py
├── hour20_lab_evaluator_optimizer.py
└── hour21_lab_combine_patterns.py
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

Shared helper used by all five labs. Not run directly.

- Loads `ANTHROPIC_API_KEY` from `.env`
- Exposes `chat(system, user, max_tokens, temperature)` → `(text, usage_dict)`
- Exposes `chat_with_tools(system, messages, tools, max_tokens)` → `(content_blocks, usage_dict)`
- Model: `claude-sonnet-4-6`

---

### `hour17_lab_routing_pattern.py` — Routing Pattern

**Hour 17.** A classifier agent reads each input and dispatches it to the most appropriate
sub-pipeline. Unlike prompt chaining (always linear), routing creates branching — different
inputs follow entirely different paths.

**The agents:**

| Agent | Colour | Role |
|-------|--------|------|
| Domain Router | Teal | Returns JSON: `{route, confidence, reason}` |
| Domain Specialists (×5) | Mixed | TECH / MEDICAL / FINANCE / LEGAL / GENERAL |
| Complexity Router | Teal | Returns JSON: `{complexity: "simple|complex", reason}` |
| Fast Path | Green | 1–3 sentence direct answer |
| Deep Path | Blue | 250–350 word thorough analysis |

**What students do:**
1. View the routing architecture diagram — router dispatching to 5 coloured specialist boxes
2. **Domain router** — enter any question; see the routing decision JSON with confidence score; the matching specialist answers; confidence below threshold escalates instead of routing
3. **Complexity router** — same question routes to fast path or deep path based on question difficulty; side-by-side path comparison
4. **Routing trace inspector** — full trace display showing raw JSON → confidence gate → specialist response for any input

**Key observations:**
- The router's only job is classification — it must not answer the question
- `confidence` is the machine-readable signal that drives fallback logic
- A confidence threshold of 0.6 means: below this, escalate rather than guess
- Two LLM calls (router + specialist) replace one generalised call, with better quality on each

```bash
streamlit run module-5/hour17_lab_routing_pattern.py
```

---

### `hour18_lab_parallelisation_pattern.py` — Parallelisation Pattern

**Hour 18.** Fan-out sends the same input to multiple agents simultaneously.
Voting sends the same task to N agents and tallies agreement. Both patterns improve
quality: fan-out through coverage, voting through reliability.

**The two sub-types:**

| Sub-type | Agents | How results combine |
|----------|--------|-------------------|
| Fan-out | Specialist A + B + C | Aggregator synthesises all three |
| Voting | Agent × N (same role) | Vote classifier tallies agreement |

**What students do:**
1. View the fan-out architecture diagram
2. **Document fan-out** — paste a document; Summarizer, Risk Analyst, and Opportunity Analyst all analyse it; Aggregator synthesises a comprehensive assessment
3. **Code review fan-out** — paste Python code; Security, Performance, and Readability reviewers analyse simultaneously; Lead Reviewer delivers a consolidated review
4. **Voting consensus** — ask a question; 3 agents at different temperatures answer independently; Vote Classifier reports agreement rate, majority answer, and what agents disagree about

**Key observations:**
- Each specialist produces deeper output than a generalist covering all dimensions
- The aggregator catches conflicts between specialists — risk analyst says "risky", opportunity analyst says "strong buy"
- Voting agreement rate is a confidence signal — 3/3 agreement is reliable; 2/3 needs scrutiny
- Token cost: N specialist calls + 1 aggregator call

```bash
streamlit run module-5/hour18_lab_parallelisation_pattern.py
```

---

### `hour19_lab_orchestrator_subagents.py` — Orchestrator-Subagents Pattern

**Hour 19.** An orchestrator dynamically decides which subagents to spawn and what to assign
each one. Unlike parallelisation (fixed agent set), an orchestrator reads the task and
assembles the appropriate team — adapting to what the input actually needs.

**The agents:**

| Agent | Colour | Role |
|-------|--------|------|
| Research Orchestrator | Purple | Decomposes question → 2–3 sub-questions → assigns researchers → synthesises |
| Researcher Subagents | Blue/Green/Red | Each answers one focused sub-question |
| Research Synthesiser | Teal | Integrates sub-findings into a final report |
| Doc Type Router | Teal | Classifies document into 5 types |
| Doc Processors (×5) | Mixed | TECHNICAL / BUSINESS / NEWS / LEGAL / ACADEMIC |
| Quality Assessor | Red | Scores subagent output: `depth` + `completeness` (1–5) |

**What students do:**
1. View the orchestrator architecture diagram — dynamic subagent assembly
2. **Research orchestrator** — enter a research question; orchestrator decomposes it, assigns 2–3 researchers, synthesises a final report; see each subagent's task brief and output
3. **Document processor** — paste a document; orchestrator detects type and routes to the matching specialist processor; 5 type-matched processors
4. **Quality-gated re-delegation** — orchestrator assesses subagent output quality; if below threshold, re-delegates with richer instructions; see the quality gate in action across multiple attempts

**Key observations:**
- The orchestrator does not do the work — it coordinates, delegates, and synthesises
- Each subagent receives only the context it needs — not the full goal or other subagents' outputs
- Re-delegation adds API calls but catches low-quality outputs before they reach the final report
- Orchestration is adaptive; planning is static — use orchestration when the best approach depends on intermediate results

```bash
streamlit run module-5/hour19_lab_orchestrator_subagents.py
```

---

### `hour20_lab_evaluator_optimizer.py` — Evaluator-Optimizer Pattern

**Hour 20.** A generator produces output. An evaluator scores it against specific criteria.
An optimizer improves it. The loop terminates when all criteria meet the threshold or
a maximum round count is reached — no wasted rounds when quality is already good.

**The three agents:**

| Agent | Colour | Role |
|-------|--------|------|
| Generator | Blue | Creates initial output from task description |
| Evaluator | Red | Returns JSON scores on domain-specific criteria (1–5) + actionable feedback |
| Optimizer | Purple | Rewrites output targeting low-score criteria, preserving high ones |

**Two domains:**

| Domain | Criteria scored |
|--------|----------------|
| Code quality | `correctness`, `efficiency`, `style`, `documentation` |
| Prompt quality | `clarity`, `specificity`, `constraints`, `format` |

**What students do:**
1. View the loop diagram — Generator → Evaluator → threshold gate → Optimizer → back to Evaluator
2. **Code quality loop** — describe a coding task; generator writes Python; loop improves it until all criteria reach the threshold or max rounds hit; see score progression per round
3. **Prompt quality loop** — describe a rough agent task; generator writes a system prompt; loop improves it until prompt engineering criteria are met; side-by-side initial vs final prompt
4. **Convergence analysis** — see which criteria improved, which plateaued; plateau detection guidance

**Key observations:**
- The evaluator must be strict — a lenient evaluator gives the optimizer no improvement signal
- The optimizer must preserve high-scoring dimensions while fixing low ones — blind "improvement" can regress what was already good
- A plateau (delta < 0.3 between rounds) is the signal to stop — not the max round count
- This pattern differs from Reflection: here, the threshold controls termination, not a fixed round count

```bash
streamlit run module-5/hour20_lab_evaluator_optimizer.py
```

---

### `hour21_lab_combine_patterns.py` — Capstone: Combine Patterns II

**Hour 21.** The capstone lab for Module 5. Combines all four Module 5 patterns in a
Smart Content Analysis Pipeline that adapts to the input type and quality-gates its output.

**Pipeline:**
```
User content input
    ↓
[ROUTER] (Routing) → classifies content type (TECHNICAL/BUSINESS/NEWS/SCIENTIFIC)
    ↓
[SPECIALISTS × 3] (Parallelisation) → 3 domain-matched specialists analyse in parallel
    ↓
[ORCHESTRATOR] (Orchestrator-Subagents) → synthesises specialist outputs into structured draft
    ↓
[EVALUATOR-OPTIMIZER] (Evaluator-Optimizer) → improves draft until quality threshold met
    ↓
Final Report
```

**What students do:**
1. View the architecture diagram — full 4-stage pipeline with pattern labels
2. **Run the pipeline** — paste content; one button executes all stages with a live progress bar
3. **Stage-by-stage results** — 5 tabs: Router Decision | Specialists | Orchestrator Draft | Evaluator Loop | Final Report
4. **Pattern attribution panel** — 4 coloured cards explaining which pattern drove each stage and why
5. **Token ledger** — per-stage breakdown (Router / Specialists ×3 / Orchestrator / Eval-Optimizer) + grand total

**Key observations:**
- The router's classification determines which specialists run — routing shapes the entire pipeline
- The orchestrator is the costliest single call because it receives all 3 specialist outputs as context
- The evaluator-optimizer adds quality assurance automatically — the pipeline self-corrects
- Total cost is higher than any single pattern; the quality gain justifies the cost for high-stakes content

```bash
streamlit run module-5/hour21_lab_combine_patterns.py
```

---

## Quick Start

```bash
# 1. Install dependencies (once, from repo root)
pip install -r requirements.txt

# 2. Create .env inside module-5/
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > module-5/.env

# 3. Run any lab
streamlit run module-5/hour17_lab_routing_pattern.py
streamlit run module-5/hour18_lab_parallelisation_pattern.py
streamlit run module-5/hour19_lab_orchestrator_subagents.py
streamlit run module-5/hour20_lab_evaluator_optimizer.py
streamlit run module-5/hour21_lab_combine_patterns.py
```

---

## Module 5 Concept Map

| Hour | Lab | Core concept | Agentic connection |
|------|-----|-------------|-------------------|
| 17 | Routing Pattern | Confidence-gated dispatch; structured routing JSON | The router never answers — separation of classification from execution |
| 18 | Parallelisation | Fan-out to specialists; voting consensus | N specialists in parallel beats one generalist covering N dimensions |
| 19 | Orchestrator-Subagents | Dynamic team assembly; quality-gated re-delegation | Orchestration is adaptive; subagents are focused and isolated |
| 20 | Evaluator-Optimizer | Domain-specific criteria; threshold-gated loop | Terminate on quality, not on round count — plateau detection saves tokens |
| 21 | Combine Patterns II | All four patterns in one adaptive pipeline | Routing + parallelisation + orchestration + evaluation compose cleanly |

---

## Colour Convention (consistent across all modules)

| Colour | Hex | Used for |
|--------|-----|----------|
| Blue | `#1E88E5` | Generator / Executor / Technical specialist |
| Orange | `#FB8C00` | Tools / Specialist |
| Green | `#43A047` | Researcher / Knowledge / Fast Path |
| Purple | `#8E24AA` | Planner / Orchestrator / Refiner |
| Teal | `#00897B` | Router / classifier agents |
| Red | `#E53935` | Critic / Evaluator / Risk Analyst |

---

## Troubleshooting

**`AuthenticationError`** → Check `.env` is inside `module-5/` and the key starts with `sk-ant-`

**Hour 17 router always returns GENERAL** → Ensure the question clearly indicates a domain. Vague or very short questions tend to route to GENERAL. Try a more specific question with domain-specific vocabulary.

**Hour 18 vote classifier parse error** → The Vote Classifier returns JSON. If Claude adds markdown fences, the app strips them automatically. If it still fails, the raw output is shown — check the response format.

**Hour 19 orchestrator returns only 1 sub-question** → The Research Orchestrator is prompted to return 2–3 sub-questions. If it returns fewer, the question may already be very narrow. Try a broader research question.

**Hour 20 optimizer regresses scores** → This is expected behaviour when criteria are in conflict. The convergence analysis section explains plateau detection — if scores are not improving after round 1, reducing max rounds saves tokens without quality loss.

**Hour 21 Token Ledger shows 0 for a stage** → This means that stage did not execute (likely a parse error in an earlier stage). Check the Stage-by-Stage Results tabs for error messages in the affected stage.

---

*Module 5 of 9 | Agentic AI — A Professional 30-Hour Course*
