"""
utils/charts.py
FIFA 2026 Intelligence Hub — Reusable Plotly chart factory.

All charts share a unified dark theme that matches the CSS design system.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots


# ── Design Tokens ─────────────────────────────────────────────
NAVY      = "#0a1628"
NAVY_MID  = "#0f2040"
NAVY_CARD = "#111e35"
GOLD      = "#f5c518"
GOLD_DIM  = "#c9a010"
TEAL      = "#00d4aa"
RED       = "#ff4b6e"
WHITE     = "#e8edf5"
WHITE_DIM = "rgba(232,237,245,0.55)"
BORDER    = "rgba(255,255,255,0.06)"
CONF_COLORS = {
    "UEFA":     "#4f8ef7",
    "CONMEBOL": "#00d4aa",
    "CONCACAF": "#f5c518",
    "CAF":      "#ff6b35",
    "AFC":      "#c084fc",
    "OFC":      "#fb7185",
    "Other":    "#94a3b8",
}

# ── Base layout ───────────────────────────────────────────────
def _base_layout(**overrides) -> dict:
    base = dict(
        paper_bgcolor=NAVY_CARD,
        plot_bgcolor=NAVY,
        font=dict(family="Inter, sans-serif", color=WHITE, size=12),
        margin=dict(l=16, r=16, t=48, b=16),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=BORDER,
            font=dict(size=11, color=WHITE_DIM),
        ),
        hoverlabel=dict(
            bgcolor=NAVY_MID,
            bordercolor=BORDER,
            font=dict(family="Inter, sans-serif", color=WHITE, size=12),
        ),
        xaxis=dict(
            gridcolor=BORDER, zerolinecolor=BORDER,
            tickfont=dict(color=WHITE_DIM),
        ),
        yaxis=dict(
            gridcolor=BORDER, zerolinecolor=BORDER,
            tickfont=dict(color=WHITE_DIM),
        ),
    )
    base.update(overrides)
    return base


# ── 1. xG Scatter — xG vs Actual Goals ───────────────────────
def xg_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Bubble chart: xG (x-axis) vs Actual Goals (y-axis).
    Bubble size = shots. Color = performance delta.
    """
    df = df.copy()
    df = df[df["xG"] > 0].copy()

    # Colour scale: red→grey→teal
    cmax = max(abs(df["delta_g"].max()), abs(df["delta_g"].min()), 1)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["xG"],
        y=df["goals"],
        mode="markers",
        marker=dict(
            size=np.clip(df["shots"].fillna(5) ** 0.6, 6, 28),
            color=df["delta_g"],
            colorscale=[
                [0.0, RED],
                [0.5, NAVY_MID],
                [1.0, TEAL],
            ],
            cmin=-cmax, cmax=cmax,
            colorbar=dict(
                title=dict(text="Goal Delta", font=dict(color=WHITE_DIM, size=11)),
                tickfont=dict(color=WHITE_DIM, size=10),
                thickness=12,
                bgcolor=NAVY_CARD,
                bordercolor=BORDER,
            ),
            opacity=0.85,
            line=dict(width=0.5, color=BORDER),
        ),
        customdata=np.stack([
            df["player"], df["team"], df["delta_g"].round(2),
            df["shots"].fillna(0).astype(int)
        ], axis=-1),
        hovertemplate=(
            "<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
            "xG: %{x:.2f} | Actual: %{y}<br>"
            "Delta: <b>%{customdata[2]:+.2f}</b><br>"
            "Shots: %{customdata[3]}"
            "<extra></extra>"
        ),
        name="Players",
    ))

    # Perfect prediction line
    lim = max(df["xG"].max(), df["goals"].max()) * 1.05
    fig.add_trace(go.Scatter(
        x=[0, lim], y=[0, lim],
        mode="lines",
        line=dict(color=WHITE_DIM, width=1, dash="dash"),
        name="xG = Goals",
        hoverinfo="skip",
    ))

    fig.update_layout(
        **_base_layout(
            title=dict(text="Expected Goals (xG) vs Actual Goals",
                       font=dict(family="Outfit, sans-serif", size=18, color=WHITE)),
            xaxis_title="Expected Goals (xG)",
            yaxis_title="Actual Goals",
            height=500,
        )
    )
    return fig


