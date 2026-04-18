"""
Hour 8 Lab — Agent Components
Module 3 | Agent Types and Components

Every agent is assembled from four core components:
  Persona        — who the agent is (system role definition)
  Knowledge      — what the agent knows (injected context)
  Tools          — what the agent can do (external functions it can call)
  Interaction    — how the agent communicates (output format and style)

Sections:
  1. Component gallery — visual overview of all four components
  2. Annotate an agent — guess-then-reveal: label each part of a sample agent
  3. Build your own   — configure all four components and run your assembled agent

Run: streamlit run hour8_lab_agent_components.py
"""

import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Hour 8 — Agent Components", page_icon="🧩", layout="wide")
st.title("🧩 Hour 8 — Agent Components")
st.caption("Module 3 | Agent Types and Components")

st.markdown(
    """
Every agent — no matter how complex — is built from the same four core components.
Understanding these components is the first step to designing agents intentionally,
not just by trial and error.
"""
)

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Hour 8 Guide")
    st.markdown(
        """
**Three sections in this lab:**

1. **Component Gallery** — Read and absorb the four components and what each one controls in code.

2. **Annotate an Agent** — A real agent config is split into 4 segments. Label each one before submitting.

3. **Build Your Own** — Fill in all four components, then click Assemble & Run to see how they combine.
"""
    )
    st.divider()
    st.markdown("**Experiments to try in Section 3:**")
    st.markdown("- Clear the **Persona** — does the tone change?")
    st.markdown("- Change **Knowledge** to a different audience")
    st.markdown("- Add a new line to **Tools** — does the agent mention it?")
    st.markdown("- Set **Interaction** to `One sentence only` — does it comply?")
    st.divider()
    st.markdown("**Key principle:**")
    st.info(
        "Each component is independently tunable. "
        "That is what makes agents composable — "
        "you can swap the Persona without touching the Tools."
    )

# ── Component metadata ────────────────────────────────────────────────────────

COMPONENTS = [
    {
        "name": "Persona",
        "icon": "🎭",
        "color": "#1E88E5",
        "bg": "#E3F2FD",
        "what": "Defines who the agent is. Sets tone, expertise, and behavioural constraints.",
        "example": "You are a senior data engineer with 10 years of experience in distributed systems.",
        "maps_to": "The `system` parameter in every API call.",
    },
    {
        "name": "Knowledge",
        "icon": "📚",
        "color": "#43A047",
        "bg": "#E8F5E9",
        "what": "What the agent knows. Background facts, documents, retrieved data injected at runtime.",
        "example": "Company policy: all refunds over £500 require manager approval.",
        "maps_to": "Context blocks prepended to the `user` message, or retrieved from a vector store.",
    },
    {
        "name": "Tools",
        "icon": "🔧",
        "color": "#FB8C00",
        "bg": "#FFF3E0",
        "what": "What the agent can do beyond text generation. Search, calculation, API calls, database queries.",
        "example": "search_web(query), get_weather(city), create_ticket(title, priority)",
        "maps_to": "The `tools` parameter in the API call — each tool is a JSON schema the model reads.",
    },
    {
        "name": "Interaction Layer",
        "icon": "💬",
        "color": "#8E24AA",
        "bg": "#F3E5F5",
        "what": "How the agent communicates. Response structure, length, format, and style constraints.",
        "example": "Respond in valid JSON. Maximum 3 sentences. Always include a confidence score (0–1).",
        "maps_to": "Format instructions at the end of the system prompt or as a final user message.",
    },
]

# ── Section 1: Component gallery ──────────────────────────────────────────────

st.subheader("The Four Components")

