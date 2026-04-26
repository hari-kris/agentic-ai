# Module 6 — Multi-Agent Systems
## Pre-Read: Flat Systems, Orchestrator-Workers, and Agent Handoffs

---

## Introduction: Why One Agent Is Not Enough

A single agent can plan, execute, evaluate, and refine. But there are three situations where one agent consistently underperforms:

1. **Scale**: The task requires more reasoning depth than a single context window can hold.
2. **Specialisation**: Different subtasks require different expertise, constraints, or output formats.
3. **Quality**: Independent critique and synthesis produce better results than self-assessment.

Multi-agent systems address all three. They distribute work across agents whose roles, prompts, and constraints are purpose-built for specific subtasks. Module 6 teaches three patterns: flat systems (independent agents, no coordination), orchestrator-workers (central coordination with typed specialists), and handoff pipelines (sequential state accumulation).

---

## Part 1 — Multi-Agent Basics

### Flat Multi-Agent Systems

In a flat system, all agents receive the same input and produce independent outputs. There is no shared state, no coordination, and no mechanism for resolving contradictions. Each agent is essentially running in isolation.

```
Input → [Agent A]  →  Output A
Input → [Agent B]  →  Output B
Input → [Agent C]  →  Output C
```

Flat systems are appropriate when:
- You need diverse perspectives and want them to remain uncorrelated
- Downstream consumers can process multiple viewpoints (e.g., a human reviewer)
- Speed matters more than coherence

Flat systems break down when:
- Agents produce contradictory outputs (Agent A says X; Agent C says not-X)
- A single downstream consumer needs one resolved answer
- Outputs build on each other conceptually but are produced in isolation

### Hierarchical Multi-Agent Systems

A hierarchical system adds a coordination layer. An orchestrator reads all agent outputs and produces a single integrated result. The agents themselves do not change — only the coordination layer is added.

```
Input → [Agent A]  ─┐
Input → [Agent B]  ─┤→ [ORCHESTRATOR] → Unified Output
Input → [Agent C]  ─┘
```

The orchestrator's value is not in being smarter than the agents — it is in having access to all agent outputs simultaneously. It can identify agreements (which strengthen the synthesis) and contradictions (which it must resolve).

### When to Choose Flat vs Hierarchical

| Scenario | Flat | Hierarchical |
|----------|------|--------------|
| Multiple independent opinions needed | ✓ | — |
| One coherent answer required | — | ✓ |
| Contradictions acceptable | ✓ | — |
| Contradictions must be resolved | — | ✓ |
| Cost is the primary constraint | ✓ (N calls) | — (N+1 calls) |
| Quality is the primary constraint | — | ✓ |

### The Coordination Cost Calculation

Adding an orchestrator adds exactly one LLM call. For N agents:
- Flat: N calls
- Hierarchical: N + 1 calls (orchestrator reads all N outputs)

The orchestrator input tokens grow with N, since it must process all agent outputs. For 3 agents producing ~250 words each, the orchestrator receives ~750 words of input before it writes its synthesis. This is generally a small cost relative to the quality gain.

### What "No Shared State" Means in Practice

In a flat system, each agent receives the same input prompt. They cannot read each other's outputs. Agent B does not know what Agent A concluded. This is both a feature (independence) and a bug (no coordination). If Agent A identifies an error and Agent B praises the same content, the contradiction is left to the user to resolve.

---

## Part 2 — Orchestrator-Workers Architecture

### The Manager-Team Analogy

The orchestrator-workers pattern maps directly to how human manager-team structures work. A manager:
- Holds the high-level goal in mind
- Decomposes it into discrete deliverables
- Assigns each deliverable to the most appropriate team member
- Collects completed work and synthesises it into a final output

The key insight: the manager does not do the work — the manager assigns it. If the manager is writing analysis themselves, they have failed to delegate.

### Goal Decomposition: The Orchestrator's Core Skill

