"""
pages/2_Player_Scout.py — Player Scout & Radar Comparison
FIFA 2026 Intelligence Hub
"""

import streamlit as st
import pandas as pd
import numpy as np
from utils.data_loader import inject_css, load_outfield, player_list
from utils.ml_model import build_xg_model, compute_radar_values, RADAR_ATTRS, get_percentile
from utils.charts import radar_chart, percentile_bar_chart

st.set_page_config(
    page_title="Player Scout · FIFA 2026",
    page_icon="🕷️",
    layout="wide",
)
inject_css()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="page-title-row">
  <h1>🕷️ Player Scout</h1>
  <span class="live-badge"><span class="live-dot"></span>Head-to-Head</span>
</div>
<p style="color:rgba(232,237,245,0.65); margin-top:-0.5rem; margin-bottom:1.5rem;">
  Compare any two players head-to-head across 6 key attributes.
  Radar percentiles calculated across all outfield players.
</p>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────
with st.spinner("Loading player data…"):
    raw     = load_outfield()
    df      = build_xg_model(raw)
    players = player_list()

# ── Player selection ──────────────────────────────────────────
col_sel_a, col_vs, col_sel_b = st.columns([5, 1, 5])

with col_sel_a:
    player_a = st.selectbox(
        "🟡 Player A",
        players,
        index=players.index("Kylian Mbappé") if "Kylian Mbappé" in players
              else players.index(players[0]),
        key="player_a",
    )

with col_vs:
    st.markdown(
        "<div style='display:flex;align-items:center;justify-content:center;"
        "height:100%;padding-top:1.8rem;font-family:Outfit;font-weight:900;"
        "font-size:2rem;color:#f5c518;'>VS</div>",
        unsafe_allow_html=True,
    )

with col_sel_b:
    # Default to second player
    default_b_idx = 1 if len(players) > 1 else 0
    if "Lionel Messi" in players:
        default_b_idx = players.index("Lionel Messi")
    player_b = st.selectbox(
        "🩵 Player B",
        players,
        index=default_b_idx,
        key="player_b",
    )

# ── Guard: same player ────────────────────────────────────────
if player_a == player_b:
    st.warning("⚠️ Please select two different players to compare.")
    st.stop()

# ── Fetch rows ────────────────────────────────────────────────
row_a = df[df["player"] == player_a].iloc[0]
row_b = df[df["player"] == player_b].iloc[0]

