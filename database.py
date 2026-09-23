"""
database.py
SQLite database management layer for the Student Expense Tracker.
Handles database creation, CRUD operations, searching, filtering, and aggregation queries.
All queries use parameterized SQL to prevent SQL injection.
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Dict, Generator, List, Optional, Tuple

from models import Expense

# Default database path inside the 'data/' folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "expenses.db")


@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager that establishes a database connection and guarantees it is cleanly closed.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_database(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Automatically creates the expenses table if it does not exist.
    Schema matches project specifications:
      - id: INTEGER PRIMARY KEY AUTOINCREMENT
      - amount: REAL NOT NULL
      - category: TEXT NOT NULL
      - expense_date: TEXT NOT NULL
      - description: TEXT
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        expense_date TEXT NOT NULL,
        description TEXT
    );
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(create_table_query)
        conn.commit()


def add_expense(
    amount: float,
    category: str,
    expense_date: str,
    description: str = "",
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """
    Insert a new expense into the database.
    Returns the newly inserted record's ID.
    """
    query = """
    INSERT INTO expenses (amount, category, expense_date, description)
    VALUES (?, ?, ?, ?);
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (amount, category, expense_date, description))
        conn.commit()
        return cursor.lastrowid


def get_expenses(
    db_path: str = DEFAULT_DB_PATH,
    sort_by: str = "date_desc"
) -> List[Expense]:
    """
    Fetch all expenses from the database, sorted as specified.
    """
    order_clause = "ORDER BY expense_date DESC, id DESC"
    if sort_by == "date_asc":
        order_clause = "ORDER BY expense_date ASC, id ASC"
    elif sort_by == "amount_desc":
        order_clause = "ORDER BY amount DESC, id DESC"
    elif sort_by == "amount_asc":
        order_clause = "ORDER BY amount ASC, id ASC"

    query = f"SELECT id, amount, category, expense_date, description FROM expenses {order_clause};"
    
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return [Expense.from_row((r["id"], r["amount"], r["category"], r["expense_date"], r["description"])) for r in rows]


def get_expense_by_id(
    expense_id: int,
    db_path: str = DEFAULT_DB_PATH
) -> Optional[Expense]:
    """
    Fetch a single expense by its ID.
    """
    query = "SELECT id, amount, category, expense_date, description FROM expenses WHERE id = ?;"
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (expense_id,))
        row = cursor.fetchone()
        if row:
            return Expense.from_row((row["id"], row["amount"], row["category"], row["expense_date"], row["description"]))
        return None