The orchestrator's first task is decomposition. Given a complex goal, it must identify the distinct work types required and assign one clear task per worker. Good decomposition:
- Produces tasks that are non-overlapping (workers don't duplicate each other's work)
- Produces tasks that together cover the full goal (nothing is left unassigned)
- Assigns each task to the worker type best suited for it

Poor decomposition produces vague instructions ("research the market"), which force the worker to interpret the intent rather than execute a clear task.

### Typed Workers: Why Specialisation Matters

Workers are typed — each has a distinct system prompt that constrains its role, output format, and scope. A Research Worker is not a Risk Worker. This separation matters because:

1. **System prompts encode expertise**: The Research Worker's prompt instructs it to find concrete data; the Risk Worker's prompt instructs it to assess failure modes.
2. **Output constraints differ**: A Writer produces readable prose; an Analyst produces structured insights.
3. **Scope prevents role confusion**: Without typed workers, a general agent will attempt to do all subtasks in one pass, producing mediocre results across the board.

### What the Worker Receives (and What It Does Not)

Workers receive:
- Their own task instruction (specific and actionable)
- Minimal context about the broader goal (enough to make their task coherent)

Workers do NOT receive:
- The full task list assigned to other workers
- Other workers' outputs
- The orchestrator's reasoning about why this task was assigned

This isolation is intentional. If Worker B reads Worker A's output before producing its own, it will be biased by Worker A's framing. Independent execution produces more diverse and genuinely complementary outputs.

### Synthesising Worker Outputs into a Coherent Deliverable

The synthesiser (orchestrator second pass) reads all worker outputs and produces a unified deliverable. Effective synthesis:
- References each worker's contribution without merely summarising them
- Identifies overlaps and integrates them (if Research and Analysis both mention cost, the synthesis presents one unified cost picture)
- Surfaces contradictions explicitly (if Research says market is large, Risk says market is risky — the synthesis holds both)
- Produces a coherent document that could stand alone without the worker outputs

### Token Economics of Orchestration

The orchestrator-workers pattern is one of the most token-expensive patterns. For a 6-agent pipeline:
- Decomposer: ~400 input tokens + ~200 output tokens
- 4 workers × ~300 input tokens + ~250 output tokens each = ~2,200 tokens
- Synthesiser: ~1,200 input tokens (all 4 worker outputs) + ~500 output tokens

Total: ~4,500 tokens for a six-agent pipeline. Compare this to a single-agent call (~400 input + ~500 output = ~900 tokens). The quality gain per token is the design question.

### Orchestrator-Workers vs Orchestrator-Subagents (Hour 19)

| | Orchestrator-Workers (Hour 23) | Orchestrator-Subagents (Hour 19) |
|---|---|---|
| Task assignment | Static typed workers | Dynamic task description |
| Worker type | Fixed (RESEARCHER, ANALYST, etc.) | Flexible (described per task) |
| Number of workers | Fixed (one per type) | Variable (one per subtask) |
| Best for | Predictable task categories | Diverse, unpredictable goals |

---

## Part 3 — Agent Communication and Handoffs

### The Handoff Package Concept

A handoff package is a structured data object that accumulates information as it moves through a pipeline. Each agent:
1. Reads the full handoff package received so far
2. Adds its own contribution as a new field or section
3. Passes the enriched package to the next agent

```
Start:    {} (empty)
After A:  {legal_analysis: {...}}
After B:  {legal_analysis: {...}, risk_assessment: {...}}
After C:  {legal_analysis: {...}, risk_assessment: {...}, recommendation: "..."}
```

By the final agent, the package is a complete record of every prior agent's work. The final agent does not need to repeat any prior reasoning — it builds on it.

### Sequential Enrichment: Why Each Agent Adds, Not Replaces

Each agent's constraint is: add to the package, do not overwrite. This discipline is essential because:

