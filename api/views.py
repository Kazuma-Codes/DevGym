import json
import os

from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import CandidateProfile, InterviewSession, InterviewTurn

from backend.stt_service import transcribe_bytes_detailed
from backend.audio_analytics import analyze_voice_delivery
from backend.resume_parser import extract_text_from_upload, parse_resume_text
from backend.question_generator import (
    get_first_question,
    get_next_question,
    build_context,
)
from backend.tts_service import (
    synthesize_text,
    synthesize_feedback_and_next_question,
    get_tts_status,
)

from llm.llm_service import evaluate_answer


VALID_MODES = {
    "SUBJECT",
    "RESUME",
    "PROJECT_GRILL",
    "RAPID_FIRE",
    "BEHAVIORAL",
    "SYSTEM_DESIGN",
    "JD_MATCH",
}


def _json_body(request):
    try:
        return json.loads(request.body)
    except Exception:
        return {}


def _adjust_difficulty(current: str, direction: str) -> str:
    current = current.lower()
    direction = direction.lower()

    if direction == "harder":
        if current == "easy":
            return "medium"
        if current == "medium":
            return "hard"
        return "hard"

    if direction == "easier":
        if current == "hard":
            return "medium"
        if current == "medium":
            return "easy"
        return "easy"

    return current


def _create_profile_from_data(data, resume_file=None):
    resume_text = str(data.get("resume_text", "")).strip()
    job_description = str(data.get("job_description", "")).strip()
    project_text = str(data.get("project_text", "")).strip()
    focus_areas = str(data.get("focus_areas", "")).strip()
    name = str(data.get("name", "")).strip()

    if resume_file:
        extracted = extract_text_from_upload(resume_file)
        if extracted:
            resume_text = extracted

    resume_json = {}
    if resume_text:
        resume_json = parse_resume_text(resume_text, job_description)

    return CandidateProfile.objects.create(
        name=name,
        resume_text=resume_text,
        resume_json=resume_json,
        job_description=job_description,
        project_text=project_text,
        focus_areas=focus_areas,
    )


def _build_summary(session: InterviewSession):
    turns = session.turns.order_by("created_at")

    timeline = []
    scores = []
    wpms = []
    filler_counts = []
    pauses = []

    knowledge_gaps = set()

    radar = {
        "communication_clarity": [],
        "structured_thinking": [],
        "depth_score": [],
    }

    for index, turn in enumerate(turns, start=1):
        voice = turn.voice or {}
        analytics = turn.analytics or {}

        scores.append(turn.score)

        wpm = voice.get("wpm", 0)
        filler_count = voice.get("filler_count", 0)
        max_pause = voice.get("max_pause_seconds", 0.0)

        wpms.append(wpm)
        filler_counts.append(filler_count)
        pauses.append(max_pause)

        for concept in turn.missing_concepts or []:
            if concept:
                knowledge_gaps.add(str(concept))

        for gap in analytics.get("knowledge_gaps", []) or []:
            if gap:
                knowledge_gaps.add(str(gap))

        for key in radar.keys():
            value = analytics.get(key)
            if isinstance(value, (int, float)):
                radar[key].append(float(value))

        timeline.append({
            "index": index,
            "question": turn.question_text[:160],
            "score": turn.score,
            "wpm": wpm,
            "filler_count": filler_count,
            "max_pause_seconds": max_pause,
            "created_at": turn.created_at.isoformat(),
        })

    def avg(values):
        if not values:
            return 0
        return round(sum(values) / len(values), 2)

    radar_avg = {
        key: avg(values)
        for key, values in radar.items()
    }

    recommendations = []

    if not timeline:
        recommendations.append("No interview turns were recorded.")

    if radar_avg["communication_clarity"] < 3:
        recommendations.append(
            "Practice explaining your thought process out loud in a structured way."
        )

    if radar_avg["structured_thinking"] < 3:
        recommendations.append(
            "Break answers into clear steps: problem understanding, approach, trade-offs, edge cases."
        )

    if radar_avg["depth_score"] < 3:
        recommendations.append(
            "Add more depth: mention alternatives, trade-offs, scalability, and failure cases."
        )

    if avg(filler_counts) > 3:
        recommendations.append(
            "Reduce filler words. Replace 'um' or 'like' with a short silent pause."
        )

    if avg(pauses) > 4:
        recommendations.append(
            "Use bridging phrases for long pauses, such as: 'Let me structure my answer...'"
        )

    if knowledge_gaps:
        gap_list = sorted(knowledge_gaps)[:10]
        recommendations.append(f"Review these concepts: {', '.join(gap_list)}")

    return {
        "session_id": str(session.id),
        "mode": session.mode,
        "subject": session.subject,
        "difficulty": session.difficulty,
        "status": session.status,
        "question_number": session.question_number,
        "max_questions": session.max_questions,
        "average_score": avg(scores),
        "average_wpm": avg(wpms),
        "average_filler_count": avg(filler_counts),
        "average_max_pause_seconds": avg(pauses),
        "radar": radar_avg,
        "timeline": timeline,
        "knowledge_gaps": sorted(knowledge_gaps),
        "recommendations": recommendations,
        "created_at": session.created_at.isoformat(),
        "completed_at": session.completed_at.isoformat() if session.completed_at else None,
    }


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_POST
def create_profile(request):
    if request.content_type and "multipart" in request.content_type:
        data = request.POST
        resume_file = request.FILES.get("resume_file")
    else:
        data = _json_body(request)
        resume_file = None

    try:
        profile = _create_profile_from_data(data, resume_file)
    except Exception as e:
        return JsonResponse({"detail": f"Could not create profile: {str(e)}"}, status=400)

    return JsonResponse({
        "profile_id": str(profile.id),
        "resume_json": profile.resume_json,
    })


