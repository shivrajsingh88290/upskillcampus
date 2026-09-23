# Student Expense Tracker 🎓💸

A desktop application built with **Python**, **Tkinter**, **SQLite3**, and **Matplotlib** designed to help students track, manage, filter, and visualize their daily personal expenses efficiently.

---

## 📌 Project Overview

Managing personal finances is a common challenge for college students. The **Student Expense Tracker** is a modular desktop application that enables students to:
- Quickly record daily expenditures with category tagging and notes.
- Monitor financial health through an interactive dashboard with key spending metrics.
- Filter, search, sort, edit, and delete transactions.
- Visualize spending habits with intuitive category breakdown and monthly trend charts.
- Export transaction records to standard CSV files for external record-keeping or reporting.

This project was developed strictly with clean, standard Python libraries and object-oriented principles, avoiding heavy web frameworks to keep the architecture transparent, lightweight, and easy to explain in technical interviews or academic viva examinations.

---

## ✨ Features

### 1. Dashboard View
- **Total Spending:** Aggregated all-time expenditure amount.
- **This Month's Spending:** Real-time sum of expenditures in the current calendar month.
- **Total Records:** Total count of logged transactions.
- **Top Spending Category:** Instantly identifies where most of the money goes.
- **Recent Transactions:** Quick-view table of the latest 5 transactions.

### 2. Add Expense Form
- Clean input form for **Amount (₹)**, **Category**, **Date (YYYY-MM-DD)**, and **Description**.
- Categories: `Food`, `Travel`, `Education`, `Shopping`, `Bills`, `Entertainment`, `Health`, and `Other`.
- Pre-filled today's date for convenient entry.
- Client-side validation:
  - Ensures amount is numeric and strictly greater than zero.
  - Ensures the date strictly follows `YYYY-MM-DD` and is a valid calendar date.
  - Prevents blank categories.

### 3. Expense Management & Table View
- **Data Table:** Interactive table displaying `ID`, `Date`, `Category`, `Description`, and `Amount`.
- **Search & Filtering:**
  - Keyword search across descriptions and categories.
  - Filter by category dropdown.
  - Filter by month (`YYYY-MM`).
  - Filter by minimum and maximum amount ranges.
- **Sorting:** Easily sort records by newest/oldest date or highest/lowest amount.
- **Record Modification:**
  - **Edit Selected:** Opens a modal dialog pre-populated with existing record data for fast edits.
  - **Delete Selected:** Deletes records with safety confirmation dialogues.
- **CSV Export:** One-click export of currently displayed records directly into the `exports/` directory or a custom path chosen by the user.

### 4. Visual Reports & Analytics
- **Category Spending Donut Chart:** Visual breakdown displaying percentages, category labels, and total amount.
- **Monthly Spending Bar Chart:** Chronological spending trajectory showing month-by-month totals with exact values above each bar.
- Embedded directly into Tkinter using Matplotlib's native `FigureCanvasTkAgg` for a seamless desktop experience.

---

## 🛠️ Technology Stack

| Technology | Purpose |
| :--- | :--- |
| **Python 3** | Core programming language |
| **Tkinter / ttk** | Desktop graphical user interface (GUI) |
| **SQLite3** | Local relational database storage |
| **Matplotlib** | Data visualization (donut & bar charts) |
| **CSV** | Transaction export functionality |

---

## 📂 Project Structure

```text
shivraj/
│
├── main.py               # Application entry point and startup logic
├── database.py           # SQLite connection, CRUD queries, filtering, and aggregations
├── models.py             # Expense dataclass and data serialization
├── ui.py                 # Tkinter GUI views (Dashboard, Add, View/Filter, Reports, Dialogs)
├── reports.py            # Matplotlib chart generation (Category Donut & Monthly Bar)
├── utils.py              # Validations, date utilities, currency formatting, CSV export
├── requirements.txt      # Minimal external dependencies (matplotlib)
├── README.md             # Project documentation and setup guide
├── .gitignore            # Git exclusion rules for databases, cache, and exports
│
├── data/                 # SQLite database storage directory
│   └── expenses.db       # Generated SQLite database file
│
└── exports/              # Directory for exported CSV files
    └── .gitkeep
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+ installed on your system.
- `pip` (Python package manager).

### Steps

1. **Clone or Navigate to the Project Directory:**
   ```bash
   git clone <repository-url>
   cd shivraj
   ```

2. **(Optional) Create and Activate a Virtual Environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application:**

   **Option A — Desktop Application (Tkinter GUI):**
   ```bash
   python main.py
   ```

   **Option B — Web Browser Application (Localhost):**
   ```bash
   python web_app.py
   ```
   Then open your web browser at: **`http://127.0.0.1:5000`** (or **`http://localhost:5000`**)

---

## 📸 Application Screenshots (Placeholders)

*Note: You can add screenshots of your running application here for viva or GitHub presentation.*

| Dashboard View | Add Expense Form |
| :---: | :---: |
| *[ Dashboard Screenshot Placeholder ]* | *[ Add Expense Screenshot Placeholder ]* |

| Expenses Table & Filters | Analytics & Reports |
| :---: | :---: |
| *[ Expenses Table Screenshot ]* | *[ Reports & Charts Screenshot ]* |

---

## 🧪 Testing Checklist

- [x] Application launches cleanly and creates database automatically if not present.
- [x] Validates all form inputs (positive amounts, valid `YYYY-MM-DD` dates, selected categories).
- [x] Adds expense to database and updates dashboard counters immediately.
- [x] Lists, filters, and searches expenses accurately.
- [x] Edits existing records in-place via modal dialog.
- [x] Deletes records safely with user confirmation.
- [x] Donut chart and bar chart render without errors even with empty or single records.
- [x] Exports records cleanly into standard formatted CSV files.

---

## 🔮 Future Improvements

- User authentication & multi-user profiles.
- Budget limits with alert warnings when approaching monthly thresholds.
- Cloud database synchronization (e.g., PostgreSQL or Firebase).
- Dark mode theme toggle.
- Receipt attachment support (saving image files linked to expenses).

---

## 👤 Author

Developed by a 3rd-year Computer Science & Engineering student.
Built to showcase clean Python development, modular design, SQL querying, and desktop GUI engineering.

