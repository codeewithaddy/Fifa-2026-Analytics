"""
app.py — FIFA World Cup 2026 Stats & Analysis
Clean, professional sports companion dashboard.
"""

import streamlit as st
import pandas as pd
import base64
import pathlib

from utils.data_loader  import inject_css, load_outfield, load_team_stats
from utils.api_client   import (
    get_matches, get_groups, time_since_update, flag,
    parse_completed_matches, parse_upcoming_matches, total_goals_from_matches
)
from utils.ml_model import build_xg_model

# ── Streamlit Config ──────────────────────────────────────────
st.set_page_config(
    page_title="FIFA World Cup 2026 — Stats & Analysis",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Load Live/Local Data ──────────────────────────────────────
with st.spinner(""):
    df = load_outfield()
    teams = load_team_stats()
    xg_df = build_xg_model(df)
    raw_matches, _ = get_matches()
    raw_groups, _  = get_groups()

matches   = parse_completed_matches(raw_matches)
upcoming  = parse_upcoming_matches(raw_matches)
api_goals = total_goals_from_matches(matches)

# Statistics normalization
total_goals   = api_goals if api_goals > 0 else int(df["goals"].sum())
total_assists = int(df["assists"].sum())
total_players = len(df)
total_teams   = df["team"].nunique()
avg_goals     = round(total_goals / max(len(matches), 1), 2) if matches else round(df["goals_per90"].mean(), 2)

# ── Header ────────────────────────────────────────────────────
update_status = time_since_update("matches")
st.markdown(f"""
<div class="site-header">
  <div class="brand">
    <span class="brand-tag">FIFA</span>
    WC 2026 Stats
  </div>
  <div style="font-size:0.8rem; color:rgba(255,255,255,0.7);">
    Status: {update_status}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Hero Card (No AI Marketing text) ──────────────────────────
st.markdown("""
<div class="clean-hero">
  <h1>Nations &amp; Players Stats Tracker</h1>
  <p class="sub">
    Visualizing shot quality, player performance relative to expectations, and live tournament outcomes.
  </p>
</div>
""", unsafe_allow_html=True)

# ── Quick Tournament Figures ─────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Tournament Figures</h2>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Goals Scored", f"{total_goals}", help="Total goals from tracked players")
with col2:
    st.metric("Assists", f"{total_assists}")
with col3:
    st.metric("Tracked Players", f"{total_players}")
with col4:
    st.metric("Nations", f"{total_teams}")
with col5:
    st.metric("Avg Goals / Match", f"{avg_goals}")

# ── Latest Match Scores ───────────────────────────────────────
if matches:
    st.markdown("""
    <div class="clean-header">
      <h2>Recent Match Outcomes</h2>
      <span class="tag">Live Scores</span>
    </div>
    """, unsafe_allow_html=True)

    m_cols = st.columns(min(4, len(matches)))
    for idx, match in enumerate(matches[:4]):
        home_flag = flag(match["home"])
        away_flag = flag(match["away"])
        with m_cols[idx]:
            st.markdown(f"""
            <div class="app-card">
              <div class="app-card-title">{match['stage']}</div>
              <div style="display:flex; align-items:center; justify-content:space-between; margin:0.5rem 0;">
                <span>{home_flag} {match['home']}</span>
                <strong style="font-size:1.2rem;">{match['home_score']}</strong>
              </div>
              <div style="display:flex; align-items:center; justify-content:space-between; margin:0.5rem 0;">
                <span>{away_flag} {match['away']}</span>
                <strong style="font-size:1.2rem;">{match['away_score']}</strong>
              </div>
              <div class="app-card-desc" style="font-size:0.75rem; text-align:right;">Finished</div>
            </div>
            """, unsafe_allow_html=True)

# ── Top Scorers Overview ──────────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Top Scorers</h2>
  <span class="tag">Goals Leaderboard</span>
</div>
""", unsafe_allow_html=True)

top_scorers = df[df["goals"] > 0].nlargest(5, "goals")
s_cols = st.columns(5)
positions_medals = ["1st", "2nd", "3rd", "4th", "5th"]

for idx, (_, row) in enumerate(top_scorers.iterrows()):
    p_name = row["player"]
    p_team = row["team"]
    p_goals = int(row["goals"])

    # Calculate xG delta class safely
    p_delta_row = xg_df[xg_df["player"] == p_name]
    p_delta = float(p_delta_row["delta_g"].values[0]) if not p_delta_row.empty else 0.0

    if p_delta >= 1.0:
        perf_badge = '<span style="color:#048a5f;font-weight:700;">Clinical</span>'
    elif p_delta <= -1.0:
        perf_badge = '<span style="color:#e01a22;font-weight:700;">Unlucky</span>'
    else:
        perf_badge = '<span style="color:#64748b;">Expected level</span>'

    with s_cols[idx]:
        st.markdown(f"""
        <div class="app-card" style="text-align:center;">
          <div class="app-card-title">{positions_medals[idx]} Player</div>
          <div style="font-size:2rem; margin:0.5rem 0;">{flag(p_team)}</div>
          <div class="app-card-value">{p_goals}</div>
          <div style="font-weight:700; margin-top:0.5rem; font-size:0.95rem;">{p_name}</div>
          <div style="font-size:0.8rem; color:#64748b; margin-bottom:0.5rem;">{p_team}</div>
          <div style="font-size:0.75rem; border-top:1px solid #f1f5f9; padding-top:0.5rem; margin-top:0.5rem;">
            {perf_badge}
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Standings Section ─────────────────────────────────────────
if raw_groups:
    st.markdown("""
    <div class="clean-header">
      <h2>Group Standings</h2>
      <span class="tag">Live Tables</span>
    </div>
    """, unsafe_allow_html=True)

    try:
        groups_list = raw_groups if isinstance(raw_groups, list) else raw_groups.get("groups", [])
        if groups_list:
            g_cols = st.columns(min(4, len(groups_list)))
            for g_idx, grp in enumerate(groups_list[:4]):
                grp_name  = grp.get("name") or grp.get("group") or f"Group {g_idx+1}"
                grp_teams = grp.get("teams") or grp.get("standings") or []
                with g_cols[g_idx]:
                    st.markdown(f"**{grp_name}**")
                    if grp_teams:
                        t_rows = []
                        for t in grp_teams[:4]:
                            t_name = t.get("team") or t.get("name") or "?"
                            t_pts  = t.get("points") or t.get("pts") or 0
                            t_gf   = t.get("goals_for") or t.get("gf") or 0
                            t_ga   = t.get("goals_against") or t.get("ga") or 0
                            t_rows.append({
                                "Nation": f"{flag(t_name)} {t_name}",
                                "Pts": t_pts,
                                "GF": t_gf,
                                "GA": t_ga,
                                "GD": int(t_gf) - int(t_ga)
                            })
                        st.dataframe(pd.DataFrame(t_rows), hide_index=True, width='stretch', height=170)
    except Exception:
        pass

# ── Navigation Cards ──────────────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Analysis Pages</h2>
</div>
""", unsafe_allow_html=True)

nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    st.markdown("""
    <div class="app-card" style="height:140px;">
      <div class="app-card-title">Analysis Mode</div>
      <strong style="font-size:1.1rem;color:#0f172a;">Shot Quality &amp; Expected Goals</strong>
      <p style="font-size:0.8rem;color:#64748b;margin-top:0.25rem;">
        Determines which players finish above or below their estimated chances.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_xG_Engine.py", label="Open Shot Quality Page", width='stretch')

with nav2:
    st.markdown("""
    <div class="app-card" style="height:140px;">
      <div class="app-card-title">Scouting Comparison</div>
      <strong style="font-size:1.1rem;color:#0f172a;">Player Comparison</strong>
      <p style="font-size:0.8rem;color:#64748b;margin-top:0.25rem;">
        Side-by-side metric comparison and percentile indicators.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Player_Scout.py", label="Open Comparison Page", width='stretch')

with nav3:
    st.markdown("""
    <div class="app-card" style="height:140px;">
      <div class="app-card-title">Scoring Projections</div>
      <strong style="font-size:1.1rem;color:#0f172a;">Top Scorers &amp; Projections</strong>
      <p style="font-size:0.8rem;color:#64748b;margin-top:0.25rem;">
        Projected final goal totals based on goals per game rates.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Golden_Boot.py", label="Open Projections Page", width='stretch')

with nav4:
    st.markdown("""
    <div class="app-card" style="height:140px;">
      <div class="app-card-title">Team Performance</div>
      <strong style="font-size:1.1rem;color:#0f172a;">Team Performance Analysis</strong>
      <p style="font-size:0.8rem;color:#64748b;margin-top:0.25rem;">
        Analysis of aggregate shots vs actual goals per nation.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_Team_DNA.py", label="Open Team Performance Page", width='stretch')

# ── Footer ────────────────────────────────────────────────────
st.markdown(f"""
<div class="site-footer">
  <div class="site-footer-brand">FIFA WC 2026 Stats</div>
  <div>Updated: {update_status} · Data sources: worldcup26.ir &amp; local records</div>
</div>
""", unsafe_allow_html=True)
