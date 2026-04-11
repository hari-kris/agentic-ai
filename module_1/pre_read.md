# Module 1 — Agentic AI Foundations
## Student Reading Material

**Course:** Agentic AI — A Professional 30-Hour Course  
**Module:** 1 of 9  
**Duration:** 3 hours (Hours 1–3)  
**Prerequisites:** Solid Python skills, REST API familiarity, basic LLM understanding

---

## Learning Objectives

By the end of this module, you will be able to:

1. Define what makes an AI system "agentic" using four precise properties.
2. Distinguish between a single-turn LLM call and a multi-step agentic workflow.
3. Name and describe the six core components of any agentic system.
4. Explain how these components interact in the agentic loop.
5. Implement a minimal two-step agentic pipeline in Python.

---

# Hour 1 — Introduction to Agentic AI

## What Is Agentic AI?

The term "agentic" has a specific technical meaning in the context of AI systems. It does not simply mean "a smarter chatbot." It refers to a fundamentally different architecture for how software interacts with AI models.

A standard LLM interaction works like this: you write a prompt, send it to a model, and receive a response. The interaction is complete. The model has no awareness of what came before (unless you include it in the prompt), no ability to take actions in the world, and no mechanism to check whether its answer is correct.

An agentic system works differently. You give it a goal — not a prompt. The system then autonomously plans how to achieve that goal, breaks it into steps, executes those steps (often using external tools), observes the results, reflects on whether it is on track, and continues until the goal is met. The human does not need to supervise each step.

This difference is not incremental. It is architectural.

## The Four Properties of Agentic Systems

Every agentic system, regardless of its domain or complexity, exhibits four fundamental properties. These are not optional features — they are what make a system agentic.

### 1. Goal-directed

An agentic system receives a high-level objective and works toward it autonomously. It does not require a human to specify each individual step. Given "write a research report on quantum computing advances in 2024," the system determines for itself what searches to run, what sources to consult, and how to structure the output.

This contrasts sharply with a standard LLM prompt, which is inherently reactive — it only responds to the exact question asked.

### 2. Tool-using

An agentic system can call external tools to gather information or take actions in the world. Tools are functions that the model can invoke: a web search API, a code execution sandbox, a database query, a calendar booking system, a file reader, or any external service.

Without tool use, the model is limited to its training data and cannot act on the world. Tool use is what gives agents their power — and their risk.

### 3. Iterative (operates in loops)

An agentic system does not complete its work in a single LLM call. It operates in cycles: plan → act → observe → reflect → revise → repeat. A single LLM invocation is just one step in a larger loop. The number of steps is not fixed in advance; the system determines when the goal has been sufficiently achieved.

This iterative structure is what allows agents to improve their outputs, recover from errors, and handle tasks that are too complex for a single prompt.

### 4. Memory-aware

An agentic system maintains context across steps. Short-term memory covers the current session: what has been searched, what has been written, what errors occurred. Long-term memory — implemented using vector databases or other persistent storage — allows the agent to recall information across sessions.

Without memory, each step would be isolated. With memory, the agent builds a coherent picture of its progress and can refer back to earlier work.

## How This Differs from What You Already Know

If you have used ChatGPT, Claude, or any other conversational AI, you have interacted with a model — not an agentic system. Those products have added features that push in the agentic direction (memory, plugins, web search), but the underlying interaction model remains largely conversational.

The distinction matters because the failure modes, design decisions, evaluation strategies, and engineering challenges of agentic systems are entirely different from those of conversational models. This course exists to teach those differences systematically.

## Where Agentic AI Appears in the Real World (2025–2026)

Agentic systems are not a research prototype. They are deployed in production at scale. Here are four examples you likely interact with or work near:

**Deep Research tools** (Perplexity, Gemini Deep Research, OpenAI Research): Given a research question, these systems plan a search strategy, retrieve multiple documents, synthesise evidence across sources, and produce a cited report — all from a single user query. This is agentic.

**GitHub Copilot Workspace**: Reads your codebase, proposes architectural changes, writes code, runs tests, observes failures, and revises — without per-step human instruction. This is agentic.

**AI customer support bots** (Salesforce Agentforce, Intercom Fin): Classify incoming queries, retrieve relevant policy documents, draft responses, escalate edge cases — all in a connected flow. This is agentic.

**AI coding assistants with tool access**: Claude Code, Cursor — these agents read your codebase, plan changes, write files, run linters, and iterate. This is agentic.

