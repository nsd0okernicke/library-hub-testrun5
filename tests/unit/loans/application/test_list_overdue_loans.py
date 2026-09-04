"""Unit tests for the ListOverdueLoans use case (mocked ports, no I/O)."""

from datetime import datetime, timedelta

from loans.application.list_overdue_loans import ListOverdueLoans
from loans.domain.loan import Loan, LoanStatus, utc_now


def _active_loan(loan_id: str, user_id: str, isbn: str, due_date: datetime) -> Loan:
    return Loan(
        loan_id=loan_id,
        user_id=user_id,
        isbn=isbn,
        status=LoanStatus.ACTIVE,
        created_at=due_date - timedelta(days=28),
        due_date=due_date,
    )


def _pending_loan(loan_id: str, user_id: str, isbn: str) -> Loan:
    return Loan(
        loan_id=loan_id,
        user_id=user_id,
        isbn=isbn,
        status=LoanStatus.PENDING,
        created_at=utc_now(),
        due_date=None,
    )


class FakeLoanRepository:
    """In-memory fake of the LoanRepository port.

    ``list_overdue`` applies the port contract itself (status ACTIVE and
    due_date < now) so the use case is tested against the real semantics of
    the port, not against a mock that always returns what the test wants.
    """

    def __init__(self, loans: list[Loan]) -> None:
        self._loans = {loan.loan_id: loan for loan in loans}
        self.list_overdue_calls: list[datetime] = []

    def save(self, loan: Loan) -> None:
        self._loans[loan.loan_id] = loan

    def get_by_id(self, loan_id: str) -> Loan | None:
        return self._loans.get(loan_id)

    def list_for_user(self, query: object) -> list[Loan]:
        raise NotImplementedError

    def count(self) -> int:
        return len(self._loans)

    def list_overdue(self, now: datetime) -> list[Loan]:
        self.list_overdue_calls.append(now)
        return [loan for loan in self._loans.values() if loan.is_overdue(now)]


NOW = datetime(2026, 5, 1, 12, 0, 0)


def _repository() -> FakeLoanRepository:
    return FakeLoanRepository(
        [
            _active_loan("loan-overdue", "usr-1", "isbn-1", NOW - timedelta(days=3)),
            _active_loan("loan-due-later", "usr-2", "isbn-2", NOW + timedelta(days=1)),
            _pending_loan("loan-pending", "usr-3", "isbn-3"),
        ]
    )


class TestListOverdueLoans:
    def test_returns_only_overdue_loans(self) -> None:
        repository = _repository()
        overdue = ListOverdueLoans(repository)(now=NOW)
        assert [loan.loan_id for loan in overdue] == ["loan-overdue"]

    def test_loans_due_in_the_future_are_excluded(self) -> None:
        repository = _repository()
        overdue = ListOverdueLoans(repository)(now=NOW)
        assert all(loan.is_overdue(NOW) for loan in overdue)

    def test_no_overdue_loans_returns_an_empty_list(self) -> None:
        repository = FakeLoanRepository([_pending_loan("loan-pending", "usr-1", "isbn-1")])
        assert ListOverdueLoans(repository)(now=NOW) == []

    def test_default_now_is_the_current_moment(self) -> None:
        repository = FakeLoanRepository([])
        before = utc_now()
        ListOverdueLoans(repository)()
        after = utc_now()
        assert before <= repository.list_overdue_calls[0] <= after
