import json


MODE_PERSONAS = {
    "SUBJECT": (
        "You are a rigorous technical interviewer for core CS subjects. "
        "You test concepts clearly and adapt difficulty based on the candidate's answer."
    ),
    "RESUME": (
        "You are a deep-dive resume interviewer. "
        "You ask specific questions about the candidate's actual resume experiences, "
        "projects, technologies, metrics, and ownership."
    ),
    "PROJECT_GRILL": (
        "You are a tough staff engineer interrogating a candidate about their project. "
        "You test whether they truly built it by asking about architecture, trade-offs, "
        "authentication, databases, failure handling, scaling, and implementation details."
    ),
    "RAPID_FIRE": (
        "You are a fast-paced campus placement screener. "
        "You ask short, sharp core CS questions that can be answered in under 45 seconds."
    ),
    "BEHAVIORAL": (
        "You are a behavioral interviewer using the STAR method. "
        "You evaluate Situation, Task, Action, and Result. "
        "You also help candidates frame employment gaps or career breaks gracefully."
    ),
    "SYSTEM_DESIGN": (
        "You are a principal engineer conducting system design and production debugging interviews. "
        "You focus on scalability, reliability, observability, trade-offs, and incident response."
    ),
    "JD_MATCH": (
        "You are a hiring manager comparing a candidate's resume against a job description. "
        "You identify missing skills and ask targeted questions to probe those gaps."
    ),
}


def build_question_generation_messages(mode: str, context: dict):
    mode = str(mode or "SUBJECT").upper()
    persona = MODE_PERSONAS.get(mode, MODE_PERSONAS["SUBJECT"])

    system_prompt = (
        persona +
        " Always return only valid JSON. "
        "Do not include markdown, comments, or explanations."
    )

    user_prompt = f"""
Generate the next interview question.

Mode:
{mode}

Context:
{json.dumps(context, indent=2, default=str)}

Rules:
- The question must match the mode and difficulty.
- Adapt difficulty based on previous performance if previous_evaluation exists.
- For RAPID_FIRE, the question must be answerable in under 45 seconds.
- For RESUME and JD_MATCH, use resume and job description context deeply.
- For PROJECT_GRILL, ask about actual implementation decisions and trade-offs.
- For BEHAVIORAL, encourage STAR-structured answers.
- For SYSTEM_DESIGN, prefer real-world production scenarios.

Return only valid JSON in exactly this format:
{{
  "question": "the interview question",
  "expected_concepts": ["concept 1", "concept 2"],
  "difficulty": "easy|medium|hard",
  "scenario": "optional scenario context",
  "rationale": "why this question was chosen"
}}
""".strip()

    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]


def build_evaluation_messages(
    mode: str,
    context: dict,
    question: str,
    transcript: str,
    expected_concepts: list,
):
    mode = str(mode or "SUBJECT").upper()
    persona = MODE_PERSONAS.get(mode, MODE_PERSONAS["SUBJECT"])

    system_prompt = (
        persona +
        " You are also an evaluation engine. "
        "Always return only valid JSON. "
        "Do not include markdown, comments, or explanations."
    )

    user_prompt = f"""
Evaluate the candidate's answer.

Mode:
{mode}

Context:
{json.dumps(context, indent=2, default=str)}

Question:
{question}

Candidate transcript:
{transcript}

Expected concepts:
{json.dumps(expected_concepts, indent=2)}

Evaluation rules:
- Score is an integer from 0 to 5.
- Evaluate technical accuracy and communication.
- If the answer is shallow, ask a follow-up question.
- If the candidate mentions a technology, probe why they chose it.
- If the candidate says "I don't know", evaluate graceful failure.
- For graceful failure, reward acknowledging the gap, connecting adjacent knowledge, and suggesting how to learn or debug.
- Provide analytics for communication clarity, structured thinking, and depth.
- Identify concrete knowledge gaps.
- If mode is BEHAVIORAL, provide a STAR score from 0 to 5.
- adaptive_difficulty must be one of: easier, same, harder.

Return only valid JSON in exactly this format:
{{
  "feedback": "concise actionable feedback",
  "score": 0,
  "missing_concepts": ["missing concept 1", "missing concept 2"],
  "follow_up_required": false,
  "follow_up_question": "targeted follow-up question",
  "next_question": "optional next question",
  "adaptive_difficulty": "same",
  "analytics": {{
    "communication_clarity": 0,
    "structured_thinking": 0,
    "depth_score": 0,
    "tradeoffs_mentioned": ["tradeoff 1"],
    "edge_cases_caught": ["edge case 1"]
  }},
  "knowledge_gaps": ["gap 1", "gap 2"],
  "star_score": 0,
  "graceful_exit_feedback": "feedback on how well they handled not knowing"
}}
""".strip()

    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]


def build_resume_parse_messages(resume_text: str, job_description: str):
    system_prompt = (
        "You are a resume parsing and recruiting intelligence system. "
        "Always return only valid JSON. "
        "Do not include markdown, comments, or explanations."
    )

    user_prompt = f"""
Parse the resume into structured JSON.

Resume:
{resume_text}

Job Description:
{job_description}

Rules:
- Extract skills, projects, experiences, education, and weak spots.
- If a job description is provided, compare the resume against it.
- Identify missing skills and suggested focus areas.
- Keep output concise and factual.

Return only valid JSON in exactly this format:
{{
  "summary": "short candidate summary",
  "skills": ["skill 1", "skill 2"],
  "projects": [
    {{
      "name": "project name",
      "description": "short description",
      "technologies": ["tech 1", "tech 2"]
    }}
  ],
  "experiences": [
    {{
      "title": "role",
      "organization": "company or institution",
      "summary": "short summary",
      "technologies": ["tech 1"]
    }}
  ],
  "education": ["education item"],
  "weak_spots": ["weak spot 1"],
  "jd_match": {{
    "matched_skills": ["matched skill"],
    "missing_skills": ["missing skill"],
    "suggested_focus": ["focus area"]
  }}
}}
""".strip()

    return [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": user_prompt,
        },
    ]