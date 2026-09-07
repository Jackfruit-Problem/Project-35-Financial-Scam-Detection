import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { api } from "../api";
import { useAuth } from "../auth";
import { Alert } from "../ui";

const DEMO = [
  ["victim@fsdiras.example.com", "Victim"],
  ["investigator@fsdiras.example.com", "Investigator"],
  ["officer@fsdiras.example.com", "Recovery officer"],
  ["admin@fsdiras.example.com", "Administrator"],
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "register") {
        await api.post("/auth/register", { full_name: fullName, email, password });
      }
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-shell">
      <span className="brand">
        FSDIRAS<span>.</span>
      </span>
      <p className="tagline">Scam detection, investigation and recovery assistance</p>

      <div className="card">
        <Alert kind="error">{error}</Alert>

        <form onSubmit={submit}>
          {mode === "register" && (
            <div className="field">
              <label htmlFor="name">Full name</label>
              <input
                id="name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                maxLength={60}
              />
            </div>
          )}

          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={mode === "register" ? 8 : undefined}
              autoComplete={mode === "register" ? "new-password" : "current-password"}
            />
            {mode === "register" && <p className="hint">At least 8 characters.</p>}
          </div>

          <button type="submit" disabled={busy} style={{ width: "100%" }}>
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        <p className="hint" style={{ marginTop: 14, textAlign: "center" }}>
          {mode === "login" ? "No account yet? " : "Already registered? "}
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              setMode(mode === "login" ? "register" : "login");
              setError("");
            }}
          >
            {mode === "login" ? "Create one" : "Sign in"}
          </a>
        </p>
      </div>

      <div className="card">
        <h2>Demo accounts</h2>
        <p className="demo-accounts" style={{ marginTop: 0 }}>
          Click one to fill the form. Password for all:{" "}
          <code>password123</code>
        </p>
        <table>
          <tbody>
            {DEMO.map(([demoEmail, role]) => (
              <tr key={demoEmail}>
                <td style={{ padding: "6px 0" }}>{role}</td>
                <td style={{ padding: "6px 0", textAlign: "right" }}>
                  <code
                    className="demo-accounts"
                    style={{ cursor: "pointer", color: "var(--accent)" }}
                    onClick={() => {
                      setMode("login");
                      setEmail(demoEmail);
                      setPassword("password123");
                    }}
                  >
                    use
                  </code>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
