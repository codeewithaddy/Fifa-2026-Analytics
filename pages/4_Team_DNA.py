"""
pages/4_Team_DNA.py — Team Performance Analysis
Aggregating player stats by team to profile playstyles.
"""

import streamlit as st
import pandas as pd
import numpy as np

from utils.data_loader import inject_css, load_team_stats, load_outfield, team_style_label
from utils.charts      import team_dna_scatter
from utils.api_client  import flag, time_since_update

# ── Streamlit Config ──────────────────────────────────────────
st.set_page_config(
    page_title="Team Performance Analysis · FIFA 2026",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="page-hero">
  <div class="ph-eyebrow">TEAM PROFILES</div>
  <h1>Team Performance Analysis</h1>
  <p class="ph-desc">
    Aggregated player performance profiles by team to evaluate shot volume, conversion rates, and defensive metrics.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────
with st.spinner(""):
    teams = load_team_stats()
    players = load_outfield()

# ── Controls ──────────────────────────────────────────────────
st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([3, 3, 2])

with col_ctrl1:
    conf_options = ["All confederations"] + sorted(teams["confederation"].unique())
    sel_conf = st.selectbox("Confederation filter:", conf_options)
with col_ctrl2:
    sort_metric = st.radio(
        "Sort teams list by:",
        ["Goals Scored", "Shot Conversion", "Total Shots Taken"],
        horizontal=True,
    )
with col_ctrl3:
    st.markdown(f"""
    <div style="padding:.5rem 0; font-size:.8rem; color:#64748b;">
      Updated: {time_since_update()}
    </div>
    """, unsafe_allow_html=True)

sort_col_map = {
    "Goals Scored": "total_goals",
    "Shot Conversion": "goals_per_shot",
    "Total Shots Taken": "total_shots",
}
sort_field = sort_col_map[sort_metric]

# Apply filter
f_teams = teams.copy()
if sel_conf != "All confederations":
    f_teams = f_teams[f_teams["confederation"] == sel_conf]

# ── Top Performers Cards ──────────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Performance Leaders</h2>
</div>
""", unsafe_allow_html=True)

best_atk = f_teams.loc[f_teams["total_goals"].idxmax()] if not f_teams.empty else None
best_con = f_teams.loc[f_teams["goals_per_shot"].idxmax()] if not f_teams.empty else None
best_sht = f_teams.loc[f_teams["total_shots"].idxmax()] if not f_teams.empty else None

if best_atk is not None:
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.markdown(f"""
        <div class="app-card" style="border-left: 4px solid #e01a22;">
          <div class="app-card-title">Top Goal-Scoring Nation</div>
          <div class="app-card-value">{int(best_atk['total_goals'])}</div>
          <div style="font-weight:700; margin-top:0.5rem; font-size:0.95rem;">
            {flag(best_atk['team'])} {best_atk['team']}
          </div>
          <div class="app-card-desc">Goals scored in the tournament</div>
        </div>
        """, unsafe_allow_html=True)
    with col_k2:
        st.markdown(f"""
        <div class="app-card" style="border-left: 4px solid #048a5f;">
          <div class="app-card-title">Most Efficient Attack</div>
          <div class="app-card-value">{best_con['goals_per_shot']:.0%}</div>
          <div style="font-weight:700; margin-top:0.5rem; font-size:0.95rem;">
            {flag(best_con['team'])} {best_con['team']}
          </div>
          <div class="app-card-desc">Shot conversion rate</div>
        </div>
        """, unsafe_allow_html=True)
    with col_k3:
        st.markdown(f"""
        <div class="app-card" style="border-left: 4px solid #0f2547;">
          <div class="app-card-title">Highest Shot Volume</div>
          <div class="app-card-value">{int(best_sht['total_shots'])}</div>
          <div style="font-weight:700; margin-top:0.5rem; font-size:0.95rem;">
            {flag(best_sht['team'])} {best_sht['team']}
          </div>
          <div class="app-card-desc">Total shots taken</div>
        </div>
        """, unsafe_allow_html=True)

# ── Bubble scatter plot ───────────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Shot Volume vs Goals Scored Map</h2>
</div>
""", unsafe_allow_html=True)
st.plotly_chart(team_dna_scatter(f_teams), width='stretch')

