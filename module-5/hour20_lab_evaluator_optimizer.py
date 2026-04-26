"""
Hour 20 Lab — Evaluator-Optimizer Pattern
Module 5 | Core Agentic Patterns II

A generator produces output. An evaluator scores it against specific criteria.
An optimizer improves it. The loop continues until quality meets a threshold or
a maximum round count is reached.

Run: streamlit run module-5/hour20_lab_evaluator_optimizer.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Hour 20 — Evaluator-Optimizer", page_icon="🔄", layout="wide")
st.title("🔄 Hour 20 — Evaluator-Optimizer Pattern")
st.caption("Module 5 | Core Agentic Patterns II")

st.markdown("""
The **Evaluator-Optimizer Pattern** creates a principled improvement loop:

```
Task → [GENERATOR] → output
              ↓
        [EVALUATOR] → structured scores + feedback
              ↓
        threshold check
        ├── all scores ≥ threshold → done ✅
        └── below threshold → [OPTIMIZER] → improved output → back to [EVALUATOR]
```

**How this differs from Reflection (Module 4):**
- Reflection runs for a fixed number of rounds regardless of quality
- Evaluator-Optimizer terminates *when quality is good enough* — no wasted rounds
- Criteria are domain-specific and predefined, not general
- The threshold is explicit and configurable

This lab shows the pattern applied to two domains:
1. **Code quality optimizer** — generates Python code, evaluates, and improves until criteria are met
2. **System prompt optimizer** — refines a rough prompt until it meets prompt engineering standards
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Hour 20 Guide")
    st.markdown("""
**Sections in this lab:**
1. **Loop diagram** — generator → evaluator → threshold gate → optimizer
2. **Code quality loop** — 4 criteria: correctness, efficiency, style, documentation
3. **Prompt quality loop** — 4 criteria: clarity, specificity, constraints, format
4. **Convergence analysis** — score progression and plateau detection

**What to observe:**
- The optimizer must preserve high-scoring dimensions while fixing low ones
- A low threshold (2/5) terminates quickly; high (4/5) runs more rounds
- Scores often plateau — more rounds don't always mean better output
- Token cost is: (N rounds × 2 calls) + 1 generator call
""")
    st.divider()
    st.markdown("**Experiment ideas:**")
    st.markdown("- Set threshold to 4 vs 2 — count the extra rounds and token cost")
    st.markdown("- Submit deliberately bad code — see how many rounds it takes to improve")
    st.markdown("- Submit a vague system prompt — watch the optimizer add specificity")
    st.divider()
    st.info("**Key principle:** A good evaluator is strict. If it scores everything 4/5 on the first pass, the optimizer never gets a useful improvement signal.")

# ── System Prompts ─────────────────────────────────────────────────────────────
CODE_GENERATOR_SYSTEM = """\
You are a Python programmer. Write clean, working Python code for the given task.
Return ONLY the code in a Python code block (```python ... ```) — no prose, no explanations.\
"""

CODE_EVALUATOR_SYSTEM = """\
You are a Python code quality assessor. Evaluate the provided code on four criteria (1–5):

- correctness: does the code correctly implement what is asked? (1=broken, 5=fully correct)
- efficiency: is the algorithm reasonably optimal? (1=O(n²) when O(n) is obvious, 5=well-optimised)
- style: does it follow PEP 8 and use clear variable names? (1=poor naming/style, 5=excellent)
- documentation: are there appropriate docstrings or comments? (1=none, 5=well-documented)

Be strict. Reserve 5 for genuinely excellent code. Reserve 1 for clearly broken code.

Return ONLY valid JSON — no markdown fences:
{"correctness": N, "efficiency": N, "style": N, "documentation": N, "feedback": "one specific improvement"}\
"""

CODE_OPTIMIZER_SYSTEM = """\
You are a Python code refactorer and improver. You receive Python code and a critique.
Rewrite the code to address the specific feedback while maintaining what already works.
Do not change scope, input, or output — only improve quality.
Return ONLY the improved code in a Python code block (```python ... ```).\
"""

PROMPT_GENERATOR_SYSTEM = """\
You are a prompt engineer. Given a rough task description, write a well-structured system prompt.
A good system prompt includes: the agent's role and expertise, what it does and does not do,
specific constraints, and the exact output format expected.
Return ONLY the system prompt text — no commentary, no labels.\
"""

