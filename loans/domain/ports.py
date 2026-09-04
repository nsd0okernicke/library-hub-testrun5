"""Port interfaces for the loans context."""

import abc

from loans.domain.loan import Loan
from loans.domain.user import User


class UserRepository(abc.ABC):
    """Persistence port for loan user accounts (one account per email)."""

    @abc.abstractmethod
    def save(self, user: User) -> None:
        """Persist a new user account."""

    @abc.abstractmethod
    def get_by_email(self, email: str) -> User | None:
        """Return the registered user for an email, or None."""

    @abc.abstractmethod
    def count_by_email(self, email: str) -> int:
        """Return how many users are registered under an email."""

    @abc.abstractmethod
    def count(self) -> int:
        """Return the total number of registered users."""


class LoanRepository(abc.ABC):
    """Persistence port for loans (a user may hold several loans for the same book)."""

    @abc.abstractmethod
    def save(self, loan: Loan) -> None:
        """Persist a new or updated loan (one row per loan_id)."""

    @abc.abstractmethod
    def get_by_id(self, loan_id: str) -> Loan | None:
        """Return the loan for a loan_id, or None (any status is queryable)."""

    @abc.abstractmethod
    def count(self) -> int:
        """Return the total number of stored loans."""


class EventPublisher(abc.ABC):
    """Outbound port for publishing domain events (e.g. borrow requests)."""

    @abc.abstractmethod
    def publish(self, event: object) -> None:
        """Publish a domain event to the message broker."""
