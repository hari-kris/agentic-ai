"""
Hour 4B Lab — Output Format Reliability Lab
Module 2 | Prompt Fundamentals

The same data extraction task is run with 5 different output format
instructions, each 3 times at temperature 0.7.

For each run, the lab attempts to parse the output programmatically
and records: parsed successfully / fields found / fields missing.

Key insight: in agentic systems an unparseable response breaks the pipeline.
Format instructions are not cosmetic — they are correctness requirements.
The difference in parse reliability between formats is the lesson.

Run: streamlit run hour4b_lab_output_format_reliability.py
"""

import json
import re
import streamlit as st
from claude_client import chat

st.set_page_config(page_title="Output Format Reliability", page_icon="📐", layout="wide")
st.title("📐 Hour 4B — Output Format Reliability Lab")
st.caption("Module 2 | Prompt Fundamentals")

st.markdown(
    """
The **same extraction task** is run with **5 different format instructions**, each **3 times**.
Every response is parsed programmatically. The reliability score = successful parses / 3 runs.

**Why this matters for agentic systems:** Your pipeline code calls `json.loads()` or a regex.
If the model adds a preamble, wraps JSON in markdown, or skips a field — the parse fails
and the pipeline crashes. Format instructions prevent this.
"""
)

# ── Source data ───────────────────────────────────────────────────────────────

SOURCE_TEXT = """
Support Ticket #4821
From: Marcus Chen (marcus.chen@techcorp.io)
Date: 14 April 2026, 09:42

Hi support team,

I've been trying to generate a PDF report for our Q1 data for the past two days
and it keeps timing out at around 80%. This is blocking our board presentation
scheduled for tomorrow morning. Our account tier is Enterprise.

The problem started after your platform update on 12 April. I've tried Chrome,
Firefox, and Edge — same result on all. Error code shown: EXPORT_TIMEOUT_503.

Please treat this as urgent.

Marcus Chen, Head of Analytics, TechCorp
"""

EXPECTED_FIELDS = ["customer_name", "email", "issue_type", "urgency", "error_code"]

TASK_BASE = (
    "Extract the following fields from this support ticket:\n"
    "- customer_name: full name of the person who raised the ticket\n"
    "- email: their email address\n"
    "- issue_type: one of EXPORT_FAILURE, LOGIN_ISSUE, PERFORMANCE, BILLING, OTHER\n"
    "- urgency: HIGH, MEDIUM, or LOW based on language and context\n"
    "- error_code: the error code mentioned, or null if none\n\n"
    f"Ticket:\n{SOURCE_TEXT}"
)

# ── Format variants ───────────────────────────────────────────────────────────

FORMATS = [
    {
        "name": "No Format",
        "color": "#888888",
        "instruction": "",
        "description": "No output format specified — model decides",
    },
    {
        "name": "Natural Language",
        "color": "#1E88E5",
        "instruction": "\nDescribe the extracted information in a short paragraph.",
        "description": "Plain prose — human-readable but hard to parse",
    },
    {
        "name": "Bullet List",
        "color": "#FB8C00",
        "instruction": (
            "\nReturn as bullet points:\n"
            "- customer_name: ...\n"
            "- email: ...\n"
            "- issue_type: ...\n"
            "- urgency: ...\n"
            "- error_code: ..."
        ),
        "description": "Labelled bullets — parseable with regex",
    },
    {
        "name": "JSON (strict schema)",
        "color": "#43A047",
        "instruction": (
            '\nReturn ONLY valid JSON — no markdown fences, no commentary:\n'
            '{"customer_name": "...", "email": "...", "issue_type": "...", '
            '"urgency": "HIGH|MEDIUM|LOW", "error_code": "..." or null}'
        ),
        "description": "Strict JSON with schema — machine-parseable",
    },
    {
        "name": "Custom Schema",
        "color": "#8E24AA",
        "instruction": (
            "\nReturn in EXACTLY this format, one field per line:\n"
            "NAME: <value>\n"
            "EMAIL: <value>\n"
            "ISSUE: <value>\n"
            "URGENCY: <value>\n"
            "ERROR: <value or NONE>"
        ),
        "description": "Custom labelled schema — most explicit",
    },
]

RUNS_PER_FORMAT = 3

# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_json(text: str) -> dict | None:
    clean = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    start, end = clean.find("{"), clean.rfind("}") + 1
    if start < 0 or end <= start:
        return None
    try:
        return json.loads(clean[start:end])
    except json.JSONDecodeError:
        return None


