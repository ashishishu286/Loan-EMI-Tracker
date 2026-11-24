# Loan EMI Tracker

A loan and EMI management app built with Python, FastAPI, SQLite and React (Vite). Staff can log in, add members, issue reducing-balance loans at 8% p.a., record monthly EMI payments, foreclose loans early, and export each member's outstanding balance to CSV.

## Features

### Core requirements

- **Login:** A mock login (`admin` / `password123`) that returns a Bearer token. Every `/api/*` endpoint checks it.
- **Dashboard:** Total members, active vs. total loans, total amount disbursed and total outstanding principal, all from one aggregate query.
- **Members:** Add a member with an employee/member ID, full name and monthly salary. Input is validated on the client and with Pydantic, and the list can be searched.
- **Loan creation:** Creating a loan generates the full monthly repayment schedule at 8% p.a. and saves it in the same transaction as the loan.
- **Loan detail:** Borrower details, current principal balance, and a schedule table with EMI number, due date, EMI amount, principal, interest, closing balance and status.
- **Outstanding report:** Per-member loan count, active loans, total principal and outstanding balance, with a CSV download.

### Bonus features

- **Record next EMI:** Marks the next `PENDING` installment as `PAID`, updates `outstanding_balance`, and closes the loan after the last installment.
- **Foreclose loan:** Settlement is `outstanding_principal + round(outstanding_principal * 0.08 / 12)`. Remaining installments are marked `WAIVED` and the loan becomes `CLOSED`.
- **Search and filters:** Search members by name or ID, and filter loans by `ALL` / `ACTIVE` / `CLOSED`.
- **Tests:** `pytest` tests for a standard 12-month schedule, a 1-month loan, invalid and zero inputs, month-end rollover (Jan 31 to Feb 28) and foreclosure amounts.

## Project structure

```text
loan-emi-tracker/
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── emi.py          # EMI, due-date and foreclosure math (no DB code)
│   │   ├── database.py     # SQLite connection and schema
│   │   ├── schemas.py      # Pydantic request models
│   │   ├── seed.py         # sample members and loans on first run
│   │   └── main.py         # routes, auth check, CSV export
│   └── tests/
│       └── test_emi.py
├── frontend/
│   └── src/
│       ├── utils.js        # INR and date formatting
│       ├── api.js          # fetch wrapper and CSV download
│       ├── App.jsx
│       └── components/     # Login, Dashboard, Members, Loans, LoanDetail, Report
└── README.md
```

## Running it locally

You need Python 3.10+ and Node.js 18+.

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The database (`loan_tracker.db`) and some sample members and loans are created on first startup. API docs are at `http://localhost:8000/docs`.

### Tests

```bash
cd backend
pytest
```

### Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and sign in with `admin` / `password123`.

## Tech choices

- **FastAPI + Pydantic:** Request validation, `401`/`404`/`409` handling, `Depends(require_auth)` for the auth check, and automatic API docs with little boilerplate.
- **SQLite (`sqlite3`):** No setup needed. A loan and its schedule are inserted inside one `db_session()` transaction, so a failure rolls both back and no loan is left without a schedule.
- **`emi.py` kept separate:** It has no FastAPI or database imports, so the formulas can be tested directly with `pytest` and reused by both the seed script and the API.
- **React + Vite with plain CSS:** A small frontend with no state-management library. Amounts are formatted with `Intl.NumberFormat('en-IN')` so they show Indian grouping (`₹1,23,456`).

## Assumptions and money handling

1. **Whole rupees.** Principal, salary and all EMI components are stored as integers. For installments 1 to n-1, interest is `round(remaining_balance * (0.08 / 12))` and the principal part is `EMI - interest`. On the last installment the principal part is set to whatever balance is left, so rounding differences of a rupee or so can't leave a small amount unpaid.
2. **Due dates.** The first due date is one month after the loan is created. `add_months` uses `calendar.monthrange`, so a date like Jan 31 becomes Feb 28 (or Feb 29 in a leap year) instead of spilling into March.
3. **Foreclosure.** An `ACTIVE` loan is settled for the outstanding balance plus one month of interest (`round(outstanding_balance * 0.08 / 12)`). Pending EMIs are marked `WAIVED` and the loan is set to `CLOSED`.

## AI Usage Notes

- AI was used in planning the whole project and Project Structure was given by AI. 
- Basic skeleton code is AI generated in the whole project.
- A major chunk of frontend is AI generated like the HTML file, CSS file and React Components because they comprise of very large number of lines of code and vibe coding this part isn't risky that's why I made this choice.
- Some variable names are AI generated to save time.
- Sometimes I got stuck while writing the code of backend AI assistance was taken.
- This project was fine tuned by reviewing manually and by consulting AI for better error handling if exists. For example in main.py I was handling the return of get_dashboard using "or 0" but AI taught me that using COALESCE is the best option, or Raising valueError instead of handling with pydantic the negative values in functions of emi.py
- This project introduced me to pytest, so I learned pytest using this project and AI.
- **Manually reviewed, verified & customized:** Reviewed and traced every line of the reducing-balance amortization logic (`emi.py`), final-month rounding adjustment, calendar month-end clamping (`add_months`), SQLite transactional boundaries (`db_session`), SQL aggregation queries (`COALESCE` / conditional `SUM`), and frontend state/API flows to ensure full understanding and correctness. 
- Lastly this README file is reviewed and edited using AI for mistakes and suggestions.