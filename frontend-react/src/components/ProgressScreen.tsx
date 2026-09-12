import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { getProgress } from "../api";
import { ProgressResponse } from "../types";

interface Props {
  onBack: () => void;
}

export default function ProgressScreen({ onBack }: Props) {
  const [progress, setProgress] = useState<ProgressResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getProgress()
      .then(setProgress)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load progress."));
  }, []);

  const trend = progress?.trend ?? [];
  const shortDate = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString() : "");

  return (
    <div className="progress-screen">
      <div className="analytics-header">
        <div>
          <h1>Progress Dashboard</h1>
          <p>Your prep tracker: score trends, delivery metrics, and recurring weak CSE topics.</p>
        </div>
        <button className="ghost-btn" onClick={onBack}>
          Back to Setup
        </button>
      </div>

      {error && <div className="error-box">{error}</div>}
      {!progress && !error && <p>Loading progress...</p>}

      {progress && (
        <>
          <section className="metric-grid">
            <div className="metric-box">
              <h3>Sessions</h3>
              <p className="big-value">{progress.overall.total_sessions}</p>
            </div>
            <div className="metric-box">
              <h3>Sessions With Answers</h3>
              <p className="big-value">{progress.overall.sessions_with_answers}</p>
            </div>
            <div className="metric-box">
              <h3>Avg WPM</h3>
              <p className="big-value">{progress.overall.average_wpm}</p>
            </div>
            <div className="metric-box">
              <h3>Avg Fillers</h3>
              <p className="big-value">{progress.overall.average_filler_count}</p>
            </div>
          </section>

          <section className="analytics-grid">
            <div className="card">
              <h2>Score Trend</h2>
              {trend.length === 0 ? (
                <p>No answered sessions yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trend.map((point) => ({ ...point, date: shortDate(point.date) }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 5]} />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="average_score" stroke="#38bdf8" strokeWidth={3} name="Avg score" />
                    <Line
                      type="monotone"
                      dataKey="average_wpm"
                      stroke="#a78bfa"
                      strokeWidth={2}
                      name="Avg WPM"
                      yAxisId={0}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="card">
              <h2>Filler Word Trend</h2>
              {trend.length === 0 ? (
                <p>No answered sessions yet.</p>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trend.map((point) => ({ ...point, date: shortDate(point.date) }))}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="average_filler_count"
                      stroke="#f472b6"
                      strokeWidth={3}
                      name="Avg fillers per answer"
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </section>

          <section className="card">
            <h2>Recurring Weak Topics</h2>
            <p className="muted-text">
              Concepts you missed most often across sessions — review these first.
            </p>
            <div className="chip-row">
              {progress.weak_topics.length > 0 ? (
                progress.weak_topics.map((weak) => (
                  <span key={weak.topic} className="chip danger">
                    {weak.topic} ×{weak.times_missed}
                  </span>
                ))
              ) : (
                <span className="chip success">No recurring weak topics yet</span>
              )}
            </div>
          </section>

          <section className="card">
            <h2>Per-Subject Breakdown</h2>
            <div className="history-list">
              {progress.subjects.map((subject) => (
                <div key={subject.subject} className="history-item">
                  <div className="history-top">
                    <strong>{subject.subject}</strong>
                    <span>
                      {subject.sessions} session{subject.sessions === 1 ? "" : "s"}
                    </span>
                  </div>
                  <div className="history-meta">
                    <span>
                      Average score: <strong>{subject.average_score}/5</strong>
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
