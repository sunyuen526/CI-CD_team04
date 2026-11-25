import os
import csv
import pytest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def validate_expense_amount(amount):
    if amount <= 0:
        raise ValueError("金額必須大於 0")
    return round(float(amount), 2)


def test_csv_write_and_read(tmp_path):
    test_csv = tmp_path / "test_expenses.csv"
    sample_data = [
        ["2026-11-25", "120.50", "飲食", "午餐便當"],
        ["2026-11-25", "45.00", "交通", "公車"]
    ]

    with open(test_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "amount", "category", "notes"])
        writer.writerows(sample_data)

    total = 0.0
    with open(test_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 2
        for row in rows:
            total += float(row["amount"])

    assert round(total, 2) == 165.50


def test_invalid_amount_blocked():
    assert validate_expense_amount(100) == 100.00
    with pytest.raises(ValueError):
        validate_expense_amount(-50)
    with pytest.raises(ValueError):
        validate_expense_amount(0)


def test_chart_generation(tmp_path):
    output_img = tmp_path / "test_pie.png"
    categories = ["飲食", "交通", "娛樂"]
    amounts = [300, 100, 200]

    fig, ax = plt.subplots()
    ax.pie(amounts, labels=categories, autopct="%1.1f%%")
    fig.savefig(output_img)
    plt.close(fig)

    assert os.path.exists(output_img)
    assert os.path.getsize(output_img) > 0
