"""
Hour 11 Lab — Implement Two Agent Types
Module 3 | Agent Types and Components

Students build and test two agent types from scratch:
  Tab A — Router Agent:  classifies input, routes to the correct specialist, executes end-to-end
  Tab B — Critic Agent:  generates a draft, evaluates it against 4 criteria, optionally rewrites

This is the capstone lab for Module 3. By the end, students will have working code
for two distinct agent types tested on multiple real inputs.

Run: streamlit run hour11_lab_implement_two_agents.py
"""

import json
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Hour 11 — Implement Two Agents", page_icon="🛠️", layout="wide")
st.title("🛠️ Hour 11 — Implement Two Agent Types")
st.caption("Module 3 | Agent Types and Components")

st.markdown(
    """
This lab moves from understanding agent types to **building** them. You will implement a Router agent
and a Critic agent, test each on sample inputs, and observe the full execution chain.

Each tab is a standalone implementation. Edit the system prompts, run the tests, and compare outputs.
"""
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Hour 11 Guide")
    st.markdown(
        """
**Tab A — Router Agent**

1. Read the architecture diagram
2. Edit the Router system prompt if you want
3. Click **Run All 3 Preset Inputs** — see the full chain for each
4. Test your own input

**Tab B — Critic Agent**

1. Set content type and audience
2. Edit the three prompts (Generator, Critic, Rewriter)
3. Click **Generate → Critique → Rewrite**
4. Compare scores and the before/after drafts
"""
    )
    st.divider()
    st.markdown("**Experiments to try:**")
    st.markdown("**Router:**")
    st.markdown("- Send an ambiguous input — what confidence score appears?")
    st.markdown("- Add a SECURITY category to the router prompt")
    st.markdown("- Remove the `reason` field — is it harder to debug?")
    st.markdown("**Critic:**")
    st.markdown("- Add a 5th criterion (`engagement`) to the Critic prompt")
    st.markdown("- Remove the `feedback` field — does the Rewriter still improve?")
    st.markdown("- Use a one-word topic — how low do scores go?")

tab_router, tab_critic = st.tabs(["Tab A — Router Agent", "Tab B — Critic Agent"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB A: ROUTER AGENT
# ══════════════════════════════════════════════════════════════════════════════

with tab_router:

    st.subheader("Router Agent")
    st.markdown(
        """
A **Router agent** reads an incoming request, classifies it into one of a fixed set of categories,
and then activates the appropriate specialist to handle it. The router itself never answers the
question — it only decides who should.

**Architecture:**
```
User Input → [ROUTER] → Route label → [SPECIALIST] → Final response
```
"""
    )

    DEFAULT_ROUTER_SYSTEM = """\
You are a routing agent for a technology company's support system.

Your ONLY job is to classify incoming requests into exactly one category:
- TECHNICAL: software bugs, error messages, performance issues, API problems, integrations
- BILLING: payments, invoices, subscription changes, refunds, pricing questions
- GENERAL: product questions, feature requests, onboarding help, account settings, other

Rules:
- Return ONLY valid JSON, nothing else.
- Never answer the question — only classify it.
- If ambiguous, pick the most likely category.

Return format:
{"route": "TECHNICAL" or "BILLING" or "GENERAL", "confidence": 0.0–1.0, "reason": "one sentence"}\
"""

    SPECIALIST_PROMPTS = {
        "TECHNICAL": """\
You are a senior technical support engineer. You handle software bugs, API issues, performance problems,
and integration failures. Be direct, technical, and solution-focused.
Provide step-by-step debugging guidance where relevant.\
""",
        "BILLING": """\
You are a billing support specialist. You handle payment queries, subscription management, refunds,
and pricing questions. Be empathetic, clear, and accurate.
Always confirm what the customer needs before offering solutions.\
""",
        "GENERAL": """\
You are a friendly customer success agent. You handle product questions, feature requests,
onboarding help, and general account queries. Be warm, helpful, and concise.
Direct the customer to relevant resources where appropriate.\
""",
    }

    ROUTE_COLORS = {"TECHNICAL": "#1E88E5", "BILLING": "#43A047", "GENERAL": "#FB8C00"}
    ROUTE_ICONS = {"TECHNICAL": "⚙️", "BILLING": "💳", "GENERAL": "💬"}

    if "router_system" not in st.session_state:
        st.session_state["router_system"] = DEFAULT_ROUTER_SYSTEM

    with st.expander("Edit Router System Prompt", expanded=False):
        st.caption("This is the prompt that defines the Router's classification behaviour.")
        st.text_area(
            "Router system prompt:",
            value=st.session_state["router_system"],
            height=220,
            key="router_system",
            label_visibility="collapsed",
        )
        if st.button("Reset Router Prompt"):
            st.session_state["router_system"] = DEFAULT_ROUTER_SYSTEM
            st.rerun()

    with st.expander("View Specialist Prompts (read-only)"):
        for route, prompt in SPECIALIST_PROMPTS.items():
            color = ROUTE_COLORS[route]
            st.markdown(
                f"<div style='border-left:4px solid {color};padding:6px 12px;"
                f"background:#f9f9f9;border-radius:4px;margin-bottom:6px;'>"
                f"<strong style='color:{color};'>{ROUTE_ICONS[route]} {route} Specialist</strong></div>",
                unsafe_allow_html=True,
            )
            st.code(prompt, language="text")

    st.divider()
    st.markdown("### Test the Router")
    st.markdown(
        "Run the router on the 3 preset inputs below, then test your own. "
        "Each run shows the full chain: Input → Route decision → Specialist response."
    )

    PRESET_INPUTS = [
        "My API calls are returning 429 errors since yesterday evening and I can't figure out why.",
        "I was charged twice for my subscription in November. I need a refund for the duplicate charge.",
        "How do I add more users to my team? I can't find the option in the settings.",
    ]

    if "router_results" not in st.session_state:
        st.session_state.router_results = []

    run_presets = st.button("▶  Run All 3 Preset Inputs", type="primary")

    if run_presets:
        st.session_state.router_results = []
        for i, preset in enumerate(PRESET_INPUTS):
            with st.container(border=True):
                st.markdown(f"**Test {i + 1}:** _{preset}_")

                with st.spinner("Router classifying..."):
                    raw_route, r_usage = chat(
                        system=st.session_state["router_system"],
                        user=preset,
                        max_tokens=200,
                        temperature=0.1,
                    )

                try:
                    clean = raw_route.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                    route_data = json.loads(clean)
                    route = route_data.get("route", "GENERAL").upper()
                    confidence = route_data.get("confidence", 0.0)
                    reason = route_data.get("reason", "")
                except json.JSONDecodeError:
                    route = "GENERAL"
                    confidence = 0.5
                    reason = raw_route

                color = ROUTE_COLORS.get(route, "#aaa")
                icon = ROUTE_ICONS.get(route, "❓")
                st.markdown(
                    f"<div style='display:inline-block;background:{color}20;border:2px solid {color};"
                    f"border-radius:20px;padding:4px 14px;font-weight:bold;color:{color};'>"
                    f"{icon} {route} — {int(confidence * 100)}% confidence</div>",
                    unsafe_allow_html=True,
                )
                st.caption(f"Router reasoning: {reason}")
                rc1, rc2 = st.columns(2)
                rc1.metric("Router input tokens", r_usage["input_tokens"])
                rc2.metric("Router output tokens", r_usage["output_tokens"])

                specialist_prompt = SPECIALIST_PROMPTS.get(route, SPECIALIST_PROMPTS["GENERAL"])
                with st.spinner(f"{route} specialist responding..."):
                    specialist_response, s_usage = chat(
                        system=specialist_prompt,
                        user=preset,
                        max_tokens=400,
                        temperature=0.5,
                    )

                st.markdown(f"**{icon} {route} Specialist Response:**")
                st.markdown(specialist_response)
                sc1, sc2 = st.columns(2)
                sc1.metric("Specialist input tokens", s_usage["input_tokens"])
                sc2.metric("Specialist output tokens", s_usage["output_tokens"])

                st.session_state.router_results.append({
                    "input": preset,
                    "route": route,
                    "confidence": confidence,
                    "router_tokens": r_usage["input_tokens"] + r_usage["output_tokens"],
                    "specialist_tokens": s_usage["input_tokens"] + s_usage["output_tokens"],
                })

        if st.session_state.router_results:
            st.divider()
            st.subheader("Results Summary")
            for r in st.session_state.router_results:
                color = ROUTE_COLORS.get(r["route"], "#aaa")
                icon = ROUTE_ICONS.get(r["route"], "❓")
                st.markdown(
                    f"<div style='border-left:4px solid {color};padding:8px 12px;"
                    f"background:#f9f9f9;border-radius:4px;margin-bottom:6px;font-size:0.9em;'>"
                    f"<strong style='color:{color};'>{icon} {r['route']}</strong> ({int(r['confidence']*100)}% confidence) "
                    f"| Router: {r['router_tokens']} tokens | Specialist: {r['specialist_tokens']} tokens<br>"
                    f"<em>{r['input'][:80]}{'…' if len(r['input']) > 80 else ''}</em></div>",
                    unsafe_allow_html=True,
                )

    st.divider()
    st.markdown("### Test Your Own Input")
    custom_input = st.text_area(
        "Your input:", height=80, placeholder="Type any support request..."
    )
    run_custom = st.button("▶  Route This Input", type="primary",
                            key="custom_router", disabled=not custom_input.strip())

    if run_custom and custom_input.strip():
        with st.container(border=True):
            with st.spinner("Router classifying..."):
                raw_route, r_usage = chat(
                    system=st.session_state["router_system"],
                    user=custom_input.strip(),
                    max_tokens=200,
                    temperature=0.1,
                )
            try:
                clean = raw_route.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                route_data = json.loads(clean)
                route = route_data.get("route", "GENERAL").upper()
                confidence = route_data.get("confidence", 0.0)
                reason = route_data.get("reason", "")
            except json.JSONDecodeError:
                route, confidence, reason = "GENERAL", 0.5, raw_route

            color = ROUTE_COLORS.get(route, "#aaa")
            icon = ROUTE_ICONS.get(route, "❓")
            st.markdown(
                f"<div style='display:inline-block;background:{color}20;border:2px solid {color};"
                f"border-radius:20px;padding:4px 14px;font-weight:bold;color:{color};margin-bottom:8px;'>"
                f"{icon} {route} — {int(confidence * 100)}% confidence</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"Router reasoning: {reason}")

            specialist_prompt = SPECIALIST_PROMPTS.get(route, SPECIALIST_PROMPTS["GENERAL"])
            with st.spinner(f"{route} specialist responding..."):
                response, s_usage = chat(
                    system=specialist_prompt, user=custom_input.strip(),
                    max_tokens=400, temperature=0.5,
                )
            st.markdown(f"**{icon} {route} Specialist Response:**")
            st.markdown(response)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Router in", r_usage["input_tokens"])
            c2.metric("Router out", r_usage["output_tokens"])
            c3.metric("Specialist in", s_usage["input_tokens"])
            c4.metric("Specialist out", s_usage["output_tokens"])

    with st.expander("Implementation notes — what to observe"):
        st.markdown(
            """
**Why the Router returns JSON:**
The route decision must be machine-readable. Plain text ("I think this is a billing issue")
cannot be used to programmatically select the next agent. JSON with a fixed key (`route`) lets
the Python code branch deterministically.

**Why confidence matters:**
A low-confidence route (< 0.6) is a signal to either escalate to a human or route to a
default fallback agent — not to proceed blindly. In production routers, confidence thresholds
are one of the first guardrails you configure.

**Try this:**
- Send an ambiguous input (e.g. "I need help with my account"). What confidence does the router return?
- Edit the router prompt to add a new category (e.g. SECURITY). Does it classify correctly?
- Remove the "reason" field from the return format. Does routing still work? Is it harder to debug?
"""
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB B: CRITIC AGENT
# ══════════════════════════════════════════════════════════════════════════════

with tab_critic:

    st.subheader("Critic Agent")
    st.markdown(
        """
A **Critic agent** evaluates content produced by another agent against defined criteria.
It does not generate the content — it judges it. The output is always structured (scores + feedback)
so it can be used programmatically by the next step in the pipeline.

**Architecture:**
```
Topic → [GENERATOR] → Draft → [CRITIC] → Scores + Feedback → [REWRITER] → Improved draft
```
"""
    )

    DEFAULT_GENERATOR_SYSTEM = """\
You are a professional content writer. Produce a well-structured draft for the given content type and topic.
Be specific, concrete, and audience-aware. Do not pad with filler — every sentence should add value.\
"""

    DEFAULT_CRITIC_SYSTEM = """\
You are a sharp editorial critic. Your job is to evaluate content against four criteria.
Be specific — quote exact phrases when something is weak. Do not be vague or generic.

Criteria (score 1–5 each):
- accuracy: Are the facts, claims, and statements correct and well-supported?
  1 = contains errors or unsupported claims, 5 = fully accurate and evidenced
- clarity: Is the writing easy to understand on first reading?
  1 = confusing or jargon-heavy, 5 = crystal clear for the target audience
- tone: Does the tone match the content type and intended audience?
  1 = completely wrong tone, 5 = perfect register and voice for the audience
- completeness: Does the content cover what it needs to? Are there notable gaps?
  1 = significant gaps or missing sections, 5 = comprehensive for the stated purpose

Return ONLY valid JSON:
{"accuracy": 0, "clarity": 0, "tone": 0, "completeness": 0,
 "feedback": "Quote 2-3 specific phrases and say exactly what to fix."}\
"""

    DEFAULT_REWRITER_SYSTEM = """\
You are a skilled editor doing a targeted revision. Rewrite the content to fix ONLY the specific issues
identified in the feedback. Do not change what is already working. Preserve the structure and length
unless the feedback explicitly requires changes to them.\
"""

    CRITERIA = ["accuracy", "clarity", "tone", "completeness"]
    CRITERIA_ICONS = {"accuracy": "✅", "clarity": "💡", "tone": "🎙️", "completeness": "📋"}
    CRITERIA_COLORS = {"accuracy": "#43A047", "clarity": "#1E88E5", "tone": "#8E24AA", "completeness": "#FB8C00"}

    for key, default in [
        ("critic_gen_system", DEFAULT_GENERATOR_SYSTEM),
        ("critic_system", DEFAULT_CRITIC_SYSTEM),
        ("critic_rew_system", DEFAULT_REWRITER_SYSTEM),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    prompt_tabs = st.tabs(["Generator Prompt", "Critic Prompt", "Rewriter Prompt"])

    with prompt_tabs[0]:
        st.caption("Produces the initial draft. You will configure content type and topic below.")
        st.text_area("Generator system prompt:", value=st.session_state["critic_gen_system"],
                     height=160, key="critic_gen_system", label_visibility="collapsed")
        if st.button("Reset Generator"):
            st.session_state["critic_gen_system"] = DEFAULT_GENERATOR_SYSTEM; st.rerun()

    with prompt_tabs[1]:
        st.caption("Evaluates the draft. Returns JSON scores + feedback. This is the Critic agent's core prompt.")
        st.text_area("Critic system prompt:", value=st.session_state["critic_system"],
                     height=260, key="critic_system", label_visibility="collapsed")
        if st.button("Reset Critic"):
            st.session_state["critic_system"] = DEFAULT_CRITIC_SYSTEM; st.rerun()

    with prompt_tabs[2]:
        st.caption("Rewrites the draft using the Critic's feedback.")
        st.text_area("Rewriter system prompt:", value=st.session_state["critic_rew_system"],
                     height=160, key="critic_rew_system", label_visibility="collapsed")
        if st.button("Reset Rewriter"):
            st.session_state["critic_rew_system"] = DEFAULT_REWRITER_SYSTEM; st.rerun()

    st.divider()
    st.markdown("### Configure and Run")

    conf_cols = st.columns([1, 2])
    with conf_cols[0]:
        content_type = st.selectbox(
            "Content type:",
            ["Blog post introduction", "Professional email", "Code explanation", "Executive summary", "Product description"],
        )
        audience = st.selectbox(
            "Target audience:",
            ["Software engineers", "Non-technical executives", "Marketing team", "Product managers", "General public"],
        )
        include_rewrite = st.checkbox("Run Rewriter after Critic", value=True)

    with conf_cols[1]:
        topic = st.text_area(
            "Topic or brief:",
            height=120,
            placeholder="e.g. Why distributed tracing is essential for microservices in production",
            value="Why every engineering team should adopt a code review culture before scaling past 10 engineers",
        )

    run_critic_lab = st.button("▶  Generate → Critique → (Rewrite)", type="primary",
                                disabled=not topic.strip())

    if run_critic_lab and topic.strip():
        generator_user = (
            f"Content type: {content_type}\n"
            f"Target audience: {audience}\n"
            f"Topic: {topic.strip()}\n\n"
            f"Write the {content_type.lower()} now."
        )

        total_in, total_out = 0, 0
        draft = ""
        rewritten = ""

        with st.container(border=True):
            st.markdown("### 📝 \[GENERATOR\] — Producing draft")
            with st.spinner("Generator writing draft..."):
                draft, g_usage = chat(
                    system=st.session_state["critic_gen_system"],
                    user=generator_user,
                    max_tokens=600,
                    temperature=0.8,
                )
            total_in += g_usage["input_tokens"]
            total_out += g_usage["output_tokens"]
            st.markdown(draft)
            c1, c2 = st.columns(2)
            c1.metric("Input tokens", g_usage["input_tokens"])
            c2.metric("Output tokens", g_usage["output_tokens"])

        critic_user = (
            f"Content type: {content_type}\n"
            f"Target audience: {audience}\n\n"
            f"Content to evaluate:\n{draft}"
        )

        scores = {}
        feedback = ""

        with st.container(border=True):
            st.markdown("### 🔍 \[CRITIC\] — Evaluating draft")
            with st.expander("View Critic system prompt"):
                st.code(st.session_state["critic_system"], language="text")

            with st.spinner("Critic evaluating..."):
                raw_critique, c_usage = chat(
                    system=st.session_state["critic_system"],
                    user=critic_user,
                    max_tokens=400,
                    temperature=0.1,
                )
            total_in += c_usage["input_tokens"]
            total_out += c_usage["output_tokens"]

            try:
                clean = raw_critique.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                critique_data = json.loads(clean)
                scores = {k: critique_data.get(k, 0) for k in CRITERIA}
                feedback = critique_data.get("feedback", "")
            except json.JSONDecodeError:
                st.error("Critic returned unexpected format. Showing raw output:")
                st.code(raw_critique)
                scores = {k: 3 for k in CRITERIA}
                feedback = raw_critique

            score_cols = st.columns(4)
            for col, criterion in zip(score_cols, CRITERIA):
                val = scores.get(criterion, 0)
                color = CRITERIA_COLORS[criterion]
                icon = CRITERIA_ICONS[criterion]
                pct = val / 5
                bg = "#e8f5e9" if val >= 4 else "#fff3e0" if val >= 3 else "#ffebee"
                col.markdown(
                    f"<div style='text-align:center;background:{bg};border-radius:6px;padding:12px;'>"
                    f"<div style='font-size:1.4em;'>{icon}</div>"
                    f"<div style='font-weight:bold;color:{color};'>{criterion.title()}</div>"
                    f"<div style='font-size:1.3em;color:{color};font-weight:bold;'>{val}/5</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                col.progress(pct)

            if feedback:
                st.warning(f"📝 Critic feedback: {feedback}")

            c1, c2 = st.columns(2)
            c1.metric("Input tokens", c_usage["input_tokens"])
            c2.metric("Output tokens", c_usage["output_tokens"])

        if include_rewrite:
            rewriter_user = (
                f"Content type: {content_type}\n"
                f"Target audience: {audience}\n\n"
                f"Original draft:\n{draft}\n\n"
                f"Critic feedback to address:\n{feedback}"
            )

            with st.container(border=True):
                st.markdown("### ✏️ \[REWRITER\] — Improving draft")
                with st.spinner("Rewriter improving draft based on feedback..."):
                    rewritten, rw_usage = chat(
                        system=st.session_state["critic_rew_system"],
                        user=rewriter_user,
                        max_tokens=600,
                        temperature=0.6,
                    )
                total_in += rw_usage["input_tokens"]
                total_out += rw_usage["output_tokens"]
                st.markdown(rewritten)
                c1, c2 = st.columns(2)
                c1.metric("Input tokens", rw_usage["input_tokens"])
                c2.metric("Output tokens", rw_usage["output_tokens"])

        if include_rewrite and rewritten and rewritten != draft:
            st.divider()
            st.subheader("Before vs After")
            ba_left, ba_right = st.columns(2)
            with ba_left:
                st.markdown(
                    "<div style='border-top:3px solid #E53935;padding:4px 0 8px 0;'>"
                    "<strong style='color:#E53935;'>Original draft</strong></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(draft)
            with ba_right:
                st.markdown(
                    "<div style='border-top:3px solid #43A047;padding:4px 0 8px 0;'>"
                    "<strong style='color:#43A047;'>Rewritten draft</strong></div>",
                    unsafe_allow_html=True,
                )
                st.markdown(rewritten)

        st.divider()
        p1, p2, p3 = st.columns(3)
        p1.metric("Total LLM calls", 3 if include_rewrite else 2)
        p2.metric("Total input tokens", total_in)
        p3.metric("Total output tokens", total_out)

    with st.expander("Implementation notes — what to observe"):
        st.markdown(
            """
**Why the Critic returns JSON:**
Scores and feedback must be machine-readable. If the Critic returns prose, the Python code cannot
extract the score for `accuracy` to decide whether to trigger a rewrite. Structured output is
what makes the Critic composable with other agents.

**The threshold question:**
At what score should the pipeline stop rewriting? Too low (e.g. 2/5) and the loop exits before
quality is acceptable. Too high (e.g. 5/5) and it may never exit. In production, you set per-criterion
thresholds based on what your use case demands most.

**Try this:**
- Change the Critic prompt to add a 5th criterion (e.g. `engagement`). Does the JSON still parse?
- Remove the "feedback" field instruction. Does the Rewriter still improve the draft?
- Deliberately write a weak topic (one word only). How low do the scores go?
- Run the same topic twice — are the scores consistent, or does the Critic vary?

**Critic vs Evaluator:**
A Critic gives feedback that loops back into the pipeline. An Evaluator (like in Module 2)
gives a final pass/fail judgement at the end of the pipeline. Both are critic-type agents —
the difference is whether the feedback triggers another round of generation.
"""
        )

st.divider()
st.markdown(
    """
### What you have built in this module

| Lab | Agent type | What it does |
|-----|------------|--------------|
| Hour 8 | 4-component agent | Assembles persona, knowledge, tools, and interaction layer |
| Hour 9 | Router, Planner, Executor, Critic | Understands each type's distinct role |
| Hour 10 | Retriever, Orchestrator, Specialist | Builds multi-agent teams with delegation |
| Hour 11 | Router + Critic | Implements and tests two full agent types |

You now have the foundation to design any multi-agent system by combining these building blocks.
Module 4 will show you how to wire them into persistent, stateful agentic pipelines.
"""
)
