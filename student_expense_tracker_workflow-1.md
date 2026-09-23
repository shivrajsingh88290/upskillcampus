# Student Expense Tracker — Project Workflow / Specification

## 1. Project Goal
Build a small but complete Student Expense Tracker desktop application for a 3rd-year CSE student with Python internship experience.

The application should allow a student to record, manage, search, and analyze personal expenses through a simple GUI.

## 2. Recommended Technology
- Python 3
- Tkinter — GUI
- SQLite3 — local database
- Matplotlib — charts
- datetime — date handling
- csv — optional CSV export
- Git/GitHub — version control

Do NOT use Django, Flask, React, or cloud services. Keep the project beginner/intermediate level and easy to understand.

## 3. Main Features

### A. Dashboard
Show:
- Total expenses
- Current month's expenses
- Number of expense records
- Highest spending category
- Recent expenses

### B. Add Expense
Form fields:
- Amount
- Category
- Date
- Description

Suggested categories:
- Food
- Travel
- Education
- Shopping
- Bills
- Entertainment
- Health
- Other

Validation:
- Amount must be a positive number
- Date must be valid
- Category must be selected
- Description can be optional

### C. View Expenses
Display expenses in a table with:
- ID
- Date
- Category
- Description
- Amount

Functions:
- Sort by date/amount
- Select a record
- Delete selected expense
- Edit selected expense

### D. Search / Filter
Allow filtering by:
- Category
- Date/month
- Amount range
- Description keyword

Include a "Clear Filter" button.

### E. Reports / Analytics
Calculate:
- Total spending
- Category-wise spending
- Monthly spending

Use Matplotlib to display:
1. Pie/donut chart for category-wise spending
2. Bar chart for monthly spending

Charts should be simple and readable.

### F. Export
Provide an option to export expenses to CSV.

## 4. Database Design

Use SQLite database file:
`expenses.db`

Table:
`expenses`

Columns:
- id INTEGER PRIMARY KEY AUTOINCREMENT
- amount REAL NOT NULL
- category TEXT NOT NULL
- expense_date TEXT NOT NULL
- description TEXT

Create the database automatically when the application starts.

## 5. Suggested Project Structure

expense_tracker/
│
├── main.py
├── database.py
├── models.py
├── ui.py
├── reports.py
├── utils.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   └── expenses.db
│
└── exports/
    └── .gitkeep

Keep the architecture simple. Do not over-engineer it.

## 6. Responsibilities of Files

### main.py
- Application entry point
- Initialize database
- Start Tkinter application

### database.py
Functions for:
- create_database()
- add_expense()
- get_expenses()
- update_expense()
- delete_expense()
- filter_expenses()
- get_category_totals()
- get_monthly_totals()

Use parameterized SQL queries.

### models.py
Create a simple Expense model/dataclass if useful.

### ui.py
Build the Tkinter interface:
- Main window
- Dashboard
- Add Expense form
- Expense table
- Search/filter controls
- Buttons
- Reports section

### reports.py
- Calculate summaries
- Generate Matplotlib charts

### utils.py
Reusable validation/date/CSV helper functions.

## 7. GUI Layout

Create a clean student-friendly interface.

Suggested navigation:
[ Dashboard ] [ Add Expense ] [ Expenses ] [ Reports ]

Dashboard:
------------------------------------
 Student Expense Tracker
------------------------------------
 Total Spending | This Month | Records

 Recent Expenses
 -----------------------------------
 Date | Category | Description | Amount

Add Expense:
------------------------------------
 Amount:       [             ]
 Category:     [Dropdown     ]
 Date:         [             ]
 Description:  [             ]

        [ Add Expense ]

Expenses:
------------------------------------
 Search: [        ]
 Category: [All ▼]
 Month:    [        ]

[Search] [Clear]

Table
------------------------------------
 ID | Date | Category | Description | Amount

[Edit] [Delete] [Export CSV]

Reports:
------------------------------------
 [Category Chart]
 [Monthly Chart]

## 8. User Flow

1. User starts `main.py`.
2. Application creates `expenses.db` if it does not exist.
3. Dashboard opens.
4. User selects "Add Expense".
5. User enters expense information.
6. Application validates the input.
7. Expense is saved to SQLite.
8. Dashboard/table refreshes.
9. User can edit/delete/search expenses.
10. User can open Reports.
11. Application calculates statistics and displays charts.
12. User can export data to CSV.

## 9. Error Handling

Handle common errors gracefully:
- Empty amount
- Non-numeric amount
- Negative amount
- Invalid date
- Missing category
- Database errors
- No records found
- Invalid record selection

Show user-friendly Tkinter message boxes instead of crashing.

## 10. Code Quality Requirements

- Use functions and classes where appropriate.
- Use meaningful variable/function names.
- Add short comments for important logic.
- Avoid putting the entire application in one file.
- Use parameterized SQLite queries.
- Keep code readable for a student who will explain it in an interview.
- Do not copy unnecessarily complex architecture.
- Do not add unnecessary dependencies.

## 11. requirements.txt

Use only packages that are actually required.

Expected external dependency:
matplotlib

Tkinter and sqlite3 normally come with Python.

## 12. README.md Requirements

README should contain:
- Project title
- Project description
- Features
- Technologies used
- Project structure
- Installation steps
- How to run
- Screenshots placeholder
- Future improvements
- Author section

Installation example:

```bash
git clone <repository-url>
cd expense_tracker
pip install -r requirements.txt
python main.py
```

## 13. Testing Checklist

Before considering the project complete, test:

[ ] Application starts without errors
[ ] Database is created automatically
[ ] Add valid expense
[ ] Reject invalid amount
[ ] Reject negative amount
[ ] Reject invalid date
[ ] Display expenses
[ ] Edit expense
[ ] Delete expense
[ ] Search expense
[ ] Filter by category
[ ] Filter by month
[ ] Dashboard totals update correctly
[ ] Category chart works
[ ] Monthly chart works
[ ] CSV export works
[ ] Application handles empty database
[ ] Application does not crash on normal invalid input

## 14. Sample Data for Testing

Use these only as optional test records:

Food | 120 | 2026-09-20 | Lunch
Travel | 80 | 2026-09-20 | Bus
Education | 500 | 2026-09-18 | Books
Shopping | 750 | 2026-09-15 | Clothes
Entertainment | 250 | 2026-09-12 | Movie

## 15. Future Improvements

Do NOT implement these unless the basic project is finished:
- User login
- Cloud database
- Mobile application
- AI expense prediction
- Online payment integration
- Multi-user accounts

These can be mentioned in README as future scope.

## 16. Antigravity / Coding Agent Instructions

Build the project according to this specification.

Important:
1. First inspect the project folder.
2. Create the complete folder/file structure.
3. Implement the SQLite database layer.
4. Implement the Tkinter UI.
5. Implement CRUD operations.
6. Implement search/filter.
7. Implement reports/charts.
8. Implement CSV export.
9. Add error handling.
10. Create README.md and requirements.txt.
11. Run/test the application.
12. Fix errors found during testing.
13. Keep the implementation simple enough for a 3rd-year CSE student to understand and explain in a viva/interview.
14. Do not add unnecessary frameworks or advanced features.
15. At the end, provide a short explanation of how each file works and the commands required to run the project.

## 17. Final Expected Result

A working desktop application named:

"Student Expense Tracker"

The project should demonstrate:
- Python programming
- Functions/classes
- GUI development
- SQLite/database operations
- CRUD operations
- Data filtering
- Basic data visualization
- CSV file handling
- Error handling
- Git/GitHub readiness
