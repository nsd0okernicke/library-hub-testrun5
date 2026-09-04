"""Use case for returning a borrowed book (closing an ACTIVE loan)."""

from loans.domain.events import BookReturned
from loans.domain.exceptions import LoanNotFound
from loans.domain.loan import Loan
from loans.domain.ports import EventPublisher, LoanRepository


class ReturnBook:
    """Return the book of an ACTIVE loan.

    The return never checks overdue status: an ACTIVE loan past its due date
    is returned just like one before its due date (no penalty in the MVP).
    """

    def __init__(self, loan_repository: LoanRepository, publisher: EventPublisher) -> None:
        """Store the loan repository and the event publisher."""
        self._loan_repository = loan_repository
        self._publisher = publisher

    def __call__(self, loan_id: str) -> Loan:
        """Mark the loan RETURNED, persist it and publish BookReturned.

        Raises LoanNotFound for an unknown loan and LoanNotActive when the
        loan is PENDING, REJECTED or already RETURNED.
        """
        loan = self._loan_repository.get_by_id(loan_id)
        if loan is None:
            raise LoanNotFound(loan_id)
        returned = loan.mark_returned()
        self._loan_repository.save(returned)
        self._publisher.publish(
            BookReturned(loan_id=returned.loan_id, user_id=returned.user_id, isbn=returned.isbn)
        )
        return returned
