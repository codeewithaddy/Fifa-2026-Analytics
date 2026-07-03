"""
utils/data_loader.py
FIFA World Cup 2026 — Data loading, cleaning, caching, and CSS injection.
"""

import re
import pathlib
import pandas as pd
import numpy as np
import streamlit as st

ROOT      = pathlib.Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "players.csv"

# ── Canonical team name mapping ───────────────────────────────────────────────
# Maps CSV / API variant names → the single canonical name used everywhere
# (flags dict, confederation map, page titles, etc.)
TEAM_NAME_MAP: dict[str, str] = {
    # CSV variants → canonical
    "Korea Republic":               "South Korea",
    "IR Iran":                      "Iran",
    "Türkiye":                      "Turkey",
    "Côte d'Ivoire":                "Ivory Coast",
    "C\u00f4te d'Ivoire":           "Ivory Coast",
    "Bosnia&Herz":                  "Bosnia and Herzegovina",
    "Bosnia–Herz":                  "Bosnia and Herzegovina",
    "Bosnia-Herzegovina":           "Bosnia and Herzegovina",
    "Cabo Verde":                   "Cape Verde",
    "Czechia":                      "Czech Republic",
    "Cura\u00e7ao":                 "Curacao",
    "Curaçao":                      "Curacao",
    "DR Congo":                     "Congo DR",
    "Democratic Republic of the Congo": "Congo DR",
    "Congo, DR":                    "Congo DR",
    "USA":                          "United States",
    "UAE":                          "United Arab Emirates",
}


# ── CSS Injector ──────────────────────────────────────────────
def inject_css() -> None:
    css_path = ROOT / "assets" / "style.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ── Age parser ("27-016" → 27) ────────────────────────────────
def _parse_age(val) -> float | None:
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    m = re.match(r"^(\d+)", str(val).strip())
    return float(m.group(1)) if m else None


# ── Raw load ──────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_raw() -> pd.DataFrame:
    """Load raw CSV and normalise team names to canonical form."""
    import os
    import streamlit as st
    
    # Authenticate with Kaggle if credentials in secrets
    try:
        if "KAGGLE_API_TOKEN" in st.secrets:
            os.environ["KAGGLE_API_TOKEN"] = st.secrets["KAGGLE_API_TOKEN"]
        if "KAGGLE_USERNAME" in st.secrets:
            os.environ["KAGGLE_USERNAME"] = st.secrets["KAGGLE_USERNAME"]
        if "KAGGLE_KEY" in st.secrets:
            os.environ["KAGGLE_KEY"] = st.secrets["KAGGLE_KEY"]
    except Exception:
        pass
        
    import kagglehub
    from kagglehub import KaggleDatasetAdapter
    
    try:
        df = kagglehub.load_dataset(
            KaggleDatasetAdapter.PANDAS,
            "swaptr/fifa-wc-2026-players",
            "players.csv"
        )
    except Exception as e:
        if DATA_PATH.exists():
            df = pd.read_csv(DATA_PATH, low_memory=False)
        else:
            st.error(f"**Critical Error: Failed to fetch Kaggle Data!**\n\nEnsure you added Kaggle credentials to the Streamlit Cloud Secrets.\n\n**Error:**\n```\n{e}\n```")
            st.stop()
            
    df["age"] = df["age"].apply(_parse_age)
    # Normalise team names so flags, confederation map, and display all match
    df["team"] = df["team"].map(lambda t: TEAM_NAME_MAP.get(str(t).strip(), str(t).strip()))
    if "team_country" in df.columns:
        df["team_country"] = df["team_country"].map(
            lambda t: TEAM_NAME_MAP.get(str(t).strip(), str(t).strip())
        )
    return df


# ── Outfield players (non-GK, minutes > 0) ───────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_outfield() -> pd.DataFrame:
    df = load_raw()
    df = df[df["minutes"].notna() & (df["minutes"] > 0)].copy()
    gk_mask = df["gk_games_starts"].fillna(0) > 0
    df = df[~gk_mask].copy()
    drop = [c for c in df.columns if c.startswith("gk_")]
    drop += [c for c in df.columns if df[c].isna().all()]
    drop += ["pens_won", "pens_conceded", "club"]
    df.drop(columns=[c for c in set(drop) if c in df.columns], inplace=True)
    num = df.select_dtypes(include="number").columns
    df[num] = df[num].fillna(0)
    df.reset_index(drop=True, inplace=True)
    return df


