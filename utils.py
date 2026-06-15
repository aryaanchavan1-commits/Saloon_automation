import pandas as pd
from datetime import datetime, date, timedelta
from database import session_scope, SessionLocal, Customer, Transaction, Staff, Expense, InventoryItem, Supplier, Appointment, Invoice, backup_database, restore_database, list_backups
from sqlalchemy import func

def load_customers():
    db = SessionLocal()
    try:
        return db.query(Customer).order_by(Customer.last_visit.desc()).all()
    finally:
        db.close()

def load_transactions(limit=500):
    db = SessionLocal()
    try:
        return db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(limit).all()
    finally:
        db.close()

def load_staff():
    db = SessionLocal()
    try:
        return db.query(Staff).filter(Staff.is_active == 1).all()
    finally:
        db.close()

def load_expenses():
    db = SessionLocal()
    try:
        return db.query(Expense).order_by(Expense.date_incurred.desc()).all()
    finally:
        db.close()

def get_customer_by_phone(phone):
    db = SessionLocal()
    try:
        return db.query(Customer).filter(Customer.phone == phone).first()
    finally:
        db.close()

def add_customer(name, phone, amount, service="General", payment_method="Cash"):
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        now = datetime.now()
        today = date.today()

        if customer:
            customer.total_visits += 1
            customer.total_spent += amount
            customer.last_visit = now
            if customer.name != name:
                customer.name = name
        else:
            customer = Customer(
                name=name, phone=phone, total_visits=1,
                total_spent=amount, first_visit=now, last_visit=now
            )
            db.add(customer)
            db.flush()

        txn = Transaction(
            customer_id=customer.id, amount=amount,
            service=service, payment_method=payment_method,
            timestamp=now, date_only=today
        )
        db.add(txn)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def add_staff(name, role, phone, salary, commission):
    db = SessionLocal()
    try:
        staff = Staff(name=name, role=role, phone=phone, salary=salary, commission_rate=commission)
        db.add(staff)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def add_expense(category, description, amount, date_incurred=None, recurring=0):
    db = SessionLocal()
    try:
        if date_incurred is None:
            date_incurred = date.today()
        exp = Expense(category=category, description=description, amount=amount, date_incurred=date_incurred, recurring=recurring)
        db.add(exp)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def get_dashboard_stats():
    db = SessionLocal()
    try:
        today = date.today()
        month_start = date(today.year, today.month, 1)

        total_revenue = db.query(func.sum(Transaction.amount)).scalar() or 0
        month_revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.date_only >= month_start
        ).scalar() or 0
        today_revenue = db.query(func.sum(Transaction.amount)).filter(
            Transaction.date_only == today
        ).scalar() or 0

        total_customers = db.query(func.count(Customer.id)).scalar() or 0
        total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
        total_staff = db.query(func.count(Staff.id)).filter(Staff.is_active == 1).scalar() or 0
        total_expenses = db.query(func.sum(Expense.amount)).scalar() or 0

        avg_per_customer = total_revenue / total_customers if total_customers > 0 else 0

        return {
            "total_revenue": total_revenue,
            "month_revenue": month_revenue,
            "today_revenue": today_revenue,
            "total_customers": total_customers,
            "total_transactions": total_transactions,
            "total_staff": total_staff,
            "total_expenses": total_expenses,
            "avg_per_customer": avg_per_customer,
        }
    finally:
        db.close()

def get_repeat_customers(min_visits=2):
    db = SessionLocal()
    try:
        customers = db.query(Customer).filter(Customer.total_visits >= min_visits).order_by(Customer.total_visits.desc()).all()
        return [
            {
                "name": c.name,
                "phone": c.phone,
                "visits": c.total_visits,
                "total_spent": c.total_spent,
                "last_visit": c.last_visit.strftime("%Y-%m-%d %H:%M") if c.last_visit else "N/A"
            }
            for c in customers
        ]
    finally:
        db.close()

def get_monthly_revenue(year=None):
    if year is None:
        year = datetime.now().year
    db = SessionLocal()
    try:
        rows = db.query(
            func.strftime("%m", Transaction.date_only).label("month"),
            func.sum(Transaction.amount).label("revenue"),
            func.count(Transaction.id).label("count")
        ).filter(
            func.strftime("%Y", Transaction.date_only) == str(year)
        ).group_by("month").order_by("month").all()

        months = {f"{i:02d}": {"revenue": 0, "count": 0} for i in range(1, 13)}
        for row in rows:
            months[row.month] = {"revenue": float(row.revenue or 0), "count": row.count}

        return months
    finally:
        db.close()

