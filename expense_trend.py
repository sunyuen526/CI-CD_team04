"""Monthly trend chart: total spending per month."""
import sys
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  必須在 matplotlib.use("Agg") 之後匯入

from expense_input import DATA_FILE, load_expenses  # noqa: E402

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Microsoft YaHei", "PingFang TC", "Heiti TC",
                                   "Noto Sans CJK TC", "Noto Sans TC", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

BLUE, INK, INK_2, GRID = "#2a78d6", "#0b0b0b", "#52514e", "#e4e3dd"


def monthly_totals(expenses):
    """Return {'2026-10': total, ...} sorted from the oldest month to the newest."""
    totals = defaultdict(float)
    for e in expenses:
        totals[e["date"][:7]] += float(e["amount"])
    return dict(sorted(totals.items()))


def _fmt(v):
    return f"{v:,.0f}" if abs(v - round(v)) < 1e-9 else f"{v:,.1f}"


def make_trend(totals, output="trend_chart.png"):
    """Bar chart with one bar per month and the amount printed above each bar."""
    months, values = list(totals), list(totals.values())
    fig, ax = plt.subplots(figsize=(9, 5), facecolor="white")
    bars = ax.bar(months, values, color=BLUE, width=0.55)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + max(values) * 0.02, _fmt(v),
                ha="center", va="bottom", fontsize=11, color=INK)
    ax.set_ylim(0, max(values) * 1.18)
    ax.yaxis.grid(True, color=GRID)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#cfcec8")
    ax.tick_params(axis="x", labelsize=11, labelcolor=INK, length=0)
    ax.tick_params(axis="y", labelsize=10, labelcolor=INK_2, length=0)
    ax.set_title("Monthly Spending", fontsize=16, fontweight="bold", color=INK, loc="left", pad=14)
    fig.savefig(output, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DATA_FILE
    expenses = load_expenses(path)
    if not expenses:
        print("No expenses found. Run expense_input.py first.")
        return 1
    print("Saved", make_trend(monthly_totals(expenses)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
