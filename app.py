"""
app.py — Compact & Ultra-Fast Student Expense Tracker (Localhost Web App)
Combines SQLite database, REST API, responsive UI, charts, and CSV export in one clean file.
"""
import io
import os
import sqlite3
import webbrowser
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string, Response

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "expenses.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# --- DATABASE SETUP ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL,
                description TEXT
            );
        """)
        # Seed 5 sample records if empty
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM expenses")
        if cur.fetchone()[0] == 0:
            sample = [
                (120.0, "Food", "2026-09-20", "Lunch"),
                (80.0, "Travel", "2026-09-20", "Bus ticket"),
                (500.0, "Education", "2026-09-18", "Semester Books"),
                (750.0, "Shopping", "2026-09-15", "New T-Shirt"),
                (250.0, "Entertainment", "2026-09-12", "Movie with friends"),
            ]
            conn.executemany("INSERT INTO expenses (amount, category, expense_date, description) VALUES (?, ?, ?, ?)", sample)
            conn.commit()

init_db()

# --- WEB DASHBOARD UI ---
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Expense Tracker</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background: #f4f6f9; font-family: 'Segoe UI', system-ui, sans-serif; }
        .nav-bar { background: #1e293b; color: white; padding: 14px 24px; }
        .card-stat { background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 18px; }
        .card-stat h6 { color: #64748b; font-weight: 700; font-size: 0.75rem; text-transform: uppercase; margin: 0; }
        .card-stat h3 { font-weight: 700; margin: 6px 0 0 0; }
        .content-box { background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 22px; }
    </style>
</head>
<body>

    <!-- Header -->
    <div class="nav-bar d-flex justify-content-between align-items-center">
        <h5 class="m-0 fw-bold"><i class="bi bi-wallet2 text-warning me-2"></i>Student Expense Tracker</h5>
        <div class="d-flex gap-2">
            <button class="btn btn-sm btn-light fw-bold" data-bs-toggle="modal" data-bs-target="#addModal">
                <i class="bi bi-plus-circle text-primary me-1"></i> Add Expense
            </button>
            <a href="/api/export" class="btn btn-sm btn-success fw-bold">
                <i class="bi bi-download me-1"></i> Export CSV
            </a>
        </div>
    </div>

    <div class="container-fluid px-4 py-4">

        <!-- Stat Cards -->
        <div class="row g-3 mb-4">
            <div class="col-md-3">
                <div class="card-stat">
                    <h6>Total Spent</h6>
                    <h3 class="text-dark" id="stat-total">₹0</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card-stat">
                    <h6>This Month</h6>
                    <h3 class="text-primary" id="stat-month">₹0</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card-stat">
                    <h6>Total Records</h6>
                    <h3 class="text-success" id="stat-count">0</h3>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card-stat">
                    <h6>Top Category</h6>
                    <h3 class="text-warning" id="stat-top">None</h3>
                </div>
            </div>
        </div>

        <div class="row g-4">
            <!-- Expenses Table -->
            <div class="col-lg-7">
                <div class="content-box">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h6 class="fw-bold m-0"><i class="bi bi-table me-2"></i>Recent Expenses</h6>
                        <div class="d-flex gap-2">
                            <input type="text" id="search" class="form-control form-control-sm" placeholder="Search..." oninput="loadData()">
                            <select id="cat-filter" class="form-select form-select-sm" onchange="loadData()">
                                <option value="All">All Categories</option>
                                <option>Food</option><option>Travel</option><option>Education</option>
                                <option>Shopping</option><option>Bills</option><option>Entertainment</option>
                                <option>Health</option><option>Other</option>
                            </select>
                        </div>
                    </div>

                    <div class="table-responsive" style="max-height: 480px; overflow-y: auto;">
                        <table class="table table-hover align-middle">
                            <thead class="table-light">
                                <tr>
                                    <th>Date</th><th>Category</th><th>Description</th><th class="text-end">Amount</th><th></th>
                                </tr>
                            </thead>
                            <tbody id="table-body">
                                <tr><td colspan="5" class="text-center py-4 text-muted">Loading...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Visual Charts -->
            <div class="col-lg-5">
                <div class="content-box mb-4">
                    <h6 class="fw-bold mb-3"><i class="bi bi-pie-chart me-2"></i>Category Breakdown</h6>
                    <div style="height: 220px; position: relative;">
                        <canvas id="pieChart"></canvas>
                    </div>
                </div>
                <div class="content-box">
                    <h6 class="fw-bold mb-3"><i class="bi bi-bar-chart me-2"></i>Monthly Spending</h6>
                    <div style="height: 180px; position: relative;">
                        <canvas id="barChart"></canvas>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <!-- Add Expense Modal -->
    <div class="modal fade" id="addModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header bg-dark text-white">
                    <h6 class="modal-title fw-bold">Log New Expense</h6>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form onsubmit="addExpense(event)">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label small fw-bold">Amount (₹) *</label>
                            <input type="number" step="0.01" min="0.01" id="add-amt" class="form-control" required placeholder="e.g. 150">
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">Category *</label>
                            <select id="add-cat" class="form-select" required>
                                <option>Food</option><option>Travel</option><option>Education</option>
                                <option>Shopping</option><option>Bills</option><option>Entertainment</option>
                                <option>Health</option><option>Other</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">Date *</label>
                            <input type="date" id="add-date" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">Description</label>
                            <input type="text" id="add-desc" class="form-control" placeholder="Optional notes">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-sm btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-sm btn-primary">Save Expense</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('add-date').value = new Date().toISOString().split('T')[0];
        let pieInst = null, barInst = null;

        async function loadData() {
            const query = document.getElementById('search').value;
            const cat = document.getElementById('cat-filter').value;
            const res = await fetch(`/api/data?q=${encodeURIComponent(query)}&cat=${encodeURIComponent(cat)}`);
            const data = await res.json();

            // Stats
            document.getElementById('stat-total').textContent = '₹' + data.total.toLocaleString(undefined, {minimumFractionDigits: 2});
            document.getElementById('stat-month').textContent = '₹' + data.this_month.toLocaleString(undefined, {minimumFractionDigits: 2});
            document.getElementById('stat-count').textContent = data.count;
            document.getElementById('stat-top').textContent = data.top_cat ? `${data.top_cat[0]} (₹${data.top_cat[1]})` : 'None';

            // Table
            const tbody = document.getElementById('table-body');
            tbody.innerHTML = '';
            if (data.expenses.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="text-center py-4 text-muted">No expenses found</td></tr>';
            } else {
                data.expenses.forEach(e => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${e.expense_date}</td>
                        <td><span class="badge bg-secondary">${e.category}</span></td>
                        <td>${e.description || '-'}</td>
                        <td class="text-end fw-bold">₹${e.amount.toFixed(2)}</td>
                        <td class="text-center">
                            <button class="btn btn-sm btn-link text-danger p-0" onclick="delExpense(${e.id})" title="Delete">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }

            // Charts
            renderCharts(data.categories, data.monthly);
        }

        function renderCharts(cats, monthly) {
            // Category Pie Chart
            const pieCtx = document.getElementById('pieChart').getContext('2d');
            if (pieInst) pieInst.destroy();
            pieInst = new Chart(pieCtx, {
                type: 'doughnut',
                data: {
                    labels: cats.map(c => c[0]),
                    datasets: [{
                        data: cats.map(c => c[1]),
                        backgroundColor: ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7']
                    }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } }
            });

            // Monthly Bar Chart
            const barCtx = document.getElementById('monthlyChart').getContext('2d');
            if (barInst) barInst.destroy();
            barInst = new Chart(barCtx, {
                type: 'bar',
                data: {
                    labels: monthly.map(m => m[0]),
                    datasets: [{ label: 'Spending (₹)', data: monthly.map(m => m[1]), backgroundColor: '#3b82f6' }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true } } }
            });
        }

        async function addExpense(e) {
            e.preventDefault();
            const payload = {
                amount: document.getElementById('add-amt').value,
                category: document.getElementById('add-cat').value,
                expense_date: document.getElementById('add-date').value,
                description: document.getElementById('add-desc').value
            };
            const res = await fetch('/api/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById('addModal')).hide();
                document.getElementById('add-amt').value = '';
                document.getElementById('add-desc').value = '';
                loadData();
            } else {
                const err = await res.json();
                alert(err.error || 'Failed to save');
            }
        }

        async function delExpense(id) {
            if (!confirm('Delete this expense?')) return;
            const res = await fetch(`/api/delete/${id}`, { method: 'POST' });
            if (res.ok) loadData();
        }

        loadData();
    </script>
</body>
</html>
"""