# ── 2. Delta Bar Chart — Over/Under-performers ────────────────
def delta_bar(df: pd.DataFrame, top_n: int = 10, mode: str = "over") -> go.Figure:
    """
    Horizontal bar chart of top over- or under-performers by delta_g.
    mode='over' → top positive delta | mode='under' → top negative
    """
    df = df.copy()
    if mode == "over":
        subset = df.nlargest(top_n, "delta_g")
        color = TEAL
        title_suffix = "Over-Performers (Clinical Finishers)"
    else:
        subset = df.nsmallest(top_n, "delta_g")
        color = RED
        title_suffix = "Under-Performers (Wasting Chances)"

    subset = subset.sort_values("delta_g", ascending=(mode == "under"))
    labels = [f"{r['player']} · {r['team']}" for _, r in subset.iterrows()]

    fig = go.Figure(go.Bar(
        x=subset["delta_g"],
        y=labels,
        orientation="h",
        marker=dict(
            color=subset["delta_g"],
            colorscale=[[0, RED], [0.5, NAVY_MID], [1, TEAL]],
            line=dict(width=0),
        ),
        customdata=np.stack([subset["goals"], subset["xG"].round(2)], axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Goals: %{customdata[0]} | xG: %{customdata[1]:.2f}<br>"
            "Delta: <b>%{x:+.2f}</b><extra></extra>"
        ),
    ))

    fig.update_layout(
        **_base_layout(
            title=dict(text=title_suffix,
                       font=dict(family="Outfit, sans-serif", size=16, color=WHITE)),
            height=420,
            margin=dict(l=180, r=20, t=48, b=16),
        )
    )
    fig.update_yaxes(tickfont=dict(size=11))
    return fig


# ── 3. Radar Chart — Player Comparison ───────────────────────
def radar_chart(
    player_a: str,
    player_b: str,
    values_a: dict,
    values_b: dict,
) -> go.Figure:
    """
    Polar radar chart comparing two players across 6 attributes.
    values_a / values_b: {label: percentile_0_100}
    """
    categories = list(values_a.keys())
    # Close the polygon
    r_a = list(values_a.values()) + [list(values_a.values())[0]]
    r_b = list(values_b.values()) + [list(values_b.values())[0]]
    cats = categories + [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=r_a, theta=cats,
        fill="toself",
        name=player_a,
        line=dict(color=GOLD, width=2.5),
        fillcolor=f"rgba(245,197,24,0.15)",
        hovertemplate="%{theta}: <b>%{r:.0f}th pct</b><extra></extra>",
    ))

    fig.add_trace(go.Scatterpolar(
        r=r_b, theta=cats,
        fill="toself",
        name=player_b,
        line=dict(color=TEAL, width=2.5),
        fillcolor=f"rgba(0,212,170,0.12)",
        hovertemplate="%{theta}: <b>%{r:.0f}th pct</b><extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=NAVY,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[25, 50, 75, 100],
                tickfont=dict(size=9, color=WHITE_DIM),
                gridcolor=BORDER,
                linecolor=BORDER,
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color=WHITE, family="Outfit"),
                gridcolor=BORDER,
                linecolor=BORDER,
            ),
            gridshape="circular",
        ),
        paper_bgcolor=NAVY_CARD,
        font=dict(family="Inter", color=WHITE),
        legend=dict(
            orientation="h",
            y=-0.12,
            x=0.5, xanchor="center",
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12, color=WHITE),
        ),
        hoverlabel=dict(bgcolor=NAVY_MID, bordercolor=BORDER, font=dict(color=WHITE)),
        height=460,
        margin=dict(l=60, r=60, t=20, b=60),
        title=dict(text=""),
    )
    return fig


