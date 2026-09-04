"""Unit tests for the loans domain events (pure Python, no I/O)."""

from dataclasses import FrozenInstanceError

import pytest

from loans.domain.events import BookReturned, BorrowRequested


def _event() -> BorrowRequested:
    return BorrowRequested(loan_id="loan-1", user_id="usr-1", isbn="978-0-20-163361-0")


class TestBorrowRequested:
    def test_carries_loan_id_user_id_isbn(self) -> None:
        event = _event()
        assert event.loan_id == "loan-1"
        assert event.user_id == "usr-1"
        assert event.isbn == "978-0-20-163361-0"

    def test_event_is_immutable(self) -> None:
        """BorrowRequested is a frozen value object: attribute assignment must fail."""
        event = _event()
        with pytest.raises(FrozenInstanceError):
            event.loan_id = "other"  # type: ignore[misc]


class TestBookReturned:
    def test_carries_loan_id_user_id_isbn(self) -> None:
        event = BookReturned(loan_id="loan-1", user_id="usr-1", isbn="978-0-20-163361-0")
        assert event.loan_id == "loan-1"
        assert event.user_id == "usr-1"
        assert event.isbn == "978-0-20-163361-0"

    def test_event_is_immutable(self) -> None:
        """BookReturned is a frozen value object: attribute assignment must fail."""
        event = BookReturned(loan_id="loan-1", user_id="usr-1", isbn="978-0-20-163361-0")
        with pytest.raises(FrozenInstanceError):
            event.isbn = "other"  # type: ignore[misc]
