import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import hashlib
import re
from datetime import datetime, date, timedelta
from database import init_db, seed_defaults, get_db, SaloonSetting, backup_database, restore_database, list_backups
from auth import check_auth, change_password, create_user
from utils import *
from ai_agent import analyze_dashboard_data, get_revenue_prediction, get_customer_suggestion, get_api_key, set_api_key_in_db, chat_with_saloon_data
from reports_pdf import generate_financial_pdf, generate_full_report_pdf
from styles import CSS, PAGE_CONFIG

st.set_page_config(**PAGE_CONFIG)
st.markdown(CSS, unsafe_allow_html=True)

init_db()
seed_defaults()

if "username" not in st.session_state:
    st.session_state["username"] = ""

if "role" not in st.session_state:
    st.session_state["role"] = "admin"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    check_auth()

@st.cache_data(ttl=60, show_spinner="Loading dashboard...")
def cached_dashboard_stats():
    return get_dashboard_stats()

@st.cache_data(ttl=120, show_spinner=False)
def cached_monthly_revenue():
    return get_monthly_revenue()

@st.cache_data(ttl=60, show_spinner=False)
def cached_repeat_customers():
    return get_repeat_customers()

@st.cache_data(ttl=300, show_spinner=False)
def cached_top_customers():
    return get_top_customers()

@st.cache_data(ttl=60, show_spinner=False)
def cached_daily_revenue():
    return get_daily_revenue(30)

@st.cache_data(ttl=60, show_spinner=False)
def cached_expense_categories():
    return get_expense_by_category()

NAV_ITEMS = [
    ("🏠", "Home", "dashboard"),
    ("📅", "Book", "appointments"),
    ("👥", "Clients", "customers"),
    ("💰", "Sales", "transactions"),
    ("🤖", "AI", "ai_chat"),
]

MORE_PAGES = {
    "👨‍💼 Staff": "staff",
    "📦 Expenses": "expenses",
    "📦 Stock": "inventory",
    "📄 Reports": "reports",
    "🤖 AI": "analytics",
    "🧾 Invoices": "invoices",
    "⚙️ Settings": "settings",
}

def render_header(title, subtitle=""):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

def dashboard_page():
    render_header("Dashboard", "Real-time salon performance overview")

    stats = cached_dashboard_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="icon">💰</div><div class="value">₹{stats['today_revenue']:,.0f}</div><div class="label">Today</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="icon">📈</div><div class="value">₹{stats['month_revenue']:,.0f}</div><div class="label">This Month</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="icon">🏆</div><div class="value">₹{stats['total_revenue']:,.0f}</div><div class="label">Total Revenue</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="icon">📊</div><div class="value">{stats['total_customers']}</div><div class="label">Total Customers</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="icon">🔄</div><div class="value">{stats['total_transactions']}</div><div class="label">Transactions</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="icon">👨‍💼</div><div class="value">{stats['total_staff']}</div><div class="label">Staff</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="icon">💸</div><div class="value">₹{stats['total_expenses']:,.0f}</div><div class="label">Total Expenses</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="icon">🎯</div><div class="value">₹{stats['avg_per_customer']:,.0f}</div><div class="label">Avg/Customer</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="glass-card"><h3>📈 Monthly Revenue Trend</h3>', unsafe_allow_html=True)
        monthly = cached_monthly_revenue()
        if monthly:
            months_list = list(monthly.keys())
            rev_list = [monthly[m]["revenue"] for m in months_list]
            count_list = [monthly[m]["count"] for m in months_list]
            month_labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=month_labels, y=rev_list, name="Revenue", marker_color="rgba(192, 132, 252, 0.7)", yaxis="y"))
            fig.add_trace(go.Scatter(x=month_labels, y=count_list, name="Transactions", mode="lines+markers", marker=dict(color="#f472b6", size=8), line=dict(color="#f472b6", width=2), yaxis="y2"))
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified", legend=dict(orientation="h", y=1.1),
                yaxis=dict(title="Revenue (₹)", gridcolor="rgba(255,255,255,0.05)"),
                yaxis2=dict(title="Count", overlaying="y", side="right", gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(l=40, r=40, t=40, b=40),
                font=dict(color="rgba(255,255,255,0.7)")
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card"><h3>🥇 Top Customers</h3>', unsafe_allow_html=True)
        top = cached_top_customers()
        if top:
            top_data = [{"Name": c.name, "Phone": c.phone, "Visits": c.total_visits, "Total Spent": f"₹{c.total_spent:,.0f}", "Last Visit": c.last_visit.strftime("%d %b %Y")} for c in top[:5]]
            st.dataframe(pd.DataFrame(top_data), hide_index=True, use_container_width=True, height=220)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="glass-card"><h3>🔄 Repeat Customers</h3>', unsafe_allow_html=True)
        repeat = cached_repeat_customers()
        if repeat:
            repeat_data = [{"Name": r["name"], "Phone": r["phone"], "Visits": r["visits"], "Total": f"₹{r['total_spent']:,.0f}", "Last": r["last_visit"]} for r in repeat[:8]]
            st.dataframe(pd.DataFrame(repeat_data), hide_index=True, use_container_width=True, height=250)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card"><h3>📊 Expenses by Category</h3>', unsafe_allow_html=True)
        exp_cats = cached_expense_categories()
        if exp_cats:
            fig = px.pie(
                names=list(exp_cats.keys()), values=list(exp_cats.values()),
                color_discrete_sequence=px.colors.sequential.Viridis,
                hole=0.4
            )
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=20, b=20),
                font=dict(color="rgba(255,255,255,0.7)")
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

