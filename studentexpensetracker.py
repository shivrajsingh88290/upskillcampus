"""
================================================================================
 Student Expense Tracker
 Developed for Upskill Campus / 3rd Year CSE Internship Project
 
 Technologies Used:
 - Python 3
 - Tkinter (Desktop Graphical User Interface)
 - SQLite3 (Local Database Management)
 - Matplotlib (Data Visualization & Spending Analytics)
 - CSV (Transaction Data Export)
================================================================================
"""

import csv
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import io
import os
import sqlite3
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Generator, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Configure Matplotlib styling
matplotlib.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Arial", "sans-serif"]
matplotlib.rcParams["axes.edgecolor"] = "#cccccc"
matplotlib.rcParams["axes.linewidth"] = 0.8

# Color Palette Constants
BG_LIGHT = "#f8f9fa"
BG_WHITE = "#ffffff"
PRIMARY_COLOR = "#2c3e50"     # Dark Slate Navy
ACCENT_COLOR = "#3498db"      # Professional Blue
ACCENT_HOVER = "#2980b9"
SUCCESS_COLOR = "#27ae60"     # Clean Green
DANGER_COLOR = "#e74c3c"      # Coral Red
CARD_BORDER = "#e2e8f0"
TEXT_DARK = "#2d3748"
TEXT_MUTED = "#718096"

CHART_COLORS = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2",
    "#59a14f", "#edc948", "#b07aa1", "#ff9da7"
]

# Standard Categories
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

# Database Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "data", "expenses.db")


# ==============================================================================
# 1. DATA MODEL
# ==============================================================================

@dataclass
class Expense:
    """
    Data model representing a single student expense record.
    """
    amount: float
    category: str
    expense_date: str
    description: str = ""
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category,
            "expense_date": self.expense_date,
            "description": self.description,
        }

    @classmethod
    def from_row(cls, row) -> "Expense":
        return cls(
            id=row[0],
            amount=float(row[1]),
            category=str(row[2]),
            expense_date=str(row[3]),
            description=str(row[4]) if row[4] is not None else "",
        )


# ==============================================================================
# 2. UTILITY & VALIDATION FUNCTIONS
# ==============================================================================

def get_today_date() -> str:
    return datetime.today().strftime("%Y-%m-%d")


def get_current_month() -> str:
    return datetime.today().strftime("%Y-%m")


def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


def validate_amount(amount_input: str) -> Tuple[bool, float, str]:
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
    if not date_input or not date_input.strip():
        return False, "", "Date cannot be empty."
    clean_date = date_input.strip()
    try:
        dt = datetime.strptime(clean_date, "%Y-%m-%d")
        return True, dt.strftime("%Y-%m-%d"), ""
    except ValueError:
        return False, "", "Invalid date format. Please use YYYY-MM-DD (e.g. 2026-09-20)."


def validate_category(category_input: str) -> Tuple[bool, str, str]:
    if not category_input or not category_input.strip():
        return False, "", "Please select a category."
    return True, category_input.strip(), ""


def validate_expense_input(
    amount_str: str,
    category_str: str,
    date_str: str,
    description_str: str = ""
) -> Tuple[bool, Optional[Expense], str]:
    ok, amount, msg = validate_amount(amount_str)
    if not ok:
        return False, None, msg

    ok, category, msg = validate_category(category_str)
    if not ok:
        return False, None, msg

    ok, expense_date, msg = validate_date(date_str)
    if not ok:
        return False, None, msg

    expense = Expense(
        amount=amount,
        category=category,
        expense_date=expense_date,
        description=(description_str or "").strip()
    )
    return True, expense, ""


def export_expenses_to_csv(expenses: List[Expense], file_path: str) -> Tuple[bool, str]:
    if not expenses:
        return False, "No expense records available to export."
    try:
        with open(file_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
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


# ==============================================================================
# 3. DATABASE MANAGEMENT (SQLITE3)
# ==============================================================================

@contextmanager
def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> Generator[sqlite3.Connection, None, None]:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def create_database(db_path: str = DEFAULT_DB_PATH) -> None:
    query = """
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
        cursor.execute(query)
        conn.commit()


def add_expense(
    amount: float,
    category: str,
    expense_date: str,
    description: str = "",
    db_path: str = DEFAULT_DB_PATH
) -> int:
    query = """
    INSERT INTO expenses (amount, category, expense_date, description)
    VALUES (?, ?, ?, ?);
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (amount, category, expense_date, description))
        conn.commit()
        return cursor.lastrowid