# ── Goalkeepers ───────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_goalkeepers() -> pd.DataFrame:
    df = load_raw()
    gk = df[df["gk_games_starts"].fillna(0) > 0].copy()
    gk = gk[gk["gk_minutes"].fillna(0) > 0].copy()
    cols = ["player", "team", "team_country", "age",
            "gk_games_starts", "gk_minutes", "gk_goals_against",
            "gk_goals_against_per90", "gk_shots_on_target_against",
            "gk_saves", "gk_save_pct", "gk_wins", "gk_ties",
            "gk_losses", "gk_clean_sheets", "gk_clean_sheets_pct"]
    available = [c for c in cols if c in gk.columns]
    gk = gk[available].copy()
    num = gk.select_dtypes(include="number").columns
    gk[num] = gk[num].fillna(0)
    return gk.reset_index(drop=True)


# ── Team aggregates ───────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_team_stats() -> pd.DataFrame:
    df = load_outfield()
    agg = df.groupby("team").agg(
        players           = ("player",             "count"),
        total_goals       = ("goals",              "sum"),
        total_assists     = ("assists",             "sum"),
        total_shots       = ("shots",              "sum"),
        total_shots_on_target = ("shots_on_target","sum"),
        total_minutes     = ("minutes",            "sum"),
        avg_goals_per90   = ("goals_per90",         "mean"),
        avg_assists_per90 = ("assists_per90",        "mean"),
        avg_shots_per90   = ("shots_per90",          "mean"),
        total_yellow      = ("cards_yellow",         "sum"),
        total_red         = ("cards_red",            "sum"),
        total_fouls       = ("fouls",               "sum"),
        total_fouled      = ("fouled",              "sum"),
        total_interceptions=("interceptions",        "sum"),
        total_tackles_won = ("tackles_won",          "sum"),
        avg_plus_minus    = ("plus_minus_per90",     "mean"),
    ).reset_index()

    agg["goals_per_shot"] = (
        agg["total_goals"] / agg["total_shots"].replace(0, np.nan)
    ).fillna(0).round(3)

    # Confederation map
    conf_map = {
        "UEFA": ["England","France","Germany","Spain","Portugal","Italy",
                 "Netherlands","Belgium","Croatia","Denmark","Poland",
                 "Switzerland","Austria","Serbia","Czech Republic","Slovakia",
                 "Hungary","Romania","Slovenia","Albania","Scotland","Wales",
                 "Turkey","Ukraine","Sweden","Norway","Finland","Greece",
                 "Bosnia and Herzegovina","Montenegro","Kosovo","Georgia"],
        "CONMEBOL": ["Brazil","Argentina","Colombia","Uruguay","Chile",
                     "Ecuador","Bolivia","Peru","Paraguay","Venezuela"],
        "CONCACAF": ["United States","Mexico","Canada","Costa Rica","Honduras",
                     "Jamaica","Panama","Guatemala","El Salvador","Haiti",
                     "Trinidad and Tobago","Cuba"],
        "CAF": ["Morocco","Senegal","Nigeria","Ghana","Cameroon","Egypt",
                "Algeria","Tunisia","Ivory Coast","South Africa","Mali",
                "Burkina Faso","Congo DR","Guinea","Cape Verde"],
        "AFC": ["Japan","South Korea","Saudi Arabia","Iran","Australia",
                "Qatar","Iraq","Uzbekistan","Jordan","Oman","Indonesia"],
        "OFC": ["New Zealand","Fiji"],
    }
    inv = {c: conf for conf, countries in conf_map.items()
           for c in countries}
    agg["confederation"] = agg["team"].map(inv).fillna("Other")
    return agg


@st.cache_data(ttl=300, show_spinner=False)
def player_list() -> list[str]:
    return sorted(load_outfield()["player"].unique().tolist())


# ── Plain-English label helpers ───────────────────────────────
def performance_label(delta: float) -> str:
    """Convert goal delta into a plain-English label."""
    if delta >= 2.5:   return "🔥 World Class Finisher"
    if delta >= 1.0:   return "✅ Clinical"
    if delta >= 0.0:   return "On Expected Level"
    if delta >= -1.0:  return "⚠️ Slightly Unlucky"
    return "❌ Missing Big Chances"


def team_style_label(goals_per_shot: float, shots_per_player: float) -> str:
    """Label a team's attacking style from two numbers."""
    high_conv  = goals_per_shot > 0.18
    high_shots = shots_per_player > 3.5
    if high_conv and high_shots:   return "⚡ Clinical & Active"
    if high_conv and not high_shots: return "🎯 Lethal — Few Shots Needed"
    if not high_conv and high_shots: return "😤 Wasteful — Lots of Shots"
    return "🛡️ Defensive — Low Output"


# ── Tournament constants ──────────────────────────────────────
MAX_GAMES = 7


def get_games_played() -> int:
    """
    Dynamically determine how many group-stage games have been played
    by reading the api_cache.json instead of relying on a hardcoded number.
    """
    try:
        from utils.api_client import get_games_played_count
        return get_games_played_count()
    except Exception:
        return 3


# Backwards-compatible constant (lazy — evaluated at import time)
GAMES_PLAYED = 3  # kept for any direct imports; prefer get_games_played()