# --- ROUTES ---
@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/data")
def api_data():
    q = request.args.get("q", "").strip()
    cat = request.args.get("cat", "All")
    cur_month = datetime.today().strftime("%Y-%m")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Stats
        cur.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0.0) FROM expenses")
        r_all = cur.fetchone()
        count = r_all[0]
        total = round(float(r_all[1]), 2)

        cur.execute("SELECT COALESCE(SUM(amount), 0.0) FROM expenses WHERE expense_date LIKE ?", (f"{cur_month}%",))
        this_month = round(float(cur.fetchone()[0]), 2)

        cur.execute("SELECT category, SUM(amount) as s FROM expenses GROUP BY category ORDER BY s DESC LIMIT 1")
        top_row = cur.fetchone()
        top_cat = (top_row[0], round(float(top_row[1]), 2)) if top_row else None

        # Filtered expenses
        where = []
        params = []
        if cat and cat != "All":
            where.append("category = ?")
            params.append(cat)
        if q:
            where.append("(description LIKE ? OR category LIKE ?)")
            params.extend([f"%{q}%", f"%{q}%"])

        w_str = ("WHERE " + " AND ".join(where)) if where else ""
        cur.execute(f"SELECT * FROM expenses {w_str} ORDER BY expense_date DESC, id DESC", params)
        expenses = [dict(row) for row in cur.fetchall()]

        # Category aggregates
        cur.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category ORDER BY SUM(amount) DESC")
        categories = [(row[0], round(float(row[1]), 2)) for row in cur.fetchall()]

        # Monthly aggregates
        cur.execute("SELECT substr(expense_date, 1, 7) as ym, SUM(amount) FROM expenses GROUP BY ym ORDER BY ym ASC")
        monthly = [(row[0], round(float(row[1]), 2)) for row in cur.fetchall()]

    return jsonify({
        "count": count,
        "total": total,
        "this_month": this_month,
        "top_cat": top_cat,
        "expenses": expenses,
        "categories": categories,
        "monthly": monthly
    })

