# Agentic AI — A Professional 30-Hour Course

**27 interactive Streamlit labs across 7 modules.**  
Every lab calls the Claude API live, shows the raw prompts, and displays token usage — no black boxes.

---

## Setup (do this once)

```bash
python -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r requirements.txt
```

Then create a `.env` file inside **each module folder** you want to run:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your key from [console.anthropic.com](https://console.anthropic.com).

> Never commit `.env` files — they contain your secret key.

---

## Find a Lab by Interest

| I want to understand… | Go to |
|---|---|
| What makes an AI system "agentic" | [Hour 1 — Agentic Classifier](#hour-1--agentic-classifier) |
| How to write better prompts | [Hour 4 — Prompt Anatomy](#hour-4--prompt-anatomy-workshop) |
| When few-shot examples help | [Hour 6 — Zero-Shot vs Few-Shot](#hour-6--zero-shot-vs-few-shot--decomposition) |
| How agents improve their own output | [Hour 7 — Refinement Loop](#hour-7--iterative-refinement-loop) / [Hour 12 — Reflection Pattern](#hour-12--reflection-pattern) |
| How to build different types of agents | [Hour 9 — Agent Types I](#hour-9--agent-types-i-router-planner-executor-critic) / [Hour 10 — Agent Types II](#hour-10--agent-types-ii-retriever-orchestrator-specialist) |
| How tool use works with Claude | [Hour 13 — Tool Use Pattern](#hour-13--tool-use-pattern) |
| How agents plan and decompose goals | [Hour 14 — Planning Pattern](#hour-14--planning-pattern) |
| How to chain multiple LLM calls | [Hour 15 — Prompt Chaining](#hour-15--prompt-chaining-pattern) |
| How routing dispatches to specialists | [Hour 17 — Routing Pattern](#hour-17--routing-pattern) |
| How to run agents in parallel | [Hour 18 — Parallelisation](#hour-18--parallelisation-pattern) |
| How multi-agent teams are coordinated | [Hour 22 — Multi-Agent Basics](#hour-22--multi-agent-basics) / [Hour 23 — Orchestrator-Workers](#hour-23--orchestrator-workers-architecture) |
| How agents hand off state to each other | [Hour 24 — Agent Handoffs](#hour-24--agent-communication-and-handoffs) |
| How RAG grounds answers in documents | [Hour 25 — RAG Fundamentals](#hour-25--rag-fundamentals) |
| How agents decide when to retrieve | [Hour 26 — Agentic RAG](#hour-26--agentic-rag) |
| How agents remember across turns | [Hour 27 — Memory and State](#hour-27--memory-and-state) |
| Everything combined in one pipeline | [Hour 16](#hour-16--capstone-combine-patterns-i) / [Hour 21](#hour-21--capstone-combine-patterns-ii) |
| Test your knowledge with a quiz | [Quiz App](#quiz-app) |

---

## Module 1 — Agentic AI Foundations
**Hours 1–3 · `module_1/`**

**Files:** `hour1_lab_agentic_classifier.py` · `hour2_lab_architecture_visualizer.py` · `hour3_lab_agentic_pipeline.py` · `hour1b_lab_single_vs_agentic.py` · `hour2b_lab_system_prompt_roles.py` · `hour3b_lab_context_window_inspector.py` · `temperature_explorer.py` · `claude_client.py` · `pre_read.md` · `Module1_Lab_AgenticAI.ipynb`

---

### Hour 1 — Agentic Classifier
**`module_1/hour1_lab_agentic_classifier.py`**

**What it is:** Submit a description of any AI product. Claude scores it against the four agentic properties (goal-directed, tool-using, iterative, memory-aware) and returns a verdict with reasoning.

**Concepts:** What makes a system agentic vs a standard LLM call · The four agentic properties · Structured JSON output from Claude · Raw prompt visibility

**Outcome:** You can look at any AI product and correctly identify whether and why it qualifies as agentic.

```bash
streamlit run module_1/hour1_lab_agentic_classifier.py
```

---

### Hour 2 — Architecture Visualizer
**`module_1/hour2_lab_architecture_visualizer.py`**

**What it is:** Describe a system in plain English. Claude identifies which of the six core components (Model, Tools, Memory, Planner, Executor, Evaluator) are present and produces a colour-coded component map with an agentic completeness score.

**Concepts:** Six core agent components · Component mapping from natural language · Colour-coded agent taxonomy · Agentic completeness scoring

**Outcome:** You can decompose any described system into its component parts and identify what's missing before building it.

```bash
streamlit run module_1/hour2_lab_architecture_visualizer.py
```

---

### Hour 3 — Your First Agentic Pipeline
**`module_1/hour3_lab_agentic_pipeline.py`**

**What it is:** A fully visible two-step pipeline — Planner generates a 4-step plan, Executor carries out steps, optional Evaluator critiques the result. Each LLM call is rendered as a labelled block so you see exactly how state flows.

**Concepts:** Planner → Executor → Evaluator pipeline · State passing between LLM calls · Multiple sequential API calls · The Evaluator as an optional quality gate

**Outcome:** You can implement a basic agentic pipeline in code and explain what each stage does and why it's separate.

```bash
streamlit run module_1/hour3_lab_agentic_pipeline.py
```

---

### Bonus — Single-Turn vs Agentic
**`module_1/hour1b_lab_single_vs_agentic.py`**

**What it is:** The same goal handled two ways simultaneously — one direct Claude call vs a Planner → Executor → Evaluator pipeline. A fourth call scores both outputs on completeness, depth, and actionability.

**Concepts:** Cost vs quality trade-off · When agentic systems outperform single calls · Empirical comparison methodology

**Outcome:** You have evidence (not theory) for when adding pipeline stages improves output quality.

```bash
streamlit run module_1/hour1b_lab_single_vs_agentic.py
```

---

### Bonus — System Prompt Role Lab
**`module_1/hour2b_lab_system_prompt_roles.py`**

**What it is:** Three editable columns — Planner, Executor, Evaluator — each with the same Claude model behind them. Edit any system prompt and watch the same model produce completely different behaviour.

**Concepts:** System prompt = agent identity · Role definition through prompting · How one model plays different roles

**Outcome:** You understand that the system prompt, not the model, defines what role an agent plays.

```bash
streamlit run module_1/hour2b_lab_system_prompt_roles.py
```

---

### Bonus — Context Window Inspector
**`module_1/hour3b_lab_context_window_inspector.py`**

**What it is:** The same pipeline as Hour 3, but exposes the exact JSON messages array at every step. A toggle switches between Chained (prior outputs included) and Isolated (fresh context) — token counts diverge visibly.

**Concepts:** Short-term memory as the messages list · Context window token accounting · Chained vs isolated context · Memory is just a Python list of dicts

**Outcome:** You can see exactly what Claude receives on each call and predict how token costs grow with context.

```bash
streamlit run module_1/hour3b_lab_context_window_inspector.py
```

---

### Bonus — Temperature Explorer
**`module_1/temperature_explorer.py`**

**What it is:** One prompt, multiple panels, each running at a different temperature. Adjust sliders and compare outputs side-by-side to understand how randomness affects generation.

**Concepts:** Temperature as a sampling parameter · Deterministic vs creative output · Which agent roles need low vs high temperature · Logit/softmax mechanics

**Outcome:** You can choose appropriate temperature settings for different agent components (e.g., routers need low temperature; creative generators need high).

```bash
streamlit run module_1/temperature_explorer.py
```

---

## Module 2 — Prompt Fundamentals
**Hours 4–7 · `module-2/`**

**Files:** `hour4_lab_prompt_anatomy.py` · `hour5_lab_prompt_types.py` · `hour6_lab_zero_shot_vs_fewshot.py` · `hour7_lab_refinement_loop.py` · `hour4b_lab_output_format_reliability.py` · `hour4c_lab_prompt_compression.py` · `hour6b_lab_chain_of_thought.py` · `claude_client.py` · `Module2_Reading_Material.md` · `Module2_Prompt_Fundamentals_Exercises.ipynb`

---

### Hour 4 — Prompt Anatomy Workshop
**`module-2/hour4_lab_prompt_anatomy.py`**

**What it is:** An interactive prompt builder using the 6-element framework (Role, Task, Context, Constraints, Output Format, Examples). Compare a broken prompt against a structured one side-by-side, then have an LLM judge score each element.

**Concepts:** 6-element prompt framework · Missing elements cause vague output · Format instructions are not cosmetic · LLM-as-judge scoring

**Outcome:** You can diagnose any broken prompt, identify the missing elements, and rebuild it to get targeted, reliable output.

```bash
streamlit run module-2/hour4_lab_prompt_anatomy.py
```

---

### Hour 5 — Prompt Type Classifier Quiz
**`module-2/hour5_lab_prompt_types.py`**

**What it is:** A 10-question quiz game. Each question shows a real prompt; you classify it, then Claude classifies it independently with reasoning. Both answers are compared against the expected answer.

**Concepts:** Six prompt types (instruction · role · planning · tool_use · routing · evaluation) · Each type maps to an agent component · Prompt intent vs prompt content

**Outcome:** You can read any agent prompt and immediately identify which component role it was designed for.

```bash
streamlit run module-2/hour5_lab_prompt_types.py
```

---

### Hour 6 — Zero-Shot vs Few-Shot + Decomposition
**`module-2/hour6_lab_zero_shot_vs_fewshot.py`**

**What it is:** Two experiments in one app. Part A runs zero-shot vs few-shot classification on 10 samples and highlights where they disagree. Part B is a task decomposition pipeline — Planner → Executor chain with a context toggle.

**Concepts:** Zero-shot vs few-shot prompting · Few-shot examples transfer definitions · Disagreements reveal label ambiguity · Task decomposition as a planning pattern

**Outcome:** You know when to add few-shot examples (ambiguous classes) and how decomposition breaks hard tasks into manageable steps.

```bash
streamlit run module-2/hour6_lab_zero_shot_vs_fewshot.py
```

---

### Hour 7 — Iterative Refinement Loop
**`module-2/hour7_lab_refinement_loop.py`**

**What it is:** A live Generate → Critique → Rewrite loop that runs for up to N rounds, stopping early when all quality scores exceed a threshold. A line chart shows score progression across rounds.

**Concepts:** Evaluator-Optimizer pattern · Threshold-gated termination · Critic structured JSON output · Score plateau detection · Round-by-round quality tracking

**Outcome:** You can implement a self-improving loop and explain why it stops on quality (not round count) to avoid wasted API calls.

```bash
streamlit run module-2/hour7_lab_refinement_loop.py
```

---

### Bonus — Output Format Reliability
**`module-2/hour4b_lab_output_format_reliability.py`**

**What it is:** The same extraction task runs with five format instructions, each three times at temperature 0.7. Every response is parsed programmatically — reliability = successful parses / 3 runs.

**Concepts:** Format reliability under temperature randomness · JSON schema enforcement · Why unstructured output breaks pipelines · Parsing failure rates per format

**Outcome:** You have empirical data showing which format instructions are reliable enough for agentic pipelines (spoiler: strict JSON schema wins).

```bash
streamlit run module-2/hour4b_lab_output_format_reliability.py
```

---

### Bonus — Prompt Compression Lab
**`module-2/hour4c_lab_prompt_compression.py`**

**What it is:** Start with a full 6-element prompt and toggle elements off one by one. After each change, an LLM judge scores quality. A history table and line charts track quality vs token count across all configurations.

**Concepts:** Prompt compression trade-offs · Minimum viable prompt · Token cost vs quality cliff · Systematic ablation methodology

**Outcome:** You can find the shortest prompt that maintains acceptable quality for a given task.

```bash
streamlit run module-2/hour4c_lab_prompt_compression.py
```

---

### Bonus — Chain-of-Thought Explorer
**`module-2/hour6b_lab_chain_of_thought.py`**

**What it is:** The same reasoning problem runs three ways simultaneously — Direct, Zero-shot CoT ("think step by step"), and Few-shot CoT (worked examples). A judge checks correctness and scores reasoning quality.

**Concepts:** Chain-of-thought prompting · CoT as externalised working memory · Zero-shot vs few-shot CoT · When CoT helps and when it doesn't

**Outcome:** You can predict which problem types benefit from CoT and write few-shot reasoning templates that guide the model's logic.

```bash
streamlit run module-2/hour6b_lab_chain_of_thought.py
```

---

## Module 3 — Agent Types and Components
**Hours 8–11 · `module-3/`**

**Files:** `hour8_lab_agent_components.py` · `hour9_lab_agent_types_i.py` · `hour10_lab_agent_types_ii.py` · `hour11_lab_implement_two_agents.py` · `claude_client.py`

---

### Hour 8 — Agent Components Workshop
**`module-3/hour8_lab_agent_components.py`**

**What it is:** Four core agent components (Persona, Knowledge, Tools, Interaction Layer) are made tangible. Students annotate a real agent config, then assemble their own from scratch and run it.

**Concepts:** Persona (system prompt identity) · Knowledge (injected context) · Tools (external functions) · Interaction Layer (output format) · Every framework uses these four components

**Outcome:** You can read any agent codebase — LangChain, LangGraph, raw API — and immediately identify the four components regardless of naming convention.

```bash
streamlit run module-3/hour8_lab_agent_components.py
```

---

### Hour 9 — Agent Types I: Router, Planner, Executor, Critic
**`module-3/hour9_lab_agent_types_i.py`**

**What it is:** Four fundamental agent types — each with a single distinct role. Send the same input to all four simultaneously and see how each agent's role shapes its response entirely differently. Then a quiz maps real-world tasks to the right agent type.

**Concepts:** Router → Label · Planner → Step list · Executor → Result · Critic → Scores + Feedback · One agent, one role · Role composability through specialisation

**Outcome:** You can decompose any multi-step task into the correct sequence of agent types and explain why each role must stay separate.

```bash
streamlit run module-3/hour9_lab_agent_types_i.py
```

---

### Hour 10 — Agent Types II: Retriever, Orchestrator, Specialist
**`module-3/hour10_lab_agent_types_ii.py`**

**What it is:** Three more agent types that connect and extend the first four. A Retriever demo shows knowledge base search without answering. An Orchestrator demo runs a 4-stage pipeline with specialists. A Team Designer validates role clarity with Claude.

**Concepts:** Retriever selects — never answers · Orchestrator coordinates — never does the work · Specialist depth vs generalist breadth · Multi-agent team composition

**Outcome:** You can design a multi-agent team, assign roles without overlap, and validate that each role can be described in one sentence.

```bash
streamlit run module-3/hour10_lab_agent_types_ii.py
```

---

### Hour 11 — Implement Two Agent Types
**`module-3/hour11_lab_implement_two_agents.py`**

**What it is:** The Module 3 capstone. Build and test a Router agent (classifying support requests to specialists) and a Critic agent (Generator → Critic → Rewriter pipeline) from scratch with editable system prompts.

**Concepts:** Router returns JSON route + confidence · Specialist isolation from routing logic · Critic structured scores (JSON) drive conditional rewriting · Confidence threshold for escalation

**Outcome:** You have working implementations of a Router and a Critic that you built and tested — not just observed.

```bash
streamlit run module-3/hour11_lab_implement_two_agents.py
```

---

## Module 4 — Core Agentic Patterns I
**Hours 12–16 · `module-4/`**

**Files:** `hour12_lab_reflection_pattern.py` · `hour13_lab_tool_use_pattern.py` · `hour14_lab_planning_pattern.py` · `hour15_lab_prompt_chaining.py` · `hour16_lab_combine_patterns.py` · `claude_client.py` · `Module4_Reading_Material.md`

> `claude_client.py` in this module adds `chat_with_tools()` — required by Hour 13.

---

### Hour 12 — Reflection Pattern
**`module-4/hour12_lab_reflection_pattern.py`**

**What it is:** A Generator produces a draft, a Critic scores it (JSON: clarity/accuracy/tone/completeness 1–5 + feedback), and a Refiner improves it. Run for 1–3 rounds and watch scores improve across rounds.

**Concepts:** Generator → Critic → Refiner loop · Structured critique drives targeted rewriting · Score progression and plateau detection · Separate critic vs combined generate-and-critique

**Outcome:** You can implement a reflection loop that measurably improves output quality and know when additional rounds stop helping.

```bash
streamlit run module-4/hour12_lab_reflection_pattern.py
```

---

### Hour 13 — Tool Use Pattern
**`module-4/hour13_lab_tool_use_pattern.py`**

**What it is:** Claude calls two external tools — a safe math calculator and a knowledge base search function. Shows the full tool call loop: Claude returns a `tool_use` block → Python executes → `tool_result` injected → Claude finalises.

**Concepts:** Tool schemas (JSON spec Claude receives) · `tool_use` content blocks · Tool result injection · Multi-tool agent sessions · Safe AST-based math evaluation

**Outcome:** You can wire Claude to any Python function using the tool use API and handle multi-turn tool call loops in code.

```bash
streamlit run module-4/hour13_lab_tool_use_pattern.py
```

---

### Hour 14 — Planning Pattern
**`module-4/hour14_lab_planning_pattern.py`**

**What it is:** A Planner decomposes a goal into 5 structured steps with effort ratings. A Parallel Planner adds dependency groups for concurrent execution. A Plan Critic then reviews the plan for gaps and risks before any execution.

**Concepts:** Sequential vs parallel planning · Plan as structured JSON · Identifying independent steps · Plan critique before execution · Effort estimation

**Outcome:** You can implement a planner that returns machine-readable plans and identify which steps can run in parallel before writing any executor code.

```bash
streamlit run module-4/hour14_lab_planning_pattern.py
```

---

### Hour 15 — Prompt Chaining Pattern
**`module-4/hour15_lab_prompt_chaining.py`**

**What it is:** A 3-stage pipeline transforms a topic into a full article — Researcher (facts), Outliner (structure), Drafter (prose). Each stage's output feeds directly into the next. Chain inspection shows exactly what each stage received vs what it produced.

**Concepts:** Output-to-input injection · Context accumulation across stages · Each stage narrows transformation · Token cost growth per stage · Stage specialisation vs one large prompt

**Outcome:** You can design a multi-stage prompt chain where each stage does one transformation, and explain why chaining beats a single all-in-one prompt.

```bash
streamlit run module-4/hour15_lab_prompt_chaining.py
```

---

### Hour 16 — Capstone: Combine Patterns I
**`module-4/hour16_lab_combine_patterns.py`**

**What it is:** A complete research assistant pipeline that chains all four Module 4 patterns: Planner creates a plan → Searcher (tool use) gathers facts per step → Drafter writes the report (chaining) → Critic scores it → Refiner improves it (reflection).

**Concepts:** Pattern composition · Planning shapes downstream quality · Tool use grounds the draft · Reflection improves after writing · Token ledger across a full pipeline

**Outcome:** You understand how the four foundational patterns compose into a production-grade pipeline and can read the token cost of each stage.

```bash
streamlit run module-4/hour16_lab_combine_patterns.py
```

---

## Module 5 — Core Agentic Patterns II
**Hours 17–21 · `module-5/`**

**Files:** `hour17_lab_routing_pattern.py` · `hour18_lab_parallelisation_pattern.py` · `hour19_lab_orchestrator_subagents.py` · `hour20_lab_evaluator_optimizer.py` · `hour21_lab_combine_patterns.py` · `claude_client.py` · `Module5_Reading_Material.md`

> `claude_client.py` in this module includes `chat_with_tools()`.

---

### Hour 17 — Routing Pattern
**`module-5/hour17_lab_routing_pattern.py`**

**What it is:** A classifier agent reads each input and dispatches it to one of five domain specialists (TECH / MEDICAL / FINANCE / LEGAL / GENERAL). A second complexity router sends the same question to a fast path or deep path based on question difficulty.

**Concepts:** Router never answers — only classifies · Confidence-gated dispatch · Below-threshold escalation · Domain routing vs complexity routing · Two LLM calls beat one generalised call

**Outcome:** You can build a router that dispatches to specialists and handles low-confidence inputs without failing silently.

```bash
streamlit run module-5/hour17_lab_routing_pattern.py
```

---

### Hour 18 — Parallelisation Pattern
**`module-5/hour18_lab_parallelisation_pattern.py`**

**What it is:** Fan-out sends the same document to three specialists simultaneously (Summariser, Risk Analyst, Opportunity Analyst); an Aggregator synthesises all three. Voting sends the same question to three agents at different temperatures and tallies agreement.

**Concepts:** Fan-out parallelisation · Aggregator synthesis · Voting consensus · Agreement rate as confidence · Coverage vs reliability trade-off · Token cost: N calls + 1 aggregator

**Outcome:** You can implement both fan-out and voting patterns and explain when each is appropriate (coverage vs reliability).

```bash
streamlit run module-5/hour18_lab_parallelisation_pattern.py
```

---

### Hour 19 — Orchestrator-Subagents Pattern
**`module-5/hour19_lab_orchestrator_subagents.py`**

**What it is:** An orchestrator reads a research question, decomposes it into 2–3 sub-questions, spawns focused subagents, and synthesises their outputs. A quality gate re-delegates if subagent output scores below threshold.

**Concepts:** Dynamic subagent assembly vs fixed agent set · Subagent context isolation · Quality-gated re-delegation · Orchestration is adaptive; planning is static · Research orchestrator vs document processor

**Outcome:** You can build an orchestrator that assembles different teams for different inputs and retries low-quality subagent work automatically.

```bash
streamlit run module-5/hour19_lab_orchestrator_subagents.py
```

---

### Hour 20 — Evaluator-Optimizer Pattern
**`module-5/hour20_lab_evaluator_optimizer.py`**

**What it is:** A Generator produces output, an Evaluator scores it on domain-specific criteria (1–5), an Optimizer rewrites targeting weak criteria. The loop terminates when all criteria meet the threshold — not when a round count is hit.

**Concepts:** Threshold-gated loop termination · Domain-specific evaluation criteria · Optimizer preserves high-scoring dimensions · Plateau detection · Code quality vs prompt quality domains

**Outcome:** You can implement a self-improving loop with a configurable quality threshold and explain why quality-gated termination beats fixed rounds.

```bash
streamlit run module-5/hour20_lab_evaluator_optimizer.py
```

---

### Hour 21 — Capstone: Combine Patterns II
**`module-5/hour21_lab_combine_patterns.py`**

**What it is:** A Smart Content Analysis Pipeline chains all four Module 5 patterns: Router classifies content type → three domain-matched Specialists analyse in parallel → Orchestrator synthesises a draft → Evaluator-Optimizer improves until quality threshold is met.

**Concepts:** Four-pattern composition · Router shapes the entire downstream pipeline · Orchestrator as the costliest single call · Self-correcting pipeline · Per-stage token ledger

**Outcome:** You have a complete, adaptive content analysis pipeline that routes, parallelises, orchestrates, and self-corrects — all in a single run button.

```bash
streamlit run module-5/hour21_lab_combine_patterns.py
```

---

## Module 6 — Multi-Agent Systems
**Hours 22–24 · `module-6/`**

**Files:** `hour22_lab_multiagent_basics.py` · `hour23_lab_orchestrator_workers.py` · `hour24_lab_agent_handoffs.py` · `claude_client.py` · `Module6_Reading_Material.md`

> `claude_client.py` in this module includes `chat_with_tools()`.

---

### Hour 22 — Multi-Agent Basics
**`module-6/hour22_lab_multiagent_basics.py`**

**What it is:** Three specialist agents (Summarizer, Fact-Checker, Implications Analyst) independently analyse the same news headline in a flat architecture. An Orchestrator then reads all three outputs and writes a coordinated synthesis — showing exactly what a hierarchy adds.

**Concepts:** Flat vs hierarchical architectures · Agents contradict without coordination · Orchestrator as conflict resolver · Confidence scores per agent · Cost of adding a coordination layer (3 vs 4 LLM calls)

**Outcome:** You can explain why flat multi-agent systems produce contradictory results and how a hierarchy resolves this by design.

```bash
streamlit run module-6/hour22_lab_multiagent_basics.py
```

---

### Hour 23 — Orchestrator-Workers Architecture
**`module-6/hour23_lab_orchestrator_workers.py`**

**What it is:** A Goal Decomposer breaks a complex goal into a 4-task JSON list (one per typed worker: Researcher/Analyst/Writer/Risk). Each worker executes independently. A Synthesiser reads all four outputs and produces an executive brief with structured headers.

**Concepts:** Goal decomposition to typed workers · Workers receive only their own task — not the full goal · Orchestrator output is a task list, not the answer · Token cost scales with workers · 6 LLM calls total

**Outcome:** You can implement the full orchestrator-workers pattern and read the token ledger showing the cost distribution across decomposition, execution, and synthesis.

```bash
streamlit run module-6/hour23_lab_orchestrator_workers.py
```

---

### Hour 24 — Agent Communication and Handoffs
**`module-6/hour24_lab_agent_handoffs.py`**

**What it is:** A Document Review Pipeline where a handoff package grows through three specialist stages — Legal (extracts clauses) → Risk (adds risk scores) → Recommendation (writes verdict). A bidirectional handoff section shows a Clarifier asking a question before a Task Completer can proceed.

**Concepts:** Handoff package as growing state · Sequential enrichment — each stage builds on prior · Schema design for handoff data · Bidirectional clarification loop · Vague tasks trigger 3 calls; clear tasks need 2

**Outcome:** You can design a multi-stage handoff pipeline with a typed JSON schema at each stage and handle ambiguous inputs with a clarification loop.

```bash
streamlit run module-6/hour24_lab_agent_handoffs.py
```

---

## Module 7 — RAG and Agentic Memory
**Hours 25–27 · `module-7/`**

**Files:** `hour25_lab_rag_fundamentals.py` · `hour26_lab_agentic_rag.py` · `hour27_lab_memory_and_state.py` · `claude_client.py` · `Module7_Reading_Material.md`

> `claude_client.py` in this module includes `chat_with_tools()`. Hours 25 and 26 require `scikit-learn` (already in `requirements.txt`).

---

### Hour 25 — RAG Fundamentals
**`module-7/hour25_lab_rag_fundamentals.py`**

**What it is:** TF-IDF retrieval from a 15-document knowledge base about agentic AI. Similarity scores shown as progress bars. A Grounded Generator answers with `[Doc N]` citations. A side-by-side comparison shows grounded vs ungrounded responses to the same query.

**Concepts:** The 4-stage RAG pipeline (Query → Retrieve → Augment → Generate) · TF-IDF cosine similarity scoring · Top-K retrieval · Grounded generation with citations · Retriever selects; LLM generates — never conflate

**Outcome:** You can implement a TF-IDF retrieval system, ground Claude's answers in retrieved documents, and explain the token cost difference between grounded and direct generation.

```bash
streamlit run module-7/hour25_lab_rag_fundamentals.py
```

---

### Hour 26 — Agentic RAG
**`module-7/hour26_lab_agentic_rag.py`**

**What it is:** A RAG Router agent classifies each query as RETRIEVE (use the knowledge base) or DIRECT (answer from model knowledge). The appropriate path executes. A force-comparison mode runs both paths on the same query for direct contrast.

**Concepts:** Routing overhead vs retrieval overhead trade-off · Router returns JSON `{route, reason, confidence}` · In-KB vs out-of-KB query classification · Grounded citations vs direct generation quality · When agentic RAG beats standard RAG

**Outcome:** You can explain when adding a router before retrieval saves cost and latency, and implement the routing decision with confidence scoring.

```bash
streamlit run module-7/hour26_lab_agentic_rag.py
```

---

### Hour 27 — Memory and State
**`module-7/hour27_lab_memory_and_state.py`**

**What it is:** Two sections: (1) Short-term memory — multi-turn chat where the full conversation history is passed to Claude on every turn; reset to verify the agent forgets. (2) Long-term memory — a Memory Extractor agent reads each turn and extracts user facts, which are injected into the system prompt so the agent personalises without being re-told.

**Concepts:** Short-term memory = the message list · Long-term memory = extracted facts in storage · Profile injection at the system prompt level · Memory Extractor runs every turn (even with no new facts) · Resetting conversation vs resetting profile — two distinct operations

**Outcome:** You can implement both short-term and long-term memory, explain the difference between them, and demonstrate that long-term memory survives a conversation reset.

```bash
streamlit run module-7/hour27_lab_memory_and_state.py
```

---

## Quiz App
**`quiz/app.py`**

A standalone Streamlit quiz application — separate from the module labs. Tests knowledge across all course concepts with scored, multi-choice questions.

```bash
streamlit run quiz/app.py
```

---

## Full Lab Index

| Module | Hour | Lab | Filename | Core pattern | Level |
|--------|------|-----|----------|-------------|-------|
| 1 | 1 | Agentic Classifier | `hour1_lab_agentic_classifier.py` | Agentic properties | Foundations |
| 1 | 2 | Architecture Visualizer | `hour2_lab_architecture_visualizer.py` | Agent components | Foundations |
| 1 | 3 | Your First Agentic Pipeline | `hour3_lab_agentic_pipeline.py` | Planner → Executor → Evaluator | Foundations |
| 1 | 1B | Single-Turn vs Agentic | `hour1b_lab_single_vs_agentic.py` | Cost vs quality trade-off | Bonus |
| 1 | 2B | System Prompt Role Lab | `hour2b_lab_system_prompt_roles.py` | System prompt as identity | Bonus |
| 1 | 3B | Context Window Inspector | `hour3b_lab_context_window_inspector.py` | Messages list as memory | Bonus |
| 1 | — | Temperature Explorer | `temperature_explorer.py` | Sampling randomness | Bonus |
| 2 | 4 | Prompt Anatomy Workshop | `hour4_lab_prompt_anatomy.py` | 6-element framework | Prompt engineering |
| 2 | 5 | Prompt Type Classifier | `hour5_lab_prompt_types.py` | Prompt type taxonomy | Prompt engineering |
| 2 | 6 | Zero-Shot vs Few-Shot | `hour6_lab_zero_shot_vs_fewshot.py` | Example transfer | Prompt engineering |
| 2 | 7 | Iterative Refinement Loop | `hour7_lab_refinement_loop.py` | Evaluator-Optimizer | Prompt engineering |
| 2 | 4B | Output Format Reliability | `hour4b_lab_output_format_reliability.py` | Format reliability | Bonus |
| 2 | 4C | Prompt Compression | `hour4c_lab_prompt_compression.py` | Token vs quality | Bonus |
| 2 | 6B | Chain-of-Thought Explorer | `hour6b_lab_chain_of_thought.py` | CoT prompting | Bonus |
| 3 | 8 | Agent Components Workshop | `hour8_lab_agent_components.py` | Persona/Knowledge/Tools/Interaction | Agent design |
| 3 | 9 | Agent Types I | `hour9_lab_agent_types_i.py` | Router/Planner/Executor/Critic | Agent design |
| 3 | 10 | Agent Types II | `hour10_lab_agent_types_ii.py` | Retriever/Orchestrator/Specialist | Agent design |
| 3 | 11 | Implement Two Agent Types | `hour11_lab_implement_two_agents.py` | Router + Critic end-to-end | Agent design |
| 4 | 12 | Reflection Pattern | `hour12_lab_reflection_pattern.py` | Generator → Critic → Refiner | Patterns I |
| 4 | 13 | Tool Use Pattern | `hour13_lab_tool_use_pattern.py` | Tool schemas + call loop | Patterns I |
| 4 | 14 | Planning Pattern | `hour14_lab_planning_pattern.py` | Sequential vs parallel plans | Patterns I |
| 4 | 15 | Prompt Chaining Pattern | `hour15_lab_prompt_chaining.py` | Stage-by-stage injection | Patterns I |
| 4 | 16 | Capstone: Combine Patterns I | `hour16_lab_combine_patterns.py` | All four patterns combined | Patterns I |
| 5 | 17 | Routing Pattern | `hour17_lab_routing_pattern.py` | Confidence-gated dispatch | Patterns II |
| 5 | 18 | Parallelisation Pattern | `hour18_lab_parallelisation_pattern.py` | Fan-out + voting | Patterns II |
| 5 | 19 | Orchestrator-Subagents | `hour19_lab_orchestrator_subagents.py` | Dynamic team assembly | Patterns II |
| 5 | 20 | Evaluator-Optimizer | `hour20_lab_evaluator_optimizer.py` | Threshold-gated loop | Patterns II |
| 5 | 21 | Capstone: Combine Patterns II | `hour21_lab_combine_patterns.py` | All four patterns combined | Patterns II |
| 6 | 22 | Multi-Agent Basics | `hour22_lab_multiagent_basics.py` | Flat vs hierarchical | Multi-agent |
| 6 | 23 | Orchestrator-Workers | `hour23_lab_orchestrator_workers.py` | Goal decomposition + synthesis | Multi-agent |
| 6 | 24 | Agent Handoffs | `hour24_lab_agent_handoffs.py` | Growing handoff package | Multi-agent |
| 7 | 25 | RAG Fundamentals | `hour25_lab_rag_fundamentals.py` | TF-IDF retrieval + grounded gen | RAG + Memory |
| 7 | 26 | Agentic RAG | `hour26_lab_agentic_rag.py` | Router → retrieve or direct | RAG + Memory |
| 7 | 27 | Memory and State | `hour27_lab_memory_and_state.py` | Short-term + long-term memory | RAG + Memory |
| — | — | Quiz App | `quiz/app.py` | All concepts | Standalone |

---

## Colour Convention

All labs use the same colour system so you can identify agent roles at a glance:

| Colour | Hex | Role |
|--------|-----|------|
| Blue | `#1E88E5` | Executor / Generator / Technical agent |
| Orange | `#FB8C00` | Specialist / Tools / Worker |
| Green | `#43A047` | Retriever / Knowledge / Memory |
| Purple | `#8E24AA` | Planner / Orchestrator / Synthesiser |
| Teal | `#00897B` | Router / Classifier |
| Red | `#E53935` | Critic / Evaluator / Risk analyst |

---

## Troubleshooting

**`AuthenticationError`** → Your `.env` file is missing or in the wrong folder. Each module needs its own `.env` with `ANTHROPIC_API_KEY=sk-ant-...`

**`ModuleNotFoundError: claude_client`** → Run labs from the repo root: `streamlit run module-7/hour27_lab_memory_and_state.py`, not from inside the module folder.

**`ModuleNotFoundError: sklearn`** → Run `pip install -r requirements.txt` from the repo root.

**Lab opens but shows nothing** → Wait 2–3 seconds and refresh. The first load compiles the Streamlit app.

**JSON parse errors in any lab** → The lab strips markdown fences automatically. If it still fails, the raw Claude output is shown — look for misformed JSON in the response and check the system prompt format instruction is intact.
