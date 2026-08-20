# Estimator — Home Value Prediction

An end-to-end regression project: **synthetic dataset → cleaning & EDA →
model comparison → Flask API → blueprint-themed web UI.** Every number the
frontend shows comes from a real `scikit-learn` pipeline behind a real HTTP
call — nothing is hardcoded.

## Overview

| Layer        | Tech                                    | What it does                                                                  |
| ------------ | ---------------------------------------- | ------------------------------------------------------------------------------ |
| **Model**    | Python, pandas, scikit-learn, Jupyter    | Cleans a messy synthetic housing dataset, compares 3 regressors, exports the winner |
| **Backend**  | Flask, plain Python validation           | Loads the pipeline once at startup, validates input, serves `/api/estimate`, `/api/health`, `/api/metrics` |
| **Frontend** | Plain HTML/CSS/JS, no build step         | A "drafting table" layout: survey form + live annotated blueprint result panel |

## Project structure

```
├── backend/
│   ├── app/
│   │   ├── api/routes.py              # /api/health, /api/estimate, /api/metrics
│   │   ├── core/config.py             # env-driven settings
│   │   ├── schemas/estimate.py        # request validation (no external lib)
│   │   ├── services/
│   │   │   ├── inference.py           # loads the pkl, predicts, confidence range, top factors
│   │   │   └── preprocessing.py       # request -> one-row DataFrame
│   │   └── __init__.py                # app factory, lightweight CORS
│   ├── models/
│   │   ├── home_value_pipeline.pkl    # trained pipeline (committed, ~6MB)
│   │   └── model_metrics.json         # test-set metrics from the notebook
│   ├── tests/test_estimate.py
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
│
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   ├── js/config.js                   # API_BASE_URL, read from a <meta> tag
│   ├── js/app.js                      # form handling + rendering, no build step
│   └── assets/
│       ├── neighborhoods.json         # dropdown options, exported by the notebook
│       └── model_metrics.json         # hero stats
│
├── notebooks/
│   ├── generate_data.py               # synthesizes the dataset
│   ├── home_value_model.ipynb         # cleaning -> EDA -> training -> export
│   └── data/homes.csv
│
└── README.md
```

## About the dataset

There's no real housing dataset behind this — `notebooks/generate_data.py`
synthesizes an **8,000-row dataset** with its own messiness, built for this
project: prices mixed between `"$287.7K"` strings and plain numbers, living
area mixed between `sqft` and `sqm`, and missing values scattered across a
few columns on purpose. The notebook cleans all of it before training.

To swap in a real dataset, point `pd.read_csv(...)` at your own CSV with a
matching column set (see `FEATURES` in the notebook) and re-run top to
bottom, then re-export the pipeline into `backend/models/`.

## Model results

| Model             | MAE        | RMSE       | R²        |
| ----------------- | ---------- | ---------- | --------- |
| Ridge              | higher     | higher     | lower     |
| **RandomForest (exported)** | **$29,499** | **$41,959** | **0.935** |
| ExtraTrees         | close second | close second | close second |

5-fold cross-validation R² on RandomForest: **0.940 ± 0.002**. A
`log1p(price)` target transform was also tested — it did not beat the plain
target here, and the notebook says so rather than assuming the "usual
trick" always helps.

Full details, plots, and commentary:
[`notebooks/home_value_model.ipynb`](notebooks/home_value_model.ipynb).

## Running it locally

### 1. Train (optional — a trained pipeline is already committed)

```bash
cd notebooks
python generate_data.py
jupyter nbconvert --to notebook --execute home_value_model.ipynb
```

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
python run.py
# -> http://localhost:8000/api/health
```

Run the tests:

```bash
pytest tests/ -v
```

### 3. Frontend

No build step. Just needs to be served (not opened as `file://`):

```bash
cd frontend
python -m http.server 5500
# -> http://localhost:5500
```

If your backend runs somewhere other than `http://localhost:8000`, change
the `<meta name="api-base-url" content="...">` tag in `frontend/index.html`.

### Environment variables (backend/.env)

| Variable       | Default                              | Purpose                                    |
| -------------- | -------------------------------------- | -------------------------------------------- |
| `MODEL_PATH`   | `models/home_value_pipeline.pkl`      | Path to the trained pipeline                |
| `METRICS_PATH` | `models/model_metrics.json`           | Path to the notebook's exported metrics     |
| `CORS_ORIGINS` | `http://localhost:5500,...`           | Origins allowed to call the API             |
| `LOG_LEVEL`    | `INFO`                                | Python logging level                        |

## API reference

### `GET /api/health`

```json
{ "status": "ok", "model_loaded": true, "model_name": "RandomForest", "model_version": "0.1.0" }
```

### `POST /api/estimate`

```bash
curl -X POST http://localhost:8000/api/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "neighborhood": "Brookhaven",
    "sqft_living": 1850,
    "lot_size_sqft": 5500,
    "bedrooms": 3,
    "bathrooms": 2,
    "floors": 2,
    "year_built": 2005,
    "renovated": "N",
    "condition": 4,
    "grade": 7,
    "garage": "Y",
    "basement": "N",
    "pool": "N",
    "school_score": 7
  }'
```

```json
{
  "estimated_value": 409000.0,
  "estimated_value_formatted": "$409,000",
  "currency": "USD",
  "range_low": 367000.0,
  "range_high": 450900.0,
  "neighborhood_used": "Brookhaven",
  "model_name": "RandomForest",
  "model_version": "0.1.0",
  "top_factors": [
    { "label": "Neighborhood", "importance_pct": 49.5 },
    { "label": "Living area", "importance_pct": 44.2 }
  ]
}
```

`neighborhood` values outside the model's trained set are bucketed as
`"other"` — the response's `neighborhood_used` field shows which bucket was
used. Invalid input (out-of-range numbers, a missing field, etc.) returns
`422` with a field-by-field explanation.

`range_low`/`range_high` are the point estimate ± the model's held-out
RMSE. `top_factors` are the trained model's real `feature_importances_`,
rolled up to human-readable labels.

### `GET /api/metrics`

Returns the full metrics JSON exported by the notebook (MAE, RMSE, R²,
cross-validation stats).

## Design notes

- **The backend reads its known-neighborhood list from the pickle itself**
  (`OneHotEncoder.categories_`), so it can't drift out of sync with what the
  model was actually trained on.
- **The model loads once**, at process startup, not on every request.
- **CORS is hand-rolled** (an `after_request` hook checking `CORS_ORIGINS`)
  instead of a dependency, to keep the backend footprint small.
- **The frontend has no build step** — vanilla HTML/CSS/JS, so it can be
  opened in any static file server.
