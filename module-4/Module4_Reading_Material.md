# Module 4 — Core Agentic Patterns I
## Pre-Read: The Four Foundational Patterns

**Agentic AI: A Professional 30-Hour Course**
*Hours 12–16 | Read before attending the lab sessions*

---

## Introduction: From Agent Types to Agent Patterns

In Module 3, you built individual agents — routers, critics, orchestrators. Each agent is a single LLM call with a carefully engineered system prompt. An agent is a component.

A **pattern** is a reusable arrangement of those components. Patterns are how agents are wired together to do work that a single call cannot do alone.

There are seven foundational agentic patterns. Module 4 covers the first four:

| Pattern | What it does |
|---------|-------------|
| **Reflection** | An agent reviews and improves its own output |
| **Tool Use** | An agent calls external functions to act on the world |
| **Planning** | An agent decomposes a goal into structured subtasks |
| **Prompt Chaining** | Output of one LLM call feeds directly into the next |

Module 5 adds three more: Routing, Parallelisation, and Evaluator-Optimizer.

These patterns are not framework-specific. You will find them inside LangChain, LangGraph, AutoGen, CrewAI, and raw API code alike. Once you understand the pattern, you can identify and implement it anywhere.

---

## Pattern 1 — Reflection

### The Core Idea

A single LLM call produces one output from one perspective. Reflection adds a second call — a critic — that reviews the first output and identifies weaknesses. A third call — a refiner — uses that critique to produce an improved version.

The insight is simple: **a model that cannot see its mistakes cannot fix them**. By making a separate call whose entire job is to find flaws, you create a feedback loop that drives quality upward.

### The Reflection Loop

```
User goal
    │
    ▼
[GENERATOR] ──── draft ────► [CRITIC] ──── JSON critique ────► [REFINER]
    ▲                                                               │
    └──────────────── improved draft (next round) ◄────────────────┘
```

Each component has a specific role:

- **Generator** — produces the initial response. It does not know it will be critiqued.
- **Critic** — reads the draft and scores it on defined criteria. Returns structured JSON so the refiner knows exactly what to fix.
- **Refiner** — receives both the original draft and the critique. Its job is to address the specific weaknesses identified.

### Why Three Separate Calls?

You might wonder: why not ask one model to write, critique, and improve in a single prompt? Two reasons.

First, **attention focus**. When you give a model a combined instruction ("write this, then critique it, then improve it"), each sub-task competes for the model's attention. A dedicated critic call has 100% of its context allocated to finding problems.

Second, **structured feedback**. A separate critic call can return JSON with numeric scores per criterion. Those scores are machine-readable — Python code can decide whether to run another round based on whether scores meet a threshold.

### The Critic Prompt Pattern

The critic must return structured output. A reliable pattern:

```
You are a quality evaluator. Score the following response on these criteria, each from 1 to 5:
- clarity (1=confusing, 5=crystal clear)
- accuracy (1=factually wrong, 5=fully correct)
- tone (1=inappropriate, 5=perfectly suited)
- completeness (1=major gaps, 5=thorough)

Return ONLY valid JSON:
{"clarity": N, "accuracy": N, "tone": N, "completeness": N, "feedback": "one specific improvement"}
```

The feedback field is the most important output. It tells the refiner what to fix, not just that something is wrong.

### Multi-Round Reflection

One round of reflection often captures the most obvious flaws. Additional rounds yield diminishing returns — by round 3, a well-written initial draft rarely improves significantly.

A production system typically:
1. Runs one mandatory reflection round.
2. Checks if scores meet a threshold (e.g., all criteria ≥ 4).
3. Runs a second round only if the threshold is not met.
4. Caps at 3 rounds to prevent infinite loops.

### When to Use Reflection

Use reflection when:
- Output quality variance is unacceptable (legal text, medical summaries, published content)
- The cost of a bad output is high
- You have a clear, checkable quality rubric

Avoid reflection when:
- Latency is critical (it adds at least 2 API calls)
- The task is factual lookup (reflection cannot add knowledge the model does not have)
- The same model critiques itself repeatedly — it will often approve its own blind spots

