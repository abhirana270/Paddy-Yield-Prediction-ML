"""Paddy Yield Prediction API (FastAPI, deployed as a Vercel Python function).

The models are trained offline by training/export_model.py and stored as
plain parameters in model.json, so inference here is a few lines of maths
with no pandas / scikit-learn dependency.

Local run (from webapp/):  uvicorn api.index:app --reload --port 8000
"""

import json
import math
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

MODEL = json.loads((Path(__file__).parent / "model.json").read_text())
INPUTS = MODEL["inputs"]
BUILDER = MODEL["feature_builder"]

app = FastAPI(
    title="Paddy Yield Prediction API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
# Frontend and API share an origin on Vercel; CORS only matters if the API
# is called from another site.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"])


class PredictRequest(BaseModel):
    hectares: float = Field(..., gt=0, le=100, examples=[4])
    agriblock: str = Field(..., examples=["Cuddalore"])
    variety: str = Field(..., examples=["CO_43"])
    soil_type: str = Field(..., examples=["alluvial"])
    nursery: Literal["dry", "wet"] = Field(..., examples=["dry"])


def build_features(req: PredictRequest) -> dict:
    """Expand the 5 user inputs into the 44 columns the model was trained on."""
    for value, key in [(req.agriblock, "Agriblock"), (req.variety, "Variety"), (req.soil_type, "Soil Types")]:
        if value not in INPUTS[key]:
            raise HTTPException(422, f"Unknown {key} '{value}'. Expected one of {INPUTS[key]}")

    row = {
        "Hectares": req.hectares,
        "Agriblock": req.agriblock,
        "Variety": req.variety,
        "Soil Types": req.soil_type,
        "Nursery": req.nursery,
        "Trash(in bundles)": BUILDER["trash_per_hectare_by_variety"][req.variety] * req.hectares,
    }
    for col, rate in BUILDER["per_hectare"].items():
        row[col] = round(rate * req.hectares, 4)
    row.update(BUILDER["block_profiles"][req.agriblock])
    return row


def transform(row: dict, prep: dict) -> list[float]:
    """StandardScaler on numeric columns + one-hot on categorical ones."""
    vec = [(row[c["name"]] - c["mean"]) / c["scale"] for c in prep["numeric"]]
    for c in prep["categorical"]:
        vec.extend(1.0 if str(row[c["name"]]) == cat else 0.0 for cat in c["categories"])
    return vec


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def predict_category(row: dict) -> dict[str, float]:
    x = transform(row, MODEL["preprocessing"])
    clf = MODEL["classifier"]
    logits = [dot(w, x) + b for w, b in zip(clf["coef"], clf["intercept"])]
    top = max(logits)
    exps = [math.exp(v - top) for v in logits]
    total = sum(exps)
    return {cls: e / total for cls, e in zip(MODEL["classes"], exps)}


def predict_kg(row: dict) -> float:
    x = transform(row, MODEL["regressor_preprocessing"])
    reg = MODEL["regressor"]
    return dot(reg["coef"], x) + reg["intercept"]


@app.get("/api/health")
def health():
    return {"status": "ok", "model_version": MODEL["version"]}


@app.get("/api/metadata")
def metadata():
    """Form options, category ranges, derived-input rules and model metrics."""
    edges = MODEL["category_edges_kg"]
    return {
        "inputs": {
            "hectares": INPUTS["hectares"],
            "agriblock": INPUTS["Agriblock"],
            "variety": INPUTS["Variety"],
            "soil_type": INPUTS["Soil Types"],
            "nursery": INPUTS["Nursery"],
        },
        "categories": [
            {"label": cls, "min_kg": edges[i], "max_kg": edges[i + 1]}
            for i, cls in enumerate(MODEL["classes"])
        ],
        "feature_builder": BUILDER,
        "metrics": MODEL["metrics"],
    }


@app.post("/api/predict")
def predict(req: PredictRequest):
    row = build_features(req)
    probs = predict_category(row)
    category = max(probs, key=probs.get)
    kg = predict_kg(row)
    h = INPUTS["hectares"]
    return {
        "category": category,
        "confidence": round(probs[category], 4),
        "probabilities": {k: round(v, 4) for k, v in probs.items()},
        "estimated_yield_kg": round(kg),
        "estimated_yield_per_hectare_kg": round(kg / req.hectares),
        "model": "Logistic Regression",
        "out_of_training_range": not (h["min"] <= req.hectares <= h["max"]),
        "features": row,
    }
