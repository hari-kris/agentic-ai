"""
Code Review Agent — Module 4 Bonus Lab
Module 4 | Core Agentic Patterns I

Four specialist critic agents review code in sequence. Each agent passes its
findings to the next via a growing handoff package. A Synthesiser produces a
prioritised action list ranked by severity.

Patterns demonstrated: Reflection · Orchestrator-Workers · Handoff State
Run: streamlit run module-4/lab_code_review_agent.py
"""

import json
import streamlit as st
from claude_client import chat

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Code Review Agent", page_icon="🔍", layout="wide")
st.title("🔍 Code Review Agent")
st.caption("Module 4 | Core Agentic Patterns I — Bonus Lab")

st.markdown("""
Four specialist critic agents review your code in sequence. Each agent passes its
findings to the next via a growing **handoff package** — so later agents see what
earlier ones already found, and never repeat the same issues.

**What you'll see:**
1. The **system prompt** that defines each critic's role and output format
2. How the **handoff state grows** from Security → Performance → Readability → Logic
3. Each agent's **structured JSON findings** — issues, severity, concrete fixes
4. A **synthesised priority report** ranking all findings by severity
""")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Lab Guide")
    st.markdown("""
**Review pipeline (5 Claude API calls):**
1. **Security Agent** — finds vulnerabilities and risks
2. **Performance Agent** — finds inefficiencies (sees security findings)
3. **Readability Agent** — scores clarity and naming (sees all prior)
4. **Logic Agent** — finds edge cases and bugs (sees all prior)
5. **Synthesiser** — deduplicates, ranks, scores, writes verdict

**What to observe:**
- How the handoff state grows between each agent
- How the same Claude model takes a different expert persona per agent
- Why structured JSON output makes each finding composable
- The compound token cost of a 5-call sequential pipeline
""")
    st.divider()
    st.markdown("**Preset examples to try:**")
    st.markdown("- *SQL Query Builder* — classic security issues")
    st.markdown("- *List Processor* — O(n²) and N+1 performance problems")
    st.markdown("- *Auth Function* — multiple issue types across all critics")
    st.markdown("- *Data Parser* — poor naming + logic edge cases")
    st.divider()
    st.info(
        "**Key principle:** Security Agent and Logic Agent are the same Claude model. "
        "Different system prompts create different expert personas — "
        "the role IS the system prompt."
    )

# ── Agent Styles (course colour convention) ────────────────────────────────────
AGENT_STYLES = {
    "security":    {"color": "#E53935", "label": "Security Agent",    "icon": "🔐"},
    "performance": {"color": "#FB8C00", "label": "Performance Agent", "icon": "⚡"},
    "readability": {"color": "#1E88E5", "label": "Readability Agent", "icon": "📖"},
    "logic":       {"color": "#8E24AA", "label": "Logic Agent",       "icon": "🧠"},
    "synthesis":   {"color": "#43A047", "label": "Synthesiser",       "icon": "📋"},
}

SEVERITY_COLORS = {
    "critical": "#B71C1C",
    "high":     "#E53935",
    "medium":   "#FB8C00",
    "low":      "#F9A825",
}

# ── System Prompts ─────────────────────────────────────────────────────────────
SECURITY_SYSTEM = """\
You are a security-focused code reviewer. Your only job is to identify security vulnerabilities.

Look for:
- SQL, command, or path-traversal injection risks
- Hardcoded credentials or API keys
- Unsafe use of eval(), exec(), or dynamic code execution
- Missing input validation and sanitisation
- Insecure data handling, open file paths, or data exposure

Return ONLY valid JSON — no markdown fences, no prose outside the JSON:
{
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "location": "brief description of where in the code",
      "description": "what the vulnerability is",
      "fix": "concrete fix recommendation"
    }
  ],
  "score": <integer 1–5 where 5 = no security issues>,
  "summary": "one sentence summary of security posture"
}

If no issues are found return an empty issues list and score 5.\
"""

