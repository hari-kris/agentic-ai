# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A professional 30-hour Agentic AI course (9 modules). Each module is a self-contained set of interactive Streamlit labs that call the Claude API to teach agentic AI concepts hands-on. Modules completed so far: `module_1/` (Hours 1–3), `module-2/` (Hours 4–7), `module-3/` (Hours 8–11), `module-4/` (Hours 12–16), `module-5/` (Hours 17–21).

Note: `module_1` uses underscores; `module-2` through `module-5` use hyphens. This is intentional.

## Running labs

Every interactive lab is a Streamlit app:

```bash
streamlit run module_1/hour1_lab_agentic_classifier.py
streamlit run module-2/hour4_lab_prompt_anatomy.py
streamlit run module-3/hour8_lab_agent_components.py
streamlit run module-4/hour12_lab_reflection_pattern.py
streamlit run module-5/hour17_lab_routing_pattern.py
```

Jupyter notebooks (reference material) run via:

```bash
jupyter notebook module_1/Module1_Lab_AgenticAI.ipynb
```

There are no tests, no build step, and no linter configured.

## Environment and dependencies

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

Each module reads its API key from its **own** `.env` file (not the repo root):

```
module_1/.env
module-2/.env
module-3/.env
module-4/.env
module-5/.env
```

Each `.env` contains one line: `ANTHROPIC_API_KEY=sk-ant-...`

## Architecture

### `claude_client.py` — shared per module

Each module has its own `claude_client.py` (not shared across modules). It:
- Loads `ANTHROPIC_API_KEY` from `.env` via `python-dotenv`
- Exposes `chat(system, user, max_tokens, temperature) → (text, usage_dict)`
- Hardcodes `MODEL = "claude-sonnet-4-6"`

Modules 4 and 5 extend `claude_client.py` with an additional function:
- `chat_with_tools(system, messages, tools, max_tokens) → (content_blocks, usage_dict)`
- `content_blocks` is a list of dicts with `type: "text"` or `type: "tool_use"` entries
- Required for any lab that uses Claude's function-calling / tool use feature

All labs in a module import `from claude_client import chat`. Tool-use labs also import `chat_with_tools`.

### Lab structure pattern

Labs are single-file Streamlit apps. The typical structure:
1. `st.set_page_config` + title/caption
2. Sidebar with instructions and experiment suggestions
3. Editable system prompt text areas with reset buttons (stored in `st.session_state`)
4. A run button that calls `chat()` one or more times in sequence
5. Structured JSON parsing from Claude responses (with `.removeprefix("```json")` stripping)
6. Token usage metrics displayed after each API call

### Agent type taxonomy used throughout the course

| Type | Role |
|------|------|
| Router | Classifies input → route label (returns JSON) |
| Planner | Decomposes goal → ordered step list |
| Executor | Carries out one concrete task |
| Critic / Evaluator | Scores output against criteria (returns JSON with numeric scores + feedback) |
| Retriever | Selects relevant chunks from a knowledge base; does not answer |
| Orchestrator | Coordinates specialists, synthesises results |
| Specialist | Deep focused work in a narrow domain |

### Colour convention (consistent across all modules)

| Colour | Hex | Used for |
|--------|-----|----------|
| Blue | `#1E88E5` | Executor / Technical / Persona |
| Orange | `#FB8C00` | Tools / Specialist |
| Green | `#43A047` | Memory / Retriever / Knowledge |
| Purple | `#8E24AA` | Planner / Orchestrator / Interaction Layer |
| Teal | `#00897B` | Router |
| Red | `#E53935` | Critic / Evaluator |

### Why Claude responses must return JSON

Agents that route or evaluate must return machine-readable JSON so Python can branch deterministically. Every lab that parses structured output uses the same stripping pattern before `json.loads()`:

```python
clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
data = json.loads(clean)
```

## Quiz app

`quiz/app.py` is a standalone Streamlit app (separate from the module labs). Run with:

```bash
streamlit run quiz/app.py
```
