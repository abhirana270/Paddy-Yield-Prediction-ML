import type { Metadata, Prediction } from "../api";
import { farmInputLabel, label, num } from "../format";

const RAIN_PERIODS = [
  ["Days 1–30", "30DRain( in mm)", "30DAI(in mm)"],
  ["Days 30–50", "30_50DRain( in mm)", "30_50DAI(in mm)"],
  ["Days 51–70", "51_70DRain(in mm)", "51_70AI(in mm)"],
  ["Days 71–105", "71_105DRain(in mm)", "71_105DAI(in mm)"],
];

const CLIMATE_PERIODS = [
  ["Days 1–30", "D1_D30"],
  ["Days 31–60", "D31_D60"],
  ["Days 61–90", "D61_D90"],
  ["Days 91–120", "D91_D120"],
];

export default function ModelInputs({ meta, result }: { meta: Metadata; result: Prediction }) {
  const f = result.features;
  const v = (col: string) => {
    const x = f[col];
    return typeof x === "number" ? num(x) : x;
  };
  const block = f["Agriblock"] as string;

  return (
    <details className="card details">
      <summary>
        <span>
          <strong>What the model receives</strong>
          <span className="muted"> · {meta.metrics.feature_columns} inputs built from your 5 answers</span>
        </span>
      </summary>
      <p className="muted">
        In the training data, farm inputs are applied at fixed rates per hectare, the weather is the same for every
        farm in a block, and trash (straw) depends on the variety. The API fills in these values the same way, so
        you only need to give the five details above.
      </p>

      <div className="inputs-grid">
        <div>
          <h3>Farm inputs for {num(result.features["Hectares"] as number)} ha</h3>
          <table>
            <tbody>
              {Object.entries(meta.feature_builder.per_hectare).map(([col, rate]) => (
                <tr key={col}>
                  <th scope="row">{farmInputLabel(col)}</th>
                  <td className="num">{v(col)}</td>
                  <td className="muted small">{num(rate)} / ha</td>
                </tr>
              ))}
              <tr>
                <th scope="row">Trash (bundles)</th>
                <td className="num">{v("Trash(in bundles)")}</td>
                <td className="muted small">
                  {num(meta.feature_builder.trash_per_hectare_by_variety[f["Variety"] as string])} / ha
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div>
          <h3>{block} weather profile</h3>
          <table>
            <thead>
              <tr>
                <th scope="col">Period</th>
                <th scope="col" className="num">Temp °C</th>
                <th scope="col" className="num">Wind kn</th>
                <th scope="col" className="num">Humidity</th>
              </tr>
            </thead>
            <tbody>
              {CLIMATE_PERIODS.map(([name, p]) => (
                <tr key={p}>
                  <th scope="row">{name}</th>
                  <td className="num">{v(`Min temp_${p}`)}–{v(`Max temp_${p}`)}</td>
                  <td className="num">{v(`Inst Wind Speed_${p}(in Knots)`)} {v(`Wind Direction_${p}`)}</td>
                  <td className="num">{v(`Relative Humidity_${p}`)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
          <table>
            <thead>
              <tr>
                <th scope="col">Period</th>
                <th scope="col" className="num">Rain mm</th>
                <th scope="col" className="num">AI mm</th>
              </tr>
            </thead>
            <tbody>
              {RAIN_PERIODS.map(([name, rain, ai]) => (
                <tr key={name}>
                  <th scope="row">{name}</th>
                  <td className="num">{v(rain)}</td>
                  <td className="num">{v(ai)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted small">
            Variety {label(f["Variety"] as string)} · {label(f["Soil Types"] as string)} soil ·{" "}
            {label(f["Nursery"] as string)} nursery
          </p>
        </div>
      </div>
    </details>
  );
}