cols = st.columns(4)
for col, comp in zip(cols, COMPONENTS):
    with col:
        st.markdown(
            f"<div style='border-top:4px solid {comp['color']};background:{comp['bg']};"
            f"border-radius:6px;padding:16px;min-height:260px;'>"
            f"<div style='font-size:2em;'>{comp['icon']}</div>"
            f"<div style='font-weight:bold;font-size:1.1em;color:{comp['color']};margin:6px 0;'>{comp['name']}</div>"
            f"<div style='font-size:0.88em;margin-bottom:10px;'>{comp['what']}</div>"
            f"<div style='font-size:0.78em;color:#666;font-style:italic;margin-bottom:8px;'>"
            f"e.g. {comp['example']}</div>"
            f"<div style='font-size:0.78em;color:#555;border-top:1px solid {comp['color']}40;padding-top:8px;'>"
            f"<strong>Maps to:</strong> {comp['maps_to']}"
            f"</div></div>",
            unsafe_allow_html=True,
        )

with st.expander("How these components map to production agent frameworks"):
    st.markdown(
        """
| Component | LangChain | LangGraph | Raw Anthropic API |
|-----------|-----------|-----------|-------------------|
| Persona | `SystemMessage` | `StateGraph` node prompt | `system` parameter |
| Knowledge | `Document` chunks in `VectorStore` | State field passed between nodes | Context in `user` message |
| Tools | `@tool` decorated functions | `ToolNode` | `tools` parameter |
| Interaction Layer | `StructuredOutputParser` | State schema types | Format instructions in system prompt |

The names differ across frameworks, but the **four components are always present**.
Recognising them lets you read any agent code and immediately understand its structure.
"""
    )

st.divider()

# ── Section 2: Annotate an Agent ──────────────────────────────────────────────

st.subheader("Exercise — Annotate a Sample Agent")
st.markdown(
    "Below is a real agent configuration split into four labelled segments. "
    "For each segment, select which component it belongs to. Then submit to see the correct answers."
)

SAMPLE_AGENT = {
    "A": {
        "code": 'system = "You are a customer support specialist for a SaaS product. '
                'You are calm, empathetic, and solutions-focused. You never make promises '
                'about features that do not yet exist."',
        "answer": "Persona",
        "reason": "This defines WHO the agent is — its identity, expertise, and behavioural constraints. "
                  "Nothing here describes a task, data, or format.",
    },
    "B": {
        "code": '# Injected at runtime from the CRM\ncontext = f"""\nCustomer: {customer_name}\n'
                'Plan: {plan_tier}\nOpen tickets: {open_count}\n'
                'Last interaction: {last_contact_date}\n"""',
        "answer": "Knowledge",
        "reason": "This is runtime context injected from an external system. The agent did not generate "
                  "this data — it is retrieved and passed in. That is the Knowledge component.",
    },
    "C": {
        "code": 'tools = [\n    {"name": "lookup_order", "description": "Look up order status by ID"},\n'
                '    {"name": "issue_refund", "description": "Process a refund up to £200"},\n'
                '    {"name": "escalate_ticket", "description": "Escalate to a human agent"}\n]',
        "answer": "Tools",
        "reason": "These are external capabilities the model can invoke. Without them, the agent can only "
                  "talk about refunds — with them, it can actually issue one.",
    },
    "D": {
        "code": 'format_instructions = """\nAlways respond in this structure:\n'
                '1. Acknowledgement (1 sentence)\n2. Solution or next step (2-3 sentences)\n'
                '3. Closing question to confirm resolution\nMaximum 120 words total.\n"""',
        "answer": "Interaction Layer",
        "reason": "This controls output structure, length, and style. It is not about identity, data, "
                  "or tools — it governs how the agent communicates.",
    },
}

COMPONENT_NAMES = [c["name"] for c in COMPONENTS]

if "annotate_answers" not in st.session_state:
    st.session_state.annotate_answers = {}
if "annotate_submitted" not in st.session_state:
    st.session_state.annotate_submitted = False