# ── 4. Golden Boot Bar ─────────────────────────────────────────
def golden_boot_bar(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar: current goals + projected remaining goals.
    Error bars show ±1σ confidence band.
    """
    df = df.nlargest(10, "projected_goals").sort_values("projected_goals")
    labels = [f"{r['player']} ({r['team']})" for _, r in df.iterrows()]

    fig = go.Figure()

    # Projected additional goals
    fig.add_trace(go.Bar(
        x=df["projected_goals"] - df["goals"],
        y=labels,
        orientation="h",
        name="Projected",
        marker=dict(color=TEAL, opacity=0.7),
        hovertemplate="Projected add'l: <b>%{x:.1f}</b><extra></extra>",
    ))

    # Current goals
    fig.add_trace(go.Bar(
        x=df["goals"],
        y=labels,
        orientation="h",
        name="Current Goals",
        marker=dict(color=GOLD),
        error_x=dict(
            type="data",
            array=(df["proj_high"] - df["projected_goals"]).clip(lower=0),
            arrayminus=(df["projected_goals"] - df["proj_low"]).clip(lower=0),
            color=WHITE_DIM,
            thickness=2,
            width=5,
        ),
        customdata=np.stack([df["projected_goals"], df["proj_low"], df["proj_high"]], axis=-1),
        hovertemplate=(
            "Current: <b>%{x}</b><br>"
            "Projected total: <b>%{customdata[0]:.1f}</b><br>"
            "Range: %{customdata[1]:.1f} – %{customdata[2]:.1f}"
            "<extra></extra>"
        ),
    ))

    fig.update_layout(
        **_base_layout(
            barmode="stack",
            title=dict(text="Golden Boot Projection (7-Game Tournament)",
                       font=dict(family="Outfit", size=18, color=WHITE)),
            height=460,
            margin=dict(l=200, r=40, t=54, b=16),
            legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
        )
    )
    return fig


# ── 5. Team DNA Scatter ────────────────────────────────────────
def team_dna_scatter(df: pd.DataFrame) -> go.Figure:
    """
    Scatter: avg shots per player (X) vs total goals (Y).
    Bubble size = goals per shot (efficiency / clinicality).
    Color = confederation.
    """
    df = df.copy()
    df["shots_per_player"] = (df["total_shots"] / df["players"]).round(2)
    df["size_val"] = (df["goals_per_shot"] * 500 + 8).clip(8, 80)

    color_list = [CONF_COLORS.get(c, "#94a3b8") for c in df["confederation"]]

    fig = go.Figure()

    for conf in df["confederation"].unique():
        sub = df[df["confederation"] == conf]
        fig.add_trace(go.Scatter(
            x=sub["shots_per_player"],
            y=sub["total_goals"],
            mode="markers+text",
            name=conf,
            marker=dict(
                size=np.clip(sub["goals_per_shot"] * 500 + 8, 10, 70),
                color=CONF_COLORS.get(conf, "#94a3b8"),
                opacity=0.82,
                line=dict(width=1, color=BORDER),
            ),
            text=sub["team"],
            textposition="top center",
            textfont=dict(size=9, color=WHITE_DIM),
            customdata=np.stack([
                sub["team"], sub["total_goals"], sub["shots_per_player"],
                (sub["goals_per_shot"] * 100).round(1), sub["players"]
            ], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b> · %{name}<br>"
                "Goals: %{customdata[1]} | Shots/Player: %{customdata[2]:.1f}<br>"
                "Conversion Rate: <b>%{customdata[3]:.1f}%</b><br>"
                "Squad size: %{customdata[4]}"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_base_layout(
            title=dict(text="Team DNA: Shot Volume vs Goals (bubble = conversion rate)",
                       font=dict(family="Outfit", size=18, color=WHITE)),
            xaxis_title="Avg Shots per Player",
            yaxis_title="Total Goals",
            height=540,
        )
    )
    return fig


# ── 6. Percentile Bar (horizontal mini-chart) ─────────────────
def percentile_bar_chart(player_a: str, player_b: str,
                          vals_a: dict, vals_b: dict) -> go.Figure:
    """Grouped horizontal bar showing each attribute percentile side-by-side."""
    attrs = list(vals_a.keys())
    a_vals = [vals_a[k] for k in attrs]
    b_vals = [vals_b[k] for k in attrs]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=attrs, x=a_vals, name=player_a,
        orientation="h",
        marker=dict(color=GOLD, opacity=0.85),
        hovertemplate="%{y}: <b>%{x:.0f}th pct</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=attrs, x=b_vals, name=player_b,
        orientation="h",
        marker=dict(color=TEAL, opacity=0.85),
        hovertemplate="%{y}: <b>%{x:.0f}th pct</b><extra></extra>",
    ))

    fig.update_layout(
        **_base_layout(
            barmode="group",
            title=dict(text="Attribute Percentile Comparison",
                       font=dict(family="Outfit", size=15, color=WHITE)),
            height=350,
            margin=dict(l=160, r=20, t=48, b=16),
            legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
            xaxis=dict(range=[0, 100], ticksuffix="th"),
        )
    )
    return fig
