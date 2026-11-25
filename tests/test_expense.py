"""Pytest 單元測試：直接測試 expense_app / expense_chart / expense_input 的真實函式。

根目錄的 test_expense.py 已涵蓋 expense_input（金額、日期、存取、刪除）與 expense_trend，
這裡補上網頁篩選邏輯、類別加總與圖表產生，讓 CI 能攔截這兩個模組被改壞的情況。
"""
import io

import pytest

import expense_app
import expense_chart
from expense_input import check_budget

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

SAMPLE = [
    {"date": "2026-10-30", "amount": "100", "category": "Food", "notes": "Lunch"},
    {"date": "2026-11-01", "amount": "120", "category": "Food", "notes": "Dinner with friends"},
    {"date": "2026-11-01", "amount": "60", "category": "Transport", "notes": "MRT top-up"},
    {"date": "2026-11-05", "amount": "899", "category": "Shopping", "notes": "Headphones"},
    {"date": "2026-11-12", "amount": "500", "category": "Education", "notes": "Textbook"},
]


# ---------- expense_app：網頁顯示與篩選邏輯 ----------

@pytest.mark.parametrize("value, expected", [
    ("1200", "1,200"),
    ("45.5", "45.5"),
    ("7.0", "7"),
    (1000000, "1,000,000"),
])
def test_fmt_amount(value, expected):
    assert expense_app.fmt_amount(value) == expected


def test_list_months_newest_first_without_duplicates():
    assert expense_app.list_months(SAMPLE) == ["2026-11", "2026-10"]


def test_list_categories_sorted_and_skips_empty():
    data = SAMPLE + [{"date": "2026-11-20", "amount": "10", "category": "", "notes": ""}]
    assert expense_app.list_categories(data) == ["Education", "Food", "Shopping", "Transport"]


def test_apply_filters_without_conditions_returns_all():
    assert expense_app.apply_filters(SAMPLE) == SAMPLE


def test_apply_filters_by_exact_date():
    result = expense_app.apply_filters(SAMPLE, date="2026-11-01")
    assert [e["category"] for e in result] == ["Food", "Transport"]


def test_apply_filters_by_month():
    result = expense_app.apply_filters(SAMPLE, month="2026-10")
    assert len(result) == 1 and result[0]["notes"] == "Lunch"


def test_apply_filters_date_takes_precedence_over_month():
    result = expense_app.apply_filters(SAMPLE, date="2026-11-05", month="2026-10")
    assert [e["category"] for e in result] == ["Shopping"]


def test_apply_filters_by_category():
    result = expense_app.apply_filters(SAMPLE, category="Food")
    assert len(result) == 2
    assert all(e["category"] == "Food" for e in result)


def test_apply_filters_keyword_is_case_insensitive_and_searches_notes():
    result = expense_app.apply_filters(SAMPLE, keyword="  FRIENDS ")
    assert len(result) == 1 and result[0]["amount"] == "120"


def test_apply_filters_combined_conditions():
    result = expense_app.apply_filters(SAMPLE, month="2026-11", category="Food", keyword="dinner")
    assert len(result) == 1 and result[0]["date"] == "2026-11-01"


def test_apply_filters_no_match_returns_empty():
    assert expense_app.apply_filters(SAMPLE, category="Travel") == []


# ---------- expense_chart：類別加總與圖表產生 ----------

def test_totals_by_category_sums_and_sorts_descending():
    totals = expense_chart.totals_by_category(SAMPLE)
    assert totals == {"Shopping": 899.0, "Education": 500.0, "Food": 220.0, "Transport": 60.0}
    assert list(totals) == ["Shopping", "Education", "Food", "Transport"]


def test_totals_by_category_skips_invalid_and_non_positive_amounts():
    data = [
        {"category": "Food", "amount": "100"},
        {"category": "Food", "amount": "abc"},
        {"category": "Food", "amount": "-5"},
        {"category": "Food", "amount": "0"},
        {"category": "", "amount": "30"},
    ]
    assert expense_chart.totals_by_category(data) == {"Food": 100.0, "Uncategorized": 30.0}


def test_totals_by_category_merges_extra_categories_into_other():
    data = [{"category": f"C{i}", "amount": str(100 - i)} for i in range(10)]
    totals = expense_chart.totals_by_category(data)
    assert len(totals) == 8
    assert list(totals)[-1] == "Other"
    assert totals["Other"] == 93 + 92 + 91
    assert sum(totals.values()) == sum(100 - i for i in range(10))


@pytest.mark.parametrize("make_chart", [expense_chart.make_pie, expense_chart.make_bar])
def test_chart_written_to_file_is_valid_png(make_chart, tmp_path):
    output = tmp_path / "chart.png"
    make_chart(expense_chart.totals_by_category(SAMPLE), str(output))
    data = output.read_bytes()
    assert data.startswith(PNG_SIGNATURE)
    assert len(data) > 1000


@pytest.mark.parametrize("make_chart", [expense_chart.make_pie, expense_chart.make_bar])
def test_chart_written_to_memory_buffer(make_chart):
    # expense_app 的 /chart.png 就是用 BytesIO 產生圖表
    buf = io.BytesIO()
    make_chart(expense_chart.totals_by_category(SAMPLE), buf)
    assert buf.getvalue().startswith(PNG_SIGNATURE)


@pytest.mark.parametrize("make_chart", [expense_chart.make_pie, expense_chart.make_bar])
def test_chart_without_data_raises(make_chart):
    with pytest.raises(ValueError):
        make_chart({}, io.BytesIO())


# ---------- expense_input.check_budget：邊界值 ----------

@pytest.mark.parametrize("total, budget, expected", [
    (0, 1000, "ok"),
    (799.9, 1000, "ok"),
    (800, 1000, "warning"),
    (1000, 1000, "warning"),
    (1000.1, 1000, "over"),
])
def test_check_budget_boundaries(total, budget, expected):
    assert check_budget(total, budget) == expected


@pytest.mark.parametrize("budget", [0, -100])
def test_check_budget_rejects_non_positive_budget(budget):
    with pytest.raises(ValueError):
        check_budget(100, budget)
