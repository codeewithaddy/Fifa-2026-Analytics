"""
utils/ml_model.py
FIFA 2026 Intelligence Hub — Linear Regression xG / xA models.

Expected Goals (xG): predicts how many goals a player "should" score
  given their shot profile (shots, shots on target, minutes played).
  delta_g = actual_goals - xG  → positive = over-performer (clinical finisher)
                                  negative = under-performer (wasting chances)

Expected Assists (xA): same logic applied to assists.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import MinMaxScaler
import streamlit as st


# ── Feature sets ──────────────────────────────────────────────
XG_FEATURES = ["shots", "shots_on_target", "minutes_90s", "shots_per90"]
XA_FEATURES  = ["assists_per90", "minutes_90s", "goals_assists_per90", "fouls"]


# ── xG Model ─────────────────────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def build_xg_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Train a Linear Regression xG model and return df enriched with:
      xG, xA, delta_g (actual - xG), delta_a (actual - xA),
      xG_per90, xA_per90, performance_score (composite)
    """
    df = df.copy()

    # ── xG ─────────────────────────────────────────────────
    features_g = [c for c in XG_FEATURES if c in df.columns]
    X_g = df[features_g].fillna(0).values
    y_g = df["goals"].fillna(0).values

    # Only train on players who have shot data (avoid trivially zero rows)
    mask_train = df["shots"].fillna(0) > 0
    if mask_train.sum() > 20:
        lr_g = LinearRegression(positive=True)  # xG can't be negative
        lr_g.fit(X_g[mask_train], y_g[mask_train])
        xg_raw = lr_g.predict(X_g)
    else:
        # Fallback: xG ≈ shots_on_target * 0.33
        xg_raw = df["shots_on_target"].fillna(0) * 0.33

    df["xG"] = np.clip(xg_raw, 0, None).round(2)
    df["delta_g"] = (df["goals"] - df["xG"]).round(2)

    # ── xA ─────────────────────────────────────────────────
    features_a = [c for c in XA_FEATURES if c in df.columns]
    X_a = df[features_a].fillna(0).values
    y_a = df["assists"].fillna(0).values

    mask_train_a = df["minutes_90s"].fillna(0) > 1
    if mask_train_a.sum() > 20:
        lr_a = LinearRegression(positive=True)
        lr_a.fit(X_a[mask_train_a], y_a[mask_train_a])
        xa_raw = lr_a.predict(X_a)
    else:
        xa_raw = df["assists_per90"].fillna(0) * df["minutes_90s"].fillna(0)

    df["xA"] = np.clip(xa_raw, 0, None).round(2)
    df["delta_a"] = (df["assists"] - df["xA"]).round(2)

    # ── Per-90 versions ─────────────────────────────────────
    mins90 = df["minutes_90s"].replace(0, np.nan)
    df["xG_per90"] = (df["xG"] / mins90).round(3)
    df["xA_per90"] = (df["xA"] / mins90).round(3)
    df[["xG_per90", "xA_per90"]] = df[["xG_per90", "xA_per90"]].fillna(0)

    # ── Performance Score: composite over/underperformance ──
    # Weighted: finishing (delta_g) counts more than creation (delta_a)
    df["performance_score"] = (df["delta_g"] * 0.65 + df["delta_a"] * 0.35).round(3)

    # ── Percentile ranks (for display) ──────────────────────
    for col in ["xG", "xA", "goals", "assists", "delta_g", "performance_score"]:
        if col in df.columns:
            df[f"{col}_pct"] = df[col].rank(pct=True).round(3)

    return df


# ── Percentile helper ─────────────────────────────────────────
def get_percentile(series: pd.Series, value: float) -> float:
    """Return the percentile (0–100) of `value` within `series`."""
    return round(float((series < value).mean() * 100), 1)


# ── Radar attributes ──────────────────────────────────────────
RADAR_ATTRS = {
    "goals_per90":         "Goals / 90",
    "assists_per90":       "Assists / 90",
    "shots_per90":         "Shots / 90",
    "shots_on_target_pct": "Shot Accuracy %",
    "plus_minus_per90":    "± per 90",
    "fouls":               "Fouls (inv.)",   # inverted: lower is better
}

RADAR_INVERT = {"fouls"}  # These columns are "better when lower"


def compute_radar_values(player_name: str, df: pd.DataFrame) -> dict[str, float]:
    """
    Return normalised radar values (0–100) for a given player.
    Each stat is percentile-ranked across all outfield players.
    """
    row = df[df["player"] == player_name]
    if row.empty:
        return {k: 0.0 for k in RADAR_ATTRS}

    row = row.iloc[0]
    values = {}
    for col, label in RADAR_ATTRS.items():
        if col not in df.columns:
            values[label] = 0.0
            continue
        pct = get_percentile(df[col], row[col])
        if col in RADAR_INVERT:
            pct = 100 - pct   # Invert: fewer fouls → higher score
        values[label] = pct

    return values


# ── Golden Boot projection ────────────────────────────────────
def project_goals(df: pd.DataFrame, max_games: int = 7) -> pd.DataFrame:
    """
    Project total goals to end of tournament.
    Assumes each game ≈ 90 minutes at the player's current per-90 rate.
    Returns top 20 scorers with projection.
    """
    df = df.copy()

    # Current games played estimate per player
    df["games_played_est"] = (df["minutes"].fillna(0) / 90).clip(lower=1)
    df["games_remaining"] = (max_games - df["games_played_est"]).clip(lower=0)

    # Project: current goals + (per90 rate × remaining 90s)
    df["projected_goals"] = (
        df["goals"] + df["goals_per90"] * df["games_remaining"]
    ).round(1)

    # Simple confidence interval ±1 std of per-90 goals among scorers
    scorer_std = df[df["goals"] > 0]["goals_per90"].std()
    df["proj_low"] = (df["projected_goals"] - scorer_std * df["games_remaining"]).clip(lower=df["goals"]).round(1)
    df["proj_high"] = (df["projected_goals"] + scorer_std * df["games_remaining"]).round(1)

    top = df[df["goals"] > 0].nlargest(20, "goals").copy()
    return top[["player", "team", "goals", "goals_per90", "games_played_est",
                "games_remaining", "projected_goals", "proj_low", "proj_high"]]
