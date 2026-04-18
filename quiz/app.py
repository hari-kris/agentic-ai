import streamlit as st
from questions import QUESTIONS

MODULE_META = {
    1: {
        "title": "Module 1: Agentic AI Foundations",
        "color": "#1E88E5",
        "icon": "🔵",
        "hours": "Hours 1–3",
        "topics": "Agentic Properties · Core Components · The Agentic Loop · Single vs Agentic",
    },
    2: {
        "title": "Module 2: Prompt Fundamentals",
        "color": "#FB8C00",
        "icon": "🟠",
        "hours": "Hours 4–7",
        "topics": "Prompt Framework · Prompt Types · Zero/Few-shot · Refinement Loops",
    },
    3: {
        "title": "Module 3: Agent Types and Components",
        "color": "#8E24AA",
        "icon": "🟣",
        "hours": "Hours 8–11",
        "topics": "Agent Components · 7 Agent Types · Multi-agent Teams",
    },
}

PASS_THRESHOLD = 7


def init_state():
    defaults = {
        "screen": "home",
        "selected_module": None,
        "questions": [],
        "current_q": 0,
        "answers": {},
        "submitted": False,
        "score": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def start_quiz(module: int):
    st.session_state.selected_module = module
    st.session_state.questions = [q for q in QUESTIONS if q["module"] == module]
    st.session_state.current_q = 0
    st.session_state.answers = {}
    st.session_state.submitted = False
    st.session_state.score = 0
    st.session_state.screen = "quiz"


def reset_to_home():
    for key in ["selected_module", "questions", "current_q", "answers", "submitted", "score"]:
        st.session_state.pop(key, None)
    st.session_state.screen = "home"


def render_home():
    st.title("Agentic AI — Student Quiz")
    st.markdown("Test your understanding of each module. Select a module below to begin.")
    st.markdown("---")

    cols = st.columns(3)
    for i, (mod_num, meta) in enumerate(MODULE_META.items()):
        with cols[i]:
            st.markdown(
                f"""<div style="border: 2px solid {meta['color']}; border-radius: 10px;
                padding: 20px; text-align: center; min-height: 180px;">
                <h3 style="color: {meta['color']};">Module {mod_num}</h3>
                <p style="font-size: 0.85rem; color: #555;">{meta['hours']}</p>
                <p style="font-size: 0.8rem;">{meta['topics']}</p>
                <p style="font-size: 0.85rem; color: #777;">10 questions</p>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown("")
            if st.button(f"Start Module {mod_num}", key=f"start_{mod_num}", use_container_width=True):
                start_quiz(mod_num)
                st.rerun()


def render_quiz():
    qs = st.session_state.questions
    idx = st.session_state.current_q
    total = len(qs)
    q = qs[idx]
    meta = MODULE_META[st.session_state.selected_module]

    # Sidebar
    with st.sidebar:
        st.markdown(f"### {meta['title']}")
        st.markdown(f"**Question {idx + 1} of {total}**")
        correct_so_far = sum(
            1 for i, ans_q in enumerate(qs[:idx])
            if st.session_state.answers.get(ans_q["id"]) == ans_q["correct"]
        )
        st.markdown(f"Score so far: **{correct_so_far} / {idx}**")
        st.progress((idx + 1) / total)
        st.markdown("---")
        if st.button("Quit Quiz", use_container_width=True):
            reset_to_home()
            st.rerun()

    # Header
    st.markdown(
        f'<span style="background:{meta["color"]}; color:white; padding:4px 12px; '
        f'border-radius:12px; font-size:0.8rem;">{meta["title"]} · {q["topic"]}</span>',
        unsafe_allow_html=True,
    )
    st.markdown(f"### Q{idx + 1}. {q['question']}")
    st.progress((idx + 1) / total, text=f"Question {idx + 1} / {total}")

    option_key = f"radio_{q['id']}"
    chosen = st.radio(
        "Select your answer:",
        q["options"],
        key=option_key,
        disabled=st.session_state.submitted,
        index=None,
    )

    if not st.session_state.submitted:
        if st.button("Submit Answer", type="primary", disabled=chosen is None):
            letter = chosen[0] if chosen else None
            st.session_state.answers[q["id"]] = letter
            st.session_state.submitted = True
            if letter == q["correct"]:
                st.session_state.score += 1
            st.rerun()
        if chosen is None:
            st.caption("Select an option before submitting.")
    else:
        letter = st.session_state.answers.get(q["id"])
        is_correct = letter == q["correct"]

        if is_correct:
            st.success("Correct!")
        else:
            correct_text = next(o for o in q["options"] if o.startswith(q["correct"]))
            st.error(f"Incorrect. The correct answer is: **{correct_text}**")

        st.info(f"**Explanation:** {q['explanation']}")

        if idx + 1 < total:
            if st.button("Next Question →", type="primary"):
                st.session_state.current_q += 1
                st.session_state.submitted = False
                st.rerun()
        else:
            if st.button("View Results →", type="primary"):
                st.session_state.screen = "results"
                st.rerun()


def render_results():
    qs = st.session_state.questions
    answers = st.session_state.answers
    score = st.session_state.score
    total = len(qs)
    mod = st.session_state.selected_module
    meta = MODULE_META[mod]
    passed = score >= PASS_THRESHOLD
    pct = int(score / total * 100)

    st.title("Quiz Results")

    badge_color = "#43A047" if passed else "#E53935"
    badge_text = "PASS" if passed else "NEEDS REVIEW"
    st.markdown(
        f"""<div style="text-align:center; padding:30px; border:2px solid {badge_color};
        border-radius:12px; margin-bottom:20px;">
        <h1 style="color:{meta['color']}; margin:0;">{score} / {total}</h1>
        <p style="font-size:1.2rem; color:#555; margin:4px 0;">{pct}%</p>
        <span style="background:{badge_color}; color:white; padding:6px 20px;
        border-radius:20px; font-size:1rem; font-weight:bold;">{badge_text}</span>
        <p style="margin-top:12px; color:#777;">Pass mark: {PASS_THRESHOLD} / {total}</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Per-topic breakdown
    st.markdown("### Breakdown by Topic")
    topic_results: dict[str, dict] = {}
    for q in qs:
        t = q["topic"]
        if t not in topic_results:
            topic_results[t] = {"correct": 0, "total": 0}
        topic_results[t]["total"] += 1
        if answers.get(q["id"]) == q["correct"]:
            topic_results[t]["correct"] += 1

    for topic, res in topic_results.items():
        c, tot = res["correct"], res["total"]
        bar_pct = c / tot
        bar_color = "#43A047" if c == tot else ("#FB8C00" if c >= tot / 2 else "#E53935")
        st.markdown(
            f"""<div style="margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between;">
            <span>{topic}</span><span style="font-weight:bold;">{c}/{tot}</span></div>
            <div style="background:#eee; border-radius:4px; height:8px;">
            <div style="width:{bar_pct*100:.0f}%; background:{bar_color};
            border-radius:4px; height:8px;"></div></div></div>""",
            unsafe_allow_html=True,
        )

    # Wrong answers review
    wrong = [q for q in qs if answers.get(q["id"]) != q["correct"]]
    if wrong:
        st.markdown("### Review Incorrect Answers")
        for q in wrong:
            your_letter = answers.get(q["id"], "—")
            your_ans = next((o for o in q["options"] if o.startswith(your_letter)), "No answer")
            correct_ans = next(o for o in q["options"] if o.startswith(q["correct"]))
            with st.expander(f"Q: {q['question'][:80]}..."):
                st.markdown(f"**Your answer:** {your_ans}")
                st.markdown(f"**Correct answer:** {correct_ans}")
                st.info(f"**Explanation:** {q['explanation']}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Retake This Module", use_container_width=True):
            start_quiz(mod)
            st.rerun()
    with col2:
        if st.button("Try Another Module", use_container_width=True):
            reset_to_home()
            st.rerun()


def main():
    st.set_page_config(
        page_title="Agentic AI Quiz",
        page_icon="🤖",
        layout="centered",
    )
    init_state()

    screen = st.session_state.screen
    if screen == "home":
        render_home()
    elif screen == "quiz":
        render_quiz()
    elif screen == "results":
        render_results()


if __name__ == "__main__":
    main()
