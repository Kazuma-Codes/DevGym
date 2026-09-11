import json
import re

import requests

from config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT

from .prompts import (
    build_question_generation_messages,
    build_evaluation_messages,
    build_resume_parse_messages,
)


def ask_llm(messages):
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
        },
    }

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=OLLAMA_TIMEOUT,
    )

    response.raise_for_status()
    return response.json()["message"]["content"]


def extract_json_content(content: str) -> str:
    content = content.strip()

    content = re.sub(r"^`(?:json)?\s*", "", content, flags=re.MULTILINE)
    content = re.sub(r"\s*`$", "", content, flags=re.MULTILINE)

    start = content.find("{")
    end = content.rfind("}")

    if start != -1 and end != -1 and end > start:
        content = content[start:end + 1]

    return content.strip()


def parse_json_safely(content: str) -> dict:
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
        return {}
    except Exception:
        pass

    cleaned = extract_json_content(content)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
        return {}
    except Exception:
        return {}


def _as_list(value):
    if value is None:
        return []

    if isinstance(value, str):
        value = value.strip()
        return [value] if value else []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    return []


def _clamp_int(value, low=0, high=5):
    try:
        result = int(value)
    except Exception:
        result = low

    return max(low, min(high, result))


def normalize_generation(raw: dict) -> dict:
    question = str(raw.get("question", "")).strip()
    expected_concepts = _as_list(raw.get("expected_concepts", []))

    difficulty = str(raw.get("difficulty", "medium")).strip().lower()
    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "medium"

    return {
        "question": question,
        "expected_concepts": expected_concepts,
        "difficulty": difficulty,
        "scenario": str(raw.get("scenario", "")).strip(),
        "rationale": str(raw.get("rationale", "")).strip(),
    }


def normalize_evaluation(raw: dict, expected_concepts: list) -> dict:
    feedback = str(raw.get("feedback", "No feedback generated.")).strip()
    score = _clamp_int(raw.get("score", 0), 0, 5)

    missing_concepts = _as_list(raw.get("missing_concepts", []))
    knowledge_gaps = _as_list(raw.get("knowledge_gaps", []))

    follow_up_required = bool(raw.get("follow_up_required", False))
    follow_up_question = str(raw.get("follow_up_question", "")).strip()

    if follow_up_required and not follow_up_question:
        follow_up_required = False

    next_question = str(raw.get("next_question", "")).strip()

    adaptive_difficulty = str(raw.get("adaptive_difficulty", "same")).strip().lower()
    if adaptive_difficulty not in {"easier", "same", "harder"}:
        adaptive_difficulty = "same"

    analytics_raw = raw.get("analytics", {})
    if not isinstance(analytics_raw, dict):
        analytics_raw = {}

    analytics = {
        "communication_clarity": _clamp_int(analytics_raw.get("communication_clarity", 3), 0, 5),
        "structured_thinking": _clamp_int(analytics_raw.get("structured_thinking", 3), 0, 5),
        "depth_score": _clamp_int(analytics_raw.get("depth_score", 3), 0, 5),
        "tradeoffs_mentioned": _as_list(analytics_raw.get("tradeoffs_mentioned", [])),
        "edge_cases_caught": _as_list(analytics_raw.get("edge_cases_caught", [])),
    }

    star_score = raw.get("star_score")
    if star_score is not None:
        star_score = _clamp_int(star_score, 0, 5)

    graceful_exit_feedback = str(raw.get("graceful_exit_feedback", "")).strip()

    return {
        "feedback": feedback or "No feedback generated.",
        "score": score,
        "missing_concepts": missing_concepts,
        "follow_up_required": follow_up_required,
        "follow_up_question": follow_up_question,
        "next_question": next_question,
        "adaptive_difficulty": adaptive_difficulty,
        "analytics": analytics,
        "knowledge_gaps": knowledge_gaps,
        "star_score": star_score,
        "graceful_exit_feedback": graceful_exit_feedback,
    }


