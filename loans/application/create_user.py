"""Use case for creating a loan user account."""

import uuid

from loans.domain.exceptions import EmailAlreadyRegistered
from loans.domain.ports import UserRepository
from loans.domain.user import User


class CreateUser:
    """Create a user account with a name and email and a system-generated user_id.

    Rejects the creation when the email is already registered.
    """

    def __init__(self, repository: UserRepository) -> None:
        """Store the user repository used to check and persist accounts."""
        self._repository = repository

    def __call__(self, name: str, email: str) -> User:
        """Create and persist the user, or raise EmailAlreadyRegistered for a known email."""
        if self._repository.get_by_email(email) is not None:
            raise EmailAlreadyRegistered(email)
        user = User(user_id=str(uuid.uuid4()), name=name, email=email)
        self._repository.save(user)
        return user