PROMPT_EVALUATOR_SYSTEM = """\
You are a system prompt quality auditor. Evaluate the provided system prompt on four criteria (1–5):

- clarity: is the agent's role and purpose unambiguous? (1=vague, 5=crystal clear)
- specificity: are the instructions concrete enough to follow without interpretation? (1=too vague, 5=very specific)
- constraints: are limits, edge cases, and restrictions defined? (1=none, 5=comprehensive)
- format: is the required output format precisely specified? (1=unclear, 5=exact format given)

Be strict. Reserve 5 for genuinely excellent prompt engineering.

Return ONLY valid JSON — no markdown fences:
{"clarity": N, "specificity": N, "constraints": N, "format": N, "feedback": "one specific improvement"}\
"""

PROMPT_OPTIMIZER_SYSTEM = """\
You are a senior prompt engineer and editor. You receive a system prompt and a quality critique.
Rewrite the prompt to address the specific feedback while preserving everything that already scores well.
Return ONLY the improved system prompt text — no commentary.\
"""


def parse_json(raw: str) -> dict | None:
    try:
        clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return None


def extract_code_block(text: str) -> str:
    if "```python" in text:
        start = text.find("```python") + len("```python")
        end = text.find("```", start)
        return text[start:end].strip() if end != -1 else text.strip()
    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        return text[start:end].strip() if end != -1 else text.strip()
    return text.strip()


CRITERIA_COLOR = {
    "correctness": "#1E88E5",
    "efficiency": "#43A047",
    "style": "#8E24AA",
    "documentation": "#FB8C00",
    "clarity": "#1E88E5",
    "specificity": "#43A047",
    "constraints": "#E53935",
    "format": "#FB8C00",
}


def render_score_bar(criteria: list[str], scores: dict, cols):
    for col, key in zip(cols, criteria):
        score = scores.get(key, 0)
        color = CRITERIA_COLOR.get(key, "#8E24AA")
        col.metric(key.capitalize(), f"{score}/5")
        col.progress(score / 5)


# ── Section 1: Loop Diagram ────────────────────────────────────────────────────
st.divider()
st.subheader("1 — The Evaluator-Optimizer Loop")

loop_cols = st.columns([1.5, 0.4, 1.5, 0.4, 1.5, 0.4, 1.5])
loop_items = [
    ("#1E88E5", "#E3F2FD", "✍️", "[GENERATOR]", "Creates initial output from task"),
    None,
    ("#E53935", "#FFEBEE", "🔍", "[EVALUATOR]", "Scores on N criteria → JSON"),
    None,
    ("#43A047", "#E8F5E9", "🚪", "THRESHOLD\nGATE", "score ≥ threshold → done\nscore < threshold → optimize"),
    None,
    ("#8E24AA", "#F3E5F5", "✨", "[OPTIMIZER]", "Targets low scores, preserves high ones"),
]

