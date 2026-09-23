"""
main.py
Application entry point for the Student Expense Tracker.
Initializes the SQLite database and launches the Tkinter desktop GUI.
"""
import sys
import tkinter as tk
from database import create_database, seed_sample_data
from ui import ExpenseTrackerApp


def main():
    """Initialize database and start the GUI application mainloop."""
    try:
        # 1. Automatically create database and tables if they don't exist
        create_database()
        seed_sample_data()

        # 2. Initialize and start Tkinter application
        root = tk.Tk()
        app = ExpenseTrackerApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Application encountered an error during launch: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
