# Module 5 — Core Agentic Patterns II
## Pre-Read: Routing, Parallelisation, Orchestrator-Subagents, and Evaluator-Optimizer

**Agentic AI: A Professional 30-Hour Course**
*Hours 17–21 | Read before attending the lab sessions*

---

## Introduction: The Next Four Patterns

Module 4 gave you four foundational patterns: Reflection, Tool Use, Planning, and Prompt Chaining. With these alone you can build a large fraction of real-world agentic systems.

Module 5 adds four more patterns that change the *structure* of how agents connect:

| Pattern | What changes |
|---------|-------------|
| **Routing** | Requests follow different paths based on their content |
| **Parallelisation** | Multiple agents work simultaneously on the same input |
| **Orchestrator-Subagents** | A coordinator dynamically assembles and directs a team |
| **Evaluator-Optimizer** | A generate-evaluate-improve loop with an explicit stop condition |

The patterns from Module 4 were mostly *linear* — one stage feeds the next in a fixed sequence. The patterns in Module 5 are primarily about *structure*: branching, fanning out, dynamic delegation, and iterative loops. Used together with the Module 4 patterns, they cover almost every production agentic architecture in use today.

---

## Pattern 5 — Routing

### What It Is

The routing pattern uses a classifier agent to decide which sub-pipeline should handle each incoming request. Instead of sending every input to the same pipeline, the router reads the input and returns a structured routing decision. Python code then dispatches to the correct handler.

```
User input → [ROUTER] → routing decision (JSON) → Python dispatches → [Pipeline A | B | C]
```

The router itself does not answer the user's question. Its only job is classification.

### Why Routing Matters

Without routing, every agent handles every input, which usually means one of two problems:
1. A generalist that handles everything adequately but nothing excellently
2. A specialist that handles its domain well but produces garbage outside it

Routing solves both problems by matching inputs to the agents best suited for them.

A support chatbot without routing treats a billing complaint, a bug report, and an account deletion the same way. With routing, each reaches the appropriate specialist with the context it needs.

### Anatomy of a Routing Decision

A well-designed router returns structured JSON so Python can branch deterministically:

```json
{
  "route": "TECH",
  "confidence": 0.94,
  "reason": "User is asking about Python package installation — a software engineering question"
}
```

The three fields are all important:
- `route`: the destination pipeline — must match a key in your dispatch table
- `confidence`: a float 0.0–1.0 — below a threshold (typically 0.6), fall back to a human or general handler
- `reason`: a short explanation — essential for debugging when the router misclassifies

### Routing Variants

**Single-level routing** is the simplest form: one router, N destination pipelines. Each pipeline is independent.

**Multi-level routing** chains routers: a primary router classifies the domain, then each domain has a secondary router that classifies sub-type. Useful when categories are nested (e.g., TECH → {database, networking, frontend, security}).

**Complexity-based routing** routes not on *what* the input is about but *how hard* it is. Simple factual questions go to a fast, cheap path. Complex analytical questions go to a deeper, more expensive path. This dramatically reduces cost without sacrificing quality on easy cases.

**Confidence-based fallback** treats low-confidence routing decisions as a special route: `ESCALATE`. When the router is uncertain, the fallback pipeline can ask a clarifying question, escalate to a human, or run the input through multiple specialists and let a synthesiser decide.

### The Router System Prompt

The router's system prompt must be precise about:
1. The exact route labels it should return (uppercase, no variations)
2. What each category includes and excludes
3. The confidence scale
4. The exact JSON format with zero tolerance for markdown fences

```
You are a request classifier. Given a user message, identify the most appropriate routing category.

Categories:
- TECH: software, hardware, programming, IT, data, networking
- BILLING: payments, invoices, subscriptions, refunds
- SUPPORT: account access, features, how-to questions
- GENERAL: anything that does not fit the above

Confidence: 1.0 = completely certain, 0.5 = about equal chance of two categories,
0.0 = no idea.

Return ONLY valid JSON, no markdown fences:
{"route": "TECH|BILLING|SUPPORT|GENERAL", "confidence": 0.0–1.0, "reason": "one sentence"}
```

