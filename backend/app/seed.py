from datetime import date, datetime, timezone
from .database import db_session
from .emi import ANNUAL_INTEREST_RATE, generate_emi_schedule


def seed_initial_data() -> None:
    with db_session() as conn:
        count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        if count > 0:
            return

        now = datetime.now(timezone.utc).isoformat()
        members = [
            ("EMP-101", "Aarav Sharma", 65000, now),
            ("EMP-102", "Priya Nair", 82000, now),
            ("EMP-103", "Rohan Deshmukh", 54000, now),
        ]
        conn.executemany(
            """
            INSERT INTO members (member_code, name, monthly_salary, created_at)
            VALUES (?, ?, ?, ?)
            """,
            members,
        )

        # Create 2 sample loans so the dashboard & reports look useful immediately
        sample_loans = [
            (1, 120000, 12, 2),  # member_id, principal, tenure, mark 2 EMIs paid
            (2, 250000, 24, 0),  # active, 0 EMIs paid
        ]

        for member_id, principal, tenure, paid_count in sample_loans:
            emi_amount, schedule = generate_emi_schedule(
                principal=principal,
                tenure_months=tenure,
                start_date=date.today(),
            )
            outstanding = (
                schedule[paid_count - 1].closing_balance if paid_count > 0 else principal
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
                    member_id,
                    principal,
                    tenure,
                    ANNUAL_INTEREST_RATE,
                    emi_amount,
                    outstanding,
                    now,
                ),
            )
            loan_id = cursor.lastrowid

            rows = []
            for item in schedule:
                is_paid = item.emi_number <= paid_count
                rows.append(
                    (
                        loan_id,
                        item.emi_number,
                        item.due_date.isoformat(),
                        item.emi_amount,
                        item.principal_component,
                        item.interest_component,
                        item.closing_balance,
                        "PAID" if is_paid else "PENDING",
                        now if is_paid else None,
                    )
                )
            conn.executemany(
                """
                INSERT INTO emi_schedule (
                    loan_id, emi_number, due_date, emi_amount,
                    principal_component, interest_component,
                    closing_balance, status, paid_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )