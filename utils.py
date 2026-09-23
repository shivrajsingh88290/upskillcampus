"""
utils.py
Utility helper functions for validation, date handling, formatting, and CSV export.
"""
import csv
from datetime import datetime
from typing import List, Optional, Tuple

from models import Expense

# Suggested categories defined in the project specification
CATEGORIES = [
    "Food",
    "Travel",
    "Education",
    "Shopping",
    "Bills",
    "Entertainment",
    "Health",
    "Other",
]


def get_today_date() -> str:
    """Return today's date formatted as YYYY-MM-DD."""
    return datetime.today().strftime("%Y-%m-%d")


def get_current_month() -> str:
    """Return the current month formatted as YYYY-MM."""
    return datetime.today().strftime("%Y-%m")


def validate_amount(amount_input: str) -> Tuple[bool, float, str]:
    """
    Validate that the amount is non-empty, numeric, and positive.
    
    Returns:
        (is_valid, parsed_amount, error_message)
    """
    if not amount_input or not amount_input.strip():
        return False, 0.0, "Amount cannot be empty."
    
    try:
        val = float(amount_input.strip())
    except ValueError:
        return False, 0.0, "Amount must be a valid numeric value."
    
    if val <= 0:
        return False, 0.0, "Amount must be a positive number greater than 0."
    
    return True, round(val, 2), ""


def validate_date(date_input: str) -> Tuple[bool, str, str]:
    """
    Validate that the date string follows the YYYY-MM-DD format and is a valid calendar date.
    
    Returns:
        (is_valid, formatted_date, error_message)
    """
    if not date_input or not date_input.strip():
        return False, "", "Date cannot be empty."
    
    clean_date = date_input.strip()
    try:
        dt = datetime.strptime(clean_date, "%Y-%m-%d")
        return True, dt.strftime("%Y-%m-%d"), ""
    except ValueError:
        return False, "", "Invalid date format. Please use YYYY-MM-DD (e.g. 2026-09-20)."


def validate_category(category_input: str) -> Tuple[bool, str, str]:
    """
    Validate that a category is selected.
    
    Returns:
        (is_valid, category, error_message)
    """
    if not category_input or not category_input.strip():
        return False, "", "Please select a category."
    
    clean_cat = category_input.strip()
    if clean_cat not in CATEGORIES and clean_cat != "Other":
        # Allow custom categories if necessary, but notify if completely blank
        pass
    
    return True, clean_cat, ""


def validate_expense_input(
    amount_str: str,
    category_str: str,
    date_str: str,
    description_str: str = ""
) -> Tuple[bool, Optional[Expense], str]:
    """
    Validate all fields required for adding or updating an expense.
    
    Returns:
        (is_valid, Expense object or None, error_message)
    """
    # 1. Validate Amount
    ok, amount, msg = validate_amount(amount_str)
    if not ok:
        return False, None, msg
    
    # 2. Validate Category
    ok, category, msg = validate_category(category_str)
    if not ok:
        return False, None, msg
    
    # 3. Validate Date
    ok, expense_date, msg = validate_date(date_str)
    if not ok:
        return False, None, msg
    
    clean_desc = (description_str or "").strip()
    
    expense = Expense(
        amount=amount,
        category=category,
        expense_date=expense_date,
        description=clean_desc
    )
    return True, expense, ""


def format_currency(amount: float) -> str:
    """Format floating-point amount as currency string."""
    return f"₹{amount:,.2f}"


def export_expenses_to_csv(expenses: List[Expense], file_path: str) -> Tuple[bool, str]:
    """
    Export a list of Expense objects to a specified CSV file.
    
    Returns:
        (success_boolean, status_message)
    """
    if not expenses:
        return False, "No expense records available to export."
    
    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Write standard header row
            writer.writerow(["ID", "Date", "Category", "Description", "Amount"])
            
            for exp in expenses:
                writer.writerow([
                    exp.id if exp.id is not None else "",
                    exp.expense_date,
                    exp.category,
                    exp.description,
                    f"{exp.amount:.2f}"
                ])
        return True, f"Successfully exported {len(expenses)} records to:\n{file_path}"
    except Exception as e:
        return False, f"Failed to export CSV: {str(e)}"