### What Routing Is Not

Routing is *not* the same as planning. A planner decides *what steps to take* to achieve a goal. A router decides *which agent should handle* the current input. The planner is goal-directed; the router is input-directed.

Routing is also not a tool call. A tool call extends an agent's capabilities. Routing changes which agent is running.

### When to Use Routing

Use routing when:
- Different input types genuinely require different expertise or different output formats
- You want to protect specialists from irrelevant inputs
- Cost control matters — routing to a cheap fast path for simple queries
- Confidence-based escalation is required (human-in-the-loop)

Avoid routing when:
- A single well-written system prompt can handle all input types adequately
- The categories are so similar that the router will misclassify frequently
- The overhead of the classification call is not justified by the quality gain

---

## Pattern 6 — Parallelisation

### What It Is

Parallelisation sends the same input to multiple agents simultaneously and then aggregates their outputs. Where routing sends an input to *one* of N pipelines, parallelisation sends it to *all* (or many) of them at once.

```
Input → [Agent 1 | Agent 2 | Agent 3] → Aggregator → Output
         (all three receive the same input)
```

There are two primary sub-types:

**Fan-out (sectioning):** Each agent handles a *different aspect* of the same input. A document analysis pipeline might fan out to a summarizer, a risk analyst, and an opportunity finder — all looking at the same document from different angles. The aggregator then synthesises the three perspectives.

**Voting (consensus):** The same task is sent to *multiple instances* of the same (or similar) agent, often with different temperatures or model settings. Outputs are compared and a majority vote or synthesised consensus is produced. This is used when reliability matters more than speed — if 3 out of 4 agents give the same answer, the probability that answer is correct is higher than if only one agent was consulted.

### Why Parallelisation Matters

**Fan-out improves coverage.** A single agent with a long system prompt covering risk analysis, summarisation, and opportunity identification will trade depth for breadth. Each specialist can go deep without being pulled in multiple directions. A security reviewer that only thinks about security will catch more security issues than a general code reviewer that also thinks about performance and readability.

**Voting improves reliability.** On high-stakes tasks — medical summaries, legal analysis, financial classification — the cost of a wrong answer is high. Running the same input through 3–5 agents and taking the majority answer significantly reduces single-model error rates.

**Wall-clock speed.** In production systems where agents run asynchronously, N agents running in parallel takes the time of *one* agent call, not N. Even in a Python/Streamlit context where calls are sequential in code, understanding the parallelisation structure is essential for design.

### The Aggregator

Parallelisation without aggregation is just redundant work. The aggregator agent's job is to:
1. Receive all specialist outputs
2. Identify complementary insights (what each specialist found that others missed)
3. Identify conflicts (if risk analyst says "high risk" but opportunity analyst says "strong buy", the aggregator must reconcile)
4. Produce a synthesised output that is better than any individual specialist's output

The aggregator system prompt must instruct it to reference all inputs, not just the most recent or most prominent.

### Voting Implementation

For classification tasks (sentiment, routing, labelling), voting works by:
1. Running N agents on the same input
2. Counting the most common label
3. Computing agreement percentage (6/6 = 100% confidence; 3/6 = 50% = uncertain)

For generative tasks (summaries, explanations), voting is more nuanced. You can:
- Choose the output of the highest-scoring agent (if agents score each other)
- Ask a meta-agent to synthesise the N outputs
- Pick the "median" output (most similar to all others) as the most representative

### When to Use Parallelisation

Use fan-out when:
- One document needs to be analysed through multiple lenses simultaneously
- You want comprehensive coverage without a single agent becoming too broad
- Different aspects require genuinely different expertise

Use voting when:
- Accuracy is more important than cost
- The task is a classification or binary decision
- You need a confidence signal (agreement rate)
- A single-model error rate is unacceptably high

