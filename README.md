# NexTrade

NexTrade is a Streamlit dashboard and research project for Nifty 50 market-regime
classification and backtesting. It displays the saved project results; opening the
dashboard does not train models or place trades.

## Run locally (Windows)

From the project root, create and activate a virtual environment, install the
dashboard dependencies, then launch Streamlit:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r dashboard\requirements.txt
python -m streamlit run dashboard\app.py
```

The dashboard uses the included `data/`, `reports/`, and `config/` files.

## Deploy on Render

The root `render.yaml` defines a free Render web service, installs the dashboard
dependencies, and runs Streamlit on Render's assigned port.

1. Sign in to [Render](https://dashboard.render.com/) and connect GitHub.
2. Create a **Blueprint** from the private `Viishall31/NexTrade` repository.
3. Review the `nextrade-dashboard` service and deploy it.

The GitHub repository stays private, but the Render web-service URL is publicly
accessible. Render's free service may spin down after inactivity, so the first
request after a quiet period can take about a minute. Do not upload secrets or
personal data to a publicly accessible dashboard.

## Repository contents

The nested `NexTrade_Project` directory is a duplicate copy and is excluded from
Git. Local browser-profile data, build caches, virtual environments, and secrets
are also excluded. Project data, reports, model artifacts, scripts, and tests are
retained for reproducibility and for the dashboard.