# ── VS Header Card ────────────────────────────────────────────
st.markdown(f"""
<div class="vs-header">
  <div class="vs-player">
    <div class="name">{player_a}</div>
    <div class="team">{row_a['team']} · {row_a.get('position','—')}</div>
  </div>
  <div class="vs-divider">⚔️</div>
  <div class="vs-player">
    <div class="name">{player_b}</div>
    <div class="team">{row_b['team']} · {row_b.get('position','—')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Compute radar values ──────────────────────────────────────
vals_a = compute_radar_values(player_a, df)
vals_b = compute_radar_values(player_b, df)

# ── Radar + Percentile Bar ────────────────────────────────────
radar_col, bar_col = st.columns([1, 1])

with radar_col:
    st.markdown("""
    <div class="section-header">
      <span class="section-icon">🕷️</span>
      <h2>Radar Comparison</h2>
    </div>
    """, unsafe_allow_html=True)
    fig_radar = radar_chart(player_a, player_b, vals_a, vals_b)
    st.plotly_chart(fig_radar, use_container_width=True)

with bar_col:
    st.markdown("""
    <div class="section-header">
      <span class="section-icon">📊</span>
      <h2>Attribute Percentiles</h2>
    </div>
    """, unsafe_allow_html=True)
    fig_bar = percentile_bar_chart(player_a, player_b, vals_a, vals_b)
    st.plotly_chart(fig_bar, use_container_width=True)

    # Verdict
    score_a = sum(vals_a.values())
    score_b = sum(vals_b.values())
    if score_a > score_b + 50:
        winner, loser, diff = player_a, player_b, score_a - score_b
        badge_color = "#f5c518"
    elif score_b > score_a + 50:
        winner, loser, diff = player_b, player_a, score_b - score_a
        badge_color = "#00d4aa"
    else:
        winner, loser, diff = None, None, 0
        badge_color = "#94a3b8"

    if winner:
        st.markdown(f"""
        <div class="stat-card" style="text-align:center;margin-top:1rem;">
          <div class="card-label">🏆 Overall Verdict</div>
          <div class="card-value" style="color:{badge_color};font-size:1.4rem;">{winner}</div>
          <div class="card-sub">Edges {loser} by {diff:.0f} pct pts across all attributes</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="stat-card" style="text-align:center;margin-top:1rem;">
          <div class="card-label">🤝 Verdict</div>
          <div class="card-value" style="color:#94a3b8;font-size:1.4rem;">Evenly Matched</div>
          <div class="card-sub">Very similar overall profiles</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Side-by-side Stat Table ───────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">📋</span>
  <h2>Full Stat Comparison</h2>
</div>
""", unsafe_allow_html=True)

# Build comparison table
stat_rows = [
    ("Games Played",        "games",               ".0f"),
    ("Minutes",             "minutes",             ".0f"),
    ("Goals",               "goals",               ".0f"),
    ("Assists",             "assists",             ".0f"),
    ("Goals/90",            "goals_per90",         ".3f"),
    ("Assists/90",          "assists_per90",       ".3f"),
    ("Shots",               "shots",               ".0f"),
    ("Shots on Target",     "shots_on_target",     ".0f"),
    ("Shot Accuracy %",     "shots_on_target_pct", ".1f"),
    ("Goals/Shot",          "goals_per_shot",      ".3f"),
    ("xG (model)",          "xG",                  ".2f"),
    ("xA (model)",          "xA",                  ".2f"),
    ("Goal Delta (vs xG)",  "delta_g",             "+.2f"),
    ("Assist Delta (vs xA)","delta_a",             "+.2f"),
    ("Plus/Minus per 90",   "plus_minus_per90",    "+.2f"),
    ("Yellow Cards",        "cards_yellow",        ".0f"),
    ("Fouls",               "fouls",               ".0f"),
    ("Fouled",              "fouled",              ".0f"),
]

table_data = []
for label, col, fmt in stat_rows:
    if col not in df.columns:
        continue
    val_a = row_a.get(col, 0)
    val_b = row_b.get(col, 0)
    # Highlight winner
    try:
        better = "A" if float(val_a) > float(val_b) else ("B" if float(val_b) > float(val_a) else "=")
    except Exception:
        better = "="
    # Invert for "lower is better" stats
    if col in ("fouls", "cards_yellow", "cards_red"):
        better = {"A": "B", "B": "A", "=": "="}.get(better, "=")

    val_a_str = format(float(val_a), fmt.lstrip("+")) if val_a is not None else "—"
    val_b_str = format(float(val_b), fmt.lstrip("+")) if val_b is not None else "—"
    if "+" in fmt and val_a is not None:
        val_a_str = f"{float(val_a):+{fmt.lstrip('+').lstrip('-')}}"
        val_b_str = f"{float(val_b):+{fmt.lstrip('+').lstrip('-')}}"

    table_data.append({
        "Stat": label,
        player_a: val_a_str,
        "Better": "🟡" if better == "A" else ("🩵" if better == "B" else "—"),
        player_b: val_b_str,
    })

comp_df = pd.DataFrame(table_data)
st.dataframe(comp_df, use_container_width=True, hide_index=True, height=560,
             column_config={
                 "Better": st.column_config.TextColumn("Winner", width="small"),
             })

# ── Percentile breakdown ──────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div class="section-header">
  <span class="section-icon">📈</span>
  <h2>Key Percentile Rankings</h2>
  <span class="badge">vs all outfield players</span>
</div>
""", unsafe_allow_html=True)

pct_cols = st.columns(3)
pct_stats = [
    ("Goals", "goals"),
    ("Assists", "assists"),
    ("Shots/90", "shots_per90"),
    ("Goals/90", "goals_per90"),
    ("Shot Accuracy", "shots_on_target_pct"),
    ("±/90", "plus_minus_per90"),
]
for i, (label, col) in enumerate(pct_stats):
    if col not in df.columns:
        continue
    pct_a = get_percentile(df[col], row_a.get(col, 0))
    pct_b = get_percentile(df[col], row_b.get(col, 0))
    with pct_cols[i % 3]:
        st.markdown(f"**{label}**")
        st.markdown(f"""
        <div class="pct-bar-wrap" style="margin-bottom:0.3rem;">
          <span style="font-size:0.8rem;color:#f5c518;min-width:90px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{player_a[:14]}</span>
          <div class="pct-bar-bg"><div class="pct-bar-fill" style="width:{pct_a}%;background:#f5c518;"></div></div>
          <span class="pct-label">{pct_a:.0f}th</span>
        </div>
        <div class="pct-bar-wrap" style="margin-bottom:1rem;">
          <span style="font-size:0.8rem;color:#00d4aa;min-width:90px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{player_b[:14]}</span>
          <div class="pct-bar-bg"><div class="pct-bar-fill" style="width:{pct_b}%;background:#00d4aa;"></div></div>
          <span class="pct-label">{pct_b:.0f}th</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<hr>
<p style="text-align:center; color:rgba(232,237,245,0.3); font-size:0.78rem;">
  Player Scout · FIFA 2026 Intelligence Hub
</p>
""", unsafe_allow_html=True)
