"""Catalog use case for manual stock return (stock correction)."""

from catalog.domain.book import Book
from catalog.domain.exceptions import BookNotFound
from catalog.domain.ports import BookRepository


class ManualStockReturn:
    """Add copies to the stock of a registered book, independent of any loan.

    No loan record is read or created and no book-returned event is published.
    Raises ValueError for a non-positive number of copies and BookNotFound for
    an unregistered ISBN.
    """

    def __init__(self, repository: BookRepository) -> None:
        """Store the book repository used to look up and persist books."""
        self._repository = repository

    def __call__(self, isbn: str, copies: int) -> Book:
        """Add copies to the registered book's stock and persist the result."""
        book = self._repository.get_by_isbn(isbn)
        if book is None:
            raise BookNotFound(isbn)
        updated = book.add_copies(copies)
        self._repository.save(updated)
        return updated
