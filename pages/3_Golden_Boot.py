"""
pages/3_Golden_Boot.py — Golden Boot Predictor
FIFA 2026 Intelligence Hub
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.data_loader import inject_css, load_outfield, MAX_GAMES
from utils.ml_model import project_goals
from utils.charts import golden_boot_bar, NAVY_CARD, GOLD, TEAL, WHITE, WHITE_DIM, BORDER, RED, NAVY_MID, _base_layout

st.set_page_config(
    page_title="Golden Boot · FIFA 2026",
    page_icon="🥾",
    layout="wide",
)
inject_css()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="page-title-row">
  <h1>🥾 Golden Boot Predictor</h1>
  <span class="live-badge"><span class="live-dot"></span>Projected</span>
</div>
<p style="color:rgba(232,237,245,0.65); margin-top:-0.5rem; margin-bottom:1.5rem;">
  Mathematical projection of each player's final goal tally based on their current
  scoring rate. The predicted winner may surprise you.
</p>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────
with st.spinner("Calculating projections…"):
    df = load_outfield()

# ── Sidebar controls ──────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Projection Settings")
    max_games = st.slider("Max tournament games", 3, 8, MAX_GAMES,
                          help="FIFA 2026 has 7 rounds (48-team format)")
    min_goals  = st.slider("Min current goals", 1, 5, 1)
    show_n     = st.slider("Show top N players", 5, 20, 10)
    st.markdown("---")
    st.caption(f"Assumes each player continues at their current goals/90 rate for remaining games.")

# ── Project ───────────────────────────────────────────────────
proj = project_goals(df, max_games=max_games)
proj = proj[proj["goals"] >= min_goals].head(show_n)

# ── Hero KPIs ─────────────────────────────────────────────────
if proj.empty:
    st.warning("No players match filters. Lower 'Min current goals'.")
    st.stop()

top_current  = proj.iloc[0]  # Already sorted by goals
top_projected = proj.loc[proj["projected_goals"].idxmax()]

k1, k2, k3, k4 = st.columns(4)
k1.metric("👑 Current Leader",
          f"{int(top_current['goals'])} goals",
          top_current['player'])
k2.metric("🔮 Projected Winner",
          f"{top_projected['projected_goals']:.1f} goals",
          top_projected['player'],
          delta="If current rate holds" if top_projected['player'] != top_current['player'] else "Same player")
k3.metric("🏟️ Max Games",      str(max_games))
k4.metric("👥 Players Tracked", str(len(proj)))

st.markdown("<hr>", unsafe_allow_html=True)

# ── Main projection chart ─────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">📈</span>
  <h2>Goal Projection Chart</h2>
  <span class="badge">7-Game Total</span>
</div>
""", unsafe_allow_html=True)

st.plotly_chart(golden_boot_bar(proj), use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Trajectory Lines Chart ────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">📉</span>
  <h2>Scoring Trajectory</h2>
  <span class="badge">Game by Game</span>
</div>
<p style="color:rgba(232,237,245,0.55); font-size:0.88rem;">
  Projected cumulative goals for each game of the tournament, based on current goals/90 rate.
</p>
""", unsafe_allow_html=True)

# Build trajectory lines
fig_traj = go.Figure()
palette = [GOLD, TEAL, "#ff6b35", "#c084fc", "#4f8ef7",
           "#fb7185", "#34d399", "#f97316", "#a78bfa", "#38bdf8"]

for i, (_, row) in enumerate(proj.head(8).iterrows()):
    games = list(range(0, max_games + 1))
    goals_traj = [
        min(row["goals"] + row["goals_per90"] * max(0, g - float(row["games_played_est"])), 99)
        if g >= float(row["games_played_est"])
        else row["goals"] * (g / max(float(row["games_played_est"]), 1))
        for g in games
    ]
    goals_traj[0] = 0

    fig_traj.add_trace(go.Scatter(
        x=games, y=goals_traj,
        mode="lines+markers",
        name=row["player"],
        line=dict(color=palette[i % len(palette)], width=2.5),
        marker=dict(size=6, color=palette[i % len(palette)]),
        hovertemplate=f"<b>{row['player']}</b><br>Game %{{x}}: %{{y:.1f}} goals<extra></extra>",
    ))

# Mark current point
for i, (_, row) in enumerate(proj.head(8).iterrows()):
    fig_traj.add_trace(go.Scatter(
        x=[float(row["games_played_est"])],
        y=[float(row["goals"])],
        mode="markers",
        marker=dict(size=14, symbol="diamond", color=palette[i % len(palette)],
                    line=dict(width=2, color="white")),
        showlegend=False,
        hovertemplate=f"<b>{row['player']}</b><br>Current: {int(row['goals'])} goals<extra></extra>",
    ))

fig_traj.add_vline(
    x=float(proj["games_played_est"].mean()),
    line_dash="dot", line_color=WHITE_DIM, line_width=1,
    annotation_text="← Actual | Projected →",
    annotation_font=dict(color=WHITE_DIM, size=10),
)

fig_traj.update_layout(
    **_base_layout(
        title=dict(text="Projected Cumulative Goals by Game",
                   font=dict(family="Outfit", size=18, color=WHITE)),
        xaxis=dict(title="Game Number", tickvals=list(range(0, max_games + 1))),
        yaxis=dict(title="Cumulative Goals", rangemode="tozero"),
        height=460,
    )
)
st.plotly_chart(fig_traj, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Data Table ────────────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">📋</span>
  <h2>Full Projection Table</h2>
</div>
""", unsafe_allow_html=True)

display = proj.copy()
display["games_played_est"] = display["games_played_est"].round(1)
display["games_remaining"]  = display["games_remaining"].round(1)
display = display.rename(columns={
    "player":           "Player",
    "team":             "Team",
    "goals":            "Current Goals",
    "goals_per90":      "Goals/90",
    "games_played_est": "Est. Games Played",
    "games_remaining":  "Games Left",
    "projected_goals":  "Projected Total",
    "proj_low":         "Proj. Low",
    "proj_high":        "Proj. High",
})
display = display.reset_index(drop=True)
display.index += 1

st.dataframe(
    display,
    use_container_width=True,
    height=420,
    column_config={
        "Current Goals":   st.column_config.ProgressColumn("Current Goals", min_value=0,
                              max_value=int(display["Current Goals"].max()) + 1),
        "Projected Total": st.column_config.NumberColumn("🔮 Projected", format="%.1f"),
        "Goals/90":        st.column_config.NumberColumn("Goals/90", format="%.3f"),
    },
)

with st.expander("📖 How the Projection Works"):
    st.markdown("""
    ### Projection Methodology
    
    **Formula:**
    ```
    Projected Goals = Current Goals + Goals_per_90 × Games_Remaining
    ```
    
    **Games Remaining** = `max_games − estimated_games_played`  
    where `estimated_games_played = total_minutes / 90`
    
    **Confidence Band (±):**  
    Based on ±1 standard deviation of the goals/90 rate among all current scorers,
    multiplied by games remaining.
    
    **Assumptions:**
    - Each game = exactly 90 minutes of play for the player
    - Players maintain their current per-90 scoring rate
    - No injuries, suspensions, or tactical changes
    
    > This is a statistical projection, not a guarantee. Real football is beautifully unpredictable.
    """)

st.markdown("""
<hr>
<p style="text-align:center; color:rgba(232,237,245,0.3); font-size:0.78rem;">
  Golden Boot Predictor · FIFA 2026 Intelligence Hub
</p>
""", unsafe_allow_html=True)
