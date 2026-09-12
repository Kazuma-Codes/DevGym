import { useCallback, useEffect, useState } from "react";

import SetupScreen from "./components/SetupScreen";
import InterviewScreen from "./components/InterviewScreen";
import AnalyticsScreen from "./components/AnalyticsScreen";
import HistoryScreen from "./components/HistoryScreen";
import ProgressScreen from "./components/ProgressScreen";
import LoginScreen from "./components/LoginScreen";

import { createProfile, getSharedSummary, getConfig, me, startInterview } from "./api";

import {
  ConfigResponse,
  SetupPayload,
  StartResponse,
  SummaryResponse,
} from "./types";

type Phase = "setup" | "interview" | "analytics" | "history" | "progress" | "login";

/** Read a /share/<token> URL if the app was opened from a shared report link. */
function shareTokenFromPath(): string | null {
  const match = window.location.pathname.match(/^\/share\/([a-zA-Z0-9]+)$/);
  return match ? match[1] : null;
}

export default function App() {
  const [phase, setPhase] = useState<Phase>("setup");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [username, setUsername] = useState<string | null>(null);

  const [startData, setStartData] = useState<StartResponse | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);

  const [shareToken] = useState<string | null>(() => shareTokenFromPath());
  const [sharedSummary, setSharedSummary] = useState<SummaryResponse | null>(null);
  const [shareError, setShareError] = useState("");

  const openSession = useCallback(async (sessionId: string) => {
    setLoading(true);
    setError("");
    try {
      const { getSummary } = await import("./api");
      const fetched = await getSummary(sessionId);
      setSummary(fetched);
      setPhase("analytics");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not open session.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Shared reports (public, read-only) bypass the whole app shell.
  useEffect(() => {
    if (!shareToken) return;
    getSharedSummary(shareToken)
      .then(setSharedSummary)
      .catch((err) => setShareError(err instanceof Error ? err.message : "Shared report not found."));
  }, [shareToken]);

  // Load server config and enforce login when single-user mode is off.
  useEffect(() => {
    if (shareToken) return;
    getConfig()
      .then(async (cfg) => {
        setConfig(cfg);
        if (!cfg.single_user_mode) {
          const current = await me();
          if (current.authenticated && current.username) {
            setUsername(current.username);
          } else {
            setPhase("login");
          }
        }
      })
      .catch(() => {
        setError("Could not reach the server. Is the backend running on port 8080?");
      });
  }, [shareToken]);

  const handleStart = async (payload: SetupPayload) => {
    setLoading(true);
    setError("");

    try {
      let profileId: string | undefined;

      const needsProfile = payload.mode === "RESUME" || payload.mode === "JD_MATCH";

      if (needsProfile && (payload.resumeFile || payload.resumeText)) {
        const form = new FormData();

        if (payload.resumeFile) {
          form.append("resume_file", payload.resumeFile);
        }

        if (payload.resumeText) {
          form.append("resume_text", payload.resumeText);
        }

        if (payload.jobDescription) {
          form.append("job_description", payload.jobDescription);
        }

        if (payload.focusAreas) {
          form.append("focus_areas", payload.focusAreas);
        }

        const profile = await createProfile(form);
        profileId = profile.profile_id;
      }

      const startPayload: Record<string, unknown> = {
        mode: payload.mode,
        subject: payload.subject,
        difficulty: payload.difficulty,
        project_text: payload.projectText,
        focus_areas: payload.focusAreas,
      };

      if (profileId) {
        startPayload.profile_id = profileId;
      }

      const started = await startInterview(startPayload);

      setStartData(started);
      setPhase("interview");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start interview.");
    } finally {
      setLoading(false);
    }
  };

  const handleViewAnalytics = (summaryData: SummaryResponse) => {
    setSummary(summaryData);
    setPhase("analytics");
  };

  const handleRestart = () => {
    setPhase("setup");
    setStartData(null);
    setSummary(null);
    setError("");
  };

  const handleLogin = (name: string) => {
    setUsername(name);
    setPhase("setup");
  };

  const handleLogout = async () => {
    try {
      const { logout } = await import("./api");
      await logout();
    } finally {
      setUsername(null);
      setStartData(null);
      setSummary(null);
      setPhase("login");
    }
  };

  if (shareToken) {
    return (
      <main className="app-shell">
        {sharedSummary ? (
          <AnalyticsScreen summary={sharedSummary} onRestart={handleRestart} readOnly />
        ) : (
          <div className="card" style={{ padding: "2rem", textAlign: "center" }}>
            <h1>Shared Report</h1>
            <p>{shareError || "Loading shared report..."}</p>
          </div>
        )}
      </main>
    );
  }

  const navItems: { id: Phase; label: string }[] = [
    { id: "setup", label: "New Interview" },
    { id: "history", label: "History" },
    { id: "progress", label: "Progress" },
  ];

  return (
    <main className="app-shell">
      <nav className="app-nav">
        <span className="app-brand">🎤 AI Interview</span>
        <div className="app-nav-links">
          {username && <span className="badge muted">{username}</span>}
          {!config?.single_user_mode && username && (
            <button className="ghost-btn" onClick={handleLogout}>
              Logout
            </button>
          )}
          {username === null && config?.single_user_mode && (
            <button className="ghost-btn" onClick={() => setPhase("history")}>
              History
            </button>
          )}
        </div>
      </nav>

      {phase !== "login" && phase !== "interview" && (
        <div className="app-nav-tabs">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={phase === item.id ? "nav-tab active" : "nav-tab"}
              onClick={() => {
                setError("");
                if (item.id === "setup") {
                  handleRestart();
                } else {
                  setPhase(item.id);
                }
              }}
            >
              {item.label}
            </button>
          ))}
        </div>
      )}

      {error && phase !== "setup" && <div className="error-box global-error">{error}</div>}

      {phase === "login" && (
        <LoginScreen
          onSuccess={handleLogin}
          singleUserUnavailable={config === null && Boolean(error)}
          errorMessage={error}
        />
      )}

      {phase === "setup" && (
        <SetupScreen
          onStart={handleStart}
          loading={loading}
          error={error}
          llmConfigured={config?.llm_configured ?? true}
          onViewHistory={() => setPhase("history")}
          onViewProgress={() => setPhase("progress")}
        />
      )}

      {phase === "interview" && startData && (
        <InterviewScreen
          sessionId={startData.session_id}
          initialQuestion={startData.question}
          mode={startData.mode}
          subject={startData.subject}
          difficulty={startData.difficulty}
          timeLimit={startData.time_limit_seconds}
          maxQuestions={startData.max_questions}
          initialQuestionNumber={startData.question_number || 1}
          onViewAnalytics={handleViewAnalytics}
        />
      )}

      {phase === "analytics" && summary && (
        <AnalyticsScreen
          summary={summary}
          onRestart={handleRestart}
          onOpenHistory={() => setPhase("history")}
        />
      )}

      {phase === "history" && (
        <HistoryScreen
          onOpenSession={openSession}
          onBack={() => setPhase("setup")}
        />
      )}

      {phase === "progress" && <ProgressScreen onBack={() => setPhase("setup")} />}
    </main>
  );
}
