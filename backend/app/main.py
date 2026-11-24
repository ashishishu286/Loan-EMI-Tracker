import csv
import io
import sqlite3
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .database import db_session, init_db
from .emi import (
    ANNUAL_INTEREST_RATE,
    calculate_foreclosure_settlement,
    generate_emi_schedule,
)
from .schemas import LoanCreate, LoginRequest, MemberCreate
from .seed import seed_initial_data


VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"
MOCK_TOKEN = "staff-session-token-123"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    seed_initial_data()
    yield


app = FastAPI(title="Loan EMI Tracker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_auth(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if token != MOCK_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token",
        )
    return VALID_USERNAME


@app.post("/api/login")
def login(payload: LoginRequest):
    if payload.username.strip() != VALID_USERNAME or payload.password != VALID_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return {
        "token": MOCK_TOKEN,
        "user": {"username": VALID_USERNAME, "role": "Staff Admin"},
    }


@app.get("/api/dashboard")
def get_dashboard(_user: str = Depends(require_auth)):
    with db_session() as conn:
        member_count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        loan_stats = conn.execute(
            """
            SELECT
                COUNT(*) AS total_loans,
                COALESCE(SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END), 0) AS active_loans,
                COALESCE(SUM(principal), 0) AS total_disbursed,
                COALESCE(SUM(outstanding_balance), 0) AS total_outstanding
            FROM loans
            """
        ).fetchone()
    return {
        "total_members": member_count,
        "total_loans": loan_stats["total_loans"],
        "active_loans": loan_stats["active_loans"],
        "total_disbursed": loan_stats["total_disbursed"],
        "total_outstanding": loan_stats["total_outstanding"],
    }


@app.get("/api/members")
def list_members(_user: str = Depends(require_auth)):
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT id, member_code, name, monthly_salary, created_at
            FROM members
            ORDER BY id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/members", status_code=status.HTTP_201_CREATED)
