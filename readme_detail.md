# Subject-Based Interview Bot — OOP MVP

## Project Overview

This project is a **Subject-Based Interview Bot** that conducts technical interview practice using voice and a local LLM.

For the MVP, the system will support:

- **Subject:** OOP only
- **Difficulty levels:** Easy, Medium, Hard
- **Voice-based interview flow**
- **Speech-to-text for user answers**
- **Local LLM evaluation**
- **Text-to-speech for feedback and next question**

---

## MVP Goal

Build a working interview bot where:

1. User selects a subject and difficulty.
2. Bot asks an interview question.
3. Bot speaks the question using text-to-speech.
4. User answers verbally.
5. Speech-to-text converts the answer into text.
6. Local LLM evaluates the answer.
7. LLM returns feedback, score, missing concepts, and next question.
8. Bot speaks the feedback and asks the next question.

---

## Core Features

### Must-Have Features

- Subject dropdown
  - Only **OOP** for now
- Difficulty selector
  - Easy
  - Medium
  - Hard
- Start interview button
- Display current question
- Speak question using TTS
- Record user answer
- Convert speech to text
- Send transcript to local LLM
- Show feedback
- Show score
- Show missing concepts
- Speak feedback
- Ask next question

---

## Recommended Tech Stack

### Backend

- Python
- FastAPI

### Local LLM

Use one of the following:

- **Ollama** ← recommended for simplicity
- LM Studio local server
- llama.cpp server

### Speech-to-Text

### STT: faster-whisper

### TTS: Kokoro



## MVP Architecture

```text
Frontend
   |
   |  1. Select subject and difficulty
   |  2. Record answer
   |  3. Send audio to backend
   v
FastAPI Backend
   |
   |  1. Transcribe audio using Whisper
   |  2. Send question + transcript to local LLM
   |  3. Receive structured feedback
   v
Local LLM
   |
   | Returns JSON:
   | - feedback
   | - score
   | - missing concepts
   | - next question
   v
Backend sends response to frontend
   |
Frontend displays response and speaks it
```

---

## Session State

The application should maintain a session object.

Example:

```json
{
  "session_id": "abc123",
  "subject": "OOP",
  "difficulty": "medium",
  "current_question_id": "oop-medium-1",
  "history": [
    {
      "question": "What is polymorphism?",
      "answer": "Polymorphism means many forms...",
      "feedback": "Good answer, but missing compile-time vs runtime polymorphism.",
      "score": 3
    }
  ]
}
```

---

## API Design

### 1. Start Interview

```http
POST /start
```

Request:

```json
{
  "subject": "OOP",
  "difficulty": "easy"
}
```

Response:

```json
{
  "session_id": "abc123",
  "question": "What are the four main pillars of OOP?"
}
```

---

### 2. Submit Answer

```http
POST /answer/{session_id}
```

Request:

- Audio file

Response:

```json
{
  "transcript": "Encapsulation means hiding data inside a class.",
  "feedback": "Good explanation, but you should mention access modifiers.",
  "score": 3,
  "missing_concepts": [
    "Access modifiers",
    "Data hiding"
  ],
  "next_question": "What is the difference between abstraction and encapsulation?"
}
```

---

## Question Bank Design

For the MVP, use a fixed question bank instead of generating all questions with the LLM.

This is more reliable and easier to control.

---

## Example Question Bank Structure

```json
{
  "OOP": {
    "easy": [
      {
        "id": "oop-easy-1",
        "question": "What are the four main pillars of OOP?",
        "expected_concepts": [
          "Encapsulation",
          "Abstraction",
          "Inheritance",
          "Polymorphism"
        ]
      },
      {
        "id": "oop-easy-2",
        "question": "What is a class and what is an object?",
        "expected_concepts": [
          "Blueprint",
          "Instance"
        ]
      }
    ],
    "medium": [
      {
        "id": "oop-medium-1",
        "question": "What is the difference between method overloading and method overriding?",
        "expected_concepts": [
          "Compile-time polymorphism",
          "Runtime polymorphism",
          "Same method name",
          "Different signature",
          "Parent-child relationship"
        ]
      }
    ],
    "hard": [
      {
        "id": "oop-hard-1",
        "question": "How would you design a notification system using OOP principles?",
        "expected_concepts": [
          "Abstraction",
          "Interface",
          "Extensibility",
          "Loose coupling"
        ]
      }
    ]
  }
}
```