### A Worked Example

**Goal:** Write a 3-sentence summary of quantum entanglement for a general audience.

**Round 1 — Generator output:**
> Quantum entanglement is a phenomenon where two particles become correlated such that measuring one instantly affects the other, regardless of distance. This seems to violate the speed of light limit but actually doesn't because no useful information can be transmitted. Einstein called it "spooky action at a distance."

**Round 1 — Critic JSON:**
```json
{
  "clarity": 3,
  "accuracy": 4,
  "tone": 4,
  "completeness": 3,
  "feedback": "The phrase 'become correlated' is too vague for a general audience. Explain what 'correlated' means in plain language. Also missing: when does entanglement happen?"
}
```

**Round 1 — Refiner output:**
> Quantum entanglement happens when two particles are created or interact in a way that links their properties permanently. After that link forms, measuring one particle — say, finding it has a "spin up" state — instantly determines the other is "spin down," no matter how far apart they are. This baffled Einstein, who called it "spooky action at a distance," though physicists have since confirmed it experimentally many times.

Clarity improved from 3 to 4. Completeness improved from 3 to 5. The abstract "correlated" was replaced with a concrete spin example.

---

## Pattern 2 — Tool Use

### The Core Idea

Language models are trained on text. They cannot look up today's weather, run a SQL query, send an email, or multiply large numbers reliably. Tools extend an agent's capabilities beyond its training data into the real world.

Tool use works through a structured negotiation between the model and the code:

1. **You define tools** — functions the model is allowed to call, described in JSON schema.
2. **The model decides** — when it needs external capability, it signals a tool call instead of answering directly.
3. **Your code executes** — you run the actual function and send the result back.
4. **The model finalises** — it uses the tool's result to compose its final answer.

### The Tool Call Loop

```
User message
    │
    ▼
[AGENT] — needs external info → returns tool_use block
    │
    ▼
[YOUR CODE] — executes the tool function → returns result
    │
    ▼
[AGENT] — receives result → returns final text answer
```

This loop can repeat. If the model needs three tools to answer a question, it issues three tool calls (sometimes in sequence, sometimes structured to allow parallel execution).

### Tool Schema Anatomy

Every tool is described in JSON schema. The model reads this schema to understand what the tool does and what arguments it requires.

```json
{
  "name": "search_knowledge",
  "description": "Search an internal knowledge base for relevant information. Use this when you need factual information that may be in company documents.",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "The search query — a phrase or question that describes what you are looking for."
      },
      "max_results": {
        "type": "integer",
        "description": "Maximum number of results to return. Default 2.",
        "default": 2
      }
    },
    "required": ["query"]
  }
}
```

Three things matter in a tool description:

1. **`name`** — must be a valid Python identifier, no spaces. The model uses this name exactly when calling the tool.
2. **`description`** — this is the most important field. The model reads it to decide whether to call this tool. Write it from the model's perspective: "Use this when you need...".
3. **`input_schema`** — JSON Schema object defining parameters. Each property needs a type and a description. Required fields are listed in the `required` array.

### Handling Tool Calls in Code

When a model returns a tool call, the API response contains a `tool_use` content block instead of (or alongside) a `text` block:

```python
# Example response content block
{
    "type": "tool_use",
    "id": "toolu_01AbCdEf",
    "name": "calculate",
    "input": {"expression": "17 * 43 + 8"}
}
```

Your code must:
1. Detect the `tool_use` block.
2. Look up the actual Python function by name.
3. Execute it with the provided `input` dict.
4. Add the result to the conversation as a `tool_result` message.
5. Call the model again with the updated conversation.

```python
# Detecting and executing tool calls
for block in response_blocks:
    if block["type"] == "tool_use":
        tool_name = block["name"]
        tool_input = block["input"]
        tool_id = block["id"]

        # Execute the actual function
        result = tool_registry[tool_name](**tool_input)

        # Add result to conversation
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": str(result)
            }]
        })
```

### Safe Tool Execution

