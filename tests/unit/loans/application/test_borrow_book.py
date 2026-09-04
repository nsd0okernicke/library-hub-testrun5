"""Unit tests for the BorrowBook use case (mocked ports, no I/O)."""

from datetime import datetime

import pytest

from loans.application.borrow_book import BorrowBook
from loans.domain.events import BorrowRequested
from loans.domain.exceptions import UserNotFound
from loans.domain.loan import Loan, LoanStatus
from loans.domain.user import User


class FakeUserRepository:
    """In-memory fake of the UserRepository port."""

    def __init__(self) -> None:
        self.users: dict[str, User] = {}

    def save(self, user: User) -> None:
        self.users[user.email] = user

    def get_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    def count_by_email(self, email: str) -> int:
        return 1 if email in self.users else 0

    def count(self) -> int:
        return len(self.users)


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


class RecordingPublisher:
    """Fake EventPublisher that records every published event."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def publish(self, event: object) -> None:
        self.events.append(event)


@pytest.fixture
def user_repository() -> FakeUserRepository:
    repository = FakeUserRepository()
    repository.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
    return repository


@pytest.fixture
def loan_repository() -> FakeLoanRepository:
    return FakeLoanRepository()


@pytest.fixture
def publisher() -> RecordingPublisher:
    return RecordingPublisher()


@pytest.fixture
def use_case(
    user_repository: FakeUserRepository,
    loan_repository: FakeLoanRepository,
    publisher: RecordingPublisher,
) -> BorrowBook:
    return BorrowBook(user_repository, loan_repository, publisher)


class TestBorrowBook:
    def test_creates_pending_loan_with_generated_id(
        self, use_case: BorrowBook, loan_repository: FakeLoanRepository
    ) -> None:
        loan = use_case(user_email="alice@example.com", isbn="978-0-20-163361-0")
        assert loan.status is LoanStatus.PENDING
        assert loan.due_date is None
        assert loan.user_id == "usr-1"
        assert loan.isbn == "978-0-20-163361-0"
        assert loan.loan_id
        assert loan_repository.get_by_id(loan.loan_id) is loan

    def test_two_borrows_get_different_loan_ids(self, use_case: BorrowBook) -> None:
        first = use_case(user_email="alice@example.com", isbn="978-0-20-163361-0")
        second = use_case(user_email="alice@example.com", isbn="978-0-20-163361-0")
        assert first.loan_id != second.loan_id

    def test_publishes_borrow_requested_event(
        self, use_case: BorrowBook, publisher: RecordingPublisher
    ) -> None:
        loan = use_case(user_email="alice@example.com", isbn="978-0-20-163361-0")
        assert len(publisher.events) == 1
        event = publisher.events[0]
        assert isinstance(event, BorrowRequested)
        assert event.loan_id == loan.loan_id
        assert event.user_id == "usr-1"
        assert event.isbn == "978-0-20-163361-0"

    def test_unknown_user_is_rejected(
        self, use_case: BorrowBook, loan_repository: FakeLoanRepository
    ) -> None:
        with pytest.raises(UserNotFound):
            use_case(user_email="nobody@example.com", isbn="978-0-20-163361-0")
        assert loan_repository.count() == 0

    def test_no_event_published_when_user_is_unknown(
        self, use_case: BorrowBook, publisher: RecordingPublisher
    ) -> None:
        with pytest.raises(UserNotFound):
            use_case(user_email="nobody@example.com", isbn="978-0-20-163361-0")
        assert publisher.events == []

    def test_created_at_comes_from_injected_clock(self) -> None:
        fixed = datetime(2026, 5, 4, 8, 0, 0)
        users = FakeUserRepository()
        users.save(User(user_id="usr-9", name="Bob", email="bob@example.com"))
        use_case = BorrowBook(
            users, FakeLoanRepository(), RecordingPublisher(), clock=lambda: fixed
        )
        loan = use_case(user_email="bob@example.com", isbn="978-3-16-148410-0")
        assert loan.created_at == fixed
