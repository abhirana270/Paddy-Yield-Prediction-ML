import type { Category, Metadata, Prediction } from "../api";
import { kg, pct } from "../format";

interface Props {
  meta: Metadata;
  result: Prediction | null;
  loading: boolean;
  error: string | null;
}

const BLURB: Record<Category, string> = {
  Low: "Expected total harvest is in the bottom third of farms in the dataset.",
  Medium: "Expected total harvest is in the middle third of farms in the dataset.",
  High: "Expected total harvest is in the top third of farms in the dataset.",
};

function YieldScale({ meta, value }: { meta: Metadata; value: number }) {
  const lo = meta.categories[0].min_kg;
  const hi = meta.categories[meta.categories.length - 1].max_kg;
  const pos = (v: number) => Math.min(100, Math.max(0, ((v - lo) / (hi - lo)) * 100));
  return (
    <div className="scale">
      <div className="scale-track">
        {meta.categories.map((c) => (
          <div
            key={c.label}
            className={`scale-seg tone-${c.label.toLowerCase()}`}
            style={{ width: `${pos(c.max_kg) - pos(c.min_kg)}%` }}
            title={`${c.label}: ${kg(c.min_kg)} – ${kg(c.max_kg)}`}
          />
        ))}
        <div className="scale-marker" style={{ left: `${pos(value)}%` }} aria-hidden="true" />
      </div>
      <div className="scale-labels">
        {meta.categories.map((c) => (
          <span key={c.label} style={{ width: `${pos(c.max_kg) - pos(c.min_kg)}%` }}>
            <strong>{c.label}</strong>
            <small>up to {kg(c.max_kg)}</small>
          </span>
        ))}
      </div>
    </div>
  );
}

export default function ResultCard({ meta, result, loading, error }: Props) {
  if (!result) {
    return (
      <section className="card result" aria-live="polite" aria-busy={loading}>
        {error ? <p className="error">{error}</p> : <><div className="spinner" /><p className="muted">Predicting…</p></>}
      </section>
    );
  }

  const tone = result.category.toLowerCase();
  return (
    <section className={`card result ${loading ? "is-updating" : ""}`} aria-live="polite" aria-busy={loading}>
      <p className="result-kicker">Predicted yield category</p>
      <div className="result-head">
        <span className={`badge tone-${tone}`}>{result.category}</span>
        <span className="confidence">{pct(result.confidence)} confidence</span>
      </div>
      <p className="muted">{BLURB[result.category]}</p>

      <div className="stats">
        <div className="stat">
          <span className="stat-label">Estimated yield</span>
          <span className="stat-value">{kg(result.estimated_yield_kg)}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Per hectare</span>
          <span className="stat-value">{kg(result.estimated_yield_per_hectare_kg)}</span>
        </div>
      </div>

      <YieldScale meta={meta} value={result.estimated_yield_kg} />

      <div className="probs">
        <p className="section-label">Class probabilities</p>
        {meta.categories.map(({ label: c }) => (
          <div className="prob-row" key={c}>
            <span className="prob-name">{c}</span>
            <div className="bar">
              <div className={`bar-fill tone-${c.toLowerCase()}`} style={{ width: pct(result.probabilities[c]) }} />
            </div>
            <span className="prob-val">{pct(result.probabilities[c])}</span>
          </div>
        ))}
      </div>

      {result.out_of_training_range && (
        <p className="warn">
          The model was trained on farms of {meta.inputs.hectares.min}–{meta.inputs.hectares.max} hectares, so this
          prediction is an extrapolation.
        </p>
      )}
      {error && <p className="error">{error}</p>}
    </section>
  );
}
