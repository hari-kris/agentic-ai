"""
Hour 9 Lab — Agent Types I: Router, Planner, Executor, Critic
Module 3 | Agent Types and Components

Four agent types introduced in this hour:
  Router   — classifies input and directs it to the right handler
  Planner  — decomposes a goal into an ordered sequence of steps
  Executor — carries out a single concrete task and produces output
  Critic   — evaluates output against criteria and returns structured feedback

Sections:
  1. Agent type gallery — one card per type with definition, prompt snippet, I/O shape
  2. Live comparison   — same input handled by Router, Planner, Executor; Critic evaluates Executor's output
  3. Task mapping quiz — match 5 real-world tasks to the correct agent type

Run: streamlit run hour9_lab_agent_types_i.py
"""

import json
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Hour 9 — Agent Types I", page_icon="🤖", layout="wide")
st.title("🤖 Hour 9 — Agent Types I")
st.caption("Module 3 | Agent Types and Components")

st.markdown(
    """
Agents are not all the same. A well-designed multi-agent system assigns each agent a **single,
well-defined role**. This hour covers the four fundamental agent types every agentic system uses.
"""
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Hour 9 Guide")
    st.markdown(
        """
**Three sections in this lab:**

1. **Gallery** — Read each agent type: definition, canonical prompt pattern, and when to use it.

2. **Live Comparison** — Send one input to all four types and watch how each agent's role shapes its response. The Critic evaluates the Executor's output — this shows the natural dependency between them.

3. **Task Mapping Quiz** — Match 5 real tasks to the correct agent type and write a justification. Claude evaluates your reasoning.
"""
    )
    st.divider()
    st.markdown("**What to observe in the comparison:**")
    st.markdown("- Router gives a **label**, not an answer")
    st.markdown("- Planner gives **steps**, not results")
    st.markdown("- Executor gives a **concrete output** immediately")
    st.markdown("- Critic **evaluates** the Executor's output — it never generates content itself")
    st.divider()
    st.markdown("**The design rule:**")
    st.info(
        "Each agent should be describable in one sentence starting with a verb. "
        "If your sentence needs two verbs and 'and' — you have two agents."
    )

# ── Agent type definitions ────────────────────────────────────────────────────

AGENT_TYPES = [
    {
        "name": "Router",
        "icon": "🔀",
        "color": "#00897B",
        "bg": "#E0F2F1",
        "definition": "Classifies an incoming request and directs it to the appropriate handler. Returns a label, not an answer.",
        "analogy": "A telephone operator who hears your question and connects you to the right department.",
        "input": "Raw user request",
        "output": "A label / route (e.g. BILLING, TECHNICAL, GENERAL)",
        "prompt_snippet": "Classify this request as exactly one of: BILLING, TECHNICAL, GENERAL.\nReturn ONLY the label.",
        "when_to_use": "When a system receives heterogeneous inputs that require different downstream handling.",
        "system_prompt": """\
You are a routing agent. Your only job is to classify the incoming request into exactly one category.

Categories:
- TECHNICAL: bugs, errors, performance, code, integrations
- BILLING: payments, invoices, subscriptions, pricing, refunds
- GENERAL: product questions, onboarding, feature requests, other

Rules:
- Return ONLY the category label, nothing else.
- Never answer the question — only route it.\
""",
    },
    {
        "name": "Planner",
        "icon": "📋",
        "color": "#8E24AA",
        "bg": "#F3E5F5",
        "definition": "Decomposes a high-level goal into an ordered sequence of concrete steps. Does not execute — only plans.",
        "analogy": "A project manager who breaks a brief into a sprint backlog before any developer writes a line of code.",
        "input": "A goal or objective",
        "output": "An ordered list of steps (the plan)",
        "prompt_snippet": "Break this goal into 4 concrete, ordered steps.\nReturn ONLY the numbered list — do not execute any step.",
        "when_to_use": "When a goal is too complex for a single LLM call and requires sequential sub-tasks.",
        "system_prompt": """\
You are a planning agent. Given a goal, decompose it into exactly 4 concrete, ordered, actionable steps.

Rules:
- Each step must be specific enough for an executor to carry out without further clarification.
- Do not execute any step — only plan.
- Return ONLY a numbered list, one step per line.\
""",
    },
    {
        "name": "Executor",
        "icon": "⚡",
        "color": "#1E88E5",
        "bg": "#E3F2FD",
        "definition": "Carries out a single, concrete task and produces a real output. Does not plan — only executes.",
        "analogy": "A specialist contractor brought in to do one specific job, not to manage the project.",
        "input": "A specific task (often one step from a Planner's output)",
        "output": "The actual result — written content, code, analysis, data",
        "prompt_snippet": "Carry out this task immediately. Produce a concrete, detailed output.\nDo not plan, do not list options — just do it.",
        "when_to_use": "For each concrete subtask in a plan, or any well-defined atomic unit of work.",
        "system_prompt": """\
You are an executor agent. You receive a specific, concrete task and you do it immediately.

Rules:
- Produce a real, detailed, useful output — not a plan, not a list of options.
- Do not explain what you are about to do — just do it.
- If the task has a format requirement, follow it exactly.\
""",
    },
    {
        "name": "Critic",
        "icon": "🔍",
        "color": "#E53935",
        "bg": "#FFEBEE",
        "definition": "Evaluates output against defined criteria and returns structured scores and feedback. Does not produce content — only judges it.",
        "analogy": "A quality assurance reviewer who reads every output before it reaches the customer.",
        "input": "Produced output + evaluation criteria",
        "output": "Structured scores + specific, actionable feedback",
        "prompt_snippet": "Score this output on clarity, accuracy, and relevance (1–5 each).\nReturn ONLY valid JSON with scores and one sentence of feedback.",
        "when_to_use": "After any Executor output — before it reaches the user or triggers the next pipeline step.",
        "system_prompt": """\
You are a critic agent. Evaluate the provided content against three criteria.

Criteria (score 1–5 each):
- clarity: Is the output easy to understand?
- accuracy: Are the claims correct and well-supported?
- relevance: Does the output address the original task?

Rules:
- Be specific — quote a phrase if something is weak.
- Return ONLY valid JSON:
  {"clarity": 0, "accuracy": 0, "relevance": 0, "feedback": "one specific improvement suggestion"}\
""",
    },
]

# ── Section 1: Gallery ────────────────────────────────────────────────────────

st.subheader("Agent Type Gallery")
st.caption("Each card shows: definition · canonical prompt pattern · input/output shape · when to use")

gallery_cols = st.columns(4)
for col, agent in zip(gallery_cols, AGENT_TYPES):
    with col:
        st.markdown(
            f"<div style='border-top:4px solid {agent['color']};background:{agent['bg']};"
            f"border-radius:6px;padding:14px;min-height:380px;'>"
            f"<div style='font-size:1.8em;'>{agent['icon']}</div>"
            f"<div style='font-weight:bold;font-size:1.05em;color:{agent['color']};margin:6px 0;'>{agent['name']}</div>"
            f"<div style='font-size:0.85em;margin-bottom:10px;'>{agent['definition']}</div>"
            f"<div style='font-size:0.76em;background:white;border-radius:4px;padding:6px 8px;"
            f"border-left:3px solid {agent['color']};margin-bottom:8px;font-family:monospace;'>"
            f"{agent['prompt_snippet']}</div>"
            f"<div style='font-size:0.78em;color:#555;border-top:1px solid {agent['color']}40;padding-top:8px;'>"
            f"<strong>Input:</strong> {agent['input']}<br>"
            f"<strong>Output:</strong> {agent['output']}<br><br>"
            f"<em style='color:#777;'>Use when: {agent['when_to_use']}</em>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

st.divider()

# ── Section 2: Live comparison ────────────────────────────────────────────────

st.subheader("Live Comparison — Same Input, Four Agent Types")
st.markdown(
    """
Enter any task or request. Click **Run All Four** to see how each agent type handles the same input.

> **How the Critic works here:** A Critic needs *generated output* to evaluate — not a raw user request.
> So the app runs the **Executor first**, then passes its output to the **Critic**. This shows the
> natural dependency: Executor produces → Critic judges.
"""
)

PRESET_INPUTS = [
    "Custom input — type below",
    "Our mobile app is crashing when users try to upload a photo larger than 5MB.",
    "We need to improve customer retention for our SaaS product.",
    "Write a short blog post introduction about the benefits of remote work.",
    "Our API response times have increased by 300% since last Tuesday's deployment.",
]

selected_preset = st.selectbox("Pick a preset or write your own:", PRESET_INPUTS)
user_input = st.text_area(
    "Input:",
    value="" if selected_preset == PRESET_INPUTS[0] else selected_preset,
    height=80,
    placeholder="Enter a task, request, or problem statement...",
)

run_comparison = st.button("▶  Run All Four Agent Types", type="primary", disabled=not user_input.strip())

if run_comparison and user_input.strip():
    st.divider()

    # Run Router, Planner, Executor first — collect results
    results = {}
    spinner_placeholder = st.empty()

    for agent in AGENT_TYPES[:3]:  # Router, Planner, Executor
        spinner_placeholder.info(f"Running {agent['name']}...")
        response, usage = chat(
            system=agent["system_prompt"],
            user=user_input.strip(),
            max_tokens=400,
            temperature=0.3,
        )
        results[agent["name"]] = {"response": response, "usage": usage}

    # Run Critic on Executor's output
    spinner_placeholder.info("Running Critic on Executor's output...")
    executor_output = results["Executor"]["response"]
    critic_agent = AGENT_TYPES[3]
    critic_user = (
        f"Original task: {user_input.strip()}\n\n"
        f"Executor's output to evaluate:\n{executor_output}"
    )
    critic_response, critic_usage = chat(
        system=critic_agent["system_prompt"],
        user=critic_user,
        max_tokens=300,
        temperature=0.1,
    )
    results["Critic"] = {"response": critic_response, "usage": critic_usage}
    spinner_placeholder.empty()

    # Display all four in columns
    st.markdown("### Results")
    result_cols = st.columns(4)

    for col, agent in zip(result_cols, AGENT_TYPES):
        with col:
            st.markdown(
                f"<div style='background:{agent['bg']};border-top:3px solid {agent['color']};"
                f"padding:8px;border-radius:4px;text-align:center;font-weight:bold;"
                f"color:{agent['color']};margin-bottom:8px;'>{agent['icon']} {agent['name']}</div>",
                unsafe_allow_html=True,
            )
            data = results[agent["name"]]

            if agent["name"] == "Critic":
                st.caption("↳ evaluating the Executor's output above")
                # Try to parse critic JSON for a nicer display
                try:
                    clean = data["response"].strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                    cdata = json.loads(clean)
                    for criterion in ["clarity", "accuracy", "relevance"]:
                        val = cdata.get(criterion, 0)
                        st.markdown(f"**{criterion.title()}:** {val}/5")
                    if cdata.get("feedback"):
                        st.caption(f"💬 {cdata['feedback']}")
                except (json.JSONDecodeError, AttributeError):
                    st.markdown(data["response"])
            else:
                st.markdown(data["response"])

            st.caption(f"↳ {data['usage']['input_tokens']} in / {data['usage']['output_tokens']} out")

    st.divider()
    st.markdown(
        """
**What to observe:**
- The **Router** gave you a label — it refused to help. That is correct behaviour for a Router.
- The **Planner** gave you steps, not results. It did not do any of the work.
- The **Executor** produced something immediately useful — but with no plan or quality check.
- The **Critic** judged the Executor's output — it could not evaluate something that didn't exist yet.

In a real pipeline, these four agents work **in sequence**: Router → Planner → Executor → Critic.
"""
    )

st.divider()

# ── Section 3: Task mapping quiz ──────────────────────────────────────────────

st.subheader("Exercise — Map Tasks to Agent Types")
st.markdown(
    "For each of the 5 real-world task descriptions below, select the agent type that should handle it "
    "and write a one-sentence justification. Claude will evaluate your reasoning."
)

QUIZ_TASKS = [
    {
        "id": 1,
        "description": "An AI receives incoming customer emails and forwards each one to the billing team, the technical support team, or the general enquiries team.",
        "answer": "Router",
        "reason": "The AI is classifying inputs into a fixed set of categories and directing them — it produces a label, not content. That is routing.",
    },
    {
        "id": 2,
        "description": "An AI is given 'Launch a new developer documentation site' and produces a 6-step sequence of tasks for the team to execute.",
        "answer": "Planner",
        "reason": "The AI decomposes a high-level goal into ordered steps. It produces a plan, not a result. That is planning.",
    },
    {
        "id": 3,
        "description": "An AI receives 'Step 3: Write the API authentication section of the developer docs' and produces the actual written section.",
        "answer": "Executor",
        "reason": "The AI receives a single, specific task and produces real output. It does not plan or evaluate — it executes.",
    },
    {
        "id": 4,
        "description": "After a draft blog post is generated, an AI reads it and returns scores for clarity, accuracy, and tone, along with specific sentences that need revision.",
        "answer": "Critic",
        "reason": "The AI evaluates produced content against criteria and returns structured feedback. It does not generate the content — it judges it.",
    },
    {
        "id": 5,
        "description": "An AI is given a product requirements document and creates a full sprint plan with epics, stories, and task assignments for a 2-week sprint.",
        "answer": "Planner",
        "reason": "Creating a structured plan from a high-level document is decomposition work — the output is a plan, not delivered product. That is a Planner.",
    },
]

AGENT_TYPE_NAMES = [a["name"] for a in AGENT_TYPES]

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}
if "quiz_justifications" not in st.session_state:
    st.session_state.quiz_justifications = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False
if "quiz_results" not in st.session_state:
    st.session_state.quiz_results = {}

EVALUATOR_SYSTEM = """\
You are an expert in agentic AI systems. Evaluate whether a student's agent type selection and justification are correct.
Be encouraging but precise. Return ONLY valid JSON.\
"""

EVALUATOR_PROMPT = """\
Task description: "{task}"

Correct agent type: {correct}
Why it's correct: {reason}

Student's selection: {student_type}
Student's justification: "{student_justification}"

Evaluate the student's answer. Consider:
1. Is the type selection correct?
2. Does the justification show understanding, even if phrased differently?

Return ONLY valid JSON:
{{"correct": true or false, "score": 0 or 1, "feedback": "one specific sentence of feedback"}}\
"""

for task in QUIZ_TASKS:
    tid = task["id"]
    agent_meta = next(a for a in AGENT_TYPES if a["name"] == task["answer"])

    st.markdown(f"**Task {tid}**")
    st.markdown(
        f"<div style='background:#f4f4f8;border-left:5px solid #aaa;"
        f"padding:12px 16px;border-radius:4px;font-size:0.95em;'>"
        f"{task['description']}</div>",
        unsafe_allow_html=True,
    )

    q_cols = st.columns([1, 2])
    with q_cols[0]:
        st.session_state.quiz_answers[tid] = st.radio(
            f"Agent type for Task {tid}:",
            AGENT_TYPE_NAMES,
            horizontal=False,
            key=f"qtype_{tid}",
            disabled=st.session_state.quiz_submitted,
        )
    with q_cols[1]:
        st.session_state.quiz_justifications[tid] = st.text_area(
            f"Justification for Task {tid}:",
            height=80,
            placeholder="Why did you choose this type? One sentence.",
            key=f"qjust_{tid}",
            disabled=st.session_state.quiz_submitted,
        )

    if st.session_state.quiz_submitted and tid in st.session_state.quiz_results:
        result = st.session_state.quiz_results[tid]
        correct = result.get("correct", False)
        feedback = result.get("feedback", "")
        st.markdown(
            f"<div style='border-left:4px solid {agent_meta['color']};padding:10px 14px;"
            f"background:{agent_meta['bg']};border-radius:4px;margin-top:4px;'>"
            f"{'✅' if correct else '❌'} Correct type: "
            f"<strong style='color:{agent_meta['color']};'>{task['answer']}</strong> — "
            f"{feedback}"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.write("")

if not st.session_state.quiz_submitted:
    filled_count = sum(
        1 for t in QUIZ_TASKS
        if st.session_state.quiz_justifications.get(t["id"], "").strip()
    )
    remaining = len(QUIZ_TASKS) - filled_count
    all_justified = remaining == 0

    if not all_justified:
        st.caption(f"Fill in {remaining} more justification(s) to unlock Submit.")

    if st.button("Submit All Answers", type="primary", disabled=not all_justified):
        st.session_state.quiz_submitted = True
        with st.spinner("Claude is evaluating your answers..."):
            for task in QUIZ_TASKS:
                tid = task["id"]
                raw, _ = chat(
                    system=EVALUATOR_SYSTEM,
                    user=EVALUATOR_PROMPT.format(
                        task=task["description"],
                        correct=task["answer"],
                        reason=task["reason"],
                        student_type=st.session_state.quiz_answers.get(tid, ""),
                        student_justification=st.session_state.quiz_justifications.get(tid, ""),
                    ),
                    max_tokens=200,
                    temperature=0.1,
                )
                try:
                    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                    st.session_state.quiz_results[tid] = json.loads(clean)
                except json.JSONDecodeError:
                    st.session_state.quiz_results[tid] = {
                        "correct": st.session_state.quiz_answers.get(tid) == task["answer"],
                        "score": 1 if st.session_state.quiz_answers.get(tid) == task["answer"] else 0,
                        "feedback": task["reason"],
                    }
        st.rerun()
else:
    total_score = sum(r.get("score", 0) for r in st.session_state.quiz_results.values())
    total_q = len(QUIZ_TASKS)
    if total_score == total_q:
        st.success(f"🎉 Full marks — {total_score}/{total_q}! You can map tasks to agent types with confidence.")
    elif total_score >= 3:
        st.info(f"Score: {total_score}/{total_q}. Good grasp — review the types you missed.")
    else:
        st.warning(f"Score: {total_score}/{total_q}. Re-read the gallery and try again after reviewing each type's definition.")

    if st.button("Reset Quiz"):
        st.session_state.quiz_submitted = False
        st.session_state.quiz_results = {}
        st.rerun()

st.divider()
with st.expander("Key design rule — one agent, one role"):
    st.markdown(
        """
The most common mistake when building multi-agent systems is giving one agent too many responsibilities.

An agent that routes **and** executes **and** evaluates will do all three poorly. The reason is that
the system prompt and context window shape the model's behaviour — and those signals conflict when
a single prompt tries to serve multiple roles simultaneously.

**The rule:** each agent in your system should be describable in one sentence that starts with a verb:
- "Routes incoming requests to the correct handler."
- "Decomposes goals into ordered steps."
- "Executes a single, concrete task."
- "Evaluates output against defined criteria."

If your sentence has two verbs connected by "and", you have two agents masquerading as one.
"""
    )