---

## OOP Question Examples

### Easy Questions

- What is a class?
- What is an object?
- What is encapsulation?
- What is inheritance?
- What is polymorphism?

### Medium Questions

- Difference between abstraction and encapsulation?
- Difference between method overloading and method overriding?
- What is composition in OOP?
- Why is multiple inheritance problematic?
- What is an abstract class?

### Hard Questions

- Design a parking lot using OOP.
- Design a payment system using OOP principles.
- How would you apply SOLID principles in an e-commerce system?
- When would you prefer composition over inheritance?
- How would you design a notification service with multiple channels?

---

## Local LLM Role

The local LLM should do three things:

1. Understand the transcribed answer.
2. Evaluate the answer against expected concepts.
3. Generate feedback and the next question.

For reliability, the LLM should return structured JSON.

---

## LLM Prompt Template

```text
You are a technical interviewer.

Subject: OOP
Difficulty: {difficulty}

Question:
{question}

Candidate answer:
{transcript}

Expected concepts:
{expected_concepts}

Return only valid JSON in this format:
{
  "feedback": "concise feedback",
  "score": 0-5,
  "missing_concepts": ["..."],
  "next_question": "next interview question"
}
```

---

## Recommended Local Models

If using Ollama:

### For 8GB RAM

- `qwen2.5:3b-instruct`
- `phi3:mini`
- `llama3.2:3b-instruct`

### For 16GB RAM

- `qwen2.5:7b-instruct`
- `llama3.1:8b-instruct`
- `mistral:7b-instruct`

Recommended starting model:

```bash
ollama pull qwen2.5:7b-instruct
```

If your system is slow, use:

```bash
ollama pull qwen2.5:3b-instruct
```

---

## Backend Setup

Create a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate
```

On Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install fastapi uvicorn python-multipart requests faster-whisper
```

Pull an Ollama model:

```bash
ollama pull qwen2.5:7b-instruct
```

---

## Minimal FastAPI Backend

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uuid
import json
import os
from faster_whisper import WhisperModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Whisper model
whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:7b-instruct"

# In-memory session storage
sessions = {}

# Sample question bank
question_bank = {
    "OOP": {
        "easy": [
            {
                "id": "oop-easy-1",
                "question": "What are the four main pillars of OOP?",
                "expected_concepts": [
                    "Encapsulation",
                    "Abstraction",
                    "Inheritance",
                    "Polymorphism"
                ]
            },
            {
                "id": "oop-easy-2",
                "question": "What is the difference between a class and an object?",
                "expected_concepts": [
                    "Blueprint",
                    "Instance"
                ]
            }
        ],
        "medium": [
            {
                "id": "oop-medium-1",
                "question": "What is the difference between method overloading and method overriding?",
                "expected_concepts": [
                    "Compile-time polymorphism",
                    "Runtime polymorphism",
                    "Same method name",
                    "Different signature",
                    "Parent-child relationship"
                ]
            }
        ],
        "hard": [
            {
                "id": "oop-hard-1",
                "question": "How would you design a notification system using OOP principles?",
                "expected_concepts": [
                    "Abstraction",
                    "Interface",
                    "Extensibility",
                    "Loose coupling"
                ]
            }
        ]
    }
}


class StartRequest(BaseModel):
    subject: str
    difficulty: str


def transcribe_audio(file_path: str):
    segments, _ = whisper_model.transcribe(file_path, language="en")
    text = " ".join(segment.text.strip() for segment in segments)
    return text.strip()


def ask_llm(messages):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": False,
            "format": "json"
        },
        timeout=180
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


def parse_json_safely(text):
    try:
        return json.loads(text)
    except Exception:
        return {
            "feedback": "Sorry, I could not parse the model output.",
            "score": 0,
            "missing_concepts": [],
            "next_question": "Please repeat your answer."
        }


