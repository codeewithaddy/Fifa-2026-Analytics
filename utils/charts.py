"""
utils/charts.py
FIFA World Cup 2026 Analytics — Reusable Plotly chart factory.
Light theme: white background, crisp grid, red/green color scheme.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Design Tokens ─────────────────────────────────────────────
BG        = "#ffffff"
BG_LIGHT  = "#f5f5f0"
NAVY      = "#1a1a2e"
RED       = "#c8102e"
GREEN     = "#006437"
AMBER     = "#f59e0b"
TEXT      = "#1a1a2e"
TEXT_MUTED= "#6b7280"
BORDER    = "#e5e7eb"
GRID      = "#f3f4f6"

CONF_COLORS = {
    "UEFA":     "#1e40af",
    "CONMEBOL": "#006437",
    "CONCACAF": "#c8102e",
    "CAF":      "#d97706",
    "AFC":      "#7c3aed",
    "OFC":      "#0891b2",
    "Other":    "#6b7280",
}


def _base_layout(**overrides) -> dict:
    base = dict(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(family="Inter, sans-serif", color=TEXT, size=12),
        margin=dict(l=16, r=16, t=52, b=16),
        legend=dict(
            bgcolor=BG,
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(size=11, color=TEXT_MUTED),
        ),
        hoverlabel=dict(
            bgcolor=NAVY,
            bordercolor=NAVY,
            font=dict(family="Inter, sans-serif", color="#fff", size=12),
        ),
        xaxis=dict(
            gridcolor=GRID,
            zerolinecolor=BORDER,
            tickfont=dict(color=TEXT_MUTED),
            linecolor=BORDER,
            showline=True,
        ),
        yaxis=dict(
            gridcolor=GRID,
            zerolinecolor=BORDER,
            tickfont=dict(color=TEXT_MUTED),
            linecolor=BORDER,
            showline=True,
        ),
    )
    base.update(overrides)
    return base


# ── 1. xG Scatter ─────────────────────────────────────────────
def xg_scatter(df: pd.DataFrame) -> go.Figure:
    df = df[df["xG"] > 0].copy()
    cmax = max(abs(df["delta_g"].max()), abs(df["delta_g"].min()), 1)

    fig = go.Figure()

    # Color: red = under-performer, green = over-performer
    colors = [
        f"rgba(200,16,46,0.7)" if d < 0 else f"rgba(0,100,55,0.7)"
        for d in df["delta_g"]
    ]

    fig.add_trace(go.Scatter(
        x=df["xG"],
        y=df["goals"],
        mode="markers",
        marker=dict(
            size=np.clip(df["shots"].fillna(5) ** 0.55, 5, 22),
            color=df["delta_g"],
            colorscale=[
                [0.0,  "rgba(200,16,46,0.8)"],
                [0.5,  "rgba(107,114,128,0.5)"],
                [1.0,  "rgba(0,100,55,0.85)"],
            ],
            cmin=-cmax, cmax=cmax,
            colorbar=dict(
                title=dict(text="Actual − xG", font=dict(color=TEXT_MUTED, size=11)),
                tickfont=dict(color=TEXT_MUTED, size=10),
                thickness=10,
                bgcolor=BG,
                bordercolor=BORDER,
                borderwidth=1,
                tickformat="+.1f",
            ),
            opacity=0.85,
            line=dict(width=0.5, color="rgba(255,255,255,0.8)"),
        ),
        customdata=np.stack([
            df["player"], df["team"], df["delta_g"].round(2),
            df["shots"].fillna(0).astype(int)
        ], axis=-1),
        hovertemplate=(
            "<b>%{customdata[0]}</b> · %{customdata[1]}<br>"
            "xG: %{x:.2f}  |  Actual: %{y}<br>"
            "Δ Goals: <b>%{customdata[2]:+.2f}</b><br>"
            "Shots: %{customdata[3]}"
            "<extra></extra>"
        ),
        name="Players",
    ))

    lim = max(df["xG"].max(), df["goals"].max()) * 1.08
    fig.add_trace(go.Scatter(
        x=[0, lim], y=[0, lim],
        mode="lines",
        line=dict(color=TEXT_MUTED, width=1.5, dash="dot"),
        name="xG = Goals (expected line)",
        hoverinfo="skip",
    ))

    fig.update_layout(
        **_base_layout(
            title=dict(
                text="Expected Goals (xG) vs Actual Goals",
                font=dict(family="Barlow Condensed, sans-serif", size=17, color=NAVY),
                x=0,
            ),
            xaxis_title="Expected Goals (xG)",
            yaxis_title="Actual Goals",
            height=480,
        )
    )
    return fig


# ── 2. Delta Bar ───────────────────────────────────────────────
def delta_bar(df: pd.DataFrame, top_n: int = 10, mode: str = "over") -> go.Figure:
    if mode == "over":
        subset = df.nlargest(top_n, "delta_g")
        color  = GREEN
        title  = f"Top {top_n} Over-Performers — Scoring Above xG"
    else:
        subset = df.nsmallest(top_n, "delta_g")
        color  = RED
        title  = f"Top {top_n} Under-Performers — Scoring Below xG"

    subset = subset.sort_values("delta_g", ascending=(mode == "under"))
    labels = [f"{r['player']}  ({r['team']})" for _, r in subset.iterrows()]

    fig = go.Figure(go.Bar(
        x=subset["delta_g"],
        y=labels,
        orientation="h",
        marker=dict(color=color, opacity=0.85),
        customdata=np.stack([subset["goals"], subset["xG"].round(2)], axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Goals: %{customdata[0]}  |  xG: %{customdata[1]:.2f}<br>"
            "Δ: <b>%{x:+.2f}</b><extra></extra>"
        ),
    ))

    fig.update_layout(
        **_base_layout(
            title=dict(
                text=title,
                font=dict(family="Barlow Condensed, sans-serif", size=16, color=NAVY),
                x=0,
            ),
            height=400,
            margin=dict(l=220, r=20, t=52, b=16),
            xaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor=BORDER),
        )
    )
    fig.update_yaxes(tickfont=dict(size=10, color=TEXT_MUTED))
    return fig


# ── 3. Radar Chart ─────────────────────────────────────────────
def radar_chart(
    player_a: str, player_b: str,
    values_a: dict, values_b: dict,
) -> go.Figure:
    categories = list(values_a.keys())
    r_a = list(values_a.values()) + [list(values_a.values())[0]]
    r_b = list(values_b.values()) + [list(values_b.values())[0]]
    cats = categories + [categories[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=r_a, theta=cats,
        fill="toself",
        name=player_a,
        line=dict(color=RED, width=2.5),
        fillcolor="rgba(200,16,46,0.08)",
        hovertemplate="%{theta}: <b>%{r:.0f}th pct</b><extra></extra>",
    ))
    fig.add_trace(go.Scatterpolar(
        r=r_b, theta=cats,
        fill="toself",
        name=player_b,
        line=dict(color=GREEN, width=2.5),
        fillcolor="rgba(0,100,55,0.07)",
        hovertemplate="%{theta}: <b>%{r:.0f}th pct</b><extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=BG,
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[25, 50, 75, 100],
                tickfont=dict(size=9, color=TEXT_MUTED),
                gridcolor=GRID,
                linecolor=BORDER,
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color=NAVY, family="Barlow Condensed"),
                gridcolor=GRID,
                linecolor=BORDER,
            ),
        ),
        paper_bgcolor=BG,
        font=dict(family="Inter", color=TEXT),
        legend=dict(
            orientation="h", y=-0.1, x=0.5, xanchor="center",
            bgcolor=BG, borderwidth=1, bordercolor=BORDER,
            font=dict(size=12, color=TEXT),
        ),
        hoverlabel=dict(bgcolor=NAVY, bordercolor=NAVY, font=dict(color="#fff")),
        height=440,
        margin=dict(l=50, r=50, t=20, b=70),
    )
    return fig


# ── 4. Top Scorers Projection Bar ─────────────────────────────
def golden_boot_bar(df: pd.DataFrame) -> go.Figure:
    df = df.nlargest(10, "projected_goals").sort_values("projected_goals")
    labels = [f"{r['player']}  ({r['team']})" for _, r in df.iterrows()]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["projected_goals"] - df["goals"],
        y=labels,
        orientation="h",
        name="Projected Additional",
        marker=dict(color=TEXT_MUTED, opacity=0.4),
        hovertemplate="Projected add'l: <b>%{x:.1f}</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=df["goals"],
        y=labels,
        orientation="h",
        name="Current Goals",
        marker=dict(color=RED, opacity=0.9),
        error_x=dict(
            type="data",
            array=(df["proj_high"] - df["projected_goals"]).clip(lower=0),
            arrayminus=(df["projected_goals"] - df["proj_low"]).clip(lower=0),
            color=TEXT_MUTED,
            thickness=2,
            width=5,
        ),
        customdata=np.stack([df["projected_goals"], df["proj_low"], df["proj_high"]], axis=-1),
        hovertemplate=(
            "Current: <b>%{x}</b><br>"
            "Projected total: <b>%{customdata[0]:.1f}</b><br>"
            "Range: %{customdata[1]:.1f} – %{customdata[2]:.1f}<extra></extra>"
        ),
    ))

    fig.update_layout(
        **_base_layout(
            barmode="stack",
            title=dict(
                text="Goal Tally Projection — Full Tournament",
                font=dict(family="Barlow Condensed, sans-serif", size=17, color=NAVY),
                x=0,
            ),
            height=440,
            margin=dict(l=230, r=40, t=52, b=16),
            legend=dict(orientation="h", y=1.06, x=0, xanchor="left"),
        )
    )
    return fig


# ── 5. Team Performance Scatter ────────────────────────────────
def team_dna_scatter(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    df["shots_per_player"] = (df["total_shots"] / df["players"]).round(2)

    fig = go.Figure()
    for conf in sorted(df["confederation"].unique()):
        sub = df[df["confederation"] == conf]
        fig.add_trace(go.Scatter(
            x=sub["shots_per_player"],
            y=sub["total_goals"],
            mode="markers+text",
            name=conf,
            marker=dict(
                size=np.clip(sub["goals_per_shot"] * 600 + 8, 10, 60),
                color=CONF_COLORS.get(conf, "#6b7280"),
                opacity=0.85,
                line=dict(width=1.5, color="#fff"),
            ),
            text=sub["team"],
            textposition="top center",
            textfont=dict(size=8, color=TEXT_MUTED),
            customdata=np.stack([
                sub["team"], sub["total_goals"], sub["shots_per_player"],
                (sub["goals_per_shot"] * 100).round(1), sub["players"]
            ], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b> · %{name}<br>"
                "Goals: %{customdata[1]} | Shots/Player: %{customdata[2]:.1f}<br>"
                "Conversion: <b>%{customdata[3]:.1f}%</b><br>"
                "Squad tracked: %{customdata[4]}"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_base_layout(
            title=dict(
                text="Shot Volume vs Goals Scored (bubble = conversion rate)",
                font=dict(family="Barlow Condensed, sans-serif", size=17, color=NAVY),
                x=0,
            ),
            xaxis_title="Avg Shots per Player",
            yaxis_title="Total Goals",
            height=520,
        )
    )
    return fig


# ── 6. Percentile Bar Chart ────────────────────────────────────
def percentile_bar_chart(player_a, player_b, vals_a, vals_b) -> go.Figure:
    attrs  = list(vals_a.keys())
    a_vals = [vals_a[k] for k in attrs]
    b_vals = [vals_b[k] for k in attrs]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=attrs, x=a_vals, name=player_a, orientation="h",
        marker=dict(color=RED, opacity=0.85),
        hovertemplate="%{y}: <b>%{x:.0f}th pct</b><extra></extra>",
    ))
    fig.add_trace(go.Bar(
        y=attrs, x=b_vals, name=player_b, orientation="h",
        marker=dict(color=GREEN, opacity=0.85),
        hovertemplate="%{y}: <b>%{x:.0f}th pct</b><extra></extra>",
    ))

    fig.update_layout(
        **_base_layout(
            barmode="group",
            title=dict(
                text="Attribute Percentile Comparison",
                font=dict(family="Barlow Condensed, sans-serif", size=15, color=NAVY),
                x=0,
            ),
            height=340,
            margin=dict(l=160, r=20, t=48, b=16),
            legend=dict(orientation="h", y=1.06, x=0, xanchor="left"),
            xaxis=dict(range=[0, 100], ticksuffix="th"),
        )
    )
    return fig
