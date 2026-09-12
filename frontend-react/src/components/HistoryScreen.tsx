import { useEffect, useState } from "react";
import { getSessions } from "../api";
import { SessionListItem } from "../types";

interface Props {
  onOpenSession: (sessionId: string) => void;
  onBack: () => void;
}

function formatDate(iso: string | null): string {
  if (!iso) return "In progress";
  return new Date(iso).toLocaleString();
}

export default function HistoryScreen({ onOpenSession, onBack }: Props) {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getSessions()
      .then(setSessions)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load session history."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="history-screen">
      <div className="analytics-header">
        <div>
          <h1>Session History</h1>
          <p>Your past interviews. Click one to reopen its full analytics report.</p>
        </div>
        <button className="ghost-btn" onClick={onBack}>
          Back to Setup
        </button>
      </div>

      {loading && <p>Loading sessions...</p>}
      {error && <div className="error-box">{error}</div>}

      {!loading && !error && sessions.length === 0 && (
        <section className="card">
          <p>No sessions yet. Start your first interview from the New Interview tab.</p>
        </section>
      )}

      <div className="history-list">
        {sessions.map((session) => (
          <button
            key={session.session_id}
            className="card history-item"
            onClick={() => onOpenSession(session.session_id)}
          >
            <div className="history-top">
              <strong>
                {session.mode.replace("_", " ")} — {session.subject}
              </strong>
              <span className={session.status === "completed" ? "chip success" : "chip warning"}>
                {session.status}
              </span>
            </div>

            <div className="history-meta">
              <span>
                Score: <strong>{session.average_score}/5</strong>
              </span>
              <span>
                Questions: {session.question_number}/{session.max_questions}
              </span>
              <span>{formatDate(session.completed_at || session.created_at)}</span>
              {session.has_overtime && <span className="chip danger">answered late</span>}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
