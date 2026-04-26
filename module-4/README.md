# Module 4 — Core Agentic Patterns I

**Course:** Agentic AI — A Professional 30-Hour Course  
**Module:** 4 of 9 | Duration: 5 hours (Hours 12–16)

---

## Before You Start — API Key Setup

Create a `.env` file inside the `module-4/` folder:

```
module-4/
├── .env        ← create this file
├── claude_client.py
├── hour12_lab_reflection_pattern.py
├── hour13_lab_tool_use_pattern.py
├── hour14_lab_planning_pattern.py
├── hour15_lab_prompt_chaining.py
└── hour16_lab_combine_patterns.py
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

The `chat_with_tools()` function is required by Hour 13 (Tool Use). All other labs use `chat()`.

---

### `hour12_lab_reflection_pattern.py` — Reflection Pattern

**Hour 12.** A generator produces output, a critic scores it, and a refiner improves it.
The Reflection pattern closes the quality loop between generation and evaluation.

**The three agents:**

| Agent | Colour | Role |
|-------|--------|------|
| Generator | Blue | Writes the initial draft from a task description |
| Critic | Red | Returns JSON scores: `clarity`, `accuracy`, `tone`, `completeness` (1–5) + `feedback` |
| Refiner | Purple | Rewrites the draft to address the specific critique |

**What students do:**
1. View the pipeline diagram — 3 agent cards with data flow arrows
2. **Single reflection round** — enter a writing task; run one Generator → Critic → Refiner cycle; see before/after side-by-side with colour-coded score bars
3. **Multi-round loop** — slider 1–3 rounds; each round feeds the previous refined draft back through the Critic and Refiner; watch scores improve across rounds

**Key observations:**
- The Critic returns structured JSON — scores must be machine-readable to drive the Refiner's prompt
- A separate critic with its own system prompt catches flaws that a combined generate+critique prompt misses
- Score progression across rounds often plateaus — more rounds don't always mean better output

```bash
streamlit run module-4/hour12_lab_reflection_pattern.py
```

---

### `hour13_lab_tool_use_pattern.py` — Tool Use Pattern

**Hour 13.** An agent calls external functions to act on the world. This lab shows how Claude decides when to call a tool, how results are returned, and how multi-tool agents handle compound queries.

**The two tools:**

| Tool | What it does |
|------|-------------|
| `calculate(expression)` | Evaluates a maths expression safely via AST parsing |
| `search_knowledge(query)` | Searches a 10-item hardcoded knowledge base; returns top-2 matching chunks |

**What students do:**
1. **Schema explorer** — view the JSON tool schemas that Claude receives
2. **Calculator tool** — ask a maths question; see the tool_use block, execution, tool_result, and final answer
3. **Knowledge search tool** — ask a question; watch Claude issue a search, receive chunks, and synthesise an answer
4. **Multi-tool agent** — both tools active; compound questions that require both tools in one session

**Key observations:**
- The tool call loop: Claude returns a `tool_use` block → Python executes → `tool_result` injected → Claude finalises
- `chat_with_tools()` returns `content_blocks` — each block has `type: "text"` or `type: "tool_use"`
- Safe math evaluation uses AST node allowlisting, not raw `eval()`

```bash
streamlit run module-4/hour13_lab_tool_use_pattern.py
```

---

### `hour14_lab_planning_pattern.py` — Planning Pattern

**Hour 14.** A planner decomposes a high-level goal into structured, actionable subtasks.
Executor agents then carry each task out — often independently, sometimes in parallel.

**The three agents:**

| Agent | Colour | Output |
|-------|--------|--------|
| Sequential Planner | Purple | JSON `{steps: [{id, title, description, effort}], rationale}` |
| Parallel Planner | Purple | Adds `parallel_groups: [[1,2],[3],[4,5]]` to identify concurrent steps |
| Plan Critic | Red | JSON `{gaps, risks, suggestion}` |

**What students do:**
1. **Sequential planner** — enter a goal; get 5 ordered steps with effort badges (low/medium/high)
2. **Sequential vs parallel** — run the same goal through both planners; see parallel groups highlighted
3. **Plan critique** — generate a plan, then run it through the Critic to find gaps and risks before execution

**Key observations:**
- A planner that can't return valid JSON is not composable — strict output format is essential
- The parallel planner identifies which steps have no dependencies and can run simultaneously
- A plan critic costs one extra API call but prevents executing a flawed plan

```bash
streamlit run module-4/hour14_lab_planning_pattern.py
```

---

### `hour15_lab_prompt_chaining.py` — Prompt Chaining Pattern

**Hour 15.** Each LLM call's output becomes the next call's input. A 3-stage pipeline
transforms a topic into a fully written article through three specialised stages.

**The three stages:**

| Stage | Colour | Transformation |
|-------|--------|----------------|
| Researcher | Green | Topic → 6–8 specific bullet-point facts |
| Outliner | Purple | Topic + facts → structured article outline (H2 headings + subpoints) |
| Drafter | Blue | Topic + facts + outline → full 300–400 word article |

**What students do:**
1. **Chain diagram** — visualise the three agents and how information grows at each stage
2. **3-stage pipeline** — choose a topic; watch the chain execute with a live progress bar; see each stage's output in an expander
3. **Chain inspection** — side-by-side view of what each stage received vs what it produced (input vs output per stage)

**Key observations:**
- Each stage narrows and transforms information; the Drafter's input is far larger than the Researcher's
- Token cost grows per stage — Stage 3 inherits all prior outputs as context
- The Researcher focuses on facts; the Outliner on structure; the Drafter on prose — each role is focused

```bash
streamlit run module-4/hour15_lab_prompt_chaining.py
```

---

### `hour16_lab_combine_patterns.py` — Capstone: Combine All Four Patterns

**Hour 16.** The capstone lab for Module 4. Combines all four patterns in a single research assistant pipeline.

**Pipeline:**
```
User research goal
    ↓
