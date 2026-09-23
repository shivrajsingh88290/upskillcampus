"""
reports.py
Handles visual analytics and report calculations for the Student Expense Tracker.
Uses Matplotlib to generate embedded charts for category distribution and monthly trends.
"""
from typing import List, Optional, Tuple
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

# Set font and style preferences for clean UI display
matplotlib.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Arial", "sans-serif"]
matplotlib.rcParams["axes.edgecolor"] = "#cccccc"
matplotlib.rcParams["axes.linewidth"] = 0.8

# Color palette suitable for clean presentation
CHART_COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
    "#59a14f", "#edc948", "#b07aa1", "#ff9da7",
    "#9c755f", "#bab0ac"
]


def create_category_pie_chart(
    category_totals: List[Tuple[str, float]],
    title: str = "Category-wise Spending Breakdown",
    figure: Optional[Figure] = None
) -> Figure:
    """
    Generate a donut/pie chart for category-wise spending distribution.
    If no data exists, renders a clean informational message.
    """
    if figure is None:
        fig = Figure(figsize=(5.5, 4.2), dpi=100)
    else:
        fig = figure
        fig.clear()

    ax = fig.add_subplot(111)

    if not category_totals or sum(amt for _, amt in category_totals) <= 0:
        ax.text(
            0.5, 0.5,
            "No expense data available\nAdd expenses to view category breakdown",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=11,
            color="#666666"
        )
        ax.axis("off")
        fig.tight_layout()
        return fig

    labels = [cat for cat, _ in category_totals]
    values = [amt for _, amt in category_totals]
    total_spent = sum(values)

    colors = CHART_COLORS[:len(labels)] if len(labels) <= len(CHART_COLORS) else None

    # Donut chart
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 4 else "",
        pctdistance=0.75,
        startangle=140,
        colors=colors,
        wedgeprops=dict(width=0.45, edgecolor="white", linewidth=1.5),
        textprops=dict(color="#333333", fontsize=9)
    )

    for at in autotexts:
        at.set_color("white")
        at.set_weight("bold")
        at.set_fontsize(8.5)

    # Center text showing total
    ax.text(
        0, 0,
        f"Total\n₹{total_spent:,.0f}",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color="#2c3e50"
    )

    ax.set_title(title, fontsize=12, fontweight="bold", pad=12, color="#2c3e50")
    fig.tight_layout()
    return fig


def create_monthly_bar_chart(
    monthly_totals: List[Tuple[str, float]],
    title: str = "Monthly Spending Trend",
    figure: Optional[Figure] = None
) -> Figure:
    """
    Generate a bar chart showing spending per month (YYYY-MM).
    If no data exists, renders a clean informational message.
    """
    if figure is None:
        fig = Figure(figsize=(5.5, 4.2), dpi=100)
    else:
        fig = figure
        fig.clear()

    ax = fig.add_subplot(111)

    if not monthly_totals or sum(amt for _, amt in monthly_totals) <= 0:
        ax.text(
            0.5, 0.5,
            "No monthly data available\nAdd expenses to view monthly trends",
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=11,
            color="#666666"
        )
        ax.axis("off")
        fig.tight_layout()
        return fig

    months = [item[0] for item in monthly_totals]
    totals = [item[1] for item in monthly_totals]

    bars = ax.bar(months, totals, color="#3498db", width=0.55, edgecolor="#2980b9", linewidth=1)

    # Add numeric labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"₹{height:,.0f}",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),  # 3 points vertical offset
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="semibold",
            color="#333333"
        )

    ax.set_title(title, fontsize=12, fontweight="bold", pad=12, color="#2c3e50")
    ax.set_xlabel("Month (YYYY-MM)", fontsize=9.5, labelpad=8, color="#555555")
    ax.set_ylabel("Total Spending (₹)", fontsize=9.5, labelpad=8, color="#555555")
    
    # Grid lines for readability
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    # Give space at top for labels
    if totals:
        max_val = max(totals)
        ax.set_ylim(0, max_val * 1.18 if max_val > 0 else 100)

    # Format ticks
    ax.tick_params(axis="x", rotation=25, labelsize=8.5)
    ax.tick_params(axis="y", labelsize=8.5)

    # Despine top and right
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return fig

