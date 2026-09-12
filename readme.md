# AI Interview Platform (CSE Mock Interviews)

An AI-powered mock interview platform focused on **Computer Science & Engineering (CSE)** subjects — OOP, DSA, DBMS, OS, Networks, System Design, Programming languages, and CS Fundamentals — plus resume deep-dives, project grilling, rapid-fire screening, and behavioral/STAR practice.

**Stack:** Spring Boot 3 (Java 21, Maven) · React 18 + TypeScript + Vite · SQLite · Groq API (free tier: LLM + Whisper STT) · Browser SpeechSynthesis TTS · Docker + GitHub Actions CI.

## Features

- **7 interview modes** — Subject (CSE topics), Resume Deep-Dive, Project Grill, Rapid Fire, Behavioral/STAR, System Design, JD Match.
- **110-question curated CSE bank** with expected concepts per question; bank-first selection keeps most turns off the LLM (free-tier friendly), and the app **works fully without an API key** (heuristic fallback scoring).
- **Adaptive interviews** — LLM follow-ups when answers are shallow, difficulty up/down per answer, no repeated questions per session.
- **Voice in, voice out** — answers recorded in the browser, transcribed via Groq's `whisper-large-v3-turbo`; questions spoken via the browser's built-in SpeechSynthesis (auto-speak toggle).
- **Voice delivery analytics** — WPM, filler words, long pauses, with actionable coaching per answer.
- **Server-side time enforcement** — sessions with time limits are marked "answered late" (overtime) and factored into evaluation.
- **Analytics** — per-session radar (clarity/structure/depth), timeline replay, knowledge gaps, recommendations.
- **Progress dashboard** — cross-session score/WPM/filler trends, recurring weak CSE topics, per-subject breakdown.
- **Reports** — downloadable PDF per session and unguessable read-only share links.
- **Multi-user ready** — register/login with per-user data isolation (`SINGLE_USER_MODE=1` keeps a local demo login-free).
- **Production hardening** — CSRF protection, upload validation (size caps, extension allowlists, PDF magic bytes), per-IP rate limiting on LLM-heavy endpoints, uniform JSON error contract, structured logging.

## Architecture

```
Browser (React SPA, browser TTS)
   │  /api  (JSON + CSRF cookie)
   ▼
Spring Boot (port 8080)
 ├── web/        controllers + uniform { error } handling
 ├── service/    interview flow, Groq LLM/STT clients, question bank,
 │               audio analytics, summary/progress, PDF reports
 ├── security/   session auth, CSRF, rate limiting
 └── repository/ Spring Data JPA → SQLite (single file, volume-friendly)
         │
         ▼
   Groq API (OpenAI-compatible):  llama-3.3-70b-versatile (chat)
                                  whisper-large-v3-turbo (STT)
```

No GPU, no local model files, no Ollama install. To switch providers (e.g. xAI Grok), change `LLM_BASE_URL`, `LLM_MODEL`, and the API key in `.env` — no code changes.

## Setup

1. **Get a free Groq API key** at [console.groq.com](https://console.groq.com) (no credit card; ~30 req/min, ~1k req/day) and put it in `.env`:
   ```
   GROQ_API_KEY=gsk_...
   ```
2. **Backend** (JDK 21+ and Maven required):
   ```
   cd server
   mvn spring-boot:run
   ```
3. **Frontend** (Node 18+):
   ```
   cd frontend-react
   npm install
   npm run dev
   ```
   Open http://localhost:5173 — `/api` is proxied to the backend on port 8080.

### Run tests

```
cd server && mvn test          # 32 hermetic tests, fully offline (Groq mocked)
cd frontend-react && npm run lint && npm run build
```

## Docker (production-style run)

```
docker compose up --build
```
Serves the full app (SPA + API) on **http://localhost:8080** with SQLite persisted to a named volume. Set `SINGLE_USER_MODE=0` in `.env` before deploying publicly so login is required.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | *(empty)* | Free key for LLM + STT. App stays usable without it (degraded mode). |
| `LLM_BASE_URL` | `https://api.groq.com/openai/v1` | OpenAI-compatible base URL. |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Chat model. |
| `STT_MODEL` | `whisper-large-v3-turbo` | Transcription model. |
| `LLM_TIMEOUT` | `60` | Seconds per LLM call (retry once on 429/5xx). |
| `SQLITE_PATH` | `./interview.db` | Database file (mounted at `/data` in Docker). |
| `SINGLE_USER_MODE` | `1` | `1` = local demo, no login. `0` = require accounts + ownership. |
| `ALLOWED_ORIGINS` | *(empty)* | Comma-separated CORS origins if hosting the SPA separately. |
| `RATE_LIMIT_*_PER_HOUR` | `10/20/120` | Per-IP hourly caps for profile/start/answer. |

## Deployment notes

- **Any VPS:** `docker compose up -d` behind your reverse proxy (Caddy/Nginx) with TLS — voice recording requires HTTPS outside localhost.
- **Render/Railway:** use the Dockerfile; free tiers have ephemeral disks, so attach a persistent disk (or accept demo data resetting) for SQLite.
- Health probe: `GET /api/health` reports db status, `llm_configured`, and active engines.

## Roadmap

Next rounds, in rough priority order:

1. **Email verification + password reset** (django-allauth equivalent via Spring Mail).
2. **Postgres** when concurrency grows; **async queue** (RabbitMQ/Redis) for report generation.
3. **Coding rounds** — in-browser editor with execution via Piston/Judge0 for DSA mode.
4. **Company-specific packs** (TCS NQT / Amazon-style) and topic-wise drills.
5. **Spaced-repetition weak-topic practice** + streaks/gamification.
6. **More domains** — ML/AI, Cloud/DevOps, ECE — the bank + prompt pattern generalizes.
7. **Regional language support**, PWA/mobile app, recruiter-facing shared reports.
8. **Billing** (Stripe) for free-tier quota protection at scale.

`docs/legacy-spec.md` preserves the original pre-Spring design spec for reference.
