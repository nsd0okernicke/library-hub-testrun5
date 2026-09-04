"""Book catalog domain model."""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Book:
    """A book registered in the catalog with its metadata and available stock."""

    isbn: str
    title: str
    author: str
    genre: str
    description: str | None
    stock: int

    def __post_init__(self) -> None:
        """Enforce the Book invariants (non-blank ISBN, non-negative stock)."""
        if not self.isbn.strip():
            raise ValueError("ISBN must not be blank")
        if self.stock < 0:
            raise ValueError(f"Stock must not be negative, got {self.stock}")

    def add_copies(self, amount: int) -> "Book":
        """Return a new Book with `amount` copies added to the stock.

        Metadata is preserved. Raises ValueError when amount is not positive.
        """
        if amount <= 0:
            raise ValueError(f"Added copies must be a positive whole number, got {amount}")
        return replace(self, stock=self.stock + amount)