def get_daily_revenue(days=30):
    db = SessionLocal()
    try:
        since = date.today() - timedelta(days=days)
        rows = db.query(
            Transaction.date_only,
            func.sum(Transaction.amount).label("revenue"),
            func.count(Transaction.id).label("count")
        ).filter(Transaction.date_only >= since).group_by(Transaction.date_only).order_by(Transaction.date_only).all()
        return rows
    finally:
        db.close()

def get_top_customers(limit=10):
    db = SessionLocal()
    try:
        return db.query(Customer).order_by(Customer.total_spent.desc()).limit(limit).all()
    finally:
        db.close()

def get_expense_by_category():
    db = SessionLocal()
    try:
        rows = db.query(
            Expense.category,
            func.sum(Expense.amount).label("total")
        ).group_by(Expense.category).all()
        return {r.category: float(r.total) for r in rows}
    finally:
        db.close()

def get_staff_salary_total():
    db = SessionLocal()
    try:
        return db.query(func.sum(Staff.salary)).filter(Staff.is_active == 1).scalar() or 0
    finally:
        db.close()

def load_inventory():
    db = SessionLocal()
    try:
        return db.query(InventoryItem).filter(InventoryItem.is_active == 1).order_by(InventoryItem.name).all()
    finally:
        db.close()

def add_inventory_item(name, category, quantity, unit, min_stock, unit_price, supplier_id, notes):
    db = SessionLocal()
    try:
        item = InventoryItem(name=name, category=category, quantity=quantity, unit=unit, min_stock_level=min_stock, unit_price=unit_price, supplier_id=supplier_id if supplier_id else None, notes=notes)
        db.add(item)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def update_inventory_quantity(item_id, new_qty):
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if item:
            item.quantity = new_qty
            db.commit()
            return True
        return False
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_inventory_item(item_id):
    db = SessionLocal()
    try:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if item:
            item.is_active = 0
            db.commit()
            return True
        return False
    except:
        db.rollback()
        return False
    finally:
        db.close()

def load_suppliers():
    db = SessionLocal()
    try:
        return db.query(Supplier).filter(Supplier.is_active == 1).order_by(Supplier.name).all()
    finally:
        db.close()

def add_supplier(name, contact_person, phone, email, address, notes):
    db = SessionLocal()
    try:
        supplier = Supplier(name=name, contact_person=contact_person, phone=phone, email=email, address=address, notes=notes)
        db.add(supplier)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_supplier(supplier_id):
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if supplier:
            supplier.is_active = 0
            db.commit()
            return True
        return False
    except:
        db.rollback()
        return False
    finally:
        db.close()

def get_inventory_stats():
    db = SessionLocal()
    try:
        total_items = db.query(func.count(InventoryItem.id)).filter(InventoryItem.is_active == 1).scalar() or 0
        low_stock = db.query(func.count(InventoryItem.id)).filter(InventoryItem.is_active == 1, InventoryItem.quantity <= InventoryItem.min_stock_level).scalar() or 0
        total_value = db.query(func.sum(InventoryItem.quantity * InventoryItem.unit_price)).filter(InventoryItem.is_active == 1).scalar() or 0
        return {"total_items": total_items, "low_stock": low_stock, "total_value": total_value}
    finally:
        db.close()

# ─── Transaction Edit/Delete ───

def update_transaction(txn_id, amount, service, payment_method):
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            return False
        old_amount = txn.amount
        txn.amount = amount
        txn.service = service
        txn.payment_method = payment_method
        customer = txn.customer
        if customer:
            customer.total_spent = customer.total_spent - old_amount + amount
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_transaction(txn_id):
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
        if not txn:
            return False
        customer = txn.customer
        if customer:
            customer.total_visits -= 1
            customer.total_spent -= txn.amount
        db.delete(txn)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def get_transaction_by_id(txn_id):
    db = SessionLocal()
    try:
        return db.query(Transaction).filter(Transaction.id == txn_id).first()
    finally:
        db.close()

