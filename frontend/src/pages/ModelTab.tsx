import { useEffect, useState } from "react";

import { api, type ModelInfo, type ModelSourceMetrics } from "../api";
import { Alert, Empty, Stat, when } from "../ui";

/** The detection model, as measured — not as claimed.
 *
 *  Everything here is read from the model service, so what the screen shows is
 *  whatever artefact is actually loaded. Typing the numbers into the interface
 *  by hand would let them drift away from the model in use, which is exactly
 *  the sort of thing that gets noticed during a demonstration.
 */
export default function ModelTab({ onError }: { onError: (value: string) => void }) {
  const [info, setInfo] = useState<ModelInfo | null>(null);

  useEffect(() => {
    api
      .get<ModelInfo>("/admin/model")
      .then(setInfo)
      .catch((err) => onError((err as Error).message));
  }, [onError]);

  if (!info) return <p className="muted">Loading…</p>;

  if (!info.available) {
    return (
      <div className="card">
        <h2>Detection model</h2>
        <Alert kind="info">{info.detail}</Alert>
        <p className="hint" style={{ marginBottom: 0 }}>
          The model runs as its own service so it can be retrained or replaced
          without touching the rest of the system. While it is down, risk scoring
          falls back to the built-in rules, so reports can still be filed — they
          are just scored less precisely. Start it from the <code>ml</code> folder
          with <code>uvicorn app.main:app --port 8001</code>, or use{" "}
          <b>Run FSDIRAS.bat</b>, which starts it for you.
        </p>
      </div>
    );
  }

  const overall = info.overall!;
  const pct = (value: number) => `${(value * 100).toFixed(1)}%`;

  return (
    <>
      <div className="grid" style={{ marginBottom: 16 }}>
        <Stat value={pct(overall.recall)} label="Scams caught (recall)" />
        <Stat value={pct(overall.precision)} label="Flags that were right (precision)" />
        <Stat value={overall.roc_auc?.toFixed(3) ?? "-"} label="ROC AUC" />
        <Stat
          value={info.dataset ? info.dataset.total_messages.toLocaleString("en-IN") : "-"}
          label="Messages trained on"
        />
      </div>

      <div className="split">
        <div>
          <div className="card">
            <h2>What is running</h2>
            <table>
              <tbody>
                <tr>
                  <td className="muted">Version</td>
                  <td className="mono">{info.model_version}</td>
                </tr>
                <tr>
                  <td className="muted">Algorithm</td>
                  <td>{info.algorithm}</td>
                </tr>
                <tr>
                  <td className="muted">Trained</td>
                  <td>{info.trained_at ? when(info.trained_at) : "-"}</td>
                </tr>
                <tr>
                  <td className="muted">Decision threshold</td>
                  <td>{info.decision_threshold}</td>
                </tr>
              </tbody>
            </table>
            {info.threshold_rationale && (
              <p className="hint" style={{ marginTop: 10 }}>
                <b>Why that threshold:</b> {info.threshold_rationale}
              </p>
            )}
          </div>

          <div className="card">
            <h2>How it scored, by data source</h2>
            <p className="hint" style={{ marginTop: 0 }}>
              Reported separately on purpose. The synthetic half is generated from
              templates and is therefore easier; a single combined figure would let
              it flatter the harder half of real messages.
            </p>
            <table>
              <thead>
                <tr>
                  <th>Source</th>
                  <th>Precision</th>
                  <th>Recall</th>
                  <th>Messages</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(info.per_source ?? {}).map(([source, m]) => (
                  <tr key={source}>
                    <td>{source === "uci_sms" ? "Real SMS (public)" : "Indian scams (synthetic)"}</td>
                    <td>{pct(m.precision)}</td>
                    <td>{pct(m.recall)}</td>
                    <td>{m.support.scam + m.support.legitimate}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <ConfusionMatrix m={overall} />
        </div>

        <div>
          <div className="card">
            <h2>Why this model</h2>
            <p style={{ margin: 0 }}>{info.why_this_model}</p>
          </div>

          {info.cross_validation && (
            <div className="card">
              <h2>Stability</h2>
              <p style={{ margin: 0 }}>
                {info.cross_validation.folds}-fold cross-validated{" "}
                {info.cross_validation.metric} on the training data:{" "}
                <b>{info.cross_validation.mean.toFixed(3)}</b> ± {info.cross_validation.std.toFixed(3)}.
              </p>
              <p className="hint">
                A single split can flatter a model by luck. This says the result
                holds across five different splits.
              </p>
            </div>
          )}

          <div className="card">
            <h2>Known limitations</h2>
            {info.honest_limitations?.length ? (
              <ul style={{ margin: 0, paddingLeft: 18 }}>
                {info.honest_limitations.map((item) => (
                  <li key={item} style={{ marginBottom: 6 }}>
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <Empty>None recorded.</Empty>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function ConfusionMatrix({ m }: { m: ModelSourceMetrics }) {
  const c = m.confusion_matrix;
  const cell = (value: number, tone: "good" | "bad") => (
    <td
      style={{
        textAlign: "center",
        fontSize: 18,
        fontWeight: 700,
        color: tone === "good" ? "var(--low)" : "var(--high)",
      }}
    >
      {value}
    </td>
  );

  return (
    <div className="card">
      <h2>Where it was right and wrong</h2>
      <table>
        <thead>
          <tr>
            <th></th>
            <th style={{ textAlign: "center" }}>Flagged as scam</th>
            <th style={{ textAlign: "center" }}>Not flagged</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <b>Actually a scam</b>
            </td>
            {cell(c.true_positive, "good")}
            {cell(c.false_negative, "bad")}
          </tr>
          <tr>
            <td>
              <b>Actually legitimate</b>
            </td>
            {cell(c.false_positive, "bad")}
            {cell(c.true_negative, "good")}
          </tr>
        </tbody>
      </table>
      <p className="hint" style={{ marginBottom: 0 }}>
        The <b>{c.false_negative}</b> scams it missed are the costly errors — a
        victim loses money. The <b>{c.false_positive}</b> false alarms cost an
        investigator a few minutes of reading. The threshold is deliberately set
        to keep the first number low, which is why it is not simply 0.5.
      </p>
    </div>
  );
}
