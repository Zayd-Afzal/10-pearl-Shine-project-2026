# Islamabad AQI Predictor

A serverless MLOps system that predicts next-hour Air Quality Index for Islamabad. Weather data from Open-Meteo lands in a Hopsworks feature store, an XGBoost model is trained and versioned in the model registry, and a Streamlit dashboard serves live predictions.

---

## How It Works

```
Open-Meteo API
     │
BackFillOpenMeteo.py  ──>  Hopsworks Feature Store (islamabad_aqi_features v2)
FeaturePipeline.py    ──>  (incremental hourly updates)
     │
TrainModel.py  ──>  model tournament (Ridge / MLP / XGBoost)
               ──>  winner registered to Hopsworks Model Registry
     │
     
app.py (Streamlit)  ──>  fetches latest model + feature data at startup
```

**Run order (first time only):**
1. `BackFillOpenMeteo.py` — historical data backfill
2. `TrainModel.py` — train and register the model
3. `app.py` — dashboard is now functional
4. Schedule steps 1–2 via GitHub Actions for fully automated operation

---

## Project Structure

```
├── app.py                   # Streamlit dashboard
├── BackFillOpenMeteo.py     # One-time historical data fetch
├── FeaturePipeline.py       # Incremental feature updates
├── TrainModel.py            # Model training & registration
└── .github/workflows/       # GitHub Actions automation
    ├── feature_pipeline.yml # Hourly data ingestion
    └── retrain_daily.yml    # Daily model retraining
```

---

## Features

- **Next-Hour AQI Forecast** — runs model.predict() on the latest feature vector with one click
- **Live Telemetry** — current AQI, PM2.5, temperature, and humidity pulled from the feature store
- **Traffic & Time Analysis** — hourly AQI profile showing morning and evening rush-hour peaks
- **Weather Correlation Explorer** — interactive feature timelines + correlation coefficients
- **Explainable AI (SHAP)** — summary plot showing which features the model relies on most

---

## Models

`TrainModel.py` runs an automated tournament across three models and picks the lowest RMSE:

| Model | Notes |
|-------|-------|
| Ridge Regression | Linear baseline |
| MLP (Neural Net) | Two hidden layers (64 → 32) |
| XGBoost | Usually wins; tree-based, handles non-linearities well |

Split is chronological (80/20) to prevent temporal leakage. The champion is saved to the Hopsworks Model Registry with RMSE and R² logged as metadata.

---

## Setup

### Prerequisites
- Python 3.10+
- Hopsworks account (free tier or pay-as-you-go)
- GitHub repository with Actions enabled

### Install dependencies

```bash
pip install -r requirements.txt
```

### Hopsworks API Key

Get your key from [app.hopsworks.ai](https://app.hopsworks.ai) → Account → API Keys.

**For local development**, create `.streamlit/secrets.toml`:
```toml
HOPSWORKS_API_KEY = "your_key_here"
```

**For Streamlit Community Cloud**, add it under App Settings → Secrets.

**For GitHub Actions**, add it as a repository secret named `HOPSWORKS_API_KEY`.

### Run locally

```bash
# 1. Backfill historical data (first time only)
python BackFillOpenMeteo.py

# 2. Train and register the model (first time only)
python TrainModel.py

# 3. Launch the dashboard
streamlit run app.py
```

---

## AQI Categories

| AQI | Category | Who's at risk |
|-----|----------|--------------| 
| 0–50 | Good 🟢 | Nobody |
| 51–100 | Moderate 🟡 | Unusually sensitive people |
| 101–150 | Unhealthy for Sensitive Groups 🟠 | Sensitive groups |
| 151–200 | Unhealthy 🔴 | Everyone |
| 201+ | Very Unhealthy 🟣 | Everyone, seriously |

---

## Automation (GitHub Actions)

| Workflow | Schedule | What It Does |
|----------|----------|--------------|
| `feature_pipeline.yml` | Every hour | Fetches latest Open-Meteo data, appends to feature store |
| `retrain_daily.yml` | Daily at 02:00 UTC | Retrains all three models, registers new champion |

---

## Tech Stack

- **Data** — Open-Meteo API (no key required)
- **Feature Store / Model Registry** — Hopsworks Cloud
- **ML** — XGBoost, scikit-learn, SHAP
- **Dashboard** — Streamlit
- **Automation** — GitHub Actions
- **Author** — Rayan Shahid
