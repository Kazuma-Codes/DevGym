import { useState } from "react";
import { InterviewMode, SetupPayload } from "../types";

interface Props {
  onStart: (payload: SetupPayload) => void;
  loading: boolean;
  error: string;
  llmConfigured?: boolean;
  onViewHistory: () => void;
  onViewProgress: () => void;
}

const MODES: {
  id: InterviewMode;
  title: string;
  description: string;
}[] = [
  {
    id: "SUBJECT",
    title: "Subject Interview",
    description: "OOP, DSA, DBMS, OS, CN, Programming, CS Fundamentals",
  },
  {
    id: "RESUME",
    title: "Resume Deep-Dive",
    description: "AI questions from your resume",
  },
  {
    id: "PROJECT_GRILL",
    title: "Project Grill Mode",
    description: "Tough project architecture interrogation",
  },
  {
    id: "RAPID_FIRE",
    title: "Rapid Fire",
    description: "Fast CS fundamentals screening",
  },
  {
    id: "BEHAVIORAL",
    title: "Behavioral / STAR",
    description: "HR, gaps, and communication defense",
  },
  {
    id: "SYSTEM_DESIGN",
    title: "System Design",
    description: "Production debugging and scalability",
  },
  {
    id: "JD_MATCH",
    title: "JD Match",
    description: "Resume vs Job Description gap interview",
  },
];

export default function SetupScreen({
  onStart,
  loading,
  error,
  llmConfigured = true,
  onViewHistory,
  onViewProgress,
}: Props) {
  const [mode, setMode] = useState<InterviewMode>("SUBJECT");
  const [subject, setSubject] = useState("OOP");
  const [difficulty, setDifficulty] = useState("easy");

  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [projectText, setProjectText] = useState("");
  const [focusAreas, setFocusAreas] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);

  const [localError, setLocalError] = useState("");

  const needsResume = mode === "RESUME" || mode === "JD_MATCH";
  const needsJD = mode === "JD_MATCH";
  const needsProject = mode === "PROJECT_GRILL";
  const needsSubject = mode === "SUBJECT";

  const submit = () => {
    if (needsResume && !resumeText.trim() && !resumeFile) {
      setLocalError("Please provide resume text or upload a resume PDF.");
      return;
    }

    if (needsProject && !projectText.trim()) {
      setLocalError("Please provide your project description.");
      return;
    }

    setLocalError("");

    onStart({
      mode,
      subject,
      difficulty,
      resumeText,
      jobDescription,
      projectText,
      focusAreas,
      resumeFile,
    });
  };

  return (
    <div className="setup-screen">
      <div className="hero">
        <h1>AI Interview Platform</h1>
        <p>
          Practice CSE-core, behavioral, resume-based, and system design interviews
          with AI follow-ups and voice analytics.
        </p>
        <div className="button-row">
          <button className="ghost-btn" onClick={onViewHistory}>
            📂 Session History
          </button>
          <button className="ghost-btn" onClick={onViewProgress}>
            📈 Progress Dashboard
          </button>
        </div>
        {!llmConfigured && (
          <div className="info-box">
            No GROQ_API_KEY configured — you can still practice with the built-in
            CSE question bank and heuristic scoring.
          </div>
        )}
      </div>

      <section className="card">
        <h2>Select Interview Mode</h2>

        <div className="mode-grid">
          {MODES.map((item) => (
            <button
              key={item.id}
              className={mode === item.id ? "mode-card active" : "mode-card"}
              onClick={() => setMode(item.id)}
            >
              <strong>{item.title}</strong>
              <span>{item.description}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="card">
        <h2>Interview Settings</h2>

        {needsSubject && (
          <div className="form-row">
            <div className="form-group">
              <label>Subject</label>
              <select
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              >
                <option value="OOP">OOP</option>
                <option value="DSA">DSA</option>
                <option value="DBMS">DBMS</option>
                <option value="OS">OS</option>
                <option value="CN">CN</option>
                <option value="SYSTEM_DESIGN">System Design</option>
                <option value="PROGRAMMING">Programming (Python/Java/C++)</option>
                <option value="CS_FUNDAMENTALS">CS Fundamentals</option>
              </select>
            </div>
          </div>
        )}

        <div className="form-row">
          <div className="form-group">
            <label>Difficulty</label>
            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>
        </div>

        {needsResume && (
          <>
            <div className="form-group">
              <label>Resume PDF</label>
              <input
                type="file"
                accept=".pdf,.txt"
                onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
              />
            </div>

            <div className="form-group">
              <label>Resume Text</label>
              <textarea
                rows={8}
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste your resume here..."
              />
            </div>
          </>
        )}

        {needsJD && (
          <div className="form-group">
            <label>Job Description</label>
            <textarea
              rows={8}
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description..."
            />
          </div>
        )}

        {needsProject && (
          <div className="form-group">
            <label>Project Description</label>
            <textarea
              rows={8}
              value={projectText}
              onChange={(e) => setProjectText(e.target.value)}
              placeholder="Describe your project, architecture, tech stack, features..."
            />
          </div>
        )}

        {(needsResume || mode === "BEHAVIORAL") && (
          <div className="form-group">
            <label>Focus Areas / Concerns</label>
            <textarea
              rows={4}
              value={focusAreas}
              onChange={(e) => setFocusAreas(e.target.value)}
              placeholder="Example: Ask me about my internship, skip project X, help with 6-month gap..."
            />
          </div>
        )}

        {(localError || error) && (
          <div className="error-box">{localError || error}</div>
        )}

        <button className="primary-btn" onClick={submit} disabled={loading}>
          {loading ? "Preparing..." : "Start Interview"}
        </button>
      </section>
    </div>
  );
}