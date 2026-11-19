# NexTrade

NexTrade is a Streamlit dashboard and research project for Nifty 50 market-regime
classification and backtesting. It displays the saved project results; opening the
dashboard does not train models or place trades.

## Live dashboard

Visit the public dashboard: [nextrade-vs1.streamlit.app](https://nextrade-vs1.streamlit.app/).

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

## Repository contents

The nested `NexTrade_Project` directory is a duplicate copy and is excluded from
Git. Local browser-profile data, build caches, virtual environments, and secrets
are also excluded. Project data, reports, model artifacts, scripts, and tests are
retained for reproducibility and for the dashboard.
