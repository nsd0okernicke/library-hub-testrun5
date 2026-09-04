"""Property-based tests for the Loan overdue rule."""

from datetime import datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from loans.domain.loan import Loan, LoanStatus

moment_strategy = st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2100, 1, 1))
term_strategy = st.integers(min_value=1, max_value=3650)
status_strategy = st.sampled_from([LoanStatus.PENDING, LoanStatus.REJECTED, LoanStatus.RETURNED])


def _active_loan(created_at: datetime, term: int) -> Loan:
    return Loan(
        loan_id="loan-1",
        user_id="usr-1",
        isbn="978-0-20-163361-0",
        status=LoanStatus.PENDING,
        created_at=created_at,
        due_date=None,
    ).activate(due_date_term_days=term)


def _non_active_loan(created_at: datetime, status: LoanStatus) -> Loan:
    return Loan(
        loan_id="loan-1",
        user_id="usr-1",
        isbn="978-0-20-163361-0",
        status=status,
        created_at=created_at,
        due_date=None,
    )


class TestLoanOverdueProperties:
    @given(created_at=moment_strategy, term=term_strategy, now=moment_strategy)
    @settings(max_examples=50)
    def test_overdue_iff_active_and_past_due(
        self, created_at: datetime, term: int, now: datetime
    ) -> None:
        loan = _active_loan(created_at, term)
        due = loan.due_date
        assert due is not None
        assert loan.is_overdue(now) is (due < now)

    @given(created_at=moment_strategy, status=status_strategy, now=moment_strategy)
    @settings(max_examples=50)
    def test_non_active_loans_are_never_overdue(
        self, created_at: datetime, status: LoanStatus, now: datetime
    ) -> None:
        loan = _non_active_loan(created_at, status)
        assert loan.is_overdue(now) is False

    @given(created_at=moment_strategy, term=term_strategy)
    @settings(max_examples=50)
    def test_becomes_overdue_exactly_one_term_after_creation(
        self, created_at: datetime, term: int
    ) -> None:
        loan = _active_loan(created_at, term)
        due = created_at + timedelta(days=term)
        assert loan.is_overdue(due) is False
        assert loan.is_overdue(due + timedelta(microseconds=1)) is True

    @given(created_at=moment_strategy, term=term_strategy)
    @settings(max_examples=50)
    def test_returning_clears_overdue_state(self, created_at: datetime, term: int) -> None:
        loan = _active_loan(created_at, term)
        returned = loan.mark_returned()
        assert returned.is_overdue(created_at + timedelta(days=term + 1)) is False
