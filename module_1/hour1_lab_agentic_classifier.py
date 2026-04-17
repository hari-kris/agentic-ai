"""
Hour 1 Lab — Is This Agentic?
Module 1 | Agentic AI Foundations

Students submit an app description. Claude classifies it against the four
agentic properties. The student guesses first — Claude reveals verdict after.

Run: streamlit run hour1_lab_agentic_classifier.py
"""

import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Hour 1 — Is This Agentic?", page_icon="🤖")
st.title("Hour 1 Lab — Is This Agentic?")
st.caption("Module 1 | Agentic AI Foundations")

st.markdown(
    "Submit an AI app description. Claude will score it against the **four agentic properties** "
    "and return a verdict. Make your guess before hitting Classify."
)

SYSTEM_PROMPT = """\
You are an expert in agentic AI systems.

The four properties that define an agentic system are:
1. Goal-directed   — works toward a high-level objective autonomously, without per-step human instruction
2. Tool-using      — calls external tools (search, code execution, APIs, databases) to act in the world
3. Iterative       — operates in loops: plan → act → observe → reflect → repeat
4. Memory-aware    — maintains context across multiple steps (short-term or long-term)

Given an app or product description, evaluate which of the four properties it exhibits.
Then give a verdict.

Format your response exactly as:

**Property Analysis:**
- Goal-directed:  [Yes / Partial / No] — [one sentence reason]
- Tool-using:     [Yes / Partial / No] — [one sentence reason]
- Iterative:      [Yes / Partial / No] — [one sentence reason]
- Memory-aware:   [Yes / Partial / No] — [one sentence reason]

**Verdict:** [AGENTIC / PARTIALLY AGENTIC / NOT AGENTIC]

**Reasoning:** [2–3 sentences explaining the verdict in plain language]\
"""

EXAMPLES = [
    "Select an example or write your own below...",
    "ChatGPT (basic): You type a question and it gives you an answer. Each conversation is independent.",
    "GitHub Copilot Workspace: Reads your codebase, proposes architectural changes, writes code, runs tests, observes failures, and revises — all without per-step human instruction.",
    "Spotify playlist generator: You type a mood and it recommends 10 songs from its catalogue.",
    "Perplexity Deep Research: Given a research question, plans a search strategy, retrieves multiple documents, synthesises evidence across sources, and produces a cited report from a single user query.",
    "An email autocomplete feature that suggests the next word as you type based on your writing style.",
    "Salesforce Agentforce: Classifies incoming customer queries, retrieves relevant policy documents, drafts responses, and escalates edge cases — all in a connected automated flow.",
]

example = st.selectbox("Try a pre-written example:", EXAMPLES)
description = st.text_area(
    "App description:",
    value="" if example == EXAMPLES[0] else example,
    height=120,
    placeholder="Describe an AI app, product, or feature...",
)

student_guess = st.radio(
    "Your guess before Claude answers:",
    ["Agentic", "Partially Agentic", "Not Agentic"],
    horizontal=True,
)

if st.button("Classify with Claude", type="primary"):
    if not description.strip():
        st.warning("Enter a description first.")
    else:
        with st.spinner("Claude is analysing..."):
            response, usage = chat(SYSTEM_PROMPT, description.strip())

        st.divider()

        col_guess, col_verdict = st.columns(2)
        with col_guess:
            st.subheader("Your Guess")
            st.info(student_guess)
        with col_verdict:
            st.subheader("Claude's Verdict")
            if "AGENTIC" in response and "NOT AGENTIC" not in response and "PARTIALLY" not in response:
                st.success("AGENTIC")
            elif "PARTIALLY AGENTIC" in response:
                st.warning("PARTIALLY AGENTIC")
            else:
                st.error("NOT AGENTIC")

        st.subheader("Full Analysis")
        st.markdown(response)

        st.divider()
        col1, col2 = st.columns(2)
        col1.metric("Input tokens", usage["input_tokens"])
        col2.metric("Output tokens", usage["output_tokens"])

        with st.expander("View the exact prompt sent to Claude"):
            st.markdown("**System prompt** (defines Claude's role):")
            st.code(SYSTEM_PROMPT, language="text")
            st.markdown("**User message** (your description):")
            st.code(description.strip(), language="text")

st.divider()
with st.expander("The four agentic properties — quick reference"):
    st.markdown(
        """
| Property | Question to ask |
|---|---|
| Goal-directed | Does it receive a high-level goal and work toward it autonomously? |
| Tool-using | Can it call external services, search engines, or code runners? |
| Iterative | Does it loop — plan, act, observe, revise — rather than answer once? |
| Memory-aware | Does it remember what it did in earlier steps? |
"""
    )
