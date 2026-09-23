"""
web_app.py
Web interface for the Student Expense Tracker.
Runs on localhost:5000 and connects to the same SQLite database (data/expenses.db).
Provides Dashboard, Add Expense, Filterable Expenses Table, Interactive Charts, and CSV Export.
"""
import io
import os
from datetime import datetime
from flask import Flask, jsonify, request, render_template_string, Response, send_file
import database
import utils
import reports
from models import Expense

app = Flask(__name__)

# Ensure DB initialized
database.create_database()
database.seed_sample_data()

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Expense Tracker</title>
    <!-- Modern CSS & Chart.js -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #2c3e50;
            --accent: #3498db;
            --success: #27ae60;
            --danger: #e74c3c;
            --bg-light: #f8f9fa;
        }
        body {
            background-color: var(--bg-light);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            color: #2d3748;
        }
        .navbar-custom {
            background-color: var(--primary);
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            border: 1px solid #e2e8f0;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 14px rgba(0,0,0,0.06);
        }
        .stat-title {
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            color: #718096;
            text-transform: uppercase;
        }
        .stat-value {
            font-size: 1.65rem;
            font-weight: 700;
            margin-top: 4px;
        }
        .content-card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #e2e8f0;
            margin-bottom: 24px;
        }
        .nav-pills .nav-link {
            color: #cfd8dc;
            font-weight: 600;
            border-radius: 8px;
            padding: 8px 18px;
        }
        .nav-pills .nav-link.active {
            background-color: #1a252f;
            color: white;
        }
        .btn-primary-custom {
            background-color: var(--primary);
            color: white;
            border: none;
        }
        .btn-primary-custom:hover {
            background-color: #1a252f;
            color: white;
        }
        .table thead th {
            background-color: #edf2f7;
            color: var(--primary);
            font-weight: 700;
            border-bottom: none;
        }
        .badge-cat {
            background-color: #e2e8f0;
            color: #2d3748;
            font-weight: 600;
            padding: 6px 10px;
            border-radius: 6px;
        }
    </style>