@csrf_exempt
@require_POST
def start_interview(request):
    data = _json_body(request)

    mode = str(data.get("mode", "SUBJECT")).upper()
    subject = str(data.get("subject", "OOP")).upper()
    difficulty = str(data.get("difficulty", "easy")).lower()

    if mode not in VALID_MODES:
        return JsonResponse({"detail": "Invalid interview mode"}, status=400)

    if difficulty not in {"easy", "medium", "hard"}:
        difficulty = "easy"

    profile = None

    if data.get("profile_id"):
        try:
            profile = CandidateProfile.objects.get(id=data["profile_id"])
        except Exception:
            profile = None

    if not profile and (
        data.get("resume_text")
        or data.get("job_description")
        or data.get("project_text")
    ):
        profile = _create_profile_from_data(data)

    if mode in {"RESUME", "JD_MATCH"} and not profile:
        return JsonResponse({
            "detail": "Resume or JD mode requires a profile with resume content."
        }, status=400)

    if mode == "PROJECT_GRILL":
        has_project = (
            (profile and profile.project_text)
            or data.get("project_text")
        )
        if not has_project:
            return JsonResponse({
                "detail": "Project Grill mode requires project_text."
            }, status=400)

    if profile and mode in {"RESUME", "JD_MATCH"}:
        if not profile.resume_json and profile.resume_text:
            profile.resume_json = parse_resume_text(
                profile.resume_text,
                profile.job_description,
            )
            profile.save()

    max_questions = int(data.get("max_questions", 10 if mode == "RAPID_FIRE" else 5))
    time_limit_seconds = int(data.get("time_limit_seconds", 600 if mode == "RAPID_FIRE" else 0))

    session = InterviewSession.objects.create(
        profile=profile,
        mode=mode,
        subject=subject,
        difficulty=difficulty,
        max_questions=max_questions,
        time_limit_seconds=time_limit_seconds,
        config={
            "focus_areas": str(data.get("focus_areas", "")),
            "used_question_ids": [],
        },
    )

    question_data = get_first_question(session)

    session.current_question = question_data.get("question", "")
    session.current_expected_concepts = question_data.get("expected_concepts", [])

    if question_data.get("difficulty"):
        session.difficulty = question_data["difficulty"]

    session.question_number = 1
    session.config["scenario"] = question_data.get("scenario", "")
    session.config["rationale"] = question_data.get("rationale", "")
    session.save()

    return JsonResponse({
        "session_id": str(session.id),
        "mode": session.mode,
        "subject": session.subject,
        "difficulty": session.difficulty,
        "question": session.current_question,
        "expected_concepts": session.current_expected_concepts,
        "time_limit_seconds": session.time_limit_seconds,
        "max_questions": session.max_questions,
        "question_number": session.question_number,
    })


