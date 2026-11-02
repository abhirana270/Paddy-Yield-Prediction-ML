# Paddy Yield Predictor — Web App

A React frontend and a FastAPI backend for the paddy yield model in this repository. Both deploy together as a single Vercel project.

```
webapp/
├── api/
│   ├── index.py          FastAPI app (Vercel Python function)
│   └── model.json        Exported model parameters (generated)
├── training/
│   ├── export_model.py   Trains the models and writes api/model.json
│   └── requirements.txt  Training-only dependencies (pandas, scikit-learn)
├── src/                  React + TypeScript frontend (Vite)
├── requirements.txt      Runtime dependencies for the API (FastAPI only)
└── vercel.json
```

## How it works

- **5 inputs, 44 features.** In the dataset, every farm input (seed, fertiliser, pesticide…) is a fixed rate per hectare, the weather is identical for every farm in an Agriblock, and trash depends on the variety. The user enters farm area, block, variety, soil type and nursery. The API rebuilds the full 44-column row the model was trained on, and reproduces 2,337 of the 2,338 dataset rows exactly.
- **Classifier:** Logistic Regression, the model chosen in the original project. It reaches 87.4% accuracy on the 80/20 stratified test split and outputs Low, Medium or High with class probabilities.
- **Yield estimate:** a companion Linear Regression on the same features predicts total yield in kg (test R² 0.989, mean absolute error about 750 kg).
- **No ML libraries at runtime.** `training/export_model.py` saves the scaler, encoder and model weights to `api/model.json`. The API applies them with plain Python, so the Vercel function only installs FastAPI. The export script checks that this gives the same results as scikit-learn.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/metadata` | Form options, category ranges, feature rules, model metrics |
| POST | `/api/predict` | Predict yield category and kg |
| GET | `/api/docs` | Interactive Swagger docs |

```bash
curl -X POST https://<your-app>.vercel.app/api/predict \
  -H "Content-Type: application/json" \
  -d '{"hectares": 4, "agriblock": "Cuddalore", "variety": "CO_43", "soil_type": "alluvial", "nursery": "dry"}'
```

```json
{
  "category": "Medium",
  "confidence": 0.996,
  "probabilities": { "Low": 0.0029, "Medium": 0.996, "High": 0.0011 },
  "estimated_yield_kg": 24122,
  "estimated_yield_per_hectare_kg": 6030,
  "model": "Logistic Regression",
  "out_of_training_range": false,
  "features": { "...": "all 44 model inputs" }
}
```

Valid values: `agriblock` is one of Chinnasalem, Cuddalore, Kallakurichi, Kurinjipadi, Panruti or Sankarapuram. `variety` is `CO_43`, `delux ponni` or `ponmani`. `soil_type` is `alluvial` or `clay`, and `nursery` is `dry` or `wet`. The training data covers farms of 1–6 hectares.

## Run locally

Run both of these from the `webapp/` folder, in two terminals:

```bash
# 1. API on http://localhost:8000
pip install -r requirements.txt uvicorn
uvicorn api.index:app --reload --port 8000

# 2. Frontend on http://localhost:5173 (proxies /api to :8000)
npm install
npm run dev
```

## Deploy to Vercel

1. Import the GitHub repository in Vercel.
2. Set **Root Directory** to `webapp`. This is required, because the repository root holds the training project.
3. Leave the remaining settings alone. `vercel.json` sets the Vite build, the `dist` output folder and the `/api/*` routing to the Python function.
4. Click **Deploy**.

To deploy from the CLI instead, run `cd webapp && npx vercel --prod`.

## Retraining

If the dataset changes, regenerate the model file and commit it:

```bash
pip install -r training/requirements.txt
python training/export_model.py
```

The script fails loudly if the data no longer fits the derived-feature rules, for example if a block's weather starts to vary between farms.
