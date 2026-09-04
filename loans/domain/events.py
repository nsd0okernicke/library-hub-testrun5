"""Domain events for the loans context."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BorrowRequested:
    """Published when a borrow request is accepted as a PENDING loan."""

    loan_id: str
    user_id: str
    isbn: str


@dataclass(frozen=True)
class BookReturned:
    """Published when an ACTIVE loan is returned (the book is back)."""

    loan_id: str
    user_id: str
    isbn: str
