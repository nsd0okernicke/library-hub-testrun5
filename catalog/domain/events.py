"""Domain events consumed or emitted by the catalog context."""

from dataclasses import dataclass


@dataclass(frozen=True)
class BookReturnedEvent:
    """A book returned message received from the shared message broker.

    Published by the loans service when a book comes back; consumed here to
    increase the stock of the returned ISBN by one copy.
    """

    user_id: str
    isbn: str

    def __post_init__(self) -> None:
        """Enforce the event invariant (non-blank ISBN)."""
        if not self.isbn.strip():
            raise ValueError("ISBN must not be blank")
