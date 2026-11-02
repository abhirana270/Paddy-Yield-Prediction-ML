import { useEffect, useState } from "react";
import { getMetadata, predict, type Metadata, type Prediction, type PredictInput } from "./api";
import PredictForm from "./components/PredictForm";
import ResultCard from "./components/ResultCard";
import ModelInputs from "./components/ModelInputs";
import Insights from "./components/Insights";

export default function App() {
  const [meta, setMeta] = useState<Metadata | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [input, setInput] = useState<PredictInput | null>(null);
  const [result, setResult] = useState<Prediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMetadata = () => {
    setMetaError(null);
    getMetadata()
      .then((m) => {
        setMeta(m);
        setInput({
          hectares: 4,
          agriblock: m.inputs.agriblock[0],
          variety: m.inputs.variety[0],
          soil_type: m.inputs.soil_type[0],
          nursery: m.inputs.nursery[0],
        });
      })
      .catch((e: Error) => setMetaError(e.message));
  };

  useEffect(loadMetadata, []);

  // Predict live as the form changes (debounced; stale requests are aborted)
  useEffect(() => {
    if (!input || !(input.hectares > 0)) return;
    const ctrl = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true);
      predict(input, ctrl.signal)
        .then((r) => {
          setResult(r);
          setError(null);
        })
        .catch((e: Error) => {
          if (e.name !== "AbortError") setError(e.message);
        })
        .finally(() => {
          if (!ctrl.signal.aborted) setLoading(false);
        });
    }, 200);
    return () => {
      clearTimeout(timer);
      ctrl.abort();
    };
  }, [input]);

  return (
    <div className="page">
      <header className="hero">
        <div className="hero-inner">
          <p className="eyebrow">Machine learning · Tamil Nadu paddy farms</p>
          <h1>Paddy Yield Predictor</h1>
          <p className="lede">
            Enter your farm details to predict whether the harvest falls in the Low, Medium or High yield
            category, with an estimate of the total yield in kilograms.
          </p>
        </div>
      </header>

      <main className="container">
        {metaError ? (
          <div className="card state-card" role="alert">
            <h2>Can't reach the prediction service</h2>
            <p className="muted">{metaError}</p>
            <button className="btn" onClick={loadMetadata}>Try again</button>
          </div>
        ) : !meta || !input ? (
          <div className="card state-card" aria-busy="true">
            <div className="spinner" />
            <p className="muted">Loading model…</p>
          </div>
        ) : (
          <>
            <section className="predict-grid" aria-label="Prediction">
              <PredictForm meta={meta} value={input} onChange={setInput} />
              <ResultCard meta={meta} result={result} loading={loading} error={error} />
            </section>
            {result && <ModelInputs meta={meta} result={result} />}
            <Insights meta={meta} />
          </>
        )}
      </main>

      <footer className="footer">
        <p>
          Model trained on the{" "}
          <a href="https://github.com/abhirana270/Paddy-Yield-Prediction-ML" target="_blank" rel="noreferrer">
            Paddy Yield Prediction ML
          </a>{" "}
          dataset by Abhishek Rana. Predictions are estimates and only cover the six blocks, three varieties and
          growing conditions in that dataset.
        </p>
        <p>
          <a href="/api/docs" target="_blank" rel="noreferrer">API documentation</a>
        </p>
      </footer>
    </div>
  );
}