## Why This Skill Gap Matters Now

The gap between engineers who understand how to build agentic systems and those who do not is widening. In 2025, job postings requiring knowledge of LangChain, LangGraph, multi-agent orchestration, and agentic RAG have grown significantly across enterprise software roles. Major cloud providers (Google, Microsoft, AWS) and software companies (Salesforce, ServiceNow, IBM) have embedded agentic capabilities into their core platform offerings.

The engineers who will lead AI transformation projects — internally at every company — are the ones who understand how these systems are structured, why they fail, and how to make them reliable. That is the purpose of this course.

---

# Hour 2 — Agentic Architecture Overview

## The Six Core Components

Every agentic system — no matter how sophisticated — is assembled from six fundamental components. Learning to identify these components in any system you encounter is one of the most valuable skills this course will give you.

The colour convention used throughout this course (and on the board) is:
- **Blue** = Model (the brain)
- **Orange/Amber** = Tools (the hands)
- **Green** = Memory (the notebook)
- **Purple** = Planner (the strategist)
- **Teal** = Executor (the worker)
- **Red/Coral** = Evaluator (the judge)

### Component 1: The Model

The model is the large language model at the centre of the system — GPT-4o, Claude, Gemini, Llama, or another. Everything routes through the model: it receives prompts, reasons about them, generates text, and decides which tool to call next.

The model is not the agent. The model is the intelligence that the agent is built around. An agent is the full system, including all six components.

### Component 2: Tools

Tools are Python functions (or callable services) that the model can invoke to interact with the world. Common tools include:

- `web_search(query)` — retrieves results from a search engine
- `run_code(code)` — executes Python in a sandbox and returns output
- `read_file(path)` — reads a file from the filesystem
- `call_api(url, params)` — makes an HTTP request and returns the response
- `query_database(sql)` — executes a SQL query and returns results

When a model calls a tool, it returns a JSON-formatted "tool call" specifying the tool name and arguments. The orchestration layer executes the function and returns the result to the model as the next input.

This function-calling interface is standardised across major model providers and is a core skill in Modules 3–4.

### Component 3: Memory

Memory gives the agent continuity across steps and sessions. There are two types:

**Short-term memory** is the conversation history or context window — the sequence of messages passed to the model on each call. This is ephemeral; it resets when the session ends.

**Long-term memory** is implemented outside the model, typically using a vector database (Chroma, Pinecone, Weaviate) or a key-value store. The agent writes summaries or embeddings to this store and retrieves them in future steps or sessions.

Memory determines how coherent and contextually aware an agent feels. A research agent with good memory can say "as I found earlier in the search results..." A research agent without memory starts each step from scratch.

### Component 4: Planner

The planner component receives a high-level goal and decomposes it into a sequence of subtasks. The plan is the spine of the agentic workflow — everything else follows from it.

A simple planner is an LLM call with a system prompt that says "Given a goal, return a numbered list of specific, concrete steps." A sophisticated planner can perform conditional planning (if step 2 fails, try this alternative), parallel planning (steps 3 and 4 can be done simultaneously), and replanning (if the environment changes, update the plan).

### Component 5: Executor

The executor takes individual subtasks from the plan and carries them out. In most implementations, the executor is also the model — it receives a subtask as a prompt and either generates the output directly or calls a tool.

The executor is responsible for producing concrete intermediate outputs: a search query, a code snippet, a drafted paragraph, a database result. These outputs become the inputs to subsequent steps.

### Component 6: Evaluator

The evaluator reviews the output of executed steps and determines whether they meet a quality threshold. If the threshold is met, the workflow continues or concludes. If not, the evaluator triggers a revision loop.

The evaluator is what makes agents self-improving. Without an evaluator, the system runs once and delivers whatever it produces, regardless of quality. With an evaluator, the system iterates until the output is good enough — or until a maximum iteration count is reached.

Evaluators can be:
- **Model-based**: another LLM call that critiques the output against a rubric
- **Rule-based**: code that checks for specific conditions (length, format, presence of citations)
- **Human-in-the-loop**: a human reviews and approves before the workflow continues

## The Agentic Loop

These six components interact in a loop. Understanding this loop is the mental model for the entire course.

