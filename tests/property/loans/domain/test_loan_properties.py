"""Property-based tests for the Loan domain invariants."""

from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from loans.domain.exceptions import LoanNotPending
from loans.domain.loan import Loan, LoanStatus

created_at_strategy = st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2100, 1, 1))
term_strategy = st.integers(min_value=1, max_value=3650)


def _pending_loan(created_at: datetime) -> Loan:
    return Loan(
        loan_id="loan-1",
        user_id="usr-1",
        isbn="978-0-20-163361-0",
        status=LoanStatus.PENDING,
        created_at=created_at,
        due_date=None,
    )


class TestLoanActivationProperties:
    @given(created_at=created_at_strategy, term=term_strategy)
    @settings(max_examples=50)
    def test_due_date_is_exactly_term_days_after_creation(
        self, created_at: datetime, term: int
    ) -> None:
        loan = _pending_loan(created_at).activate(due_date_term_days=term)
        assert loan.due_date is not None
        assert loan.due_date - created_at == timedelta(days=term)

    @given(created_at=created_at_strategy, term=term_strategy)
    @settings(max_examples=50)
    def test_activation_preserves_identity_fields(self, created_at: datetime, term: int) -> None:
        loan = _pending_loan(created_at)
        active = loan.activate(due_date_term_days=term)
        assert (active.loan_id, active.user_id, active.isbn) == (
            loan.loan_id,
            loan.user_id,
            loan.isbn,
        )
        assert active.created_at == created_at

    @given(created_at=created_at_strategy, term=st.integers(min_value=-100, max_value=0))
    @settings(max_examples=50)
    def test_non_positive_terms_are_rejected(self, created_at: datetime, term: int) -> None:
        with pytest.raises(ValueError):
            _pending_loan(created_at).activate(due_date_term_days=term)


class TestLoanDecisionProperties:
    @given(created_at=created_at_strategy)
    @settings(max_examples=50)
    def test_pending_loan_accepts_exactly_one_decision(self, created_at: datetime) -> None:
        loan = _pending_loan(created_at)
        first = loan.reject()
        assert first.status is LoanStatus.REJECTED
        with pytest.raises(LoanNotPending):
            first.activate(due_date_term_days=7)
        with pytest.raises(LoanNotPending):
            first.reject()

    @given(created_at=created_at_strategy)
    @settings(max_examples=50)
    def test_rejected_loan_never_has_due_date(self, created_at: datetime) -> None:
        assert _pending_loan(created_at).reject().due_date is None
