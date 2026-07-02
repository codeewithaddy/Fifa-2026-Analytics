# ⚽ FIFA 2026 Intelligence Hub

> A data-driven analytics dashboard for the FIFA 2026 World Cup — built with Python, Streamlit, and scikit-learn.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.58-red?logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What is this?

This is **not** a simple score tracker. The FIFA 2026 Intelligence Hub gives viewers genuinely unique, data-science-powered insights into the World Cup:

| Feature | Description |
|---------|-------------|
| **xG Engine** | ML-based Expected Goals/Assists — find who's "lucky" vs. truly clinical |
| **Player Scout** | Head-to-head radar chart comparisons (like FBref / Sofascore) |
| **Golden Boot Predictor** | Goal projections based on math, not media hype |
| **Team DNA** | Which teams punch above their weight? Clinical vs. wasteful analysis |

All powered by a dataset of **1,247 players × 72 stats**, auto-refreshed daily from Kaggle.

---

## Tech Stack

- **Frontend:** Streamlit (multi-page app)
- **Data:** Pandas, NumPy
- **ML:** scikit-learn (Linear Regression for xG/xA)
- **Visualization:** Plotly (interactive charts with hover tooltips)
- **Deployment:** Render (cloud hosting, daily cron refresh)
- **Data Source:** Kaggle FIFA 2026 World Cup dataset

---

## Project Structure

```
fifa-2026-analytics/
├── app.py                     # Main Streamlit entry point
├── pages/
│   ├── 1_xG_Engine.py         # ML Expected Goals leaderboard
│   ├── 2_Player_Scout.py      # Player comparison + radar chart
│   ├── 3_Golden_Boot.py       # Goal projection predictor
│   └── 4_Team_DNA.py          # Team style & performance analysis
├── utils/
│   ├── data_loader.py         # Kaggle API download + caching
│   ├── ml_model.py            # Linear Regression xG/xA model
│   └── charts.py              # Reusable Plotly chart functions
├── data/
│   └── players.csv            # Auto-refreshed daily via Kaggle API
├── refresh_data.py            # Standalone data refresh script
├── requirements.txt           # Python dependencies
├── render.yaml                # Render deployment config
└── .gitignore
```

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/fifa-2026-analytics.git
cd fifa-2026-analytics

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
.\venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your Kaggle credentials
# Place kaggle.json in project root (or set KAGGLE_USERNAME & KAGGLE_KEY env vars)

# 5. Download the dataset
python refresh_data.py

# 6. Run the dashboard
streamlit run app.py
```

---

## Daily Data Refresh

The dashboard auto-refreshes its dataset via the Kaggle API. On Render, this runs as a daily cron job at midnight UTC. Set these environment variables in your Render dashboard:

- `KAGGLE_USERNAME` — Your Kaggle username
- `KAGGLE_KEY` — Your Kaggle API key

---

## Screenshots

*Coming soon — dashboard is under active development.*

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ☕ and data science. Not affiliated with FIFA.*
# Fifa-2026-Analytics
