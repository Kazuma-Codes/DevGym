import { useEffect, useRef, useState } from "react";

import { useRecorder } from "../hooks/useRecorder";
import { submitAnswer, finishSession, getSummary } from "../api";

import {
  AnswerResponse,
  InterviewMode,
  SummaryResponse,
} from "../types";

interface Props {
  sessionId: string;
  initialQuestion: string;
  mode: InterviewMode;
  subject: string;
  difficulty: string;
  timeLimit: number;
  maxQuestions: number;
  initialQuestionNumber?: number;
  onViewAnalytics: (summary: SummaryResponse) => void;
}

function formatTime(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export default function InterviewScreen({
  sessionId,
  initialQuestion,
  mode,
  subject,
  difficulty,
  timeLimit,
  maxQuestions,
  initialQuestionNumber = 1,
  onViewAnalytics,
}: Props) {
  const { recording, error: micError, start, stop } = useRecorder();

  const [question, setQuestion] = useState(initialQuestion);
  const [response, setResponse] = useState<AnswerResponse | null>(null);
  const [processing, setProcessing] = useState(false);
  const [finished, setFinished] = useState(false);
  const [questionNumber, setQuestionNumber] = useState(initialQuestionNumber);
  const [textAnswer, setTextAnswer] = useState("");
  const [inputMode, setInputMode] = useState<"voice" | "text">("voice");
  const [error, setError] = useState("");
  const [timeLeft, setTimeLeft] = useState(timeLimit);

  const finishingRef = useRef(false);

  const finishInterview = async () => {
    if (finishingRef.current) return;

    finishingRef.current = true;

    try {
      await finishSession(sessionId);
      const summary = await getSummary(sessionId);
      onViewAnalytics(summary);
    } catch (err: any) {
      setError(err?.message || "Could not finish interview.");
    } finally {
      finishingRef.current = false;
    }
  };

  useEffect(() => {
    if (timeLimit <= 0 || finished) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => Math.max(0, prev - 1));
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLimit, finished]);

  useEffect(() => {
    if (timeLimit > 0 && timeLeft === 0 && !finished) {
      finishInterview();
    }
  }, [timeLeft, finished]);

  const speakQuestion = async () => {
    if (!question) return;

    try {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: question }),
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audio.play();
        return;
      }
    } catch {
      // Fallback to browser SpeechSynthesis below
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(question);
    utterance.rate = 1;
    utterance.pitch = 1;
    window.speechSynthesis.speak(utterance);
  };

  const toggleRecording = async () => {
    if (processing || finished) return;

    if (!recording) {
      setError("");
      await start();
      return;
    }

    setProcessing(true);
    setError("");

    const blob = await stop();

    if (!blob) {
      setProcessing(false);
      setError("No audio recorded.");
      return;
    }

    const form = new FormData();
    form.append("audio", blob, "answer.webm");
    form.append("question", question);

    try {
      const res = await submitAnswer(sessionId, form);

      setResponse(res);
      setQuestion(res.next_question);
      setFinished(res.finished);
      setQuestionNumber(res.question_number);

      if (res.finished) {
        window.speechSynthesis.cancel();
      }
    } catch (err: any) {
      setError(err?.message || "Failed to submit answer.");
    } finally {
      setProcessing(false);
    }
  };

  const handleTextSubmit = async () => {
    if (!textAnswer.trim() || processing || finished) return;

    setProcessing(true);
    setError("");

    const form = new FormData();
    form.append("text", textAnswer.trim());
    form.append("question", question);

    try {
      const res = await submitAnswer(sessionId, form);

      setResponse(res);
      setQuestion(res.next_question);
      setFinished(res.finished);
      setQuestionNumber(res.question_number);
      setTextAnswer("");

      if (res.finished) {
        window.speechSynthesis.cancel();
      }
    } catch (err: any) {
      setError(err?.message || "Failed to submit answer.");
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="interview-screen">
      <div className="interview-header">
        <div className="badge-row">
          <span className="badge">{mode.replace("_", " ")}</span>
          <span className="badge muted">{subject}</span>
          <span className="badge muted">{difficulty}</span>
        </div>

        <div className="status-row">
          <span>
            Question {questionNumber}/{maxQuestions}
          </span>

          {timeLimit > 0 && <span>⏱ {formatTime(timeLeft)}</span>}
        </div>
      </div>

      <section className="card question-card">
        <h2>Current Question</h2>
        <p className="question-text">{question}</p>

        <button className="ghost-btn" onClick={speakQuestion}>
          🔊 Speak question
        </button>
      </section>

      <section className="card controls-card">
        <div className="tab-row" style={{ marginBottom: "1rem", display: "flex", gap: "0.5rem" }}>
          <button
            className={inputMode === "voice" ? "badge" : "badge muted"}
            onClick={() => setInputMode("voice")}
            style={{ cursor: "pointer" }}
          >
            🎙 Voice Answer
          </button>
          <button
            className={inputMode === "text" ? "badge" : "badge muted"}
            onClick={() => setInputMode("text")}
            style={{ cursor: "pointer" }}
          >
            ✍️ Text Answer
          </button>
        </div>

        {inputMode === "voice" ? (
          <button
            className={recording ? "record-btn recording" : "record-btn"}
            onClick={toggleRecording}
            disabled={processing || finished}
          >
            {processing
              ? "Processing..."
              : recording
              ? "Stop Recording"
              : "Start Recording"}
          </button>
        ) : (
          <div className="text-input-group" style={{ display: "flex", flexDirection: "column", gap: "0.5rem", width: "100%" }}>
            <textarea
              rows={4}
              value={textAnswer}
              onChange={(e) => setTextAnswer(e.target.value)}
              placeholder="Type your answer here..."
              disabled={processing || finished}
              style={{ width: "100%", padding: "0.75rem", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.15)", background: "#1e293b", color: "#fff" }}
            />
            <button
              className="primary-btn"
              onClick={handleTextSubmit}
              disabled={processing || finished || !textAnswer.trim()}
            >
              {processing ? "Submitting..." : "Submit Answer"}
            </button>
          </div>
        )}

        <div className="status-text">
          {micError && <p className="error-box">{micError}</p>}
          {error && <p className="error-box">{error}</p>}

          {!processing && !finished && !recording && inputMode === "voice" && (
            <p>Press Start Recording to answer.</p>
          )}

          {recording && <p>Listening... Speak clearly.</p>}

          {processing && <p>Transcribing and evaluating...</p>}

          {finished && <p>Interview completed.</p>}
        </div>

        {finished ? (
          <button className="primary-btn" onClick={finishInterview}>
            View Analytics
          </button>
        ) : (
          <button className="danger-btn" onClick={finishInterview}>
            Finish Interview
          </button>
        )}
      </section>

      {response && (
        <section className="card result-card">
          <h2>Feedback</h2>

          <div className="metric-grid">
            <div className="metric-box">
              <h3>Score</h3>
              <p className="big-value">{response.score}/5</p>
            </div>

            <div className="metric-box">
              <h3>WPM</h3>
              <p className="big-value">{response.voice?.wpm ?? 0}</p>
            </div>

            <div className="metric-box">
              <h3>Filler Words</h3>
              <p className="big-value">{response.voice?.filler_count ?? 0}</p>
            </div>

            <div className="metric-box">
              <h3>Max Pause</h3>
              <p className="big-value">
                {response.voice?.max_pause_seconds ?? 0}s
              </p>
            </div>
          </div>

          <div className="result-block">
            <h3>Transcript</h3>
            <p>{response.transcript || "(No speech detected)"}</p>
          </div>

          <div className="result-block">
            <h3>AI Feedback</h3>
            <p>{response.feedback}</p>
          </div>

          {response.graceful_exit_feedback && (
            <div className="result-block">
              <h3>Graceful Exit Coaching</h3>
              <p>{response.graceful_exit_feedback}</p>
            </div>
          )}

          {response.voice?.feedback && (
            <div className="result-block">
              <h3>Voice Coach</h3>
              <p>{response.voice.feedback}</p>
            </div>
          )}

          <div className="result-block">
            <h3>Missing Concepts</h3>
            <div className="chip-row">
              {response.missing_concepts.length > 0 ? (
                response.missing_concepts.map((concept, index) => (
                  <span key={index} className="chip warning">
                    {concept}
                  </span>
                ))
              ) : (
                <span className="chip success">None detected</span>
              )}
            </div>
          </div>

          <div className="result-block">
            <h3>Knowledge Gaps</h3>
            <div className="chip-row">
              {response.knowledge_gaps.length > 0 ? (
                response.knowledge_gaps.map((gap, index) => (
                  <span key={index} className="chip danger">
                    {gap}
                  </span>
                ))
              ) : (
                <span className="chip success">No major gaps detected</span>
              )}
            </div>
          </div>

          {typeof response.star_score === "number" && (
            <div className="result-block">
              <h3>STAR Score</h3>
              <p>{response.star_score}/5</p>
            </div>
          )}
        </section>
      )}
    </div>
  );
}