@app.post("/start")
def start_interview(req: StartRequest):
    subject = req.subject.upper()
    difficulty = req.difficulty.lower()

    if subject not in question_bank:
        raise HTTPException(status_code=400, detail="Subject not supported yet")

    if difficulty not in question_bank[subject]:
        raise HTTPException(status_code=400, detail="Difficulty not supported")

    question_data = question_bank[subject][difficulty][0]

    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "subject": subject,
        "difficulty": difficulty,
        "question_index": 0,
        "history": []
    }

    return {
        "session_id": session_id,
        "question": question_data["question"]
    }


@app.post("/answer/{session_id}")
async def answer(session_id: str, audio: UploadFile = File(...)):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]
    subject = session["subject"]
    difficulty = session["difficulty"]
    index = session["question_index"]

    current_question = question_bank[subject][difficulty][index]

    temp_path = f"temp_{session_id}.webm"

    with open(temp_path, "wb") as f:
        f.write(await audio.read())

    transcript = transcribe_audio(temp_path)

    if os.path.exists(temp_path):
        os.remove(temp_path)

    if not transcript:
        return {
            "transcript": "",
            "feedback": "I did not hear any answer.",
            "score": 0,
            "missing_concepts": current_question["expected_concepts"],
            "next_question": current_question["question"]
        }

    prompt = f"""
You are a technical interviewer.

Subject: {subject}
Difficulty: {difficulty}

Question:
{current_question["question"]}

Candidate answer:
{transcript}

Expected concepts:
{json.dumps(current_question["expected_concepts"], indent=2)}

Return only valid JSON in this format:
{{
  "feedback": "concise feedback",
  "score": 0-5,
  "missing_concepts": ["..."],
  "next_question": "next interview question"
}}
""".strip()

    messages = [
        {
            "role": "system",
            "content": "You are a precise technical interview evaluator. Always return valid JSON only."
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    raw_response = ask_llm(messages)
    evaluation = parse_json_safely(raw_response)

    questions = question_bank[subject][difficulty]

    if index + 1 < len(questions):
        session["question_index"] += 1
        next_bank_question = questions[index + 1]["question"]
    else:
        next_bank_question = "That was the last question in this set."

    final_next_question = evaluation.get("next_question") or next_bank_question

    session["history"].append({
        "question": current_question["question"],
        "answer": transcript,
        "evaluation": evaluation
    })

    return {
        "transcript": transcript,
        "feedback": evaluation.get("feedback", ""),
        "score": evaluation.get("score", 0),
        "missing_concepts": evaluation.get("missing_concepts", []),
        "next_question": final_next_question
    }
```

Run backend:

```bash
uvicorn main:app --reload
```

---

## Minimal Frontend

```html
<!DOCTYPE html>
<html>
<head>
  <title>OOP Interview Bot</title>
</head>
<body>
  <h1>OOP Interview Bot</h1>

  <select id="subject">
    <option value="OOP">OOP</option>
  </select>

  <select id="difficulty">
    <option value="easy">Easy</option>
    <option value="medium">Medium</option>
    <option value="hard">Hard</option>
  </select>

  <button onclick="startInterview()">Start</button>

  <h3 id="question">Question will appear here</h3>

  <button id="recordBtn" onclick="toggleRecording()">Start Recording</button>

  <h4>Transcript</h4>
  <p id="transcript"></p>

  <h4>Feedback</h4>
  <p id="feedback"></p>

  <script>
    let sessionId = null;
    let mediaRecorder = null;
    let chunks = [];
    let recording = false;

    function speak(text) {
      const utterance = new SpeechSynthesisUtterance(text);
      speechSynthesis.speak(utterance);
    }

    async function startInterview() {
      const subject = document.getElementById("subject").value;
      const difficulty = document.getElementById("difficulty").value;

      const res = await fetch("http://localhost:8000/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ subject, difficulty })
      });

      const data = await res.json();

      sessionId = data.session_id;
      document.getElementById("question").innerText = data.question;

      speak(data.question);
    }

    async function toggleRecording() {
      if (!recording) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        mediaRecorder = new MediaRecorder(stream);
        chunks = [];

        mediaRecorder.ondataavailable = e => {
          chunks.push(e.data);
        };

        mediaRecorder.onstop = async () => {
          const blob = new Blob(chunks, { type: "audio/webm" });

          const formData = new FormData();
          formData.append("audio", blob);

          const res = await fetch(`http://localhost:8000/answer/${sessionId}`, {
            method: "POST",
            body: formData
          });

          const data = await res.json();

          document.getElementById("transcript").innerText = data.transcript;
          document.getElementById("feedback").innerText = data.feedback;

          const spoken = `${data.feedback}. Next question: ${data.next_question}`;

          document.getElementById("question").innerText = data.next_question;

          speak(spoken);
        };

        mediaRecorder.start();

        recording = true;
        document.getElementById("recordBtn").innerText = "Stop Recording";
      } else {
        mediaRecorder.stop();

        recording = false;
        document.getElementById("recordBtn").innerText = "Start Recording";
      }
    }
  </script>
