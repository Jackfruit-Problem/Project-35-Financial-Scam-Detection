import { useState } from "react";
import { Link } from "react-router-dom";

import { api, type Detection } from "../api";
import { useAuth } from "../auth";
import { Alert, RiskBadge } from "../ui";

const EXAMPLE =
  "URGENT: your account will be blocked immediately. Complete KYC now and share " +
  "your OTP and PAN card to avoid suspension. Verify at http://bit.ly/kyc-verify-now";

export default function CheckMessage() {
  const { user } = useAuth();
  const [text, setText] = useState("");
  const [result, setResult] = useState<Detection | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function check(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setResult(null);
    setBusy(true);
    try {
      setResult(await api.post<Detection>("/detection/analyse", { text }));
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <h1>Check a message</h1>
        <p>
          Paste a suspicious message, link or payment request. You will get a risk
          score and, more usefully, the reasons behind it.
        </p>
      </div>

      {!user && (
        <Alert kind="info">
          <Link to="/login">Sign in</Link> to check a message. You can still read the{" "}
          <Link to="/awareness">awareness guides</Link> without an account.
        </Alert>
      )}

      <div className="split">
        <div className="card">
          <form onSubmit={check}>
            <div className="field">
              <label htmlFor="text">Message, link or payment detail</label>
              <textarea
                id="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Paste the message here…"
                maxLength={5000}
                required
                disabled={!user}
              />
              <p className="hint">
                Not sure what to try?{" "}
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setText(EXAMPLE);
                  }}
                >
                  Use an example scam message
                </a>
              </p>
            </div>
            <button type="submit" disabled={busy || !user || !text.trim()}>
              {busy ? "Checking…" : "Check this message"}
            </button>
          </form>

          <Alert kind="error">{error}</Alert>
        </div>

        <div className="card">
          <h2>Result</h2>
          {!result ? (
            <p className="muted" style={{ margin: 0 }}>
              The score and the reasons behind it will appear here.
            </p>
          ) : (
            <>
              <div style={{ marginBottom: 14 }}>
                <RiskBadge band={result.risk_band} score={result.risk_score} />
                {result.matched_blacklist && (
                  <span className="badge high" style={{ marginLeft: 6 }}>
                    Known scammer
                  </span>
                )}
              </div>

              <strong style={{ fontSize: 13 }}>Why:</strong>
              <ul style={{ marginTop: 6, paddingLeft: 20 }}>
                {result.reasons.map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>

              <p className="hint" style={{ marginTop: 14 }}>
                {result.advisory_note}
              </p>
              <p className="hint">
                Scored in {result.latency_ms} ms by <code>{result.model_version}</code>.
              </p>

              {result.risk_band !== "low" && (
                <Link to="/report">
                  <button className="secondary small">Report this as a scam</button>
                </Link>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
