"""Port interfaces for the loans context."""

import abc

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