Avoid parallelisation when:
- Agents are likely to produce contradictory results that are hard to resolve
- The cost of N API calls is not justified by the marginal quality gain
- Order matters — later agents need the output of earlier ones

---

## Pattern 7 — Orchestrator-Subagents

### What It Is

An orchestrator is an agent that coordinates other agents (subagents) to accomplish a goal. Unlike parallelisation (which fans out to a *fixed* set of agents), an orchestrator *dynamically* decides:
- Which subagents to spawn
- What task to assign each
- In what order
- How to handle failures and re-delegations

```
Goal → [ORCHESTRATOR] → decides team composition and task assignments
                     ↓
         [Subagent 1] [Subagent 2] [Subagent 3]  ← dynamically chosen
                     ↓
         [ORCHESTRATOR] synthesises results → Final output
```

### Why This Is Different from Planning

The planning pattern (Module 4) creates a fixed sequence of steps before execution starts. Once the plan is created, execution follows it rigidly. An orchestrator, by contrast, can:
- Inspect intermediate results and change course
- Decide to spawn an additional subagent based on what it finds
- Re-delegate a task to a different subagent if the first one fails or produces low-quality output
- Terminate early if a satisfactory result is found

Orchestration is *adaptive*. Planning is *static*. Use planning when the goal is well-understood and the steps are predictable. Use orchestration when the task is open-ended or the best approach cannot be determined until you see intermediate results.

### The Orchestrator System Prompt

The orchestrator is the most complex role in any multi-agent system. Its system prompt must cover:

1. **Task decomposition**: how to break the goal into subagent assignments
2. **Delegation format**: what information each subagent needs in its task brief
3. **Quality check**: criteria for deciding if a subagent's output is acceptable
4. **Re-delegation**: what to do if a subagent output is insufficient
5. **Synthesis**: how to combine subagent outputs into a final result

A key design decision: should the orchestrator know the specific capabilities of each specialist, or should it describe the task and let a router/dispatch layer assign specialists? In most implementations, the orchestrator knows its specialists by name and selects them explicitly.

### Subagent Design Principles

Subagents in an orchestration pattern share three characteristics:

**Single responsibility.** Each subagent handles one clearly defined type of work. A research subagent finds information. An editor subagent improves prose. They do not do each other's jobs.

**Isolated context.** Each subagent receives only the context it needs for its task. It does not need to know about the overall goal or the other subagents. Its system prompt, input, and output format are entirely self-contained.

**Structured output.** Subagents should return output in a format the orchestrator can parse and act on. Free prose from a subagent makes synthesis harder. JSON or structured markdown with defined sections makes orchestration reliable.

### Handling Failure

In a real orchestration system, subagents fail. Network errors, API rate limits, parsing failures, low-quality outputs — all of these happen in production. The orchestrator must have explicit logic for:

**Retrying**: call the same subagent again with a refined task brief
**Re-delegating**: assign the task to a different specialist
**Partial synthesis**: proceed with the subagents that succeeded; flag the missing parts in the final output
**Escalating**: surface the failure to a human operator

In the labs, we simulate failure with a quality threshold check: if a subagent's output is below a threshold score, the orchestrator re-delegates.

### When to Use Orchestrator-Subagents

Use orchestration when:
- The task requires different types of expertise that cannot all fit in one system prompt
- The optimal approach depends on intermediate results
- You need adaptive re-routing or quality-gating between steps
- The task is complex enough that a single agent would lose coherence

Avoid orchestration when:
- A well-written single-agent prompt can handle the full task
- The overhead of orchestrator token usage is not justified
- The task has a fixed, known structure (use planning instead)

---

## Pattern 8 — Evaluator-Optimizer

### What It Is

The Evaluator-Optimizer pattern creates an explicit quality improvement loop: a generator produces output, an evaluator scores it against specific criteria, and if the scores fall below a threshold, an optimizer improves it. The loop repeats until the threshold is met or a maximum round count is reached.

