"""
app.py — FIFA 2026 Intelligence Hub
Home / Landing Page
"""

import streamlit as st
import pandas as pd
from utils.data_loader import inject_css, load_outfield, load_team_stats

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="FIFA 2026 Intelligence Hub",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Load Data ─────────────────────────────────────────────────
with st.spinner("Loading tournament data…"):
    df   = load_outfield()
    team = load_team_stats()


# ── Hero Banner ───────────────────────────────────────────────
st.markdown("""
<div class="hub-hero">
  <div class="subtitle">⚽ FIFA World Cup 2026 · Live Analytics</div>
  <h1>FIFA 2026<br>Intelligence Hub</h1>
  <p class="desc">
    ML-powered insights: Expected Goals, player radar comparisons,
    Golden Boot projections, and team DNA analysis — all from real tournament data.
  </p>
</div>
""", unsafe_allow_html=True)


# ── Tournament Headline Stats ─────────────────────────────────
total_goals   = int(df["goals"].sum())
total_assists = int(df["assists"].sum())
total_players = len(df)
total_teams   = df["team"].nunique()

top_scorer_row = df.loc[df["goals"].idxmax()]
top_assist_row = df.loc[df["assists"].idxmax()]

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("⚽ Total Goals", f"{total_goals:,}", help="All outfield player goals in the dataset")
with col2:
    st.metric("🎯 Total Assists", f"{total_assists:,}")
with col3:
    st.metric("👥 Players Tracked", f"{total_players:,}")
with col4:
    st.metric("🏟️ Teams", f"{total_teams:,}")
with col5:
    avg_goals_per_game = round(df["goals_per90"].mean(), 2)
    st.metric("📈 Avg Goals/90", f"{avg_goals_per_game}")

st.markdown("<hr>", unsafe_allow_html=True)


# ── Top Performers Strip ──────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">🏅</span>
  <h2>Tournament Leaders</h2>
  <span class="badge">Live</span>
</div>
""", unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.markdown(f"""
    <div class="stat-card">
      <div class="card-label">🥇 Top Scorer</div>
      <div class="card-value">{int(top_scorer_row['goals'])}</div>
      <div class="card-sub"><strong>{top_scorer_row['player']}</strong> · {top_scorer_row['team']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown(f"""
    <div class="stat-card">
      <div class="card-label">🎯 Top Assister</div>
      <div class="card-value">{int(top_assist_row['assists'])}</div>
      <div class="card-sub"><strong>{top_assist_row['player']}</strong> · {top_assist_row['team']}</div>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    # Most clinical team
    best_team = team.loc[team["goals_per_shot"].idxmax()]
    st.markdown(f"""
    <div class="stat-card">
      <div class="card-label">⚡ Most Clinical Team</div>
      <div class="card-value">{best_team['goals_per_shot']:.0%}</div>
      <div class="card-sub"><strong>{best_team['team']}</strong> conversion rate</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ── Navigation Cards ──────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">🔬</span>
  <h2>Analysis Modules</h2>
</div>
""", unsafe_allow_html=True)

nav1, nav2, nav3, nav4 = st.columns(4)

with nav1:
    st.markdown("""
    <div class="nav-card">
      <div class="icon">🤖</div>
      <h3>xG Engine</h3>
      <p>ML-based Expected Goals model. Discover who's lucky and who's elite.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/1_xG_Engine.py", label="Open xG Engine →", use_container_width=True)

with nav2:
    st.markdown("""
    <div class="nav-card">
      <div class="icon">🕷️</div>
      <h3>Player Scout</h3>
      <p>Head-to-head radar chart comparison across 6 key attributes.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/2_Player_Scout.py", label="Open Player Scout →", use_container_width=True)

with nav3:
    st.markdown("""
    <div class="nav-card">
      <div class="icon">🥾</div>
      <h3>Golden Boot</h3>
      <p>Mathematical goal projections to tournament end. The real race.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/3_Golden_Boot.py", label="Open Golden Boot →", use_container_width=True)

with nav4:
    st.markdown("""
    <div class="nav-card">
      <div class="icon">🧬</div>
      <h3>Team DNA</h3>
      <p>Team styles, shot efficiency, and which nations punch above their weight.</p>
    </div>
    """, unsafe_allow_html=True)
    st.page_link("pages/4_Team_DNA.py", label="Open Team DNA →", use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ── Quick Stats Table ─────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">📊</span>
  <h2>Top 15 Scorers</h2>
  <span class="badge">Current</span>
</div>
""", unsafe_allow_html=True)

top15 = (
    df[df["goals"] > 0]
    .nlargest(15, "goals")
    [["player", "team", "goals", "assists", "goals_per90",
      "assists_per90", "shots", "minutes"]]
    .rename(columns={
        "player": "Player", "team": "Team",
        "goals": "G", "assists": "A",
        "goals_per90": "G/90", "assists_per90": "A/90",
        "shots": "Shots", "minutes": "Mins",
    })
    .reset_index(drop=True)
)
top15.index += 1
top15["G/90"] = top15["G/90"].round(2)
top15["A/90"] = top15["A/90"].round(2)
top15["Mins"] = top15["Mins"].astype(int)

st.dataframe(
    top15,
    use_container_width=True,
    height=500,
    column_config={
        "G":    st.column_config.ProgressColumn("Goals", min_value=0, max_value=top15["G"].max()),
        "A":    st.column_config.ProgressColumn("Assists", min_value=0, max_value=top15["A"].max()),
        "G/90": st.column_config.NumberColumn("G/90", format="%.2f"),
        "A/90": st.column_config.NumberColumn("A/90", format="%.2f"),
    },
)

# ── Footer ─────────────────────────────────────────────────────
st.markdown("""
<hr>
<p style="text-align:center; color:rgba(232,237,245,0.35); font-size:0.8rem; font-family:Inter;">
  FIFA 2026 Intelligence Hub · Built with Streamlit & scikit-learn ·
  Data: Kaggle FIFA 2026 Dataset · Not affiliated with FIFA
</p>
""", unsafe_allow_html=True)