```
Goal / Input
     ↓
  Planner  →  produces a task list
     ↓
  Model  →  selects the next task and decides how to address it
     ↓
  Tools  →  model may call one or more tools and receive results
     ↓
  Executor  →  produces an intermediate output
     ↓
  Evaluator  →  scores the output
     ↓
  (if threshold not met) → back to Model with critique
  (if threshold met) → continue to next task or deliver final output
     ↑↓
  Memory  →  read and written at every step
```

This loop is not hypothetical. Every production agentic system implements a version of this cycle. The differences between systems lie in how each component is implemented, how the loop is controlled, and when it terminates.

## Worked Example: A Research Agent

To make the architecture concrete, trace through a simple research agent:

**Goal received:** "Write a summary of recent advances in fusion energy, with citations."

**Planner:** Generates four subtasks:
1. Search for recent papers and articles on fusion energy advances.
2. Identify 3–4 key themes from the search results.
3. Draft a 3-paragraph summary covering those themes.
4. Add citations for each claim.

**Executor + Model (subtask 1):** The model calls the `web_search` tool with the query "fusion energy advances 2024". Results are returned and stored in memory.

**Executor + Model (subtask 2):** The model reads the search results from memory and identifies themes: inertial confinement progress, tokamak milestones, private investment growth.

**Executor + Model (subtask 3):** The model drafts three paragraphs using the themes and stored search results.

**Evaluator:** Scores the draft. Finds that citations are missing and one paragraph is vague. Sends a critique back to the model.

**Revision loop:** The model revises with the critique. The evaluator scores again. Citations are added; vagueness is resolved. Threshold met.

**Output delivered.**

Total LLM calls: approximately 6–8. Total wall-clock time: 15–60 seconds depending on model latency. This is what agentic looks like in practice.

---

# Hour 3 — Lab: Build Your First Agentic Flow

## Lab Overview

In this lab, you will implement the minimal version of an agentic pipeline in Python. The goal is not to build a production system — it is to see the architecture we have discussed come alive in code, and to build the habit of thinking in components.

You will build a two-step pipeline that:
1. Calls an LLM to generate a plan for a given goal (the planner).
2. Extracts the first step of the plan.
3. Calls the LLM again to execute that step (the executor).

This is the kernel — the smallest possible agentic system. Every complex agent we build later is this pattern, extended.

## Before You Write Code: Sketch the Flow

A practice you will follow in every lab in this course: before opening the code editor, sketch the component diagram on paper or a digital canvas.

```
User Goal
    ↓
generate_plan()    ← LLM call 1 (PLANNER)
    ↓
extract_first_step()    ← parse state
    ↓
execute_step()    ← LLM call 2 (EXECUTOR)
    ↓
Output
```

Identify: which component does each function represent? Where is state passing between steps? This is exactly how experienced AI engineers think before they write a line of code.

## The Code

### Setup

```python
import openai

client = openai.OpenAI()  # Uses OPENAI_API_KEY from environment
```

If you are using the Anthropic API instead:

```python
import anthropic

client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY from environment
```

### The Planner Function

```python
def generate_plan(goal: str) -> str:
    """
    COMPONENT: Planner
    Calls the LLM with a planning system prompt.
    Returns a numbered list of steps as a string.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a planning agent. Given a goal, return a numbered list "
                    "of 4-5 concrete, specific steps to achieve it. Each step should "
                    "be actionable and unambiguous. Return only the list."
                )
            },
            {
                "role": "user",
                "content": goal
            }
        ]
    )
    return response.choices[0].message.content
```

**What to notice:**
- The system prompt defines the agent's role: it is a *planning* agent.
- The model receives the raw goal and is asked to produce a structured plan.
- The function returns plain text — the plan is state that we pass to the next component.

### The State Parser

```python
def extract_first_step(plan: str) -> str:
    """
    STATE MANAGEMENT: Parses the plan to extract step 1.
    This is not an LLM call — it is data processing.
    """
    lines = [line.strip() for line in plan.split('\n') if line.strip()]
    # Return the first non-empty line (the first step)
    return lines[0] if lines else plan
```

**What to notice:**
- This is not an LLM call. It is Python code that processes state.
- State management — parsing, filtering, transforming — is a normal part of agentic pipelines, not everything is an AI call.

### The Executor Function

```python
def execute_step(step: str) -> str:
    """
    COMPONENT: Executor
    Calls the LLM with an execution system prompt.
    Returns the output of carrying out the step.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an executor agent. You receive a specific task and carry it out. "
                    "Produce a concrete, detailed output. Do not plan — act."
                )
            },
            {
                "role": "user",
                "content": step
            }
        ]
    )
    return response.choices[0].message.content
```

