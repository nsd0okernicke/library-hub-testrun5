"""Catalog application use cases."""

from catalog.domain.book import Book
from catalog.domain.exceptions import BookAlreadyExists
from catalog.domain.ports import BookRepository


class CreateBook:
    """Register a new book in the catalog with its metadata and initial stock.

    Rejects the creation when the ISBN is already registered.
    """

    def __init__(self, repository: BookRepository) -> None:
        """Store the book repository used to check and persist books."""
        self._repository = repository

    def __call__(
        self,
        isbn: str,
        title: str,
        author: str,
        genre: str,
        description: str | None,
        stock: int,
    ) -> Book:
        """Create and persist the book, or raise BookAlreadyExists for a known ISBN."""
        if self._repository.get_by_isbn(isbn) is not None:
            raise BookAlreadyExists(isbn)
        book = Book(
            isbn=isbn,
            title=title,
            author=author,
            genre=genre,
            description=description,
            stock=stock,
        )
        self._repository.save(book)
        return book