def parse_bullets(text: str) -> dict:
    result = {}
    mapping = {
        "customer_name": r"customer[_\s]?name[:\s]+(.+)",
        "email":         r"email[:\s]+(.+)",
        "issue_type":    r"issue[_\s]?type[:\s]+(.+)",
        "urgency":       r"urgency[:\s]+(.+)",
        "error_code":    r"error[_\s]?code[:\s]+(.+)",
    }
    for field, pattern in mapping.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            result[field] = m.group(1).strip().strip("*_`")
    return result


def parse_custom(text: str) -> dict:
    mapping = {
        "customer_name": r"NAME[:\s]+(.+)",
        "email":         r"EMAIL[:\s]+(.+)",
        "issue_type":    r"ISSUE[:\s]+(.+)",
        "urgency":       r"URGENCY[:\s]+(.+)",
        "error_code":    r"ERROR[:\s]+(.+)",
    }
    result = {}
    for field, pattern in mapping.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            result[field] = None if val.upper() in ("NONE", "NULL", "N/A") else val
    return result


def parse_prose(text: str) -> dict:
    result = {}
    patterns = {
        "customer_name": r"(?:name|customer)[^\w]*([A-Z][a-z]+ [A-Z][a-z]+)",
        "email":         r"[\w.+-]+@[\w-]+\.\w+",
        "urgency":       r"\b(HIGH|MEDIUM|LOW)\b",
        "error_code":    r"\b([A-Z_]+_\d{3})\b",
    }
    for field, pattern in patterns.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            result[field] = m.group(0) if field == "email" else m.group(1)
    return result


def try_parse(fmt_name: str, text: str) -> tuple[dict, bool]:
    if fmt_name == "JSON (strict schema)":
        parsed = parse_json(text)
        if parsed and isinstance(parsed, dict):
            return parsed, True
        return {}, False
    elif fmt_name == "Bullet List":
        parsed = parse_bullets(text)
        return parsed, len(parsed) >= 4
    elif fmt_name == "Custom Schema":
        parsed = parse_custom(text)
        return parsed, len(parsed) >= 4
    else:
        parsed = parse_prose(text)
        return parsed, len(parsed) >= 2


# ── UI ────────────────────────────────────────────────────────────────────────

st.divider()

with st.expander("Source ticket (same for all formats)", expanded=False):
    st.code(SOURCE_TEXT.strip(), language="text")

with st.expander("Extraction task (same for all formats)", expanded=False):
    st.code(TASK_BASE, language="text")

