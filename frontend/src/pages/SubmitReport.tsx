import { useState } from "react";
import { Link } from "react-router-dom";

import { api, type Case, type Detection, type Report } from "../api";
import { useAuth } from "../auth";
import { Alert, CATEGORIES, RiskBadge, StatusBadge, rupees } from "../ui";

interface Result {
  report: Report;
  case: Case;
  detection: Detection;
}

/** SRS 3.1 asks for a guided multi-step wizard with inline validation. Three
 *  steps: who you are, what happened, then confirm. Splitting it matters --
 *  people filing these are often distressed, and one long form loses them. */
const STEPS = ["Your details", "What happened", "Review"];

export default function SubmitReport() {
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    reporter_name: user?.full_name ?? "",
    reporter_contact: "",
    category: "upi_fraud",
    description: "",
    amount_involved: "",
  });
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function set(field: keyof typeof form, value: string) {
    setForm({ ...form, [field]: value });
  }

  const contactValid = /^[0-9]{10}$|^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.reporter_contact);
  const stepValid = [
    form.reporter_name.trim().length > 1 && contactValid,
    form.description.trim().length > 10,
    true,
  ][step];

  async function submit() {
    setError("");
    setBusy(true);
    try {
      setResult(
        await api.post<Result>("/reports", {
          ...form,
          amount_involved: form.amount_involved ? Number(form.amount_involved) : null,
        }),
      );
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    return (
      <>
        <div className="page-head">
          <h1>Report received</h1>
          <p>Keep your case reference — you will need it to track progress.</p>
        </div>

        <Alert kind="success">
          Your report has been recorded and a case has been opened.
        </Alert>

        <div className="card">
          <table>
            <tbody>
              <tr>
                <td className="muted">Report reference</td>
                <td className="mono">{result.report.report_ref}</td>
              </tr>
              <tr>
                <td className="muted">Case reference</td>
                <td className="mono">
                  <Link to={`/cases/${result.case.case_ref}`}>{result.case.case_ref}</Link>
                </td>
              </tr>
              <tr>
                <td className="muted">Case status</td>
                <td>
                  <StatusBadge status={result.case.status} />
                </td>
              </tr>
              <tr>
                <td className="muted">Risk assessment</td>
                <td>
                  <RiskBadge
                    band={result.report.risk_band}
                    score={result.report.risk_score}
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2>Why it was scored this way</h2>
          <ul style={{ marginTop: 0, paddingLeft: 20 }}>
            {result.detection.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <p className="hint">{result.detection.advisory_note}</p>
        </div>

        <div className="actions">
          <Link to="/my-reports">
            <button>View my reports</button>
          </Link>
          <Link to={`/cases/${result.case.case_ref}`}>
            <button className="secondary">Open the case and add evidence</button>
          </Link>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="page-head">
        <h1>Report a scam</h1>
        <p>
          Step {step + 1} of {STEPS.length} — {STEPS[step]}
        </p>
      </div>

      <Alert kind="error">{error}</Alert>

      <div className="card">
        {step === 0 && (
          <>
            <div className="field">
              <label htmlFor="name">Your name</label>
              <input
                id="name"
                value={form.reporter_name}
                onChange={(e) => set("reporter_name", e.target.value)}
                maxLength={60}
              />
            </div>
            <div className="field">
              <label htmlFor="contact">Phone number or email</label>
              <input
                id="contact"
                value={form.reporter_contact}
                onChange={(e) => set("reporter_contact", e.target.value)}
                maxLength={15}
                placeholder="9876543210"
              />
              {form.reporter_contact && !contactValid && (
                <p className="hint" style={{ color: "var(--high)" }}>
                  Enter a 10-digit phone number or a valid email address.
                </p>
              )}
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <div className="field">
              <label htmlFor="category">What kind of scam was it?</label>
              <select
                id="category"
                value={form.category}
                onChange={(e) => set("category", e.target.value)}
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="description">What happened?</label>
              <textarea
                id="description"
                value={form.description}
                onChange={(e) => set("description", e.target.value)}
                maxLength={500}
                placeholder="Include the message you received, any links, and the UPI ID or number involved."
              />
              <p className="hint">
                {form.description.length}/500 characters. Paste the original message
                if you still have it — it is what the risk check reads.
              </p>
            </div>
            <div className="field">
              <label htmlFor="amount">How much did you lose? (optional)</label>
              <input
                id="amount"
                type="number"
                min="0"
                step="0.01"
                value={form.amount_involved}
                onChange={(e) => set("amount_involved", e.target.value)}
                placeholder="0.00"
              />
              <p className="hint">Leave blank if you did not lose money.</p>
            </div>
          </>
        )}

        {step === 2 && (
          <table>
            <tbody>
              <tr>
                <td className="muted">Name</td>
                <td>{form.reporter_name}</td>
              </tr>
              <tr>
                <td className="muted">Contact</td>
                <td>{form.reporter_contact}</td>
              </tr>
              <tr>
                <td className="muted">Category</td>
                <td>{CATEGORIES.find((c) => c.value === form.category)?.label}</td>
              </tr>
              <tr>
                <td className="muted">Amount lost</td>
                <td>{form.amount_involved ? rupees(Number(form.amount_involved)) : "Not stated"}</td>
              </tr>
              <tr>
                <td className="muted">What happened</td>
                <td style={{ whiteSpace: "pre-wrap" }}>{form.description}</td>
              </tr>
            </tbody>
          </table>
        )}
      </div>

      <div className="actions">
        {step > 0 && (
          <button className="secondary" onClick={() => setStep(step - 1)}>
            Back
          </button>
        )}
        {step < STEPS.length - 1 ? (
          <button disabled={!stepValid} onClick={() => setStep(step + 1)}>
            Continue
          </button>
        ) : (
          <button disabled={busy} onClick={submit}>
            {busy ? "Submitting…" : "Submit report"}
          </button>
        )}
      </div>
    </>
  );
}
