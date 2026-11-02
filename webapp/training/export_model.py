"""Train the paddy yield models and export them to api/model.json.

Mirrors paddy_project.py (drop duplicates, 3 equal-size yield categories,
80/20 stratified split, scaling + one-hot encoding), then exports the
fitted parameters as plain JSON so the API can predict without pandas or
scikit-learn installed (keeps the Vercel function small).

Run from the webapp/ folder:
    pip install -r training/requirements.txt
    python training/export_model.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             mean_absolute_error, r2_score)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "dataset" / "paddydataset.csv"
OUT = Path(__file__).resolve().parents[1] / "api" / "model.json"

TARGET = "Paddy yield(in Kg)"
CLASSES = ["Low", "Medium", "High"]
USER_INPUTS = ["Hectares", "Agriblock", "Variety", "Soil Types", "Nursery"]


def load():
    df = pd.read_csv(DATASET).drop_duplicates()
    df.columns = df.columns.str.strip()
    return df.reset_index(drop=True)


def feature_builder(df, X):
    """Work out how every model column follows from the 5 user inputs.

    In this dataset farm inputs are fixed per-hectare rates, weather is fixed
    per Agriblock and trash per hectare depends on the variety. The asserts
    make the export fail loudly if a new dataset breaks those assumptions.
    """
    num_cols = X.select_dtypes(include="number").columns
    per_hectare = {}
    for col in num_cols:
        if col == "Hectares":
            continue
        rates = (df[col] / df["Hectares"]).round(4).unique()
        if len(rates) == 1:
            per_hectare[col] = float(rates[0])

    weather_cols = [c for c in X.columns
                    if c not in USER_INPUTS and c not in per_hectare and c != "Trash(in bundles)"]
    assert (df.groupby("Agriblock")[weather_cols].nunique() == 1).all().all(), \
        "weather columns are not constant per Agriblock"
    block_profiles = {
        block: {c: (v.item() if hasattr(v, "item") else v) for c, v in row.items()}
        for block, row in df.groupby("Agriblock")[weather_cols].first().iterrows()
    }

    trash_rate = (df["Trash(in bundles)"] / df["Hectares"]).groupby(df["Variety"])
    trash_per_hectare = {v: float(s.mode().iloc[0]) for v, s in trash_rate}

    covered = set(USER_INPUTS) | set(per_hectare) | set(weather_cols) | {"Trash(in bundles)"}
    assert covered == set(X.columns), set(X.columns) - covered
    return per_hectare, block_profiles, trash_per_hectare


def build_preprocessor(X):
    cat_cols = X.select_dtypes(exclude="number").columns.tolist()
    num_cols = X.select_dtypes(include="number").columns.tolist()
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ])
    pre = ColumnTransformer([
        ("num", num_pipeline, num_cols),
        ("cat", cat_pipeline, cat_cols),
    ])
    return pre, num_cols, cat_cols


def export_preprocessing(pre, num_cols, cat_cols):
    scaler = pre.named_transformers_["num"].named_steps["scaler"]
    encoder = pre.named_transformers_["cat"].named_steps["encoder"]
    return {
        "numeric": [{"name": c, "mean": float(m), "scale": float(s)}
                    for c, m, s in zip(num_cols, scaler.mean_, scaler.scale_)],
        "categorical": [{"name": c, "categories": [str(v) for v in cats]}
                        for c, cats in zip(cat_cols, encoder.categories_)],
    }


def main():
    df = load()
    df["Yield Category"], edges = pd.qcut(df[TARGET], q=3, labels=CLASSES, retbins=True)

    X = df.drop(columns=[TARGET, "Yield Category"])
    y = df["Yield Category"].astype(str)
    per_hectare, block_profiles, trash_per_hectare = feature_builder(df, X)

    X_train, X_test, y_train, y_test, yk_train, yk_test = train_test_split(
        X, y, df[TARGET], test_size=0.2, random_state=42, stratify=y)

    candidates = {
        "Logistic Regression": LogisticRegression(max_iter=2000),
        "SVM": SVC(kernel="rbf"),
        "Naive Bayes": GaussianNB(),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "Decision Tree": DecisionTreeClassifier(max_depth=8, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
    }
    _, num_cols, cat_cols = build_preprocessor(X)
    comparison, fitted = [], {}
    for name, clf in candidates.items():
        pre = build_preprocessor(X)[0]
        model = Pipeline([("preprocessing", pre), ("classifier", clf)]).fit(X_train, y_train)
        pred = model.predict(X_test)
        comparison.append({
            "model": name,
            "accuracy": round(accuracy_score(y_test, pred), 4),
            "f1_macro": round(f1_score(y_test, pred, average="macro"), 4),
        })
        fitted[name] = (model, pred)
        print(f"{name:20s} accuracy={comparison[-1]['accuracy']:.4f}")

    # Deployed classifier: Logistic Regression (best model in the original project)
    lr_model, lr_pred = fitted["Logistic Regression"]
    pre = lr_model.named_steps["preprocessing"]
    lr = lr_model.named_steps["classifier"]
    order = [list(lr.classes_).index(c) for c in CLASSES]
    coef, intercept = lr.coef_[order], lr.intercept_[order]

    # Companion regressor so the app can show an estimated yield in kg
    pre_r = build_preprocessor(X)[0]
    reg_model = Pipeline([("preprocessing", pre_r), ("regressor", LinearRegression())]).fit(X_train, yk_train)
    reg_pred = reg_model.predict(X_test)
    reg = reg_model.named_steps["regressor"]

    # Sanity check: the plain-maths version must match scikit-learn exactly
    Z = pre.transform(X_test)
    Z = Z.toarray() if hasattr(Z, "toarray") else Z
    logits = Z @ coef.T + intercept
    probs = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs /= probs.sum(axis=1, keepdims=True)
    assert np.allclose(probs, lr_model.predict_proba(X_test)[:, order], atol=1e-9)
    assert np.allclose(Z @ reg.coef_ + reg.intercept_, reg_pred)

    model = {
        "version": 1,
        "classes": CLASSES,
        "category_edges_kg": [round(float(e), 2) for e in edges],
        "preprocessing": export_preprocessing(pre, num_cols, cat_cols),
        "classifier": {
            "type": "logistic_regression",
            "coef": coef.round(10).tolist(),
            "intercept": intercept.round(10).tolist(),
        },
        "regressor_preprocessing": export_preprocessing(pre_r, num_cols, cat_cols),
        "regressor": {
            "type": "linear_regression",
            "coef": reg.coef_.round(10).tolist(),
            "intercept": float(reg.intercept_),
        },
        "feature_builder": {
            "per_hectare": per_hectare,
            "trash_per_hectare_by_variety": trash_per_hectare,
            "block_profiles": block_profiles,
        },
        "inputs": {
            "hectares": {"min": float(X["Hectares"].min()), "max": float(X["Hectares"].max())},
            "Agriblock": sorted(X["Agriblock"].unique().tolist()),
            "Variety": sorted(X["Variety"].unique().tolist()),
            "Soil Types": sorted(X["Soil Types"].unique().tolist()),
            "Nursery": sorted(X["Nursery"].unique().tolist()),
        },
        "metrics": {
            "rows_raw": int(len(pd.read_csv(DATASET))),
            "rows_after_dedup": int(len(df)),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "feature_columns": int(X.shape[1]),
            "comparison": sorted(comparison, key=lambda r: -r["accuracy"]),
            "confusion_matrix": {
                "labels": CLASSES,
                "matrix": confusion_matrix(y_test, lr_pred, labels=CLASSES).tolist(),
            },
            "regressor": {
                "r2": round(r2_score(yk_test, reg_pred), 4),
                "mae_kg": round(mean_absolute_error(yk_test, reg_pred), 1),
            },
            "yield_per_hectare_kg": {
                "min": round(float((df[TARGET] / df["Hectares"]).min()), 1),
                "mean": round(float((df[TARGET] / df["Hectares"]).mean()), 1),
                "max": round(float((df[TARGET] / df["Hectares"]).max()), 1),
            },
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(model, indent=1))
    print(f"Regressor R2={model['metrics']['regressor']['r2']} MAE={model['metrics']['regressor']['mae_kg']} kg")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
