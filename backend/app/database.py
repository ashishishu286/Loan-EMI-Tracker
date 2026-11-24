import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "loan_tracker.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with db_session() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                monthly_salary INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                principal INTEGER NOT NULL,
                tenure_months INTEGER NOT NULL,
                annual_interest_rate REAL NOT NULL,
                emi_amount INTEGER NOT NULL,
                outstanding_balance INTEGER NOT NULL,
                status TEXT NOT NULL,
                foreclosed_amount INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (member_id) REFERENCES members (id)
            );

            CREATE TABLE IF NOT EXISTS emi_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id INTEGER NOT NULL,
                emi_number INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                emi_amount INTEGER NOT NULL,
                principal_component INTEGER NOT NULL,
                interest_component INTEGER NOT NULL,
                closing_balance INTEGER NOT NULL,
                status TEXT NOT NULL,
                paid_at TEXT,
                FOREIGN KEY (loan_id) REFERENCES loans (id)
            );
            """
        )