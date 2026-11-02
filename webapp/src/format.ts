const nf = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 2 });

export const num = (n: number) => nf.format(n);

export const kg = (n: number) => `${nf.format(Math.round(n))} kg`;

export const pct = (n: number, digits = 1) => `${(n * 100).toFixed(digits)}%`;

/** "delux ponni" -> "Delux Ponni", "CO_43" -> "CO 43" */
export const label = (s: string) =>
  s.replace(/_/g, " ").replace(/\b[a-z]/g, (c) => c.toUpperCase());

const FARM_INPUT_LABELS: Record<string, string> = {
  "Seedrate(in Kg)": "Seed rate (kg)",
  "LP_Mainfield(in Tonnes)": "Land prep, main field (t)",
  "Nursery area (Cents)": "Nursery area (cents)",
  "LP_nurseryarea(in Tonnes)": "Land prep, nursery (t)",
  DAP_20days: "DAP at 20 days",
  Weed28D_thiobencarb: "Thiobencarb at 28 days",
  Urea_40Days: "Urea at 40 days",
  Potassh_50Days: "Potash at 50 days",
  Micronutrients_70Days: "Micronutrients at 70 days",
  "Pest_60Day(in ml)": "Pesticide at 60 days (ml)",
};

export const farmInputLabel = (col: string) => FARM_INPUT_LABELS[col] ?? col.replace(/_/g, " ");
