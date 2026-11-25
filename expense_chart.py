import csv
import os
import sys
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402  必須在 matplotlib.use("Agg") 之後匯入
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "Microsoft YaHei", "PingFang TC", "Heiti TC",
                                   "Noto Sans CJK TC", "Noto Sans TC", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
from matplotlib.lines import Line2D  # noqa: E402

# 統一配色（對應範例圖表：藍、橘、綠、黃、粉紅，並擴充至 8 色）
PALETTE = [
    "#2374D8",  # Blue (Shopping)
    "#EA662D",  # Orange (Food)
    "#18AC6E",  # Green (Education)
    "#E7A100",  # Yellow/Gold (Entertainment)
    "#E5729F",  # Pink (Transport)
    "#8A5CF6",  # Purple
    "#06B6D4",  # Cyan
    "#64748B",  # Slate Gray (Other)
]


def totals_by_category(expenses):
    """將支出紀錄列表依類別加總並由高到低排序（回傳有序 dict 供網頁介面與圖表使用）。"""
    raw = defaultdict(float)
    for row in expenses:
        category = str(row.get("category") or "Uncategorized").strip()
        try:
            amount = float(row.get("amount", 0))
        except (ValueError, TypeError):
            continue
        if amount > 0:
            raw[category] += amount

    sorted_items = sorted(raw.items(), key=lambda x: x[1], reverse=True)
    if len(sorted_items) > 8:
        top_seven = sorted_items[:7]
        other_sum = sum(val for _, val in sorted_items[7:])
        sorted_items = top_seven + [("Other", other_sum)]

    return dict(sorted_items)


def load_expenses(csv_path="expenses.csv"):
    """獨立執行時從 CSV 讀取支出列表。"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"找不到資料檔案：{csv_path}")
    records = []
    with open(csv_path, mode="r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            records.append(row)
    return records


def _format_num(val):
    """若為整數則去掉小數點，否則保留兩位小數並加上千分位逗號。"""
    if float(val).is_integer():
        return f"{int(round(val)):,}"
    return f"{val:,.2f}"


def _prepare_totals(data_or_path):
    """同時支援傳入 totals 字典、支出紀錄 list，或 CSV 檔案路徑。"""
    if isinstance(data_or_path, dict):
        items = sorted(data_or_path.items(), key=lambda x: x[1], reverse=True)
        if len(items) > 8:
            items = items[:7] + [("Other", sum(v for _, v in items[7:]))]
        return dict(items)
    if isinstance(data_or_path, list):
        return totals_by_category(data_or_path)
    return totals_by_category(load_expenses(data_or_path))


def _save_fig(fig, output_target):
    """同時支援檔案路徑字串與 io.BytesIO() 記憶體緩衝區。"""
    if isinstance(output_target, (str, os.PathLike)):
        with open(output_target, "wb") as f:
            fig.savefig(f, format="png", dpi=150)
    else:
        fig.savefig(output_target, format="png", dpi=150)


def make_pie(totals, output_path="pie_chart.png"):
    """產生甜甜圈圖（Donut Chart），供 expense_app.py 與單獨執行呼叫。"""
    data = _prepare_totals(totals)
    if not data:
        raise ValueError("沒有有效的支出資料可供繪圖。")

    categories = list(data.keys())
    amounts = list(data.values())
    total_spent = sum(amounts)
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(categories))]

    fig, ax = plt.subplots(figsize=(9, 5.8), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.pie(
        amounts,
        colors=colors,
        startangle=90,
        counterclock=False,
        wedgeprops=dict(width=0.37, edgecolor="white", linewidth=2.5),
    )

    ax.text(
        0, 0.05,
        _format_num(total_spent),
        ha="center", va="center",
        fontsize=26, fontweight="bold", color="#111111",
    )
    ax.text(
        0, -0.15,
        "TOTAL SPENT",
        ha="center", va="center",
        fontsize=10.5, color="#555555",
    )

    legend_handles = []
    for cat, amt, color in zip(categories, amounts, colors):
        pct = (amt / total_spent) * 100
        label = f"  {cat}   {_format_num(amt)}  ({pct:.1f}%)"
        handle = Line2D(
            [0], [0],
            marker="o", color="w", label=label,
            markerfacecolor=color, markersize=12,
        )
        legend_handles.append(handle)

    ax.legend(
        handles=legend_handles,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=11.5,
        labelspacing=1.25,
        handletextpad=0.6,
    )

    fig.suptitle(
        "Expenses by Category",
        x=0.04, y=0.95, ha="left",
        fontsize=17, fontweight="bold", color="#111111",
    )

    ax.set_aspect("equal")
    plt.subplots_adjust(left=0.04, right=0.58, top=0.84, bottom=0.06)
    _save_fig(fig, output_path)
    plt.close(fig)
    return output_path


def make_bar(totals, output_path="bar_chart.png"):
    """產生水平長條圖（Horizontal Bar Chart），供 expense_app.py 與單獨執行呼叫。"""
    data = _prepare_totals(totals)
    if not data:
        raise ValueError("沒有有效的支出資料可供繪圖。")

    items_rev = list(reversed(list(data.items())))
    categories = [k for k, _ in items_rev]
    amounts = [v for _, v in items_rev]
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(data) - 1, -1, -1)]

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    bars = ax.barh(categories, amounts, color=colors, height=0.55)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["left"].set_linewidth(1.0)
    ax.xaxis.set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=12, pad=8, colors="#111111")

    max_amt = max(amounts) if amounts else 1
    ax.set_xlim(0, max_amt * 1.16)
    for bar, amt in zip(bars, amounts):
        ax.text(
            bar.get_width() + max_amt * 0.018,
            bar.get_y() + bar.get_height() / 2,
            _format_num(amt),
            va="center", ha="left",
            fontsize=11.5, color="#111111",
        )

    ax.set_title(
        "Spending per Category",
        loc="left", pad=18,
        fontsize=17, fontweight="bold", color="#111111",
    )

    plt.subplots_adjust(left=0.18, right=0.94, top=0.86, bottom=0.06)
    _save_fig(fig, output_path)
    plt.close(fig)
    return output_path


generate_pie_chart = make_pie
generate_bar_chart = make_bar


if __name__ == "__main__":
    target_csv = sys.argv[1] if len(sys.argv) > 1 else "expenses.csv"
    if not os.path.exists(target_csv) and os.path.exists("sample_expenses.csv"):
        target_csv = "sample_expenses.csv"

    totals = totals_by_category(load_expenses(target_csv))
    pie_out = make_pie(totals, "pie_chart.png")
    bar_out = make_bar(totals, "bar_chart.png")
    print(f"已產生圖表：{pie_out}, {bar_out}")
