"""Unit tests for the ReturnBook use case (mocked ports, no I/O)."""

from datetime import datetime, timedelta

import pytest

from loans.application.return_book import ReturnBook
from loans.domain.events import BookReturned
from loans.domain.exceptions import LoanNotActive, LoanNotFound
from loans.domain.loan import Loan, LoanStatus


class FakeLoanRepository:
    """In-memory fake of the LoanRepository port."""

    def __init__(self) -> None:
        self.loans: dict[str, Loan] = {}

    def save(self, loan: Loan) -> None:
        self.loans[loan.loan_id] = loan

    def get_by_id(self, loan_id: str) -> Loan | None:
        return self.loans.get(loan_id)

    def list_overdue(self, now: datetime) -> list[Loan]:
        return [loan for loan in self.loans.values() if loan.is_overdue(now)]

    def count(self) -> int:
        return len(self.loans)


class RecordingPublisher:
    """In-memory fake of the EventPublisher port."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def publish(self, event: object) -> None:
        self.events.append(event)


def _active_loan(loan_id: str = "loan-1") -> Loan:
    return Loan(
        loan_id=loan_id,
        user_id="usr-1",
        isbn="978-0-20-163361-0",
        status=LoanStatus.ACTIVE,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        due_date=datetime(2026, 1, 29, 12, 0, 0),
    )


def _loan(status: LoanStatus) -> Loan:
    due = datetime(2026, 1, 29, 12, 0, 0) if status is LoanStatus.ACTIVE else None
    return Loan(
        loan_id="loan-1",
        user_id="usr-1",
        isbn="978-0-20-163361-0",
        status=status,
        created_at=datetime(2026, 1, 1, 12, 0, 0),
        due_date=due,
    )


@pytest.fixture
def repository() -> FakeLoanRepository:
    return FakeLoanRepository()


@pytest.fixture
def publisher() -> RecordingPublisher:
    return RecordingPublisher()


@pytest.fixture
def use_case(repository: FakeLoanRepository, publisher: RecordingPublisher) -> ReturnBook:
    return ReturnBook(repository, publisher)


class TestReturnBook:
    def test_returning_active_loan_marks_returned_and_publishes(
        self, use_case: ReturnBook, repository: FakeLoanRepository, publisher: RecordingPublisher
    ) -> None:
        loan = _active_loan()
        repository.save(loan)
        returned = use_case(loan_id="loan-1")
        assert returned.status is LoanStatus.RETURNED
        assert returned.due_date is None
        assert repository.get_by_id("loan-1") is returned
        assert publisher.events == [
            BookReturned(loan_id="loan-1", user_id="usr-1", isbn="978-0-20-163361-0")
        ]

    def test_returning_overdue_active_loan_succeeds_without_penalty(
        self, use_case: ReturnBook, repository: FakeLoanRepository
    ) -> None:
        # due_date is in the past: the return must still succeed.
        repository.save(
            Loan(
                loan_id="loan-1",
                user_id="usr-1",
                isbn="978-0-20-163361-0",
                status=LoanStatus.ACTIVE,
                created_at=datetime(2026, 1, 1, 12, 0, 0),
                due_date=datetime(2026, 1, 15, 12, 0, 0) + timedelta(days=-30),
            )
        )
        returned = use_case(loan_id="loan-1")
        assert returned.status is LoanStatus.RETURNED

    def test_unknown_loan_is_rejected(self, use_case: ReturnBook) -> None:
        with pytest.raises(LoanNotFound):
            use_case(loan_id="nope")

    def test_returning_a_pending_loan_fails_and_publishes_nothing(
        self, use_case: ReturnBook, repository: FakeLoanRepository, publisher: RecordingPublisher
    ) -> None:
        repository.save(_loan(LoanStatus.PENDING))
        with pytest.raises(LoanNotActive):
            use_case(loan_id="loan-1")
        assert repository.get_by_id("loan-1").status is LoanStatus.PENDING
        assert publisher.events == []

    def test_returning_a_rejected_loan_fails(
        self, use_case: ReturnBook, repository: FakeLoanRepository
    ) -> None:
        repository.save(_loan(LoanStatus.REJECTED))
        with pytest.raises(LoanNotActive):
            use_case(loan_id="loan-1")

    def test_returning_an_already_returned_loan_fails(
        self, use_case: ReturnBook, repository: FakeLoanRepository
    ) -> None:
        repository.save(_loan(LoanStatus.RETURNED))
        with pytest.raises(LoanNotActive):
            use_case(loan_id="loan-1")