Tools can be dangerous. A model that calls `delete_file(path="/etc/passwd")` would be catastrophic. Apply these safeguards:

**Allowlist over blocklist.** Only register tools you intentionally expose. Never give the model access to a generic `execute_python()` function.

**Validate inputs before executing.** For a calculator tool, parse the expression before calling `eval`. Reject expressions that contain import statements, file operations, or network calls.

**Sandbox mathematical evaluation:**
```python
import ast

def safe_eval(expression: str) -> float:
    """Evaluate a mathematical expression safely."""
    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
        ast.USub, ast.UAdd, ast.Constant,
    )
    tree = ast.parse(expression, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            raise ValueError(f"Disallowed expression: {type(node).__name__}")
    return eval(compile(tree, "<string>", "eval"))
```

**Limit result size.** If a tool returns 10,000 words of search results, you are wasting tokens and confusing the model. Truncate tool results to what the model actually needs.

### Two Categories of Tools

**Read-only tools** — safe to call without user confirmation:
- `search_knowledge(query)` — retrieves information
- `calculate(expression)` — runs arithmetic
- `get_weather(city)` — fetches a web API
- `read_file(path)` — reads a local file

**Write tools** — require careful guardrails or explicit user approval:
- `send_email(to, subject, body)` — irreversible side effect
- `create_database_record(table, data)` — modifies shared state
- `call_api(endpoint, payload)` — may trigger external actions

For this module, all labs use read-only tools only.

### When to Use Tool Use

Use tool use when:
- The model needs information it cannot have from training (current data, private databases)
- The model needs to perform computation it cannot do reliably (complex arithmetic, code execution)
- The model needs to trigger real-world actions (send email, create ticket)

Avoid tool use when:
- The answer is directly in the model's training data
- The overhead of a tool call loop adds latency that is not justified by the result
- You could pass the information directly in the prompt instead

---

## Pattern 3 — Planning

### The Core Idea

Complex goals cannot be accomplished in a single step. Planning is the pattern where an agent receives a high-level goal and returns a structured decomposition: what to do, in what order, and (optionally) which steps can run in parallel.

Planning separates the **what** from the **how**. The planner does not execute anything. It produces a structured task list that executor agents then carry out.

### Sequential vs Parallel Planning

A **sequential plan** is a linear list of steps, each depending on the previous:

```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5
```

A **parallel plan** identifies which steps are independent and can run simultaneously:

```
Step 1 ──────────────────────────────► Step 4
         ↘ Step 2a ─► Step 2b ─────►
         ↘ Step 3  ──────────────►
```

In a parallel plan, Steps 2 and 3 can begin as soon as Step 1 completes. Step 4 waits for all of them. This can dramatically reduce wall-clock time when executor agents run concurrently.

### Structured Plan Output

A planner must return machine-readable output. The executor code reads this to dispatch work. A reliable schema:

```json
{
  "steps": [
    {
      "id": 1,
      "title": "Research the competitive landscape",
      "description": "Search for recent articles and reports on competitors in the European EV market.",
      "effort": "medium",
      "depends_on": []
    },
    {
      "id": 2,
      "title": "Analyse pricing data",
      "description": "Extract and compare EV prices across 5 manufacturers from the research.",
      "effort": "low",
      "depends_on": [1]
    }
  ],
  "parallel_groups": [[1], [2, 3], [4]],
  "rationale": "Steps 2 and 3 can run in parallel after step 1 because they analyse different dimensions of the same source data."
}
```

The `depends_on` field is optional but useful when planning complex workflows. The `parallel_groups` field explicitly groups steps for parallel execution.

### The Planner System Prompt Pattern

```
You are a planning agent. Given a goal, decompose it into exactly 5 concrete, 
specific, actionable subtasks.

Rules:
- Each step must be independently executable by a different agent
- Steps must cover the goal completely
- Order steps from foundation to completion
- Estimate effort as: low (< 30 min), medium (30–90 min), high (> 90 min)

Return ONLY valid JSON matching this schema:
{"steps": [{"id": N, "title": "...", "description": "...", "effort": "low|medium|high"}],
 "rationale": "one sentence explaining the decomposition logic"}
```

