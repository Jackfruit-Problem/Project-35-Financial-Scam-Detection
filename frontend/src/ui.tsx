/** Small shared pieces, so every screen speaks the same visual language. */
import type { ReactNode } from "react";

/** Turns snake_case enum values from the API into readable labels. */
export function humanise(value: string | null | undefined): string {
  if (!value) return "-";
  return value.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function rupees(amount: number | null | undefined): string {
  return `₹${Number(amount ?? 0).toLocaleString("en-IN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function when(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function RiskBadge({ band, score }: { band: string | null; score: number | null }) {
  if (band === null) return <span className="badge neutral">Not scored</span>;
  return (
    <span className={`badge ${band}`}>
      {humanise(band)}
      {score !== null ? ` · ${score}` : ""}
    </span>
  );
}

/** Case and recovery statuses share a colour language: red needs attention. */
export function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "resolved" || status === "closed" || status === "fully_recovered"
      ? "low"
      : status === "escalated" || status === "rejected"
        ? "high"
        : status === "under_investigation" || status === "in_progress"
          ? "medium"
          : "neutral";
  return <span className={`badge ${tone}`}>{humanise(status)}</span>;
}

export function Alert({ kind, children }: { kind: "error" | "success" | "info"; children: ReactNode }) {
  if (!children) return null;
  return <div className={`alert ${kind}`}>{children}</div>;
}

export function Stat({ value, label }: { value: ReactNode; label: string }) {
  return (
    <div className="stat">
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}

export const CATEGORIES = [
  { value: "phishing", label: "Phishing message or email" },
  { value: "upi_fraud", label: "UPI / payment fraud" },
  { value: "loan_app", label: "Fake loan application" },
  { value: "investment", label: "Investment fraud" },
  { value: "other", label: "Something else" },
];

export const CASE_STATUSES = [
  "new",
  "under_investigation",
  "escalated",
  "resolved",
  "closed",
];

export const RECOVERY_STATUSES = [
  "requested",
  "in_progress",
  "partially_recovered",
  "fully_recovered",
  "rejected",
];
