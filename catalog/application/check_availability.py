"""Catalog use case for checking a book's availability by ISBN."""

from catalog.domain.availability import BookAvailability
from catalog.domain.exceptions import BookNotFound
from catalog.domain.ports import BookRepository


class CheckBookAvailability:
    """Return the lightweight availability (ISBN + available count) of a book.

    Raises BookNotFound when no book is registered under the given ISBN.
    """

    def __init__(self, repository: BookRepository) -> None:
        """Store the book repository used to look up books."""
        self._repository = repository

    def __call__(self, isbn: str) -> BookAvailability:
        """Return the availability for the ISBN, or raise BookNotFound."""
        book = self._repository.get_by_isbn(isbn)
        if book is None:
            raise BookNotFound(isbn)
        return BookAvailability(isbn=isbn, available_count=book.stock)