Notice the constraints: exactly 5 steps, machine-readable JSON, effort classification. Without these constraints, planners produce vague, unexecutable plans.

### Plan Quality and the Plan Critic

A plan is only as good as its decomposition. Common planner failures:

- **Too coarse** — "Do the research" is not actionable.
- **Too fine** — 20 micro-steps creates orchestration overhead without benefit.
- **Circular** — Step 3 depends on Step 4 which depends on Step 3.
- **Incomplete** — The plan skips a necessary step, leaving a gap the executor cannot fill.

A **plan critic** is a second agent that reviews the plan before execution begins:

```json
{
  "gaps": ["The plan does not include a review step before final submission"],
  "risks": ["Step 2 assumes data is publicly available; it may require authentication"],
  "suggestion": "Add a validation step between steps 3 and 4 to catch data quality issues early"
}
```

Running a plan critic before dispatching to executors costs one API call but can prevent executing a flawed plan for five rounds.

### When to Use Planning

Use planning when:
- The goal is complex enough that it cannot be accomplished in 2–3 calls
- Different parts of the goal require different specialisations (different agent types)
- You want to show the user a plan before committing to execution
- You need to parallelise work across multiple executors

Avoid planning when:
- The goal is simple enough for a single executor call
- Latency is critical — planning adds at least one round-trip before any execution begins
- The goal is too ambiguous for a plan to be meaningful without user clarification

---

## Pattern 4 — Prompt Chaining

### The Core Idea

Prompt chaining is the simplest pattern: the output of one LLM call becomes the input to the next. Each call transforms the information further, like an assembly line where each station adds value.

```
Input ──► [Stage 1] ──► output_1 ──► [Stage 2] ──► output_2 ──► [Stage 3] ──► Final
```

The key difference from a single complex prompt is **focus**. Each stage has a narrow, well-defined task. Stage 1 does not worry about the final format. Stage 3 does not worry about gathering raw information. This separation of concerns produces better results than asking one prompt to do everything.

### A 3-Stage Content Pipeline

The most common use of prompt chaining is content generation:

**Stage 1 — Researcher**
- Input: Topic
- Task: Extract the most important facts, statistics, and concepts
- Output: Bullet-point list of key information

**Stage 2 — Outliner**
- Input: Key facts from Stage 1
- Task: Organise those facts into a logical structure with sections and subpoints
- Output: Outline with headings

**Stage 3 — Drafter**
- Input: Outline from Stage 2
- Task: Write the full article following the outline, using the facts from Stage 1
- Output: Complete article

Each stage builds on the previous. The drafter cannot write a well-structured article without the outline. The outliner cannot create a logical structure without the facts. The researcher cannot write the article — that is not its job.

### Passing Information Between Stages

The handoff between stages is explicit in Python:

```python
# Stage 1
facts, u1 = chat(RESEARCHER_SYSTEM, f"Research topic: {topic}", max_tokens=600)

# Stage 2 — inject Stage 1 output
outline, u2 = chat(
    OUTLINER_SYSTEM,
    f"Topic: {topic}\n\nKey facts:\n{facts}\n\nCreate an outline.",
    max_tokens=400,
)

# Stage 3 — inject Stage 1 and Stage 2 outputs
draft, u3 = chat(
    DRAFTER_SYSTEM,
    f"Topic: {topic}\n\nFacts:\n{facts}\n\nOutline:\n{outline}\n\nWrite the full article.",
    max_tokens=1200,
)
```

Each call's `user` parameter contains all the information from previous stages that the current stage needs. Stage 3 receives both the raw facts and the outline — the drafter needs both to write accurately and in the right structure.

### Information Transformation

Prompt chaining is fundamentally about **information transformation**. Each stage transforms the input into a different form that is more useful for the next stage:

| Stage | Input form | Output form | Transformation |
|-------|-----------|-------------|----------------|
| Researcher | Topic (one line) | Facts (list) | Expansion |
| Outliner | Facts (list) | Structure (hierarchy) | Organisation |
| Drafter | Structure (hierarchy) | Article (prose) | Composition |