PERFORMANCE_SYSTEM = """\
You are a performance-focused code reviewer. Your only job is to identify efficiency problems.

Look for:
- Unnecessary nested loops that raise time complexity
- Repeated computation that could be cached or hoisted
- Inefficient data structure choices (list search vs set lookup, etc.)
- N+1 database or API call patterns
- Missing early exits, short-circuits, or lazy evaluation

You will also receive security findings already identified — do NOT repeat those issues.

Return ONLY valid JSON — no markdown fences, no prose outside the JSON:
{
  "issues": [
    {
      "severity": "high|medium|low",
      "location": "brief description of where in the code",
      "description": "what the inefficiency is",
      "fix": "concrete fix recommendation"
    }
  ],
  "score": <integer 1–5 where 5 = no performance issues>,
  "summary": "one sentence summary of performance"
}

If no issues are found return an empty issues list and score 5.\
"""

READABILITY_SYSTEM = """\
You are a readability-focused code reviewer. Your only job is to assess code clarity.

Look for:
- Poor variable, function, or class naming (single letters, cryptic abbreviations)
- Missing or inadequate docstrings and comments on non-obvious logic
- Overly complex or deeply nested logic that could be simplified
- Magic numbers or hardcoded literals that should be named constants
- Inconsistent style that makes the code harder to scan

You will also receive security and performance findings — do NOT repeat those issues.

Return ONLY valid JSON — no markdown fences, no prose outside the JSON:
{
  "issues": [
    {
      "severity": "high|medium|low",
      "location": "brief description of where in the code",
      "description": "what the readability issue is",
      "fix": "concrete fix recommendation"
    }
  ],
  "score": <integer 1–5 where 5 = excellent readability>,
  "summary": "one sentence summary of code readability"
}

If no issues are found return an empty issues list and score 5.\
"""

LOGIC_SYSTEM = """\
You are a logic-focused code reviewer. Your only job is to find bugs and edge-case failures.

Look for:
- Off-by-one errors in loops or index access
- Missing null / None / empty-collection checks before use
- Incorrect conditional logic or operator precedence errors
- Unhandled exception paths or swallowed errors
- Division by zero or other arithmetic edge cases
- Incorrect assumptions about input types or ranges

You will also receive security, performance, and readability findings — do NOT repeat those issues.

Return ONLY valid JSON — no markdown fences, no prose outside the JSON:
{
  "issues": [
    {
      "severity": "critical|high|medium|low",
      "location": "brief description of where in the code",
      "description": "what the logic issue is",
      "fix": "concrete fix recommendation"
    }
  ],
  "score": <integer 1–5 where 5 = no logic issues>,
  "summary": "one sentence summary of logic correctness"
}

If no issues are found return an empty issues list and score 5.\
"""

SYNTHESIS_SYSTEM = """\
You are a senior engineering lead synthesising code review findings from four specialist reviewers:
Security Agent, Performance Agent, Readability Agent, and Logic Agent.

Your tasks:
1. Rank ALL issues across all four reviewers by priority (critical first, then high, medium, low)
2. Remove any duplicate issues that appear across multiple reviewers
3. Compute an overall score: average of the four individual scores, rounded to one decimal place
4. Write a brief, honest overall verdict

Return ONLY valid JSON — no markdown fences, no prose outside the JSON:
{
  "priority_actions": [
    {
      "rank": <integer starting at 1>,
      "category": "security|performance|readability|logic",
      "severity": "critical|high|medium|low",
      "description": "clear description of the action to take",
      "fix": "concrete implementation recommendation"
    }
  ],
  "scores": {
    "security":    <score from security agent 1–5>,
    "performance": <score from performance agent 1–5>,
    "readability": <score from readability agent 1–5>,
    "logic":       <score from logic agent 1–5>,
    "overall":     <average of the four, rounded to 1 decimal>
  },
  "verdict": "needs significant work|needs some work|acceptable|good|excellent",
  "summary": "2–3 sentence overall assessment of the code"
}\
"""

# ── Helpers ────────────────────────────────────────────────────────────────────
def parse_json(raw: str) -> dict:
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        return {"error": "JSON parse failed", "raw": raw[:300], "issues": [], "score": 0, "summary": ""}


