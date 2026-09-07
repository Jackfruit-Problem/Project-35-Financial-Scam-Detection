import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./auth";
import Admin from "./pages/Admin";
import Awareness from "./pages/Awareness";
import CaseDetail from "./pages/CaseDetail";
import Cases from "./pages/Cases";
import CheckMessage from "./pages/CheckMessage";
import Login from "./pages/Login";
import MyReports from "./pages/MyReports";
import SubmitReport from "./pages/SubmitReport";
import type { Role } from "./api";

/** Nav is built from the signed-in role, so nobody is shown a door they
 *  cannot open. The server enforces this too -- this is only courtesy. */
const NAV: { to: string; label: string; roles: Role[] | "all" }[] = [
  { to: "/report", label: "Report a scam", roles: ["victim", "admin"] },
  { to: "/my-reports", label: "My reports", roles: ["victim", "admin"] },
  { to: "/cases", label: "Cases", roles: ["investigator", "recovery_officer", "admin"] },
  { to: "/check", label: "Check a message", roles: "all" },
  { to: "/awareness", label: "Learn", roles: "all" },
  { to: "/admin", label: "Admin", roles: ["admin"] },
];

function Shell() {
  const { user, logout } = useAuth();
  const visible = NAV.filter(
    (item) => item.roles === "all" || (user && item.roles.includes(user.role)),
  );

  return (
    <>
      <header className="topbar">
        <NavLink to="/" className="brand">
          FSDIRAS<span>.</span>
        </NavLink>
        <nav className="nav">
          {visible.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="whoami">
          {user ? (
            <>
              <span>
                {user.full_name} · <strong>{user.role.replace(/_/g, " ")}</strong>
              </span>
              <button className="secondary small" onClick={logout}>
                Sign out
              </button>
            </>
          ) : (
            <NavLink to="/login">Sign in</NavLink>
          )}
        </div>
      </header>

      <main className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/check" element={<CheckMessage />} />
          <Route path="/awareness" element={<Awareness />} />
          <Route path="/report" element={<Protected><SubmitReport /></Protected>} />
          <Route path="/my-reports" element={<Protected><MyReports /></Protected>} />
          <Route path="/cases" element={<Protected><Cases /></Protected>} />
          <Route path="/cases/:caseRef" element={<Protected><CaseDetail /></Protected>} />
          <Route path="/admin" element={<Protected><Admin /></Protected>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}

function Protected({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <p className="muted">Loading…</p>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function Home() {
  const { user } = useAuth();

  return (
    <>
      <div className="page-head">
        <h1>Financial Scam Detection, Investigation &amp; Recovery</h1>
        <p>
          Report a scam, track the investigation, and follow what happens to your
          money — in one place.
        </p>
      </div>

      <div className="grid">
        <div className="card">
          <h2>Been scammed?</h2>
          <p>
            File a report with whatever detail you have. It is scored for risk
            immediately and a case is opened for you.
          </p>
          <NavLink to={user ? "/report" : "/login"}>
            <button>Report a scam</button>
          </NavLink>
        </div>
        <div className="card">
          <h2>Not sure yet?</h2>
          <p>
            Paste a suspicious message or link and see why it does or does not
            look like a scam. No account needed to learn the patterns.
          </p>
          <NavLink to="/check">
            <button className="secondary">Check a message</button>
          </NavLink>
        </div>
        <div className="card">
          <h2>Learn the patterns</h2>
          <p>
            Short articles and a quiz covering UPI fraud, phishing and fake loan
            apps — the three that catch the most people.
          </p>
          <NavLink to="/awareness">
            <button className="secondary">Read and test yourself</button>
          </NavLink>
        </div>
      </div>

      <div className="card">
        <p className="muted" style={{ margin: 0, fontSize: 13 }}>
          FSDIRAS assists with reporting and recovery. It does not guarantee that
          lost funds are returned, and it does not replace filing an official
          complaint with the police or the National Cyber Crime Reporting Portal
          at cybercrime.gov.in.
        </p>
      </div>
    </>
  );
}

export default function App() {
  return <Shell />;
}
