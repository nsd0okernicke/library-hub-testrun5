"""Property-based tests for the Loan return transition (pure Python)."""

import string
from datetime import datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from loans.domain.exceptions import LoanNotActive
from loans.domain.loan import Loan, LoanStatus, utc_now

ID_TEXT = st.text(alphabet=string.ascii_letters + string.digits + "-_", min_size=1, max_size=16)
TIMESTAMPS = st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2100, 1, 1))


def _active_loan(loan_id: str, user_id: str, isbn: str, created: datetime) -> Loan:
    return Loan(
        loan_id=loan_id,
        user_id=user_id,
        isbn=isbn,
        status=LoanStatus.ACTIVE,
        created_at=created,
        due_date=created + timedelta(days=28),
    )


@given(ID_TEXT, ID_TEXT, ID_TEXT, TIMESTAMPS)
def test_returning_an_active_loan_keeps_identity_and_clears_due_date(
    loan_id: str, user_id: str, isbn: str, created: datetime
) -> None:
    """An ACTIVE loan — overdue or not — always returns as RETURNED with identity intact."""
    loan = _active_loan(loan_id, user_id, isbn, created)
    returned = loan.mark_returned()
    assert returned.status is LoanStatus.RETURNED
    assert returned.due_date is None
    assert (returned.loan_id, returned.user_id, returned.isbn) == (loan_id, user_id, isbn)
    assert returned.created_at == created
    assert loan.status is LoanStatus.ACTIVE  # original untouched


@given(st.integers(min_value=-365, max_value=365))
def test_return_does_not_depend_on_overdue_state(days_past: int) -> None:
    """Overdue (past due date) and not-yet-due ACTIVE loans return identically."""
    loan = _active_loan("loan-1", "usr-1", "978-0-20-163361-0", utc_now())
    due_date = utc_now() + timedelta(days=days_past)
    dated = Loan(
        loan_id=loan.loan_id,
        user_id=loan.user_id,
        isbn=loan.isbn,
        status=LoanStatus.ACTIVE,
        created_at=loan.created_at,
        due_date=due_date,
    )
    returned = dated.mark_returned()
    assert returned.status is LoanStatus.RETURNED
    assert returned.due_date is None


@given(st.sampled_from([LoanStatus.PENDING, LoanStatus.REJECTED, LoanStatus.RETURNED]))
def test_returning_a_non_active_loan_always_raises(status: LoanStatus) -> None:
    """PENDING, REJECTED and already-RETURNED loans can never be returned."""
    due = (
        datetime(2026, 2, 1)
        if status is LoanStatus.ACTIVE  # unreachable, kept for readability
        else None
    )
    loan = Loan(
        loan_id="loan-1",
        user_id="usr-1",
        isbn="978-0-20-163361-0",
        status=status,
        created_at=datetime(2026, 1, 1),
        due_date=due,
    )
    try:
        loan.mark_returned()
        raise AssertionError(f"expected LoanNotActive for {status}")
    except LoanNotActive:
        assert loan.status is status  # loan unchanged
