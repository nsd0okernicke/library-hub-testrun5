"""Unit tests for the DecideReservation use case (mocked ports, no I/O)."""

from datetime import datetime, timedelta

import pytest

from loans.application.decide_reservation import DecideReservation
from loans.domain.exceptions import LoanNotFound, LoanNotPending
from loans.domain.loan import Loan, LoanStatus, ReservationDecision


class FakeLoanRepository:
    """In-memory fake of the LoanRepository port."""

    def __init__(self) -> None:
        self.loans: dict[str, Loan] = {}

    def save(self, loan: Loan) -> None:
        self.loans[loan.loan_id] = loan

    def get_by_id(self, loan_id: str) -> Loan | None:
        return self.loans.get(loan_id)

    def count(self) -> int:
        return len(self.loans)


def _pending_loan(loan_id: str = "loan-1") -> Loan:
    return Loan(
        loan_id=loan_id,
        user_id="usr-1",
        isbn="978-0-20-163361-0",
        status=LoanStatus.PENDING,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        due_date=None,
    )


@pytest.fixture
def repository() -> FakeLoanRepository:
    return FakeLoanRepository()


@pytest.fixture
def use_case(repository: FakeLoanRepository) -> DecideReservation:
    return DecideReservation(repository, due_date_term_days=28)


class TestDecideReservation:
    def test_active_decision_activates_with_global_term(
        self, use_case: DecideReservation, repository: FakeLoanRepository
    ) -> None:
        loan = _pending_loan()
        repository.save(loan)
        decided = use_case(loan_id="loan-1", decision=ReservationDecision.ACTIVE)
        assert decided.status is LoanStatus.ACTIVE
        assert decided.due_date == loan.created_at + timedelta(days=28)
        assert repository.get_by_id("loan-1") is decided

    def test_active_decision_uses_currently_configured_term(
        self, repository: FakeLoanRepository
    ) -> None:
        loan = _pending_loan()
        repository.save(loan)
        use_case = DecideReservation(repository, due_date_term_days=7)
        decided = use_case(loan_id="loan-1", decision=ReservationDecision.ACTIVE)
        assert decided.due_date == loan.created_at + timedelta(days=7)

    def test_rejected_decision_rejects_loan(
        self, use_case: DecideReservation, repository: FakeLoanRepository
    ) -> None:
        loan = _pending_loan()
        repository.save(loan)
        decided = use_case(loan_id="loan-1", decision=ReservationDecision.REJECTED)
        assert decided.status is LoanStatus.REJECTED
        assert decided.due_date is None
        assert repository.get_by_id("loan-1") is decided

    def test_unknown_loan_is_rejected(self, use_case: DecideReservation) -> None:
        with pytest.raises(LoanNotFound):
            use_case(loan_id="nope", decision=ReservationDecision.ACTIVE)

    def test_deciding_an_already_decided_loan_fails(
        self, use_case: DecideReservation, repository: FakeLoanRepository
    ) -> None:
        loan = _pending_loan()
        repository.save(loan)
        use_case(loan_id="loan-1", decision=ReservationDecision.REJECTED)
        with pytest.raises(LoanNotPending):
            use_case(loan_id="loan-1", decision=ReservationDecision.ACTIVE)
