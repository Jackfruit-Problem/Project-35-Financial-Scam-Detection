import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api, type Report } from "../api";
import { Alert, Empty, RiskBadge, humanise, rupees, when } from "../ui";

export default function MyReports() {
  const [reports, setReports] = useState<Report[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Report[]>("/reports/mine")
      .then(setReports)
      .catch((err) => setError((err as Error).message));
  }, []);

  return (
    <>
      <div className="page-head">
        <h1>My reports</h1>
        <p>Everything you have filed, newest first.</p>
      </div>

      <Alert kind="error">{error}</Alert>

      <div className="card">
        {reports === null ? (
          <p className="muted">Loading…</p>
        ) : reports.length === 0 ? (
          <Empty>
            You have not filed any reports yet.{" "}
            <Link to="/report">Report a scam</Link>
          </Empty>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Reference</th>
                <th>Filed</th>
                <th>Category</th>
                <th>Amount</th>
                <th>Risk</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td className="mono">{report.report_ref}</td>
                  <td>{when(report.created_at)}</td>
                  <td>{humanise(report.category)}</td>
                  <td>{report.amount_involved ? rupees(report.amount_involved) : "-"}</td>
                  <td>
                    <RiskBadge band={report.risk_band} score={report.risk_score} />
                  </td>
                  <td>{report.evidence_attached ? "Attached" : "None yet"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
