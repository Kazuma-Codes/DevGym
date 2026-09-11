# Subject & Resume-Based AI Voice Interview Bot

An interactive AI voice interview platform built with **Django**, **React (TypeScript + Vite)**, **faster-whisper**, **Ollama LLM**, and **Kokoro/Piper TTS**.

## Features

- **Subject-Based Interviews:** Technical practice for OOP, Data Structures, Algorithms, DBMS, System Design.
- **Resume & Custom Topic Generation:** AI-generated interview questions based on uploaded resumes or custom technical topics.
- **Multi-Turn AI Follow-up Questions:** Adaptive follow-up questions when expected concepts are missed.
- **Speech Analytics & Audio Feedback:** Evaluates words per minute (WPM), filler word frequency ("um", "like"), and concept coverage.
- **Voice Interactivity:** Voice recording with MediaRecorder, STT transcription, and TTS feedback synthesis.

## Project Structure

```text
Interview/
├── .env
├── .env.example
├── .gitignore
├── config.py
├── manage.py
├── requirements.txt
├── README.md
│
├── api/
│   ├── __init__.py
│   ├── apps.py
│   ├── admin.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   └── migrations/
│       └── __init__.py
│
├── backend/
│   ├── __init__.py
│   ├── question_bank.json
│   ├── question_bank.py
│   ├── question_generator.py
│   ├── audio_analytics.py
│   ├── resume_parser.py
│   ├── stt_service.py
│   └── tts_service.py
│
├── interview_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── llm/
│   ├── __init__.py
│   ├── prompts.py
│   └── llm_service.py
│
└── frontend-react/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api.ts
        ├── types.ts
        ├── styles.css
        ├── vite-env.d.ts
        ├── hooks/
        │   └── useRecorder.ts
        └── components/
            ├── SetupScreen.tsx
            ├── InterviewScreen.tsx
            └── AnalyticsScreen.tsx
```

## Running the Application

### 1. Backend (Django)
```bash
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver 8000
```

### 2. Frontend (React + Vite)
```bash
cd frontend-react
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.