1. **Traceability**: The full reasoning chain is preserved. If the final recommendation seems wrong, you can inspect the legal and risk findings that produced it.
2. **Downstream context**: Each agent can explicitly build on prior findings ("Given the Legal Agent's finding that the IP clause is ambiguous, the Risk Agent assigns a score of 4…")
3. **Debugging**: If the pipeline fails at Stage 3, you know exactly what Stages 1 and 2 produced.

### Handoff Schema Design: Structure Beats Prose

Handoff packages should be structured (JSON), not prose. Prose is readable but hard to parse programmatically. JSON:
- Allows downstream agents to reference specific fields (`legal_findings["jurisdiction"]`)
- Supports automated validation (check that required fields are present before passing to next agent)
- Enables partial handoffs (pass only the fields the next agent needs)

### Bidirectional Handoffs and Clarification Loops

Not all handoffs are unidirectional. A bidirectional handoff involves back-and-forth between two agents before the final output is produced:

```
Agent A → question → Agent B
          answer   ← Agent B
Agent A → final output (using question + answer)
```

This pattern is useful when:
- The task request is ambiguous and cannot be resolved without additional information
- The cost of producing a wrong output (and re-running) exceeds the cost of one clarifying question
- The clarification answer materially changes the output

### State Accumulation vs State Reset

In a handoff pipeline, state accumulates across agents. Each agent enriches the package. This is different from a stateless pipeline where each agent receives only the original input.

State accumulation enables:
- Each agent to build on prior work (the Risk Agent knows what the Legal Agent found)
- Downstream agents to produce tighter outputs (no need to repeat upstream reasoning)
- Full traceability of the reasoning chain

State accumulation requires:
- Package schemas that don't conflict between agents
- Validation that each agent's contribution is well-formed before passing it on
- Clear ownership of each field (only the Legal Agent writes to `legal_analysis`)

### Failure Modes: What Happens When a Handoff Package Is Corrupt

Common failure modes in handoff pipelines:

1. **Upstream JSON parse failure**: If the Legal Agent returns malformed JSON, the Risk Agent receives a corrupt package. Mitigation: validate and error-handle at each stage.
2. **Missing required fields**: If the Legal Agent omits `jurisdiction`, the Risk Agent may fail or produce a weaker assessment. Mitigation: explicit output schemas with required fields.
3. **Inconsistent data**: Legal Agent reports one jurisdiction; Risk Agent contradicts it. Mitigation: treat each agent's domain as exclusive — only the owning agent writes to its fields.

### Comparing Handoffs to Tool Use

| | Tool Use | Agent Handoffs |
|---|---|---|
| What passes | Tool result string | Structured data object |
| Who controls execution | Single LLM + tool executor | Multiple agents in sequence |
| State growth | Single context window | Accumulates across agents |
| Parallelism | Sequential within one agent | Could be parallel (independent stages) |
| Best for | External data retrieval | Sequential reasoning chain |

---

## Summary: Multi-Agent Design Principles

1. **Add a hierarchy only when you need coordination**. Flat systems are cheaper and simpler. Hierarchy costs one extra call but resolves contradictions.
2. **The orchestrator assigns, not executes**. If your orchestrator is writing analysis, it needs a worker.
3. **Type your workers**. Specialised prompts produce better outputs than generalised ones.
4. **Workers work in isolation from each other**. Do not show Worker B what Worker A concluded.
5. **Handoff packages grow, not reset**. Each agent adds new fields; none overwrites prior work.
6. **Use JSON for handoffs**. Prose is hard to reference programmatically; structured objects are reliable.
7. **Validate at each stage**. A corrupt handoff package at Stage 2 produces garbage at Stage 3.

---

## Checklist: When to Add a Second Agent

Ask yourself:
- [ ] Does the task have distinct subtasks that benefit from different constraints or expertise?
- [ ] Is a single context window insufficient for the full reasoning chain?
- [ ] Are multiple perspectives genuinely needed (rather than a single, thorough answer)?
- [ ] Does the output of one subtask need to inform another subtask?
- [ ] Is quality more important than token cost for this use case?

If you answered yes to two or more: a multi-agent architecture is likely justified.