def create_member(payload: MemberCreate, _user: str = Depends(require_auth)):
    now = datetime.now(timezone.utc).isoformat()
    try:
        with db_session() as conn:
            cursor = conn.execute(
                """
                INSERT INTO members (member_code, name, monthly_salary, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (payload.member_code, payload.name, payload.monthly_salary, now),
            )
            member_id = cursor.lastrowid
            row = conn.execute(
                "SELECT id, member_code, name, monthly_salary, created_at FROM members WHERE id = ?",
                (member_id,),
            ).fetchone()
        return dict(row)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Member ID '{payload.member_code}' already exists",
        )


@app.get("/api/loans")
def list_loans(_user: str = Depends(require_auth)):
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT
                l.id, l.member_id, m.name AS member_name, m.member_code,
                l.principal, l.tenure_months, l.annual_interest_rate,
                l.emi_amount, l.outstanding_balance, l.status,
                l.foreclosed_amount, l.created_at
            FROM loans l
            JOIN members m ON m.id = l.member_id
            ORDER BY l.id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/loans", status_code=status.HTTP_201_CREATED)
def create_loan(payload: LoanCreate, _user: str = Depends(require_auth)):
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        member = conn.execute(
            "SELECT id, name FROM members WHERE id = ?", (payload.member_id,)
        ).fetchone()
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")

        emi_amount, schedule = generate_emi_schedule(
            principal=payload.principal,
            tenure_months=payload.tenure_months,
            start_date=date.today(),
        )

        cursor = conn.execute(
            """
            INSERT INTO loans (
                member_id, principal, tenure_months, annual_interest_rate,
                emi_amount, outstanding_balance, status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
            """,
            (
                payload.member_id,
                payload.principal,
                payload.tenure_months,
                ANNUAL_INTEREST_RATE,
                emi_amount,
                payload.principal,
                now,
            ),
        )
        loan_id = cursor.lastrowid

        schedule_rows = [
            (
                loan_id,
                item.emi_number,
                item.due_date.isoformat(),
                item.emi_amount,
                item.principal_component,
                item.interest_component,
                item.closing_balance,
                "PENDING",
                None,
            )
            for item in schedule
        ]
        conn.executemany(
            """
            INSERT INTO emi_schedule (
                loan_id, emi_number, due_date, emi_amount,
                principal_component, interest_component,
                closing_balance, status, paid_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            schedule_rows,
        )

    return {"id": loan_id, "emi_amount": emi_amount, "status": "ACTIVE"}


@app.get("/api/loans/{loan_id}")
def get_loan_detail(loan_id: int, _user: str = Depends(require_auth)):
    with db_session() as conn:
        loan = conn.execute(
            """
            SELECT
                l.*, m.name AS member_name, m.member_code
            FROM loans l
            JOIN members m ON m.id = l.member_id
            WHERE l.id = ?
            """,
            (loan_id,),
        ).fetchone()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")

        schedule = conn.execute(
            """
            SELECT
                id, emi_number, due_date, emi_amount,
                principal_component, interest_component,
                closing_balance, status, paid_at
            FROM emi_schedule
            WHERE loan_id = ?
            ORDER BY emi_number ASC
            """,
            (loan_id,),
        ).fetchall()

    foreclosure_interest, foreclosure_total = calculate_foreclosure_settlement(
        loan["outstanding_balance"]
    )
    result = dict(loan)
    result["schedule"] = [dict(row) for row in schedule]
    result["foreclosure_preview"] = {
        "current_month_interest": foreclosure_interest,
        "settlement_amount": foreclosure_total,
    }
    return result


@app.post("/api/loans/{loan_id}/pay-next")
def pay_next_emi(loan_id: int, _user: str = Depends(require_auth)):
    now = datetime.now(timezone.utc).isoformat()
    with db_session() as conn:
        loan = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        if loan["status"] != "ACTIVE":
            raise HTTPException(status_code=400, detail="Loan is already closed")

        next_emi = conn.execute(
            """
            SELECT * FROM emi_schedule
            WHERE loan_id = ? AND status = 'PENDING'
            ORDER BY emi_number ASC
            LIMIT 1
            """,
            (loan_id,),
        ).fetchone()
        if not next_emi:
            raise HTTPException(status_code=400, detail="No pending EMIs left")

        conn.execute(
            "UPDATE emi_schedule SET status = 'PAID', paid_at = ? WHERE id = ?",
            (now, next_emi["id"]),
        )

        new_balance = next_emi["closing_balance"]
        new_status = "CLOSED" if new_balance <= 0 else "ACTIVE"
        conn.execute(
            "UPDATE loans SET outstanding_balance = ?, status = ? WHERE id = ?",
            (new_balance, new_status, loan_id),
        )

    return {"paid_emi_number": next_emi["emi_number"], "new_balance": new_balance, "status": new_status}


@app.post("/api/loans/{loan_id}/foreclose")
def foreclose_loan(loan_id: int, _user: str = Depends(require_auth)):
    with db_session() as conn:
        loan = conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        if loan["status"] != "ACTIVE":
            raise HTTPException(status_code=400, detail="Loan is already closed")

        _, settlement_amount = calculate_foreclosure_settlement(
            loan["outstanding_balance"]
        )

        conn.execute(
            """
            UPDATE emi_schedule
            SET status = 'WAIVED'
            WHERE loan_id = ? AND status = 'PENDING'
            """,
            (loan_id,),
        )
        conn.execute(
            """
            UPDATE loans
            SET outstanding_balance = 0, status = 'CLOSED', foreclosed_amount = ?
            WHERE id = ?
            """,
            (settlement_amount, loan_id),
        )

    return {"status": "CLOSED", "settlement_amount": settlement_amount}


def _fetch_member_outstanding_report():
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT
                m.id AS member_id,
                m.member_code,
                m.name AS member_name,
                m.monthly_salary,
                COUNT(l.id) AS total_loans,
                SUM(CASE WHEN l.status = 'ACTIVE' THEN 1 ELSE 0 END) AS active_loans,
                COALESCE(SUM(l.principal), 0) AS total_principal,
                COALESCE(SUM(l.outstanding_balance), 0) AS total_outstanding
            FROM members m
            LEFT JOIN loans l ON l.member_id = m.id
            GROUP BY m.id
            ORDER BY total_outstanding DESC, m.name ASC
            """
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/reports/member-outstanding")
def member_outstanding_report(_user: str = Depends(require_auth)):
    return _fetch_member_outstanding_report()


@app.get("/api/reports/member-outstanding/csv")
def export_member_outstanding_csv(_user: str = Depends(require_auth)):
    rows = _fetch_member_outstanding_report()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "Member ID",
            "Member Name",
            "Monthly Salary (INR)",
            "Total Loans",
            "Active Loans",
            "Total Principal (INR)",
            "Total Outstanding (INR)",
        ]
    )
    for row in rows:
        writer.writerow(
            [
                row["member_code"],
                row["member_name"],
                row["monthly_salary"],
                row["total_loans"],
                row["active_loans"] or 0,
                row["total_principal"],
                row["total_outstanding"],
            ]
        )

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="member-outstanding-report.csv"'
        },
    )