def update_customer(customer_id, name, phone, email, notes):
    db = SessionLocal()
    try:
        c = db.query(Customer).filter(Customer.id == customer_id).first()
        if not c:
            return False
        c.name = name
        c.phone = phone
        c.email = email
        c.notes = notes
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_customer(customer_id):
    db = SessionLocal()
    try:
        c = db.query(Customer).filter(Customer.id == customer_id).first()
        if not c:
            return False
        db.delete(c)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def update_staff(staff_id, name, role, phone, salary, commission):
    db = SessionLocal()
    try:
        s = db.query(Staff).filter(Staff.id == staff_id).first()
        if not s:
            return False
        s.name = name
        s.role = role
        s.phone = phone
        s.salary = salary
        s.commission_rate = commission
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_staff(staff_id):
    db = SessionLocal()
    try:
        s = db.query(Staff).filter(Staff.id == staff_id).first()
        if not s:
            return False
        s.is_active = 0
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def update_expense(expense_id, category, description, amount, date_incurred, recurring):
    db = SessionLocal()
    try:
        e = db.query(Expense).filter(Expense.id == expense_id).first()
        if not e:
            return False
        e.category = category
        e.description = description
        e.amount = amount
        e.date_incurred = date_incurred
        e.recurring = recurring
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_expense(expense_id):
    db = SessionLocal()
    try:
        e = db.query(Expense).filter(Expense.id == expense_id).first()
        if not e:
            return False
        db.delete(e)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

# ─── Appointment CRUD ───

TIME_SLOTS = [f"{h:02d}:{m:02d}" for h in range(9, 20) for m in [0, 30]]

def load_appointments(date_filter=None):
    db = SessionLocal()
    try:
        q = db.query(Appointment).order_by(Appointment.appointment_date, Appointment.appointment_time)
        if date_filter:
            q = q.filter(Appointment.appointment_date == date_filter)
        return q.all()
    finally:
        db.close()

def add_appointment(customer_id, staff_id, service, app_date, app_time, duration, notes):
    db = SessionLocal()
    try:
        existing = db.query(Appointment).filter(
            Appointment.staff_id == staff_id,
            Appointment.appointment_date == app_date,
            Appointment.appointment_time == app_time,
            Appointment.status.in_(["scheduled", "confirmed"])
        ).first()
        if existing:
            return False, "Time slot already booked"
        apt = Appointment(
            customer_id=customer_id, staff_id=staff_id,
            service=service, appointment_date=app_date,
            appointment_time=app_time, duration_minutes=duration,
            notes=notes, status="scheduled"
        )
        db.add(apt)
        db.commit()
        return True, None
    except Exception as e:
        db.rollback()
        return False, str(e)
    finally:
        db.close()

def update_appointment_status(apt_id, status):
    db = SessionLocal()
    try:
        apt = db.query(Appointment).filter(Appointment.id == apt_id).first()
        if not apt:
            return False
        apt.status = status
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def delete_appointment(apt_id):
    db = SessionLocal()
    try:
        apt = db.query(Appointment).filter(Appointment.id == apt_id).first()
        if not apt:
            return False
        db.delete(apt)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    finally:
        db.close()

def get_appointments_by_date_range(start_date, end_date):
    db = SessionLocal()
    try:
        return db.query(Appointment).filter(
            Appointment.appointment_date.between(start_date, end_date)
        ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    finally:
        db.close()

# ─── Invoice Generation ───

def generate_invoice_number():
    db = SessionLocal()
    try:
        count = db.query(func.count(Invoice.id)).scalar() or 0
        return f"INV-{datetime.now().strftime('%Y%m')}-{count + 1:04d}"
    finally:
        db.close()

def create_invoice(transaction_id, customer_id, amount, tax_pct=0, discount=0):
    db = SessionLocal()
    try:
        tax = amount * tax_pct / 100
        total = amount + tax - discount
        inv = Invoice(
            invoice_number=generate_invoice_number(),
            transaction_id=transaction_id,
            customer_id=customer_id,
            amount=amount, tax=tax,
            discount=discount, total=total
        )
        db.add(inv)
        db.commit()
        return inv
    except:
        db.rollback()
        return None
    finally:
        db.close()

def load_invoices():
    db = SessionLocal()
    try:
        return db.query(Invoice).order_by(Invoice.created_at.desc()).all()
    finally:
        db.close()

def get_appointment_stats():
    db = SessionLocal()
    try:
        today = date.today()
        total = db.query(func.count(Appointment.id)).filter(Appointment.appointment_date == today).scalar() or 0
        upcoming = db.query(func.count(Appointment.id)).filter(Appointment.appointment_date >= today,
            Appointment.status.in_(["scheduled", "confirmed"])).scalar() or 0
        completed = db.query(func.count(Appointment.id)).filter(Appointment.status == "completed",
            Appointment.appointment_date == today).scalar() or 0
        return {"today": total, "upcoming": upcoming, "completed": completed}
    finally:
        db.close()