def fallback_evaluation(expected_concepts: list, transcript: str = "") -> dict:
    missing_concepts = []
    matched_concepts = []

    clean_transcript = transcript.lower() if transcript else ""

    for concept in expected_concepts or []:
        concept_str = str(concept).strip()
        if not concept_str:
            continue
        words = [w.lower() for w in re.findall(r"[a-z0-9]+", concept_str) if len(w) > 2]
        if words and any(w in clean_transcript for w in words):
            matched_concepts.append(concept_str)
        else:
            missing_concepts.append(concept_str)

    total = len(expected_concepts) if expected_concepts else 0
    if total > 0:
        coverage = len(matched_concepts) / total
        score = max(1, min(5, round(coverage * 5)))
    else:
        word_count = len(clean_transcript.split())
        score = 4 if word_count >= 30 else (3 if word_count >= 10 else 1)

    if total > 0:
        if matched_concepts and missing_concepts:
            feedback_msg = f"Good effort. You covered key concepts ({', '.join(matched_concepts)}), but missed: {', '.join(missing_concepts)}."
        elif matched_concepts:
            feedback_msg = f"Excellent answer! You covered all expected concepts: {', '.join(matched_concepts)}."
        else:
            feedback_msg = f"Your answer missed the core expected concepts: {', '.join(missing_concepts)}."
    else:
        feedback_msg = "Answer evaluated based on overall clarity and structure."

    follow_up_req = len(missing_concepts) > 0 and len(matched_concepts) > 0
    follow_up_q = f"Could you expand on how {missing_concepts[0]} works?" if follow_up_req else ""

    return {
        "feedback": feedback_msg,
        "score": score,
        "missing_concepts": missing_concepts,
        "follow_up_required": follow_up_req,
        "follow_up_question": follow_up_q,
        "next_question": "",
        "adaptive_difficulty": "same",
        "analytics": {
            "communication_clarity": min(5, max(1, round(len(clean_transcript.split()) / 15))) if clean_transcript else 1,
            "structured_thinking": score,
            "depth_score": score,
            "tradeoffs_mentioned": matched_concepts[:2],
            "edge_cases_caught": [],
        },
        "knowledge_gaps": missing_concepts,
        "star_score": score,
        "graceful_exit_feedback": "",
    }


def generate_question(mode: str, context: dict) -> dict:
    try:
        messages = build_question_generation_messages(mode, context)
        raw_content = ask_llm(messages)
        parsed = parse_json_safely(raw_content)

        if not parsed:
            return {}

        return normalize_generation(parsed)

    except Exception:
        return {}


def evaluate_answer(
    mode: str,
    context: dict,
    question: str,
    transcript: str,
    expected_concepts: list,
) -> dict:
    if not transcript or not transcript.strip():
        return {
            "feedback": "I did not hear any answer.",
            "score": 0,
            "missing_concepts": expected_concepts,
            "follow_up_required": False,
            "follow_up_question": "",
            "next_question": "",
            "adaptive_difficulty": "same",
            "analytics": {
                "communication_clarity": 0,
                "structured_thinking": 0,
                "depth_score": 0,
                "tradeoffs_mentioned": [],
                "edge_cases_caught": [],
            },
            "knowledge_gaps": expected_concepts,
            "star_score": None,
            "graceful_exit_feedback": "",
        }

    try:
        messages = build_evaluation_messages(
            mode=mode,
            context=context,
            question=question,
            transcript=transcript,
            expected_concepts=expected_concepts,
        )

        raw_content = ask_llm(messages)
        parsed = parse_json_safely(raw_content)

        if not parsed:
            return fallback_evaluation(expected_concepts, transcript)

        return normalize_evaluation(parsed, expected_concepts)

    except Exception:
        return fallback_evaluation(expected_concepts, transcript)


def normalize_resume(raw: dict, resume_text: str) -> dict:
    jd_match = raw.get("jd_match", {})
    if not isinstance(jd_match, dict):
        jd_match = {}

    return {
        "summary": str(raw.get("summary", "")).strip() or resume_text[:300],
        "skills": _as_list(raw.get("skills", [])),
        "projects": raw.get("projects", []) if isinstance(raw.get("projects"), list) else [],
        "experiences": raw.get("experiences", []) if isinstance(raw.get("experiences"), list) else [],
        "education": _as_list(raw.get("education", [])),
        "weak_spots": _as_list(raw.get("weak_spots", [])),
        "jd_match": {
            "matched_skills": _as_list(jd_match.get("matched_skills", [])),
            "missing_skills": _as_list(jd_match.get("missing_skills", [])),
            "suggested_focus": _as_list(jd_match.get("suggested_focus", [])),
        },
    }


def parse_resume(resume_text: str, job_description: str = "") -> dict:
    try:
        messages = build_resume_parse_messages(resume_text, job_description)
        raw_content = ask_llm(messages)
        parsed = parse_json_safely(raw_content)

        if not parsed:
            raise ValueError("Resume parsing returned invalid JSON.")

        return normalize_resume(parsed, resume_text)

    except Exception:
        return {
            "summary": resume_text[:300],
            "skills": [],
            "projects": [],
            "experiences": [],
            "education": [],
            "weak_spots": [],
            "jd_match": {
                "matched_skills": [],
                "missing_skills": [],
                "suggested_focus": [],
            },
        }