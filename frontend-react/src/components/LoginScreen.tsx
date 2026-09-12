import { useState } from "react";
import { login, register } from "../api";

interface Props {
  onSuccess: (username: string) => void;
  singleUserUnavailable?: boolean;
  errorMessage?: string;
}

export default function LoginScreen({ onSuccess, singleUserUnavailable, errorMessage }: Props) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    if (!username.trim() || !password || busy) return;

    setBusy(true);
    setError("");

    try {
      if (mode === "login") {
        await login(username.trim(), password);
      } else {
        await register(username.trim(), password);
        await login(username.trim(), password);
      }
      onSuccess(username.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setBusy(false);
    }
  };

  if (singleUserUnavailable) {
    return (
      <div className="login-screen">
        <section className="card login-card">
          <h1>AI Interview Platform</h1>
          <p className="error-box">{errorMessage || "Server unavailable."}</p>
          <p>The backend could not be reached. Start it with: cd server && mvn spring-boot:run</p>
        </section>
      </div>
    );
  }

  return (
    <div className="login-screen">
      <section className="card login-card">
        <div className="hero">
          <h1>AI Interview Platform</h1>
          <p>Sign in to track your CSE interview practice across devices.</p>
        </div>

        <div className="tab-row" style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
          <button
            className={mode === "login" ? "badge" : "badge muted"}
            onClick={() => setMode("login")}
            style={{ cursor: "pointer" }}
          >
            Login
          </button>
          <button
            className={mode === "register" ? "badge" : "badge muted"}
            onClick={() => setMode("register")}
            style={{ cursor: "pointer" }}
          >
            Register
          </button>
        </div>

        <div className="form-group">
          <label>Username</label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="your-username"
            autoComplete="username"
          />
        </div>

        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                void submit();
              }
            }}
            placeholder="at least 8 characters"
            autoComplete={mode === "login" ? "current-password" : "new-password"}
          />
        </div>

        {(error || errorMessage) && <div className="error-box">{error || errorMessage}</div>}

        <button className="primary-btn" onClick={submit} disabled={busy || !username.trim() || !password}>
          {busy ? "Please wait..." : mode === "login" ? "Login" : "Create Account"}
        </button>
      </section>
    </div>
  );
}