def customers_page():
    render_header("Customer Management", "Add, view and manage customers")

    tab1, tab2, tab3 = st.tabs(["➕ New Transaction", "📋 All Customers", "🔄 Repeat Analysis"])

    with tab1:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            with st.form("customer_form"):
                name = st.text_input("Customer Name", placeholder="Full name")
                phone = st.text_input("Phone Number", placeholder="+91 9X XXX XXXX")
                amount = st.number_input("Amount Paid (₹)", min_value=0.0, step=50.0, format="%.2f")
                service = st.selectbox("Service", ["Haircut", "Hair Color", "Facial", "Manicure", "Pedicure", "Spa", "Beard Trim", "Shave", "Styling", "Treatment", "General"])
                payment = st.selectbox("Payment Method", ["Cash", "UPI", "Card", "Wallet"])
                submitted = st.form_submit_button("💾 Save Transaction", use_container_width=True, type="primary")
                if submitted:
                    if not name or not phone:
                        st.warning("Name and phone required")
                    elif amount <= 0:
                        st.warning("Amount must be positive")
                    elif not re.match(r'^[\d\+\-\s]{7,20}$', phone.strip()):
                        st.warning("Enter a valid phone number (7-20 digits, optional +, -, spaces)")
                    else:
                        try:
                            add_customer(name, phone, amount, service, payment)
                            st.success(f"✅ {name} - ₹{amount:,.2f} saved!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="glass-card"><h3>⚡ Recent Activity</h3>', unsafe_allow_html=True)
            recent = load_transactions(10)
            if recent:
                recent_data = []
                for t in recent:
                    recent_data.append({
                        "Name": t.customer.name if t.customer else "Unknown",
                        "Amount": f"₹{t.amount:,.0f}",
                        "Service": t.service,
                        "Time": t.timestamp.strftime("%H:%M %d/%m")
                    })
                st.dataframe(pd.DataFrame(recent_data), hide_index=True, use_container_width=True, height=280)
            st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        customers = load_customers()
        if customers:
            data = []
            for c in customers:
                data.append({
                    "ID": c.id,
                    "Name": c.name, "Phone": c.phone, "Visits": c.total_visits,
                    "Total Spent": f"₹{c.total_spent:,.0f}",
                    "First Visit": c.first_visit.strftime("%d %b %Y") if c.first_visit else "",
                    "Last Visit": c.last_visit.strftime("%d %b %Y %H:%M") if c.last_visit else ""
                })
            df = pd.DataFrame(data)
            st.dataframe(df, hide_index=True, use_container_width=True, height=350)
            st.caption(f"Total: {len(customers)} customers")

            if st.session_state.get("role") == "admin":
                st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
                st.markdown("<h4>✏️ Edit / Delete Customer</h4>", unsafe_allow_html=True)
                cust_map = {f"{c.id} - {c.name} ({c.phone})": c for c in customers}
                sel_cust_key = st.selectbox("Select Customer", list(cust_map.keys()), key="cust_edit")
                sel_cust = cust_map[sel_cust_key]
                with st.expander("Edit Customer Details"):
                    with st.form("edit_customer_form"):
                        e_name = st.text_input("Name", value=sel_cust.name)
                        e_phone = st.text_input("Phone", value=sel_cust.phone)
                        e_email = st.text_input("Email", value=sel_cust.email or "")
                        e_notes = st.text_area("Notes", value=sel_cust.notes or "", height=80)
                        if st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary"):
                            if update_customer(sel_cust.id, e_name, e_phone, e_email, e_notes):
                                st.success("Customer updated!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Update failed")
                if st.button("🗑️ Delete Customer", use_container_width=True, type="primary"):
                    if delete_customer(sel_cust.id):
                        st.success("Customer deleted!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Delete failed")
        else:
            st.info("No customers yet. Add your first transaction!")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="glass-card"><h3>🔄 Customer Repeat Analysis</h3>', unsafe_allow_html=True)
        repeat = cached_repeat_customers()
        if repeat:
            col1, col2 = st.columns([1, 2])
            with col1:
                total = get_dashboard_stats()["total_customers"]
                repeat_count = len(repeat)
                ratio = (repeat_count / total * 100) if total > 0 else 0
                st.markdown(f"""<div class="metric-card"><div class="icon">🔄</div><div class="value">{ratio:.1f}%</div><div class="label">Repeat Rate ({repeat_count}/{total})</div></div>""", unsafe_allow_html=True)
            with col2:
                repeat_data = [{"Name": r["name"], "Phone": r["phone"], "Visits": r["visits"], "Total": f"₹{r['total_spent']:,.0f}", "Last": r["last_visit"]} for r in repeat]
                st.dataframe(pd.DataFrame(repeat_data), hide_index=True, use_container_width=True, height=300)
        else:
            st.info("No repeat customers yet (2+ visits)")
        st.markdown('</div>', unsafe_allow_html=True)

def transactions_page():
    render_header("Transactions", "Complete transaction history")

    tab1, tab2 = st.tabs(["📋 All Transactions", "✏️ Edit / Delete"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            days_filter = st.selectbox("Period", ["Today", "This Week", "This Month", "All Time"], index=2)
        with col2:
            st.metric("Total Revenue", f"₹{get_dashboard_stats()['total_revenue']:,.0f}")

        txns = load_transactions(1000)
        if txns:
            data = []
            for t in txns:
                data.append({
                    "ID": t.id,
                    "Date": t.timestamp.strftime("%d %b %Y"),
                    "Time": t.timestamp.strftime("%H:%M"),
                    "Customer": t.customer.name if t.customer else "N/A",
                    "Service": t.service,
                    "Amount": f"₹{t.amount:,.2f}",
                    "Payment": t.payment_method
                })
            df = pd.DataFrame(data)
            st.dataframe(df, hide_index=True, use_container_width=True, height=500)
        else:
            st.info("No transactions recorded yet")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        if st.session_state.get("role") != "admin":
            st.info("Only admins can edit/delete transactions")
        else:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            txns_ed = load_transactions(200)
            if txns_ed:
                txn_map = {}
                for t in txns_ed:
                    c_name = t.customer.name if t.customer else "N/A"
                    txn_map[f"{t.id} - {c_name} - ₹{t.amount:,.0f} ({t.timestamp.strftime('%d %b %H:%M')})"] = t

                col1, col2 = st.columns([2, 1])
                with col1:
                    sel_txn_key = st.selectbox("Select Transaction", list(txn_map.keys()), key="txn_edit_sel")
                with col2:
                    with st.form("edit_txn_form"):
                        sel_txn = txn_map[sel_txn_key]
                        e_amount = st.number_input("Amount", value=sel_txn.amount, min_value=0.0, step=50.0, format="%.2f")
                        e_service = st.selectbox("Service", ["Haircut", "Hair Color", "Facial", "Manicure", "Pedicure", "Spa", "Beard Trim", "Shave", "Styling", "Treatment", "General"], index=["Haircut", "Hair Color", "Facial", "Manicure", "Pedicure", "Spa", "Beard Trim", "Shave", "Styling", "Treatment", "General"].index(sel_txn.service) if sel_txn.service in ["Haircut", "Hair Color", "Facial", "Manicure", "Pedicure", "Spa", "Beard Trim", "Shave", "Styling", "Treatment", "General"] else 0)
                        e_payment = st.selectbox("Payment", ["Cash", "UPI", "Card", "Wallet"], index=["Cash", "UPI", "Card", "Wallet"].index(sel_txn.payment_method) if sel_txn.payment_method in ["Cash", "UPI", "Card", "Wallet"] else 0)
                        if st.form_submit_button("💾 Update", use_container_width=True, type="primary"):
                            if update_transaction(sel_txn.id, e_amount, e_service, e_payment):
                                st.success("Transaction updated!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Update failed")

                st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
                if st.button("🗑️ Delete Selected Transaction", use_container_width=True, type="primary"):
                    if delete_transaction(txn_map[sel_txn_key].id):
                        st.success("Transaction deleted!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Delete failed")
            else:
                st.info("No transactions to edit")
            st.markdown('</div>', unsafe_allow_html=True)

def staff_page():
    render_header("Staff Management", "Manage your team and payroll")

    tab1, tab2 = st.tabs(["👨‍💼 Current Staff", "➕ Add Staff"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        staff = load_staff()
        if staff:
            data = []
            for s in staff:
                data.append({
                    "Name": s.name, "Role": s.role, "Phone": s.phone,
                    "Salary": f"₹{s.salary:,.0f}/mo",
                    "Commission": f"{s.commission_rate:.0f}%",
                    "Joined": s.joined_date.strftime("%d %b %Y") if s.joined_date else ""
                })
            total_salary = get_staff_salary_total()
            st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True, height=300)
            st.caption(f"Total Staff: {len(staff)} · Monthly Salary Budget: ₹{total_salary:,.0f}")
        else:
            st.info("No staff added yet")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("staff_form"):
            col1, col2 = st.columns(2)
            with col1:
                s_name = st.text_input("Staff Name", placeholder="Full name")
                s_role = st.selectbox("Role", ["Stylist", "Senior Stylist", "Colorist", "Nail Technician", "Spa Therapist", "Barber", "Receptionist", "Manager", "Assistant", "Trainee"])
                s_phone = st.text_input("Phone", placeholder="Phone number")
            with col2:
                s_salary = st.number_input("Monthly Salary (₹)", min_value=0.0, step=1000.0, format="%.2f")
                s_commission = st.number_input("Commission Rate (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.1f")
            s_submit = st.form_submit_button("➕ Add Staff Member", use_container_width=True, type="primary")
            if s_submit:
                if not s_name:
                    st.warning("Name is required")
                elif s_salary < 0:
                    st.warning("Salary cannot be negative")
                else:
                    if add_staff(s_name, s_role, s_phone, s_salary, s_commission):
                        st.success(f"✅ {s_name} added to staff!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Failed to add staff")
        st.markdown('</div>', unsafe_allow_html=True)

def expenses_page():
    render_header("Expense Tracking", "Monitor and manage business expenses")

    tab1, tab2 = st.tabs(["📦 All Expenses", "➕ Add Expense"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        expenses = load_expenses()
        if expenses:
            data = []
            for e in expenses:
                data.append({
                    "Date": e.date_incurred.strftime("%d %b %Y") if e.date_incurred else "",
                    "Category": e.category,
                    "Description": e.description[:50] + "..." if len(e.description or "") > 50 else (e.description or ""),
                    "Amount": f"₹{e.amount:,.2f}",
                    "Recurring": "🔄 Yes" if e.recurring else "No"
                })
            total_exp = sum(e.amount for e in expenses)
            st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True, height=350)
            st.caption(f"Total Expenses: ₹{total_exp:,.2f}")
        else:
            st.info("No expenses recorded")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            with col1:
                exp_cat = st.selectbox("Category", ["Rent", "Electricity", "Water", "Supplies", "Products", "Equipment", "Marketing", "Maintenance", "Salary", "Insurance", "Software", "Miscellaneous", "Other"])
                exp_desc = st.text_area("Description", placeholder="Brief description", height=80)
            with col2:
                exp_amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f")
                exp_date = st.date_input("Date", value=date.today())
                exp_recur = st.checkbox("Recurring monthly expense")
            exp_submit = st.form_submit_button("💸 Add Expense", use_container_width=True, type="primary")
            if exp_submit:
                if exp_amount <= 0:
                    st.warning("Amount must be positive")
                else:
                    if add_expense(exp_cat, exp_desc, exp_amount, exp_date, int(exp_recur)):
                        st.success(f"✅ {exp_cat} expense of ₹{exp_amount:,.2f} added!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Failed to add expense")
        st.markdown('</div>', unsafe_allow_html=True)

def analytics_page():
    render_header("AI Analytics", "Deep insights powered by DeepSeek V4 Flash Free")

    st.markdown('<div class="glass-card"><h3>📅 Date Range</h3>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        start_date = st.date_input("From", value=date.today() - timedelta(days=365), key="analytics_from")
    with col2:
        end_date = st.date_input("To", value=date.today(), key="analytics_to")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        preset = st.selectbox("Quick Filter", ["Last 30 Days", "Last 3 Months", "Last 6 Months", "Last Year", "All Time"], index=3)
        if preset == "Last 30 Days":
            start_date, end_date = date.today() - timedelta(days=30), date.today()
        elif preset == "Last 3 Months":
            start_date, end_date = date.today() - timedelta(days=90), date.today()
        elif preset == "Last 6 Months":
            start_date, end_date = date.today() - timedelta(days=180), date.today()
        elif preset == "Last Year":
            start_date, end_date = date.today() - timedelta(days=365), date.today()
    st.markdown('</div>', unsafe_allow_html=True)

    stats = get_dashboard_stats()
    monthly = get_monthly_revenue()
    repeat = get_repeat_customers()
    expenses = load_expenses()
    staff = load_staff()
    top_customers = get_top_customers(5)

    salary_total = get_staff_salary_total()
    total_expenses = sum(e.amount for e in expenses)
    net_profit = stats["total_revenue"] - total_expenses - salary_total

    repeat_ratio = len(repeat) / stats["total_customers"] * 100 if stats["total_customers"] > 0 else 0
    avg_txn = stats["total_revenue"] / stats["total_transactions"] if stats["total_transactions"] > 0 else 0

    customer_list = []
    for c in top_customers:
        customer_list.append({"name": c.name, "phone": c.phone, "total_visits": c.total_visits, "total_spent": c.total_spent})

    expense_by_cat = cached_expense_categories()

    data_summary = {
        "business_name": "Saloon Pro",
        "period": f"{datetime.now().strftime('%B %Y')}",
        "date_range": {"from": str(start_date), "to": str(end_date)},
        "revenue": {
            "total": stats["total_revenue"],
            "this_month": stats["month_revenue"],
            "today": stats["today_revenue"],
            "monthly_breakdown": monthly
        },
        "customers": {
            "total": stats["total_customers"],
            "repeat_customers": len(repeat),
            "repeat_rate": round(repeat_ratio, 1),
            "top_customers": customer_list
        },
        "transactions": {
            "total": stats["total_transactions"],
            "average_value": round(avg_txn, 2)
        },
        "staff": {
            "count": len(staff),
            "total_salaries": salary_total
        },
        "expenses": {
            "total": total_expenses,
            "by_category": expense_by_cat
        },
        "profit_analysis": {
            "gross_revenue": stats["total_revenue"],
            "total_expenses": total_expenses,
            "staff_salaries": salary_total,
            "net_profit": net_profit,
            "profit_margin": round((net_profit / stats["total_revenue"] * 100), 1) if stats["total_revenue"] > 0 else 0
        }
    }

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="icon">📈</div><div class="value" style="color: {'#4ade80' if net_profit >= 0 else '#f87171'}">₹{net_profit:,.0f}</div><div class="label">Net Profit</div></div>""", unsafe_allow_html=True)
    with col2:
        margin = (net_profit / stats["total_revenue"] * 100) if stats["total_revenue"] > 0 else 0
        st.markdown(f"""<div class="metric-card"><div class="icon">🎯</div><div class="value">{margin:.1f}%</div><div class="label">Profit Margin</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="icon">🔄</div><div class="value">{repeat_ratio:.1f}%</div><div class="label">Repeat Rate</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class="metric-card"><div class="icon">💳</div><div class="value">₹{avg_txn:,.0f}</div><div class="label">Avg Transaction</div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="glass-card"><h3>📊 Revenue vs Expenses</h3>', unsafe_allow_html=True)
        monthly_data = {k: v["revenue"] for k, v in monthly.items()} if monthly else {}
        if monthly_data:
            months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            rev_vals = [monthly_data.get(f"{i:02d}", 0) for i in range(1, 13)]
            exp_vals = []
            for i in range(1, 13):
                m_key = f"{start_date.year}-{i:02d}"
                exp_vals.append(sum(e.amount for e in expenses if e.date_incurred and e.date_incurred.strftime("%Y-%m") == m_key) if start_date.year == datetime.now().year else 0)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=months, y=rev_vals, name="Revenue", marker_color="rgba(192, 132, 252, 0.7)"))
            fig.add_trace(go.Bar(x=months, y=exp_vals, name="Expenses", marker_color="rgba(248, 113, 113, 0.5)"))
            fig.update_layout(barmode="group", template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=20, b=40), font=dict(color="rgba(255,255,255,0.7)"))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card"><h3>🔮 Revenue Forecast</h3>', unsafe_allow_html=True)
        monthly_data = {k: v["revenue"] for k, v in monthly.items()} if monthly else {}
        if monthly_data:
            fig = go.Figure()
            months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
            vals = [monthly_data.get(f"{i:02d}", 0) for i in range(1, 13)]
            fig.add_trace(go.Scatter(x=months, y=vals, mode="lines+markers", name="Actual", line=dict(color="#c084fc", width=3), marker=dict(size=10, color="#c084fc")))
            prediction = get_revenue_prediction({k: monthly_data[k] for k in sorted(monthly_data.keys())[-3:]})
            if prediction:
                fig.add_trace(go.Scatter(x=["Next"], y=[prediction["prediction"]], mode="markers", name=f'Forecast ({prediction["trend"]})', marker=dict(size=15, color="#fbbf24", symbol="diamond")))
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=20, b=40), font=dict(color="rgba(255,255,255,0.7)"))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="glass-card"><h3>🤖 AI Business Analysis</h3>', unsafe_allow_html=True)

    with st.spinner("🧠 AI is analyzing your salon data..."):
        analysis = analyze_dashboard_data(data_summary)

    st.markdown(f'<div class="chat-message">{analysis}</div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="glass-card"><h3>💡 AI Recommendations</h3>', unsafe_allow_html=True)
        recommendations = []
        if repeat_ratio < 30:
            recommendations.append("🔸 Launch a loyalty program to boost repeat visits")
        if avg_txn < 500:
            recommendations.append("🔹 Bundle services to increase average transaction value")
        if total_expenses > stats["total_revenue"] * 0.6:
            recommendations.append("🔸 Expense ratio is high — review non-essential costs")
        if len(staff) < 2:
            recommendations.append("🔹 Consider hiring additional stylists for peak hours")
        if stats["total_customers"] < 20:
            recommendations.append("🔸 Run local ads & referral campaigns to acquire customers")
        if not recommendations:
            recommendations.append("✅ Your salon is performing well! Keep maintaining standards.")
            recommendations.append("💎 Consider premium service packages for higher margins")

        for rec in recommendations:
            st.markdown(f'<div style="padding: 0.5rem 0; color: rgba(255,255,255,0.8);">{rec}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="glass-card"><h3>📈 Trend Comparison</h3>', unsafe_allow_html=True)
        daily = get_daily_revenue(60)
        if daily:
            fig = go.Figure()
            dates = [r.date_only for r in daily]
            revs = [float(r.revenue or 0) for r in daily]
            counts = [r.count for r in daily]
            fig.add_trace(go.Scatter(x=dates, y=revs, mode="lines", name="Daily Revenue", line=dict(color="#c084fc", width=2), yaxis="y"))
            fig.add_trace(go.Scatter(x=dates, y=counts, mode="lines", name="Transactions", line=dict(color="#f472b6", width=2), yaxis="y2"))
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=20, b=40), font=dict(color="rgba(255,255,255,0.7)"), yaxis=dict(gridcolor="rgba(255,255,255,0.05)"), yaxis2=dict(overlaying="y", side="right", gridcolor="rgba(255,255,255,0.05)"))
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

