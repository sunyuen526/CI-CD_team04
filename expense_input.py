"""Member A - Input module: add expenses and store them in expenses.csv."""
import csv
import os
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.csv")
FIELDS = ["date", "amount", "category", "notes"]


def load_expenses(path=DATA_FILE):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_expense(expense, path=DATA_FILE):
    new_file = not os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(expense)


def delete_expense(index, path=DATA_FILE):
    """Remove the expense at row `index` (0-based, in file order) and rewrite the CSV."""
    rows = load_expenses(path)
    if not 0 <= index < len(rows):
        raise IndexError("no such expense")
    del rows[index]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def parse_date(text):
    return datetime.strptime(text.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")


def parse_amount(text):
    """Accept a positive integer or a number with at most one decimal place."""
    try:
        value = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError("amount must be a number")
    if not value.is_finite() or value <= 0:
        raise ValueError("amount must be positive")
    if value > 1_000_000:
        raise ValueError("amount is too large")
    if value != value.quantize(Decimal("0.1")):
        raise ValueError("use a whole number or at most 1 decimal place")
    return str(int(value)) if value == value.to_integral_value() else f"{value:.1f}"


def ask(prompt, parser):
    while True:
        try:
            return parser(input(prompt))
        except ValueError as e:
            print(f"  Invalid input ({e}). Try again.")


def main():
    print("Expense input - leave date empty to finish.")
    while True:
        raw = input("Date (YYYY-MM-DD, empty to quit): ").strip()
        if not raw:
            break
        try:
            date = parse_date(raw)
        except ValueError:
            print("  Invalid date. Use YYYY-MM-DD.")
            continue
        amount = ask("Amount: ", parse_amount)
        category = input("Category: ").strip() or "Other"
        notes = input("Notes (optional): ").strip()
        save_expense({"date": date, "amount": amount, "category": category, "notes": notes})
        print("  Saved.")
    print(f"Total records: {len(load_expenses())}")


if __name__ == "__main__":
    sys.exit(main())