@csrf_exempt
@require_POST
def submit_answer(request, session_id):
    try:
        session = InterviewSession.objects.get(id=session_id)
    except InterviewSession.DoesNotExist:
        return JsonResponse({"detail": "Session not found"}, status=404)

    if session.status != "active":
        return JsonResponse({
            "detail": "Interview is already finished. Start a new session."
        }, status=400)

    audio_file = request.FILES.get("audio")
    text_answer = request.POST.get("text", "")

    question_text = request.POST.get("question") or session.current_question

    if audio_file:
        audio_bytes = audio_file.read()
        suffix = os.path.splitext(audio_file.name or "answer.webm")[1] or ".webm"

        initial_prompt = ", ".join(session.current_expected_concepts or [])

        try:
            transcript, segments, duration = transcribe_bytes_detailed(
                audio_bytes,
                suffix,
                initial_prompt,
            )
        except Exception:
            transcript, segments, duration = "", [], 0.0

        if not transcript.strip() and text_answer.strip():
            transcript = text_answer.strip()

    elif text_answer:
        transcript = text_answer.strip()
        segments = []
        duration = 0.0

    else:
        return JsonResponse({
            "detail": "No audio or text answer provided"
        }, status=400)

    if not transcript.strip():
        return JsonResponse({
            "transcript": "",
            "feedback": "I did not hear any answer. Please try again.",
            "score": 0,
            "missing_concepts": session.current_expected_concepts,
            "next_question": session.current_question,
            "finished": False,
            "voice": analyze_voice_delivery([], 0.0),
            "analytics": {},
            "knowledge_gaps": [],
            "graceful_exit_feedback": "",
            "star_score": None,
            "question_number": session.question_number,
            "max_questions": session.max_questions,
        })

    voice = analyze_voice_delivery(segments, duration)

    context = build_context(session)

    evaluation = evaluate_answer(
        mode=session.mode,
        context=context,
        question=question_text,
        transcript=transcript,
        expected_concepts=session.current_expected_concepts,
    )

    analytics_payload = {
        **(evaluation.get("analytics") or {}),
        "knowledge_gaps": evaluation.get("knowledge_gaps", []),
        "star_score": evaluation.get("star_score"),
        "graceful_exit_feedback": evaluation.get("graceful_exit_feedback", ""),
        "adaptive_difficulty": evaluation.get("adaptive_difficulty", "same"),
    }

    InterviewTurn.objects.create(
        session=session,
        question_text=question_text,
        answer_text=transcript,
        score=evaluation.get("score", 0),
        feedback=evaluation.get("feedback", ""),
        missing_concepts=evaluation.get("missing_concepts", []),
        voice=voice,
        analytics=analytics_payload,
        duration_seconds=duration,
    )

    adaptive = evaluation.get("adaptive_difficulty", "same")
    if adaptive in {"easier", "harder"}:
        session.difficulty = _adjust_difficulty(session.difficulty, adaptive)

    main_answer = not session.is_follow_up

    if main_answer:
        session.question_number += 1

    main_limit_reached = session.question_number >= session.max_questions

    if (
        main_answer
        and evaluation.get("follow_up_required", False)
        and evaluation.get("follow_up_question", "").strip()
    ):
        session.is_follow_up = True
        session.current_question = evaluation["follow_up_question"].strip()
        next_question = session.current_question
        finished = False

    else:
        session.is_follow_up = False

        if main_limit_reached:
            session.status = "completed"
            session.completed_at = timezone.now()
            session.current_question = ""
            next_question = "Interview completed."
            finished = True

        else:
            next_question_data = get_next_question(session, evaluation, transcript)

            if not next_question_data or not next_question_data.get("question"):
                session.status = "completed"
                session.completed_at = timezone.now()
                session.current_question = ""
                next_question = "Interview completed."
                finished = True

            else:
                session.current_question = next_question_data.get("question", "")
                session.current_expected_concepts = next_question_data.get(
                    "expected_concepts",
                    []
                )

                if next_question_data.get("difficulty"):
                    session.difficulty = next_question_data["difficulty"]

                session.config["scenario"] = next_question_data.get("scenario", "")
                session.config["rationale"] = next_question_data.get("rationale", "")

                next_question = session.current_question
                finished = False

    session.save()

    return JsonResponse({
        "transcript": transcript,
        "feedback": evaluation.get("feedback", ""),
        "score": evaluation.get("score", 0),
        "missing_concepts": evaluation.get("missing_concepts", []),
        "next_question": next_question,
        "finished": finished,
        "voice": voice,
        "analytics": evaluation.get("analytics", {}),
        "knowledge_gaps": evaluation.get("knowledge_gaps", []),
        "graceful_exit_feedback": evaluation.get("graceful_exit_feedback", ""),
        "star_score": evaluation.get("star_score"),
        "question_number": session.question_number,
        "max_questions": session.max_questions,
    })


@csrf_exempt
@require_POST
def finish_session(request, session_id):
    try:
        session = InterviewSession.objects.get(id=session_id)
    except InterviewSession.DoesNotExist:
        return JsonResponse({"detail": "Session not found"}, status=404)

    if session.status == "active":
        session.status = "completed"
        session.completed_at = timezone.now()
        session.save()

    return JsonResponse(_build_summary(session))


@require_GET
def session_summary(request, session_id):
    try:
        session = InterviewSession.objects.get(id=session_id)
    except InterviewSession.DoesNotExist:
        return JsonResponse({"detail": "Session not found"}, status=404)

    return JsonResponse(_build_summary(session))


@require_GET
def tts_status(request):
    return JsonResponse(get_tts_status())


@csrf_exempt
@require_POST
def text_to_speech(request):
    data = _json_body(request)
    text = str(data.get("text", ""))

    audio_bytes = synthesize_text(text)
    if not audio_bytes:
        return JsonResponse({
            "detail": "TTS engine is not configured or failed to synthesize audio."
        }, status=503)

    return HttpResponse(audio_bytes, content_type="audio/wav")


@csrf_exempt
@require_POST
def speak_answer_feedback(request):
    data = _json_body(request)

    feedback = str(data.get("feedback", ""))
    score = data.get("score")
    next_question = str(data.get("next_question", ""))

    audio_bytes = synthesize_feedback_and_next_question(
        feedback=feedback,
        score=score,
        next_question=next_question,
    )

    if not audio_bytes:
        return JsonResponse({
            "detail": "TTS engine is not configured or failed to synthesize audio."
        }, status=503)

    return HttpResponse(audio_bytes, content_type="audio/wav")