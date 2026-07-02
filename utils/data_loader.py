"""
utils/data_loader.py
FIFA 2026 Intelligence Hub — Data loading, cleaning, and caching.
"""

import re
import pathlib
import pandas as pd
import streamlit as st

# ── Path resolution ──────────────────────────────────────────
ROOT = pathlib.Path(__file__).parent.parent
DATA_PATH = ROOT / "data" / "players.csv"


# ── CSS Injector ─────────────────────────────────────────────
def inject_css() -> None:
    """Inject the global premium CSS into every Streamlit page."""
    css_path = ROOT / "assets" / "style.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# ── Age Parser ───────────────────────────────────────────────
def _parse_age(val) -> float | None:
    """Convert age strings like '27-016' → 27.0, pass through numbers."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    m = re.match(r"^(\d+)", str(val).strip())
    return float(m.group(1)) if m else None


# ── Raw loader ───────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_raw() -> pd.DataFrame:
    """Load players.csv with minimal cleaning. Cached for 1 hour."""
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df["age"] = df["age"].apply(_parse_age)
    return df


# ── Outfield player loader ────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_outfield() -> pd.DataFrame:
    """
    Return only outfield players (non-GK) with minutes > 0.
    Drops columns that are >95% null (GK-specific) and useless cols.
    Fills remaining nulls with 0.
    """
    df = load_raw()

    # Keep only players with playing time
    df = df[df["minutes"].notna() & (df["minutes"] > 0)].copy()

    # Exclude goalkeepers (gk_games_starts > 0 is reliable GK flag)
    gk_mask = df["gk_games_starts"].fillna(0) > 0
    df = df[~gk_mask].copy()

    # Drop GK columns and fully-null columns
    gk_cols = [c for c in df.columns if c.startswith("gk_")]
    always_null = [c for c in df.columns if df[c].isna().all()]
    drop_cols = list(set(gk_cols + always_null + ["pens_won", "pens_conceded", "club"]))
    df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

    # Fill remaining numeric nulls
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(0)

    df.reset_index(drop=True, inplace=True)
    return df


# ── Goalkeeper loader ─────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_goalkeepers() -> pd.DataFrame:
    """Return goalkeepers only with GK-specific stats."""
    df = load_raw()
    gk_mask = df["gk_games_starts"].fillna(0) > 0
    df = df[gk_mask].copy()
    df = df[df["gk_minutes"].fillna(0) > 0].copy()
    gk_cols = ["player", "team", "team_country", "age",
               "gk_games_starts", "gk_minutes", "gk_goals_against",
               "gk_goals_against_per90", "gk_shots_on_target_against",
               "gk_saves", "gk_save_pct", "gk_wins", "gk_ties",
               "gk_losses", "gk_clean_sheets", "gk_clean_sheets_pct",
               "gk_pens_att", "gk_pens_saved", "gk_pens_save_pct"]
    available = [c for c in gk_cols if c in df.columns]
    df = df[available].copy()
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].fillna(0)
    df.reset_index(drop=True, inplace=True)
    return df


# ── Team aggregator ───────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def load_team_stats() -> pd.DataFrame:
    """Aggregate outfield player stats to team level."""
    df = load_outfield()

    agg = df.groupby("team").agg(
        players=("player", "count"),
        total_goals=("goals", "sum"),
        total_assists=("assists", "sum"),
        total_shots=("shots", "sum"),
        total_shots_on_target=("shots_on_target", "sum"),
        total_minutes=("minutes", "sum"),
        avg_goals_per90=("goals_per90", "mean"),
        avg_assists_per90=("assists_per90", "mean"),
        avg_shots_per90=("shots_per90", "mean"),
        total_yellow=("cards_yellow", "sum"),
        total_red=("cards_red", "sum"),
        total_fouls=("fouls", "sum"),
        total_fouled=("fouled", "sum"),
        total_interceptions=("interceptions", "sum"),
        total_tackles_won=("tackles_won", "sum"),
        avg_plus_minus=("plus_minus_per90", "mean"),
    ).reset_index()

    # Derived metrics
    agg["goals_per_shot"] = (
        agg["total_goals"] / agg["total_shots"].replace(0, pd.NA)
    ).fillna(0).round(3)
    agg["minutes_per_player"] = (
        agg["total_minutes"] / agg["players"]
    ).round(1)

    # Continent mapping (approximate)
    continent_map = {
        "UEFA": ["England", "France", "Germany", "Spain", "Portugal", "Italy",
                 "Netherlands", "Belgium", "Croatia", "Denmark", "Poland",
                 "Switzerland", "Austria", "Serbia", "Czech Republic",
                 "Slovakia", "Hungary", "Romania", "Slovenia", "Albania",
                 "Scotland", "Wales", "Turkey", "Ukraine", "Sweden",
                 "Norway", "Finland", "Greece", "Bosnia and Herzegovina",
                 "Montenegro", "Kosovo", "Northern Ireland", "Ireland",
                 "Iceland", "Georgia", "Azerbaijan", "Armenia"],
        "CONMEBOL": ["Brazil", "Argentina", "Colombia", "Uruguay",
                     "Chile", "Ecuador", "Bolivia", "Peru", "Paraguay",
                     "Venezuela"],
        "CONCACAF": ["United States", "Mexico", "Canada", "Costa Rica",
                     "Honduras", "Jamaica", "Panama", "Guatemala",
                     "El Salvador", "Haiti", "Trinidad and Tobago",
                     "Cuba", "Curaçao"],
        "CAF": ["Morocco", "Senegal", "Nigeria", "Ghana", "Cameroon",
                "Egypt", "Algeria", "Tunisia", "Ivory Coast",
                "South Africa", "Mali", "Burkina Faso", "Congo DR",
                "Guinea", "Cape Verde", "Zambia", "Tanzania", "Comoros"],
        "AFC": ["Japan", "South Korea", "Saudi Arabia", "Iran",
                "Australia", "Qatar", "Iraq", "Uzbekistan", "Jordan",
                "Oman", "Bahrain", "UAE", "Indonesia", "Thailand",
                "Vietnam", "China", "India"],
        "OFC": ["New Zealand", "Fiji", "Papua New Guinea"],
    }
    # Invert map: country → confederation
    country_to_conf = {}
    for conf, countries in continent_map.items():
        for country in countries:
            country_to_conf[country] = conf

    agg["confederation"] = agg["team"].map(country_to_conf).fillna("Other")
    return agg


# ── Helper: sorted player list ────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def player_list() -> list[str]:
    """Sorted list of outfield player names for dropdowns."""
    df = load_outfield()
    return sorted(df["player"].unique().tolist())


# ── Tournament context constants ──────────────────────────────
MAX_GAMES = 7       # Max games in FIFA 2026 World Cup
GAMES_PLAYED = 3    # Approximate group stage games completed (update as needed)