for col, item in zip(loop_cols, loop_items):
    with col:
        if item is None:
            st.markdown(
                "<div style='display:flex;align-items:center;justify-content:center;"
                "height:140px;font-size:1.8em;color:#999;'>→</div>",
                unsafe_allow_html=True,
            )
        else:
            color, bg, icon, label, desc = item
            st.markdown(
                f"<div style='border-top:4px solid {color};background:{bg};"
                f"border-radius:6px;padding:10px;text-align:center;min-height:140px;'>"
                f"<div style='font-size:1.6em;'>{icon}</div>"
                f"<div style='font-weight:bold;color:{color};font-size:0.82em;margin:4px 0;'>{label}</div>"
                f"<div style='font-size:0.75em;color:#444;'>{desc}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

st.markdown(
    "<div style='background:#FFF3E0;border-left:4px solid #FB8C00;padding:8px 14px;"
    "border-radius:4px;margin-top:8px;font-size:0.9em;'>"
    "↩ The Optimizer's output feeds back into the Evaluator — the loop continues until the threshold is met "
    "or the maximum round count is reached."
    "</div>",
    unsafe_allow_html=True,
)

with st.expander("See system prompts"):
    tabs = st.tabs(["Code Generator", "Code Evaluator", "Code Optimizer", "Prompt Generator", "Prompt Evaluator", "Prompt Optimizer"])
    for tab, prompt in zip(tabs, [
        CODE_GENERATOR_SYSTEM, CODE_EVALUATOR_SYSTEM, CODE_OPTIMIZER_SYSTEM,
        PROMPT_GENERATOR_SYSTEM, PROMPT_EVALUATOR_SYSTEM, PROMPT_OPTIMIZER_SYSTEM,
    ]):
        with tab:
            st.code(prompt, language="text")

# ── Section 2: Code Quality Optimizer ─────────────────────────────────────────
st.divider()
st.subheader("2 — Code Quality Optimizer")

st.markdown("""
Describe a Python coding task. The generator writes the code, the evaluator scores it,
and the optimizer improves it until all criteria meet the threshold.
""")

CODE_THRESHOLD = st.slider("Quality threshold (each criterion must reach this):", 2, 5, 3, key="code_threshold")
CODE_MAX_ROUNDS = st.slider("Maximum optimization rounds:", 1, 4, 3, key="code_max_rounds")

CODE_TASK_PRESETS = [
    "Custom task — type below",
    "Write a function that finds all duplicate values in a list",
    "Write a function that reads a CSV file and returns a list of dictionaries",
    "Write a function that checks if a string is a valid email address",
    "Write a class for a stack data structure with push, pop, and peek methods",
    "Write a function that merges two sorted lists into one sorted list",
]

sel_code_task = st.selectbox("Pick a preset task or write your own:", CODE_TASK_PRESETS, key="code_task_preset")
code_task = st.text_area(
    "Coding task:",
    value="" if sel_code_task == CODE_TASK_PRESETS[0] else sel_code_task,
    height=70,
    key="code_task_input",
)

CODE_CRITERIA = ["correctness", "efficiency", "style", "documentation"]

if st.button("▶ Run Code Quality Optimizer", type="primary", disabled=not code_task.strip()):
    code_rounds = []
    code_total_in, code_total_out = 0, 0

    progress = st.progress(0, text="Generator writing initial code…")
    with st.spinner("Generator writing code…"):
        raw_code, u_gen = chat(CODE_GENERATOR_SYSTEM, f"Task: {code_task.strip()}", max_tokens=600, temperature=0.4)
    code_total_in += u_gen["input_tokens"]
    code_total_out += u_gen["output_tokens"]
    current_code = extract_code_block(raw_code)
    progress.progress(10, text="Initial code generated…")

    for round_num in range(1, CODE_MAX_ROUNDS + 1):
        with st.spinner(f"Round {round_num}: Evaluator scoring…"):
            eval_user = f"Task: {code_task.strip()}\n\nCode to evaluate:\n```python\n{current_code}\n```"
            raw_eval, u_eval = chat(CODE_EVALUATOR_SYSTEM, eval_user, max_tokens=300, temperature=0.1)
        code_total_in += u_eval["input_tokens"]
        code_total_out += u_eval["output_tokens"]

        eval_result = parse_json(raw_eval)
        if not eval_result:
            st.error(f"Round {round_num}: Evaluator parse error.")
            st.code(raw_eval)
            break

        scores = {k: eval_result.get(k, 0) for k in CODE_CRITERIA}
        avg = sum(scores.values()) / len(scores)
        feedback = eval_result.get("feedback", "")

        below_threshold = [k for k in CODE_CRITERIA if scores.get(k, 0) < CODE_THRESHOLD]
        passed = len(below_threshold) == 0

        code_rounds.append({
            "round": round_num,
            "code": current_code,
            "scores": scores,
            "avg": avg,
            "feedback": feedback,
            "passed": passed,
        })

        progress.progress(10 + round_num * 25, text=f"Round {round_num} scored (avg {avg:.1f}/5)…")

        if passed:
            break

        if round_num < CODE_MAX_ROUNDS:
            opt_user = (
                f"Task: {code_task.strip()}\n\n"
                f"Current code:\n```python\n{current_code}\n```\n\n"
                f"Scores: {', '.join(f'{k}={scores[k]}/5' for k in CODE_CRITERIA)}\n"
                f"Feedback: {feedback}\n\n"
                f"Criteria below threshold ({CODE_THRESHOLD}/5): {', '.join(below_threshold)}\n"
                "Improve the code to address the feedback, preserving what scores well."
            )
            with st.spinner(f"Round {round_num}: Optimizer improving code…"):
                raw_opt, u_opt = chat(CODE_OPTIMIZER_SYSTEM, opt_user, max_tokens=700, temperature=0.4)
            code_total_in += u_opt["input_tokens"]
            code_total_out += u_opt["output_tokens"]
            current_code = extract_code_block(raw_opt)

    progress.progress(100, text="Optimization loop complete.")
    st.session_state["code_rounds"] = code_rounds
    st.session_state["code_totals"] = (code_total_in, code_total_out)
    st.session_state["code_threshold_val"] = CODE_THRESHOLD

if "code_rounds" in st.session_state:
    rounds = st.session_state["code_rounds"]
    code_total_in, code_total_out = st.session_state["code_totals"]
    threshold = st.session_state.get("code_threshold_val", 3)

    for rd in rounds:
        passed = rd["passed"]
        status = "✅ PASSED" if passed else ("🔁 OPTIMIZING" if rd["round"] < len(rounds) else "⏹ MAX ROUNDS")
        with st.expander(
            f"Round {rd['round']} — avg {rd['avg']:.1f}/5 — {status}",
            expanded=(rd["round"] == len(rounds)),
        ):
            st.code(rd["code"], language="python")
            score_cols = st.columns(4)
            render_score_bar(CODE_CRITERIA, rd["scores"], score_cols)
            if rd["feedback"]:
                st.info(f"**Evaluator feedback:** {rd['feedback']}")
            if passed:
                st.success(f"All criteria ≥ {threshold}/5 — optimization complete.")

    if len(rounds) > 1:
        st.markdown("**Score progression:**")
        prog_cols = st.columns(len(rounds))
        for col, rd in zip(prog_cols, rounds):
            delta = f"+{rd['avg'] - rounds[0]['avg']:.1f}" if rd["round"] > 1 else None
            col.metric(f"Round {rd['round']}", f"{rd['avg']:.1f}/5", delta=delta)

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Rounds run", len(rounds))
    c2.metric("Total input tokens", code_total_in)
    c3.metric("Total output tokens", code_total_out)

# ── Section 3: System Prompt Optimizer ────────────────────────────────────────
st.divider()
st.subheader("3 — System Prompt Optimizer")

st.markdown("""
Describe a rough task for an agent. The generator writes a system prompt, the evaluator
scores it on prompt engineering criteria, and the optimizer refines it until the threshold is met.
""")

PROMPT_THRESHOLD = st.slider("Quality threshold (each criterion must reach this):", 2, 5, 3, key="prompt_threshold")
PROMPT_MAX_ROUNDS = st.slider("Maximum optimization rounds:", 1, 4, 3, key="prompt_max_rounds")

PROMPT_TASK_PRESETS = [
    "Custom task description — type below",
    "An agent that answers customer support questions about a software product",
    "An agent that reviews pull requests and provides code feedback",
    "An agent that extracts key dates and deadlines from legal documents",
    "An agent that writes product descriptions for an e-commerce store",
    "An agent that translates technical documentation for non-technical readers",
]

sel_prompt_task = st.selectbox("Pick a preset task or write your own:", PROMPT_TASK_PRESETS, key="prompt_task_preset")
prompt_task = st.text_area(
    "Agent task description:",
    value="" if sel_prompt_task == PROMPT_TASK_PRESETS[0] else sel_prompt_task,
    height=70,
    key="prompt_task_input",
)

PROMPT_CRITERIA = ["clarity", "specificity", "constraints", "format"]

if st.button("▶ Run Prompt Quality Optimizer", type="primary", disabled=not prompt_task.strip()):
    prompt_rounds = []
    prompt_total_in, prompt_total_out = 0, 0

    prog2 = st.progress(0, text="Generator writing initial system prompt…")
    with st.spinner("Generator writing system prompt…"):
        initial_prompt, u_pg = chat(PROMPT_GENERATOR_SYSTEM, f"Task: {prompt_task.strip()}", max_tokens=500, temperature=0.5)
    prompt_total_in += u_pg["input_tokens"]
    prompt_total_out += u_pg["output_tokens"]
    current_prompt = initial_prompt
    prog2.progress(10, text="Initial prompt generated…")

    for round_num in range(1, PROMPT_MAX_ROUNDS + 1):
        with st.spinner(f"Round {round_num}: Evaluator scoring…"):
            p_eval_user = f"Task this prompt is for: {prompt_task.strip()}\n\nSystem prompt to evaluate:\n\n{current_prompt}"
            raw_peval, u_pe = chat(PROMPT_EVALUATOR_SYSTEM, p_eval_user, max_tokens=300, temperature=0.1)
        prompt_total_in += u_pe["input_tokens"]
        prompt_total_out += u_pe["output_tokens"]

        p_eval = parse_json(raw_peval)
        if not p_eval:
            st.error(f"Round {round_num}: Evaluator parse error.")
            st.code(raw_peval)
            break

        scores = {k: p_eval.get(k, 0) for k in PROMPT_CRITERIA}
        avg = sum(scores.values()) / len(scores)
        feedback = p_eval.get("feedback", "")
        below = [k for k in PROMPT_CRITERIA if scores.get(k, 0) < PROMPT_THRESHOLD]
        passed = len(below) == 0

        prompt_rounds.append({
            "round": round_num,
            "prompt": current_prompt,
            "scores": scores,
            "avg": avg,
            "feedback": feedback,
            "passed": passed,
        })

        prog2.progress(10 + round_num * 25, text=f"Round {round_num} scored (avg {avg:.1f}/5)…")

        if passed:
            break

        if round_num < PROMPT_MAX_ROUNDS:
            p_opt_user = (
                f"Task: {prompt_task.strip()}\n\n"
                f"Current system prompt:\n{current_prompt}\n\n"
                f"Scores: {', '.join(f'{k}={scores[k]}/5' for k in PROMPT_CRITERIA)}\n"
                f"Feedback: {feedback}\n\n"
                f"Criteria below threshold ({PROMPT_THRESHOLD}/5): {', '.join(below)}\n"
                "Rewrite the prompt to address the feedback, preserving what scores well."
            )
            with st.spinner(f"Round {round_num}: Optimizer refining prompt…"):
                raw_popt, u_po = chat(PROMPT_OPTIMIZER_SYSTEM, p_opt_user, max_tokens=600, temperature=0.4)
            prompt_total_in += u_po["input_tokens"]
            prompt_total_out += u_po["output_tokens"]
            current_prompt = raw_popt.strip()

    prog2.progress(100, text="Optimization complete.")
    st.session_state["prompt_rounds"] = prompt_rounds
    st.session_state["prompt_totals"] = (prompt_total_in, prompt_total_out)
    st.session_state["prompt_threshold_val"] = PROMPT_THRESHOLD

if "prompt_rounds" in st.session_state:
    p_rounds = st.session_state["prompt_rounds"]
    prompt_total_in, prompt_total_out = st.session_state["prompt_totals"]
    p_threshold = st.session_state.get("prompt_threshold_val", 3)

    if len(p_rounds) >= 2:
        compare_cols = st.columns(2)
        with compare_cols[0]:
            st.markdown(
                "<div style='border-top:3px solid #1E88E5;padding:4px 0 6px;'>"
                "<strong style='color:#1E88E5;'>Initial prompt (Round 1):</strong></div>",
                unsafe_allow_html=True,
            )
            st.text_area(label="", value=p_rounds[0]["prompt"], height=200, disabled=True, label_visibility="collapsed", key="pr_initial")
        with compare_cols[1]:
            st.markdown(
                "<div style='border-top:3px solid #8E24AA;padding:4px 0 6px;'>"
                "<strong style='color:#8E24AA;'>Final prompt:</strong></div>",
                unsafe_allow_html=True,
            )
            st.text_area(label="", value=p_rounds[-1]["prompt"], height=200, disabled=True, label_visibility="collapsed", key="pr_final")

    for rd in p_rounds:
        passed = rd["passed"]
        status = "✅ PASSED" if passed else ("🔁 OPTIMIZING" if rd["round"] < len(p_rounds) else "⏹ MAX ROUNDS")
        with st.expander(
            f"Round {rd['round']} — avg {rd['avg']:.1f}/5 — {status}",
            expanded=False,
        ):
            score_cols = st.columns(4)
            render_score_bar(PROMPT_CRITERIA, rd["scores"], score_cols)
            if rd["feedback"]:
                st.info(f"**Evaluator feedback:** {rd['feedback']}")

    if len(p_rounds) > 1:
        st.markdown("**Score progression:**")
        prog_cols = st.columns(len(p_rounds))
        for col, rd in zip(prog_cols, p_rounds):
            delta = f"+{rd['avg'] - p_rounds[0]['avg']:.1f}" if rd["round"] > 1 else None
            col.metric(f"Round {rd['round']}", f"{rd['avg']:.1f}/5", delta=delta)

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Rounds run", len(p_rounds))
    c2.metric("Total input tokens", prompt_total_in)
    c3.metric("Total output tokens", prompt_total_out)

# ── Section 4: Convergence Analysis ───────────────────────────────────────────
st.divider()
st.subheader("4 — Convergence Analysis")

st.markdown("""
Observe how scores evolve across rounds and when they plateau.
A plateau means the optimizer is no longer making meaningful improvements — stopping earlier saves tokens.
""")

if "code_rounds" not in st.session_state and "prompt_rounds" not in st.session_state:
    st.info("Run Section 2 or Section 3 first to see convergence data here.")
else:
    analysis_cols = st.columns(2)

    with analysis_cols[0]:
        if "code_rounds" in st.session_state:
            st.markdown("**Code optimizer convergence:**")
            cr = st.session_state["code_rounds"]
            if len(cr) > 1:
                for crit in CODE_CRITERIA:
                    first = cr[0]["scores"].get(crit, 0)
                    last = cr[-1]["scores"].get(crit, 0)
                    delta_str = f" (+{last-first})" if last > first else (" (no change)" if last == first else f" ({last-first})")
                    color = CRITERIA_COLOR.get(crit, "#8E24AA")
                    st.markdown(
                        f"<span style='color:{color};font-weight:bold;'>{crit.capitalize()}</span>: "
                        f"{first}/5 → {last}/5{delta_str}",
                        unsafe_allow_html=True,
                    )
                avg_first = cr[0]["avg"]
                avg_last = cr[-1]["avg"]
                if avg_last - avg_first < 0.3 and len(cr) > 1:
                    st.warning(f"Score delta is only {avg_last - avg_first:.2f} — this run may have plateaued. Stopping after round 1 would have saved tokens.")
                else:
                    st.success(f"Meaningful improvement: {avg_first:.1f} → {avg_last:.1f}/5 (+{avg_last - avg_first:.1f})")
            else:
                st.info("Run multiple rounds to see convergence data.")

    with analysis_cols[1]:
        if "prompt_rounds" in st.session_state:
            st.markdown("**Prompt optimizer convergence:**")
            pr = st.session_state["prompt_rounds"]
            if len(pr) > 1:
                for crit in PROMPT_CRITERIA:
                    first = pr[0]["scores"].get(crit, 0)
                    last = pr[-1]["scores"].get(crit, 0)
                    delta_str = f" (+{last-first})" if last > first else (" (no change)" if last == first else f" ({last-first})")
                    color = CRITERIA_COLOR.get(crit, "#8E24AA")
                    st.markdown(
                        f"<span style='color:{color};font-weight:bold;'>{crit.capitalize()}</span>: "
                        f"{first}/5 → {last}/5{delta_str}",
                        unsafe_allow_html=True,
                    )
                avg_first = pr[0]["avg"]
                avg_last = pr[-1]["avg"]
                if avg_last - avg_first < 0.3 and len(pr) > 1:
                    st.warning(f"Score delta is only {avg_last - avg_first:.2f} — plateau detected. Consider reducing max rounds.")
                else:
                    st.success(f"Meaningful improvement: {avg_first:.1f} → {avg_last:.1f}/5 (+{avg_last - avg_first:.1f})")
            else:
                st.info("Run multiple rounds to see convergence data.")

    st.markdown("""
**Plateau detection rule of thumb:** If average score delta between consecutive rounds is < 0.3,
the optimizer is no longer making meaningful improvements. Stopping early saves:
- N × 2 API calls (evaluator + optimizer per round)
- Typically 400–800 input tokens per round

In production systems, add an explicit plateau check: if `current_avg - prev_avg < 0.2`, terminate.
""")
