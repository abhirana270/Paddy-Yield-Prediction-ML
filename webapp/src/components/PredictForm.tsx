import { useEffect, useId, useState } from "react";
import type { Metadata, PredictInput } from "../api";
import { label } from "../format";

interface Props {
  meta: Metadata;
  value: PredictInput;
  onChange: (v: PredictInput) => void;
}

function Segmented({ name, options, value, onChange }: {
  name: string;
  options: string[];
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="segmented" role="radiogroup" aria-label={name}>
      {options.map((o) => (
        <label key={o} className={o === value ? "seg active" : "seg"}>
          <input type="radio" name={name} value={o} checked={o === value} onChange={() => onChange(o)} />
          {label(o)}
        </label>
      ))}
    </div>
  );
}

export default function PredictForm({ meta, value, onChange }: Props) {
  const ids = { hectares: useId(), block: useId() };
  const { min, max } = meta.inputs.hectares;
  // Keep the typed text separately so the field can be briefly empty while editing
  const [hectaresText, setHectaresText] = useState(String(value.hectares));
  useEffect(() => setHectaresText(String(value.hectares)), [value.hectares]);

  const set = <K extends keyof PredictInput>(key: K, v: PredictInput[K]) => onChange({ ...value, [key]: v });

  const onHectaresText = (text: string) => {
    setHectaresText(text);
    const n = Number(text);
    if (text !== "" && n > 0 && n <= 100) set("hectares", n);
  };

  return (
    <form className="card form" onSubmit={(e) => e.preventDefault()}>
      <h2>Farm details</h2>

      <div className="field">
        <div className="field-head">
          <label htmlFor={ids.hectares}>Farm area</label>
          <span className="input-suffix">
            <input
              className="num-input"
              type="number"
              inputMode="decimal"
              min={0.5}
              max={100}
              step={0.5}
              value={hectaresText}
              onChange={(e) => onHectaresText(e.target.value)}
              aria-label="Farm area in hectares"
            />
            <span>ha</span>
          </span>
        </div>
        <input
          id={ids.hectares}
          type="range"
          min={min}
          max={max}
          step={0.5}
          value={Math.min(Math.max(value.hectares, min), max)}
          onChange={(e) => set("hectares", Number(e.target.value))}
        />
        <div className="range-scale" aria-hidden="true">
          <span>{min} ha</span>
          <span>{max} ha</span>
        </div>
      </div>

      <div className="field">
        <label htmlFor={ids.block}>Agricultural block</label>
        <select id={ids.block} value={value.agriblock} onChange={(e) => set("agriblock", e.target.value)}>
          {meta.inputs.agriblock.map((b) => (
            <option key={b} value={b}>{b}</option>
          ))}
        </select>
        <p className="hint">Sets the rainfall, temperature, wind and humidity profile.</p>
      </div>

      <div className="field">
        <span className="field-label">Paddy variety</span>
        <Segmented name="Paddy variety" options={meta.inputs.variety} value={value.variety} onChange={(v) => set("variety", v)} />
      </div>

      <div className="field">
        <span className="field-label">Soil type</span>
        <Segmented name="Soil type" options={meta.inputs.soil_type} value={value.soil_type} onChange={(v) => set("soil_type", v)} />
      </div>

      <div className="field">
        <span className="field-label">Nursery</span>
        <Segmented name="Nursery" options={meta.inputs.nursery} value={value.nursery} onChange={(v) => set("nursery", v)} />
      </div>
    </form>
  );
}
