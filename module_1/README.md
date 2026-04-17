# Module 1 — Agentic AI Foundations

**Course:** Agentic AI — A Professional 30-Hour Course  
**Module:** 1 of 9 | Duration: 3 hours

---

## Before You Start — API Key Setup

All labs in this module call the **Claude API** (Anthropic). You need an API key.

### Step 1 — Create a `.env` file

Create a file named `.env` inside the `module_1/` folder:

```
module_1/
├── .env                ← create this file here
├── claude_client.py
├── hour1_lab_agentic_classifier.py
├── ...
```

### Step 2 — Add your API key

Open `.env` and add this single line:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

Replace `sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx` with your actual key from [console.anthropic.com](https://console.anthropic.com).

> **Important:** Never commit your `.env` file to git. It contains a secret key.  
> A `.gitignore` entry for `.env` is already present in the repo root.

---

## File Reference

### `claude_client.py` — Shared API Wrapper

A lightweight helper used by all three Streamlit labs. You do not run this file directly.

**What it does:**
- Loads your `ANTHROPIC_API_KEY` from the `.env` file
- Exposes a single `chat(system, user)` function that calls Claude and returns `(response_text, usage_dict)`
- All labs import from this file

---

### `hour1_lab_agentic_classifier.py` — Is This Agentic?

**Hour 1 exercise.** Students submit a description of an AI app or product. Claude scores it against the **four agentic properties** (goal-directed, tool-using, iterative, memory-aware) and returns a verdict.

**Key learning:** Understanding what makes a system agentic vs. a standard LLM call.

**Features:**
- Pre-loaded examples (ChatGPT, Copilot Workspace, Perplexity Deep Research, etc.)
- Student makes a guess *before* Claude reveals its verdict
- Raw prompt sent to Claude is visible in an expander — no black box
- Token usage displayed after each call

**How to run:**
```bash
cd module_1
streamlit run hour1_lab_agentic_classifier.py
```

---

### `hour2_lab_architecture_visualizer.py` — Architecture Visualizer

**Hour 2 exercise.** Students describe a system in plain English. Claude returns structured JSON identifying which of the **six core components** are present (Model, Tools, Memory, Planner, Executor, Evaluator).

**Key learning:** Recognising agentic components in any system description.

**Features:**
- Colour-coded component cards matching the course colour convention (blue = Model, orange = Tools, green = Memory, purple = Planner, teal = Executor, red = Evaluator)
- Agentic completeness score (0–6)
- Raw JSON output visible in an expander
- Pre-loaded example: a web-search research agent

**How to run:**
```bash
cd module_1
streamlit run hour2_lab_architecture_visualizer.py
```

---

### `hour3_lab_agentic_pipeline.py` — Your First Agentic Pipeline

**Hour 3 lab (core lab).** A fully visible two-step agentic pipeline. Each LLM call is rendered as a labelled, bordered block so students can see exactly how state flows between components.

**Key learning:** Implementing the Planner → State → Executor → Evaluator pattern in code.

**Pipeline stages:**

| Stage | LLM call? | What it does |
|---|---|---|
| 🟣 PLANNER | Yes — Call 1 | Generates a 4-step numbered plan from the goal |
| ⚙️ STATE | No | Python parses the plan and extracts individual steps |
| 🟢 EXECUTOR | Yes — Call 2+ | Executes one or more steps from the plan |
| 🔴 EVALUATOR | Optional | Critiques the final output and suggests one improvement |

**Exercises (controlled via the sidebar):**

| Exercise | What to do | What it demonstrates |
|---|---|---|
| Exercise 1 | Run as-is (1 step) | Two separate LLM calls, state passing between them |
| Exercise 2 | Set "Steps to execute" = 2 | Third LLM call; context from step 1 passed to step 2 |
| Exercise 3 | Enable "Add Evaluator" | A fourth LLM call critiques the output against the goal |

**How to run:**
```bash
cd module_1
streamlit run hour3_lab_agentic_pipeline.py
```

---

### `hour1b_lab_single_vs_agentic.py` — Single-Turn vs Agentic (Bonus Lab)

**Hour 1 bonus.** The same goal is handled two ways simultaneously. Left column: one Claude call, direct answer. Right column: Planner → Executor → Evaluator pipeline filling in stage by stage. A 4th Claude call scores both outputs on completeness, depth, and actionability.

**Key learning:** The cost vs quality trade-off of agentic systems — empirically, not theoretically.

**How to run:**
```bash
streamlit run module_1/hour1b_lab_single_vs_agentic.py
```

---

### `hour2b_lab_system_prompt_roles.py` — System Prompt Role Lab (Bonus Lab)

**Hour 2 bonus.** Three editable columns — Planner / Executor / Evaluator — each pre-filled with the canonical system prompt from Hour 3. Students edit any prompt and hit Run. The same model produces completely different output based solely on the system prompt.

**Key learning:** System prompt = agent identity. The model is not the agent; the system prompt defines what role it plays.

**How to run:**
```bash
streamlit run module_1/hour2b_lab_system_prompt_roles.py
```

---

### `hour3b_lab_context_window_inspector.py` — Context Window Inspector (Bonus Lab)

**Hour 3 bonus.** Runs the same pipeline as Hour 3 but exposes the exact JSON messages array sent to Claude at every step. A context fill bar shows `X / 200,000 tokens used`. A toggle switches between Chained (prior outputs included) and Isolated (fresh context each step) — token counts diverge visibly.

**Key learning:** Short-term memory IS the messages list. It is a Python list of dicts that grows with every step.

**How to run:**
```bash
streamlit run module_1/hour3b_lab_context_window_inspector.py
```

---

### `temperature_explorer.py` — Temperature Explorer (Bonus Lab)

**Bonus exercise.** One prompt, multiple panels, each running at a different temperature. Students adjust temperature sliders and compare outputs side-by-side to understand how randomness affects Claude's responses.

**Key learning:** How temperature controls creativity vs. consistency, and which agentic components should use low vs. high temperature.

**Features:**
- 2, 3, or 4 comparison panels (student chooses)
- Default temperatures pre-set to 0.0 / 0.5 / 1.0 — fully adjustable per panel
- Panels fill in one-by-one as each API call completes — students watch results arrive
- Colour-coded labels: Deterministic → Focused → Balanced → Creative
- Observation prompts guide students on what to look for
- Deep-dive expander explains the logit/softmax mechanics behind temperature

**How to run:**
```bash
cd module_1
streamlit run temperature_explorer.py
```

---

### `pre_read.md` — Student Reading Material

The complete pre-reading for Module 1. Covers:
- The four properties of agentic systems
- The six core components and how they interact
- The agentic loop
- A worked example (research agent)
- Starter code for the pipeline lab (reference implementation)

Read this before the session.

---

### `Module1_Lab_AgenticAI.ipynb` — Jupyter Notebook (Reference)

A Jupyter notebook version of the Module 1 lab. Use this if you prefer working in a notebook environment rather than the Streamlit apps.

**How to run:**
```bash
cd module_1
jupyter notebook Module1_Lab_AgenticAI.ipynb
```

---

## Quick Start (all labs)

```bash
# 1. Install dependencies (once)
pip install -r requirements.txt

# 2. Create your .env file inside module_1/
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > module_1/.env

# 3. Run any lab
streamlit run module_1/hour1_lab_agentic_classifier.py
streamlit run module_1/hour2_lab_architecture_visualizer.py
streamlit run module_1/hour3_lab_agentic_pipeline.py

# Bonus labs
streamlit run module_1/hour1b_lab_single_vs_agentic.py
streamlit run module_1/hour2b_lab_system_prompt_roles.py
streamlit run module_1/hour3b_lab_context_window_inspector.py
```

---

## Troubleshooting

**`AuthenticationError` or `Invalid API key`**  
→ Check that your `.env` file is inside `module_1/` and the key starts with `sk-ant-`.

**`ModuleNotFoundError: anthropic`**  
→ Run `pip install anthropic streamlit python-dotenv`.

**Streamlit opens but shows a blank page**  
→ Wait 2–3 seconds and refresh. The first load compiles the app.

**Claude returns unexpected output in Hour 2**  
→ Try simplifying your description. Very short descriptions may not have enough detail for Claude to identify all components.

---

*Module 1 of 9 | Agentic AI — A Professional 30-Hour Course*
