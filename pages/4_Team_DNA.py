"""
pages/4_Team_DNA.py — Team DNA & Performance Analysis
FIFA 2026 Intelligence Hub
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.data_loader import inject_css, load_team_stats, load_outfield
from utils.charts import team_dna_scatter, NAVY_CARD, GOLD, TEAL, WHITE, WHITE_DIM, BORDER, RED, NAVY, NAVY_MID, CONF_COLORS, _base_layout

st.set_page_config(
    page_title="Team DNA · FIFA 2026",
    page_icon="🧬",
    layout="wide",
)
inject_css()

# ── Header ────────────────────────────────────────────────────
st.markdown("""
<div class="page-title-row">
  <h1>🧬 Team DNA</h1>
  <span class="live-badge"><span class="live-dot"></span>Team Analysis</span>
</div>
<p style="color:rgba(232,237,245,0.65); margin-top:-0.5rem; margin-bottom:1.5rem;">
  Team-level performance profiles: shot volume, efficiency, defensive solidity,
  and which nations punch above their weight.
</p>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────
with st.spinner("Aggregating team data…"):
    team = load_team_stats()
    players = load_outfield()

# ── Sidebar filters ───────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Filters")
    confs = ["All"] + sorted(team["confederation"].unique().tolist())
    sel_conf = st.selectbox("Confederation", confs)
    min_players = st.slider("Min squad size", 1, 15, 3)
    sort_by = st.selectbox("Rank teams by",
                           ["total_goals", "goals_per_shot", "total_shots",
                            "avg_plus_minus", "total_interceptions"],
                           format_func=lambda x: {
                               "total_goals": "Total Goals",
                               "goals_per_shot": "Conversion Rate",
                               "total_shots": "Total Shots",
                               "avg_plus_minus": "Avg ±/90",
                               "total_interceptions": "Interceptions",
                           }.get(x, x))

# Apply filters
fteam = team[team["players"] >= min_players].copy()
if sel_conf != "All":
    fteam = fteam[fteam["confederation"] == sel_conf]

# ── Top KPIs ──────────────────────────────────────────────────
best_attack  = fteam.loc[fteam["total_goals"].idxmax()] if not fteam.empty else None
best_convert = fteam.loc[fteam["goals_per_shot"].idxmax()] if not fteam.empty else None
best_defend  = fteam.loc[fteam["avg_plus_minus"].idxmax()] if not fteam.empty else None
most_shots   = fteam.loc[fteam["total_shots"].idxmax()] if not fteam.empty else None

k1, k2, k3, k4 = st.columns(4)
if best_attack is not None:
    k1.metric("⚔️ Top Attack",     best_attack["team"],   f"{int(best_attack['total_goals'])} goals")
    k2.metric("🎯 Most Clinical",  best_convert["team"],  f"{best_convert['goals_per_shot']:.1%} conv.")
    k3.metric("🛡️ Best ±/90",     best_defend["team"],   f"{best_defend['avg_plus_minus']:+.2f}")
    k4.metric("🔫 Most Shots",     most_shots["team"],    f"{int(most_shots['total_shots'])} shots")

st.markdown("<hr>", unsafe_allow_html=True)

# ── Main Scatter (DNA chart) ──────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">🗺️</span>
  <h2>Team DNA Map</h2>
  <span class="badge">Shots vs Goals</span>
</div>
<p style="color:rgba(232,237,245,0.55); font-size:0.88rem;">
  X-axis: average shots per player (shot volume) · Y-axis: total goals scored ·
  Bubble size: conversion rate (goals per shot).
</p>
""", unsafe_allow_html=True)

st.plotly_chart(team_dna_scatter(fteam), use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Clinicality / Wastefulness Rankings ───────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">⚡</span>
  <h2>Clinicality Index</h2>
  <span class="badge">Goals per Shot</span>
</div>
""", unsafe_allow_html=True)

tab_clin, tab_waste, tab_conf = st.tabs(["🎯 Most Clinical", "😤 Most Wasteful", "🌍 By Confederation"])

with tab_clin:
    top_conv = fteam.nlargest(12, "goals_per_shot")[
        ["team","confederation","total_goals","total_shots","goals_per_shot","players"]
    ].reset_index(drop=True)
    top_conv.index += 1

    fig_clin = go.Figure(go.Bar(
        x=[f"{r['team']}" for _, r in top_conv.iterrows()],
        y=top_conv["goals_per_shot"],
        marker=dict(
            color=[CONF_COLORS.get(c, "#94a3b8") for c in top_conv["confederation"]],
            opacity=0.85,
            line=dict(width=0),
        ),
        customdata=np.stack([top_conv["team"], top_conv["total_goals"],
                              top_conv["total_shots"], top_conv["confederation"]], axis=-1),
        hovertemplate=(
            "<b>%{customdata[0]}</b> · %{customdata[3]}<br>"
            "Conversion: <b>%{y:.1%}</b><br>"
            "Goals: %{customdata[1]} | Shots: %{customdata[2]}"
            "<extra></extra>"
        ),
    ))
    fig_clin.update_layout(
        **_base_layout(
            title=dict(text="Conversion Rate by Team (Goals per Shot)",
                       font=dict(family="Outfit", size=16, color=WHITE)),
            yaxis=dict(tickformat=".0%"),
            height=400,
        )
    )
    st.plotly_chart(fig_clin, use_container_width=True)

