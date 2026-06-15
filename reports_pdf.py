import os
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
from utils import *

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "reports")
os.makedirs(REPORT_DIR, exist_ok=True)

RS = "Rs."  # Using ASCII-safe Rupee notation (avoids Unicode font dependency)


class SalonPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 15)
        self.set_text_color(192, 132, 252)
        self.cell(0, 10, "Saloon Pro", align="L")
        self.set_font("Helvetica", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, datetime.now().strftime("%d %b %Y %H:%M"), align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(192, 132, 252)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(40, 40, 60)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(200, 200, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)

    def kv_line(self, key, value):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(80, 80, 80)
        self.cell(80, 6, key)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(30, 30, 30)
        self.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")

    def table(self, headers, data, col_widths=None):
        if not data:
            return
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(192, 132, 252)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("Helvetica", "", 8)
        self.set_text_color(40, 40, 40)
        for row in data:
            for i, cell in enumerate(row):
                align = "R" if isinstance(cell, (int, float)) else "L"
                self.cell(col_widths[i], 6, str(cell), border=1, align=align)
            self.ln()
        self.ln(3)


def _r(val):
    return f"{RS}{val:,.0f}" if isinstance(val, (int, float)) else str(val)


def generate_financial_pdf():
    buf = BytesIO()
    pdf = SalonPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 30, 50)
    pdf.cell(0, 12, "Financial Summary Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    stats = get_dashboard_stats()
    monthly = get_monthly_revenue()
    expenses = load_expenses()
    salary_total = get_staff_salary_total()
    total_exp = sum(e.amount for e in expenses)
    net_profit = stats["total_revenue"] - total_exp - salary_total
    margin = (net_profit / stats["total_revenue"] * 100) if stats["total_revenue"] > 0 else 0
    avg_txn = stats["total_revenue"] / max(stats["total_transactions"], 1)

    pdf.section_title("Revenue")
    pdf.kv_line("Total Revenue:", _r(stats["total_revenue"]))
    pdf.kv_line("This Month:", _r(stats["month_revenue"]))
    pdf.kv_line("Today:", _r(stats["today_revenue"]))
    pdf.kv_line("Average Transaction:", _r(avg_txn))

    pdf.section_title("Expenses")
    pdf.kv_line("Total Expenses:", _r(total_exp))
    pdf.kv_line("Staff Salaries:", _r(salary_total) + "/mo")

    pdf.section_title("Profitability")
    pdf.kv_line("Net Profit:", _r(net_profit))
    pdf.kv_line("Profit Margin:", f"{margin:.1f}%")

    pdf.section_title("Customers")
    pdf.kv_line("Total Customers:", str(stats["total_customers"]))
    pdf.kv_line("Total Transactions:", str(stats["total_transactions"]))
    pdf.kv_line("Staff Count:", str(stats["total_staff"]))
    repeat = get_repeat_customers()
    ratio = (len(repeat) / stats["total_customers"] * 100) if stats["total_customers"] > 0 else 0
    pdf.kv_line("Repeat Rate:", f"{ratio:.1f}%")

    pdf.add_page()
    pdf.section_title("Monthly Revenue Breakdown")
    if monthly:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        data = [[months[i], _r(monthly[f"{i+1:02d}"]["revenue"]), str(monthly[f"{i+1:02d}"]["count"])]
                for i in range(12) if monthly[f"{i+1:02d}"]["revenue"] > 0]
        pdf.table(["Month", "Revenue", "Transactions"], data, [40, 90, 60])

    pdf.section_title("Expenses by Category")
    exp_cats = get_expense_by_category()
    if exp_cats:
        data = [[cat, _r(amt)] for cat, amt in sorted(exp_cats.items(), key=lambda x: -x[1])]
        pdf.table(["Category", "Amount"], data, [100, 90])

    pdf.section_title("Top Customers")
    top = get_top_customers(10)
    if top:
        data = [[c.name, c.phone, str(c.total_visits), _r(c.total_spent)] for c in top]
        pdf.table(["Name", "Phone", "Visits", "Total Spent"], data, [50, 45, 30, 65])

    pdf.output(buf)
    buf.seek(0)
    return buf


def generate_full_report_pdf():
    buf = BytesIO()
    pdf = SalonPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(30, 30, 50)
    pdf.cell(0, 14, "SALOON PRO", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, "Complete Business Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"Generated: {datetime.now().strftime('%d %B %Y at %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # 1. Financial Summary
    pdf.section_title("1. Financial Summary")
    stats = get_dashboard_stats()
    expenses = load_expenses()
    salary_total = get_staff_salary_total()
    total_exp = sum(e.amount for e in expenses)
    net_profit = stats["total_revenue"] - total_exp - salary_total
    margin = (net_profit / stats["total_revenue"] * 100) if stats["total_revenue"] > 0 else 0
    avg_txn = stats["total_revenue"] / max(stats["total_transactions"], 1)
    repeat = get_repeat_customers()
    ratio = (len(repeat) / stats["total_customers"] * 100) if stats["total_customers"] > 0 else 0

    pdf.kv_line("Total Revenue:", _r(stats["total_revenue"]))
    pdf.kv_line("Total Expenses:", _r(total_exp))
    pdf.kv_line("Staff Salaries:", _r(salary_total) + "/mo")
    pdf.kv_line("Net Profit:", _r(net_profit))
    pdf.kv_line("Profit Margin:", f"{margin:.1f}%")
    pdf.kv_line("Avg Transaction:", _r(avg_txn))
    pdf.kv_line("Repeat Rate:", f"{ratio:.1f}%")
    pdf.ln(3)

    # 2. All Transactions
    pdf.add_page()
    pdf.section_title("2. All Transactions")
    txns = load_transactions(500)
    if txns:
        data = [[t.timestamp.strftime("%d-%b-%Y"), t.timestamp.strftime("%H:%M"),
                 t.customer.name if t.customer else "N/A", t.service, _r(t.amount), t.payment_method]
                for t in txns]
        pdf.table(["Date", "Time", "Customer", "Service", "Amount", "Payment"], data, [25, 18, 40, 35, 32, 40])

    # 3. All Customers
    pdf.section_title("3. All Customers")
    custs = load_customers()
    if custs:
        data = [[c.name, c.phone, str(c.total_visits), _r(c.total_spent)] for c in custs]
        pdf.table(["Name", "Phone", "Visits", "Total Spent"], data, [50, 50, 30, 60])

    # 4. Staff
    pdf.add_page()
    pdf.section_title("4. Staff Members")
    stff = load_staff()
    if stff:
        data = [[s.name, s.role, s.phone, _r(s.salary), f"{s.commission_rate:.0f}%"] for s in stff]
        pdf.table(["Name", "Role", "Phone", "Salary", "Comm."], data, [40, 40, 40, 40, 30])

    # 5. Expenses
    pdf.section_title("5. Expenses")
    exps = load_expenses()
    if exps:
        data = [[e.date_incurred.strftime("%d-%b-%Y") if e.date_incurred else "",
                 e.category[:25], _r(e.amount), "Yes" if e.recurring else "No"] for e in exps]
        pdf.table(["Date", "Category", "Amount", "Recurring"], data, [25, 80, 50, 35])

    # 6. Inventory
    pdf.section_title("6. Inventory")
    inv = load_inventory()
    if inv:
        data = [[i.name, i.category, f"{i.quantity:.0f} {i.unit}", _r(i.unit_price),
                 "Low" if i.quantity <= i.min_stock_level else "OK"] for i in inv]
        pdf.table(["Item", "Category", "Stock", "Price", "Status"], data, [45, 40, 35, 35, 35])

    pdf.output(buf)
    buf.seek(0)
    return buf