def get_expenses(db_path: str = DEFAULT_DB_PATH, sort_by: str = "date_desc") -> List[Expense]:
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


def get_expense_by_id(expense_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Expense]:
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


def delete_expense(expense_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
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

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

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


def get_category_totals(month: Optional[str] = None, db_path: str = DEFAULT_DB_PATH) -> List[Tuple[str, float]]:
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


def get_monthly_totals(db_path: str = DEFAULT_DB_PATH) -> List[Tuple[str, float]]:
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


def get_dashboard_summary(current_month_str: str, db_path: str = DEFAULT_DB_PATH) -> Dict:
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0.0) FROM expenses;")
        row_totals = cursor.fetchone()
        record_count = row_totals[0]
        total_spending = round(float(row_totals[1]), 2)

        cursor.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses WHERE expense_date LIKE ?;", (f"{current_month_str}%",))
        month_spending = round(float(cursor.fetchone()[0]), 2)

        cursor.execute("""
            SELECT category, SUM(amount) as cat_sum
            FROM expenses
            GROUP BY category
            ORDER BY cat_sum DESC
            LIMIT 1;
        """)
        top_cat_row = cursor.fetchone()
        highest_category = (top_cat_row[0], round(float(top_cat_row[1]), 2)) if top_cat_row else ("None", 0.0)

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


# ==============================================================================
# 4. DATA VISUALIZATION (MATPLOTLIB)
# ==============================================================================

def create_category_pie_chart(
    category_totals: List[Tuple[str, float]],
    title: str = "Category-wise Spending Breakdown",
    figure: Optional[Figure] = None
) -> Figure:
    fig = figure if figure is not None else Figure(figsize=(5.5, 4.2), dpi=100)
    fig.clear()
    ax = fig.add_subplot(111)

    if not category_totals or sum(amt for _, amt in category_totals) <= 0:
        ax.text(0.5, 0.5, "No expense data available\nAdd expenses to view category breakdown",
                ha="center", va="center", transform=ax.transAxes, fontsize=11, color="#666666")
        ax.axis("off")
        fig.tight_layout()
        return fig

    labels = [cat for cat, _ in category_totals]
    values = [amt for _, amt in category_totals]
    total_spent = sum(values)
    colors = CHART_COLORS[:len(labels)] if len(labels) <= len(CHART_COLORS) else None

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

    ax.text(0, 0, f"Total\n₹{total_spent:,.0f}", ha="center", va="center",
            fontsize=10, fontweight="bold", color="#2c3e50")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=12, color="#2c3e50")
    fig.tight_layout()
    return fig