@app.route("/api/add", methods=["POST"])
def api_add():
    data = request.get_json() or {}
    try:
        amt = float(data.get("amount", 0))
        if amt <= 0:
            return jsonify({"error": "Amount must be greater than zero."}), 400
    except ValueError:
        return jsonify({"error": "Invalid amount."}), 400

    cat = data.get("category", "").strip()
    date = data.get("expense_date", "").strip()
    desc = data.get("description", "").strip()

    if not cat or not date:
        return jsonify({"error": "Category and Date are required."}), 400

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT INTO expenses (amount, category, expense_date, description) VALUES (?, ?, ?, ?)",
                     (amt, cat, date, desc))
        conn.commit()

    return jsonify({"success": True}), 201

@app.route("/api/delete/<int:exp_id>", methods=["POST"])
def api_delete(exp_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (exp_id,))
        conn.commit()
    return jsonify({"success": True})

@app.route("/api/export")
def api_export():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM expenses ORDER BY expense_date DESC, id DESC").fetchall()

    buf = io.StringIO()
    buf.write("ID,Date,Category,Description,Amount\n")
    for r in rows:
        d = (r["description"] or "").replace('"', '""')
        buf.write(f'{r["id"]},{r["expense_date"]},{r["category"]},"{d}",{r["amount"]:.2f}\n')

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=student_expenses.csv"}
    )

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  Student Expense Tracker is running on localhost!")
    print("  Open in browser: http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False)

