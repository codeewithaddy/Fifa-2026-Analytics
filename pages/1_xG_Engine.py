"""
pages/1_xG_Engine.py — Shot Quality & Expected Goals
Comparing actual goals against model projections.
"""

import streamlit as st
import pandas as pd
import numpy as np

from utils.data_loader import inject_css, load_outfield, performance_label
from utils.ml_model    import build_xg_model
from utils.charts      import xg_scatter, delta_bar
from utils.api_client  import time_since_update, flag

# ── Streamlit Config ──────────────────────────────────────────
st.set_page_config(
    page_title="Shot Quality & Expected Goals · FIFA 2026",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
  <div class="ph-eyebrow">SHOOTING ANALYSIS</div>
  <h1>Shot Quality &amp; Expected Goals</h1>
  <p class="ph-desc">
    This analysis compares the quality of chances each player gets (Expected Goals / xG) against what they actually score.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Methodology Explainer ─────────────────────────────────────
with st.expander("📖 Explanation of Expected Goals (xG)"):
    st.markdown("""
    **Expected Goals (xG)** measures the quality of a shot based on features like position, accuracy, and shot volume.
    - **Actual Goals > xG**: Player is scoring from low-quality positions or converting difficult chances (clinical).
    - **Actual Goals < xG**: Player is getting good opportunities but failing to convert (unlucky/underperforming).
    """)

# ── Load and Model Data ───────────────────────────────────────
with st.spinner(""):
    raw = load_outfield()
    df  = build_xg_model(raw)

# ── Controls ──────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([3, 3, 2])

with col_ctrl1:
    position_sel = st.radio(
        "Player positions to display:",
        ["All positions", "Forwards", "Midfielders"],
        horizontal=True,
    )
with col_ctrl2:
    shots_threshold = st.radio(
        "Minimum shots taken:",
        [3, 5, 10],
        index=0,
        horizontal=True,
    )
with col_ctrl3:
    st.markdown(f"""
    <div style="padding:.5rem 0; font-size:.8rem; color:#64748b;">
      Updated: {time_since_update()}
    </div>
    """, unsafe_allow_html=True)

# Apply filters
f_mask = df["shots"].fillna(0) >= shots_threshold
if position_sel == "Forwards":
    f_mask &= df["position"].str.contains("FW|ST|CF|LW|RW", case=False, na=False)
elif position_sel == "Midfielders":
    f_mask &= df["position"].str.contains("MF|CM|AM|DM", case=False, na=False)

fdf = df[f_mask].copy()

# ── KPIs ──────────────────────────────────────────────────────
overperformers  = (fdf["delta_g"] > 0.5).sum()
underperformers = (fdf["delta_g"] < -0.5).sum()
sum_xg = fdf["xG"].sum()
sum_actual = fdf["goals"].sum()

st.markdown(f"""
<div class="kpi-strip">
  <div class="kpi-item">
    <div class="ki-label">Players Analysed</div>
    <div class="ki-value">{len(fdf)}</div>
    <div class="ki-sub">matching selections</div>
  </div>
  <div class="kpi-item">
    <div class="ki-label">Goals Scored</div>
    <div class="ki-value">{int(sum_actual)}</div>
    <div class="ki-sub">total actual goals</div>
  </div>
  <div class="kpi-item">
    <div class="ki-label">Expected Goals (xG)</div>
    <div class="ki-value">{sum_xg:.1f}</div>
    <div class="ki-sub">expected sum total</div>
  </div>
  <div class="kpi-item">
    <div class="ki-label">Overperforming xG</div>
    <div class="ki-value" style="color:#048a5f;">{overperformers}</div>
    <div class="ki-sub">players above expected</div>
  </div>
  <div class="kpi-item">
    <div class="ki-label">Underperforming xG</div>
    <div class="ki-value" style="color:#e01a22;">{underperformers}</div>
    <div class="ki-sub">players below expected</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────
tab_over, tab_under, tab_data = st.tabs([
    "🟢 Over-performing Players",
    "🔴 Under-performing Players",
    "📋 Complete Dataset"
])

with tab_over:
    st.markdown("""
    <div class="clean-header">
      <h2>Clinical Finishers</h2>
    </div>
    """, unsafe_allow_html=True)

    over_players = fdf[fdf["delta_g"] > 0].nlargest(8, "delta_g")
    for _, row in over_players.iterrows():
        p_name = row["player"]
        p_team = row["team"]
        p_actual = int(row["goals"])
        p_xg = row["xG"]
        p_delta = row["delta_g"]

        st.markdown(f"""
        <div class="row-item">
          <div class="row-item-main">
            <span style="font-size:1.5rem;">{flag(p_team)}</span>
            <div>
              <div class="row-item-name">{p_name}</div>
              <div class="row-item-meta">{p_team} · {row['position']} · {int(row['shots'])} shots</div>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:1.5rem;">
            <div style="text-align:right;">
              <div style="font-size:0.75rem; color:#64748b;">Goals / xG</div>
              <div style="font-size:0.9rem; font-weight:600;">{p_actual} goals / {p_xg:.1f} xG</div>
            </div>
            <div class="row-item-value" style="color:#048a5f;">+{p_delta:.1f}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.plotly_chart(delta_bar(fdf, top_n=10, mode="over"), width='stretch')

with tab_under:
    st.markdown("""
    <div class="clean-header">
      <h2>Under-performing Players</h2>
    </div>
    """, unsafe_allow_html=True)

    under_players = fdf[fdf["delta_g"] < 0].nsmallest(8, "delta_g")
    for _, row in under_players.iterrows():
        p_name = row["player"]
        p_team = row["team"]
        p_actual = int(row["goals"])
        p_xg = row["xG"]
        p_delta = row["delta_g"]

        st.markdown(f"""
        <div class="row-item">
          <div class="row-item-main">
            <span style="font-size:1.5rem;">{flag(p_team)}</span>
            <div>
              <div class="row-item-name">{p_name}</div>
              <div class="row-item-meta">{p_team} · {row['position']} · {int(row['shots'])} shots</div>
            </div>
          </div>
          <div style="display:flex; align-items:center; gap:1.5rem;">
            <div style="text-align:right;">
              <div style="font-size:0.75rem; color:#64748b;">Goals / xG</div>
              <div style="font-size:0.9rem; font-weight:600;">{p_actual} goals / {p_xg:.1f} xG</div>
            </div>
            <div class="row-item-value" style="color:#e01a22;">{p_delta:.1f}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.plotly_chart(delta_bar(fdf, top_n=10, mode="under"), width='stretch')

with tab_data:
    st.markdown("""
    <div class="clean-header">
      <h2>Tournament Dataset</h2>
    </div>
    """, unsafe_allow_html=True)

    # Plotly Scatter view
    st.plotly_chart(xg_scatter(fdf), width='stretch')

    # Dataframe table
    st.markdown("<br>", unsafe_allow_html=True)
    tbl = fdf[["player", "team", "position", "goals", "xG", "delta_g", "shots", "minutes"]].copy()
    tbl.columns = ["Player", "Nation", "Position", "Goals", "Expected Goals (xG)", "Difference (Goals-xG)", "Shots", "Minutes"]
    tbl["Expected Goals (xG)"] = tbl["Expected Goals (xG)"].round(2)
    tbl["Difference (Goals-xG)"] = tbl["Difference (Goals-xG)"].round(2)
    st.dataframe(tbl.sort_values("Goals", ascending=False).reset_index(drop=True), width='stretch', height=400)

# ── Footer ────────────────────────────────────────────────────
st.markdown(f"""
<div class="site-footer">
  <div class="site-footer-brand">FIFA WC 2026 Stats</div>
  <div>Model Type: Positive Linear Regression Model · Features: shots, minutes</div>
</div>
""", unsafe_allow_html=True)
