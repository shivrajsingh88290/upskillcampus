"""
ui.py
Tkinter GUI for the Student Expense Tracker application.
Includes Dashboard, Add Expense form, View & Filter Expenses table,
interactive Reports with embedded Matplotlib charts, and CSV Export.
"""
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import database
import reports
import utils
from models import Expense

# Color Theme Constants
BG_LIGHT = "#f8f9fa"
BG_WHITE = "#ffffff"
PRIMARY_COLOR = "#2c3e50"     # Dark Slate Navy
ACCENT_COLOR = "#3498db"      # Blue
ACCENT_HOVER = "#2980b9"
SUCCESS_COLOR = "#27ae60"     # Green
DANGER_COLOR = "#e74c3c"      # Coral Red
CARD_BORDER = "#e2e8f0"
TEXT_DARK = "#2d3748"
TEXT_MUTED = "#718096"


class EditExpenseDialog(tk.Toplevel):
    """
    Modal dialog to edit an existing expense record.
    """
    def __init__(self, parent, expense_id: int, on_save_callback):
        super().__init__(parent)
        self.expense_id = expense_id
        self.on_save_callback = on_save_callback

        self.title(f"Edit Expense #{self.expense_id}")
        self.geometry("420x400")
        self.resizable(False, False)
        self.configure(bg=BG_WHITE)

        # Make modal
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
        self.expense = database.get_expense_by_id(self.expense_id)
        if not self.expense:
            messagebox.showerror("Error", f"Expense #{self.expense_id} not found in database.", parent=self)
            self.destroy()

    def _build_ui(self):
        container = tk.Frame(self, bg=BG_WHITE, padx=25, pady=20)
        container.pack(fill="both", expand=True)

        header = tk.Label(
            container,
            text=f"Edit Expense (ID: {self.expense.id})",
            font=("Segoe UI", 13, "bold"),
            bg=BG_WHITE,
            fg=PRIMARY_COLOR
        )
        header.pack(anchor="w", pady=(0, 15))

        # Amount
        tk.Label(container, text="Amount (₹) *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.amount_entry = ttk.Entry(container, font=("Segoe UI", 10))
        self.amount_entry.pack(fill="x", pady=(2, 10))
        self.amount_entry.insert(0, f"{self.expense.amount:.2f}")

        # Category
        tk.Label(container, text="Category *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.category_combo = ttk.Combobox(container, values=utils.CATEGORIES, state="readonly", font=("Segoe UI", 10))
        self.category_combo.pack(fill="x", pady=(2, 10))
        if self.expense.category in utils.CATEGORIES:
            self.category_combo.set(self.expense.category)
        else:
            self.category_combo.set(utils.CATEGORIES[0])

        # Date
        tk.Label(container, text="Date (YYYY-MM-DD) *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.date_entry = ttk.Entry(container, font=("Segoe UI", 10))
        self.date_entry.pack(fill="x", pady=(2, 10))
        self.date_entry.insert(0, self.expense.expense_date)

        # Description
        tk.Label(container, text="Description (Optional)", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.desc_entry = ttk.Entry(container, font=("Segoe UI", 10))
        self.desc_entry.pack(fill="x", pady=(2, 15))
        self.desc_entry.insert(0, self.expense.description or "")

        # Action Buttons
        btn_frame = tk.Frame(container, bg=BG_WHITE)
        btn_frame.pack(fill="x", pady=(10, 0))

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Segoe UI", 10),
            bg="#edf2f7",
            fg=TEXT_DARK,
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6,
            command=self.destroy
        )
        cancel_btn.pack(side="right", padx=(10, 0))

        save_btn = tk.Button(
            btn_frame,
            text="Save Changes",
            font=("Segoe UI", 10, "bold"),
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=6,
            command=self._save_changes
        )
        save_btn.pack(side="right")

    def _save_changes(self):
        amt_str = self.amount_entry.get()
        cat_str = self.category_combo.get()
        date_str = self.date_entry.get()
        desc_str = self.desc_entry.get()

        is_valid, expense, err_msg = utils.validate_expense_input(
            amount_str=amt_str,
            category_str=cat_str,
            date_str=date_str,
            description_str=desc_str
        )

        if not is_valid:
            messagebox.showwarning("Validation Error", err_msg, parent=self)
            return

        success = database.update_expense(
            expense_id=self.expense_id,
            amount=expense.amount,
            category=expense.category,
            expense_date=expense.expense_date,
            description=expense.description
        )

        if success:
            messagebox.showinfo("Success", "Expense updated successfully!", parent=self)
            self.on_save_callback()
            self.destroy()
        else:
            messagebox.showerror("Error", "Failed to update the expense record.", parent=self)


class DashboardView(tk.Frame):
    """
    Dashboard showing key statistics cards and a table of recent expenses.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_LIGHT)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # Header banner
        header_frame = tk.Frame(self, bg=BG_WHITE, padx=25, pady=18, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        header_frame.pack(fill="x", padx=20, pady=(15, 15))

        title_lbl = tk.Label(
            header_frame,
            text="Expense Overview & Statistics",
            font=("Segoe UI", 16, "bold"),
            bg=BG_WHITE,
            fg=PRIMARY_COLOR
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            header_frame,
            text="Track your personal budget, recent transactions, and category spending at a glance.",
            font=("Segoe UI", 10),
            bg=BG_WHITE,
            fg=TEXT_MUTED
        )
        sub_lbl.pack(anchor="w", pady=(3, 0))

        # Stat Cards Container
        cards_frame = tk.Frame(self, bg=BG_LIGHT)
        cards_frame.pack(fill="x", padx=20, pady=(0, 15))
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="stat_cards")

        # 1. Total Spending Card
        self.total_spent_val = tk.StringVar(value="₹0.00")
        self._create_card(cards_frame, 0, "TOTAL SPENDING", self.total_spent_val, "#2c3e50", "All-time expenses")

        # 2. Current Month Spending Card
        self.month_spent_val = tk.StringVar(value="₹0.00")
        current_m_label = datetime.today().strftime("%B %Y")
        self._create_card(cards_frame, 1, "THIS MONTH", self.month_spent_val, "#2980b9", f"Spending in {current_m_label}")

        # 3. Total Records Card
        self.records_val = tk.StringVar(value="0")
        self._create_card(cards_frame, 2, "RECORDS COUNT", self.records_val, "#27ae60", "Total transactions logged")

        # 4. Highest Category Card
        self.top_cat_val = tk.StringVar(value="None")
        self._create_card(cards_frame, 3, "TOP CATEGORY", self.top_cat_val, "#e67e22", "Highest spending category")

        # Recent Transactions Section
        recent_frame = tk.Frame(self, bg=BG_WHITE, padx=20, pady=15, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        recent_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        sec_header = tk.Frame(recent_frame, bg=BG_WHITE)
        sec_header.pack(fill="x", pady=(0, 10))

        sec_title = tk.Label(sec_header, text="Recent Transactions", font=("Segoe UI", 12, "bold"), bg=BG_WHITE, fg=PRIMARY_COLOR)
        sec_title.pack(side="left")

        quick_add_btn = tk.Button(
            sec_header,
            text="+ Add New Expense",
            font=("Segoe UI", 10, "bold"),
            bg=ACCENT_COLOR,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=lambda: self.controller.show_view("AddExpenseView")
        )
        quick_add_btn.pack(side="right")

        # Table for recent expenses
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

        scrollbar = ttk.Scrollbar(recent_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _create_card(self, parent, col, title, var, accent_color, subtitle):
        card = tk.Frame(parent, bg=BG_WHITE, padx=16, pady=14, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        tk.Label(card, text=title, font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(card, textvariable=var, font=("Segoe UI", 15, "bold"), bg=BG_WHITE, fg=accent_color).pack(anchor="w", pady=(4, 2))
        tk.Label(card, text=subtitle, font=("Segoe UI", 8), bg=BG_WHITE, fg=TEXT_MUTED).pack(anchor="w")

    def refresh(self):
        """Update dashboard metrics and recent table."""
        current_m = utils.get_current_month()
        summary = database.get_dashboard_summary(current_month_str=current_m)

        self.total_spent_val.set(utils.format_currency(summary["total_spending"]))
        self.month_spent_val.set(utils.format_currency(summary["current_month_spending"]))
        self.records_val.set(f"{summary['record_count']} items")
        
        top_cat_name, top_cat_amt = summary["highest_category"]
        if top_cat_name != "None":
            self.top_cat_val.set(f"{top_cat_name} ({utils.format_currency(top_cat_amt)})")
        else:
            self.top_cat_val.set("None")

        # Clear and reload recent table
        for item in self.tree.get_children():
            self.tree.delete(item)

        recent_expenses = summary["recent_expenses"]
        for exp in recent_expenses:
            self.tree.insert(
                "",
                "end",
                values=(
                    exp.expense_date,
                    exp.category,
                    exp.description or "-",
                    utils.format_currency(exp.amount)
                )
            )


class AddExpenseView(tk.Frame):
    """
    Form view to log new student expenses with instant validation.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_LIGHT)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # Center container
        center_frame = tk.Frame(self, bg=BG_LIGHT)
        center_frame.pack(expand=True)

        card = tk.Frame(
            center_frame,
            bg=BG_WHITE,
            padx=35,
            pady=30,
            relief="flat",
            highlightbackground=CARD_BORDER,
            highlightthickness=1
        )
        card.pack()

        # Header
        header_lbl = tk.Label(card, text="Log New Expense", font=("Segoe UI", 16, "bold"), bg=BG_WHITE, fg=PRIMARY_COLOR)
        header_lbl.pack(anchor="w", pady=(0, 4))

        sub_lbl = tk.Label(
            card,
            text="Enter details below. All fields with * are required.",
            font=("Segoe UI", 10),
            bg=BG_WHITE,
            fg=TEXT_MUTED
        )
        sub_lbl.pack(anchor="w", pady=(0, 20))

        # Amount
        tk.Label(card, text="Amount (₹) *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.amount_entry = ttk.Entry(card, font=("Segoe UI", 11), width=35)
        self.amount_entry.pack(fill="x", pady=(4, 14))

        # Category
        tk.Label(card, text="Category *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.category_combo = ttk.Combobox(card, values=utils.CATEGORIES, state="readonly", font=("Segoe UI", 10), width=33)
        self.category_combo.pack(fill="x", pady=(4, 14))
        self.category_combo.set(utils.CATEGORIES[0])

        # Date
        tk.Label(card, text="Date (YYYY-MM-DD) *", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.date_entry = ttk.Entry(card, font=("Segoe UI", 11), width=35)
        self.date_entry.pack(fill="x", pady=(4, 14))
        self.date_entry.insert(0, utils.get_today_date())

        # Description
        tk.Label(card, text="Description (Optional)", font=("Segoe UI", 10, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(anchor="w")
        self.desc_entry = ttk.Entry(card, font=("Segoe UI", 11), width=35)
        self.desc_entry.pack(fill="x", pady=(4, 24))

        # Button group
        btn_frame = tk.Frame(card, bg=BG_WHITE)
        btn_frame.pack(fill="x")

        clear_btn = tk.Button(
            btn_frame,
            text="Reset Form",
            font=("Segoe UI", 10),
            bg="#edf2f7",
            fg=TEXT_DARK,
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
            command=self.clear_form
        )
        clear_btn.pack(side="left")

        submit_btn = tk.Button(
            btn_frame,
            text="Add Expense",
            font=("Segoe UI", 10, "bold"),
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=self.submit_expense
        )
        submit_btn.pack(side="right")

    def submit_expense(self):
        amt_str = self.amount_entry.get()
        cat_str = self.category_combo.get()
        date_str = self.date_entry.get()
        desc_str = self.desc_entry.get()

        is_valid, expense, err_msg = utils.validate_expense_input(
            amount_str=amt_str,
            category_str=cat_str,
            date_str=date_str,
            description_str=desc_str
        )

        if not is_valid:
            messagebox.showwarning("Validation Error", err_msg, parent=self)
            return

        # Insert into database
        new_id = database.add_expense(
            amount=expense.amount,
            category=expense.category,
            expense_date=expense.expense_date,
            description=expense.description
        )

        if new_id:
            messagebox.showinfo("Success", f"Expense of ₹{expense.amount:.2f} logged successfully!", parent=self)
            self.clear_form()
            self.controller.refresh_all_views()
            self.controller.show_view("ExpensesView")
        else:
            messagebox.showerror("Error", "Could not save expense to database.", parent=self)

    def clear_form(self):
        self.amount_entry.delete(0, tk.END)
        self.category_combo.set(utils.CATEGORIES[0])
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, utils.get_today_date())
        self.desc_entry.delete(0, tk.END)

    def refresh(self):
        if not self.date_entry.get().strip():
            self.date_entry.insert(0, utils.get_today_date())


class ExpensesView(tk.Frame):
    """
    Table view to display, search, filter, edit, delete, and export expenses.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_LIGHT)
        self.controller = controller
        self.current_records = []
        self._build_ui()

    def _build_ui(self):
        # 1. Filter / Search Toolbar
        filter_card = tk.Frame(self, bg=BG_WHITE, padx=16, pady=14, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        filter_card.pack(fill="x", padx=20, pady=(15, 10))

        # Row 1 of Filters: Keyword, Category, Month
        r1 = tk.Frame(filter_card, bg=BG_WHITE)
        r1.pack(fill="x", pady=(0, 8))

        # Search Keyword
        tk.Label(r1, text="Search Keyword:", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.search_entry = ttk.Entry(r1, width=16, font=("Segoe UI", 10))
        self.search_entry.pack(side="left", padx=(0, 14))

        # Category Filter
        tk.Label(r1, text="Category:", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        cat_options = ["All"] + utils.CATEGORIES
        self.category_filter = ttk.Combobox(r1, values=cat_options, state="readonly", width=12, font=("Segoe UI", 10))
        self.category_filter.set("All")
        self.category_filter.pack(side="left", padx=(0, 14))

        # Month Filter
        tk.Label(r1, text="Month (YYYY-MM):", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.month_entry = ttk.Entry(r1, width=11, font=("Segoe UI", 10))
        self.month_entry.pack(side="left", padx=(0, 14))

        # Sort order
        tk.Label(r1, text="Sort By:", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.sort_combo = ttk.Combobox(
            r1,
            values=["Date (Newest)", "Date (Oldest)", "Amount (Highest)", "Amount (Lowest)"],
            state="readonly",
            width=16,
            font=("Segoe UI", 10)
        )
        self.sort_combo.set("Date (Newest)")
        self.sort_combo.pack(side="left", padx=(0, 14))

        # Row 2 of Filters: Min/Max Amount and Action Buttons
        r2 = tk.Frame(filter_card, bg=BG_WHITE)
        r2.pack(fill="x")

        tk.Label(r2, text="Min Amount (₹):", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.min_amount_entry = ttk.Entry(r2, width=10, font=("Segoe UI", 10))
        self.min_amount_entry.pack(side="left", padx=(0, 14))

        tk.Label(r2, text="Max Amount (₹):", font=("Segoe UI", 9, "bold"), bg=BG_WHITE, fg=TEXT_DARK).pack(side="left", padx=(0, 4))
        self.max_amount_entry = ttk.Entry(r2, width=10, font=("Segoe UI", 10))
        self.max_amount_entry.pack(side="left", padx=(0, 14))

        # Buttons
        filter_btn = tk.Button(
            r2,
            text="Apply Filter",
            font=("Segoe UI", 9, "bold"),
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=4,
            command=self.apply_filter
        )
        filter_btn.pack(side="left", padx=(0, 8))

        clear_btn = tk.Button(
            r2,
            text="Clear Filter",
            font=("Segoe UI", 9),
            bg="#edf2f7",
            fg=TEXT_DARK,
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self.clear_filter
        )
        clear_btn.pack(side="left")

        # 2. Main Expenses Table
        table_card = tk.Frame(self, bg=BG_WHITE, padx=15, pady=15, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        table_card.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        cols = ("id", "date", "category", "description", "amount")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID", command=lambda: self._sort_column("id", False))
        self.tree.heading("date", text="Date", command=lambda: self._sort_column("date", False))
        self.tree.heading("category", text="Category", command=lambda: self._sort_column("category", False))
        self.tree.heading("description", text="Description")
        self.tree.heading("amount", text="Amount (₹)", command=lambda: self._sort_column("amount", False))

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("date", width=110, anchor="center")
        self.tree.column("category", width=140, anchor="center")
        self.tree.column("description", width=400, anchor="w")
        self.tree.column("amount", width=120, anchor="e")

        # Double click to edit
        self.tree.bind("<Double-1>", lambda event: self.edit_selected())

        vsb = ttk.Scrollbar(table_card, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_card, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

        # 3. Bottom Action Bar
        bottom_bar = tk.Frame(self, bg=BG_LIGHT)
        bottom_bar.pack(fill="x", padx=20, pady=(0, 15))

        self.status_label = tk.Label(
            bottom_bar,
            text="Showing 0 expenses | Total: ₹0.00",
            font=("Segoe UI", 10, "bold"),
            bg=BG_LIGHT,
            fg=TEXT_DARK
        )
        self.status_label.pack(side="left")

        export_btn = tk.Button(
            bottom_bar,
            text="Export to CSV",
            font=("Segoe UI", 10),
            bg="#27ae60",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.export_csv
        )
        export_btn.pack(side="right", padx=(8, 0))

        delete_btn = tk.Button(
            bottom_bar,
            text="Delete Selected",
            font=("Segoe UI", 10),
            bg=DANGER_COLOR,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.delete_selected
        )
        delete_btn.pack(side="right", padx=(8, 0))

        edit_btn = tk.Button(
            bottom_bar,
            text="Edit Selected",
            font=("Segoe UI", 10),
            bg=ACCENT_COLOR,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=6,
            command=self.edit_selected
        )
        edit_btn.pack(side="right")

    def _sort_column(self, col, reverse):
        """Click header to toggle sort."""
        pass  # We use the explicit sort dropdown for full consistency

    def get_selected_expense_id(self) -> Optional[int]:
        selected = self.tree.selection()
        if not selected:
            return None
        item_vals = self.tree.item(selected[0], "values")
        return int(item_vals[0])

    def edit_selected(self):
        exp_id = self.get_selected_expense_id()
        if exp_id is None:
            messagebox.showwarning("Selection Required", "Please select an expense row from the table to edit.", parent=self)
            return
        EditExpenseDialog(self, exp_id, on_save_callback=self.controller.refresh_all_views)

    def delete_selected(self):
        exp_id = self.get_selected_expense_id()
        if exp_id is None:
            messagebox.showwarning("Selection Required", "Please select an expense row from the table to delete.", parent=self)
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to permanently delete expense record #{exp_id}?",
            parent=self
        )
        if confirm:
            success = database.delete_expense(exp_id)
            if success:
                messagebox.showinfo("Deleted", f"Expense #{exp_id} was deleted successfully.", parent=self)
                self.controller.refresh_all_views()
            else:
                messagebox.showerror("Error", f"Failed to delete expense #{exp_id}.", parent=self)

    def apply_filter(self):
        sort_map = {
            "Date (Newest)": "date_desc",
            "Date (Oldest)": "date_asc",
            "Amount (Highest)": "amount_desc",
            "Amount (Lowest)": "amount_asc"
        }
        sort_key = sort_map.get(self.sort_combo.get(), "date_desc")

        keyword = self.search_entry.get().strip() or None
        cat = self.category_filter.get()
        month = self.month_entry.get().strip() or None

        # Min / Max Amount validation
        min_amt = None
        max_amt = None

        min_str = self.min_amount_entry.get().strip()
        if min_str:
            try:
                min_amt = float(min_str)
            except ValueError:
                messagebox.showwarning("Filter Warning", "Min amount must be a valid number.", parent=self)
                return

        max_str = self.max_amount_entry.get().strip()
        if max_str:
            try:
                max_amt = float(max_str)
            except ValueError:
                messagebox.showwarning("Filter Warning", "Max amount must be a valid number.", parent=self)
                return

        if month:
            # Validate format YYYY-MM
            try:
                datetime.strptime(month, "%Y-%m")
            except ValueError:
                messagebox.showwarning("Filter Warning", "Month filter must follow YYYY-MM format (e.g. 2026-09).", parent=self)
                return

        results = database.filter_expenses(
            category=cat,
            search_keyword=keyword,
            month=month,
            min_amount=min_amt,
            max_amount=max_amt,
            sort_by=sort_key
        )
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
            messagebox.showwarning("Export Notice", "No expense records are currently displayed to export.", parent=self)
            return

        # Prepare default export path inside exports/ folder
        base_dir = os.path.dirname(os.path.abspath(__file__))
        exports_dir = os.path.join(base_dir, "exports")
        os.makedirs(exports_dir, exist_ok=True)
        default_file = f"expenses_export_{datetime.today().strftime('%Y%m%d_%H%M%S')}.csv"

        target_file = filedialog.asksaveasfilename(
            initialdir=exports_dir,
            initialfile=default_file,
            title="Export Expenses as CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            parent=self
        )

        if not target_file:
            return  # User canceled

        ok, msg = utils.export_expenses_to_csv(self.current_records, target_file)
        if ok:
            messagebox.showinfo("Export Successful", msg, parent=self)
        else:
            messagebox.showerror("Export Failed", msg, parent=self)

    def _populate_table(self, records):
        self.current_records = records
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_sum = 0.0
        for exp in records:
            total_sum += exp.amount
            self.tree.insert(
                "",
                "end",
                values=(
                    exp.id,
                    exp.expense_date,
                    exp.category,
                    exp.description or "-",
                    f"{exp.amount:.2f}"
                )
            )

        count = len(records)
        self.status_label.config(text=f"Showing {count} expense{'s' if count != 1 else ''} | Total: ₹{total_sum:,.2f}")

    def refresh(self):
        sort_map = {
            "Date (Newest)": "date_desc",
            "Date (Oldest)": "date_asc",
            "Amount (Highest)": "amount_desc",
            "Amount (Lowest)": "amount_asc"
        }
        sort_key = sort_map.get(self.sort_combo.get(), "date_desc")
        records = database.get_expenses(sort_by=sort_key)
        self._populate_table(records)


class ReportsView(tk.Frame):
    """
    Analytics and visualization view featuring embedded Matplotlib charts
    for category-wise distribution and monthly trends.
    """
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_LIGHT)
        self.controller = controller
        self._build_ui()

    def _build_ui(self):
        # Header Controls Bar
        ctrl_card = tk.Frame(self, bg=BG_WHITE, padx=20, pady=12, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        ctrl_card.pack(fill="x", padx=20, pady=(15, 10))

        tk.Label(ctrl_card, text="Spending Analytics & Reports", font=("Segoe UI", 13, "bold"), bg=BG_WHITE, fg=PRIMARY_COLOR).pack(side="left")

        refresh_btn = tk.Button(
            ctrl_card,
            text="Refresh Charts",
            font=("Segoe UI", 10),
            bg=PRIMARY_COLOR,
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=4,
            command=self.refresh
        )
        refresh_btn.pack(side="right")

        # Container for Charts
        charts_container = tk.Frame(self, bg=BG_LIGHT)
        charts_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        charts_container.columnconfigure((0, 1), weight=1, uniform="charts")
        charts_container.rowconfigure(0, weight=1)

        # Left: Category Donut Chart Card
        self.pie_card = tk.Frame(charts_container, bg=BG_WHITE, padx=10, pady=10, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        self.pie_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Right: Monthly Bar Chart Card
        self.bar_card = tk.Frame(charts_container, bg=BG_WHITE, padx=10, pady=10, relief="flat", highlightbackground=CARD_BORDER, highlightthickness=1)
        self.bar_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Canvas references
        self.pie_canvas = None
        self.bar_canvas = None

    def refresh(self):
        cat_totals = database.get_category_totals()
        month_totals = database.get_monthly_totals()

        # 1. Update Pie/Donut Chart
        fig_pie = reports.create_category_pie_chart(cat_totals)
        if self.pie_canvas is not None:
            self.pie_canvas.get_tk_widget().destroy()
        
        self.pie_canvas = FigureCanvasTkAgg(fig_pie, master=self.pie_card)
        self.pie_canvas.draw()
        self.pie_canvas.get_tk_widget().pack(fill="both", expand=True)

        # 2. Update Monthly Bar Chart
        fig_bar = reports.create_monthly_bar_chart(month_totals)
        if self.bar_canvas is not None:
            self.bar_canvas.get_tk_widget().destroy()

        self.bar_canvas = FigureCanvasTkAgg(fig_bar, master=self.bar_card)
        self.bar_canvas.draw()
        self.bar_canvas.get_tk_widget().pack(fill="both", expand=True)


class ExpenseTrackerApp:
    """
    Main application window and coordinator for navigation and global refresh.
    """
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Student Expense Tracker")
        self.root.geometry("1060x720")
        self.root.minsize(920, 620)
        self.root.configure(bg=BG_LIGHT)

        # Ensure database tables exist
        database.create_database()

        self._configure_styles()
        self._build_layout()

        # Load initial view
        self.show_view("DashboardView")

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Treeview styling
        style.configure(
            "Treeview",
            background=BG_WHITE,
            foreground=TEXT_DARK,
            rowheight=26,
            fieldbackground=BG_WHITE,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#edf2f7",
            foreground=PRIMARY_COLOR,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", PRIMARY_COLOR)])

    def _build_layout(self):
        # 1. Top Navigation Bar
        nav_bar = tk.Frame(self.root, bg=PRIMARY_COLOR, padx=20, pady=10)
        nav_bar.pack(fill="x")

        # Brand / App Title
        brand_frame = tk.Frame(nav_bar, bg=PRIMARY_COLOR)
        brand_frame.pack(side="left")

        app_title = tk.Label(
            brand_frame,
            text="Student Expense Tracker",
            font=("Segoe UI", 14, "bold"),
            bg=PRIMARY_COLOR,
            fg="white"
        )
        app_title.pack(anchor="w")

        # Navigation Buttons
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
                btn_container,
                text=label,
                font=("Segoe UI", 10, "bold"),
                bg=PRIMARY_COLOR,
                fg="#cfd8dc",
                activebackground="#34495e",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                padx=16,
                pady=6,
                command=lambda v=view_name: self.show_view(v)
            )
            btn.pack(side="left", padx=4)
            self.nav_buttons[view_name] = btn

        # 2. Main View Container
        self.container = tk.Frame(self.root, bg=BG_LIGHT)
        self.container.pack(fill="both", expand=True)
        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        # 3. Instantiate Views
        self.views = {
            "DashboardView": DashboardView(self.container, self),
            "AddExpenseView": AddExpenseView(self.container, self),
            "ExpensesView": ExpensesView(self.container, self),
            "ReportsView": ReportsView(self.container, self),
        }

        for view in self.views.values():
            view.grid(row=0, column=0, sticky="nsew")

    def show_view(self, view_name: str):
        """Bring the chosen view frame to top and refresh its content."""
        view = self.views.get(view_name)
        if view:
            view.tkraise()
            view.refresh()

            # Update active nav button visual state
            for name, btn in self.nav_buttons.items():
                if name == view_name:
                    btn.configure(bg="#1a252f", fg="#ffffff")
                else:
                    btn.configure(bg=PRIMARY_COLOR, fg="#cfd8dc")

    def refresh_all_views(self):
        """Refresh data across all views."""
        for view in self.views.values():
            view.refresh()
