# Module 2 — Prompt Fundamentals

**Course:** Agentic AI — A Professional 30-Hour Course  
**Module:** 2 of 9 | Duration: 4 hours (Hours 4–7)

---

## Before You Start — API Key Setup

Create a `.env` file inside the `module-2/` folder:

```
module-2/
├── .env        ← create this file
├── claude_client.py
├── hour4_lab_prompt_anatomy.py
├── ...
```

Add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
```

Get your key from [console.anthropic.com](https://console.anthropic.com).

---

## File Reference

### `claude_client.py` — Shared API Wrapper

Shared helper used by all four labs. Not run directly.

- Loads `ANTHROPIC_API_KEY` from `.env`
- Exposes `chat(system, user, max_tokens, temperature)` → `(text, usage_dict)`

---

### `hour4_lab_prompt_anatomy.py` — Prompt Anatomy Workshop

**Hour 4.** Interactive prompt builder using the **6-element framework** (Role, Task, Context, Constraints, Output Format, Examples).

**What students do:**
1. Pick a broken prompt (e.g. "Tell me about machine learning.")
2. See colour-coded badges showing which elements are missing
3. Fill in each element in separate text areas
4. Watch the assembled prompt build in a live preview
5. Click **Compare** — broken vs structured outputs appear side-by-side
6. Click **Score My Prompt** — an LLM judge scores each element 0 / 0.5 / 1 and gives targeted feedback

**Key learning:** The most commonly missing elements (constraints, output format) are what turn a vague response into a targeted one.

```bash
streamlit run module-2/hour4_lab_prompt_anatomy.py
```

---

### `hour5_lab_prompt_types.py` — Prompt Type Classifier Quiz

**Hour 5.** A 10-question quiz game. Each question shows a prompt; the student selects the type, then Claude reveals its classification with reasoning.

**The 6 types:** instruction · role · planning · tool_use · routing · evaluation

**What students do:**
1. Read the prompt, select the type from a radio group
2. Click Submit — Claude classifies it independently and shows its reasoning
3. See if your answer matches Claude's; both are compared to the expected answer
4. Track score across all 10 questions
5. **Bonus:** Write your own prompt for a chosen type — Claude validates whether it reads as intended

**Key learning:** Each type maps to a specific component in an agentic system — routing prompts become routers, evaluation prompts become evaluators.

```bash
streamlit run module-2/hour5_lab_prompt_types.py
```

---

### `hour6_lab_zero_shot_vs_fewshot.py` — Zero-Shot vs Few-Shot + Decomposition

**Hour 6.** Two experiments in one app (two tabs).

**Part A — Zero-Shot vs Few-Shot:**
- Editable zero-shot and few-shot prompt templates (pre-filled with good defaults)
- Both run on 10 customer feedback samples → results table with colour-coded labels
- Agreement/disagreement highlighted — disagreements are the ambiguous cases
- Consistency score and key insight about what few-shot examples actually do

**Part B — Task Decomposition Pipeline:**
- Editable Planner + Executor prompts
- Student enters a goal → Planner generates 4 subtasks → each Executor call runs live
- Toggle: chain prior step outputs as context vs isolated calls (reuses the Hour 3B concept)

**Key learning:** Few-shot examples transfer your definition of categories to the model. Disagreements between zero-shot and few-shot reveal the cases your examples need to cover.

```bash
streamlit run module-2/hour6_lab_zero_shot_vs_fewshot.py
```

---

### `hour7_lab_refinement_loop.py` — Iterative Refinement Loop

**Hour 7.** A live Generate → Critique → Rewrite loop that runs for up to N rounds, stopping early when all quality scores exceed a threshold.

**Loop architecture:**
```
output = generate(topic)
while round < MAX_ROUNDS:
    scores, feedback = evaluate(output)   ← Critic returns JSON
    if all scores >= THRESHOLD: break
    output = rewrite(output, feedback)    ← Rewriter uses feedback
    round += 1
```

**What students do:**
1. Edit the Generator, Critic, and Rewriter prompts (pre-filled with strong defaults)
2. Set max rounds (1–5) and pass threshold (1–5) in the sidebar
3. Pick a topic and hit Run
4. Watch each round fill in live with scores, feedback, and rewritten text
5. See a line chart of score progression across rounds
6. Compare Round 1 (initial) vs the final output side-by-side

**Experiments to try (listed in sidebar):**
- Lower threshold to 2 — loop exits after round 1
- Remove the feedback field from the Critic — Rewriter makes generic changes
- Make the Generator deliberately weak — measure recovery rounds

**Key learning:** This is the Evaluator-Optimizer pattern. `generate()` = Executor, `evaluate()` = Evaluator, `rewrite()` = Executor with critique context.

```bash
streamlit run module-2/hour7_lab_refinement_loop.py
```

---

### `Module2_Prompt_Fundamentals_Exercises.ipynb` — Jupyter Notebook (Reference)

The complete exercise notebook for Module 2. Covers all four hours with fill-in-the-blank exercises, model answers, and a bonus combined pipeline. Use as a reference or for students who prefer a notebook environment.

```bash
jupyter notebook module-2/Module2_Prompt_Fundamentals_Exercises.ipynb
```

---

## Quick Start

```bash
# 1. Install dependencies (once)
pip install -r requirements.txt

# 2. Create .env inside module-2/
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > module-2/.env

# 3. Run any lab
streamlit run module-2/hour4_lab_prompt_anatomy.py
streamlit run module-2/hour5_lab_prompt_types.py
streamlit run module-2/hour6_lab_zero_shot_vs_fewshot.py
streamlit run module-2/hour7_lab_refinement_loop.py
```

---

## Module 2 Concept Map

| Hour | Lab | Core concept | Agentic connection |
|---|---|---|---|
| 4 | Prompt Anatomy | 6-element framework | Every agent prompt uses this structure |
| 5 | Prompt Types | instruction / role / planning / tool_use / routing / evaluation | Each type maps to a component role |
| 6 | Zero-Shot vs Few-Shot | Examples transfer definitions | Few-shot is how you teach the Executor your domain |
| 6 | Decomposition | Planning pattern | This IS the Planner component |
| 7 | Refinement Loop | Generate → Evaluate → Rewrite | This IS the Evaluator-Optimizer pattern |

---

## Troubleshooting

**`AuthenticationError`** → Check `.env` is inside `module-2/` and key starts with `sk-ant-`

**Hour 7 Critic returns parse error** → Your Critic prompt must return only valid JSON. Check the format matches the template in the Critic prompt.

**Hour 6 results show UNKNOWN** → Your prompt template must contain `{feedback}` as a placeholder. Check it wasn't accidentally removed.

**Hour 5 quiz stuck** → Click "Next →" after each answer is revealed. Use "Restart Quiz" from the end screen to reset.

---

*Module 2 of 9 | Agentic AI — A Professional 30-Hour Course*
