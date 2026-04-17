# Module 2 — Prompt Fundamentals
## Student Reading Material | Agentic AI Professional Course

---

> **Module Overview**  
> Before you can build agents, you must master prompts. This module teaches you the anatomy of a well-structured prompt, the distinct types of prompts used in agentic systems, and the techniques that transform vague instructions into reliable, repeatable behaviours. By the end of these four hours, you will be able to design prompts deliberately — not by trial and error.

---

## Hour 4 — Prompt Structure and Anatomy

### Why Prompt Structure Matters

When you write code, you follow syntax rules. When you write a prompt, you are also writing instructions — but in natural language. And natural language is ambiguous by design. The challenge is that LLMs do not fail loudly when given bad instructions. They confidently produce plausible-sounding output that may be entirely wrong. The solution is not to write better-sounding prompts — it is to write **structured** prompts.

A structured prompt eliminates ambiguity by making explicit what would otherwise be implicit: the role of the model, the task it must perform, the context it needs, and the shape of the output it should produce.

---

### The Six-Element Prompt Structure

Every production-quality prompt contains some or all of the following six elements. Understanding each element, and why it exists, is the foundation of everything else in this module.

---

#### Element 1: Role

**What it is:** A statement of who the model is pretending to be.

**Why it matters:** LLMs are trained on vast corpora. By assigning a role, you activate the relevant slice of that knowledge and adjust the model's tone, vocabulary, and frame of reference.

**Example:**
```
You are a senior software engineer with 15 years of Python experience.
```

**Without a role:**
```
Explain async programming.
```
This works, but produces a generic response. The model doesn't know if you are a student or a systems architect.

**With a role:**
```
You are a senior Python engineer. Explain async programming to a mid-level developer who understands functions and classes but has not yet used asyncio.
```
This produces a targeted, appropriately levelled response.

---

#### Element 2: Task

**What it is:** A clear, action-oriented statement of what the model must do.

**Why it matters:** Without an explicit task, the model guesses. Vague tasks produce vague outputs.

**Good task statements:**
- "Write a Python function that..."
- "Summarise the following document in three bullet points..."
- "Identify the five most common causes of..."
- "Compare the following two approaches and recommend one..."

**Common mistakes:**
- "Tell me about X" — no specific action
- "Help me with X" — unclear what help means
- "Think about X" — not an actionable instruction

**Rule:** Your task statement should begin with a verb. If it doesn't, rewrite it.

---

#### Element 3: Context

**What it is:** The background information the model needs to perform the task correctly.

**Why it matters:** The model has no access to your project, your organisation, or your intent. Without context, it makes assumptions. Those assumptions are often wrong.

**Types of context:**
- **Input data:** "Here is the document you will summarise: [document]"
- **Situational context:** "This is a B2B SaaS company serving mid-market financial services firms."
- **Constraints context:** "The user is a non-technical executive who does not read code."
- **Prior history:** "In the previous step, the model produced this plan: [plan]"

**In agentic systems,** context becomes critical. Each agent call receives the outputs of previous agents as part of its context. This is how information flows through an agentic pipeline.

---

#### Element 4: Constraints

**What it is:** Explicit rules about what the model must or must not do.

**Why it matters:** The model, left to its own devices, will make choices you didn't ask it to make. Constraints prevent that.

**Examples:**
```
- Do not include any code examples.
- Use only information from the provided document. Do not use external knowledge.
- Respond in a maximum of 200 words.
- Do not speculate. If you are uncertain, say so explicitly.
- Output only the JSON object. Do not include explanation text.
```

**In agentic systems,** constraints are especially important for safety. They prevent the model from taking actions outside its authorised scope.

---

#### Element 5: Output Format

**What it is:** A specification of the exact shape of the response.

**Why it matters:** Agentic systems need to parse model outputs programmatically. A response that is close to what you wanted is not the same as a response that your code can reliably process.

**Examples:**

Plain format:
```
Return your response as a numbered list of five items.
```

