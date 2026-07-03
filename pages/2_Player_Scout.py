"""
pages/2_Player_Scout.py — Player Comparison
Side-by-side metric comparison and percentile indicators.
"""

import streamlit as st
import pandas as pd
import numpy as np
import base64
import pathlib

from utils.data_loader import inject_css, load_outfield, player_list
from utils.ml_model    import build_xg_model, compute_radar_values, get_percentile, RADAR_ATTRS
from utils.charts      import radar_chart, percentile_bar_chart
from utils.api_client  import flag

# ── Streamlit Config ──────────────────────────────────────────
st.set_page_config(
    page_title="Player Comparison · FIFA 2026",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

inject_css()

# ── Header with Banner Image ──────────────────────────────────
bg_path = "assets/players_matchup.png"
bg_tag = ""
try:
    bg_bytes = pathlib.Path(bg_path).read_bytes()
    bg_b64 = base64.b64encode(bg_bytes).decode()
    bg_tag = f'<img class="bg" src="data:image/png;base64,{bg_b64}" alt="Player Matchup">'
except Exception:
    pass

st.markdown(f"""
<div class="premium-hero">
  {bg_tag}
  <div class="overlay" style="background: linear-gradient(90deg, rgba(15,23,42,0.95) 0%, rgba(15,23,42,0.7) 50%, rgba(15,23,42,0.2) 100%);"></div>
  <div class="hero-content">
    <div class="eyebrow" style="color:#e01a22; font-weight:800; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.4rem;">PLAYER COMPARISON</div>
    <h1 style="color:#ffffff !important;">Player Matchups</h1>
    <p class="hero-sub" style="color:rgba(255,255,255,0.8);">
      Compare stats between any two outfield players. Attribute bars indicate their percentile rank compared to all tournament players.
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Load Data ─────────────────────────────────────────────────
with st.spinner(""):
    raw = load_outfield()
    df  = build_xg_model(raw)
    players = player_list()

# Helper for index search
def get_idx(name):
    try:
        return players.index(name)
    except ValueError:
        return 0

# ── Selectors ─────────────────────────────────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Select Players</h2>
</div>
""", unsafe_allow_html=True)

col_sel1, col_vs, col_sel2 = st.columns([5, 1, 5])

with col_sel1:
    p_a = st.selectbox(
        "Player A",
        players,
        index=get_idx("Kylian Mbappé") if "Kylian Mbappé" in players else 0,
        key="sel_pa",
    )

with col_vs:
    st.markdown("""
    <div style="display:flex; align-items:center; justify-content:center; height:80px; 
                font-family:'Montserrat',sans-serif; font-weight:900; font-size:1.6rem; color:#94a3b8;">VS</div>
    """, unsafe_allow_html=True)

with col_sel2:
    p_b = st.selectbox(
        "Player B",
        players,
        index=get_idx("Lionel Messi") if "Lionel Messi" in players else min(1, len(players)-1),
        key="sel_pb",
    )

if p_a == p_b:
    st.warning("Select two different players to compare.")
    st.stop()

# Get rows
row_a = df[df["player"] == p_a].iloc[0]
row_b = df[df["player"] == p_b].iloc[0]

# ── Matchup Card ──────────────────────────────────────────────
st.markdown(f"""
<div class="card-matchup">
  <div class="matchup-player">
    <div style="font-size:2.5rem;">{flag(row_a['team'])}</div>
    <div class="name">{p_a}</div>
    <div class="team">{row_a['team']} · {row_a['position']}</div>
  </div>
  <div class="matchup-vs">VS</div>
  <div class="matchup-player">
    <div style="font-size:2.5rem;">{flag(row_b['team'])}</div>
    <div class="name">{p_b}</div>
    <div class="team">{row_b['team']} · {row_b['position']}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Verdict ───────────────────────────────────────────────────
vals_a = compute_radar_values(p_a, df)
vals_b = compute_radar_values(p_b, df)
score_a = sum(vals_a.values())
score_b = sum(vals_b.values())
diff = abs(score_a - score_b)

if diff < 40:
    verdict = "Players are statistically similar across the tracked attributes."
    v_class = "border-left: 4px solid #94a3b8;"
elif score_a > score_b:
    verdict = f"{p_a} ranks higher in key attributes compared to {p_b}."
    v_class = "border-left: 4px solid #e01a22;"
else:
    verdict = f"{p_b} ranks higher in key attributes compared to {p_a}."
    v_class = "border-left: 4px solid #048a5f;"

st.markdown(f"""
<div class="app-card" style="{v_class}">
  <div class="app-card-title">Analysis Verdict</div>
  <p style="font-size:1.05rem; font-weight:600; margin:0;">{verdict}</p>
</div>
""", unsafe_allow_html=True)

# ── Percentile Metrics (Custom Meters) ───────────────────────
st.markdown("""
<div class="clean-header">
  <h2>Metric Rankings (Percentiles)</h2>
</div>
""", unsafe_allow_html=True)

for attr, label in RADAR_ATTRS.items():
    pct_a = vals_a.get(label, 0)
    pct_b = vals_b.get(label, 0)

    st.markdown(f"""
    <div class="meter-row">
      <div class="meter-label">{label}</div>
      <div class="meter-container">
        <span style="font-size:0.8rem; color:#e01a22; font-weight:700; width:45px; text-align:right;">{pct_a:.0f}%</span>
        <div class="meter-bar">
          <div class="meter-fill-a" style="width:{pct_a}%;"></div>
        </div>
        <div class="meter-bar" style="transform: scaleX(-1);">
          <div class="meter-fill-b" style="width:{pct_b}%;"></div>
        </div>
        <span style="font-size:0.8rem; color:#048a5f; font-weight:700; width:45px;">{pct_b:.0f}%</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Chart Visualizations ──────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_c1, col_c2 = st.columns(2)

with col_c1:
    st.plotly_chart(radar_chart(p_a, p_b, vals_a, vals_b), width='stretch')
with col_c2:
    st.plotly_chart(percentile_bar_chart(p_a, p_b, vals_a, vals_b), width='stretch')

# ── Stats Table ───────────────────────────────────────────────
with st.expander("Full Stats Sheet"):
    stat_definitions = [
        ("Games Played", "games"),
        ("Minutes Played", "minutes"),
        ("Goals Scored", "goals"),
        ("Assists", "assists"),
        ("Goals / 90 Mins", "goals_per90"),
        ("Assists / 90 Mins", "assists_per90"),
        ("Shots Taken", "shots"),
        ("Shots on Target", "shots_on_target"),
        ("Expected Goals (xG)", "xG"),
        ("Expected Assists (xA)", "xA"),
        ("Plus/Minus per 90", "plus_minus_per90"),
        ("Yellow Cards", "cards_yellow"),
        ("Fouls", "fouls"),
    ]
    t_rows = []
    for label, col in stat_definitions:
        if col not in df.columns:
            continue
        v_a = float(row_a.get(col, 0))
        v_b = float(row_b.get(col, 0))
        invert = col in ("fouls", "cards_yellow")
        better = "A" if ((v_a > v_b) != invert) else ("B" if (v_b > v_a) != invert else "=")

        t_rows.append({
            "Stat Attribute": label,
            p_a: f"{v_a:.2f}".rstrip("0").rstrip(".") if "." in f"{v_a}" else str(int(v_a)),
            "Leader": p_a if better == "A" else (p_b if better == "B" else "Draw"),
            p_b: f"{v_b:.2f}".rstrip("0").rstrip(".") if "." in f"{v_b}" else str(int(v_b)),
        })
    st.dataframe(pd.DataFrame(t_rows), hide_index=True, width='stretch')

# ── Footer ────────────────────────────────────────────────────
st.markdown(f"""
<div class="site-footer">
  <div class="site-footer-brand">FIFA WC 2026 Stats Centre</div>
  <div>Dataset: FIFA World Cup 2026 Player Stats by Swapnil Tripathi (Kaggle)</div>
</div>
""", unsafe_allow_html=True)
