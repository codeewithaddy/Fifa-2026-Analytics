"""
pages/3_Golden_Boot.py — Top Scorers & Projections
Projecting player tournament scores.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import base64
import pathlib

from utils.data_loader import inject_css, load_outfield, MAX_GAMES
from utils.ml_model    import project_goals
from utils.charts      import golden_boot_bar, NAVY, RED, GREEN, TEXT, TEXT_MUTED, BORDER, BG, _base_layout
from utils.api_client  import flag, time_since_update

# ── Streamlit Config ──────────────────────────────────────────
st.set_page_config(
    page_title="Top Scorers & Projections · FIFA 2026",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Header with Banner Image ──────────────────────────────────
bg_path = "assets/goal_projections.png"
bg_tag = ""
try:
    bg_bytes = pathlib.Path(bg_path).read_bytes()
    bg_b64 = base64.b64encode(bg_bytes).decode()
    bg_tag = f'<img class="bg" src="data:image/png;base64,{bg_b64}" alt="Goal Projections">'
except Exception:
    pass

st.markdown(f"""
<div class="premium-hero">
  {bg_tag}
  <div class="overlay" style="background: linear-gradient(90deg, rgba(15,23,42,0.95) 0%, rgba(15,23,42,0.7) 50%, rgba(15,23,42,0.2) 100%);"></div>
  <div class="hero-content">
    <div class="eyebrow" style="color:#e01a22; font-weight:800; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.4rem;">GOAL PROJECTIONS</div>
    <h1 style="color:#ffffff !important;">Top Scorers &amp; Projections</h1>
    <p class="hero-sub" style="color:rgba(255,255,255,0.8);">
      Goal projections to the end of the tournament, extrapolated from current goals per 90-minute rates.
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────
with st.spinner(""):
    df = load_outfield()

# ── Controls ──────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([3, 3, 2])

with col_ctrl1:
    view_type = st.radio(
        "Current vs Projected metrics:",
        ["Current Goals", "Projected Goals Total", "Goals per 90 mins"],
        horizontal=True,
    )
with col_ctrl2:
    rounds_val = st.radio(
        "Projected rounds played:",
        [6, 7, 8],
        index=1,
        horizontal=True,
    )
with col_ctrl3:
    st.markdown(f"""
    <div style="padding:.5rem 0; font-size:.8rem; color:#64748b;">
      {time_since_update()}
    </div>
    """, unsafe_allow_html=True)

# Projection Model Fit
proj = project_goals(df, max_games=rounds_val)
if proj.empty:
    st.warning("No players found with goals recorded.")
    st.stop()

# ── Top 5 Projected Scorers Cards ─────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Scoring Race Leaders</h2>
  <span class="tag">Standings</span>
</div>
""", unsafe_allow_html=True)

top5 = proj.head(5)
s_cols = st.columns(5)
positions_tags = ["First", "Second", "Third", "Fourth", "Fifth"]

for idx, (_, row) in enumerate(top5.iterrows()):
    p_name = row["player"]
    p_team = row["team"]
    p_goals = int(row["goals"])
    p_proj = row["projected_goals"]

    with s_cols[idx]:
        st.markdown(f"""
        <div class="app-card" style="text-align:center; border-top: 4px solid {RED if idx==0 else BORDER};">
          <div class="app-card-title">{positions_tags[idx]} Scorer</div>
          <div style="font-size:2rem; margin:0.5rem 0;">{flag(p_team)}</div>
          <div class="app-card-value">{p_goals}</div>
          <div style="font-weight:700; margin-top:0.5rem; font-size:0.95rem;">{p_name}</div>
          <div style="font-size:0.8rem; color:#64748b;">{p_team}</div>
          <div style="margin-top:0.75rem; padding:0.35rem 0.5rem; background:#f1f5f9; border-radius:4px; font-weight:700; font-size:0.8rem;">
            {p_proj:.1f} Projected
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Projected goal bar chart ──────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Goal Tally Projection Map</h2>
  <span class="tag">Top 10 Scorers</span>
</div>
""", unsafe_allow_html=True)
st.plotly_chart(golden_boot_bar(proj), width='stretch')

# ── Goal Trajectories ─────────────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Scoring Trajectory Profile</h2>
</div>
""", unsafe_allow_html=True)