```
Task → [GENERATOR] → draft
         ↓
      [EVALUATOR] → scores (JSON) + feedback
         ↓
   [threshold check]
   ├── scores ≥ threshold → done
   └── scores < threshold → [OPTIMIZER] → improved draft → back to [EVALUATOR]
```

### How It Differs from Reflection

Both Evaluator-Optimizer and Reflection (Module 4) use a generate → critique → improve loop. The differences are important:

| | Reflection | Evaluator-Optimizer |
|---|---|---|
| **Criteria** | General quality | Domain-specific, predefined |
| **Threshold** | None (fixed rounds) | Explicit score threshold |
| **Termination** | Always runs N rounds | Terminates when quality is met |
| **Optimization target** | General improvement | Specific criteria to maximize |

Reflection is best when you want general improvement across any content. Evaluator-Optimizer is best when you have a specific definition of "good enough" and want the loop to stop once that definition is satisfied — avoiding unnecessary API calls when quality is already high.

### Designing the Evaluator

The evaluator is the linchpin of this pattern. A weak evaluator produces noise — the optimizer receives inaccurate feedback and makes changes in the wrong direction. A strong evaluator is:

**Criteria-specific.** Score dimensions should be independent and unambiguous. "Clarity" and "conciseness" are separate dimensions. "Good writing" is not a useful single dimension.

**Strict.** The evaluator should reserve 4 and 5 for genuinely excellent work. If the evaluator is lenient, the optimizer never receives the signal to keep improving.

**Actionable in feedback.** The feedback field should name one specific thing to fix, not a vague instruction like "improve clarity". Bad: "Make it clearer." Good: "The second paragraph assumes knowledge of Bayesian inference — define the term on first use."

**Deterministic where possible.** Use `temperature=0.1` for evaluators. They should not be creative; they should be consistent.

### Designing the Optimizer

The optimizer receives: the original task, the current draft, and the evaluator's scores plus feedback. Its job is targeted improvement:
- Address the specific feedback
- Maintain all the things the evaluator scored highly
- Do not change scope or length drastically

A common failure mode: the optimizer over-corrects. If clarity is 3/5 and efficiency is 5/5, an optimizer that blindly "improves" may boost clarity to 4/5 but drop efficiency to 3/5. The optimizer's system prompt must explicitly instruct it to preserve high-scoring dimensions while targeting the low ones.

### Threshold Design

The threshold determines how many rounds the loop runs. Too low → poor output. Too high → many unnecessary rounds.

For most production use cases:
- Use a **per-dimension threshold** (each criterion must reach the target, not just an average)
- Set thresholds at 3/5 or 4/5 depending on quality requirements
- Cap rounds at 3–5 to prevent infinite loops
- Log per-round scores to detect plateaus

A **plateau** occurs when the optimizer makes no meaningful improvement between rounds. This typically happens when:
- The feedback is not actionable enough
- The model has reached its ability ceiling on this task
- The criteria are in conflict (improving one reduces another)

When you detect a plateau (score delta < 0.2 between rounds), terminate early — additional rounds waste tokens without improving output.

### When to Use Evaluator-Optimizer

Use Evaluator-Optimizer when:
- You have specific, measurable quality criteria for the output
- Quality requirements are strict enough that a single generation pass is insufficient
- You need a principled stopping condition (not just "run 3 rounds")
- The task domain has well-defined correctness metrics (code, prompts, formal writing)

Avoid Evaluator-Optimizer when:
- Quality criteria are subjective and hard to specify
- A single well-prompted generation produces acceptable results
- The cost of multiple rounds is not justified

---

## Combining the Module 5 Patterns

In production systems, these four patterns compose naturally:

### Pattern: Routed Fan-Out

Route the input first, then fan out to specialists in the matched domain:

```
Input → [ROUTER] → TECH route
                     ↓
         [Security | Performance | Readability] (fan-out)
                     ↓
              [Aggregator] → Combined review
```

This combines routing's precision (each domain gets the right specialists) with parallelisation's coverage (multiple angles simultaneously).

### Pattern: Orchestrated Evaluation Loop

