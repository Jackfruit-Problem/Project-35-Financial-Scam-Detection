import { useCallback, useEffect, useState } from "react";

import { api, type Analytics, type Role, type User } from "../api";
import { Alert, Empty, Stat, humanise, rupees } from "../ui";

interface BlacklistEntry {
  id: number;
  entry_type: string;
  value: string;
  note: string | null;
}

const ROLES: Role[] = ["victim", "investigator", "recovery_officer", "admin"];

export default function Admin() {
  const [tab, setTab] = useState<"analytics" | "users" | "blacklist">("analytics");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  return (
    <>
      <div className="page-head">
        <h1>Administration</h1>
        <p>System analytics, user roles, and the detection blacklist.</p>
      </div>

      <div className="actions" style={{ marginBottom: 16 }}>
        {(["analytics", "users", "blacklist"] as const).map((value) => (
          <button
            key={value}
            className={tab === value ? "" : "secondary"}
            onClick={() => {
              setTab(value);
              setError("");
              setMessage("");
            }}
          >
            {humanise(value)}
          </button>
        ))}
      </div>

      <Alert kind="error">{error}</Alert>
      <Alert kind="success">{message}</Alert>

      {tab === "analytics" && <AnalyticsTab onError={setError} />}
      {tab === "users" && <UsersTab onError={setError} onMessage={setMessage} />}
      {tab === "blacklist" && <BlacklistTab onError={setError} onMessage={setMessage} />}
    </>
  );
}