</body>
</html>
```

---

## Session Flow

Use this flow:

```text
START
  |
  v
ASK_QUESTION
  |
  v
LISTENING
  |
  v
TRANSCRIBING
  |
  v
EVALUATING
  |
  v
FEEDBACK_AND_NEXT_QUESTION
  |
  v
ASK_QUESTION AGAIN
```

---

## Scoring System

Use a simple scoring rubric.

### Score 0

No relevant answer.

### Score 1

Very weak answer, mostly incorrect.

### Score 2

Some correct keywords but no clear understanding.

### Score 3

Basic correct answer but missing important details.

### Score 4

Good answer with minor gaps.

### Score 5

Strong, clear, and complete answer.

---

## Future Product Features

After the MVP, you can add:

- Session summary
- Score history
- Hint button
- Repeat question button
- Adaptive difficulty
- Transcript editing before submission
- Multiple subjects:
  - DSA
  - DBMS
  - System Design
- Performance analytics
- Follow-up questions
- Better local TTS using Piper

---

## Suggested Folder Structure

```text
interview-bot/
│
├── backend/
│   ├── main.py
│   ├── question_bank.json
│   ├── llm_service.py
│   ├── stt_service.py
│   ├── tts_service.py
│   └── session_manager.py
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
│
└── README.md
```

---

## Build Plan

### Phase 1: Core Logic Without Voice

Build:

- OOP question bank
- Difficulty selection
- Text answer input
- Local LLM feedback

Goal:

- Prove that evaluation works.

---

### Phase 2: Add Speech-to-Text

Build:

- Record answer
- Transcribe answer
- Send transcript to backend

Goal:

- Replace typed answer with spoken answer.

---

### Phase 3: Add Text-to-Speech

Build:

- Speak question
- Speak feedback
- Speak next question

Goal:

- Make the interview feel voice-based.

---

### Phase 4: Polish UI

Add:

- Better styling
- Score display
- Missing concepts display
- Session summary
- Restart interview

---

## Common Mistakes to Avoid

### Mistake 1: Letting the LLM generate all questions

Use a fixed question bank first.

### Mistake 2: Sending raw audio directly to the LLM

Convert speech to text first.

### Mistake 3: Expecting perfect JSON from the LLM

Always add fallback parsing.

### Mistake 4: Using a model that is too large

A slow model can ruin the user experience.

### Mistake 5: Trying to build all subjects at once

Start with OOP only.

---

## Recommended MVP Stack

For the simplest working version:

- Backend: FastAPI
- LLM: Ollama
- Model: `qwen2.5:3b-instruct` or `qwen2.5:7b-instruct`
- Speech-to-text: faster-whisper
- Text-to-speech: Browser SpeechSynthesis
- Frontend: HTML, JavaScript
- Question source: Local JSON file
- Subject: OOP only

---

## Final MVP Summary

The MVP is:

> An OOP-only interview bot that asks questions by voice, listens to the user's answer, transcribes it, evaluates it using a local LLM, and speaks feedback plus the next question.

This is a clean, focused, and impressive portfolio project.