JSON format:
```
Return your response as a JSON object with the following keys:
- "summary": a string of no more than 100 words
- "key_points": a list of strings, maximum 5 items
- "confidence": a number between 0 and 1

Output only the JSON object. Do not include any other text.
```

**Why JSON matters for agents:** When Agent A produces output that Agent B must consume, Agent B needs predictable structure. A JSON schema solves this.

---

#### Element 6: Examples (Few-Shot)

**What it is:** One or more input-output pairs that demonstrate the expected behaviour.

**Why it matters:** Examples are the most efficient way to communicate intent. They show the model exactly what you want without relying on imprecise language.

**Zero-shot vs. few-shot:**
- **Zero-shot:** No examples. The model must infer everything from the instructions.
- **Few-shot:** One or more examples are provided. The model pattern-matches against them.

For structured, precise tasks — classification, formatting, extraction — few-shot prompts consistently outperform zero-shot.

---

### Assembling the Six Elements

Here is a complete, structured prompt using all six elements:

```
[ROLE]
You are a technical documentation specialist who writes clear, concise API documentation for developer audiences.

[TASK]
Write a reference entry for the Python function described below.

[CONTEXT]
Function name: chunk_text
Description: Takes a string and splits it into chunks of a specified maximum token length, preserving word boundaries.
Parameters:
  - text: str — the input text to be split
  - max_tokens: int — maximum tokens per chunk (default: 512)
Returns: List[str] — list of text chunks

[CONSTRAINTS]
- Use Google-style docstring format.
- Do not add information not present in the description above.
- Keep the description under 30 words.

[OUTPUT FORMAT]
Return only the Python docstring. Do not include any other text or the function signature.

[EXAMPLE]
Input: A simple addition function that takes two integers and returns their sum.
Output:
"""
Adds two integers.

Args:
    a (int): First integer.
    b (int): Second integer.

Returns:
    int: Sum of a and b.
"""
```

---

### The Iterative Prompt Refinement Habit

No prompt is correct on the first try. Treat every prompt like you treat code: write it, test it, observe the output, identify the failure, fix the failure. The difference between a junior and a senior AI engineer is not that the senior writes perfect prompts — it is that the senior knows *how* to diagnose and fix imperfect ones.

**Prompt debugging checklist:**
1. Is the role too vague or missing?
2. Does the task begin with a clear action verb?
3. Is the model missing context it would need to do the task?
4. Are the constraints explicit and unambiguous?
5. Is the output format clearly specified?
6. Would adding an example clarify the intent?

---

### Hour 4 Exercise

Rewrite the following three prompts into fully structured prompts using the six-element framework:

1. "Tell me about machine learning."
2. "Summarise this document."
3. "Write some Python code."

For each, decide: which elements are missing? What context do you need to invent? What output format makes sense?

---

## Hour 5 — Types of Prompts

### Why Type Classification Matters

Not all prompts do the same thing. In a single-turn conversation, this doesn't matter much. But in an agentic system, different components need different types of prompts. An orchestrator needs a planning prompt. A validator needs an evaluation prompt. A dispatcher needs a routing prompt. Mixing these up — or not knowing which type you need — is one of the most common causes of poorly behaved agentic systems.

Understanding prompt types is the equivalent of understanding design patterns in software engineering. Once you recognise the pattern, you know what to use and when.

---

### The Six Prompt Types

#### Type 1: Instruction Prompts

**Definition:** A prompt that tells the model to perform a direct, specific task.

**When to use:** When you have a well-defined task with a known input and expected output format. Instruction prompts are the most common type and form the foundation of all other types.

**Key characteristics:**
- Contains a clear action verb in the task
- Specifies input explicitly
- Specifies output format explicitly

**Example:**
```
Extract all dates mentioned in the following text and return them as a JSON list in ISO 8601 format.

Text: [input]
```

**In agentic systems:** Used by executor agents to perform concrete steps.

---

