"""Catalog use case for retrieving a single book by ISBN."""

from catalog.domain.book import Book
from catalog.domain.exceptions import BookNotFound
from catalog.domain.ports import BookRepository


class RetrieveBook:
    """Look up a registered book by its ISBN.

    Raises BookNotFound when no book is registered under the given ISBN.
    """

    def __init__(self, repository: BookRepository) -> None:
        """Store the book repository used to look up books."""
        self._repository = repository

    def __call__(self, isbn: str) -> Book:
        """Return the registered book for the ISBN, or raise BookNotFound."""
        book = self._repository.get_by_isbn(isbn)
        if book is None:
            raise BookNotFound(isbn)
        return book