def severity_badge(sev: str) -> str:
    color = SEVERITY_COLORS.get(sev.lower(), "#999")
    return (
        f"<span style='background:{color};color:white;padding:2px 8px;"
        f"border-radius:10px;font-size:0.77em;font-weight:bold;'>{sev.upper()}</span>"
    )


def score_bar(score: int | float, color: str) -> str:
    try:
        pct = float(score) * 20
    except (TypeError, ValueError):
        pct = 0
    label = {1: "Critical", 2: "Poor", 3: "Fair", 4: "Good", 5: "Excellent"}.get(int(round(float(score or 0))), "")
    return (
        f"<div style='margin:4px 0 6px 0;'>"
        f"<div style='background:#eee;border-radius:4px;height:9px;width:100%;'>"
        f"<div style='background:{color};width:{pct}%;height:9px;border-radius:4px;'></div></div>"
        f"<span style='font-size:0.78em;color:{color};'>{score}/5 — {label}</span></div>"
    )

# ── Code Presets ───────────────────────────────────────────────────────────────
PRESETS = {
    "Custom — paste your own code": "",

    "SQL Query Builder (security issues)": """\
def get_user(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def delete_account(user_id):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM accounts WHERE id={user_id}")
    conn.commit()
    conn.close()
""",

    "List Processor (performance issues)": """\
def find_duplicates(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                if items[i] not in duplicates:
                    duplicates.append(items[i])
    return duplicates

def get_user_names(user_ids):
    names = []
    for uid in user_ids:
        user = db.query(f"SELECT name FROM users WHERE id = {uid}")
        names.append(user["name"])
    return names
""",

    "Auth Function (multiple issue types)": """\
def login(u, p):
    r = db.execute("SELECT * FROM users WHERE name='" + u + "'")
    if r:
        if r[0]["pass"] == p:
            tok = str(random.random())
            sessions[tok] = u
            return tok
    return None

def get_file(token, filename):
    u = sessions[token]
    path = "/data/" + u + "/" + filename
    return open(path).read()

def is_admin(token):
    user = sessions[token]
    roles = db.execute("SELECT role FROM users WHERE name='" + user + "'")
    if roles[0] == "admin":
        return True
""",

    "Data Parser (logic + readability issues)": """\
def p(d):
    r = []
    for i in range(len(d)):
        x = d[i].split(",")
        if len(x) > 0:
            n = x[0]
            v = x[1]
            if v > 0:
                r.append({"n": n, "v": int(v)})
    return r

def calc(items):
    t = 0
    for i in items:
        t = t + i["v"]
    avg = t / len(items)
    return avg

def top(items, n):
    s = sorted(items, key=lambda x: x["v"])
    return s[0:n]
""",
}