trajectory_palette = [RED, GREEN, "#1e40af", "#d97706", "#7c3aed", "#0891b2", "#059669"]
fig_traj = go.Figure()

for idx, (_, row) in enumerate(proj.head(7).iterrows()):
    g_played = float(row["games_played_est"])
    g_rate = float(row["goals_per90"])
    g_actual = float(row["goals"])
    games = list(range(0, rounds_val + 1))
    traj = []
    for g in games:
        if g <= g_played:
            traj.append(g_actual * (g / max(g_played, 1)))
        else:
            traj.append(g_actual + g_rate * (g - g_played))
    traj[0] = 0.0

    fig_traj.add_trace(go.Scatter(
        x=games, y=[round(v, 1) for v in traj],
        mode="lines",
        name=row["player"],
        line=dict(color=trajectory_palette[idx % len(trajectory_palette)], width=2.5),
        hovertemplate=f"<b>{row['player']}</b><br>Game %{{x}}: %{{y:.1f}} goals<extra></extra>",
    ))
    # Diamond Marker
    fig_traj.add_trace(go.Scatter(
        x=[g_played], y=[g_actual],
        mode="markers",
        marker=dict(size=11, color=trajectory_palette[idx % len(trajectory_palette)], symbol="diamond", line=dict(width=2, color="white")),
        showlegend=False,
        hovertemplate=f"<b>{row['player']}</b><br>Current: {int(g_actual)} goals<extra></extra>",
    ))

fig_traj.add_vline(
    x=float(proj["games_played_est"].median()),
    line_dash="dot", line_color="#cbd5e1", line_width=1.5,
    annotation_text="Played | Projected",
    annotation_font=dict(color=TEXT_MUTED, size=10),
    annotation_position="top",
)

fig_traj.update_layout(
    **_base_layout(
        title=dict(text="Cumulative Goals vs Projected Match Increments",
                   font=dict(family="Montserrat, sans-serif", size=17, color=NAVY), x=0),
        xaxis=dict(title="Matches", tickvals=list(range(0, rounds_val + 1))),
        yaxis=dict(title="Goals Count", rangemode="tozero"),
        height=420,
    )
)
st.plotly_chart(fig_traj, width='stretch')

# ── Projections Explainer List ────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Projection Details</h2>
</div>
""", unsafe_allow_html=True)

for _, row in proj.head(5).iterrows():
    g_left = float(row["games_remaining"])
    st.markdown(f"""
    <div class="row-item">
      <div class="row-item-main">
        <span style="font-size:1.5rem;">{flag(row['team'])}</span>
        <div>
          <div class="row-item-name">{row['player']} ({row['team']})</div>
          <div class="row-item-meta">{int(row['goals'])} goals scored · {row['goals_per90']:.2f} goals per 90 · {g_left:.1f} matches remaining</div>
        </div>
      </div>
      <div class="row-item-value" style="color:#e01a22;">
        {row['projected_goals']:.1f} Goals Projected
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Data Expandable ───────────────────────────────────────────
with st.expander("Full Projections Dataset"):
    tbl = proj.rename(columns={
        "player": "Player", "team": "Team",
        "goals": "Current Goals", "goals_per90": "Goals/90 Rate",
        "games_played_est": "Matches Played (est.)",
        "games_remaining": "Matches Remaining",
        "projected_goals": "Projected Goals Total",
    })
    tbl["Goals/90 Rate"]           = tbl["Goals/90 Rate"].round(3)
    tbl["Matches Played (est.)"] = tbl["Matches Played (est.)"].round(1)
    tbl["Matches Remaining"]       = tbl["Matches Remaining"].round(1)
    st.dataframe(tbl.reset_index(drop=True), width='stretch', hide_index=True)

# ── Footer ────────────────────────────────────────────────────
st.markdown(f"""
<div class="site-footer">
  <div class="site-footer-brand">FIFA WC 2026 Stats Centre</div>
  <div>Dataset: FIFA World Cup 2026 Player Stats by Swapnil Tripathi (Kaggle)</div>
</div>
""", unsafe_allow_html=True)