Understanding what transformation each stage performs helps you design chains correctly. If a stage's output is the same form as its input, it is probably not needed as a separate stage.

### When to Chain vs When to Use a Single Prompt

**Chain when:**
- Different stages require different temperatures (research at 0.3, creative drafting at 0.8)
- Different stages require different expertise (technical research vs accessible writing)
- Intermediate outputs are valuable on their own (you might want the outline even if the draft fails)
- A single prompt would exceed the model's effective reasoning depth

**Use a single prompt when:**
- The task is simple enough that a well-written prompt handles it completely
- You cannot clearly define what each intermediate stage should produce
- The transformation is not meaningful enough to justify an extra API call

### Chain Length and Context Growth

A critical consideration: each stage typically receives all previous outputs in its context. By Stage 3, the prompt is substantially longer than at Stage 1. This has two effects:

1. **Cost** — more input tokens at each stage. A 3-stage chain with 600 tokens at Stage 1 might send 1,800 tokens at Stage 3.
2. **Attention dilution** — very long contexts can cause models to weight early information less precisely.

Design chains so each stage receives only what it needs. Stage 3 in the content pipeline needs the outline and the facts — it does not need to know that Stage 1 searched three different sources.

---

## Combining the Four Patterns

The four patterns are most powerful when combined. A realistic production agent might:

1. **Plan** the overall approach (Planning)
2. **Search** for information using tools (Tool Use)
3. **Draft** a response stage by stage (Prompt Chaining)
4. **Critique and refine** the draft (Reflection)

This is the architecture of the Hour 16 lab — a research assistant that combines all four patterns into a single workflow.

```
User research goal
        │
        ▼
  [PLANNER] ──── 3-step plan ────────────────────────────────────────┐
        │                                                            │
        ▼                                                            │
  [SEARCHER × n] (Tool Use) ──── facts per step ───────────────────┐ │
        │                                                           │ │
        ▼                                                           ▼ ▼
  [DRAFTER] (Chaining: plan + facts → draft) ──── draft ──────────────►
        │                                                            │
        ▼                                                            │
  [CRITIC] (Reflection) ──── JSON critique ───────────────────────►  │
        │                                                            │
        ▼                                                            │
  [REFINER] ──── final report ◄────────────────────────────────────────
```

Each pattern contributes a distinct capability:
- Planning ensures the work is structured before it starts
- Tool use grounds the content in retrieved facts
- Chaining transforms raw facts into a polished narrative
- Reflection catches quality issues before the final output is delivered

Understanding these four patterns — separately and in combination — is the foundation for everything that follows in this course.

---

## What Comes Next

Module 5 — Core Agentic Patterns II — adds three more patterns that govern how agents coordinate with each other rather than how a single agent improves its own work:

- **Routing** — an agent classifies input and dispatches to different specialist paths
- **Parallelisation** — the same task is sharded across multiple concurrent agents
- **Evaluator-Optimizer** — a generation loop where an evaluator drives iterative improvement toward a measurable threshold

By the end of Module 5, you will have implemented all seven foundational patterns. Everything after that — multi-agent systems, RAG integration, production safety — builds on these seven.

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **Agentic pattern** | A reusable workflow structure for arranging LLM calls and tools |
| **Reflection loop** | Generator → Critic → Refiner cycle that improves output quality |
| **Tool schema** | JSON Schema description of a tool's name, purpose, and parameters |
| **tool_use block** | The API response structure indicating the model wants to call a tool |
| **tool_result** | The message you send back to the model containing a tool's output |
| **Sequential plan** | A linear subtask list where each step depends on the previous |
| **Parallel plan** | A grouped subtask list identifying steps that can run concurrently |
| **Prompt chaining** | Feeding the output of one LLM call as input to the next |
| **Information transformation** | The change in form that each stage in a chain applies to its input |
| **Plan critic** | An agent that reviews a generated plan for gaps and risks before execution |

---

*Read time: approximately 40 minutes. Bring questions to the Hour 12 session.*