def appointments_page():
    render_header("Appointments", "Schedule and manage customer bookings")

    today = date.today()

    tab1, tab2, tab3 = st.tabs(["📅 Calendar View", "➕ New Appointment", "📊 Overview"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            view_date = st.date_input("Date", value=today, key="apt_date")
        with col2:
            view_status = st.selectbox("Status", ["all", "scheduled", "confirmed", "completed", "cancelled"], key="apt_status")
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            apt_stats = get_appointment_stats()
            st.markdown(f"""<div style="display:flex;gap:1rem;color:rgba(255,255,255,0.6);font-size:0.85rem;">
                📅 Today: <b>{apt_stats['today']}</b> &nbsp;|&nbsp;
                ✅ Completed: <b>{apt_stats['completed']}</b> &nbsp;|&nbsp;
                🔜 Upcoming: <b>{apt_stats['upcoming']}</b>
            </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

        appointments = load_appointments(view_date)
        if view_status != "all":
            appointments = [a for a in appointments if a.status == view_status]

        if appointments:
            apt_data = []
            for a in appointments:
                c_name = a.customer.name if a.customer else "Unknown"
                s_name = a.staff.name if a.staff else "Unassigned"
                status_emoji = {"scheduled": "🟡", "confirmed": "🟢", "completed": "✅", "cancelled": "❌", "no-show": "🚫"}
                apt_data.append({
                    "Time": a.appointment_time,
                    "Customer": c_name,
                    "Service": a.service,
                    "Staff": s_name,
                    "Duration": f"{a.duration_minutes}m",
                    "Status": f"{status_emoji.get(a.status, '🟡')} {a.status.title()}",
                    "Notes": a.notes or ""
                })
            st.dataframe(pd.DataFrame(apt_data), hide_index=True, use_container_width=True, height=300)
        else:
            st.info("No appointments for this date")

        st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        st.markdown("<h4>✏️ Update Status</h4>", unsafe_allow_html=True)
        all_apts = load_appointments(view_date)
        if all_apts:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                apt_choices = {f"{a.appointment_time} - {a.customer.name if a.customer else '?'} ({a.service})": a.id for a in all_apts}
                sel_apt = st.selectbox("Select Appointment", list(apt_choices.keys()), key="apt_status_update")
            with col2:
                new_status = st.selectbox("New Status", ["confirmed", "completed", "cancelled", "no-show", "scheduled"], key="apt_new_status")
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Update", use_container_width=True, type="primary"):
                    if update_appointment_status(apt_choices[sel_apt], new_status):
                        st.success(f"Appointment → {new_status}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Update failed")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        customers = load_customers()
        staff_list = load_staff()

        customer_choices = {}
        for c in customers:
            label = f"{c.name} ({c.phone})" if c.phone else c.name
            customer_choices[label] = c.id

        staff_choices = {"None (Walk-in)": None}
        for s in staff_list:
            staff_choices[f"{s.name} ({s.role})"] = s.id

        with st.form("appointment_form"):
            col1, col2 = st.columns(2)
            with col1:
                apt_cust = st.selectbox("Customer", list(customer_choices.keys()) if customer_choices else ["No customers"], key="apt_cust")
                apt_service = st.selectbox("Service", ["Haircut", "Hair Color", "Facial", "Manicure", "Pedicure", "Spa", "Beard Trim", "Shave", "Styling", "Treatment", "General"])
                apt_date_pick = st.date_input("Date", value=today + timedelta(days=1), key="apt_new_date")
                apt_notes = st.text_area("Notes", placeholder="Optional notes", height=80)
            with col2:
                apt_staff = st.selectbox("Staff Member", list(staff_choices.keys()) if staff_choices else ["No staff"], key="apt_staff")
                apt_time = st.selectbox("Time", TIME_SLOTS, key="apt_time")
                apt_duration = st.selectbox("Duration", [15, 30, 45, 60, 90, 120], index=1, format_func=lambda x: f"{x} min")
                apt_status_init = st.selectbox("Status", ["scheduled", "confirmed"], key="apt_init_status")

            if st.form_submit_button("📅 Book Appointment", use_container_width=True, type="primary"):
                if not customer_choices:
                    st.warning("No customers available. Add a customer first.")
                else:
                    cid = customer_choices[apt_cust]
                    sid = staff_choices[apt_staff]
                    success, err = add_appointment(cid, sid, apt_service, apt_date_pick, apt_time, apt_duration, apt_notes)
                    if success:
                        st.success(f"✅ Appointment booked for {apt_cust} on {apt_date_pick} at {apt_time}")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Booking failed: {err or 'Time slot conflict'}")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<h4>📊 Weekly Overview</h4>", unsafe_allow_html=True)
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_apts = get_appointments_by_date_range(week_start, week_end)
        if week_apts:
            daily_counts = {}
            for a in week_apts:
                d = a.appointment_date.strftime("%a %d %b")
                daily_counts[d] = daily_counts.get(d, 0) + 1
            days_of_week = [(week_start + timedelta(days=i)).strftime("%a %d %b") for i in range(7)]
            counts = [daily_counts.get(d, 0) for d in days_of_week]
            fig = go.Figure()
            fig.add_trace(go.Bar(x=days_of_week, y=counts, marker_color="rgba(192,132,252,0.7)"))
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=20, b=40), font=dict(color="rgba(255,255,255,0.7)"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No appointments this week")
        st.markdown('</div>', unsafe_allow_html=True)

def invoices_page():
    render_header("Invoices", "View and print customer invoices")

    tab1, tab2 = st.tabs(["📄 All Invoices", "➕ Generate Invoice"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        invoices = load_invoices()
        if invoices:
            inv_data = []
            for inv in invoices:
                c_name = inv.customer.name if inv.customer else "Unknown"
                inv_data.append({
                    "Invoice #": inv.invoice_number,
                    "Customer": c_name,
                    "Amount": f"₹{inv.amount:,.2f}",
                    "Tax": f"₹{inv.tax:,.2f}",
                    "Discount": f"₹{inv.discount:,.2f}",
                    "Total": f"₹{inv.total:,.2f}",
                    "Date": inv.created_at.strftime("%d %b %Y %H:%M"),
                    "Status": "✅ Paid" if inv.status == "paid" else "⏳ Pending"
                })
            df = pd.DataFrame(inv_data)
            st.dataframe(df, hide_index=True, use_container_width=True, height=350)

            st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            sel_inv = st.selectbox("Select Invoice for Details", [f"{i.invoice_number} - {i.customer.name if i.customer else '?'}" for i in invoices])
            selected = next((i for i in invoices if f"{i.invoice_number} - {i.customer.name if i.customer else '?'}" == sel_inv), None)
            if selected:
                c = selected.customer
                inv_html = f"""
                <div style="background:white;color:#1a1a2e;padding:2rem;border-radius:12px;max-width:600px;margin:1rem auto;font-family:'Inter',sans-serif;">
                    <div style="text-align:center;border-bottom:2px dashed #eee;padding-bottom:1rem;margin-bottom:1rem;">
                        <div style="font-size:2rem;">💈</div>
                        <h2 style="margin:0;font-weight:800;">SALOON PRO</h2>
                        <p style="color:#666;font-size:0.85rem;">Premium Salon Services</p>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:1rem;">
                        <div>
                            <strong>Invoice:</strong> {selected.invoice_number}<br>
                            <strong>Date:</strong> {selected.created_at.strftime('%d %b %Y %H:%M')}
                        </div>
                        <div style="text-align:right;">
                            <strong>Customer:</strong> {c.name if c else 'N/A'}<br>
                            <strong>Phone:</strong> {c.phone if c else ''}
                        </div>
                    </div>
                    <table style="width:100%;border-collapse:collapse;margin:1rem 0;">
                        <tr style="background:#f5f5f5;"><th style="padding:0.5rem;text-align:left;">Description</th><th style="padding:0.5rem;text-align:right;">Amount</th></tr>
                        <tr><td style="padding:0.5rem;">Salon Services</td><td style="padding:0.5rem;text-align:right;">₹{selected.amount:,.2f}</td></tr>
                        <tr><td style="padding:0.5rem;">Tax</td><td style="padding:0.5rem;text-align:right;">₹{selected.tax:,.2f}</td></tr>
                        <tr><td style="padding:0.5rem;">Discount</td><td style="padding:0.5rem;text-align:right;">-₹{selected.discount:,.2f}</td></tr>
                        <tr style="font-weight:800;border-top:2px solid #333;"><td style="padding:0.5rem;">TOTAL</td><td style="padding:0.5rem;text-align:right;">₹{selected.total:,.2f}</td></tr>
                    </table>
                    <div style="text-align:center;color:#666;font-size:0.75rem;border-top:2px dashed #eee;padding-top:1rem;">
                        Thank you for your visit! 💈
                    </div>
                </div>
                """
                st.markdown(inv_html, unsafe_allow_html=True)
                st.download_button("📥 Download Invoice HTML", inv_html.encode("utf-8"), f"{selected.invoice_number}.html", "text/html", use_container_width=True)
        else:
            st.info("No invoices generated yet")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        txns = load_transactions(100)
        if txns:
            txn_choices = {}
            for t in txns:
                c_name = t.customer.name if t.customer else "Unknown"
                txn_choices[f"{c_name} - ₹{t.amount:,.2f} ({t.service}) [{t.timestamp.strftime('%d %b')}]"] = t
            sel_txn_label = st.selectbox("Select Transaction", list(txn_choices.keys()), key="inv_txn")
            sel_txn = txn_choices[sel_txn_label]
            if sel_txn:
                col1, col2, col3 = st.columns(3)
                with col1:
                    tax_pct = st.number_input("Tax %", min_value=0.0, max_value=50.0, value=0.0, step=1.0, format="%.1f")
                with col2:
                    discount = st.number_input("Discount (₹)", min_value=0.0, value=0.0, step=50.0, format="%.2f")
                with col3:
                    st.markdown("<br>", unsafe_allow_html=True)
                    total = sel_txn.amount + (sel_txn.amount * tax_pct / 100) - discount
                    st.metric("Total", f"₹{total:,.2f}")

                if st.button("🧾 Generate Invoice", use_container_width=True, type="primary"):
                    inv = create_invoice(sel_txn.id, sel_txn.customer_id, sel_txn.amount, tax_pct, discount)
                    if inv:
                        st.success(f"✅ Invoice {inv.invoice_number} generated!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Failed to generate invoice")
        else:
            st.info("No transactions available. Add a transaction first.")
        st.markdown('</div>', unsafe_allow_html=True)

def inventory_page():
    render_header("Inventory Management", "Track products, supplies and stock levels")

    tab1, tab2, tab3 = st.tabs(["📋 All Items", "➕ Add Item", "🏭 Suppliers"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        inv_stats = get_inventory_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""<div class="metric-card"><div class="icon">📦</div><div class="value">{inv_stats['total_items']}</div><div class="label">Total Items</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="metric-card"><div class="icon">⚠️</div><div class="value" style="color: {'#f87171' if inv_stats['low_stock'] > 0 else '#4ade80'}">{inv_stats['low_stock']}</div><div class="label">Low Stock Alert</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="metric-card"><div class="icon">💰</div><div class="value">₹{inv_stats['total_value']:,.0f}</div><div class="label">Inventory Value</div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        items = load_inventory()
        if items:
            item_data = []
            for item in items:
                status = "✅" if item.quantity > item.min_stock_level else "⚠️ Low"
                supplier_name = item.supplier.name if item.supplier else "-"
                item_data.append({
                    "Name": item.name, "Category": item.category,
                    "Stock": f"{item.quantity:.0f} {item.unit}",
                    "Min Level": f"{item.min_stock_level:.0f}",
                    "Unit Price": f"₹{item.unit_price:,.2f}",
                    "Value": f"₹{item.quantity * item.unit_price:,.2f}",
                    "Supplier": supplier_name, "Status": status
                })
            df = pd.DataFrame(item_data)
            st.dataframe(df, hide_index=True, use_container_width=True, height=350)

            st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            st.markdown("<h4>✏️ Update Stock Quantity</h4>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                item_names = {f"{i.name} ({i.quantity} {i.unit})": i.id for i in items}
                selected_item = st.selectbox("Select Item", list(item_names.keys()), key="stock_update_item")
            with col2:
                new_qty = st.number_input("New Quantity", min_value=0.0, step=1.0, format="%.0f", key="stock_update_qty")
            with col3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Update", use_container_width=True, type="primary"):
                    if update_inventory_quantity(item_names[selected_item], new_qty):
                        st.success("Stock updated!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Update failed")
        else:
            st.info("No inventory items. Add your first item!")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        suppliers = load_suppliers()
        supplier_choices = {"None (No Supplier)": None}
        for s in suppliers:
            supplier_choices[s.name] = s.id

        with st.form("inventory_form"):
            col1, col2 = st.columns(2)
            with col1:
                inv_name = st.text_input("Item Name", placeholder="Shampoo, Scissors, Towels...")
                inv_category = st.selectbox("Category", ["Hair Products", "Skincare", "Nail Products", "Tools", "Equipment", "Towels & Linens", "Cleaning", "Stationery", "Uniforms", "General"])
                inv_quantity = st.number_input("Quantity", min_value=0.0, step=1.0, format="%.1f")
                inv_unit = st.text_input("Unit", value="pcs", placeholder="pcs, bottles, ml, packs")
            with col2:
                inv_min = st.number_input("Min Stock Level", min_value=0.0, value=5.0, step=1.0, format="%.0f")
                inv_price = st.number_input("Unit Price (₹)", min_value=0.0, step=50.0, format="%.2f")
                inv_supplier = st.selectbox("Supplier", list(supplier_choices.keys()))
                inv_notes = st.text_area("Notes", placeholder="Optional notes", height=80)

            if st.form_submit_button("➕ Add Inventory Item", use_container_width=True, type="primary"):
                if not inv_name:
                    st.warning("Item name is required")
                else:
                    if add_inventory_item(inv_name, inv_category, inv_quantity, inv_unit, inv_min, inv_price, supplier_choices[inv_supplier], inv_notes):
                        st.success(f"✅ {inv_name} added to inventory!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Failed to add item")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        supps = load_suppliers()
        if supps:
            supp_data = []
            for s in supps:
                supp_data.append({"Name": s.name, "Contact": s.contact_person, "Phone": s.phone, "Email": s.email})
            st.dataframe(pd.DataFrame(supp_data), hide_index=True, use_container_width=True, height=200)
        else:
            st.info("No suppliers yet")

        st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        st.markdown("<h4>➕ New Supplier</h4>", unsafe_allow_html=True)
        with st.form("supplier_form"):
            col1, col2 = st.columns(2)
            with col1:
                sup_name = st.text_input("Company Name", placeholder="Supplier name")
                sup_contact = st.text_input("Contact Person")
                sup_phone = st.text_input("Phone")
            with col2:
                sup_email = st.text_input("Email")
                sup_address = st.text_area("Address", height=60)
                sup_notes = st.text_area("Notes", height=60)
            if st.form_submit_button("💾 Save Supplier", use_container_width=True, type="primary"):
                if not sup_name:
                    st.warning("Supplier name is required")
                else:
                    if add_supplier(sup_name, sup_contact, sup_phone, sup_email, sup_address, sup_notes):
                        st.success(f"✅ {sup_name} added!")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error("Failed to add supplier")
        st.markdown('</div>', unsafe_allow_html=True)

def reports_page():
    render_header("Reports & Exports", "Download data and generate professional PDF reports")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Transactions", "👥 Customers", "💰 Financial Summary", "📄 Export All"])

    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        txns = load_transactions(5000)
        if txns:
            data = []
            for t in txns:
                data.append({
                    "Date": t.timestamp.strftime("%d-%b-%Y"),
                    "Time": t.timestamp.strftime("%H:%M"),
                    "Customer": t.customer.name if t.customer else "N/A",
                    "Service": t.service,
                    "Amount": t.amount,
                    "Payment": t.payment_method
                })
            df = pd.DataFrame(data)
            st.dataframe(df, hide_index=True, use_container_width=True, height=350)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, f"transactions_{date.today()}.csv", "text/csv", use_container_width=True, type="primary")
        else:
            st.info("No transactions data")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        custs = load_customers()
        if custs:
            data = []
            for c in custs:
                data.append({
                    "Name": c.name, "Phone": c.phone,
                    "Visits": c.total_visits, "Total Spent": c.total_spent,
                    "First Visit": c.first_visit.strftime("%d-%b-%Y") if c.first_visit else "",
                    "Last Visit": c.last_visit.strftime("%d-%b-%Y") if c.last_visit else ""
                })
            df = pd.DataFrame(data)
            st.dataframe(df, hide_index=True, use_container_width=True, height=350)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, f"customers_{date.today()}.csv", "text/csv", use_container_width=True, type="primary")
        else:
            st.info("No customer data")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        stats = get_dashboard_stats()
        monthly = get_monthly_revenue()
        expenses = load_expenses()
        salary_total = get_staff_salary_total()
        total_exp = sum(e.amount for e in expenses)
        net_profit = stats["total_revenue"] - total_exp - salary_total

        report_lines = [
            f"📈 Financial Summary Report",
            f"Generated: {datetime.now().strftime('%d %B %Y %H:%M')}",
            "",
            f"─── REVENUE ───",
            f"  Total Revenue:      ₹{stats['total_revenue']:>10,.0f}",
            f"  This Month:         ₹{stats['month_revenue']:>10,.0f}",
            f"  Today:              ₹{stats['today_revenue']:>10,.0f}",
            f"  Avg Transaction:    ₹{stats['total_revenue'] / max(stats['total_transactions'], 1):>10,.0f}",
            "",
            f"─── EXPENSES ───",
            f"  Total Expenses:     ₹{total_exp:>10,.0f}",
            f"  Staff Salaries:     ₹{salary_total:>10,.0f}/mo",
            "",
            f"─── PROFIT ───",
            f"  Net Profit:         ₹{net_profit:>10,.0f}",
            f"  Profit Margin:      {(net_profit / stats['total_revenue'] * 100):>9.1f}%" if stats["total_revenue"] > 0 else "  Profit Margin:       N/A",
            "",
            f"─── CUSTOMERS ───",
            f"  Total Customers:    {stats['total_customers']:>10}",
            f"  Total Transactions: {stats['total_transactions']:>10}",
            f"  Total Staff:        {stats['total_staff']:>10}",
        ]
        report = "\n".join(report_lines)
        st.text(report)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download Report (.txt)", report.encode("utf-8"), f"financial_report_{date.today()}.txt", "text/plain", use_container_width=True, type="primary")
        with col2:
            with st.spinner("Generating PDF..."):
                pdf_buf = generate_financial_pdf()
            st.download_button("📄 Download PDF Report", pdf_buf.read(), f"financial_report_{date.today()}.pdf", "application/pdf", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<h4>📦 Bulk Export</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: rgba(255,255,255,0.5);'>Download all data as a single CSV package.</p>", unsafe_allow_html=True)

        txns = load_transactions(5000)
        custs = load_customers()
        stff = load_staff()
        exps = load_expenses()

        if txns:
            tdf = pd.DataFrame([{"Date": t.timestamp.strftime("%d-%b-%Y"), "Time": t.timestamp.strftime("%H:%M"), "Customer": t.customer.name if t.customer else "", "Service": t.service, "Amount": t.amount, "Payment": t.payment_method} for t in txns])
        else:
            tdf = pd.DataFrame()

        if custs:
            cdf = pd.DataFrame([{"Name": c.name, "Phone": c.phone, "Visits": c.total_visits, "Total Spent": c.total_spent} for c in custs])
        else:
            cdf = pd.DataFrame()

        if stff:
            sdf = pd.DataFrame([{"Name": s.name, "Role": s.role, "Salary": s.salary, "Commission": f"{s.commission_rate}%"} for s in stff])
        else:
            sdf = pd.DataFrame()

        if exps:
            edf = pd.DataFrame([{"Date": e.date_incurred.strftime("%d-%b-%Y"), "Category": e.category, "Description": e.description, "Amount": e.amount, "Recurring": "Yes" if e.recurring else "No"} for e in exps])
        else:
            edf = pd.DataFrame()

        combined_csv = ""
        if not tdf.empty:
            combined_csv += "TRANSACTIONS\n" + tdf.to_csv(index=False) + "\n\n"
        if not cdf.empty:
            combined_csv += "CUSTOMERS\n" + cdf.to_csv(index=False) + "\n\n"
        if not sdf.empty:
            combined_csv += "STAFF\n" + sdf.to_csv(index=False) + "\n\n"
        if not edf.empty:
            combined_csv += "EXPENSES\n" + edf.to_csv(index=False)

        if combined_csv:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Download All Data (.csv)", combined_csv.encode("utf-8"), f"saloon_full_export_{date.today()}.csv", "text/csv", use_container_width=True, type="primary")
            with col2:
                with st.spinner("Generating complete PDF report..."):
                    pdf_buf = generate_full_report_pdf()
                st.download_button("📄 Download Complete PDF Report", pdf_buf.read(), f"saloon_full_report_{date.today()}.pdf", "application/pdf", use_container_width=True, type="primary")
        else:
            st.info("No data to export")
        st.markdown('</div>', unsafe_allow_html=True)

def settings_page():
    render_header("Settings", "Configure your salon system")

    role = st.session_state.get("role", "staff")
    tabs = ["👤 Profile", "🔐 Security"]
    if role == "admin":
        tabs += ["🔑 API Key", "💾 Backup & Restore"]
    tabs.append("ℹ️ About")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(tabs + (["_"] * (5 - len(tabs))))

    with tab1 if len(tabs) >= 1 else st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown(f"<h3>Welcome, {st.session_state['username']} 👋</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: rgba(255,255,255,0.5);'>Role: <span style='color: #fbbf24; text-transform: capitalize;'>{role}</span> · Logged in since this session</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

        if st.button("🚪 Sign Out", use_container_width=True):
            for key in ["authenticated", "username", "role"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.cache_data.clear()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2 if len(tabs) >= 2 else st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        with st.form("password_form"):
            new_pass = st.text_input("New Password", type="password", placeholder="Enter new password")
            confirm = st.text_input("Confirm Password", type="password", placeholder="Confirm new password")
            if st.form_submit_button("🔄 Update Password", use_container_width=True, type="primary"):
                if not new_pass:
                    st.warning("Password cannot be empty")
                elif new_pass != confirm:
                    st.warning("Passwords do not match")
                elif len(new_pass) < 4:
                    st.warning("Minimum 4 characters")
                else:
                    if change_password(st.session_state["username"], new_pass):
                        st.success("✅ Password updated successfully!")
                    else:
                        st.error("Failed to update password")
        st.markdown('</div>', unsafe_allow_html=True)

        if role == "admin":
            st.markdown('<div class="glass-card" style="margin-top: 1rem;">', unsafe_allow_html=True)
            with st.form("new_user_form"):
                st.markdown("<h3>Add New User</h3>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    nu = st.text_input("Username")
                    np = st.text_input("Password", type="password")
                with col2:
                    nr = st.selectbox("Role", ["admin", "staff", "receptionist"])
                if st.form_submit_button("➕ Create User", use_container_width=True):
                    if nu and np and len(np) >= 4:
                        from auth import create_user as _create_user
                        if _create_user(nu, np, nr):
                            st.success(f"✅ User {nu} ({nr}) created!")
                        else:
                            st.error("Username already exists")
                    else:
                        st.warning("Invalid username or password too short")
            st.markdown('</div>', unsafe_allow_html=True)

    if role == "admin":
        with tab3:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<h3>🔑 OpenCode Zen API Configuration</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: rgba(255,255,255,0.5);'>Enter your OpenCode Zen API key to enable AI analytics powered by DeepSeek V4 Flash Free.</p>", unsafe_allow_html=True)
            st.markdown("<p style='color: rgba(255,255,255,0.4); font-size: 0.85rem;'>Set via Streamlit secrets: <code>[opencode]\napi_key = \"your-key-here\"</code> or enter below.</p>", unsafe_allow_html=True)

            current_key = get_api_key()
            masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else ""
            if current_key:
                st.markdown(f"<p style='color: #4ade80;'>✅ Configured: <code>{masked}</code></p>", unsafe_allow_html=True)
            else:
                st.markdown("<p style='color: #f87171;'>⚠️ Not configured — AI features will be unavailable.</p>", unsafe_allow_html=True)

            st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            with st.form("api_key_form"):
                new_key = st.text_input("OpenCode Zen API Key", type="password", placeholder="sk-... or opencode-zen-api-...", value=current_key if current_key else "")
                if st.form_submit_button("💾 Save API Key", use_container_width=True, type="primary"):
                    if new_key:
                        set_api_key_in_db(new_key)
                        st.success("✅ API key saved! AI features are now active.")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.warning("Please enter a valid API key")
                if current_key and st.form_submit_button("🗑️ Clear API Key", use_container_width=True):
                    set_api_key_in_db("")
                    st.success("API key cleared")
                    st.cache_data.clear()
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        with tab4:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("<h3>💾 Backup & Restore</h3>", unsafe_allow_html=True)
            st.markdown("<p style='color: rgba(255,255,255,0.5);'>Create backups of your salon data and restore from previous backups.</p>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📀 Create Backup Now", use_container_width=True, type="primary"):
                    try:
                        fname = backup_database()
                        st.success(f"✅ Backup created: {fname}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Backup failed: {e}")
            with col2:
                st.info("Backups stored in data/backups/")

            st.markdown("<hr style='border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            st.markdown("<h4>📋 Available Backups</h4>", unsafe_allow_html=True)
            backups = list_backups()
            if backups:
                bdf = pd.DataFrame(backups)
                st.dataframe(bdf, hide_index=True, use_container_width=True, height=200)

                sel_backup = st.selectbox("Select backup to restore", [b["file"] for b in backups], key="restore_backup")
                if st.button("⚠️ Restore Selected Backup", use_container_width=True):
                    try:
                        restore_database(sel_backup)
                        st.success(f"✅ Restored from {sel_backup}. Reloading...")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Restore failed: {e}")
            else:
                st.info("No backups yet")

            st.markdown('</div>', unsafe_allow_html=True)

    with tab5 if len(tabs) == 5 else (tab4 if len(tabs) == 4 else st.container()):
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        db_type = "PostgreSQL" if "postgresql" in str(os.environ.get("DATABASE_URL", "")).lower() else "SQLite"
        st.markdown(f"""
        <h3>💈 Saloon Pro v3.0</h3>
        <p style='color: rgba(255,255,255,0.5);'>Premium Salon Management System</p>
        <ul style='color: rgba(255,255,255,0.7); line-height: 2;'>
            <li>🚀 Powered by DeepSeek V4 Flash Free AI</li>
            <li>🗄️ Database: {db_type}</li>
            <li>🔒 Secure authentication with bcrypt</li>
            <li>📊 Real-time analytics & forecasting</li>
            <li>💈 Built for modern salons in 2026</li>
        </ul>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def more_page():
    role = st.session_state.get("role", "staff")
    render_header("More", "All features")
    allowed = ["staff", "expenses", "inventory", "reports", "analytics", "invoices"]
    more_items = [(icon, label, key) for icon, label, key in [
        ("👨‍💼", "Staff", "staff"), ("📦", "Expenses", "expenses"), ("📦", "Stock", "inventory"),
        ("📄", "Reports", "reports"), ("📊", "AI Analytics", "analytics"), ("🧾", "Invoices", "invoices"),
        ("⚙️", "Settings", "settings"),
    ] if role == "admin" or key not in ["staff", "expenses", "inventory", "reports", "analytics", "invoices"]]

    html = '<div class="more-grid">'
    for icon, label, key in more_items:
        html += f'<button class="more-item" onclick="window.location.href=\'?page={key}\'" type="button"><span class="mi-icon">{icon}</span><span class="mi-label">{label}</span></button>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def gather_salon_context():
    """Gather full salon data context for AI chat."""
    stats = get_dashboard_stats()
    monthly = get_monthly_revenue()
    repeat = get_repeat_customers()
    expenses = load_expenses()
    staff = load_staff()
    top_customers = get_top_customers(5)
    salary_total = get_staff_salary_total()
    total_expenses = sum(e.amount for e in expenses)
    net_profit = stats["total_revenue"] - total_expenses - salary_total
    repeat_ratio = len(repeat) / stats["total_customers"] * 100 if stats["total_customers"] > 0 else 0
    avg_txn = stats["total_revenue"] / stats["total_transactions"] if stats["total_transactions"] > 0 else 0
    customer_list = [{"name": c.name, "phone": c.phone, "total_visits": c.total_visits, "total_spent": c.total_spent} for c in top_customers]
    expense_by_cat = cached_expense_categories()
    appointments_today = get_appointment_stats()
    return {
        "business_name": "Saloon Pro",
        "report_date": datetime.now().strftime("%d %B %Y %H:%M"),
        "revenue": {
            "total": stats["total_revenue"], "this_month": stats["month_revenue"],
            "today": stats["today_revenue"], "monthly_breakdown": monthly
        },
        "customers": {
            "total": stats["total_customers"], "repeat_customers": len(repeat),
            "repeat_rate_pct": round(repeat_ratio, 1), "top_customers": customer_list
        },
        "transactions": {"total": stats["total_transactions"], "average_value_rs": round(avg_txn, 2)},
        "staff": {"count": len(staff), "total_salaries_rs": salary_total},
        "expenses": {"total_rs": total_expenses, "by_category": expense_by_cat},
        "profit": {
            "gross_revenue_rs": stats["total_revenue"], "total_expenses_rs": total_expenses,
            "staff_salaries_rs": salary_total, "net_profit_rs": net_profit,
            "profit_margin_pct": round((net_profit / stats["total_revenue"] * 100), 1) if stats["total_revenue"] > 0 else 0
        },
        "appointments": {"today": appointments_today['today'], "completed": appointments_today['completed'], "upcoming": appointments_today['upcoming']}
    }

def ai_chat_page():
    render_header("AI Assistant", "Chat with your salon business data")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "context_cached" not in st.session_state:
        st.session_state.context_cached = None

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<h3>🧠 SaloonAI — Your Business Intelligence Agent</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: rgba(255,255,255,0.5); font-size:0.8rem;'>Ask anything about your revenue, customers, expenses, staff, appointments, and more.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            st.markdown(f"""<div style="display:flex;justify-content:flex-end;margin:0.5rem 0;">
                <div style="background:linear-gradient(135deg,rgba(192,132,252,0.2),rgba(244,114,182,0.1));border:1px solid rgba(192,132,252,0.2);border-radius:14px 14px 4px 14px;padding:0.7rem 1rem;max-width:85%;font-size:0.85rem;color:rgba(255,255,255,0.9);">
                    {content}
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="display:flex;margin:0.5rem 0;">
                <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.06);border-radius:14px 14px 14px 4px;padding:0.7rem 1rem;max-width:90%;font-size:0.82rem;line-height:1.6;color:rgba(255,255,255,0.85);">
                    {content}
                </div>
            </div>""", unsafe_allow_html=True)

    user_input = st.chat_input("Ask about your salon business...", key="ai_chat_input")

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("🧠 Thinking..."):
            ctx = gather_salon_context()
            response = chat_with_saloon_data(user_input, ctx)
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("📋 Quick Actions (Staff, Expenses, Reports, etc.)"):
        role = st.session_state.get("role", "staff")
        allowed = ["staff", "expenses", "inventory", "reports", "invoices", "settings"]
        quick_items = [
            ("👨‍💼", "Staff", "staff"), ("📦", "Expenses", "expenses"),
            ("📦", "Stock", "inventory"), ("📄", "Reports", "reports"),
            ("🧾", "Invoices", "invoices"), ("⚙️", "Settings", "settings"),
        ]
        html = '<div class="more-grid">'
        for icon, label, key in quick_items:
            if role == "admin" or key not in ["staff", "expenses", "inventory", "reports", "analytics", "invoices"]:
                html += f'<button class="more-item" onclick="window.location.href=\'?page={key}\'" type="button"><span class="mi-icon">{icon}</span><span class="mi-label">{label}</span></button>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

def render_nav_link(key, icon, label, active, container_class, item_class):
    active_cls = f"{item_class} active" if active else item_class
    return f'<button class="{active_cls}" onclick="window.location.href=\'?page={key}\'" type="button"><span class="nav-icon">{icon}</span><span class="nav-label">{label}</span></button>'

def main():
    params = st.query_params
    page = params.get("page", "dashboard")

    role = st.session_state.get("role", "staff")
    username = st.session_state.get("username", "")
    role_badge = f'<span class="role-badge">{role.title()}</span>'

    # Desktop sidebar
    sidebar_items = "".join(
        render_nav_link(key, icon, label, page == key, "desktop-sidebar-nav", "sidebar-nav-item")
        for icon, label, key in NAV_ITEMS
    )
    st.markdown(f"""
    <div class="desktop-sidebar">
        <div class="sidebar-logo">💈 Saloon Pro</div>
        <div class="sidebar-user">{username} {role_badge}</div>
        {sidebar_items}
        <div style="margin-top:auto;padding:1rem 1.2rem;">
            <button class="sidebar-nav-item" onclick="window.location.href='?page=settings'" type="button" style="border-left-color:transparent;{'color:#c084fc' if page == 'settings' else ''}">
                <span class="nav-icon">⚙️</span><span class="nav-label">Settings</span>
            </button>
            <button class="sidebar-nav-item" onclick="window.location.href='?page=more'" type="button" style="border-left-color:transparent;{'color:#c084fc' if page == 'more' else ''}">
                <span class="nav-icon">📋</span><span class="nav-label">More</span>
            </button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top bar
    st.markdown(f"""
    <div class="app-topbar">
        <div class="app-title">💈 Saloon Pro</div>
        <div class="app-user">{username} {role_badge}
            <button class="signout-btn" onclick="window.location.href='?page=settings'" type="button" style="background:none;border:none;cursor:pointer;font-size:1rem;">⚙️</button>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Content area
    st.markdown('<div class="app-content">', unsafe_allow_html=True)

    pages = {
        "dashboard": dashboard_page,
        "appointments": appointments_page,
        "customers": customers_page,
        "transactions": transactions_page,
        "staff": staff_page,
        "expenses": expenses_page,
        "inventory": inventory_page,
        "reports": reports_page,
        "analytics": analytics_page,
        "invoices": invoices_page,
        "settings": settings_page,
        "more": more_page,
        "ai_chat": ai_chat_page,
    }

    pages.get(page, dashboard_page)()

    st.markdown('</div>', unsafe_allow_html=True)

    # Bottom nav (mobile)
    html = '<div class="bottom-nav">'
    for icon, label, key in NAV_ITEMS:
        active = "active" if key == page else ""
        html += f'<button class="nav-item {active}" onclick="window.location.href=\'?page={key}\'" type="button"><span class="nav-icon">{icon}</span><span class="nav-label">{label}</span></button>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