def create_monthly_bar_chart(
    monthly_totals: List[Tuple[str, float]],
    title: str = "Monthly Spending Trend",
    figure: Optional[Figure] = None
) -> Figure:
    fig = figure if figure is not None else Figure(figsize=(5.5, 4.2), dpi=100)
    fig.clear()
    ax = fig.add_subplot(111)

    if not monthly_totals or sum(amt for _, amt in monthly_totals) <= 0:
        ax.text(0.5, 0.5, "No monthly data available\nAdd expenses to view monthly trends",
                ha="center", va="center", transform=ax.transAxes, fontsize=11, color="#666666")
        ax.axis("off")
        fig.tight_layout()
        return fig

    months = [item[0] for item in monthly_totals]
    totals = [item[1] for item in monthly_totals]

    bars = ax.bar(months, totals, color="#3498db", width=0.55, edgecolor="#2980b9", linewidth=1)
    for bar in bars:
        h = bar.get_height()
        ax.annotate(f"₹{h:,.0f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha="center", va="bottom",
                    fontsize=8.5, fontweight="semibold", color="#333333")

    ax.set_title(title, fontsize=12, fontweight="bold", pad=12, color="#2c3e50")
    ax.set_xlabel("Month (YYYY-MM)", fontsize=9, labelpad=8, color="#555555")
    ax.set_ylabel("Total Spending (₹)", fontsize=9, labelpad=8, color="#555555")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    if totals:
        max_val = max(totals)
        ax.set_ylim(0, max_val * 1.18 if max_val > 0 else 100)

    ax.tick_params(axis="x", rotation=25, labelsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


# ==============================================================================
# 5. TKINTER GUI INTERFACE
# ==============================================================================

class EditExpenseDialog(tk.Toplevel):
    def __init__(self, parent, expense_id: int, on_save_callback):
        super().__init__(parent)
        self.expense_id = expense_id
        self.on_save_callback = on_save_callback

        self.title(f"Edit Expense #{self.expense_id}")
        self.geometry("420x400")
        self.resizable(False, False)
        self.configure(bg=BG_WHITE)
        self.transient(parent)
        self.grab_set()

        self._load_data()
        self._build_ui()
        self.center_window()

    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _load_data(self):
        self.expense = get_expense_by_id(self.expense_id)
        if not self.expense:
            messagebox.showerror("Error", f"Expense #{self.expense_id} not found in database.", parent=self)
            self.destroy()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_WHITE, padx=25, pady=20)
        container.pack(fill="both", expand=True)

        header = tk.Label(container, text=f"Edit Expense (ID: {self.expense.id})",
                          font=("Segoe UI", 13, "bold"), bg=BG_WHITE, fg=PRIMARY_COLOR)
        header.pack(anchor="w", pady=(0, 15))

        tk.Label(container, text="Amount (₹) *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.amount_entry = ttk.Entry(container, font=("Segoe UI", 10))
        self.amount_entry.pack(fill="x", pady=(2, 10))
        self.amount_entry.insert(0, f"{self.expense.amount:.2f}")

        tk.Label(container, text="Category *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.category_combo = ttk.Combobox(container, values=CATEGORIES, state="readonly", font=("Segoe UI", 10))
        self.category_combo.pack(fill="x", pady=(2, 10))
        self.category_combo.set(self.expense.category if self.expense.category in CATEGORIES else CATEGORIES[0])

        tk.Label(container, text="Date (YYYY-MM-DD) *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.date_entry = ttk.Entry(container, font=("Segoe UI", 10))
        self.date_entry.pack(fill="x", pady=(2, 10))
        self.date_entry.insert(0, self.expense.expense_date)

        tk.Label(container, text="Description (Optional)", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.desc_entry = ttk.Entry(container, font=("Segoe UI", 10))
        self.desc_entry.pack(fill="x", pady=(2, 15))
        self.desc_entry.insert(0, self.expense.description or "")

        btn_frame = tk.Frame(container, bg=BG_WHITE)
        btn_frame.pack(fill="x", pady=(10, 0))

        cancel_btn = tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 10), bg="#edf2f7",
                               fg=TEXT_DARK, relief="flat", cursor="hand2", padx=15, pady=6, command=self.destroy)
        cancel_btn.pack(side="right", padx=(10, 0))

        save_btn = tk.Button(btn_frame, text="Save Changes", font=("Segoe UI", 10, "bold"), bg=PRIMARY_COLOR,
                             fg="white", relief="flat", cursor="hand2", padx=15, pady=6, command=self._save_changes)
        save_btn.pack(side="right")

    def _save_changes(self):
        is_valid, expense, err_msg = validate_expense_input(
            self.amount_entry.get(), self.category_combo.get(), self.date_entry.get(), self.desc_entry.get()
        )
        if not is_valid:
            messagebox.showwarning("Validation Error", err_msg, parent=self)
            return

        success = update_expense(self.expense_id, expense.amount, expense.category, expense.expense_date, expense.description)
        if success:
            messagebox.showinfo("Success", "Expense updated successfully!", parent=self)
            self.on_save_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to update expense.", parent=self)


class DashboardView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_LIGHT)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        header_frame = tk.Frame(self, bg=BG_WHITE, padx=25, pady=18, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        header_frame.pack(fill="x", padx=20, pady=(15, 15))

        tk.Label(header_frame, text="Expense Overview & Statistics", font=("Segoe UI", 16, "bold"), bg=BG_WHITE, fg=PRIMARY_COLOR).pack(anchor="w")
        tk.Label(header_frame, text="Track your personal budget, recent transactions, and category spending at a glance.",
                 font=("Segoe UI", 10), bg=BG_WHITE, fg=TEXT_MUTED).pack(anchor="w", pady=(3, 0))

        cards_frame = tk.Frame(self, bg=BG_LIGHT)
        cards_frame.pack(fill="x", padx=20, pady=(0, 15))
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        self.total_spent_val = tk.StringVar(value="₹0.00")
        self._create_card(cards_frame, 0, "TOTAL SPENDING", self.total_spent_val, "#2c3e50", "All-time expenses")

        self.month_spent_val = tk.StringVar(value="₹0.00")
        cur_m_label = datetime.today().strftime("%B %Y")
        self._create_card(cards_frame, 1, "THIS MONTH", self.month_spent_val, "#2980b9", f"Spending in {cur_m_label}")

        self.records_val = tk.StringVar(value="0")
        self._create_card(cards_frame, 2, "RECORDS COUNT", self.records_val, "#27ae60", "Total transactions logged")

        self.top_cat_val = tk.StringVar(value="None")
        self._create_card(cards_frame, 3, "TOP CATEGORY", self.top_cat_val, "#e67e22", "Highest spending category")

        recent_frame = tk.Frame(self, bg=BG_WHITE, padx=20, pady=15, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        recent_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        sec_header = tk.Frame(recent_frame, bg=BG_WHITE)
        sec_header.pack(fill="x", pady=(0, 10))

        tk.Label(sec_header, text="Recent Transactions", font=("Segoe UI", 12, "bold"), bg=BG_WHITE, fg=PRIMARY_COLOR).pack(side="left")

        quick_add_btn = tk.Button(
            sec_header, text="+ Add New Expense", font=("Segoe UI", 10, "bold"), bg=ACCENT_COLOR, fg="white",
            relief="flat", cursor="hand2", padx=12, pady=4, command=lambda: self.controller.show_view("AddExpenseView")
        )
        quick_add_btn.pack(side="right")

        cols = ("date", "category", "description", "amount")
        self.tree = ttk.Treeview(recent_frame, columns=cols, show="headings", height=8, selectmode="browse")
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")
        self.tree.heading("amount", text="Amount")

        self.tree.column("date", width=120, anchor="center")
        self.tree.column("category", width=140, anchor="center")
        self.tree.column("description", width=360, anchor="w")
        self.tree.column("amount", width=120, anchor="e")

        sb = ttk.Scrollbar(recent_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _create_card(self, parent, col, title, var, accent_color, subtitle):
        card = tk.Frame(parent, bg=BG_WHITE, padx=16, pady=14, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        card.grid(row=0, column=col, padx=6, sticky="nsew")
        tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(card, textvariable=var, font=("Segoe UI", 15, "bold"), bg=BG_WHITE, fg=accent_color).pack(anchor="w", pady=(4, 2))
        tk.Label(card, text=subtitle, font=("Segoe UI", 8), bg=BG_WHITE, fg=TEXT_MUTED).pack(anchor="w")

    def refresh(self):
        summary = get_dashboard_summary(current_month_str=get_current_month())
        self.total_spent_val.set(format_currency(summary["total_spending"]))
        self.month_spent_val.set(format_currency(summary["current_month_spending"]))
        self.records_val.set(f"{summary['record_count']} items")

        top_name, top_amt = summary["highest_category"]
        self.top_cat_val.set(f"{top_name} ({format_currency(top_amt)})" if top_name != "None" else "None")

        for item in self.tree.get_children():
            self.tree.delete(item)

        for exp in summary["recent_expenses"]:
            self.tree.insert("", "end", values=(
                exp.expense_date, exp.category, exp.description or "-", format_currency(exp.amount)
            ))


class AddExpenseView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_LIGHT)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        center_frame = tk.Frame(self, bg=BG_LIGHT)
        center_frame.pack(expand=True)

        card = tk.Frame(center_frame, bg=BG_WHITE, padx=35, pady=30, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack()

        tk.Label(card, text="Log New Expense", font=("Segoe UI", 16, "bold"), bg=BG_WHITE, fg=PRIMARY_COLOR).pack(anchor="w", pady=(0, 4))
        tk.Label(card, text="Enter details below. All fields with * are required.", font=("Segoe UI", 10), bg=BG_WHITE, fg=TEXT_MUTED).pack(anchor="w", pady=(0, 20))

        tk.Label(card, text="Amount (₹) *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.amount_entry = ttk.Entry(card, font=("Segoe UI", 11), width=35)
        self.amount_entry.pack(fill="x", pady=(4, 14))

        tk.Label(card, text="Category *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.category_combo = ttk.Combobox(card, values=CATEGORIES, state="readonly", font=("Segoe UI", 10), width=33)
        self.category_combo.pack(fill="x", pady=(4, 14))
        self.category_combo.set(CATEGORIES[0])

        tk.Label(card, text="Date (YYYY-MM-DD) *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.date_entry = ttk.Entry(card, font=("Segoe UI", 11), width=35)
        self.date_entry.pack(fill="x", pady=(4, 14))
        self.date_entry.insert(0, get_today_date())

        tk.Label(card, text="Description (Optional)", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.desc_entry = ttk.Entry(card, font=("Segoe UI", 11), width=35)
        self.desc_entry.pack(fill="x", pady=(4, 24))

        btn_frame = tk.Frame(card, bg=BG_WHITE)
        btn_frame.pack(fill="x")

        clear_btn = tk.Button(btn_frame, text="Reset Form", font=("Segoe UI", 10), bg="#edf2f7",
                              fg=TEXT_DARK, relief="flat", cursor="hand2", padx=16, pady=8, command=self.clear_form)
        clear_btn.pack(side="left")

        submit_btn = tk.Button(btn_frame, text="Add Expense", font=("Segoe UI", 10, "bold"), bg=PRIMARY_COLOR,
                               fg="white", relief="flat", cursor="hand2", padx=20, pady=8, command=self.submit_expense)
        submit_btn.pack(side="right")

    def submit_expense(self):
        is_valid, expense, err_msg = validate_expense_input(
            self.amount_entry.get(), self.category_combo.get(), self.date_entry.get(), self.desc_entry.get()
        )
        if not is_valid:
            messagebox.showwarning("Validation Error", err_msg, parent=self)
            return

        new_id = add_expense(expense.amount, expense.category, expense.expense_date, expense.description)
        if new_id:
            messagebox.showinfo("Success", f"Expense of ₹{expense.amount:.2f} logged successfully!", parent=self)
            self.clear_form()
            self.controller.refresh_all_views()
            self.controller.show_view("ExpensesView")
        else:
            messagebox.showerror("Error", "Could not save expense to database.", parent=self)

    def clear_form(self):
        self.amount_entry.delete(0, tk.END)
        self.category_combo.set(CATEGORIES[0])
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, get_today_date())
        self.desc_entry.delete(0, tk.END)

    def refresh(self):
        if not self.date_entry.get().strip():
            self.date_entry.insert(0, get_today_date())


class ExpensesView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_LIGHT)
        self.controller = controller
        self.current_records = []
        self._build_ui()

    def _build_ui(self):
        filter_card = tk.Frame(self, bg=BG_WHITE, padx=16, pady=14, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        filter_card.pack(fill="x", padx=20, pady=(15, 10))

        r1 = tk.Frame(filter_card, bg=BG_WHITE)
        r1.pack(fill="x", pady=(0, 8))

        tk.Label(r1, text="Search Keyword:", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.search_entry = ttk.Entry(r1, width=16, font=("Segoe UI", 10))
        self.search_entry.pack(side="left", padx=(0, 14))

        tk.Label(r1, text="Category:", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.category_filter = ttk.Combobox(r1, values=["All"] + CATEGORIES, state="readonly", width=12, font=("Segoe UI", 10))
        self.category_filter.set("All")
        self.category_filter.pack(side="left", padx=(0, 14))

        tk.Label(r1, text="Month (YYYY-MM):", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.month_entry = ttk.Entry(r1, width=11, font=("Segoe UI", 10))
        self.month_entry.pack(side="left", padx=(0, 14))

        tk.Label(r1, text="Sort By:", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.sort_combo = ttk.Combobox(r1, values=["Date (Newest)", "Date (Oldest)", "Amount (Highest)", "Amount (Lowest)"],
                                       state="readonly", width=16, font=("Segoe UI", 10))
        self.sort_combo.set("Date (Newest)")
        self.sort_combo.pack(side="left", padx=(0, 14))

        r2 = tk.Frame(filter_card, bg=BG_WHITE)
        r2.pack(fill="x")

        tk.Label(r2, text="Min Amount (₹):", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.min_amount_entry = ttk.Entry(r2, width=10, font=("Segoe UI", 10))
        self.min_amount_entry.pack(side="left", padx=(0, 14))

        tk.Label(r2, text="Max Amount (₹):", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.max_amount_entry = ttk.Entry(r2, width=10, font=("Segoe UI", 10))
        self.max_amount_entry.pack(side="left", padx=(0, 14))

        filter_btn = tk.Button(r2, text="Apply Filter", font=("Segoe UI", 9, "bold"), bg=PRIMARY_COLOR,
                               fg="white", relief="flat", cursor="hand2", padx=14, pady=4, command=self.apply_filter)
        filter_btn.pack(side="left", padx=(0, 8))

        clear_btn = tk.Button(r2, text="Clear Filter", font=("Segoe UI", 9), bg="#edf2f7",
                              fg=TEXT_DARK, relief="flat", cursor="hand2", padx=12, pady=4, command=self.clear_filter)
        clear_btn.pack(side="left")

        table_card = tk.Frame(self, bg=BG_WHITE, padx=15, pady=15, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        cols = ("id", "date", "category", "description", "amount")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("category", text="Category")
        self.tree.heading("description", text="Description")
        self.tree.heading("amount", text="Amount (₹)")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("date", width=110, anchor="center")
        self.tree.column("category", width=140, anchor="center")
        self.tree.column("description", width=400, anchor="w")
        self.tree.column("amount", width=120, anchor="e")

        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

        bottom_bar = tk.Frame(self, bg=BG_LIGHT)
        bottom_bar.pack(fill="x", padx=20, pady=(0, 15))

        self.status_label = tk.Label(bottom_bar, text="Showing 0 expenses", font=("Segoe UI", 10, "bold"), bg=BG_LIGHT, fg=TEXT_DARK)
        self.status_label.pack(side="left")

        export_btn = tk.Button(bottom_bar, text="Export to CSV", font=("Segoe UI", 10), bg="#27ae60",
                               fg="white", relief="flat", cursor="hand2", padx=14, pady=6, command=self.export_csv)
        export_btn.pack(side="right", padx=(8, 0))

        delete_btn = tk.Button(bottom_bar, text="Delete Selected", font=("Segoe UI", 10), bg=DANGER_COLOR,
                               fg="white", relief="flat", cursor="hand2", padx=14, pady=6, command=self.delete_selected)
        delete_btn.pack(side="right", padx=(8, 0))

        edit_btn = tk.Button(bottom_bar, text="Edit Selected", font=("Segoe UI", 10), bg=ACCENT_COLOR,
                             fg="white", relief="flat", cursor="hand2", padx=14, pady=6, command=self.edit_selected)
        edit_btn.pack(side="right")

    def get_selected_expense_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            return None
        return int(self.tree.item(selected[0], "values")[0])

    def edit_selected(self):
        exp_id = self.get_selected_expense_id()
        if exp_id is None:
            messagebox.showwarning("Selection Required", "Please select an expense row to edit.", parent=self)
            return
        EditExpenseDialog(self, exp_id, on_save_callback=self.controller.refresh_all_views)

    def delete_selected(self):
        exp_id = self.get_selected_expense_id()
        if exp_id is None:
            messagebox.showwarning("Selection Required", "Please select an expense row to delete.", parent=self)
            return
        if messagebox.askyesno("Confirm Delete", f"Permanently delete expense #{exp_id}?", parent=self):
            if delete_expense(exp_id):
                messagebox.showinfo("Deleted", f"Expense #{exp_id} deleted successfully.", parent=self)
                self.controller.refresh_all_views()
            else:
                messagebox.showerror("Error", f"Failed to delete expense #{exp_id}.", parent=self)

    def apply_filter(self):
        sort_map = {"Date (Newest)": "date_desc", "Date (Oldest)": "date_asc", "Amount (Highest)": "amount_desc", "Amount (Lowest)": "amount_asc"}
        sort_key = sort_map.get(self.sort_combo.get(), "date_desc")

        keyword = self.search_entry.get().strip() or None
        cat = self.category_filter.get()
        month = self.month_entry.get().strip() or None

        min_amt, max_amt = None, None
        if self.min_amount_entry.get().strip():
            try:
                min_amt = float(self.min_amount_entry.get().strip())
            except ValueError:
                messagebox.showwarning("Warning", "Min amount must be numeric.", parent=self)
                return
        if self.max_amount_entry.get().strip():
            try:
                max_amt = float(self.max_amount_entry.get().strip())
            except ValueError:
                messagebox.showwarning("Warning", "Max amount must be numeric.", parent=self)
                return

        results = filter_expenses(category=cat, search_keyword=keyword, month=month, min_amount=min_amt, max_amount=max_amt, sort_by=sort_key)
        self._populate_table(results)

    def clear_filter(self):
        self.search_entry.delete(0, tk.END)
        self.category_filter.set("All")
        self.month_entry.delete(0, tk.END)
        self.min_amount_entry.delete(0, tk.END)
        self.max_amount_entry.delete(0, tk.END)
        self.sort_combo.set("Date (Newest)")
        self.refresh()

    def export_csv(self):
        if not self.current_records:
            messagebox.showwarning("Export", "No records to export.", parent=self)
            return
        exports_dir = os.path.join(BASE_DIR, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        default_file = f"expenses_{datetime.today().strftime('%Y%m%d_%H%M%S')}.csv"

        target_file = filedialog.asksaveasfilename(
            initialdir=exports_dir, initialfile=default_file, title="Export Expenses as CSV",
            defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")], parent=self
        )
        if target_file:
            ok, msg = export_expenses_to_csv(self.current_records, target_file)
            if ok:
                messagebox.showinfo("Export Successful", msg, parent=self)
            else:
                messagebox.showerror("Export Failed", msg, parent=self)

    def _populate_table(self, records):
        self.current_records = records
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_sum = sum(exp.amount for exp in records)
        for exp in records:
            self.tree.insert("", "end", values=(exp.id, exp.expense_date, exp.category, exp.description or "-", f"{exp.amount:.2f}"))
        self.status_label.config(text=f"Showing {len(records)} records | Total: ₹{total_sum:,.2f}")

    def refresh(self):
        sort_map = {"Date (Newest)": "date_desc", "Date (Oldest)": "date_asc", "Amount (Highest)": "amount_desc", "Amount (Lowest)": "amount_asc"}
        records = get_expenses(sort_by=sort_map.get(self.sort_combo.get(), "date_desc"))
        self._populate_table(records)


class ReportsView(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_LIGHT)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        ctrl_card = tk.Frame(self, bg=BG_WHITE, padx=20, pady=12, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        ctrl_card.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(ctrl_card, text="Spending Analytics & Reports", font=("Segoe UI", 13, "bold"), bg=BG_WHITE, fg=PRIMARY_COLOR).pack(side="left")

        refresh_btn = tk.Button(ctrl_card, text="Refresh Charts", font=("Segoe UI", 10), bg=PRIMARY_COLOR,
                                fg="white", relief="flat", cursor="hand2", padx=14, pady=4, command=self.refresh)
        refresh_btn.pack(side="right")

        charts_container = tk.Frame(self, bg=BG_LIGHT)
        charts_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        charts_container.columnconfigure((0, 1), weight=1, uniform="charts")
        charts_container.rowconfigure(0, weight=1)

        self.pie_card = tk.Frame(charts_container, bg=BG_WHITE, padx=10, pady=10, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        self.pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.bar_card = tk.Frame(charts_container, bg=BG_WHITE, padx=10, pady=10, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        self.bar_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        self.pie_canvas = None
        self.bar_canvas = None

    def refresh(self):
        fig_pie = create_category_pie_chart(get_category_totals())
        if self.pie_canvas is not None:
            self.pie_canvas.get_tk_widget().destroy()
        self.pie_canvas = FigureCanvasTkAgg(fig_pie, master=self.pie_card)
        self.pie_canvas.draw()
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True)

        fig_bar = create_monthly_bar_chart(get_monthly_totals())
        if self.bar_canvas is not None:
            self.bar_canvas.get_tk_widget().destroy()
        self.bar_canvas = FigureCanvasTkAgg(fig_bar, master=self.bar_card)
        self.bar_canvas.draw()
        self.bar_canvas.get_tk_widget().pack(fill="both", expand=True)


class ExpenseTrackerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Student Expense Tracker")
        self.root.geometry("1060x720")
        self.root.minsize(920, 620)
        self.root.configure(bg=BG_LIGHT)

        create_database()
        self._configure_styles()
        self._build_layout()
        self.show_view("DashboardView")

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Treeview", background=BG_WHITE, foreground=TEXT_DARK, rowheight=26, fieldbackground=BG_WHITE, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#edf2f7", foreground=PRIMARY_COLOR, font=("Segoe UI", 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", PRIMARY_COLOR)])

    def _build_layout(self):
        nav_bar = tk.Frame(self.root, bg=PRIMARY_COLOR, padx=20, pady=10)
        nav_bar.pack(fill="x")

        brand_frame = tk.Frame(nav_bar, bg=PRIMARY_COLOR)
        brand_frame.pack(side="left")

        app_title = tk.Label(brand_frame, text="Student Expense Tracker", font=("Segoe UI", 14, "bold"), bg=PRIMARY_COLOR, fg="white")
        app_title.pack(anchor="w")

        btn_container = tk.Frame(nav_bar, bg=PRIMARY_COLOR)
        btn_container.pack(side="right")

        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", "DashboardView"),
            ("Add Expense", "AddExpenseView"),
            ("Expenses", "ExpensesView"),
            ("Reports", "ReportsView"),
        ]

        for label, view_name in nav_items:
            btn = tk.Button(
                btn_container, text=label, font=("Segoe UI", 10, "bold"), bg=PRIMARY_COLOR,
                fg="#cfd8dc", activebackground="#34495e", activeforeground="white", relief="flat", cursor="hand2",
                padx=16, pady=6, command=lambda v=view_name: self.show_view(v)
            )
            btn.pack(side="left", padx=4)
            self.nav_buttons[view_name] = btn

        self.container = tk.Frame(self.root, bg=BG_LIGHT)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.views = {
            "DashboardView": DashboardView(self.container, self),
            "AddExpenseView": AddExpenseView(self.container, self),
            "ExpensesView": ExpensesView(self.container, self),
            "ReportsView": ReportsView(self.container, self),
        }

        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def show_view(self, view_name: str):
        view = self.views.get(view_name)
        if view:
            view.tkraise()
            view.refresh()
            for name, btn in self.nav_buttons.items():
                if name == view_name:
                    btn.configure(bg="#1a252f", fg="#ffffff")
                else:
                    btn.configure(bg=PRIMARY_COLOR, fg="#cfd8dc")

    def refresh_all_views(self):
        for view in self.views.values():
            view.refresh()


def main():
    try:
        create_database()
        seed_sample_data()
        root = tk.Tk()
        app = ExpenseTrackerApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error launching Student Expense Tracker: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

