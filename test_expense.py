"""Unit tests for the input and trend modules.  Run:  python -m unittest -v"""
import os
import tempfile
import unittest

import expense_input as ei
import expense_trend as et
from expense_input import check_budget


class ParseAmountTests(unittest.TestCase):
    def test_whole_number(self):
        self.assertEqual(ei.parse_amount("120"), "120")

    def test_one_decimal(self):
        self.assertEqual(ei.parse_amount("45.5"), "45.5")

    def test_trailing_zero_is_normalised(self):
        self.assertEqual(ei.parse_amount("7.0"), "7")
        self.assertEqual(ei.parse_amount("45.50"), "45.5")

    def test_two_decimals_rejected(self):
        with self.assertRaises(ValueError):
            ei.parse_amount("12.34")

    def test_zero_and_negative_rejected(self):
        for bad in ("0", "-3"):
            with self.assertRaises(ValueError):
                ei.parse_amount(bad)

    def test_not_a_number_rejected(self):
        with self.assertRaises(ValueError):
            ei.parse_amount("abc")

    def test_too_large_rejected(self):
        with self.assertRaises(ValueError):
            ei.parse_amount("2000000")


class ParseDateTests(unittest.TestCase):
    def test_valid_date(self):
        self.assertEqual(ei.parse_date("2026-11-14"), "2026-11-14")

    def test_invalid_dates_rejected(self):
        for bad in ("2026-13-01", "14/11/2026", "hello"):
            with self.assertRaises(ValueError):
                ei.parse_date(bad)


class StorageTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".csv")
        os.close(fd)
        os.remove(self.path)  # start without a file, like a first run

    def tearDown(self):
        if os.path.exists(self.path):
            os.remove(self.path)

    def _add(self, date, amount, category, notes=""):
        ei.save_expense({"date": date, "amount": amount, "category": category, "notes": notes}, self.path)

    def test_load_without_file_is_empty(self):
        self.assertEqual(ei.load_expenses(self.path), [])

    def test_save_and_load_round_trip(self):
        self._add("2026-11-01", "120", "Food", "lunch")
        rows = ei.load_expenses(self.path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["category"], "Food")
        self.assertEqual(rows[0]["notes"], "lunch")

    def test_chinese_category_is_preserved(self):
        self._add("2026-11-01", "60", "交通")
        self.assertEqual(ei.load_expenses(self.path)[0]["category"], "交通")

    def test_delete_removes_only_that_row(self):
        self._add("2026-11-01", "10", "A")
        self._add("2026-11-02", "20", "B")
        self._add("2026-11-03", "30", "C")
        ei.delete_expense(1, self.path)
        self.assertEqual([r["category"] for r in ei.load_expenses(self.path)], ["A", "C"])

    def test_delete_invalid_index_raises(self):
        self._add("2026-11-01", "10", "A")
        for bad in (-1, 5):
            with self.assertRaises(IndexError):
                ei.delete_expense(bad, self.path)
        self.assertEqual(len(ei.load_expenses(self.path)), 1)


class MonthlyTotalsTests(unittest.TestCase):
    def test_groups_by_month_and_sorts(self):
        data = [
            {"date": "2026-11-12", "amount": "500"},
            {"date": "2026-10-10", "amount": "100.5"},
            {"date": "2026-10-20", "amount": "100"},
        ]
        self.assertEqual(et.monthly_totals(data), {"2026-10": 200.5, "2026-11": 500.0})

    def test_empty(self):
        self.assertEqual(et.monthly_totals([]), {})


class CheckBudgetTests(unittest.TestCase):
    def test_status(self):
        self.assertEqual(check_budget(500, 1000), "ok")
        self.assertEqual(check_budget(800, 1000), "warning")
        self.assertEqual(check_budget(1200, 1000), "over")

    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            check_budget(100, 0)


if __name__ == "__main__":
    unittest.main()
