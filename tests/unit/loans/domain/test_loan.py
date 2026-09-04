"""Unit tests for the Loan domain entity (pure Python, no I/O)."""

from datetime import datetime, timedelta

import pytest

from loans.domain.exceptions import LoanNotPending
from loans.domain.loan import Loan, LoanStatus, ReservationDecision, utc_now


def _pending_loan(**overrides: object) -> Loan:
    kwargs: dict[str, object] = {
        "loan_id": "loan-1",
        "user_id": "usr-1",
        "isbn": "978-0-20-163361-0",
        "status": LoanStatus.PENDING,
        "created_at": datetime(2026, 1, 1, 12, 0, 0),
        "due_date": None,
    }
    kwargs.update(overrides)
    return Loan(**kwargs)  # type: ignore[arg-type]


class TestLoanInvariants:
    def test_pending_loan_has_no_due_date(self) -> None:
        loan = _pending_loan()
        assert loan.status is LoanStatus.PENDING
        assert loan.due_date is None

    def test_blank_loan_id_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            _pending_loan(loan_id="   ")

    def test_blank_user_id_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            _pending_loan(user_id="")

    def test_blank_isbn_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            _pending_loan(isbn="")

    def test_active_loan_requires_due_date(self) -> None:
        with pytest.raises(ValueError):
            _pending_loan(status=LoanStatus.ACTIVE, due_date=None)

    def test_non_active_loan_cannot_have_due_date(self) -> None:
        with pytest.raises(ValueError):
            _pending_loan(status=LoanStatus.PENDING, due_date=datetime(2026, 2, 1))


class TestLoanActivation:
    def test_activate_sets_status_and_due_date_from_term(self) -> None:
        created = datetime(2026, 3, 1, 9, 30, 0)
        loan = _pending_loan(created_at=created)
        active = loan.activate(due_date_term_days=28)
        assert active.status is LoanStatus.ACTIVE
        assert active.due_date == created + timedelta(days=28)
        assert active.loan_id == loan.loan_id
        assert active.created_at == created

    def test_activate_does_not_mutate_the_original(self) -> None:
        loan = _pending_loan()
        loan.activate(due_date_term_days=7)
        assert loan.status is LoanStatus.PENDING
        assert loan.due_date is None

    def test_activate_with_non_positive_term_is_rejected(self) -> None:
        loan = _pending_loan()
        with pytest.raises(ValueError):
            loan.activate(due_date_term_days=0)
        with pytest.raises(ValueError):
            loan.activate(due_date_term_days=-3)


class TestLoanRejection:
    def test_reject_sets_status_rejected(self) -> None:
        loan = _pending_loan()
        rejected = loan.reject()
        assert rejected.status is LoanStatus.REJECTED
        assert rejected.due_date is None
        assert rejected.loan_id == loan.loan_id

    def test_reject_does_not_mutate_the_original(self) -> None:
        loan = _pending_loan()
        loan.reject()
        assert loan.status is LoanStatus.PENDING


class TestLoanTransitionGuards:
    def test_active_loan_cannot_be_activated_again(self) -> None:
        loan = _pending_loan().activate(due_date_term_days=28)
        with pytest.raises(LoanNotPending):
            loan.activate(due_date_term_days=7)

    def test_active_loan_cannot_be_rejected(self) -> None:
        loan = _pending_loan().activate(due_date_term_days=28)
        with pytest.raises(LoanNotPending):
            loan.reject()

    def test_rejected_loan_cannot_be_activated(self) -> None:
        loan = _pending_loan().reject()
        with pytest.raises(LoanNotPending):
            loan.activate(due_date_term_days=28)

    def test_rejected_loan_cannot_be_rejected_again(self) -> None:
        loan = _pending_loan().reject()
        with pytest.raises(LoanNotPending):
            loan.reject()

    def test_pending_loan_can_transition(self) -> None:
        assert _pending_loan().activate(due_date_term_days=7).status is LoanStatus.ACTIVE
        assert _pending_loan().reject().status is LoanStatus.REJECTED


class TestReservationDecision:
    def test_decision_members(self) -> None:
        assert ReservationDecision.ACTIVE.value == "ACTIVE"
        assert ReservationDecision.REJECTED.value == "REJECTED"

    def test_parse_from_string(self) -> None:
        assert ReservationDecision("ACTIVE") is ReservationDecision.ACTIVE
        assert ReservationDecision("REJECTED") is ReservationDecision.REJECTED

    def test_parse_unknown_string_fails(self) -> None:
        with pytest.raises(ValueError):
            ReservationDecision("MAYBE")


class TestUtcNow:
    def test_returns_naive_aware_of_now(self) -> None:
        now = utc_now()
        assert now.tzinfo is None
        assert (now + timedelta(minutes=1)) > now
