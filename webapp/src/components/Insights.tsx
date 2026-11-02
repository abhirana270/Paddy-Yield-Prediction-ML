import type { CSSProperties } from "react";
import type { Metadata } from "../api";
import { kg, num, pct } from "../format";

const DEPLOYED = "Logistic Regression";

export default function Insights({ meta }: { meta: Metadata }) {
  const m = meta.metrics;
  const { labels, matrix } = m.confusion_matrix;
  const maxCell = Math.max(...matrix.flat());
  const lr = m.comparison.find((r) => r.model === DEPLOYED)!;

  return (
    <section className="insights" aria-labelledby="insights-title">
      <h2 id="insights-title">About the model</h2>

      <div className="kpis">
        <div className="card kpi">
          <span className="stat-label">Accuracy (test set)</span>
          <span className="kpi-value">{pct(lr.accuracy)}</span>
          <span className="muted small">{DEPLOYED}</span>
        </div>
        <div className="card kpi">
          <span className="stat-label">Yield estimate error</span>
          <span className="kpi-value">±{kg(m.regressor.mae_kg)}</span>
          <span className="muted small">mean absolute error · R² {m.regressor.r2}</span>
        </div>
        <div className="card kpi">
          <span className="stat-label">Training data</span>
          <span className="kpi-value">{num(m.rows_after_dedup)}</span>
          <span className="muted small">farms after removing {num(m.rows_raw - m.rows_after_dedup)} duplicates</span>
        </div>
      </div>

      <div className="insights-grid">
        <div className="card">
          <h3>Classifier comparison</h3>
          <p className="muted small">Accuracy on the same {m.test_rows}-farm test set (80/20 split).</p>
          <div className="compare">
            {m.comparison.map((r) => (
              <div className="prob-row" key={r.model}>
                <span className="prob-name wide">
                  {r.model}
                  {r.model === DEPLOYED && <span className="tag">in use</span>}
                </span>
                <div className="bar">
                  <div
                    className={`bar-fill ${r.model === DEPLOYED ? "tone-accent" : "tone-neutral"}`}
                    style={{ width: pct(r.accuracy) }}
                  />
                </div>
                <span className="prob-val">{pct(r.accuracy)}</span>
              </div>
            ))}
          </div>
          <p className="muted small">
            Logistic Regression is used because it is the original project's chosen model. Its accuracy is within
            1% of the top model, and it gives a probability for each class.
          </p>
        </div>

        <div className="card">
          <h3>Confusion matrix</h3>
          <p className="muted small">Logistic Regression on the test set: rows are actual, columns predicted.</p>
          <div className="cm" role="table" aria-label="Confusion matrix">
            <div role="row" className="cm-row">
              <span role="columnheader" />
              {labels.map((l) => (
                <span role="columnheader" key={l} className="cm-head">{l}</span>
              ))}
            </div>
            {matrix.map((row, i) => (
              <div role="row" className="cm-row" key={labels[i]}>
                <span role="rowheader" className="cm-head">{labels[i]}</span>
                {row.map((n, j) => (
                  <span
                    role="cell"
                    key={j}
                    className={`cm-cell ${i === j ? "diag" : ""}`}
                    style={{ "--a": (n / maxCell).toFixed(3) } as CSSProperties}
                  >
                    {n}
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card note">
        <h3>How to read the result</h3>
        <p>
          The categories split farms into three equal groups by <strong>total</strong> harvest: Low is up to{" "}
          {kg(meta.categories[0].max_kg)}, Medium up to {kg(meta.categories[1].max_kg)}, and High above that. Total
          harvest grows almost exactly with farm area, so <strong>farm size is the biggest driver of the category</strong>.
          To compare how productive farms are, look at the per-hectare estimate. In this dataset it ranges from{" "}
          {kg(m.yield_per_hectare_kg.min)} to {kg(m.yield_per_hectare_kg.max)} per hectare, with an average of{" "}
          {kg(m.yield_per_hectare_kg.mean)}.
        </p>
      </div>
    </section>
  );
}
