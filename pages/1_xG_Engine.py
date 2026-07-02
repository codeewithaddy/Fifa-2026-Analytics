"""
pages/1_xG_Engine.py — Expected Goals (xG) Engine
FIFA 2026 Intelligence Hub
"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.data_loader import inject_css, load_outfield
from utils.ml_model import build_xg_model
from utils.charts import xg_scatter, delta_bar

st.set_page_config(
    page_title="xG Engine · FIFA 2026",
    page_icon="🤖",
    layout="wide",
)
inject_css()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="page-title-row">
  <h1>🤖 Expected Goals Engine</h1>
  <span class="live-badge"><span class="live-dot"></span>ML Powered</span>
</div>
<p style="color:rgba(232,237,245,0.65); margin-top:-0.5rem; margin-bottom:1.5rem;">
  Linear Regression trained on shot profiles to predict how many goals each player 
  <em>should</em> score. Delta reveals who's lucky vs. elite.
</p>
""", unsafe_allow_html=True)

# ── Load + model ──────────────────────────────────────────────
with st.spinner("Training xG model…"):
    raw   = load_outfield()
    df    = build_xg_model(raw)

# ── Filters sidebar ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Filters")
    min_shots = st.slider("Min shots taken", 0, 30, 3,
                          help="Filter out players with very few shots")
    min_mins  = st.slider("Min minutes played", 0, 600, 90)
    positions = df["position"].dropna().unique().tolist()
    sel_pos   = st.multiselect("Positions", positions, default=positions,
                                help="Filter by playing position")
    st.markdown("---")
    st.markdown("**Model Info**")
    st.caption("Features: shots, shots on target, 90s played, shots/90")
    st.caption("Target: actual goals")
    st.caption("Algorithm: Linear Regression (sklearn)")

# Apply filters
mask = (
    (df["shots"].fillna(0) >= min_shots) &
    (df["minutes"].fillna(0) >= min_mins) &
    (df["position"].isin(sel_pos) if sel_pos else True)
)
fdf = df[mask].copy()

# ── Top KPIs ─────────────────────────────────────────────────
total_xg    = fdf["xG"].sum()
total_actual = fdf["goals"].sum()
over_n  = (fdf["delta_g"] > 0.5).sum()
under_n = (fdf["delta_g"] < -0.5).sum()
best_finisher = fdf.loc[fdf["delta_g"].idxmax(), "player"] if not fdf.empty else "—"

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Σ xG (Expected)", f"{total_xg:.1f}")
k2.metric("Σ Actual Goals",  f"{total_actual:.0f}")
k3.metric("xG Delta",  f"{total_actual - total_xg:+.1f}",
          delta="Tournament over-performed" if total_actual > total_xg else "Under-performed")
k4.metric("Over-performers", f"{over_n}")
k5.metric("Under-performers",f"{under_n}")

st.markdown("<hr>", unsafe_allow_html=True)

# ── Scatter Plot ──────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">📍</span>
  <h2>xG vs Actual Goals</h2>
  <span class="badge">Scatter</span>
