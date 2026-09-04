"""Loan domain model: a borrow request tracked by the loan service."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum

from loans.domain.exceptions import LoanNotActive, LoanNotPending


class LoanStatus(Enum):
    """Lifecycle states of a loan."""

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"


class ReservationDecision(Enum):
    """The reservation outcome the catalog can report for a pending loan."""

    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"


def utc_now() -> datetime:
    """Return the current time as a naive UTC datetime."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True)
class Loan:
    """A borrow request for one book by one user, identified by loan_id.

    A loan starts PENDING when the borrow request is accepted. The reservation
    outcome arrives later, asynchronously: ACTIVE sets the due date from the
    global due date term, REJECTED ends the loan without a due date. An ACTIVE
    loan can be returned at any time — overdue or not — which ends it as
    RETURNED. Every decided or returned loan stays queryable.
    """

    loan_id: str
    user_id: str
    isbn: str
    status: LoanStatus
    created_at: datetime
    due_date: datetime | None

    def __post_init__(self) -> None:
        """Enforce the Loan invariants (non-blank identifiers, consistent due date)."""
        if not self.loan_id.strip():
            raise ValueError("Loan ID must not be blank")
        if not self.user_id.strip():
            raise ValueError("User ID must not be blank")
        if not self.isbn.strip():
            raise ValueError("ISBN must not be blank")
        if self.status is LoanStatus.ACTIVE and self.due_date is None:
            raise ValueError("An ACTIVE loan must have a due date")
        if self.status is not LoanStatus.ACTIVE and self.due_date is not None:
            raise ValueError("Only an ACTIVE loan may have a due date")

    def _require_active(self) -> None:
        """Raise LoanNotActive when the loan is not an open (ACTIVE) loan."""
        if self.status is not LoanStatus.ACTIVE:
            raise LoanNotActive(self.loan_id)

    def _require_pending(self) -> None:
        """Raise LoanNotPending when a reservation outcome was already decided."""
        if self.status is not LoanStatus.PENDING:
            raise LoanNotPending(self.loan_id)

    def activate(self, due_date_term_days: int) -> "Loan":
        """Return a copy of this pending loan as ACTIVE with the global due date term.

        Raises ValueError for a non-positive term and LoanNotPending when the
        reservation outcome was already decided.
        """
        self._require_pending()
        if due_date_term_days < 1:
            raise ValueError("Due date term must be at least 1 day")
        return replace(
            self,
            status=LoanStatus.ACTIVE,
            due_date=self.created_at + timedelta(days=due_date_term_days),
        )

    def reject(self) -> "Loan":
        """Return a copy of this pending loan as REJECTED (no due date).

        Raises LoanNotPending when the reservation outcome was already decided.
        """
        self._require_pending()
        return replace(self, status=LoanStatus.REJECTED)

    def mark_returned(self) -> "Loan":
        """Return a copy of this ACTIVE loan as RETURNED (due date cleared).

        The return never checks overdue status: an ACTIVE loan past its due
        date is returned just like one before its due date. Raises
        LoanNotActive when the loan is PENDING, REJECTED or already RETURNED.
        """
        self._require_active()
        return replace(self, status=LoanStatus.RETURNED, due_date=None)
