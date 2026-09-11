import { useState } from "react";

import SetupScreen from "./components/SetupScreen";
import InterviewScreen from "./components/InterviewScreen";
import AnalyticsScreen from "./components/AnalyticsScreen";

import { createProfile, startInterview } from "./api";

import {
  SetupPayload,
  StartResponse,
  SummaryResponse,
} from "./types";

type Phase = "setup" | "interview" | "analytics";

export default function App() {
  const [phase, setPhase] = useState<Phase>("setup");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [startData, setStartData] = useState<StartResponse | null>(null);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);

  const handleStart = async (payload: SetupPayload) => {
    setLoading(true);
    setError("");

    try {
      let profileId: string | undefined;

      const needsProfile =
        payload.mode === "RESUME" || payload.mode === "JD_MATCH";

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
    } catch (err: any) {
      setError(err?.message || "Failed to start interview.");
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

  return (
    <main className="app-shell">
      {phase === "setup" && (
        <SetupScreen
          onStart={handleStart}
          loading={loading}
          error={error}
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
        <AnalyticsScreen summary={summary} onRestart={handleRestart} />
      )}
    </main>
  );
}