</div>
""", unsafe_allow_html=True)

st.caption("Points **above** the dashed line = over-performers (better than expected). Below = under-performers. Bubble size = shots taken.")
st.plotly_chart(xg_scatter(fdf), use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Leaderboards ──────────────────────────────────────────────
tab_over, tab_under, tab_all = st.tabs(["🟢 Over-Performers", "🔴 Under-Performers", "📋 All Players"])

with tab_over:
    st.markdown("""
    <div class="section-header">
      <span class="section-icon">🟢</span>
      <h2>Clinical Finishers</h2>
      <span class="badge">Top 10</span>
    </div>
    <p style="color:rgba(232,237,245,0.55); font-size:0.88rem;">
      These players score significantly more than their shot profile predicts — elite finishers.
    </p>
    """, unsafe_allow_html=True)
    st.plotly_chart(delta_bar(fdf, top_n=10, mode="over"), use_container_width=True)

    over_table = (
        fdf[fdf["delta_g"] > 0]
        .nlargest(15, "delta_g")
        [["player", "team", "position", "goals", "xG", "delta_g", "shots", "shots_on_target"]]
        .rename(columns={"player":"Player","team":"Team","position":"Pos",
                         "goals":"Goals","xG":"xG","delta_g":"Delta","shots":"Shots","shots_on_target":"SoT"})
        .reset_index(drop=True)
    )
    over_table.index += 1
    over_table["xG"]   = over_table["xG"].round(2)
    over_table["Delta"] = over_table["Delta"].round(2)
    st.dataframe(over_table, use_container_width=True, height=420,
                 column_config={"Delta": st.column_config.NumberColumn("Delta ▲", format="%+.2f")})

with tab_under:
    st.markdown("""
    <div class="section-header">
      <span class="section-icon">🔴</span>
      <h2>Wasting Chances</h2>
      <span class="badge">Bottom 10</span>
    </div>
    <p style="color:rgba(232,237,245,0.55); font-size:0.88rem;">
      These players score far fewer goals than their chance creation warrants.
    </p>
    """, unsafe_allow_html=True)
    st.plotly_chart(delta_bar(fdf, top_n=10, mode="under"), use_container_width=True)

    under_table = (
        fdf[fdf["delta_g"] < 0]
        .nsmallest(15, "delta_g")
        [["player", "team", "position", "goals", "xG", "delta_g", "shots", "shots_on_target"]]
        .rename(columns={"player":"Player","team":"Team","position":"Pos",
                         "goals":"Goals","xG":"xG","delta_g":"Delta","shots":"Shots","shots_on_target":"SoT"})
        .reset_index(drop=True)
    )
    under_table.index += 1
    under_table["xG"]    = under_table["xG"].round(2)
    under_table["Delta"] = under_table["Delta"].round(2)
    st.dataframe(under_table, use_container_width=True, height=420,
                 column_config={"Delta": st.column_config.NumberColumn("Delta ▼", format="%+.2f")})

with tab_all:
    st.markdown("""
    <div class="section-header">
      <span class="section-icon">📋</span>
      <h2>All Players — xG Data</h2>
    </div>
    """, unsafe_allow_html=True)

    search = st.text_input("🔍 Search player", placeholder="e.g. Messi, Mbappe…")
    all_table = fdf[["player","team","position","goals","xG","xA","delta_g","delta_a",
                      "performance_score","shots","minutes"]].copy()
    all_table.columns = ["Player","Team","Pos","Goals","xG","xA",
                          "G Delta","A Delta","Perf Score","Shots","Mins"]
    for c in ["xG","xA","G Delta","A Delta","Perf Score"]:
        all_table[c] = all_table[c].round(2)

    if search:
        all_table = all_table[all_table["Player"].str.contains(search, case=False, na=False)]

    all_table = all_table.sort_values("Goals", ascending=False).reset_index(drop=True)
    all_table.index += 1
    st.dataframe(all_table, use_container_width=True, height=520,
                 column_config={
                     "G Delta": st.column_config.NumberColumn("G Delta", format="%+.2f"),
                     "A Delta": st.column_config.NumberColumn("A Delta", format="%+.2f"),
                     "Perf Score": st.column_config.NumberColumn("Perf ⭐", format="%+.3f"),
                 })

# ── Methodology Note ──────────────────────────────────────────
with st.expander("📖 Methodology & Model Details"):
    st.markdown("""
    ### How the xG Model Works
    
    **Algorithm:** `sklearn.linear_model.LinearRegression` with `positive=True` constraint
    (xG cannot be negative).
    
    **Input features (xG):**
    - `shots` — total shots taken
    - `shots_on_target` — shots requiring save or scoring
    - `minutes_90s` — 90-minute blocks played (proxy for opportunity)
    - `shots_per90` — shooting rate normalised to 90 minutes
    
    **Input features (xA):**
    - `assists_per90`, `minutes_90s`, `goals_assists_per90`, `fouls`
    
    **Training:** Only players with at least 1 shot taken (avoids trivial zero rows).
    
    **Interpretation of Delta:**
    - `delta_g = actual_goals − xG`
    - **+ve** → player scores more than expected → clinical finisher
    - **−ve** → player scores less than expected → unlucky or poor finisher
    
    **Limitations:** Linear Regression is intentionally simple for interpretability.
    A production system would use gradient-boosted trees with shot location data.
    """)

st.markdown("""
<hr>
<p style="text-align:center; color:rgba(232,237,245,0.3); font-size:0.78rem;">
  xG Engine · FIFA 2026 Intelligence Hub
</p>
""", unsafe_allow_html=True)