An orchestrator assembles a team, runs them in parallel, collects results, and then passes the synthesised draft through an evaluator-optimizer loop:

```
Goal → [ORCHESTRATOR] → team assignments
             ↓
    [Subagents in parallel] → individual outputs
             ↓
       [ORCHESTRATOR synthesises] → draft
             ↓
    [EVALUATOR-OPTIMIZER loop] → final output
```

This is the pattern used in the capstone lab (Hour 21) and is representative of how production research assistant pipelines are built.

### Pattern: Adaptive Routing with Quality Gate

A router makes an initial decision, but a quality gate (evaluator) checks the output and can re-route if quality is insufficient:

```
Input → [ROUTER] → Pipeline A → Output
                                  ↓
                            [EVALUATOR]
                            ├── quality OK → done
                            └── quality low → [ROUTER] tries Pipeline B
```

This is common in document processing where the correct handler is not always obvious from the input alone.

---

## Module 5 at a Glance

| Hour | Lab | Pattern | Key skill |
|------|-----|---------|-----------|
| 17 | Routing Pattern | Routing | Structured classification JSON; confidence-based fallback |
| 18 | Parallelisation Pattern | Parallelisation | Fan-out to specialists; voting; aggregation |
| 19 | Orchestrator-Subagents | Orchestrator-Subagents | Dynamic team assembly; re-delegation; synthesis |
| 20 | Evaluator-Optimizer | Evaluator-Optimizer | Loop with threshold; plateau detection; criteria design |
| 21 | Combine Patterns II | All four | Full pipeline: route → fan-out → orchestrate → evaluate |

---

## Key Vocabulary

| Term | Definition |
|------|-----------|
| **Route** | A named destination pipeline; the output of a router's classification |
| **Confidence** | A float 0–1 expressing a router's certainty about its classification |
| **Fallback** | The route taken when confidence is below threshold |
| **Fan-out** | Sending the same input to multiple agents simultaneously |
| **Voting** | Running the same task N times and aggregating results by agreement |
| **Aggregator** | An agent that synthesises outputs from a fan-out into one result |
| **Orchestrator** | An agent that coordinates other agents; makes dynamic delegation decisions |
| **Subagent** | An agent that receives task assignments from an orchestrator |
| **Re-delegation** | Assigning a failed or low-quality subagent task to a different agent |
| **Evaluator** | An agent that scores output against predefined criteria; returns structured JSON |
| **Optimizer** | An agent that improves a draft based on evaluator feedback |
| **Threshold** | The minimum score an output must achieve before the loop terminates |
| **Plateau** | A state where additional optimizer rounds produce no meaningful score improvement |
| **Wall-clock time** | Elapsed real time; N parallel agents take the time of 1, not N |

---

## What You Will Build in Module 5

**Hour 17** — A domain router that classifies questions into TECH / MEDICAL / FINANCE / LEGAL / GENERAL and dispatches to the correct specialist. You will see how routing decisions are structured, how confidence gates work, and what happens when a router is uncertain.

**Hour 18** — A fan-out document analyser that sends the same document to three specialists simultaneously (Summarizer, Risk Analyst, Opportunity Analyst) and an aggregator that synthesises their outputs. You will also build a voting system that sends the same question to multiple agents and tallies agreement.

**Hour 19** — A dynamic research orchestrator that decomposes a question into sub-questions, assigns them to specialised researcher subagents, inspects output quality, and synthesises a final report. You will implement re-delegation logic for low-quality subagent outputs.

**Hour 20** — A code quality evaluator-optimizer loop that generates Python code, scores it on four criteria, and iteratively improves it until all scores reach the threshold (or the maximum round limit is hit). You will see how plateau detection works and why the optimizer must preserve high-scoring dimensions.

**Hour 21** — The Module 5 capstone: a smart content pipeline that routes the input type, fans out to specialists, orchestrates subagent results, and runs the synthesised draft through an evaluator-optimizer loop. All four new patterns working together.

---

*Module 5 of 9 | Agentic AI — A Professional 30-Hour Course*
