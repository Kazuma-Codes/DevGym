import { useState } from "react";
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

import { createShare, reportUrl } from "../api";
import { SummaryResponse } from "../types";

interface Props {
  summary: SummaryResponse;
  onRestart: () => void;
  onOpenHistory?: () => void;
  readOnly?: boolean;
}

export default function AnalyticsScreen({ summary, onRestart, onOpenHistory, readOnly }: Props) {
  const [shareMessage, setShareMessage] = useState("");

  const radarData = [
    {
      metric: "Clarity",
      value: summary.radar.communication_clarity,
    },
    {
      metric: "Structure",
      value: summary.radar.structured_thinking,
    },
    {
      metric: "Depth",
      value: summary.radar.depth_score,
    },
  ];

  const handleShare = async () => {
    setShareMessage("");
    try {
      const share = await createShare(summary.session_id);
      const url = `${window.location.origin}${share.share_url}`;
      await navigator.clipboard?.writeText(url).catch(() => undefined);
      setShareMessage(`Share link copied: ${url}`);
    } catch (err) {
      setShareMessage(err instanceof Error ? err.message : "Could not create share link.");
    }
  };

  return (
    <div className="analytics-screen">
      <div className="analytics-header">
        <div>
          <h1>{readOnly ? "Shared Interview Report" : "Post-Interview Analytics"}</h1>
          <p>
            Mode: {summary.mode.replace("_", " ")} | Subject: {summary.subject} |
            Difficulty: {summary.difficulty}
          </p>
        </div>

        {!readOnly && (
          <div className="button-row">
            <a className="ghost-btn" href={reportUrl(summary.session_id)} download>
              ⬇ Download PDF
            </a>
            <button className="ghost-btn" onClick={handleShare}>
              🔗 Share
            </button>
            {onOpenHistory && (
              <button className="ghost-btn" onClick={onOpenHistory}>
                History
              </button>
            )}
            <button className="primary-btn" onClick={onRestart}>
              Start New Interview
            </button>
          </div>
        )}
      </div>

      {shareMessage && <div className="info-box">{shareMessage}</div>}

      <section className="metric-grid">
        <div className="metric-box">
          <h3>Average Score</h3>
          <p className="big-value">{summary.average_score}/5</p>
        </div>

        <div className="metric-box">
          <h3>Average WPM</h3>
          <p className="big-value">{summary.average_wpm}</p>
        </div>

        <div className="metric-box">
          <h3>Average Fillers</h3>
          <p className="big-value">{summary.average_filler_count}</p>
        </div>

        <div className="metric-box">
          <h3>Avg Max Pause</h3>
          <p className="big-value">{summary.average_max_pause_seconds}s</p>
        </div>
      </section>

      <section className="analytics-grid">
        <div className="card">
          <h2>Communication Radar</h2>

          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="metric" />
              <Radar
                name="Performance"
                dataKey="value"
                stroke="#38bdf8"
                fill="#38bdf8"
                fillOpacity={0.4}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h2>Timeline Replay</h2>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={summary.timeline}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="index" />
              <YAxis />
              <Tooltip />

              <Line
                type="monotone"
                dataKey="score"
                stroke="#38bdf8"
                strokeWidth={3}
                name="Score"
              />

              <Line
                type="monotone"
                dataKey="wpm"
                stroke="#a78bfa"
                strokeWidth={2}
                name="WPM"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="card">
        <h2>Knowledge Gaps</h2>

        <div className="chip-row">
          {summary.knowledge_gaps.length > 0 ? (
            summary.knowledge_gaps.map((gap, index) => (
              <span key={index} className="chip danger">
                {gap}
              </span>
            ))
          ) : (
            <span className="chip success">No major knowledge gaps detected</span>
          )}
        </div>
      </section>

      <section className="card">
        <h2>Recommendations</h2>

        <ul className="recommendation-list">
          {summary.recommendations.length > 0 ? (
            summary.recommendations.map((recommendation, index) => (
              <li key={index}>{recommendation}</li>
            ))
          ) : (
            <li>No recommendations generated.</li>
          )}
        </ul>
      </section>

      <section className="card">
        <h2>Question Timeline</h2>

        <div className="timeline-list">
          {summary.timeline.map((turn) => (
            <div key={turn.index} className="timeline-item">
              <div className="timeline-top">
                <strong>Question {turn.index}</strong>
                <span>
                  Score: {turn.score}/5
                  {turn.overtime && <span className="chip danger"> answered late</span>}
                </span>
              </div>

              <p>{turn.question}</p>

              <div className="timeline-meta">
                <span>WPM: {turn.wpm}</span>
                <span>Fillers: {turn.filler_count}</span>
                <span>Max Pause: {turn.max_pause_seconds}s</span>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
