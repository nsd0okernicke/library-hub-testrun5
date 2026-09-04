"""Use case for requesting a book for borrowing."""

import uuid
from collections.abc import Callable
from datetime import datetime

from loans.domain.events import BorrowRequested
from loans.domain.exceptions import UserNotFound
from loans.domain.loan import Loan, LoanStatus, utc_now
from loans.domain.ports import EventPublisher, LoanRepository, UserRepository


class BorrowBook:
    """Accept a borrow request: create a PENDING loan and publish BorrowRequested.

    The loan service answers immediately; the reservation outcome (ACTIVE/REJECTED)
    arrives later, asynchronously. A user's existing active loans do not limit
    new borrow requests.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        loan_repository: LoanRepository,
        event_publisher: EventPublisher,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Store the ports and the clock used to stamp created_at (UTC)."""
        self._user_repository = user_repository
        self._loan_repository = loan_repository
        self._event_publisher = event_publisher
        self._clock = clock or utc_now

    def __call__(self, user_email: str, isbn: str) -> Loan:
        """Create and persist a PENDING loan for the user, publish the event, return it.

        Raises UserNotFound when no account exists for the email.
        """
        user = self._user_repository.get_by_email(user_email)
        if user is None:
            raise UserNotFound(user_email)
        loan = Loan(
            loan_id=str(uuid.uuid4()),
            user_id=user.user_id,
            isbn=isbn,
            status=LoanStatus.PENDING,
            created_at=self._clock(),
            due_date=None,
        )
        self._loan_repository.save(loan)
        self._event_publisher.publish(
            BorrowRequested(loan_id=loan.loan_id, user_id=user.user_id, isbn=isbn)
        )
        return loan