# ── Run Review Pipeline ────────────────────────────────────────────────────────
def run_code_review(code: str) -> dict:
    """Run all five agents in sequence, accumulating the handoff state."""
    findings: dict = {}
    stages: list   = []
    token_totals   = {"input": 0, "output": 0}

    # Stage 1 — Security (sees only the code)
    msg = f"Review this code for security issues:\n\n```\n{code}\n```"
    raw, usage = chat(SECURITY_SYSTEM, msg, max_tokens=900, temperature=0.2)
    token_totals["input"]  += usage["input_tokens"]
    token_totals["output"] += usage["output_tokens"]
    findings["security"] = parse_json(raw)
    stages.append(("security", findings["security"], usage))

    # Stage 2 — Performance (sees code + security findings)
    msg = (
        f"Review this code for performance issues.\n\n"
        f"Code:\n```\n{code}\n```\n\n"
        f"Security findings already identified (do NOT repeat these):\n"
        f"{json.dumps(findings['security'], indent=2)}"
    )
    raw, usage = chat(PERFORMANCE_SYSTEM, msg, max_tokens=900, temperature=0.2)
    token_totals["input"]  += usage["input_tokens"]
    token_totals["output"] += usage["output_tokens"]
    findings["performance"] = parse_json(raw)
    stages.append(("performance", findings["performance"], usage))

    # Stage 3 — Readability (sees code + security + performance)
    msg = (
        f"Review this code for readability issues.\n\n"
        f"Code:\n```\n{code}\n```\n\n"
        f"Prior findings already identified (do NOT repeat these):\n"
        f"{json.dumps({'security': findings['security'], 'performance': findings['performance']}, indent=2)}"
    )
    raw, usage = chat(READABILITY_SYSTEM, msg, max_tokens=900, temperature=0.2)
    token_totals["input"]  += usage["input_tokens"]
    token_totals["output"] += usage["output_tokens"]
    findings["readability"] = parse_json(raw)
    stages.append(("readability", findings["readability"], usage))

    # Stage 4 — Logic (sees code + all three prior findings)
    prior_three = {k: findings[k] for k in ("security", "performance", "readability")}
    msg = (
        f"Review this code for logic bugs and edge-case failures.\n\n"
        f"Code:\n```\n{code}\n```\n\n"
        f"Prior findings already identified (do NOT repeat these):\n"
        f"{json.dumps(prior_three, indent=2)}"
    )
    raw, usage = chat(LOGIC_SYSTEM, msg, max_tokens=900, temperature=0.2)
    token_totals["input"]  += usage["input_tokens"]
    token_totals["output"] += usage["output_tokens"]
    findings["logic"] = parse_json(raw)
    stages.append(("logic", findings["logic"], usage))

    # Stage 5 — Synthesiser (sees code + all four findings)
    msg = (
        f"Synthesise these four code review findings into a ranked priority action list.\n\n"
        f"Original code:\n```\n{code}\n```\n\n"
        f"All findings:\n{json.dumps(findings, indent=2)}"
    )
    raw, usage = chat(SYNTHESIS_SYSTEM, msg, max_tokens=1200, temperature=0.2)
    token_totals["input"]  += usage["input_tokens"]
    token_totals["output"] += usage["output_tokens"]
    synthesis = parse_json(raw)
    stages.append(("synthesis", synthesis, usage))

    return {
        "findings":     findings,
        "synthesis":    synthesis,
        "stages":       stages,
        "token_totals": token_totals,
    }