**What to notice:**
- Different system prompt, different role. The executor is told to act, not to plan.
- This is the same model invoked differently — the behaviour changes based on the prompt.

### The Runner

```python
def run_agentic_pipeline(goal: str):
    """
    Orchestrates the two-step agentic pipeline.
    Planner → parse state → Executor
    """
    # Step 1: PLANNER
    print("[PLANNER] Generating plan...")
    plan = generate_plan(goal)
    print(f"\nPLAN:\n{plan}\n")
    print("-" * 50)

    # Step 2: STATE PARSING
    step_1 = extract_first_step(plan)
    print(f"[STATE] Extracted step 1: {step_1}\n")

    # Step 3: EXECUTOR
    print("[EXECUTOR] Executing step 1...")
    result = execute_step(step_1)
    print(f"\nOUTPUT:\n{result}")


# Run it with a goal
run_agentic_pipeline(
    "Research and write a 3-paragraph summary of quantum computing "
    "for a developer audience who is new to the topic."
)
```

## What You Are Observing

When you run this code, watch for:

1. **Two distinct LLM calls** — the model is invoked twice with different roles and different outputs.
2. **State passing** — the output of call 1 (the plan) becomes the input to the parser and then to call 2.
3. **Role differentiation** — the same model behaves differently as a planner vs an executor because of the system prompt.
4. **The component boundary** — `generate_plan` is the planner, `execute_step` is the executor. The boundary is where the state is parsed.

This is not a toy. This is the pattern that underlies every agentic framework, from LangChain to LangGraph to CrewAI. The abstractions change; the pattern does not.

## Lab Exercises

### Exercise 1 — Run and observe (10 minutes)
Run the starter code with the provided goal. Read both LLM outputs carefully. Could you have predicted what the planner would produce? Does the executor's output make sense for step 1?

### Exercise 2 — Add a second step (15 minutes)
Modify `run_agentic_pipeline` to execute step 2 of the plan as well. What state do you need to parse? How do you pass context between step 1's output and step 2's execution?

### Exercise 3 — Add a simple evaluator (15 minutes)
After executing step 2, add a third LLM call that reviews the output and produces one concrete improvement suggestion. This is your first evaluator. What should its system prompt say?

```python
def evaluate_output(output: str, goal: str) -> str:
    """
    COMPONENT: Evaluator
    Reviews the output against the original goal and suggests one improvement.
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a quality evaluator. Review the provided output against "
                    "the original goal. Identify ONE specific, concrete improvement "
                    "that would make the output better. Be brief and precise."
                )
            },
            {
                "role": "user",
                "content": f"GOAL: {goal}\n\nOUTPUT TO EVALUATE:\n{output}"
            }
        ]
    )
    return response.choices[0].message.content
```

### Exercise 4 — Stretch goal: label everything (5 minutes)
Add a print statement before every function call that labels it with `[PLANNER]`, `[EXECUTOR]`, or `[EVALUATOR]`. Run the full pipeline. Observe the three-component pattern in the console output.

---

# Key Concepts Summary

| Concept | Definition |
|---|---|
| Agentic system | An AI system that is goal-directed, tool-using, iterative, and memory-aware |
| Single-turn LLM | One prompt → one response. No state, no loop, no tools. |
| The agentic loop | Perceive → Plan → Act → Observe → Reflect → Repeat |
| Model | The LLM at the centre of the agent. The brain. |
| Tools | Functions the model can call to interact with the world. |
| Memory | Short-term (context window) and long-term (vector store) persistence. |
| Planner | Decomposes a goal into a sequence of subtasks. |
| Executor | Carries out individual subtasks. |
| Evaluator | Reviews output quality and triggers revision loops. |
| State | Data passed between steps in an agentic pipeline. |

---

# Preparation for Module 2

Before the next session, complete the following:

1. Annotate your lab code — add a comment on each line indicating which component it belongs to (planner / executor / evaluator / state management).
2. Think of one real-world AI product you use and identify which of the four agentic properties it exhibits. Be prepared to discuss this at the start of Module 2.
3. Read the first two sections of the Anthropic blog post "Agents" (anthropic.com/research/building-effective-agents) — this is background reading that reinforces the architecture we introduced today.

---

*Module 1 of 9 | Agentic AI — A Professional 30-Hour Course*****
