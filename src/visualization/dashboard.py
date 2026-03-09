"""
dashboard.py
------------
Interactive Plotly dashboard for credit risk analysis.
Reads processed CSVs and renders four analytical charts
in a single HTML file — no server required.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── 1. Load processed data ────────────────────────────────────
df_segments     = pd.read_csv("data/processed/segments.csv")
df_delinquency  = pd.read_csv("data/processed/delinquency_profile.csv")
df_concentration = pd.read_csv("data/processed/concentration.csv")
df_heatmap = pd.read_csv("data/processed/heatmap.csv")

# ── 2. Prepare heatmap data ───────────────────────────────────
# Pivot: rows = age_group, cols = income_band, values = avg default rate
heatmap_data = df_heatmap.pivot(
    index="age_group",
    columns="income_band",
    values="default_rate_pct"
)

# Consistent ordering
age_order    = ["under_30", "30_to_44", "45_to_59", "60_plus"]
income_order = ["low", "medium", "high", "very_high"]

heatmap_data = heatmap_data.reindex(index=age_order, columns=income_order)

# ── 3. Prepare delinquency bar data ───────────────────────────
bucket_order = ["0_clean", "1_event", "2_events", "3_to_5_events", "6_plus_events"]
df_delinquency["delinquency_bucket"] = pd.Categorical(
    df_delinquency["delinquency_bucket"], categories=bucket_order, ordered=True
)
df_delinquency = df_delinquency.sort_values("delinquency_bucket")

# ── 4. Build dashboard ────────────────────────────────────────
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Default Rate by Age Group & Income Band",
        "Default Rate by Delinquency History",
        "Portfolio Default Concentration by Segment",
        "Credit Utilization vs Default Rate",
    ),
    specs=[
        [{"type": "xy"},      {"type": "xy"}],
        [{"type": "domain"},  {"type": "xy"}],
    ],
    vertical_spacing=0.14,
    horizontal_spacing=0.10,
)

# ── Chart 1: Heatmap ──────────────────────────────────────────
heatmap_data = heatmap_data.reindex(index=age_order, columns=income_order)

text_values = heatmap_data.map(
    lambda v: f"{v:.1f}%" if pd.notna(v) else ""
)

fig.add_trace(
    go.Heatmap(
        z=heatmap_data.values,
        x=[c.replace("_", " ").title() for c in heatmap_data.columns],
        y=[r.replace("_", " ").title() for r in heatmap_data.index],
        colorscale="RdYlGn_r",
        text=text_values.values,
        texttemplate="%{text}",
        showscale=True,
        zmin=0,
        zmax=20,
        colorbar=dict(x=0.46, len=0.45, title="Default %"),
    ),
    row=1, col=1,
)

# ── Chart 2: Delinquency bar ──────────────────────────────────
colors = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c", "#8e44ad"]

fig.add_trace(
    go.Bar(
        x=[b.replace("_", " ") for b in df_delinquency["delinquency_bucket"]],
        y=df_delinquency["default_rate_pct"],
        marker_color=colors,
        text=df_delinquency["default_rate_pct"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
        showlegend=False,
    ),
    row=1, col=2,
)

# ── Chart 3: Treemap — concentration ─────────────────────────
df_concentration["label"] = (
    df_concentration["income_band"].str.replace("_", " ").str.title()
    + "<br>"
    + df_concentration["age_group"].str.replace("_", " ").str.title()
)

fig.add_trace(
    go.Treemap(
        labels=df_concentration["label"],
        parents=["Portfolio"] * len(df_concentration),
        values=df_concentration["total_defaults"],
        customdata=df_concentration[["default_rate_pct", "pct_of_total_defaults"]],
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Total Defaults: %{value}<br>"
            "Default Rate: %{customdata[0]:.1f}%<br>"
            "Share of Portfolio Defaults: %{customdata[1]:.1f}%"
            "<extra></extra>"
        ),
        marker=dict(colorscale="RdYlGn_r"),
    ),
    row=2, col=1,
)

# ── Chart 4: Scatter — utilization vs default rate ────────────
util_data = (
    df_segments
    .groupby("utilization_band")
    .apply(lambda g: pd.Series({
        "default_rate_pct": (g["total_defaults"].sum() / g["total_borrowers"].sum() * 100).round(2),
        "avg_utilization_pct": g["avg_utilization_pct"].mean().round(2),
        "total_borrowers": g["total_borrowers"].sum(),
    }))
    .reset_index()
)

util_order  = ["low", "medium", "high", "critical"]
util_colors = ["#2ecc71", "#f1c40f", "#e67e22", "#e74c3c"]

for band, color in zip(util_order, util_colors):
    row = util_data[util_data["utilization_band"] == band]
    if row.empty:
        continue
    fig.add_trace(
        go.Scatter(
            x=row["avg_utilization_pct"],
            y=row["default_rate_pct"],
            mode="markers+text",
            marker=dict(
                size=row["total_borrowers"] / 5000,  # fixed divisor
                sizemin=20,                           # minimum visible size
                color=color,
                opacity=0.8
            ),
            text=band.title(),
            textposition="top center",
            name=band.title(),
            showlegend=True,
        ),
        row=2, col=2,
    )
# ── 5. Layout ─────────────────────────────────────────────────
fig.update_layout(
    title=dict(
        text="<b>Credit Risk Portfolio Analysis Dashboard</b>",
        font=dict(size=22),
        x=0.5,
    ),
    height=850,
    paper_bgcolor="#f8f9fa",
    plot_bgcolor="#ffffff",
    font=dict(family="Arial", size=12),
    legend=dict(
        title="Utilization Band",
        orientation="v",
        x=1.01,
        y=0.25,
    ),
)

# Axis labels
fig.update_xaxes(title_text="Income Band",        row=1, col=1)
fig.update_yaxes(title_text="Age Group",          row=1, col=1)
fig.update_xaxes(title_text="Delinquency History", row=1, col=2)
fig.update_yaxes(title_text="Default Rate (%)",   row=1, col=2)
fig.update_xaxes(title_text="Avg Utilization (%)", row=2, col=2)
fig.update_yaxes(title_text="Default Rate (%)",   row=2, col=2)

# ── 6. Export ─────────────────────────────────────────────────
output_path = "outputs/figures/credit_risk_dashboard.html"
fig.write_html(output_path)
print(f"Dashboard saved to: {output_path}")

# Also open in browser automatically
fig.show()