function AnalyticsTab({ onError }: { onError: (value: string) => void }) {
  const [data, setData] = useState<Analytics | null>(null);

  useEffect(() => {
    api
      .get<Analytics>("/admin/analytics")
      .then(setData)
      .catch((err) => onError((err as Error).message));
  }, [onError]);

  if (!data) return <p className="muted">Loading…</p>;

  const busiest = data.trending_categories[0]?.count ?? 1;

  return (
    <>
      <div className="grid" style={{ marginBottom: 16 }}>
        <Stat value={data.total_reports} label="Reports filed" />
        <Stat value={data.total_cases} label="Cases opened" />
        <Stat value={`${data.resolution_rate}%`} label="Cases resolved" />
        <Stat value={`${data.recovery_rate}%`} label="Funds recovered" />
      </div>

      <div className="split">
        <div className="card">
          <h2>Trending scam categories</h2>
          {data.trending_categories.length === 0 ? (
            <Empty>No reports yet.</Empty>
          ) : (
            <table>
              <tbody>
                {data.trending_categories.map((row) => (
                  <tr key={row.category}>
                    <td style={{ width: 160 }}>{humanise(row.category)}</td>
                    <td>
                      {/* A bar is easier to compare at a glance than a column
                          of numbers, and needs no charting library. */}
                      <div
                        style={{
                          background: "var(--accent)",
                          height: 10,
                          borderRadius: 5,
                          width: `${Math.max((row.count / busiest) * 100, 6)}%`,
                        }}
                      />
                    </td>
                    <td style={{ width: 40, textAlign: "right" }}>{row.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="card">
          <h2>Money</h2>
          <table>
            <tbody>
              <tr>
                <td className="muted">Reported lost</td>
                <td>{rupees(data.total_amount_reported)}</td>
              </tr>
              <tr>
                <td className="muted">Recovered</td>
                <td>{rupees(data.total_amount_recovered)}</td>
              </tr>
              <tr>
                <td className="muted">Fully recovered cases</td>
                <td>{data.fully_recovered_cases}</td>
              </tr>
              <tr>
                <td className="muted">Cases resolved or closed</td>
                <td>
                  {data.resolved_cases} of {data.total_cases}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}

function UsersTab({
  onError,
  onMessage,
}: {
  onError: (value: string) => void;
  onMessage: (value: string) => void;
}) {
  const [users, setUsers] = useState<User[] | null>(null);

  const load = useCallback(() => {
    api
      .get<User[]>("/admin/users")
      .then(setUsers)
      .catch((err) => onError((err as Error).message));
  }, [onError]);

  useEffect(load, [load]);

  async function setRole(id: number, role: string) {
    try {
      await api.patch(`/admin/users/${id}/role`, { role });
      onMessage("Role updated.");
      load();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  async function setActive(id: number, isActive: boolean) {
    try {
      await api.patch(`/admin/users/${id}/active?is_active=${isActive}`);
      onMessage(isActive ? "Account reactivated." : "Account deactivated.");
      load();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  if (!users) return <p className="muted">Loading…</p>;

  return (
    <div className="card">
      <h2>Users and roles</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => (
            <tr key={user.id}>
              <td>{user.full_name}</td>
              <td className="hint">{user.email}</td>
              <td>
                <select
                  value={user.role}
                  onChange={(e) => setRole(user.id, e.target.value)}
                  style={{ width: 165 }}
                >
                  {ROLES.map((role) => (
                    <option key={role} value={role}>
                      {humanise(role)}
                    </option>
                  ))}
                </select>
              </td>
              <td>
                <span className={`badge ${user.is_active ? "low" : "neutral"}`}>
                  {user.is_active ? "Active" : "Deactivated"}
                </span>
              </td>
              <td style={{ textAlign: "right" }}>
                <button
                  className="secondary small"
                  onClick={() => setActive(user.id, !user.is_active)}
                >
                  {user.is_active ? "Deactivate" : "Reactivate"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="hint">
        Promoting someone to a staff role is the only way they gain access to
        cases — registration always creates a victim account.
      </p>
    </div>
  );
}

function BlacklistTab({
  onError,
  onMessage,
}: {
  onError: (value: string) => void;
  onMessage: (value: string) => void;
}) {
  const [entries, setEntries] = useState<BlacklistEntry[] | null>(null);
  const [form, setForm] = useState({ entry_type: "upi_id", value: "", note: "" });

  const load = useCallback(() => {
    api
      .get<BlacklistEntry[]>("/admin/blacklist")
      .then(setEntries)
      .catch((err) => onError((err as Error).message));
  }, [onError]);

  useEffect(load, [load]);

  async function add(event: React.FormEvent) {
    event.preventDefault();
    try {
      await api.post("/admin/blacklist", { ...form, note: form.note || null });
      onMessage(`${form.value} is now blacklisted and will score 100 immediately.`);
      setForm({ ...form, value: "", note: "" });
      load();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  async function remove(id: number) {
    try {
      await api.del(`/admin/blacklist/${id}`);
      onMessage("Entry removed.");
      load();
    } catch (err) {
      onError((err as Error).message);
    }
  }

  return (
    <div className="split">
      <div className="card">
        <h2>Blacklisted identifiers</h2>
        {entries === null ? (
          <p className="muted">Loading…</p>
        ) : entries.length === 0 ? (
          <Empty>Nothing blacklisted yet.</Empty>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Type</th>
                <th>Value</th>
                <th>Note</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id}>
                  <td>{humanise(entry.entry_type)}</td>
                  <td className="mono">{entry.value}</td>
                  <td className="hint">{entry.note ?? "-"}</td>
                  <td style={{ textAlign: "right" }}>
                    <button className="secondary small" onClick={() => remove(entry.id)}>
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="card">
        <h2>Add an entry</h2>
        <form onSubmit={add}>
          <div className="field">
            <label>Type</label>
            <select
              value={form.entry_type}
              onChange={(e) => setForm({ ...form, entry_type: e.target.value })}
            >
              <option value="upi_id">UPI ID</option>
              <option value="url">URL</option>
              <option value="phone">Phone number</option>
            </select>
          </div>
          <div className="field">
            <label>Value</label>
            <input
              value={form.value}
              onChange={(e) => setForm({ ...form, value: e.target.value })}
              placeholder="fraudster@ybl"
              required
            />
          </div>
          <div className="field">
            <label>Note (optional)</label>
            <input
              value={form.note}
              onChange={(e) => setForm({ ...form, note: e.target.value })}
              placeholder="Reported in 12 cases"
            />
          </div>
          <button type="submit">Add to blacklist</button>
        </form>
        <p className="hint">
          The blacklist is checked before the risk model runs. A match scores 100
          straight away, because a known fraudulent identifier is a fact rather
          than a prediction.
        </p>
      </div>
    </div>
  );
}