# ── Render Review Trace ────────────────────────────────────────────────────────
def render_review_trace(result: dict):
    findings  = result["findings"]
    synthesis = result["synthesis"]
    stages    = result["stages"]

    st.markdown("### Review trace")
    handoff_chars = 0

    for agent_key, agent_data, usage in stages:
        if agent_key == "synthesis":
            continue

        style   = AGENT_STYLES[agent_key]
        issues  = agent_data.get("issues", [])
        score   = agent_data.get("score", 0)
        summary = agent_data.get("summary", "")

        # Agent header card
        st.markdown(
            f"<div style='background:#FAFAFA;border-left:5px solid {style['color']};"
            f"border-radius:6px;padding:10px 16px;margin:10px 0 4px 0;'>"
            f"<strong style='color:{style['color']};font-size:1.05em;'>"
            f"{style['icon']} {style['label']}</strong>"
            f"&ensp;<span style='font-size:0.8em;color:#999;'>"
            f"{usage['input_tokens']} in / {usage['output_tokens']} out tokens</span>"
            f"{score_bar(score, style['color'])}"
            f"<span style='font-size:0.88em;color:#555;'>{summary}</span></div>",
            unsafe_allow_html=True,
        )

        # Issues
        if issues:
            for issue in issues:
                sev = issue.get("severity", "low").lower()
                border = SEVERITY_COLORS.get(sev, "#999")
                st.markdown(
                    f"<div style='background:#FAFAFA;border-left:3px solid {border};"
                    f"padding:6px 12px;margin:3px 0 3px 22px;border-radius:4px;font-size:0.87em;'>"
                    f"{severity_badge(sev)}&ensp;"
                    f"<strong>{issue.get('location', '')}</strong> — {issue.get('description', '')}<br>"
                    f"<span style='color:#2E7D32;'>💡 {issue.get('fix', '')}</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f"<div style='color:#43A047;font-size:0.87em;margin:3px 0 3px 22px;'>"
                f"✅ No {agent_key} issues found.</div>",
                unsafe_allow_html=True,
            )

        # Handoff size indicator
        handoff_chars += len(json.dumps(agent_data))
        st.markdown(
            f"<div style='text-align:center;color:#00897B;font-size:0.78em;margin:2px 0;'>"
            f"↓&ensp;handoff package grows to ~{handoff_chars:,} chars</div>",
            unsafe_allow_html=True,
        )

    # ── Synthesis output ───────────────────────────────────────────────────────
    st.markdown("---")
    style   = AGENT_STYLES["synthesis"]
    scores  = synthesis.get("scores", {})
    verdict = synthesis.get("verdict", "")
    summary = synthesis.get("summary", "")
    actions = synthesis.get("priority_actions", [])

    st.markdown(
        f"<div style='background:#E8F5E9;border-left:5px solid {style['color']};"
        f"border-radius:6px;padding:10px 16px;margin:6px 0;'>"
        f"<strong style='color:{style['color']};font-size:1.1em;'>"
        f"{style['icon']} {style['label']}"
        f"{' — ' + verdict.upper() if verdict else ''}</strong><br>"
        f"<span style='font-size:0.9em;color:#444;'>{summary}</span></div>",
        unsafe_allow_html=True,
    )

    # Score grid
    if scores:
        cols = st.columns(5)
        for col, key in zip(cols, ("security", "performance", "readability", "logic", "overall")):
            val   = scores.get(key, "–")
            color = AGENT_STYLES.get(key, {"color": "#43A047"})["color"]
            col.markdown(
                f"<div style='text-align:center;padding:6px 0;'>"
                f"<div style='font-size:0.75em;color:#888;text-transform:capitalize;'>{key}</div>"
                f"<div style='font-size:2em;font-weight:bold;color:{color};'>{val}</div>"
                f"<div style='font-size:0.72em;color:#aaa;'>/ 5</div></div>",
                unsafe_allow_html=True,
            )

    # Priority action list
    if actions:
        st.markdown("**Priority action list:**")
        for action in actions:
            sev      = action.get("severity", "low").lower()
            cat      = action.get("category", "")
            cat_s    = AGENT_STYLES.get(cat, {"color": "#888", "icon": "•"})
            border   = SEVERITY_COLORS.get(sev, "#999")
            st.markdown(
                f"<div style='background:#F9FBE7;border-left:4px solid {border};"
                f"padding:7px 12px;margin:4px 0;border-radius:4px;font-size:0.88em;'>"
                f"<strong style='color:#333;'>#{action.get('rank','')} &ensp;"
                f"<span style='color:{cat_s['color']};'>{cat_s['icon']} {cat.title()}</span></strong>"
                f"&ensp;{severity_badge(sev)}<br>"
                f"{action.get('description', '')}<br>"
                f"<span style='color:#2E7D32;'>💡 {action.get('fix', '')}</span></div>",
                unsafe_allow_html=True,
            )

# ── Section 1: Agent Explorer ──────────────────────────────────────────────────
st.divider()
st.subheader("1 — The Four Specialist Critics")

st.markdown("""
Each critic is defined entirely by its **system prompt**.
The same Claude model becomes four different expert reviewers — purely through prompting.
Notice how each subsequent agent is told *"do not repeat prior findings"* — this keeps the
handoff clean and each critic focused on its own domain.
""")

_PROMPT_MAP = {
    "security":    ("🔐 Security Agent",    SECURITY_SYSTEM),
    "performance": ("⚡ Performance Agent", PERFORMANCE_SYSTEM),
    "readability": ("📖 Readability Agent", READABILITY_SYSTEM),
    "logic":       ("🧠 Logic Agent",       LOGIC_SYSTEM),
}
for key, (label, prompt) in _PROMPT_MAP.items():
    color = AGENT_STYLES[key]["color"]
    with st.expander(label, expanded=False):
        st.markdown(
            f"<div style='border-left:4px solid {color};padding:4px 10px;margin-bottom:8px;"
            f"background:#FAFAFA;border-radius:4px;font-size:0.85em;color:#555;'>"
            f"Returns: JSON with <code>issues[]</code>, <code>score 1–5</code>, "
            f"<code>summary</code></div>",
            unsafe_allow_html=True,
        )
        st.code(prompt, language="text")