for seg_id, seg in SAMPLE_AGENT.items():
    st.markdown(f"**Segment {seg_id}**")
    st.code(seg["code"], language="python")
    if not st.session_state.annotate_submitted:
        choice = st.radio(
            f"Which component is Segment {seg_id}?",
            COMPONENT_NAMES,
            horizontal=True,
            key=f"ann_{seg_id}",
        )
        st.session_state.annotate_answers[seg_id] = choice
    else:
        correct = seg["answer"]
        chosen = st.session_state.annotate_answers.get(seg_id, "")
        comp_meta = next(c for c in COMPONENTS if c["name"] == correct)
        is_right = chosen == correct
        st.markdown(
            f"<div style='border-left:4px solid {comp_meta['color']};padding:10px 14px;"
            f"background:{comp_meta['bg']};border-radius:4px;margin-bottom:4px;'>"
            f"{'✅' if is_right else '❌'} You said <strong>{chosen}</strong> — "
            f"Correct answer: <strong style='color:{comp_meta['color']};'>{correct}</strong><br>"
            f"<span style='font-size:0.88em;color:#555;'>{seg['reason']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.write("")

if not st.session_state.annotate_submitted:
    if st.button("Submit Annotations", type="primary"):
        st.session_state.annotate_submitted = True
        correct_count = sum(
            1 for seg_id, seg in SAMPLE_AGENT.items()
            if st.session_state.annotate_answers.get(seg_id) == seg["answer"]
        )
        st.session_state.annotate_score = correct_count
        st.rerun()
else:
    score = st.session_state.get("annotate_score", 0)
    total = len(SAMPLE_AGENT)
    if score == total:
        st.success(f"🎉 Perfect score — {score}/{total}! You can identify all four components.")
    elif score >= 2:
        st.info(f"Score: {score}/{total}. Review the explanations above for the ones you missed.")
    else:
        st.warning(f"Score: {score}/{total}. Re-read the component gallery at the top and try again.")

    if st.button("Reset Exercise"):
        st.session_state.annotate_submitted = False
        st.session_state.annotate_answers = {}
        st.rerun()

st.divider()

# ── Section 3: Build Your Own Agent ──────────────────────────────────────────

st.subheader("Build Your Own Agent")
st.markdown(
    "Fill in each of the four components below. The app assembles them into a single system prompt "
    "and sends it to Claude. **Before clicking Run, form a hypothesis** — what do you expect Claude "
    "to say given your configuration? Then compare."
)

st.info(
    "⚠️ **Note on Tools:** In this lab, tool descriptions are passed as plain text inside the system "
    "prompt so the agent can reference them in its response. In a real production agent, tools are "
    "registered as JSON schemas in the API's `tools` parameter — Claude then decides when to call "
    "them and receives the results. We simulate this here so you can see how tool awareness changes "
    "the agent's reasoning without needing real function implementations."
)

DEFAULT_PERSONA = "You are a concise technical writer who specialises in explaining complex software concepts to non-technical stakeholders."
DEFAULT_KNOWLEDGE = "Context: The stakeholder is a VP of Marketing with no engineering background. They have 5 minutes before their next meeting."
DEFAULT_TOOLS = "web_search(query: str) — search the web for current information\nformat_as_slides(text: str) — convert text into a slide outline"
DEFAULT_INTERACTION = "Respond in plain English. Maximum 3 short paragraphs. Avoid jargon. End with one concrete next step."
DEFAULT_TASK = "Explain what a vector database is and why our engineering team wants to adopt one."

for key, default in [
    ("build_persona", DEFAULT_PERSONA),
    ("build_knowledge", DEFAULT_KNOWLEDGE),
    ("build_tools", DEFAULT_TOOLS),
    ("build_interaction", DEFAULT_INTERACTION),
    ("build_task", DEFAULT_TASK),
]:
    if key not in st.session_state:
        st.session_state[key] = default

comp_cols = st.columns(2)

with comp_cols[0]:
    st.markdown(
        f"<div style='color:{COMPONENTS[0]['color']};font-weight:bold;font-size:1em;'>"
        f"{COMPONENTS[0]['icon']} Persona</div>",
        unsafe_allow_html=True,
    )
    st.text_area("Persona:", value=st.session_state["build_persona"],
                 height=100, key="build_persona", label_visibility="collapsed")
    if st.button("Reset Persona"):
        st.session_state["build_persona"] = DEFAULT_PERSONA; st.rerun()

    st.write("")
    st.markdown(
        f"<div style='color:{COMPONENTS[2]['color']};font-weight:bold;font-size:1em;'>"
        f"{COMPONENTS[2]['icon']} Tools <span style='font-weight:normal;font-size:0.85em;'>(one per line — simulated, see note above)</span></div>",
        unsafe_allow_html=True,
    )
    st.text_area("Tools:", value=st.session_state["build_tools"],
                 height=100, key="build_tools", label_visibility="collapsed")
    if st.button("Reset Tools"):
        st.session_state["build_tools"] = DEFAULT_TOOLS; st.rerun()

with comp_cols[1]:
    st.markdown(
        f"<div style='color:{COMPONENTS[1]['color']};font-weight:bold;font-size:1em;'>"
        f"{COMPONENTS[1]['icon']} Knowledge (injected context)</div>",
        unsafe_allow_html=True,
    )
    st.text_area("Knowledge:", value=st.session_state["build_knowledge"],
                 height=100, key="build_knowledge", label_visibility="collapsed")
    if st.button("Reset Knowledge"):
        st.session_state["build_knowledge"] = DEFAULT_KNOWLEDGE; st.rerun()

    st.write("")
    st.markdown(
        f"<div style='color:{COMPONENTS[3]['color']};font-weight:bold;font-size:1em;'>"
        f"{COMPONENTS[3]['icon']} Interaction Layer (output format)</div>",
        unsafe_allow_html=True,
    )
    st.text_area("Interaction:", value=st.session_state["build_interaction"],
                 height=100, key="build_interaction", label_visibility="collapsed")
    if st.button("Reset Interaction"):
        st.session_state["build_interaction"] = DEFAULT_INTERACTION; st.rerun()

st.write("")
st.markdown("<div style='font-weight:bold;'>📨 User Task / Request</div>", unsafe_allow_html=True)
st.text_area("Task:", value=st.session_state["build_task"],
             height=70, key="build_task", label_visibility="collapsed")
if st.button("Reset Task"):
    st.session_state["build_task"] = DEFAULT_TASK; st.rerun()

run_build = st.button("▶  Assemble & Run Agent", type="primary",
                       disabled=not st.session_state["build_task"].strip())

if run_build and st.session_state["build_task"].strip():
    persona = st.session_state["build_persona"]
    knowledge = st.session_state["build_knowledge"]
    tools_text = st.session_state["build_tools"]
    interaction = st.session_state["build_interaction"]
    task = st.session_state["build_task"]

    assembled_system = f"{persona.strip()}\n\n"
    if knowledge.strip():
        assembled_system += f"Background knowledge:\n{knowledge.strip()}\n\n"
    if tools_text.strip():
        tool_lines = [ln.strip() for ln in tools_text.strip().split("\n") if ln.strip()]
        assembled_system += "Available tools (describe how you would use them if relevant):\n"
        for tl in tool_lines:
            assembled_system += f"  • {tl}\n"
        assembled_system += "\n"
    assembled_system += interaction.strip()

    with st.expander("View assembled system prompt", expanded=True):
        st.code(assembled_system, language="text")

    with st.container(border=True):
        st.markdown("### Agent Response")
        with st.spinner("Agent running..."):
            response, usage = chat(
                system=assembled_system,
                user=task.strip(),
                max_tokens=600,
                temperature=0.7,
            )
        st.markdown(response)
        c1, c2 = st.columns(2)
        c1.metric("Input tokens", usage["input_tokens"])
        c2.metric("Output tokens", usage["output_tokens"])

    st.divider()
    st.markdown(
        """
**Did the response match your hypothesis?**

Now try changing one component at a time and re-running:
- Remove the **Persona** entirely — does the response feel less focused?
- Change the **Knowledge** audience to "a 12-year-old" — does the vocabulary shift?
- Add `send_email(to, subject, body)` to **Tools** — does the agent acknowledge it?
- Set **Interaction** to `Respond in a single bullet point only` — does it comply?
"""
    )
