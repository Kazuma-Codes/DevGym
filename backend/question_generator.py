from backend.question_bank import bank
from llm.llm_service import generate_question


def _profile_context(session):
    profile = session.profile

    if not profile:
        return {}

    return {
        "resume": profile.resume_json or {},
        "job_description": profile.job_description or "",
        "project": profile.project_text or "",
        "focus_areas": profile.focus_areas or "",
    }


def build_context(session, previous_evaluation=None, previous_transcript=None):
    context = {
        "mode": session.mode,
        "subject": session.subject,
        "difficulty": session.difficulty,
        "question_number": session.question_number,
        "max_questions": session.max_questions,
        "used_question_ids": session.config.get("used_question_ids", []) if session.config else [],
        "profile": _profile_context(session),
    }

    if previous_evaluation:
        context["previous_evaluation"] = previous_evaluation

    if previous_transcript:
        context["previous_transcript"] = previous_transcript

    return context


def _mark_used(session, question):
    if not question:
        return

    if session.config is None:
        session.config = {}

    used = session.config.setdefault("used_question_ids", [])

    question_id = question.get("id")
    if question_id and question_id not in used:
        used.append(question_id)


def _fallback_question(session):
    fallbacks = {
        "SUBJECT": f"Explain an important {session.subject or 'technical'} concept and its practical trade-offs.",
        "RESUME": "Walk me through one experience from your resume and explain your exact contribution.",
        "PROJECT_GRILL": "Explain the architecture of your project and justify your technology choices.",
        "RAPID_FIRE": "Explain one core computer science concept clearly in under 30 seconds.",
        "BEHAVIORAL": "Tell me about a challenging situation and how you handled it using the STAR method.",
        "SYSTEM_DESIGN": "Describe how you would debug a production system experiencing high latency.",
        "JD_MATCH": "Based on the job description, explain how your background matches this role.",
    }

    return {
        "question": fallbacks.get(session.mode, "Tell me about your technical background."),
        "expected_concepts": [],
        "difficulty": session.difficulty,
        "scenario": "",
        "rationale": "Fallback question generated because LLM question generation failed.",
    }


def get_first_question(session):
    if session.config is None:
        session.config = {}

    used = session.config.get("used_question_ids", [])

    if session.mode == "SUBJECT":
        question = bank.random_question(
            session.subject,
            session.difficulty,
            used,
        )
        if question:
            _mark_used(session, question)
            question["difficulty"] = session.difficulty
            return question

    if session.mode == "RAPID_FIRE":
        question = bank.random_rapid_question(used)
        if question:
            _mark_used(session, question)
            question["difficulty"] = session.difficulty
            return question

    if session.mode == "BEHAVIORAL":
        question = bank.random_question(
            "behavioral",
            session.difficulty,
            used,
        )
        if question:
            _mark_used(session, question)
            question["difficulty"] = session.difficulty
            return question

    context = build_context(session)
    generated = generate_question(session.mode, context)

    if generated.get("question"):
        return generated

    return _fallback_question(session)


def get_next_question(session, previous_evaluation=None, previous_transcript=None):
    if session.question_number >= session.max_questions:
        return None

    if session.config is None:
        session.config = {}

    used = session.config.get("used_question_ids", [])

    adaptive = "same"
    if previous_evaluation:
        adaptive = previous_evaluation.get("adaptive_difficulty", "same")

    if session.mode == "SUBJECT" and adaptive == "same":
        question = bank.random_question(
            session.subject,
            session.difficulty,
            used,
        )
        if question:
            _mark_used(session, question)
            question["difficulty"] = session.difficulty
            return question

    if session.mode == "RAPID_FIRE":
        question = bank.random_rapid_question(used)
        if question:
            _mark_used(session, question)
            question["difficulty"] = session.difficulty
            return question

    context = build_context(
        session,
        previous_evaluation=previous_evaluation,
        previous_transcript=previous_transcript,
    )

    generated = generate_question(session.mode, context)

    if generated.get("question"):
        return generated

    return _fallback_question(session)