#### Type 2: Role Prompts (System Prompts)

**Definition:** A prompt that establishes the model's identity, persona, and behavioural boundaries for an entire session.

**When to use:** At the beginning of every agent session. Role prompts are typically placed in the system message, not the user message.

**Key characteristics:**
- Defines who the model is
- Sets behavioural boundaries (what it will and won't do)
- Establishes tone and communication style

**Example:**
```
You are a customer support agent for Meridian Software. You assist customers with billing, account management, and technical issues. You speak in a professional but friendly tone. You do not discuss competitor products. If asked about topics outside your scope, politely redirect to your domain.
```

**In agentic systems:** Every specialist agent begins with a role prompt that defines its scope. This is how a "billing agent" stays focused on billing even when the user tries to ask it about unrelated topics.

---

#### Type 3: Planning Prompts

**Definition:** A prompt that asks the model to decompose a complex goal into a sequence of subtasks.

**When to use:** At the beginning of a multi-step workflow. The planner produces a task list that executor agents then carry out.

**Key characteristics:**
- Asks for a step-by-step plan, not an answer
- Includes the goal and relevant constraints
- Specifies the output format of the plan

**Example:**
```
You are a project planner. Given the goal below, produce a numbered list of subtasks that, if executed in order, would achieve the goal.

Goal: Write a market analysis report for the UK electric vehicle sector targeting retail investors.

Constraints:
- Each subtask must be concrete and executable by a research agent.
- Maximum 7 subtasks.
- Each subtask must produce a specific output.

Return the subtasks as a numbered list with the format:
[n]. [Action verb] [specific deliverable]
```

**In agentic systems:** The planner is often the first agent in a pipeline. Its output drives the rest of the system.

---

#### Type 4: Tool-Use Prompts

**Definition:** A prompt that tells the model it has access to external tools and instructs it on how to use them.

**When to use:** When the model needs to call external functions — web search, calculators, APIs, databases — rather than relying solely on its parametric knowledge.

**Key characteristics:**
- Describes available tools and their parameters
- Instructs the model to emit tool calls in a specific format
- Handles the model's response after tools return results

**Example (simplified):**
```
You are a research assistant. You have access to the following tools:

web_search(query: str) → str: Searches the web and returns a summary.
get_current_date() → str: Returns today's date.

When you need information you don't have, emit a tool call in this format:
TOOL_CALL: tool_name(argument)

Wait for the tool result before continuing.
```

**In agentic systems:** Tool-use prompts are what distinguish agents from chatbots. They extend the model's capabilities beyond its training data.

---

#### Type 5: Routing Prompts

**Definition:** A prompt that asks the model to classify an input and return a routing decision.

**When to use:** When a system receives inputs of varying types and needs to dispatch them to the correct specialist agent or workflow path.

**Key characteristics:**
- Provides a classification schema
- Asks for a category label, not a full response
- Uses tightly constrained output format

**Example:**
```
You are a query classifier. Given the following customer message, classify it into exactly one of these categories:

- BILLING: Questions about invoices, payments, or charges
- TECHNICAL: Questions about product features, bugs, or errors
- ACCOUNT: Questions about account settings, passwords, or access
- ESCALATE: Complaints, threats, or requests to speak to a human

Customer message: [message]

Return only the category label. Do not include any other text.
```

**In agentic systems:** The router is the gateway of a multi-agent system. It ensures each input reaches the right specialist without wasting computation.

---

#### Type 6: Evaluation Prompts

**Definition:** A prompt that asks the model to judge the quality of another piece of text against explicit criteria.

**When to use:** In reflection loops, evaluator-optimizer patterns, and quality control steps.

**Key characteristics:**
- Provides explicit evaluation criteria
- Asks for a structured score or assessment
- May ask for specific feedback to enable improvement

**Example:**
```
You are a quality evaluator. Score the following text on three criteria, each from 1 to 5:

1. Accuracy: Does the text contain factual errors? (5 = no errors, 1 = significant errors)
2. Clarity: Is the text easy to understand? (5 = very clear, 1 = confusing)
3. Completeness: Does the text address all aspects of the topic? (5 = complete, 1 = severely incomplete)

Text to evaluate: [text]

Return your assessment as a JSON object:
{
  "accuracy": [score],
  "clarity": [score],
  "completeness": [score],
  "feedback": "[specific suggestions for improvement]"
}
```

**In agentic systems:** Evaluation prompts power the critic role. They close the feedback loop that enables self-improvement.

---

### Prompt Type Summary Table

| Type | Primary Role | Output | Used By |
|---|---|---|---|
| Instruction | Perform a task | Task result | Executor agents |
| Role | Define identity | (Sets behaviour, no direct output) | All agents |
| Planning | Decompose a goal | Subtask list | Planner agents |
| Tool-Use | Call external tools | Tool call + result | Tool-enabled agents |
| Routing | Classify input | Category label | Router agents |
| Evaluation | Judge quality | Score + feedback | Critic agents |

---

### Hour 5 Exercise

Given the following 10 prompts, classify each by type and justify your classification:

1. "You are a legal assistant specialising in contract review for UK law."
2. "Summarise the key points from this meeting transcript."
3. "Break down this goal into subtasks: Launch a product blog for our SaaS platform."
4. "You have access to a calculator tool. Use it to compute the compound interest."
5. "Determine whether this support ticket is a billing issue, technical issue, or other."
6. "Score this product description from 1-10 on persuasiveness and clarity."
7. "Extract all named entities from this news article."
8. "What steps would I need to take to set up a RAG system from scratch?"
9. "Is this customer complaint urgent? Respond with YES, NO, or UNCLEAR."
10. "Review this Python function and identify any bugs or anti-patterns."

---

## Hour 6 — Prompting Techniques I: Zero-Shot, Few-Shot, and Decomposition

### Introduction

Knowing the structure and types of prompts gives you the vocabulary. Prompting techniques give you the methods. This hour covers three foundational techniques that every agent builder must understand deeply: zero-shot prompting, few-shot prompting, and task decomposition.

---

### Technique 1: Zero-Shot Prompting

**Definition:** Asking the model to perform a task with no examples — only instructions.

**When it works well:**
- Simple, well-defined tasks
- Tasks the model has seen extensively in training
- When you need a quick result and the format is flexible

**When it struggles:**
- Precise formatting requirements
- Classification tasks with nuanced categories
- Tasks outside the model's training distribution

**Example — zero-shot classification:**
```
Classify the sentiment of the following review as Positive, Negative, or Neutral.

Review: "The product arrived quickly but the build quality was disappointing."
```

**Why it sometimes fails:** The model's interpretation of "Positive," "Negative," and "Neutral" may not match yours. With zero-shot, you are trusting the model's priors.

---

### Technique 2: Few-Shot Prompting

**Definition:** Providing one or more input-output examples before the actual input.

**The power of examples:** When you show the model what you want rather than just telling it, you bypass the ambiguity of language. Examples communicate both the format and the reasoning style you expect.

**Structure of a few-shot prompt:**
```
[Instruction]

[Example 1 input]
[Example 1 output]

[Example 2 input]
[Example 2 output]

[Actual input]
[Model generates output here]
```

**Example — few-shot classification:**
```
Classify the sentiment of each customer review. Use only: Positive, Negative, or Neutral.

Review: "Great product, arrived on time and works perfectly."
Sentiment: Positive

Review: "Total waste of money. Broke after one week."
Sentiment: Negative

Review: "It does what it says. Nothing special."
Sentiment: Neutral

Review: "The product arrived quickly but the build quality was disappointing."
Sentiment:
```

**Why this works better:** The model now has a concrete calibration of what you consider Positive vs. Negative. The ambiguous review about build quality is much more likely to be classified correctly.

---

### Choosing the Right Number of Examples

| Shots | Best for |
|---|---|
| 0 (zero-shot) | Simple tasks, flexible format |
| 1 (one-shot) | When one example is sufficient to demonstrate format |
| 2–5 (few-shot) | Classification, structured extraction, formatting tasks |
| 5+ | Rare; only when category variance is very high |

**Rule:** Use the minimum number of examples that achieves the required reliability. More examples consume tokens and increase cost.

---

### Technique 3: Task Decomposition

**Definition:** Breaking a complex, multi-step task into a sequence of simpler, individual prompts.

**The core insight:** LLMs are better at small, focused tasks than large, vague ones. A prompt that asks the model to "research, analyse, and write a report" produces worse results than three separate prompts that research, then analyse, then write.

**Why decomposition works:**
- Each step is independently verifiable
- Errors don't compound invisibly
- Each sub-prompt can be optimised for its specific task
- Intermediate outputs can be inspected and corrected

---

### Types of Decomposition

**Sequential decomposition:** Steps must happen in order because each step depends on the previous.

```
Step 1 (Research): Find the three most common causes of customer churn in SaaS.
↓
Step 2 (Analyse): For each cause identified, assess which is most addressable with product changes.
↓
Step 3 (Recommend): Produce a prioritised list of product recommendations.
```

**Parallel decomposition:** Steps are independent and can run simultaneously.

```
Task: Analyse this document from three perspectives simultaneously.
  Worker A: Extract all factual claims.
  Worker B: Identify logical inconsistencies.
  Worker C: Summarise the main argument.
→ Aggregator: Combine results into a final report.
```

---

### The Decomposition Prompt Pattern

When you want an agent to produce a decomposition plan:

```
You are a task planner. Given the goal below, produce a numbered list of subtasks. Each subtask must:
- Start with an action verb
- Produce a specific, concrete output
- Be executable independently by a language model
- Not require human input to complete

Goal: [goal]

Return the subtask list as a numbered list. No other text.
```

---

### Practical Comparison: Same Task, Different Techniques

**Task:** Write a blog post about the benefits of remote work.

**Zero-shot (single prompt):**
```
Write a blog post about the benefits of remote work.
```
Result: Generic, predictable, often too broad.

**Decomposition approach:**
```
Step 1: List 5 compelling, non-obvious benefits of remote work for knowledge workers.
Step 2: For each benefit, write one specific supporting statistic or study reference.
Step 3: Write an engaging opening paragraph that challenges the reader's assumptions.
Step 4: Write one paragraph for each benefit, weaving in the statistic.
Step 5: Write a closing paragraph with a strong call to action.
```
Result: Structured, evidence-based, and considerably higher quality at each step.

---

### Hour 6 Exercise

**Part A:** Solve the following problem with a zero-shot prompt and a few-shot prompt separately.

Task: Classify customer feedback into one of three categories: Feature Request, Bug Report, or General Praise.

Write both prompts, run them (mentally or actually with an LLM), and compare the quality and consistency of the outputs.

**Part B:** Decompose the following complex goal into a sequence of 4–6 concrete subtask prompts:

Goal: "Produce a competitive analysis of the top three project management tools for enterprise software teams."

---

## Hour 7 — Prompting Techniques II: Reflection, Critique, and Iterative Refinement

### Introduction

The techniques in this hour move beyond single-shot prompting into multi-step, self-improving interactions. Reflection and critique are the foundation of the **reflection agentic pattern** — one of the five core patterns in this course. Mastering these techniques here will make implementing that pattern in code straightforward.

---

### The Core Idea: Models Can Evaluate Their Own Output

LLMs are not just generators — they are also capable evaluators. Given a piece of text and a set of criteria, they can assess quality, identify weaknesses, and produce improvements. This capability enables something powerful: **self-improving loops**.

Instead of sending one prompt and accepting whatever comes back, you can:
1. Generate an initial output
2. Critique that output against explicit criteria
3. Rewrite the output incorporating the critique
4. Repeat until the output meets your quality threshold

---

### Technique 4: Reflection Prompting

**Definition:** A prompt that asks the model to review its own previous output and identify weaknesses.

**The two-prompt reflection pattern:**

**Prompt 1 (Generate):**
```
Write a 3-paragraph explanation of how transformers work, aimed at a developer who understands Python but has no ML background.
```

**Prompt 2 (Reflect):**
```
Below is an explanation of transformers written for a Python developer with no ML background.

[paste generated output]

Review this explanation against these criteria:
1. Clarity — Is every sentence understandable without ML knowledge?
2. Accuracy — Is any technical claim imprecise or misleading?
3. Completeness — Does it cover the core mechanism (attention, encoding, output)?
4. Engagement — Does it use analogies or examples that a developer would find familiar?

For each criterion, score it 1-5 and explain exactly what could be improved. Be specific.
```

**Why specificity matters in critique prompts:** Vague critique ("it could be better") produces vague improvements. Specific critique ("the explanation of attention scores in paragraph 2 uses the term 'softmax' without defining it, and a developer with no ML background will not understand this") produces actionable improvements.

---

### Technique 5: Critique-and-Rewrite

**Definition:** An extension of reflection prompting that chains critique directly into a rewrite step.

**Three-prompt pattern:**

```
Prompt 1: [Generate initial output]

Prompt 2: Critique the output above. Identify 3 specific weaknesses.

Prompt 3: Rewrite the output, fixing each weakness identified in the critique. 
           Output only the rewritten version.
```

**Combined single-prompt version (critique + rewrite):**
```
Review the text below. Identify its three most significant weaknesses. Then rewrite it to fix those weaknesses.

Text: [text]

Format your response as:
WEAKNESSES:
1. [weakness]
2. [weakness]
3. [weakness]

REWRITTEN VERSION:
[rewritten text]
```

The single-prompt version is more efficient but gives you less control. The three-prompt version lets you inspect the critique before the rewrite proceeds.

---

### Technique 6: Iterative Refinement Loops

**Definition:** Running critique-and-rewrite cycles multiple times until a quality threshold is met.

**Loop structure:**

```python
output = generate(goal)

for round in range(max_rounds):
    critique = evaluate(output, criteria)
    score = extract_score(critique)
    
    if score >= threshold:
        break
    
    output = rewrite(output, critique)

return output
```

**Key design decisions in refinement loops:**

1. **Stopping condition:** When do you stop? Options:
   - Fixed number of rounds (simplest)
   - Score threshold (quality-driven)
   - Score convergence (stop when improvement is marginal)

2. **Evaluation criteria:** What are you scoring? The more specific the criteria, the better the feedback signal.

3. **Rewrite scope:** Full rewrite vs. targeted edits. Targeted edits preserve what's good; full rewrites can lose it.

---

### Designing Evaluation Criteria for Refinement Loops

The quality of a refinement loop is entirely determined by the quality of its evaluation criteria. Weak criteria produce weak signal.

**Weak criteria:**
- "Is this good?"
- "Rate the quality."
- "Is this clear?"

**Strong criteria:**
```
Evaluate the text on these specific dimensions:

1. Technical accuracy (1-5): Does every factual claim have a valid basis? Is any claim potentially misleading?
2. Audience fit (1-5): Is the vocabulary, depth, and assumed knowledge appropriate for a non-technical manager?
3. Actionability (1-5): Can the reader immediately act on the recommendations, or are they too abstract?
4. Structure (1-5): Does the structure guide the reader clearly? Are there logical gaps or jumps?

For each dimension, give a score and one specific improvement action.
```

---

### Agentic Implementation: The Critic Agent

In an agentic system, the reflection loop becomes explicit architecture:

```
User Goal
    ↓
[Generator Agent] → Initial Output
    ↓
[Critic Agent] ← Initial Output
    ↓
Critique with Scores
    ↓
[Generator Agent] ← Critique + Initial Output → Improved Output
    ↓
[Critic Agent] ← Improved Output → Check threshold
    ↓ (if threshold met)
Final Output
```

The Generator and Critic are separate prompts — sometimes separate agents with different personas. A common pattern is to give the Critic a different role from the Generator to avoid sycophancy:

```
Generator role: "You are a persuasive copywriter."
Critic role: "You are a sceptical editor. Your job is to find weaknesses, not praise strengths."
```

---

### The Sycophancy Problem

LLMs have a tendency toward sycophancy — agreeing with the human's apparent preferences, or in the case of self-critique, going easy on their own output. This is a known training artefact.

**Mitigations:**
1. Give the critic an adversarial persona explicitly: "Your job is to find every weakness. Do not soften your critique."
2. Ask for a minimum number of improvements: "Identify at least three specific weaknesses, even if the output is generally good."
3. Ask for specific examples of where the output failed, not just categories: "Quote the exact sentence that is problematic and explain why."

---

### Hour 7 Exercise

**Implement a 3-iteration prompt refinement loop in Python for a content writing task.**

Your loop should:
1. Generate an initial blog introduction on a topic of your choice
2. Evaluate it against 3 specific criteria (clarity, hook strength, relevance) with scores 1-5
3. If any score is below 4, rewrite to fix the specific weaknesses
4. Repeat up to 3 times
5. Print the output of each round and the final result

**Starter structure:**

```python
import anthropic

client = anthropic.Anthropic()

TOPIC = "Why software engineers should learn to build agentic AI systems"

GENERATOR_PROMPT = """
Write a 3-sentence blog introduction about: {topic}

The introduction must: hook the reader immediately, establish the problem, and hint at the solution.
"""

CRITIC_PROMPT = """
Evaluate this blog introduction on three criteria, each scored 1-5:

1. Hook strength (1-5): Does the first sentence immediately grab attention?
2. Clarity (1-5): Is the problem/solution clearly established?
3. Specificity (1-5): Are concrete details used rather than vague generalities?

Introduction: {introduction}

Return a JSON object:
{{
  "hook": [score],
  "clarity": [score],
  "specificity": [score],
  "feedback": "[specific improvements]"
}}
Return only the JSON. No other text.
"""

REWRITE_PROMPT = """
Rewrite the following blog introduction to fix these specific issues: {feedback}

Original introduction: {introduction}

Return only the rewritten introduction. No other text.
"""

# Your implementation here
```

---

## Module 2 Summary

| Hour | Topic | Key Concepts |
|---|---|---|
| 4 | Prompt Structure | Role, Task, Context, Constraints, Output Format, Examples |
| 5 | Prompt Types | Instruction, Role, Planning, Tool-Use, Routing, Evaluation |
| 6 | Techniques I | Zero-shot, Few-shot, Task decomposition |
| 7 | Techniques II | Reflection, Critique-and-rewrite, Iterative refinement loops |

### The Big Picture

Prompts are not magic incantations — they are engineering artifacts. They have structure, types, and failure modes. They can be tested, iterated, and improved. Every technique in this module corresponds directly to an agentic pattern you will implement in later modules:

- **Structured prompts** → Foundation of every agent
- **Prompt types** → Map to agent roles (router, planner, critic, executor)
- **Decomposition** → Planning pattern
- **Few-shot** → Better performance on specialist tasks
- **Reflection loops** → Reflection pattern
- **Evaluator prompts** → Evaluator-optimizer pattern

Master this module and the rest of the course will feel like assembly — because it is.

---

## Recommended Reading and Resources

- **Anthropic Prompt Engineering Guide**: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview
- **OpenAI Prompt Engineering**: https://platform.openai.com/docs/guides/prompt-engineering
- **DeepLearning.AI ChatGPT Prompt Engineering for Developers**: https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/
- **DAIR.AI Prompt Engineering Guide**: https://www.promptingguide.ai/

---

*Module 2 Reading Material — Agentic AI Professional Course*  
*Version 1.0 | For participant use only*
