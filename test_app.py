"""
test_app.py
Automated tests for Student Expense Tracker:
Validates models, database operations, utilities, validations,
reporting chart generators, and GUI components.
"""
import os
import shutil
import tempfile
import unittest

from models import Expense
import utils
import database
import reports


class TestStudentExpenseTracker(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing database and exports
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_expenses.db")
        database.create_database(self.test_db)

    def tearDown(self):
        # Clean up temporary test files
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_database_crud(self):
        """Test creating, reading, updating, and deleting an expense."""
        # 1. Add Expense
        exp_id = database.add_expense(
            amount=150.0,
            category="Food",
            expense_date="2026-09-20",
            description="Lunch with friends",
            db_path=self.test_db
        )
        self.assertIsNotNone(exp_id)
        self.assertGreater(exp_id, 0)

        # 2. Read Expense
        exp = database.get_expense_by_id(exp_id, db_path=self.test_db)
        self.assertIsNotNone(exp)
        self.assertEqual(exp.amount, 150.0)
        self.assertEqual(exp.category, "Food")
        self.assertEqual(exp.expense_date, "2026-09-20")
        self.assertEqual(exp.description, "Lunch with friends")

        # 3. Update Expense
        updated = database.update_expense(
            expense_id=exp_id,
            amount=200.0,
            category="Food",
            expense_date="2026-09-20",
            description="Dinner with friends",
            db_path=self.test_db
        )
        self.assertTrue(updated)
        exp_updated = database.get_expense_by_id(exp_id, db_path=self.test_db)
        self.assertEqual(exp_updated.amount, 200.0)
        self.assertEqual(exp_updated.description, "Dinner with friends")

        # 4. Delete Expense
        deleted = database.delete_expense(exp_id, db_path=self.test_db)
        self.assertTrue(deleted)
        exp_deleted = database.get_expense_by_id(exp_id, db_path=self.test_db)
        self.assertIsNone(exp_deleted)

    def test_filtering_and_aggregations(self):
        """Test search, filtering, category totals, and monthly totals."""
        sample_records = [
            (120.0, "Food", "2026-09-20", "Lunch"),
            (80.0, "Travel", "2026-09-20", "Bus ticket"),
            (500.0, "Education", "2026-09-18", "Books"),
            (750.0, "Shopping", "2026-09-15", "Clothes"),
            (250.0, "Entertainment", "2026-08-12", "Movie"),
        ]
        for amt, cat, dt, desc in sample_records:
            database.add_expense(amt, cat, dt, desc, db_path=self.test_db)

        # Filter by category
        food_items = database.filter_expenses(category="Food", db_path=self.test_db)
        self.assertEqual(len(food_items), 1)
        self.assertEqual(food_items[0].category, "Food")

        # Search keyword
        search_res = database.filter_expenses(search_keyword="ticket", db_path=self.test_db)
        self.assertEqual(len(search_res), 1)
        self.assertEqual(search_res[0].description, "Bus ticket")

        # Filter by month
        aug_items = database.filter_expenses(month="2026-08", db_path=self.test_db)
        self.assertEqual(len(aug_items), 1)
        self.assertEqual(aug_items[0].category, "Entertainment")

        # Filter by amount range
        range_items = database.filter_expenses(min_amount=100.0, max_amount=600.0, db_path=self.test_db)
        self.assertEqual(len(range_items), 3)  # 120, 500, 250

        # Category totals
        cat_totals = database.get_category_totals(db_path=self.test_db)
        cat_dict = dict(cat_totals)
        self.assertEqual(cat_dict.get("Shopping"), 750.0)
        self.assertEqual(cat_dict.get("Food"), 120.0)

        # Monthly totals
        m_totals = database.get_monthly_totals(db_path=self.test_db)
        m_dict = dict(m_totals)
        self.assertEqual(m_dict.get("2026-08"), 250.0)
        self.assertEqual(m_dict.get("2026-09"), 1450.0)

        # Dashboard summary
        summary = database.get_dashboard_summary("2026-09", db_path=self.test_db)
        self.assertEqual(summary["record_count"], 5)
        self.assertEqual(summary["total_spending"], 1700.0)
        self.assertEqual(summary["current_month_spending"], 1450.0)
        self.assertEqual(summary["highest_category"][0], "Shopping")
        self.assertEqual(len(summary["recent_expenses"]), 5)

    def test_validations(self):
        """Test input validations for amount, date, category."""
        # Amount validation
        ok, val, msg = utils.validate_amount("150.50")
        self.assertTrue(ok)
        self.assertEqual(val, 150.50)

        ok, val, msg = utils.validate_amount("-50")
        self.assertFalse(ok)
        self.assertIn("positive", msg.lower())

        ok, val, msg = utils.validate_amount("abc")
        self.assertFalse(ok)
        self.assertIn("valid numeric", msg.lower())

        ok, val, msg = utils.validate_amount("")
        self.assertFalse(ok)
        self.assertIn("cannot be empty", msg.lower())

        # Date validation
        ok, val, msg = utils.validate_date("2026-09-20")
        self.assertTrue(ok)
        self.assertEqual(val, "2026-09-20")

        ok, val, msg = utils.validate_date("20-09-2026")
        self.assertFalse(ok)

        ok, val, msg = utils.validate_date("invalid-date")
        self.assertFalse(ok)

        # Category validation
        ok, val, msg = utils.validate_category("Food")
        self.assertTrue(ok)

        ok, val, msg = utils.validate_category("")
        self.assertFalse(ok)

    def test_csv_export(self):
        """Test CSV export functionality."""
        expenses = [
            Expense(id=1, amount=120.0, category="Food", expense_date="2026-09-20", description="Lunch"),
            Expense(id=2, amount=80.0, category="Travel", expense_date="2026-09-20", description="Bus"),
        ]
        csv_path = os.path.join(self.test_dir, "test_export.csv")
        ok, msg = utils.export_expenses_to_csv(expenses, csv_path)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(csv_path))

        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("ID,Date,Category,Description,Amount", content)
            self.assertIn("Food", content)
            self.assertIn("Lunch", content)
            self.assertIn("120.00", content)

    def test_reports_generation(self):
        """Test Matplotlib charts for both empty and populated data."""
        # Empty data
        fig_pie_empty = reports.create_category_pie_chart([])
        self.assertIsNotNone(fig_pie_empty)

        fig_bar_empty = reports.create_monthly_bar_chart([])
        self.assertIsNotNone(fig_bar_empty)

        # Populated data
        sample_cats = [("Food", 300.0), ("Travel", 150.0), ("Education", 500.0)]
        fig_pie = reports.create_category_pie_chart(sample_cats)
        self.assertIsNotNone(fig_pie)

        sample_months = [("2026-08", 450.0), ("2026-09", 950.0)]
        fig_bar = reports.create_monthly_bar_chart(sample_months)
        self.assertIsNotNone(fig_bar)

    def test_ui_views(self):
        """Test Tkinter GUI views instantiation and view switching."""
        import tkinter as tk
        from ui import ExpenseTrackerApp

        root = tk.Tk()
        root.withdraw()
        try:
            app = ExpenseTrackerApp(root)
            # Switch between views
            app.show_view("AddExpenseView")
            app.show_view("ExpensesView")
            app.show_view("ReportsView")
            app.show_view("DashboardView")
            app.refresh_all_views()
            root.update_idletasks()
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()

