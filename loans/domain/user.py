"""Loan user account domain model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """A library patron account identified by a system-generated user_id.

    No password or authentication is involved — name and email alone are sufficient.
    """

    user_id: str
    name: str
    email: str

    def __post_init__(self) -> None:
        """Enforce the User invariants (non-blank user_id, name, and email)."""
        if not self.user_id.strip():
            raise ValueError("User ID must not be blank")
        if not self.name.strip():
            raise ValueError("Name must not be blank")
        if not self.email.strip():
            raise ValueError("Email must not be blank")
