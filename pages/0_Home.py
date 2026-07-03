"""
pages/0_Home.py — FIFA World Cup 2026 Stats & Analysis
Home Page / Match Centre.
"""

import streamlit as st
import pandas as pd
import base64
import pathlib

from utils.data_loader  import inject_css, load_outfield, load_team_stats
from utils.api_client   import (
    get_matches, get_groups, time_since_update, flag,
    parse_completed_matches, parse_upcoming_matches,
    total_goals_from_matches, get_current_round
)
from utils.ml_model import build_xg_model

# ── Streamlit Config with Favicon ─────────────────────────────
st.set_page_config(
    page_title="FIFA World Cup 2026 — Stats & Analysis",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Load Static Page Data (confederation cards, nav cards) ────
with st.spinner(""):
    teams = load_team_stats()
    df    = load_outfield()

# ── Header ────────────────────────────────────────────────────
update_status = time_since_update("matches")
logo_path = "assets/favicon-96x96.png"
logo_tag = ""
try:
    logo_bytes = pathlib.Path(logo_path).read_bytes()
    logo_b64 = base64.b64encode(logo_bytes).decode()
    logo_tag = f'<img src="data:image/png;base64,{logo_b64}" style="height:32px; border-radius:4px;">'
except Exception:
    pass

st.markdown(f"""
<div class="site-header">
  <div class="brand">
    {logo_tag}
    <span class="brand-tag" style="background:#0f2547;">FIFA</span>
    WC 2026 Stats
  </div>
  <div style="font-size:0.8rem; color:#64748b;">
    {update_status}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Premium Hero (Mbappé Silhouette Mockup) ──────────────────
player_path = "assets/player_header.png"
player_tag = ""
try:
    player_bytes = pathlib.Path(player_path).read_bytes()
    player_b64 = base64.b64encode(player_bytes).decode()
    player_tag = f'<img class="hero-player" src="data:image/png;base64,{player_b64}" alt="Player Profile">'
except Exception:
    pass

st.markdown(f"""
<div class="premium-hero">
  <div class="hero-text">
    <div class="eyebrow" style="font-family:'Montserrat',sans-serif;font-size:0.75rem;font-weight:900;color:#e01a22;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:0.4rem;">TOURNAMENT CENTRE</div>
    <h1>You can be the<br>king of stats</h1>
    <p class="sub">
      Analyzing the most interesting FIFA 2026 World Cup data metrics. Expected goals, player comparisons, and live match updates.
    </p>
  </div>
  <div class="hero-img-container">
    {player_tag}
  </div>
</div>
""", unsafe_allow_html=True)

# ── Quick Stats Strip + Live Matches: AUTO-REFRESHING FRAGMENT ───────────────
# This fragment re-runs every 5 minutes automatically without full page reload
@st.fragment(run_every=300)
def live_section():
    raw_matches, _ = get_matches()
    raw_groups, _  = get_groups()
    matches  = parse_completed_matches(raw_matches)
    upcoming = parse_upcoming_matches(raw_matches)
    api_goals = total_goals_from_matches(matches)

    df_live = load_outfield()
    total_goals   = api_goals if api_goals > 0 else int(df_live["goals"].sum())
    total_assists = int(df_live["assists"].sum())
    total_players = len(df_live)
    total_teams   = df_live["team"].nunique()
    avg_goals     = round(total_goals / max(len(matches), 1), 2) if matches else round(df_live["goals_per90"].mean(), 2)
    current_round = get_current_round()

    # ── Quick Stats Strip ───────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Goals Scored", f"{total_goals}", help="Total goals from all completed matches")
    with col2:
        st.metric("Assists", f"{total_assists}")
    with col3:
        st.metric("Tracked Players", f"{total_players}")
    with col4:
        st.metric("Nations", f"{total_teams}")
    with col5:
        st.metric("Avg Goals / Match", f"{avg_goals}")

    # ── Recent Matches ───────────────────────────────────────────────────
    st.markdown(f"""
    <div class="clean-header">
      <h2>Recent Matches</h2>
      <span class="tag">{current_round}</span>
    </div>
    """, unsafe_allow_html=True)

    recent = sorted(matches, key=lambda m: m.get("date", ""), reverse=True)[:5]
    if recent:
        for match in recent:
            home_flag = flag(match["home"])
            away_flag = flag(match["away"])
            st.markdown(f"""
            <div class="live-match-row">
              <div style="display:flex; align-items:center; gap:1.5rem; flex:1;">
                <div class="live-badge" style="background:rgba(15,37,71,0.06); color:#0f2547; border-color:rgba(15,37,71,0.12);">
                  {match.get('stage', 'Match')}
                </div>
                <span style="font-size:1.05rem; font-weight:700;">
                  {home_flag} {match['home']}
                  <span style="color:#e01a22; margin:0 0.5rem; font-family:Montserrat,sans-serif; font-size:1.3rem;">
                    {match['home_score']} – {match['away_score']}
                  </span>
                  {match['away']} {away_flag}
                </span>
              </div>
              <div style="font-size:0.82rem; color:#94a3b8; font-weight:600;">Completed</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No match results available yet.")

    # ── Upcoming Fixtures ────────────────────────────────────────────
    if upcoming:
        st.markdown("""
        <div class="clean-header">
          <h2>Upcoming Fixtures</h2>
          <span class="tag">Next Matches</span>
        </div>
        """, unsafe_allow_html=True)
        for match in upcoming[:4]:
            home_flag = flag(match["home"])
            away_flag = flag(match["away"])
            date_label = match.get("date", "").split(" ")[0] if match.get("date") else ""
            st.markdown(f"""
            <div class="live-match-row">
              <div style="display:flex; align-items:center; gap:1.5rem; flex:1;">
                <div class="live-badge" style="background:rgba(224,26,34,0.08); color:#e01a22; border-color:rgba(224,26,34,0.2);">
                  {match.get('stage', 'Match')}
                </div>
                <span style="font-size:1.05rem; font-weight:700;">
                  {home_flag} {match['home']}
                  <span style="color:#94a3b8; margin:0 0.75rem; font-size:1rem;">vs</span>
                  {match['away']} {away_flag}
                </span>
              </div>
              <div style="font-size:0.82rem; color:#94a3b8; font-weight:600;">{date_label}</div>
            </div>
            """, unsafe_allow_html=True)

live_section()


# ── Confederation Cards (Mockup Leagues Grid) ─────────────────
st.markdown("""
<div class="clean-header">
  <h2>Confederation Performance</h2>
  <span class="tag">Continental Groups</span>
</div>
""", unsafe_allow_html=True)

# Compute quick stats per confederation
conf_agg = teams.groupby("confederation").agg(
    goals=("total_goals", "sum"),
    squads=("team", "count")
).reset_index()

card_cols = st.columns(5)
conf_styles = {
    "UEFA": ("card-uefa", "UEFA"),
    "CONMEBOL": ("card-conmebol", "CONMEBOL"),
    "CONCACAF": ("card-concacaf", "CONCACAF"),
    "CAF": ("card-caf", "CAF"),
    "AFC": ("card-afc", "AFC"),
}

for idx, (conf_name, style_tuple) in enumerate(conf_styles.items()):
    c_style, c_text = style_tuple
    row_c = conf_agg[conf_agg["confederation"] == conf_name]
    c_goals = int(row_c["goals"].values[0]) if not row_c.empty else 0
    c_squads = int(row_c["squads"].values[0]) if not row_c.empty else 0

    with card_cols[idx]:
        st.markdown(f"""
        <div class="conf-card {c_style}">
          <div class="conf-card-header">
            <span class="conf-card-title">{conf_name}</span>
            <span class="conf-card-tag" style="background:rgba(15,37,71,0.06); color:#0f2547;">Active</span>
          </div>
          <div>
            <div class="conf-card-body">{c_goals}</div>
            <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase; margin-top:0.25rem; opacity:0.8;">
              Goals · {c_squads} Nations
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── Navigation Cards ──────────────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Analysis Hub Pages</h2>
</div>
""", unsafe_allow_html=True)

nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    st.markdown("""
    <div class="app-card" style="height:140px;">
      <div class="app-card-title">Analysis Mode</div>
      <strong style="font-size:1.1rem;color:#0f2547;">Shooting Analysis</strong>
      <p style="font-size:0.8rem;color:#64748b;margin-top:0.25rem;">
        Determines which players finish above or below their estimated chances.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_xG_Engine.py", label="Open Shooting Analysis", width='stretch')

with nav2:
    st.markdown("""
    <div class="app-card" style="height:140px;">
      <div class="app-card-title">Scouting Comparison</div>
      <strong style="font-size:1.1rem;color:#0f2547;">Player Comparison</strong>
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
      <strong style="font-size:1.1rem;color:#0f2547;">Goal Projections</strong>
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
      <strong style="font-size:1.1rem;color:#0f2547;">Team Performance</strong>
      <p style="font-size:0.8rem;color:#64748b;margin-top:0.25rem;">
        Analysis of aggregate shots vs actual goals per nation.
      </p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_Team_DNA.py", label="Open Team Performance Page", width='stretch')

# ── Footer ────────────────────────────────────────────────────
st.markdown(f"""
<div class="site-footer">
  <div class="site-footer-brand">FIFA WC 2026 Stats Centre</div>
  <div>Dataset: FIFA World Cup 2026 Player Stats by Swapnil Tripathi (Kaggle) · Not affiliated with FIFA</div>
</div>
""", unsafe_allow_html=True)
