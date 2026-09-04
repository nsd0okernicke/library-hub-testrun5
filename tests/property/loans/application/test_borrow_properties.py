"""Property-based tests for the BorrowBook and DecideReservation use cases."""

import uuid as uuid_module
from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from loans.application.borrow_book import BorrowBook
from loans.application.decide_reservation import DecideReservation
from loans.domain.events import BorrowRequested
from loans.domain.exceptions import LoanNotPending
from loans.domain.loan import Loan, LoanStatus, ReservationDecision
from loans.domain.user import User

isbn_strategy = st.from_regex(r"978-[0-9]{1,5}-[0-9]{1,7}-[0-9]{1,7}-[0-9]", fullmatch=True)
name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), min_codepoint=0x20),
    min_size=1,
    max_size=20,
)


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

    def list_overdue(self, now: datetime) -> list[Loan]:
        return [loan for loan in self.loans.values() if loan.is_overdue(now)]

    def count(self) -> int:
        return len(self.loans)


class RecordingPublisher:
    """Fake EventPublisher that records every published event."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def publish(self, event: object) -> None:
        self.events.append(event)


def _setup() -> tuple[BorrowBook, FakeUserRepository, FakeLoanRepository, RecordingPublisher]:
    users = FakeUserRepository()
    users.save(User(user_id="usr-1", name="Alice", email="alice@example.com"))
    loans = FakeLoanRepository()
    publisher = RecordingPublisher()
    return (
        BorrowBook(users, loans, publisher, clock=lambda: datetime(2026, 1, 1, 12, 0, 0)),
        users,
        loans,
        publisher,
    )


class TestBorrowBookProperties:
    @given(name=name_strategy, isbn=isbn_strategy)
    @settings(max_examples=25)
    def test_borrow_always_yields_a_stored_pending_loan(self, name: str, isbn: str) -> None:
        use_case, _, loans, _ = _setup()
        loan = use_case(user_email="alice@example.com", isbn=isbn)
        assert loan.status is LoanStatus.PENDING
        assert loan.user_id == "usr-1"
        assert loans.get_by_id(loan.loan_id) is loan

    @given(name=name_strategy, isbn=isbn_strategy)
    @settings(max_examples=25)
    def test_loan_ids_are_unique_and_uuid_format(self, name: str, isbn: str) -> None:
        use_case, _, _, _ = _setup()
        seen = set()
        for _ in range(3):
            loan = use_case(user_email="alice@example.com", isbn=isbn)
            assert loan.loan_id not in seen
            seen.add(loan.loan_id)
            uuid_module.UUID(loan.loan_id)

    @given(isbn=isbn_strategy)
    @settings(max_examples=25)
    def test_every_borrow_publishes_exactly_one_matching_event(self, isbn: str) -> None:
        use_case, _, _, publisher = _setup()
        use_case(user_email="alice@example.com", isbn=isbn)
        assert len(publisher.events) == 1
        event = publisher.events[0]
        assert isinstance(event, BorrowRequested)
        assert event.isbn == isbn and event.user_id == "usr-1"


class TestDecideReservationProperties:
    @given(term=st.integers(min_value=1, max_value=3650))
    @settings(max_examples=25)
    def test_active_decision_applies_the_global_term(self, term: int) -> None:
        use_case, _, loans, _ = _setup()
        loan = use_case(user_email="alice@example.com", isbn="978-0-20-163361-0")
        decided = DecideReservation(loans, due_date_term_days=term)(
            loan_id=loan.loan_id, decision=ReservationDecision.ACTIVE
        )
        assert decided.due_date is not None
        assert decided.due_date - loan.created_at == timedelta(days=term)
        assert loans.get_by_id(loan.loan_id) is decided

    @given(isbn=isbn_strategy)
    @settings(max_examples=25)
    def test_rejection_is_terminal_and_loan_stays_queryable(self, isbn: str) -> None:
        use_case, _, loans, _ = _setup()
        loan = use_case(user_email="alice@example.com", isbn=isbn)
        decide = DecideReservation(loans, due_date_term_days=28)
        rejected = decide(loan_id=loan.loan_id, decision=ReservationDecision.REJECTED)
        assert rejected.status is LoanStatus.REJECTED
        assert loans.get_by_id(loan.loan_id).status is LoanStatus.REJECTED
        with pytest.raises(LoanNotPending):
            decide(loan_id=loan.loan_id, decision=ReservationDecision.ACTIVE)