with tab_waste:
    bot_conv = fteam[fteam["total_shots"] > 5].nsmallest(12, "goals_per_shot")[
        ["team","confederation","total_goals","total_shots","goals_per_shot","players"]
    ].reset_index(drop=True)
    bot_conv.index += 1

    fig_waste = go.Figure(go.Bar(
        x=[f"{r['team']}" for _, r in bot_conv.iterrows()],
        y=bot_conv["goals_per_shot"],
        marker=dict(color=RED, opacity=0.75, line=dict(width=0)),
        hovertemplate=(
            "<b>%{x}</b><br>Conversion: <b>%{y:.1%}</b><extra></extra>"
        ),
    ))
    fig_waste.update_layout(
        **_base_layout(
            title=dict(text="Most Wasteful Teams (Lowest Conversion Rate)",
                       font=dict(family="Outfit", size=16, color=WHITE)),
            yaxis=dict(tickformat=".0%"),
            height=400,
        )
    )
    st.plotly_chart(fig_waste, use_container_width=True)

with tab_conf:
    conf_agg = fteam.groupby("confederation").agg(
        teams=("team","count"),
        total_goals=("total_goals","sum"),
        total_shots=("total_shots","sum"),
        avg_conversion=("goals_per_shot","mean"),
        avg_plus_minus=("avg_plus_minus","mean"),
    ).reset_index()
    conf_agg["goals_per_shot_pct"] = conf_agg["avg_conversion"] * 100

    fig_conf = go.Figure()
    for _, row in conf_agg.iterrows():
        fig_conf.add_trace(go.Bar(
            name=row["confederation"],
            x=[row["confederation"]],
            y=[row["goals_per_shot_pct"]],
            marker=dict(color=CONF_COLORS.get(row["confederation"], "#94a3b8"), opacity=0.85),
            customdata=[[row["total_goals"], int(row["teams"]), row["avg_plus_minus"]]],
            hovertemplate=(
                f"<b>{row['confederation']}</b><br>"
                "Avg Conversion: <b>%{y:.1f}%</b><br>"
                "Total Goals: %{customdata[0][0]}<br>"
                "Teams: %{customdata[0][1]}<br>"
                "Avg ±/90: %{customdata[0][2]:+.2f}"
                "<extra></extra>"
            ),
        ))
    fig_conf.update_layout(
        **_base_layout(
            title=dict(text="Average Conversion Rate by Confederation",
                       font=dict(family="Outfit", size=16, color=WHITE)),
            showlegend=False,
            height=380,
            yaxis=dict(ticksuffix="%"),
        )
    )
    st.plotly_chart(fig_conf, use_container_width=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ── Full Team Table ───────────────────────────────────────────
st.markdown("""
<div class="section-header">
  <span class="section-icon">📋</span>
  <h2>Full Team Stats</h2>
</div>
""", unsafe_allow_html=True)

search_team = st.text_input("🔍 Search team", placeholder="e.g. Brazil, France…")

display = fteam.sort_values(sort_by, ascending=False).copy()
if search_team:
    display = display[display["team"].str.contains(search_team, case=False, na=False)]

display["goals_per_shot_pct"] = (display["goals_per_shot"] * 100).round(1)
display = display[[
    "team","confederation","players","total_goals","total_assists",
    "total_shots","goals_per_shot_pct","avg_plus_minus",
    "total_interceptions","total_tackles_won","total_yellow","total_red"
]].rename(columns={
    "team":"Team","confederation":"Conf","players":"Squad",
    "total_goals":"Goals","total_assists":"Assists","total_shots":"Shots",
    "goals_per_shot_pct":"Conv%","avg_plus_minus":"Avg±/90",
    "total_interceptions":"Intercept","total_tackles_won":"Tackles",
    "total_yellow":"🟨","total_red":"🟥",
}).reset_index(drop=True)
display.index += 1
display["Avg±/90"] = display["Avg±/90"].round(2)

st.dataframe(
    display,
    use_container_width=True,
    height=520,
    column_config={
        "Goals":   st.column_config.ProgressColumn("Goals", min_value=0,
                      max_value=int(display["Goals"].max()) + 1),
        "Conv%":   st.column_config.NumberColumn("Conv %", format="%.1f%%"),
        "Avg±/90": st.column_config.NumberColumn("Avg ±/90", format="%+.2f"),
    },
)

st.markdown("""
<hr>
<p style="text-align:center; color:rgba(232,237,245,0.3); font-size:0.78rem;">
  Team DNA · FIFA 2026 Intelligence Hub
</p>
""", unsafe_allow_html=True)