# ── Dynamic Team Style Grid ───────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Nations Profile Cards</h2>
</div>
""", unsafe_allow_html=True)

ranked_teams = f_teams.sort_values(sort_field, ascending=False).reset_index(drop=True)

# Grid layout with 4 cards per row
total_ranked = len(ranked_teams)
for r_idx in range(0, min(total_ranked, 20), 4):
    row_t = ranked_teams.iloc[r_idx : r_idx + 4]
    row_cols = st.columns(4)
    for c_idx, (_, t) in enumerate(row_t.iterrows()):
        style_txt = team_style_label(t["goals_per_shot"], t["total_shots"] / max(t["players"], 1))
        conv_c = "#048a5f" if t["goals_per_shot"] > 0.18 else ("#e01a22" if t["goals_per_shot"] < 0.10 else "#0f2547")
        with row_cols[c_idx]:
            st.markdown(f"""
            <div class="app-card" style="text-align:center;">
              <div style="font-size:2rem; margin-bottom:0.25rem;">{flag(t['team'])}</div>
              <div style="font-weight:800; font-size:1rem; color:#0f2547; margin-bottom:0.25rem;">{t['team']}</div>
              <div style="font-size:0.7rem; color:#64748b; font-weight:700; text-transform:uppercase; margin-bottom:0.75rem;">
                {t['confederation']}
              </div>
              <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:0.5rem; text-align:center; border-top:1px solid #f1f5f9; padding-top:0.75rem;">
                <div>
                  <strong style="font-size:1rem;color:#0f2547;">{int(t['total_goals'])}</strong>
                  <div style="font-size:0.65rem;color:#94a3b8;text-transform:uppercase;">goals</div>
                </div>
                <div>
                  <strong style="font-size:1rem;color:{conv_c};">{t['goals_per_shot']:.0%}</strong>
                  <div style="font-size:0.65rem;color:#94a3b8;text-transform:uppercase;">conv.</div>
                </div>
                <div>
                  <strong style="font-size:1rem;color:#0f2547;">{int(t['total_shots'])}</strong>
                  <div style="font-size:0.65rem;color:#94a3b8;text-transform:uppercase;">shots</div>
                </div>
              </div>
              <div style="margin-top:0.75rem; font-size:0.75rem; font-weight:700; background:#f1f5f9; padding:0.3rem; border-radius:4px; color:#0f2547;">
                {style_txt}
              </div>
            </div>
            """, unsafe_allow_html=True)

# ── Team Deep Dive spotlight ──────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Nation Spotlight Detail</h2>
</div>
""", unsafe_allow_html=True)

spotlight_nations = sorted(f_teams["team"].tolist())
spotlight_team = st.selectbox("Select nation to spotlight:", spotlight_nations)
team_row = f_teams[f_teams["team"] == spotlight_team].iloc[0]
team_players = players[players["team"] == spotlight_team].copy()

if not team_players.empty:
    style_label = team_style_label(team_row["goals_per_shot"], team_row["total_shots"] / max(team_row["players"], 1))
    shots_pp = team_row["total_shots"] / max(team_row["players"], 1)

    st.markdown(f"""
    <div class="app-card">
      <div style="display:flex; align-items:center; gap:1rem; margin-bottom:1rem;">
        <span style="font-size:2.5rem;">{flag(spotlight_team)}</span>
        <div>
          <h3 style="margin:0; font-family:'Montserrat',sans-serif; font-size:1.3rem; text-transform:uppercase;">{spotlight_team}</h3>
          <span style="font-size:0.8rem; font-weight:700; color:#048a5f;">{style_label}</span>
        </div>
      </div>
      <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:1rem; text-align:center; border-top:1px solid #f1f5f9; padding-top:1rem;">
        <div>
          <div style="font-family:'Montserrat',sans-serif; font-weight:800; font-size:1.4rem; color:#e01a22;">{int(team_row['total_goals'])}</div>
          <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase;">Goals</div>
        </div>
        <div>
          <div style="font-family:'Montserrat',sans-serif; font-weight:800; font-size:1.4rem; color:#0f2547;">{team_row['goals_per_shot']:.0%}</div>
          <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase;">Conversion</div>
        </div>
        <div>
          <div style="font-family:'Montserrat',sans-serif; font-weight:800; font-size:1.4rem; color:#0f2547;">{int(team_row['total_shots'])}</div>
          <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase;">Shots</div>
        </div>
        <div>
          <div style="font-family:'Montserrat',sans-serif; font-weight:800; font-size:1.4rem; color:#0f2547;">{shots_pp:.1f}</div>
          <div style="font-size:0.65rem; color:#94a3b8; text-transform:uppercase;">Shots / Player</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Players table for this team
    team_scorers = team_players[team_players["goals"] > 0].nlargest(5, "goals")[
        ["player", "position", "goals", "assists", "goals_per90", "shots"]
    ]
    if not team_scorers.empty:
        st.markdown(f"**Top scorers for {spotlight_team}:**")
        team_scorers = team_scorers.rename(columns={
            "player": "Player", "position": "Position", "goals": "Goals",
            "assists": "Assists", "goals_per90": "Goals / 90", "shots": "Shots"
        })
        team_scorers["Goals / 90"] = team_scorers["Goals / 90"].round(2)
        st.dataframe(team_scorers.reset_index(drop=True), hide_index=True, width='stretch', height=200)

# ── Footer ────────────────────────────────────────────────────
st.markdown(f"""
<div class="site-footer">
  <div class="site-footer-brand">FIFA WC 2026 Stats</div>
  <div>Team records are derived dynamically from active tournament registries</div>
</div>
""", unsafe_allow_html=True)
