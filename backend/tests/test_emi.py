from datetime import date
import pytest

from app.emi import (
    calculate_foreclosure_settlement,
    calculate_monthly_emi,
    generate_emi_schedule,
)


def test_standard_12_month_loan_balances_to_zero():
    principal = 100_000
    tenure = 12
    emi, schedule = generate_emi_schedule(
        principal=principal, tenure_months=tenure, start_date=date(2025, 1, 15)
    )

    assert emi == 8699
    assert len(schedule) == 12

    # Reducing balance: month 1 interest must be strictly greater than month 12 interest
    assert schedule[0].interest_component > schedule[-1].interest_component

    # Sum of principal components must equal exact principal
    assert sum(row.principal_component for row in schedule) == principal

    # Every row must satisfy: EMI = principal + interest, and balance decreases properly
    prev_balance = principal
    for row in schedule:
        assert row.emi_amount == row.principal_component + row.interest_component
        assert row.closing_balance == prev_balance - row.principal_component
        prev_balance = row.closing_balance

    # Last EMI clears balance to 0
    assert schedule[-1].closing_balance == 0


def test_one_month_loan_edge_case():
    principal = 50_000
    emi, schedule = generate_emi_schedule(
        principal=principal, tenure_months=1, start_date=date(2025, 3, 1)
    )
    assert len(schedule) == 1
    expected_interest = round(50_000 * (0.08 / 12))  # 333
    assert schedule[0].principal_component == 50_000
    assert schedule[0].interest_component == expected_interest
    assert schedule[0].emi_amount == 50_000 + expected_interest
    assert schedule[0].closing_balance == 0
    assert emi == 50_000 + expected_interest


def test_invalid_inputs_raise_value_error():
    with pytest.raises(ValueError):
        calculate_monthly_emi(principal=10_000, tenure_months=0)

    with pytest.raises(ValueError):
        generate_emi_schedule(principal=0, tenure_months=12)

    with pytest.raises(ValueError):
        generate_emi_schedule(principal=-5000, tenure_months=6)


def test_month_end_due_date_handling():
    _, schedule = generate_emi_schedule(
        principal=24_000, tenure_months=2, start_date=date(2025, 1, 31)
    )
    assert schedule[0].due_date == date(2025, 2, 28)
    assert schedule[1].due_date == date(2025, 3, 31)


def test_foreclosure_settlement():
    interest, total = calculate_foreclosure_settlement(outstanding_principal=60_000)
    assert interest == 400  # 60000 * 0.08 / 12
    assert total == 60_400