import os
import shutil
import json
import logging
from datetime import datetime, date, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, Text, ForeignKey, func, text, Index
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import NullPool, QueuePool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("saloon.db")

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BACKUP_DIR = os.path.join(DB_DIR, "backups")
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "salon.db")

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
IS_SQLITE = "sqlite" in DATABASE_URL

if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args={
            "check_same_thread": False,
        },
        poolclass=NullPool,
    )
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA synchronous=NORMAL"))
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("PRAGMA busy_timeout=5000"))
        conn.execute(text("PRAGMA cache_size=-64000"))
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@contextmanager
def session_scope():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ─── Models ───

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    phone = Column(String(50), nullable=False, index=True)
    email = Column(String(200), default="")
    notes = Column(Text, default="")
    total_visits = Column(Integer, default=1)
    total_spent = Column(Float, default=0.0)
    first_visit = Column(DateTime, default=datetime.now)
    last_visit = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    transactions = relationship("Transaction", back_populates="customer", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="customer", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    service = Column(String(200), default="General")
    payment_method = Column(String(50), default="Cash")
    timestamp = Column(DateTime, default=datetime.now, index=True)
    date_only = Column(Date, default=date.today, index=True)
    created_by = Column(String(100), default="")
    customer = relationship("Customer", back_populates="transactions")

class Staff(Base):
    __tablename__ = "staff"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    role = Column(String(100), default="Stylist")
    phone = Column(String(50), default="")
    salary = Column(Float, default=0.0)
    commission_rate = Column(Float, default=0.0)
    joined_date = Column(Date, default=date.today)
    is_active = Column(Integer, default=1, index=True)
    created_at = Column(DateTime, default=datetime.now)
    appointments = relationship("Appointment", back_populates="staff")

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    description = Column(Text, default="")
    amount = Column(Float, nullable=False)
    date_incurred = Column(Date, default=date.today, index=True)
    recurring = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

class SaloonSetting(Base):
    __tablename__ = "saloon_settings"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(200), default="")
    phone = Column(String(50), default="")
    email = Column(String(200), default="")
    address = Column(Text, default="")
    notes = Column(Text, default="")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)

class InventoryItem(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(100), default="General", index=True)
    quantity = Column(Float, default=0)
    unit = Column(String(50), default="pcs")
    min_stock_level = Column(Float, default=5)
    unit_price = Column(Float, default=0.0)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    notes = Column(Text, default="")
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    supplier = relationship("Supplier")

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey("staff.id"), nullable=True, index=True)
    service = Column(String(200), default="General")
    appointment_date = Column(Date, nullable=False, index=True)
    appointment_time = Column(String(10), default="10:00")
    duration_minutes = Column(Integer, default=30)
    status = Column(String(20), default="scheduled", index=True)
    notes = Column(Text, default="")
    created_by = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.now)
    customer = relationship("Customer", back_populates="appointments")
    staff = relationship("Staff", back_populates="appointments")

class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    amount = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    status = Column(String(20), default="paid")
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.now)
    customer = relationship("Customer")


# ─── Init & Migration ───

def init_db():
    Base.metadata.create_all(bind=engine)
    _run_migrations()
    engine_type = "SQLite (WAL mode)" if IS_SQLITE else "PostgreSQL"
    logger.info(f"Database initialized — {engine_type}")


def _run_migrations():
    with session_scope() as db:
        for col, table, definition in [
            ("created_by", "transactions", "VARCHAR(100) DEFAULT ''"),
            ("created_by", "appointments", "VARCHAR(100) DEFAULT ''"),
            ("is_active", "users", "INTEGER DEFAULT 1"),
        ]:
            try:
                db.execute(text(f"SELECT {col} FROM {table} LIMIT 0"))
            except Exception:
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {definition}"))
                logger.info(f"Migration: added {col} to {table}")


def get_db():
    return SessionLocal()


@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def seed_defaults():
    try:
        with session_scope() as db:
            existing = db.query(User).filter(User.username == "admin").first()
            if not existing:
                import bcrypt
                hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
                db.add(User(username="admin", password_hash=hashed, role="admin"))
                logger.info("Default admin user created (admin / admin123)")
    except Exception:
        pass  # Swallow race-condition duplicates; admin user already exists


# ─── Backup & Restore (SQLite-optimized) ───

def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"salon_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    if IS_SQLITE:
        with session_scope() as db:
            db.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
        shutil.copy2(DB_PATH, backup_path)
    else:
        with session_scope() as db:
            data = {}
            for table in Base.metadata.tables.keys():
                rows = db.execute(text(f"SELECT * FROM {table}")).fetchall()
                data[table] = [
                    {c: (v.isoformat() if isinstance(v, (datetime, date)) else v)
                     for c, v in r._mapping.items()}
                    for r in rows
                ]
        backup_path = backup_path.replace(".db", ".json")
        with open(backup_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    size = os.path.getsize(backup_path)
    logger.info(f"Backup created: {backup_name} ({size / 1024:.1f} KB)")
    return backup_name


def restore_database(backup_filename):
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"Backup not found: {backup_filename}")

    if IS_SQLITE:
        if backup_filename.endswith(".json"):
            with open(backup_path, "r") as f:
                data = json.load(f)
            with session_scope() as db:
                for table in reversed(list(data.keys())):
                    if Base.metadata.tables.get(table):
                        db.execute(text(f"DELETE FROM {table}"))
                for table, rows in data.items():
                    if not rows or not Base.metadata.tables.get(table):
                        continue
                    for row in rows:
                        clean = {k: v for k, v in row.items() if v is not None}
                        if clean:
                            cols = ",".join(clean.keys())
                            vals = ",".join([f":{k}" for k in clean.keys()])
                            db.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({vals})"), clean)
        else:
            engine.dispose()
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
            shutil.copy2(backup_path, DB_PATH)
            init_db()
    else:
        with open(backup_path, "r") as f:
            data = json.load(f)
        with session_scope() as db:
            for table in reversed(list(data.keys())):
                if Base.metadata.tables.get(table):
                    db.execute(text(f"DELETE FROM {table}"))
            for table, rows in data.items():
                if not rows or not Base.metadata.tables.get(table):
                    continue
                for row in rows:
                    clean = {k: v for k, v in row.items() if v is not None}
                    if clean:
                        cols = ",".join(clean.keys())
                        vals = ",".join([f":{k}" for k in clean.keys()])
                        try:
                            db.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({vals})"), clean)
                        except Exception as e:
                            logger.warning(f"Skipping row in {table}: {e}")

    logger.info(f"Restored from: {backup_filename}")
    return True


def list_backups():
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        path = os.path.join(BACKUP_DIR, f)
        size = os.path.getsize(path)
        mod = datetime.fromtimestamp(os.path.getmtime(path))
        backups.append({"file": f, "size": f"{size / 1024:.1f} KB", "date": mod.strftime("%d %b %Y %H:%M")})
    return backups
