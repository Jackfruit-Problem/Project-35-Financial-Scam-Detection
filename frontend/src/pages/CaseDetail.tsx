import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";

import {
  api,
  type Case,
  type CustodyEvent,
  type Evidence,
  type Recovery,
  type Report,
  type Verification,
} from "../api";
import { useAuth } from "../auth";
import {
  Alert,
  CASE_STATUSES,
  Empty,
  RECOVERY_STATUSES,
  RiskBadge,
  StatusBadge,
  humanise,
  rupees,
  when,
} from "../ui";

interface Detail {
  case: Case;
  report: Report;
  investigator_name: string | null;
}

interface Note {
  id: number;
  author_id: number;
  body: string;
  created_at: string;
}

export default function CaseDetail() {
  const { caseRef = "" } = useParams();
  const { user } = useAuth();

  const [detail, setDetail] = useState<Detail | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [recovery, setRecovery] = useState<Recovery | null>(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      setDetail(await api.get<Detail>(`/cases/${caseRef}`));
      setEvidence(await api.get<Evidence[]>(`/cases/${caseRef}/evidence`));
      setNotes(await api.get<Note[]>(`/cases/${caseRef}/notes`));
      try {
        setRecovery(await api.get<Recovery>(`/cases/${caseRef}/recovery`));
      } catch {
        // A case without a recovery request is normal, not an error.
        setRecovery(null);
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }, [caseRef]);

  useEffect(() => {
    load();
  }, [load]);

  if (error && !detail) return <Alert kind="error">{error}</Alert>;
  if (!detail) return <p className="muted">Loading…</p>;

  const isAssignedInvestigator =
    user?.role === "investigator" && detail.case.assigned_investigator_id === user.id;
  const isOfficer = user?.role === "recovery_officer" || user?.role === "admin";
  const isStaff = user?.role !== "victim";

  return (
    <>
      <div className="page-head">
        <h1 className="mono" style={{ fontSize: 22 }}>
          {detail.case.case_ref}
        </h1>
        <p>
          Opened {when(detail.case.created_at)} · last updated{" "}
          {when(detail.case.updated_at)}
        </p>
      </div>

      <Alert kind="error">{error}</Alert>
      <Alert kind="success">{message}</Alert>

      <div className="split">
        <div>
          <div className="card">
            <h2>The report</h2>
            <table>
              <tbody>
                <tr>
                  <td className="muted">Reference</td>
                  <td className="mono">{detail.report.report_ref}</td>
                </tr>
                <tr>
                  <td className="muted">Reported by</td>
                  <td>
                    {detail.report.reporter_name} · {detail.report.reporter_contact}
                  </td>
                </tr>
                <tr>
                  <td className="muted">Category</td>
                  <td>{humanise(detail.report.category)}</td>
                </tr>
                <tr>
                  <td className="muted">Amount lost</td>
                  <td>
                    {detail.report.amount_involved
                      ? rupees(detail.report.amount_involved)
                      : "Not stated"}
                  </td>
                </tr>
                <tr>
                  <td className="muted">Risk</td>
                  <td>
                    <RiskBadge
                      band={detail.report.risk_band}
                      score={detail.report.risk_score}
                    />
                  </td>
                </tr>
                <tr>
                  <td className="muted">Status</td>
                  <td>
                    <StatusBadge status={detail.case.status} />
                  </td>
                </tr>
                <tr>
                  <td className="muted">Investigator</td>
                  <td>{detail.investigator_name ?? "Not yet assigned"}</td>
                </tr>
              </tbody>
            </table>

            <p style={{ marginBottom: 0, whiteSpace: "pre-wrap" }}>
              {detail.report.description}
            </p>
          </div>

          <EvidencePanel
            caseRef={caseRef}
            evidence={evidence}
            canArchive={isAssignedInvestigator || user?.role === "admin"}
            onChange={load}
            onMessage={setMessage}
            onError={setError}
          />

          <NotesPanel
            caseRef={caseRef}
            notes={notes}
            canWrite={isStaff}
            onChange={load}
            onError={setError}
          />
        </div>

        <div>
          {isAssignedInvestigator && (
            <StatusPanel
              caseRef={caseRef}
              current={detail.case.status}
              onChange={load}
              onMessage={setMessage}
              onError={setError}
            />
          )}

          <RecoveryPanel
            caseRef={caseRef}
            recovery={recovery}
            canRaise={isAssignedInvestigator || isOfficer}
            canUpdate={isOfficer}
            onChange={load}
            onMessage={setMessage}
            onError={setError}
          />

          <div className="card">
            <h2>Reports</h2>
            <div className="actions">
              <button
                className="secondary small"
                onClick={() =>
                  api.download(`/cases/${caseRef}/report.pdf`, `case-${caseRef}.pdf`)
                }
              >
                Download case report
              </button>
              {recovery && (
                <button
                  className="secondary small"
                  onClick={() =>
                    api.download(
                      `/cases/${caseRef}/recovery-report.pdf`,
                      `recovery-${caseRef}.pdf`,
                    )
                  }
                >
                  Download recovery report
                </button>
              )}
            </div>
            <p className="hint">
              PDFs formatted for submission to a bank, the police or the RBI
              Ombudsman.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

function EvidencePanel({
  caseRef,
  evidence,
  canArchive,
  onChange,
  onMessage,
  onError,
}: {
  caseRef: string;
  evidence: Evidence[];
  canArchive: boolean;
  onChange: () => void;
  onMessage: (value: string) => void;
  onError: (value: string) => void;
}) {
  const fileInput = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [openChain, setOpenChain] = useState<number | null>(null);

  async function upload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setBusy(true);
    onError("");
    try {
      await api.upload(`/cases/${caseRef}/evidence`, file);
      onMessage(`${file.name} uploaded and recorded in the chain of custody.`);
      onChange();
    } catch (err) {
      onError((err as Error).message);
    } finally {
      setBusy(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function archive(id: number) {
    const reason = window.prompt("Why is this evidence being archived?");
    if (!reason) return;
    try {
      await api.post(`/evidence/${id}/archive`, { reason });
      onMessage("Evidence archived. It remains in the record and in the chain.");
      onChange();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  return (
    <div className="card">
      <h2>Evidence</h2>

      {evidence.length === 0 ? (
        <Empty>No evidence attached yet.</Empty>
      ) : (
        <table>
          <thead>
            <tr>
              <th>File</th>
              <th>Size</th>
              <th>Fingerprint</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {evidence.map((item) => (
              <tr key={item.id}>
                <td>
                  {item.filename}
                  {item.is_archived && (
                    <span className="badge neutral" style={{ marginLeft: 6 }}>
                      Archived
                    </span>
                  )}
                  <div className="hint">{when(item.created_at)}</div>
                </td>
                <td>{(item.size_bytes / 1024).toFixed(1)} KB</td>
                <td className="mono" title={item.sha256}>
                  {item.sha256.slice(0, 12)}…
                </td>
                <td style={{ textAlign: "right", whiteSpace: "nowrap" }}>
                  <button
                    className="secondary small"
                    onClick={() => setOpenChain(openChain === item.id ? null : item.id)}
                  >
                    {openChain === item.id ? "Hide" : "Custody"}
                  </button>{" "}
                  <button
                    className="secondary small"
                    onClick={() =>
                      api.download(`/evidence/${item.id}/download`, item.filename)
                    }
                  >
                    Download
                  </button>
                  {canArchive && !item.is_archived && (
                    <>
                      {" "}
                      <button className="secondary small" onClick={() => archive(item.id)}>
                        Archive
                      </button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {openChain !== null && <CustodyChain evidenceId={openChain} />}

      <div style={{ marginTop: 14 }}>
        <input ref={fileInput} type="file" onChange={upload} disabled={busy} />
        <p className="hint">
          PNG, JPEG, WebP, PDF or plain text, up to 10 MB. Files are scanned,
          encrypted before storage, and can never be deleted — only archived
          with a reason.
        </p>
      </div>
    </div>
  );
}

function CustodyChain({ evidenceId }: { evidenceId: number }) {
  const [events, setEvents] = useState<CustodyEvent[] | null>(null);
  const [verification, setVerification] = useState<Verification | null>(null);

  useEffect(() => {
    api.get<CustodyEvent[]>(`/evidence/${evidenceId}/custody`).then(setEvents);
    api.get<Verification>(`/evidence/${evidenceId}/verify`).then(setVerification);
  }, [evidenceId]);

  if (!events) return <p className="muted">Loading chain…</p>;

  return (
    <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--border)" }}>
      {verification && (
        <Alert kind={verification.chain_intact && verification.file_intact ? "success" : "error"}>
          {verification.chain_intact && verification.file_intact ? (
            <>
              Verified. The custody record has not been altered and the file still
              matches its original fingerprint.
            </>
          ) : (
            <>
              <strong>Tampering detected.</strong>{" "}
              {!verification.chain_intact &&
                `The custody record was altered at entry #${verification.broken_at_event_id}. `}
              {!verification.file_intact && "The stored file no longer matches its fingerprint."}
            </>
          )}
        </Alert>
      )}

      <ul className="chain">
        {events.map((event) => (
          <li key={event.id}>
            <strong>{humanise(event.action)}</strong> by user #{event.actor_id}
            <div className="hint">{when(event.created_at)}</div>
            {event.detail && <div className="hint">{event.detail}</div>}
            <div className="mono hint">
              {event.prev_hash?.slice(0, 10)}… → {event.entry_hash.slice(0, 10)}…
            </div>
          </li>
        ))}
      </ul>
      <p className="hint">
        Each entry contains a fingerprint of the one before it, so altering any
        past entry breaks every link that follows.
      </p>
    </div>
  );
}

function NotesPanel({
  caseRef,
  notes,
  canWrite,
  onChange,
  onError,
}: {
  caseRef: string;
  notes: Note[];
  canWrite: boolean;
  onChange: () => void;
  onError: (value: string) => void;
}) {
  const [body, setBody] = useState("");

  async function add() {
    try {
      await api.post(`/cases/${caseRef}/notes`, { body });
      setBody("");
      onChange();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  return (
    <div className="card">
      <h2>Investigation notes</h2>
      {notes.length === 0 ? (
        <Empty>No notes yet.</Empty>
      ) : (
        <ul className="chain">
          {notes.map((note) => (
            <li key={note.id}>
              {note.body}
              <div className="hint">
                User #{note.author_id} · {when(note.created_at)}
              </div>
            </li>
          ))}
        </ul>
      )}

      {canWrite && (
        <div style={{ marginTop: 12 }}>
          <textarea
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Add a note to the case file…"
            maxLength={2000}
          />
          <button disabled={!body.trim()} onClick={add} style={{ marginTop: 8 }}>
            Add note
          </button>
        </div>
      )}
    </div>
  );
}

function StatusPanel({
  caseRef,
  current,
  onChange,
  onMessage,
  onError,
}: {
  caseRef: string;
  current: string;
  onChange: () => void;
  onMessage: (value: string) => void;
  onError: (value: string) => void;
}) {
  const [status, setStatus] = useState(current);
  const [note, setNote] = useState("");

  async function save() {
    try {
      await api.patch(`/cases/${caseRef}/status`, { status, note: note || null });
      onMessage(`Case status changed to ${humanise(status)}.`);
      setNote("");
      onChange();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  return (
    <div className="card">
      <h2>Update status</h2>
      <div className="field">
        <select value={status} onChange={(e) => setStatus(e.target.value)}>
          {CASE_STATUSES.map((value) => (
            <option key={value} value={value}>
              {humanise(value)}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Optional note explaining the change"
          style={{ minHeight: 70 }}
        />
      </div>
      <button disabled={status === current && !note} onClick={save}>
        Save
      </button>
      <p className="hint">
        Only the investigator assigned to this case can change its status.
      </p>
    </div>
  );
}

function RecoveryPanel({
  caseRef,
  recovery,
  canRaise,
  canUpdate,
  onChange,
  onMessage,
  onError,
}: {
  caseRef: string;
  recovery: Recovery | null;
  canRaise: boolean;
  canUpdate: boolean;
  onChange: () => void;
  onMessage: (value: string) => void;
  onError: (value: string) => void;
}) {
  const [bank, setBank] = useState({ bank_name: "", ifsc_code: "", account_number: "" });
  const [status, setStatus] = useState(recovery?.status ?? "requested");
  const [amount, setAmount] = useState("");
  const [remarks, setRemarks] = useState("");

  useEffect(() => {
    if (recovery) setStatus(recovery.status);
  }, [recovery]);

  async function raise() {
    try {
      await api.post(`/cases/${caseRef}/recovery`, bank);
      onMessage("Recovery request raised and the victim has been notified.");
      onChange();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  async function update() {
    try {
      await api.patch(`/cases/${caseRef}/recovery`, {
        status,
        amount_recovered: amount ? Number(amount) : null,
        remarks: remarks || null,
      });
      onMessage("Recovery updated. The victim has been notified of the change.");
      setAmount("");
      setRemarks("");
      onChange();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  if (!recovery) {
    return (
      <div className="card">
        <h2>Recovery</h2>
        {canRaise ? (
          <>
            <p className="hint" style={{ marginTop: 0 }}>
              The amount lost and the reporter's details are taken from the case —
              only the receiving bank is needed here.
            </p>
            <div className="field">
              <label>Bank name</label>
              <input
                value={bank.bank_name}
                onChange={(e) => setBank({ ...bank, bank_name: e.target.value })}
                placeholder="State Bank of India"
              />
            </div>
            <div className="field">
              <label>IFSC code</label>
              <input
                value={bank.ifsc_code}
                onChange={(e) => setBank({ ...bank, ifsc_code: e.target.value })}
                maxLength={11}
                placeholder="SBIN0001234"
              />
            </div>
            <div className="field">
              <label>Beneficiary account number</label>
              <input
                value={bank.account_number}
                onChange={(e) => setBank({ ...bank, account_number: e.target.value })}
                maxLength={20}
              />
            </div>
            <button onClick={raise}>Raise recovery request</button>
          </>
        ) : (
          <Empty>No recovery request has been raised for this case yet.</Empty>
        )}
      </div>
    );
  }

  const outstanding = recovery.amount_reported - recovery.amount_recovered;

  return (
    <div className="card">
      <h2>Recovery</h2>

      <div style={{ marginBottom: 12 }}>
        <StatusBadge status={recovery.status} />
      </div>

      <table>
        <tbody>
          <tr>
            <td className="muted">Bank</td>
            <td>{recovery.bank_name ?? "-"}</td>
          </tr>
          <tr>
            <td className="muted">Reported lost</td>
            <td>{rupees(recovery.amount_reported)}</td>
          </tr>
          <tr>
            <td className="muted">Recovered</td>
            <td>{rupees(recovery.amount_recovered)}</td>
          </tr>
          <tr>
            <td className="muted">Outstanding</td>
            <td>{rupees(outstanding)}</td>
          </tr>
        </tbody>
      </table>

      {recovery.remarks && <p className="hint">{recovery.remarks}</p>}

      {canUpdate && (
        <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--border)" }}>
          <div className="field">
            <label>New status</label>
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              {RECOVERY_STATUSES.map((value) => (
                <option key={value} value={value}>
                  {humanise(value)}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Amount recovered</label>
            <input
              type="number"
              min="0"
              max={recovery.amount_reported}
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder={String(recovery.amount_recovered)}
            />
            <p className="hint">Cannot exceed {rupees(recovery.amount_reported)}.</p>
          </div>
          <div className="field">
            <label>Remarks</label>
            <input value={remarks} onChange={(e) => setRemarks(e.target.value)} />
          </div>
          <button onClick={update}>Update recovery</button>
        </div>
      )}
    </div>
  );
}