</head>
<body>

    <!-- Navigation Bar -->
    <nav class="navbar navbar-expand-lg navbar-dark navbar-custom py-2">
        <div class="container-fluid px-4">
            <a class="navbar-brand fw-bold d-flex align-items-center gap-2" href="#">
                <i class="bi bi-wallet2 fs-4 text-warning"></i>
                <span>Student Expense Tracker</span>
            </a>
            <div class="d-flex align-items-center gap-2">
                <button class="btn btn-sm btn-outline-light d-flex align-items-center gap-1" data-bs-toggle="modal" data-bs-target="#addExpenseModal">
                    <i class="bi bi-plus-circle"></i> Add Expense
                </button>
                <a href="/api/export-csv" class="btn btn-sm btn-success d-flex align-items-center gap-1">
                    <i class="bi bi-file-earmark-spreadsheet"></i> Export CSV
                </a>
            </div>
        </div>
    </nav>

    <!-- Main Container -->
    <div class="container-fluid px-4 py-4">

        <!-- Stat Cards Row -->
        <div class="row g-3 mb-4">
            <div class="col-12 col-md-6 col-xl-3">
                <div class="stat-card">
                    <div class="stat-title">Total Spending</div>
                    <div class="stat-value text-dark" id="stat-total">₹0.00</div>
                    <small class="text-muted">All-time recorded expenses</small>
                </div>
            </div>
            <div class="col-12 col-md-6 col-xl-3">
                <div class="stat-card">
                    <div class="stat-title">This Month</div>
                    <div class="stat-value text-primary" id="stat-month">₹0.00</div>
                    <small class="text-muted" id="stat-month-label">Current month</small>
                </div>
            </div>
            <div class="col-12 col-md-6 col-xl-3">
                <div class="stat-card">
                    <div class="stat-title">Total Records</div>
                    <div class="stat-value text-success" id="stat-count">0</div>
                    <small class="text-muted">Logged transactions</small>
                </div>
            </div>
            <div class="col-12 col-md-6 col-xl-3">
                <div class="stat-card">
                    <div class="stat-title">Top Category</div>
                    <div class="stat-value text-warning" id="stat-top-cat">None</div>
                    <small class="text-muted">Highest spending category</small>
                </div>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <ul class="nav nav-pills mb-4 bg-white p-2 rounded-3 border" id="pills-tab" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active text-dark" id="tab-expenses-btn" data-bs-toggle="pill" data-bs-target="#tab-expenses" type="button" role="tab">
                    <i class="bi bi-table me-1"></i> Expenses List & Search
                </button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link text-dark" id="tab-charts-btn" data-bs-toggle="pill" data-bs-target="#tab-charts" type="button" role="tab" onclick="loadCharts()">
                    <i class="bi bi-pie-chart me-1"></i> Spending Analytics & Charts
                </button>
            </li>
        </ul>

        <div class="tab-content" id="pills-tabContent">
            <!-- TAB 1: Expenses Table & Filters -->
            <div class="tab-pane fade show active" id="tab-expenses" role="tabpanel">
                <div class="content-card">
                    <h5 class="fw-bold mb-3"><i class="bi bi-funnel me-1"></i> Search & Filter Expenses</h5>
                    <form id="filter-form" class="row g-2 mb-4" onsubmit="event.preventDefault(); fetchExpenses();">
                        <div class="col-md-3">
                            <label class="form-label small fw-bold text-muted">Keyword</label>
                            <input type="text" id="filter-keyword" class="form-control form-control-sm" placeholder="Search description...">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label small fw-bold text-muted">Category</label>
                            <select id="filter-category" class="form-select form-select-sm">
                                <option value="All">All Categories</option>
                                <option value="Food">Food</option>
                                <option value="Travel">Travel</option>
                                <option value="Education">Education</option>
                                <option value="Shopping">Shopping</option>
                                <option value="Bills">Bills</option>
                                <option value="Entertainment">Entertainment</option>
                                <option value="Health">Health</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                        <div class="col-md-2">
                            <label class="form-label small fw-bold text-muted">Month (YYYY-MM)</label>
                            <input type="text" id="filter-month" class="form-control form-control-sm" placeholder="e.g. 2026-09">
                        </div>
                        <div class="col-md-2">
                            <label class="form-label small fw-bold text-muted">Sort By</label>
                            <select id="filter-sort" class="form-select form-select-sm">
                                <option value="date_desc">Date (Newest)</option>
                                <option value="date_asc">Date (Oldest)</option>
                                <option value="amount_desc">Amount (Highest)</option>
                                <option value="amount_asc">Amount (Lowest)</option>
                            </select>
                        </div>
                        <div class="col-md-3 d-flex align-items-end gap-2">
                            <button type="button" class="btn btn-sm btn-primary-custom flex-grow-1" onclick="fetchExpenses()">
                                <i class="bi bi-search"></i> Apply Filter
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-secondary" onclick="resetFilters()">
                                Reset
                            </button>
                        </div>
                    </form>

                    <!-- Table -->
                    <div class="table-responsive">
                        <table class="table table-hover align-middle">
                            <thead>
                                <tr>
                                    <th style="width: 70px;">ID</th>
                                    <th style="width: 130px;">Date</th>
                                    <th style="width: 150px;">Category</th>
                                    <th>Description</th>
                                    <th style="width: 130px;" class="text-end">Amount (₹)</th>
                                    <th style="width: 140px;" class="text-center">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="expenses-tbody">
                                <tr><td colspan="6" class="text-center text-muted py-4">Loading expenses...</td></tr>
                            </tbody>
                        </table>
                    </div>

                    <div class="d-flex justify-content-between align-items-center mt-3 pt-2 border-top">
                        <span class="small fw-bold text-muted" id="table-summary-text">Showing 0 records</span>
                        <button class="btn btn-sm btn-outline-success" onclick="window.location.href='/api/export-csv'">
                            <i class="bi bi-download me-1"></i> Download as CSV
                        </button>
                    </div>
                </div>
            </div>

            <!-- TAB 2: Charts & Analytics -->
            <div class="tab-pane fade" id="tab-charts" role="tabpanel">
                <div class="row g-4">
                    <div class="col-12 col-lg-6">
                        <div class="content-card h-100">
                            <h5 class="fw-bold mb-3"><i class="bi bi-pie-chart me-1"></i> Category Spending Distribution</h5>
                            <div style="height: 350px; position: relative;">
                                <canvas id="categoryChart"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-12 col-lg-6">
                        <div class="content-card h-100">
                            <h5 class="fw-bold mb-3"><i class="bi bi-bar-chart me-1"></i> Monthly Spending Trajectory</h5>
                            <div style="height: 350px; position: relative;">
                                <canvas id="monthlyChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>

    <!-- Add Expense Modal -->
    <div class="modal fade" id="addExpenseModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header navbar-custom text-white">
                    <h5 class="modal-title fw-bold"><i class="bi bi-plus-circle me-1"></i> Add New Expense</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form id="add-expense-form" onsubmit="handleAddExpense(event)">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label fw-bold">Amount (₹) *</label>
                            <input type="number" step="0.01" min="0.01" id="add-amount" class="form-control" placeholder="e.g. 150.00" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Category *</label>
                            <select id="add-category" class="form-select" required>
                                <option value="Food">Food</option>
                                <option value="Travel">Travel</option>
                                <option value="Education">Education</option>
                                <option value="Shopping">Shopping</option>
                                <option value="Bills">Bills</option>
                                <option value="Entertainment">Entertainment</option>
                                <option value="Health">Health</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Date (YYYY-MM-DD) *</label>
                            <input type="date" id="add-date" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Description (Optional)</label>
                            <input type="text" id="add-desc" class="form-control" placeholder="e.g. Lunch with project group">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary-custom">Save Expense</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Edit Expense Modal -->
    <div class="modal fade" id="editExpenseModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header navbar-custom text-white">
                    <h5 class="modal-title fw-bold"><i class="bi bi-pencil-square me-1"></i> Edit Expense</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form id="edit-expense-form" onsubmit="handleEditExpense(event)">
                    <input type="hidden" id="edit-id">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label fw-bold">Amount (₹) *</label>
                            <input type="number" step="0.01" min="0.01" id="edit-amount" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Category *</label>
                            <select id="edit-category" class="form-select" required>
                                <option value="Food">Food</option>
                                <option value="Travel">Travel</option>
                                <option value="Education">Education</option>
                                <option value="Shopping">Shopping</option>
                                <option value="Bills">Bills</option>
                                <option value="Entertainment">Entertainment</option>
                                <option value="Health">Health</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Date (YYYY-MM-DD) *</label>
                            <input type="date" id="edit-date" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Description (Optional)</label>
                            <input type="text" id="edit-desc" class="form-control">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="submit" class="btn btn-primary-custom">Save Changes</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- Scripts -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let catChartInstance = null;
        let monthChartInstance = null;

        // Set default date to today in Add modal
        document.getElementById('add-date').value = new Date().toISOString().split('T')[0];

        async function fetchDashboard() {
            try {
                const res = await fetch('/api/dashboard');
                const data = await res.json();
                document.getElementById('stat-total').textContent = '₹' + data.total_spending.toLocaleString(undefined, {minimumFractionDigits: 2});
                document.getElementById('stat-month').textContent = '₹' + data.current_month_spending.toLocaleString(undefined, {minimumFractionDigits: 2});
                document.getElementById('stat-count').textContent = data.record_count + ' items';
                
                const topCat = data.highest_category;
                if (topCat && topCat[0] !== 'None') {
                    document.getElementById('stat-top-cat').textContent = topCat[0] + ' (₹' + Number(topCat[1]).toFixed(0) + ')';
                } else {
                    document.getElementById('stat-top-cat').textContent = 'None';
                }
            } catch (err) {
                console.error('Error fetching dashboard stats:', err);
            }
        }

        async function fetchExpenses() {
            const keyword = document.getElementById('filter-keyword').value;
            const category = document.getElementById('filter-category').value;
            const month = document.getElementById('filter-month').value;
            const sort = document.getElementById('filter-sort').value;

            const params = new URLSearchParams();
            if (keyword) params.append('search', keyword);
            if (category && category !== 'All') params.append('category', category);
            if (month) params.append('month', month);
            if (sort) params.append('sort_by', sort);

            try {
                const res = await fetch('/api/expenses?' + params.toString());
                const records = await res.json();
                const tbody = document.getElementById('expenses-tbody');
                tbody.innerHTML = '';

                let total = 0;
                if (records.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">No matching expenses found.</td></tr>';
                } else {
                    records.forEach(r => {
                        total += r.amount;
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td class="text-muted fw-bold">${r.id}</td>
                            <td>${r.expense_date}</td>
                            <td><span class="badge-cat">${r.category}</span></td>
                            <td>${r.description || '<span class="text-muted">-</span>'}</td>
                            <td class="text-end fw-bold">₹${r.amount.toFixed(2)}</td>
                            <td class="text-center">
                                <button class="btn btn-sm btn-outline-primary py-0 px-2 me-1" onclick="openEditModal(${r.id}, ${r.amount}, '${r.category}', '${r.expense_date}', '${escapeQuotes(r.description)}')">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger py-0 px-2" onclick="deleteExpense(${r.id})">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </td>
                        `;
                        tbody.appendChild(tr);
                    });
                }
                document.getElementById('table-summary-text').textContent = `Showing ${records.length} records | Total: ₹${total.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
            } catch (err) {
                console.error('Error fetching expenses:', err);
            }
        }

        function escapeQuotes(str) {
            return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
        }

        function resetFilters() {
            document.getElementById('filter-keyword').value = '';
            document.getElementById('filter-category').value = 'All';
            document.getElementById('filter-month').value = '';
            document.getElementById('filter-sort').value = 'date_desc';
            fetchExpenses();
        }

        async function handleAddExpense(e) {
            e.preventDefault();
            const payload = {
                amount: document.getElementById('add-amount').value,
                category: document.getElementById('add-category').value,
                expense_date: document.getElementById('add-date').value,
                description: document.getElementById('add-desc').value
            };

            const res = await fetch('/api/expenses', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById('addExpenseModal')).hide();
                document.getElementById('add-expense-form').reset();
                document.getElementById('add-date').value = new Date().toISOString().split('T')[0];
                fetchDashboard();
                fetchExpenses();
                if (document.getElementById('tab-charts').classList.contains('active')) loadCharts();
            } else {
                alert(data.error || 'Failed to add expense.');
            }
        }

        function openEditModal(id, amount, category, date, desc) {
            document.getElementById('edit-id').value = id;
            document.getElementById('edit-amount').value = amount;
            document.getElementById('edit-category').value = category;
            document.getElementById('edit-date').value = date;
            document.getElementById('edit-desc').value = desc;
            new bootstrap.Modal(document.getElementById('editExpenseModal')).show();
        }

        async function handleEditExpense(e) {
            e.preventDefault();
            const id = document.getElementById('edit-id').value;
            const payload = {
                amount: document.getElementById('edit-amount').value,
                category: document.getElementById('edit-category').value,
                expense_date: document.getElementById('edit-date').value,
                description: document.getElementById('edit-desc').value
            };

            const res = await fetch('/api/expenses/' + id, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok) {
                bootstrap.Modal.getInstance(document.getElementById('editExpenseModal')).hide();
                fetchDashboard();
                fetchExpenses();
                if (document.getElementById('tab-charts').classList.contains('active')) loadCharts();
            } else {
                alert(data.error || 'Failed to update expense.');
            }
        }

        async function deleteExpense(id) {
            if (!confirm(`Are you sure you want to delete expense #${id}?`)) return;
            const res = await fetch('/api/expenses/' + id, { method: 'DELETE' });
            if (res.ok) {
                fetchDashboard();
                fetchExpenses();
                if (document.getElementById('tab-charts').classList.contains('active')) loadCharts();
            } else {
                alert('Failed to delete expense.');
            }
        }

        async function loadCharts() {
            try {
                // Category Donut Chart
                const catRes = await fetch('/api/reports/category');
                const catData = await catRes.json();
                
                const catLabels = catData.map(c => c[0]);
                const catValues = catData.map(c => c[1]);

                if (catChartInstance) catChartInstance.destroy();
                const ctxCat = document.getElementById('categoryChart').getContext('2d');
                catChartInstance = new Chart(ctxCat, {
                    type: 'doughnut',
                    data: {
                        labels: catLabels,
                        datasets: [{
                            data: catValues,
                            backgroundColor: ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });

                // Monthly Bar Chart
                const monthRes = await fetch('/api/reports/monthly');
                const monthData = await monthRes.json();

                const monthLabels = monthData.map(m => m[0]);
                const monthValues = monthData.map(m => m[1]);

                if (monthChartInstance) monthChartInstance.destroy();
                const ctxMonth = document.getElementById('monthlyChart').getContext('2d');
                monthChartInstance = new Chart(ctxMonth, {
                    type: 'bar',
                    data: {
                        labels: monthLabels,
                        datasets: [{
                            label: 'Spending (₹)',
                            data: monthValues,
                            backgroundColor: '#3498db',
                            borderColor: '#2980b9',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            } catch (err) {
                console.error('Error loading charts:', err);
            }
        }

        // Initialize on load
        fetchDashboard();
        fetchExpenses();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    current_m = utils.get_current_month()
    summary = database.get_dashboard_summary(current_month_str=current_m)
    return jsonify({
        "record_count": summary["record_count"],
        "total_spending": summary["total_spending"],
        "current_month_spending": summary["current_month_spending"],
        "highest_category": summary["highest_category"],
        "recent_expenses": [e.to_dict() for e in summary["recent_expenses"]]
    })

@app.route("/api/expenses", methods=["GET"])
def api_get_expenses():
    category = request.args.get("category")
    search = request.args.get("search")
    month = request.args.get("month")
    min_amount = request.args.get("min_amount", type=float)
    max_amount = request.args.get("max_amount", type=float)
    sort_by = request.args.get("sort_by", default="date_desc")

    expenses = database.filter_expenses(
        category=category,
        search_keyword=search,
        month=month,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_by=sort_by
    )
    return jsonify([e.to_dict() for e in expenses])

@app.route("/api/expenses", methods=["POST"])
def api_add_expense():
    data = request.get_json() or {}
    ok, exp, err = utils.validate_expense_input(
        amount_str=str(data.get("amount", "")),
        category_str=str(data.get("category", "")),
        date_str=str(data.get("expense_date", "")),
        description_str=str(data.get("description", ""))
    )
    if not ok:
        return jsonify({"error": err}), 400

    new_id = database.add_expense(
        amount=exp.amount,
        category=exp.category,
        expense_date=exp.expense_date,
        description=exp.description
    )
    return jsonify({"success": True, "id": new_id}), 201

@app.route("/api/expenses/<int:expense_id>", methods=["PUT"])
def api_update_expense(expense_id):
    data = request.get_json() or {}
    ok, exp, err = utils.validate_expense_input(
        amount_str=str(data.get("amount", "")),
        category_str=str(data.get("category", "")),
        date_str=str(data.get("expense_date", "")),
        description_str=str(data.get("description", ""))
    )
    if not ok:
        return jsonify({"error": err}), 400

    updated = database.update_expense(
        expense_id=expense_id,
        amount=exp.amount,
        category=exp.category,
        expense_date=exp.expense_date,
        description=exp.description
    )
    if updated:
        return jsonify({"success": True})
    return jsonify({"error": "Expense record not found"}), 404

@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def api_delete_expense(expense_id):
    deleted = database.delete_expense(expense_id)
    if deleted:
        return jsonify({"success": True})
    return jsonify({"error": "Expense record not found"}), 404

@app.route("/api/reports/category", methods=["GET"])
def api_reports_category():
    totals = database.get_category_totals()
    return jsonify(totals)

@app.route("/api/reports/monthly", methods=["GET"])
def api_reports_monthly():
    totals = database.get_monthly_totals()
    return jsonify(totals)

@app.route("/api/export-csv", methods=["GET"])
def api_export_csv():
    expenses = database.get_expenses()
    csv_buffer = io.StringIO()
    # Write header
    csv_buffer.write("ID,Date,Category,Description,Amount\n")
    for exp in expenses:
        clean_desc = (exp.description or "").replace('"', '""')
        csv_buffer.write(f'{exp.id},"{exp.expense_date}","{exp.category}","{clean_desc}",{exp.amount:.2f}\n')

    filename = f"expenses_{datetime.today().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        csv_buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    print("==================================================================")
    print(" Student Expense Tracker Web Server running on localhost!")
    print(" Access the application in your browser at: http://127.0.0.1:5000")
    print("==================================================================")
    app.run(host="127.0.0.1", port=5000, debug=False)

