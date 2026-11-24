import calendar
from dataclasses import dataclass
from datetime import date

ANNUAL_INTEREST_RATE = 0.08


@dataclass
class EmiInstallment:
    emi_number: int
    due_date: date
    emi_amount: int
    principal_component: int
    interest_component: int
    closing_balance: int


def add_months(start_date: date, months: int) -> date:
    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def calculate_monthly_emi(
    principal: int,
    tenure_months: int,
    annual_rate: float = ANNUAL_INTEREST_RATE,
) -> int:

    if principal <= 0:
        raise ValueError("Principal must be greater than zero")
    if tenure_months <= 0:
        raise ValueError("Tenure must be at least 1 month")

    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        return round(principal / tenure_months)

    factor = (1 + monthly_rate) ** tenure_months
    raw_emi = principal * monthly_rate * factor / (factor - 1)
    return round(raw_emi)


def generate_emi_schedule(
    principal: int,
    tenure_months: int,
    start_date: date | None = None,
    annual_rate: float = ANNUAL_INTEREST_RATE,
) -> tuple[int, list[EmiInstallment]]:

    if principal <= 0:
        raise ValueError("Principal must be greater than zero")
    if tenure_months <= 0:
        raise ValueError("Tenure must be at least 1 month")

    base_date = start_date or date.today()
    monthly_rate = annual_rate / 12
    base_emi = calculate_monthly_emi(principal, tenure_months, annual_rate)

    balance = int(principal)
    schedule: list[EmiInstallment] = []

    for month_num in range(1, tenure_months + 1):
        due_date = add_months(base_date, month_num)
        interest = round(balance * monthly_rate)

        if month_num == tenure_months:
            principal_part = balance
            emi_this_month = principal_part + interest
        else:
            principal_part = base_emi - interest
            if principal_part > balance:
                principal_part = balance
            emi_this_month = principal_part + interest

        balance -= principal_part

        schedule.append(
            EmiInstallment(
                emi_number=month_num,
                due_date=due_date,
                emi_amount=emi_this_month,
                principal_component=principal_part,
                interest_component=interest,
                closing_balance=balance,
            )
        )

    return base_emi, schedule


def calculate_foreclosure_settlement(
    outstanding_principal: int,
    annual_rate: float = ANNUAL_INTEREST_RATE,
) -> tuple[int, int]:

    if outstanding_principal <= 0:
        return 0, 0

    if annual_rate < 0:
        raise ValueError("Annual interest rate cannot be negative")

    monthly_rate = annual_rate / 12
    current_interest = round(outstanding_principal * monthly_rate)

    return current_interest, outstanding_principal + current_interest