[PLANNER] (Planning) → 3-step research plan
    ↓
[SEARCHER × 3] (Tool Use) → facts per plan step
    ↓
[DRAFTER] (Prompt Chaining) → full draft from plan + facts
    ↓
[CRITIC] (Reflection) → JSON quality scores
    ↓
[REFINER] → final improved report
```

**What students do:**
1. View the architecture diagram — full pipeline with pattern labels at each stage
2. **Run the pipeline** — enter a research goal; one button runs all stages with a live progress bar
3. **Stage-by-stage results** — tabbed view: Plan | Search Results | Draft | Critique | Final Report
4. **Pattern attribution panel** — 4 coloured cards showing which pattern drove each stage
5. **Token ledger** — per-stage and grand total; shows the cost of combining patterns

**Key observations:**
- Planning determines research quality — a good plan leads to focused, useful search results
- Tool use grounds the draft in actual retrieved facts, not hallucinated ones
- The Reflection loop improves the draft quality after it is written
- Total token cost is significantly higher than any single pattern — combining patterns is not free

```bash
streamlit run module-4/hour16_lab_combine_patterns.py
```

---

## Quick Start

```bash
# 1. Install dependencies (once, from repo root)
pip install -r requirements.txt

# 2. Create .env inside module-4/
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > module-4/.env

# 3. Run any lab
streamlit run module-4/hour12_lab_reflection_pattern.py
streamlit run module-4/hour13_lab_tool_use_pattern.py
streamlit run module-4/hour14_lab_planning_pattern.py
streamlit run module-4/hour15_lab_prompt_chaining.py
streamlit run module-4/hour16_lab_combine_patterns.py
```

---

## Module 4 Concept Map

| Hour | Lab | Core concept | Agentic connection |
|------|-----|-------------|-------------------|
| 12 | Reflection Pattern | Generator → Critic → Refiner loop | Structured critique output makes quality improvement composable |
| 13 | Tool Use Pattern | Tool schemas; tool call loop; safe execution | Tool use extends an agent from text-only to acting on the world |
| 14 | Planning Pattern | Sequential vs parallel plans; plan critique | A planner that can't return JSON can't be integrated into a pipeline |
| 15 | Prompt Chaining | Stage-by-stage output injection; token growth | Each stage should do one transformation — chaining beats an all-in-one prompt |
| 16 | Combine Patterns I | All four patterns in one pipeline | Patterns compose; each removes a specific class of failure |

---

## Colour Convention (consistent across all modules)

| Colour | Hex | Used for |
|--------|-----|----------|
| Blue | `#1E88E5` | Generator / Executor / Drafter |
| Orange | `#FB8C00` | Tools / tool call traces |
| Green | `#43A047` | Researcher / Knowledge / Memory |
| Purple | `#8E24AA` | Planner / Refiner / Orchestrator |
| Teal | `#00897B` | Router |
| Red | `#E53935` | Critic / Evaluator |

---

## Troubleshooting

**`AuthenticationError`** → Check `.env` is inside `module-4/` and the key starts with `sk-ant-`

**Hour 13 `chat_with_tools` import error** → Ensure you are using the `module-4/claude_client.py` — it adds `chat_with_tools()`. The `module-3` client does not have this function.

**Hour 14 planner returns parse error** → The planner is instructed to return JSON with no markdown fences. If it still fails, check you have not edited the system prompt to remove the JSON format instruction. The fallback shows the raw output.

**Hour 16 search returns no results** → The knowledge base is hardcoded with 12 items on specific topics. Try a research goal closely related to: remote work, electric vehicles, the internet, AI, climate change, or renewable energy.

**Token metrics show 0** → The `usage_dict` is returned by `chat()` as `{"input_tokens": N, "output_tokens": N}`. If metrics show 0, the call may have failed silently — check the Streamlit terminal output for API errors.

---

*Module 4 of 9 | Agentic AI — A Professional 30-Hour Course*
