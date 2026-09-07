import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api, type Case } from "../api";
import { useAuth } from "../auth";
import { Alert, Empty, StatusBadge, when } from "../ui";

export default function Cases() {
  const { user } = useAuth();
  const [cases, setCases] = useState<Case[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<Case[]>("/cases")
      .then(setCases)
      .catch((err) => setError((err as Error).message));
  }, []);

  return (
    <>
      <div className="page-head">
        <h1>{user?.role === "investigator" ? "My case queue" : "All cases"}</h1>
        <p>
          {user?.role === "investigator"
            ? "Cases assigned to you. High-risk reports are allocated automatically."
            : "Every case in the system."}
        </p>
      </div>

      <Alert kind="error">{error}</Alert>

      <div className="card">
        {cases === null ? (
          <p className="muted">Loading…</p>
        ) : cases.length === 0 ? (
          <Empty>No cases assigned to you yet.</Empty>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Case</th>
                <th>Status</th>
                <th>Opened</th>
                <th>Last updated</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {cases.map((item) => (
                <tr key={item.id}>
                  <td className="mono">{item.case_ref}</td>
                  <td>
                    <StatusBadge status={item.status} />
                  </td>
                  <td>{when(item.created_at)}</td>
                  <td>{when(item.updated_at)}</td>
                  <td style={{ textAlign: "right" }}>
                    <Link to={`/cases/${item.case_ref}`}>
                      <button className="secondary small">Open</button>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}