# ── Section 2: How It Works ────────────────────────────────────────────────────
st.divider()
st.subheader("2 — How It Works")

with st.expander("🗺️  Architecture — the 5-stage review pipeline", expanded=True):
    _ARROW = "<div style='text-align:center;font-size:1.3em;color:#aaa;margin:1px 0;'>▼</div>"
    _BOX = (
        "<div style='background:{bg};border-left:5px solid {border};"
        "border-radius:6px;padding:8px 14px;margin:3px 0;'>"
        "<strong style='color:{border};'>{icon} {title}</strong>"
        "<br><span style='font-size:0.87em;color:#444;'>{body}</span></div>"
    )
    for item in [
        dict(bg="#E3F2FD", border="#1E88E5", icon="1️⃣",
             title="Code Input",
             body="You paste a code snippet. It becomes the payload for all five agents."),
        dict(bg="#FFEBEE", border="#E53935", icon="2️⃣",
             title="Security Agent",
             body="Receives: code only. Scans for injection, secrets, unsafe eval. "
                  "Returns JSON: issues + score."),
        dict(bg="#FFF3E0", border="#FB8C00", icon="3️⃣",
             title="Performance Agent",
             body="Receives: code + security JSON. Scans for O(n²), N+1, wasted computation. "
                  "Does NOT repeat security issues."),
        dict(bg="#E3F2FD", border="#1E88E5", icon="4️⃣",
             title="Readability Agent",
             body="Receives: code + security + performance JSON. Checks naming, comments, complexity. "
                  "Does NOT repeat prior issues."),
        dict(bg="#F3E5F5", border="#8E24AA", icon="5️⃣",
             title="Logic Agent",
             body="Receives: code + all three prior JSON objects. Finds null checks, off-by-ones, "
                  "bad conditionals. Does NOT repeat prior issues."),
        dict(bg="#E8F5E9", border="#43A047", icon="6️⃣",
             title="Synthesiser",
             body="Receives: code + all four findings. Deduplicates, ranks by severity, "
                  "computes overall score, writes verdict."),
    ]:
        st.markdown(_BOX.format(**item), unsafe_allow_html=True)
        if item["icon"] != "6️⃣":
            st.markdown(_ARROW, unsafe_allow_html=True)

with st.expander("📦  Handoff State — how findings accumulate between agents"):
    st.markdown(
        "Each agent is given all prior findings as part of its user message. "
        "This growing package serves two purposes: it prevents duplicate findings, "
        "and it lets later agents build on earlier context."
    )
    st.code("""\
# Stage 1 — Security sees only the code
msg = f"Review this code for security issues:\\n\\n```\\n{code}\\n```"

# Stage 2 — Performance sees code + security JSON
msg = (
    f"Review for performance issues.\\n\\nCode:\\n```\\n{code}\\n```\\n\\n"
    f"Security findings already identified (do NOT repeat):\\n"
    f"{json.dumps(findings['security'], indent=2)}"
)

# Stage 3 — Readability sees code + security + performance
msg = (
    f"Review for readability issues.\\n\\nCode:\\n```\\n{code}\\n```\\n\\n"
    f"Prior findings (do NOT repeat):\\n"
    f"{json.dumps({'security': findings['security'],
                   'performance': findings['performance']}, indent=2)}"
)

# Stage 4 — Logic sees code + all three prior findings
# Stage 5 — Synthesiser sees code + all four findings
""", language="python")
    st.markdown(
        "Notice the handoff size indicator in the trace (↓ ~N chars). "
        "By Stage 5 the Synthesiser's input is 5–10× the size of Stage 1's input — "
        "that is the accumulated knowledge of the whole pipeline."
    )