def update_expense(
    expense_id: int,
    amount: float,
    category: str,
    expense_date: str,
    description: str = "",
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """
    Update an existing expense record.
    Returns True if an update occurred.
    """
    query = """
    UPDATE expenses
    SET amount = ?, category = ?, expense_date = ?, description = ?
    WHERE id = ?;
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (amount, category, expense_date, description, expense_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_expense(
    expense_id: int,
    db_path: str = DEFAULT_DB_PATH
) -> bool:
    """
    Delete an expense record by its ID.
    Returns True if a record was deleted.
    """
    query = "DELETE FROM expenses WHERE id = ?;"
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (expense_id,))
        conn.commit()
        return cursor.rowcount > 0


def filter_expenses(
    category: Optional[str] = None,
    search_keyword: Optional[str] = None,
    month: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    sort_by: str = "date_desc",
    db_path: str = DEFAULT_DB_PATH
) -> List[Expense]:
    """
    Filter and search expenses by category, keyword, month (YYYY-MM), and amount range.
    All filters are parameterized to ensure safe SQL execution.
    """
    conditions = []
    params = []

    if category and category != "All":
        conditions.append("category = ?")
        params.append(category)

    if search_keyword and search_keyword.strip():
        term = f"%{search_keyword.strip()}%"
        conditions.append("(description LIKE ? OR category LIKE ?)")
        params.extend([term, term])

    if month and month.strip() and month != "All":
        conditions.append("expense_date LIKE ?")
        params.append(f"{month.strip()}%")

    if min_amount is not None:
        conditions.append("amount >= ?")
        params.append(min_amount)

    if max_amount is not None:
        conditions.append("amount <= ?")
        params.append(max_amount)

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    order_clause = "ORDER BY expense_date DESC, id DESC"
    if sort_by == "date_asc":
        order_clause = "ORDER BY expense_date ASC, id ASC"
    elif sort_by == "amount_desc":
        order_clause = "ORDER BY amount DESC, id DESC"
    elif sort_by == "amount_asc":
        order_clause = "ORDER BY amount ASC, id ASC"

    query = f"SELECT id, amount, category, expense_date, description FROM expenses {where_clause} {order_clause};"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [Expense.from_row((r["id"], r["amount"], r["category"], r["expense_date"], r["description"])) for r in rows]


def get_category_totals(
    month: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH
) -> List[Tuple[str, float]]:
    """
    Calculate the sum of expenses grouped by category.
    Optional filter by month (YYYY-MM).
    Returns list of (category, total_amount) sorted by total descending.
    """
    conditions = []
    params = []

    if month and month.strip() and month != "All":
        conditions.append("expense_date LIKE ?")
        params.append(f"{month.strip()}%")

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
    SELECT category, SUM(amount) as total
    FROM expenses
    {where_clause}
    GROUP BY category
    ORDER BY total DESC;
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [(r["category"], round(float(r["total"]), 2)) for r in rows]


def get_monthly_totals(
    db_path: str = DEFAULT_DB_PATH
) -> List[Tuple[str, float]]:
    """
    Calculate monthly spending totals (YYYY-MM).
    Returns list of (year_month, total_amount) sorted by year_month chronologically.
    """
    query = """
    SELECT substr(expense_date, 1, 7) as ym, SUM(amount) as total
    FROM expenses
    GROUP BY ym
    ORDER BY ym ASC;
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return [(r["ym"], round(float(r["total"]), 2)) for r in rows]


def get_dashboard_summary(
    current_month_str: str,
    db_path: str = DEFAULT_DB_PATH
) -> Dict:
    """
    Retrieve aggregated dashboard statistics in one efficient call:
      - total_spending
      - current_month_spending
      - record_count
      - highest_category (name and amount)
      - recent_expenses (top 5 latest)
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Total spending & record count
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0.0) FROM expenses;")
        row_totals = cursor.fetchone()
        record_count = row_totals[0]
        total_spending = round(float(row_totals[1]), 2)

        # 2. Current month spending
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0.0) FROM expenses WHERE expense_date LIKE ?;",
            (f"{current_month_str}%",)
        )
        month_spending = round(float(cursor.fetchone()[0]), 2)

        # 3. Highest spending category overall
        cursor.execute("""
            SELECT category, SUM(amount) as cat_sum
            FROM expenses
            GROUP BY category
            ORDER BY cat_sum DESC
            LIMIT 1;
        """)
        top_cat_row = cursor.fetchone()
        highest_category = (top_cat_row[0], round(float(top_cat_row[1]), 2)) if top_cat_row else ("None", 0.0)

        # 4. Recent expenses (latest 5 records)
        cursor.execute("""
            SELECT id, amount, category, expense_date, description
            FROM expenses
            ORDER BY expense_date DESC, id DESC
            LIMIT 5;
        """)
        recent_rows = cursor.fetchall()
        recent_expenses = [
            Expense.from_row((r["id"], r["amount"], r["category"], r["expense_date"], r["description"]))
            for r in recent_rows
        ]

        return {
            "record_count": record_count,
            "total_spending": total_spending,
            "current_month_spending": month_spending,
            "highest_category": highest_category,
            "recent_expenses": recent_expenses,
        }


def seed_sample_data(db_path: str = DEFAULT_DB_PATH) -> int:
    """
    Seed initial sample records defined in the specification if database is empty.
    Returns the number of seeded records.
    """
    existing = get_expenses(db_path=db_path)
    if existing:
        return 0

    sample_records = [
        (120.0, "Food", "2026-09-20", "Lunch"),
        (80.0, "Travel", "2026-09-20", "Bus"),
        (500.0, "Education", "2026-09-18", "Books"),
        (750.0, "Shopping", "2026-09-15", "Clothes"),
        (250.0, "Entertainment", "2026-09-12", "Movie"),
    ]
    for amt, cat, dt, desc in sample_records:
        add_expense(amt, cat, dt, desc, db_path=db_path)
    return len(sample_records)