st.subheader("Format instructions — what changes between columns")
fmt_cols = st.columns(len(FORMATS))
for col, fmt in zip(fmt_cols, FORMATS):
    with col:
        st.markdown(
            f"<div style='border-top:4px solid {fmt['color']};padding:6px 0 2px 0;'>"
            f"<strong style='color:{fmt['color']};font-size:0.9em;'>{fmt['name']}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(fmt["description"])
        if fmt["instruction"]:
            with st.expander("Format instruction"):
                st.code(fmt["instruction"].strip(), language="text")
        else:
            st.caption("*(no instruction appended)*")

st.divider()
run = st.button(
    f"▶  Run All {len(FORMATS)} Formats × {RUNS_PER_FORMAT} Runs Each "
    f"({len(FORMATS) * RUNS_PER_FORMAT} total API calls)",
    type="primary",
)

# ── Execution ─────────────────────────────────────────────────────────────────

if run:
    total_calls = len(FORMATS) * RUNS_PER_FORMAT
    progress = st.progress(0, text="Starting...")
    call_num = 0

    all_results: list[dict] = []

    for fmt in FORMATS:
        prompt = TASK_BASE + fmt["instruction"]
        fmt_runs = []

        for r in range(RUNS_PER_FORMAT):
            call_num += 1
            progress.progress(
                call_num / total_calls,
                text=f"Format: {fmt['name']} — Run {r+1}/{RUNS_PER_FORMAT}",
            )
            raw, usage = chat(
                system="You are a precise data extraction assistant.",
                user=prompt,
                max_tokens=250,
                temperature=0.7,
            )
            parsed, success = try_parse(fmt["name"], raw)
            fields_found = [f for f in EXPECTED_FIELDS if f in parsed and parsed[f]]
            fmt_runs.append({
                "run": r + 1,
                "raw": raw,
                "parsed": parsed,
                "success": success,
                "fields_found": fields_found,
            })

        reliability = sum(r["success"] for r in fmt_runs) / RUNS_PER_FORMAT
        avg_fields  = sum(len(r["fields_found"]) for r in fmt_runs) / RUNS_PER_FORMAT
        all_results.append({
            "fmt": fmt,
            "runs": fmt_runs,
            "reliability": reliability,
            "avg_fields": avg_fields,
        })

    progress.empty()

    # ── Results per format ────────────────────────────────────────────────────
    st.subheader("Results — all formats × all runs")
    res_cols = st.columns(len(FORMATS))

    for col, result in zip(res_cols, all_results):
        fmt = result["fmt"]
        with col:
            rel_pct = int(result["reliability"] * 100)
            bar_color = "#43A047" if rel_pct == 100 else ("#FB8C00" if rel_pct >= 67 else "#E53935")
            st.markdown(
                f"<div style='border-top:4px solid {fmt['color']};padding:6px 0 2px;'>"
                f"<strong style='color:{fmt['color']};'>{fmt['name']}</strong></div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='text-align:center;font-size:1.8em;font-weight:bold;"
                f"color:{bar_color};'>{rel_pct}%</div>"
                f"<div style='text-align:center;font-size:0.8em;color:#888;'>parse reliability</div>",
                unsafe_allow_html=True,
            )
            st.caption(f"Avg fields found: {result['avg_fields']:.1f} / {len(EXPECTED_FIELDS)}")

            for run_data in result["runs"]:
                icon = "✅" if run_data["success"] else "❌"
                fields_ok = len(run_data["fields_found"])
                with st.expander(f"Run {run_data['run']} {icon} — {fields_ok}/{len(EXPECTED_FIELDS)} fields"):
                    st.code(run_data["raw"], language="text")
                    if run_data["parsed"]:
                        st.json(run_data["parsed"])
                    missing = [f for f in EXPECTED_FIELDS if f not in run_data["fields_found"]]
                    if missing:
                        st.caption(f"Missing: {', '.join(missing)}")

    # ── Comparison chart ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("Reliability Comparison")

    import pandas as pd
    chart_df = pd.DataFrame({
        "Format": [r["fmt"]["name"] for r in all_results],
        "Parse Reliability (%)": [int(r["reliability"] * 100) for r in all_results],
        "Avg Fields Found": [round(r["avg_fields"], 1) for r in all_results],
    }).set_index("Format")

    st.bar_chart(chart_df["Parse Reliability (%)"], color="#1E88E5", y_label="Parse Success %")

    st.dataframe(chart_df, use_container_width=True)

    # ── Key observations ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("What to observe")
    st.markdown(
        """
- **No Format vs Custom Schema:** How much does an explicit format instruction improve reliability?
- **JSON vs Bullet List:** Which is more reliably parseable? Which has higher field completeness?
- **Run-to-run variation:** Do any formats give *inconsistent* results across the 3 runs? Why?
- **The production implication:** An agentic pipeline calls `json.loads()` after this step.
  A parse failure means the pipeline crashes — or needs a fallback/retry handler.
- **Format as a contract:** A strict format instruction turns the model's output into a
  machine-readable contract. The more explicit the contract, the more reliable the parse.
- **Try at temperature 0:** Rerun with `temperature=0.0` in `claude_client.py`.
  Do structured formats become perfectly reliable? Does No Format still vary?
"""
    )

# ── Reference ─────────────────────────────────────────────────────────────────

st.divider()
with st.expander("Format reliability in production agentic systems"):
    st.markdown(
        """
In a production pipeline, the output of one LLM call is the *input* to the next.
If the format is wrong, the pipeline fails. Three defensive strategies:

| Strategy | How it works | Trade-off |
|---|---|---|
| **Strict prompt** | Explicit schema + "no other text" | Fails silently if model ignores it |
| **Retry loop** | If parse fails, re-call with "you returned invalid format, try again" | Extra latency + cost |
| **Post-processing** | Code that strips markdown fences, normalises whitespace, etc. | Fragile to format drift |

The best strategy is strict prompt + retry loop with a max of 2 retries.
The `hour7_lab_refinement_loop.py` already shows how retry logic is structured.

**JSON best practices for agents:**
- Always include an example of the exact expected structure in the prompt
- Add "Return ONLY valid JSON — no markdown fences, no commentary"
- Use `response.model_dump()` with Pydantic if using structured outputs
"""
    )