with st.expander("🧱  Structured JSON Output — why every agent must return JSON"):
    st.markdown(
        "Each agent is instructed to return **only valid JSON** with no prose outside it. "
        "This is what makes the handoff composable — each agent's output becomes "
        "the next agent's input directly via `json.dumps()`."
    )
    st.code("""\
# What Security Agent returns (example):
{
  "issues": [
    {
      "severity": "critical",
      "location": "cursor.execute(query) on line 4",
      "description": "SQL injection — username is concatenated directly into the query string",
      "fix": "Use parameterised queries: cursor.execute('SELECT * FROM users WHERE username=?', (username,))"
    }
  ],
  "score": 1,
  "summary": "Critical SQL injection vulnerability — user input is never sanitised"
}
""", language="json")
    st.code("""\
# How the agent is invoked and its output parsed:
raw, usage = chat(SECURITY_SYSTEM, user_message, max_tokens=900, temperature=0.2)

# Strip any accidental markdown fences before parsing
clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
findings["security"] = json.loads(clean)

# Pass directly to next agent as context
f"Prior findings:\\n{json.dumps(findings['security'], indent=2)}"
""", language="python")

with st.expander("💰  Token Cost — why 5 calls cost more than 5× a single call"):
    st.markdown("""
Each stage resends the code *plus all prior findings*. Input tokens grow at every stage:

| Stage | What's sent as input | ~Input tokens (medium snippet) |
|-------|----------------------|-------------------------------|
| Security | code only | ~200 |
| Performance | code + security JSON | ~450 |
| Readability | code + security + performance | ~750 |
| Logic | code + all three findings | ~1,100 |
| Synthesiser | code + all four findings | ~1,600 |

**Total ≈ 4,100+ input tokens** for a 20-line code snippet.

This is the cost of **specialisation** — each expert gets full context.
The per-stage token breakdown at the bottom of the results shows exactly where tokens are spent.
""")

# ── Section 3: Run the Review ──────────────────────────────────────────────────
st.divider()
st.subheader("3 — Review Your Code")

sel = st.selectbox("Choose a preset or paste your own:", list(PRESETS.keys()), key="preset_sel")
code_input = st.text_area(
    "Code to review:",
    value=PRESETS[sel],
    height=240,
    placeholder="Paste any code snippet here (Python, JavaScript, etc.)…",
    key="code_input",
)

col_run, col_hint = st.columns([1, 3])
with col_run:
    run_btn = st.button(
        "▶ Run Code Review", type="primary", disabled=not code_input.strip()
    )
with col_hint:
    st.caption("Runs 5 Claude API calls: Security → Performance → Readability → Logic → Synthesis")

if run_btn and code_input.strip():
    with st.spinner("Running 5-agent review pipeline…"):
        result = run_code_review(code_input.strip())

    render_review_trace(result)

    # ── Metrics ────────────────────────────────────────────────────────────────
    st.divider()
    stages = result["stages"]
    totals = result["token_totals"]
    total_issues = sum(
        len(result["findings"].get(k, {}).get("issues", []))
        for k in ("security", "performance", "readability", "logic")
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("API calls made", 5)
    c2.metric("Total issues found", total_issues)
    c3.metric("Total input tokens",  totals["input"])
    c4.metric("Total output tokens", totals["output"])

    # Per-agent token breakdown
    st.markdown("**Token cost per agent:**")
    for agent_key, _, usage in stages:
        s = AGENT_STYLES.get(agent_key, {"color": "#888", "label": agent_key, "icon": "•"})
        st.markdown(
            f"<div style='display:inline-block;background:{s['color']}22;"
            f"border:1px solid {s['color']};padding:3px 10px;border-radius:6px;"
            f"margin:3px;font-size:0.85em;'>"
            f"<strong style='color:{s['color']};'>{s['icon']} {s['label']}</strong>"
            f"&ensp;{usage['input_tokens']} in / {usage['output_tokens']} out</div>",
            unsafe_allow_html=True,
        )
