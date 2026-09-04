"""Unit tests for the ManualStockReturn use case (mocked repository port)."""

import pytest

from catalog.application.return_stock import ManualStockReturn
from catalog.domain.book import Book
from catalog.domain.exceptions import BookNotFound


class FakeBookRepository:
    """In-memory fake of the BookRepository port that records saves."""

    def __init__(self, books: dict[str, Book] | None = None) -> None:
        self.books = books or {}
        self.saved: list[Book] = []

    def save(self, book: Book) -> None:
        self.books[book.isbn] = book
        self.saved.append(book)

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.books.get(isbn)

    def count_by_isbn(self, isbn: str) -> int:
        return 1 if isbn in self.books else 0


@pytest.fixture
def dune() -> Book:
    return Book(
        isbn="978-0-20-163361-0",
        title="Dune",
        author="Frank Herbert",
        genre="Sci-Fi",
        description="Arrakis saga",
        stock=3,
    )


@pytest.fixture
def repository(dune: Book) -> FakeBookRepository:
    return FakeBookRepository({dune.isbn: dune})


class TestManualStockReturn:
    def test_returns_book_with_increased_stock(
        self, repository: FakeBookRepository, dune: Book
    ) -> None:
        use_case = ManualStockReturn(repository)
        result = use_case(dune.isbn, 2)
        assert result.stock == 5

    def test_persists_the_updated_book(self, repository: FakeBookRepository, dune: Book) -> None:
        use_case = ManualStockReturn(repository)
        use_case(dune.isbn, 5)
        assert repository.saved == [
            Book(
                isbn=dune.isbn,
                title=dune.title,
                author=dune.author,
                genre=dune.genre,
                description=dune.description,
                stock=8,
            )
        ]
        assert repository.get_by_isbn(dune.isbn).stock == 8

    def test_metadata_is_not_touched(self, repository: FakeBookRepository, dune: Book) -> None:
        use_case = ManualStockReturn(repository)
        result = use_case(dune.isbn, 1)
        assert (result.title, result.author, result.genre, result.description) == (
            dune.title,
            dune.author,
            dune.genre,
            dune.description,
        )

    def test_works_from_zero_stock(self) -> None:
        book = Book(
            isbn="978-3-16-148410-0",
            title="The Hobbit",
            author="J.R.R. Tolkien",
            genre="Fantasy",
            description=None,
            stock=0,
        )
        repository = FakeBookRepository({book.isbn: book})
        result = ManualStockReturn(repository)(book.isbn, 5)
        assert result.stock == 5

    def test_unknown_isbn_raises_book_not_found(self, repository: FakeBookRepository) -> None:
        use_case = ManualStockReturn(repository)
        with pytest.raises(BookNotFound):
            use_case("978-1-40-289462-6", 3)

    def test_unknown_isbn_message_contains_isbn(self, repository: FakeBookRepository) -> None:
        use_case = ManualStockReturn(repository)
        with pytest.raises(BookNotFound, match="978-1-40-289462-6"):
            use_case("978-1-40-289462-6", 3)

    def test_unknown_isbn_saves_nothing(self, repository: FakeBookRepository) -> None:
        use_case = ManualStockReturn(repository)
        with pytest.raises(BookNotFound):
            use_case("978-1-40-289462-6", 3)
        assert repository.saved == []

    @pytest.mark.parametrize("copies", [0, -2, -1])
    def test_non_positive_copies_rejected_with_value_error(
        self, repository: FakeBookRepository, dune: Book, copies: int
    ) -> None:
        use_case = ManualStockReturn(repository)
        with pytest.raises(ValueError):
            use_case(dune.isbn, copies)

    @pytest.mark.parametrize("copies", [0, -2])
    def test_rejection_leaves_the_book_unchanged(
        self, repository: FakeBookRepository, dune: Book, copies: int
    ) -> None:
        use_case = ManualStockReturn(repository)
        with pytest.raises(ValueError):
            use_case(dune.isbn, copies)
        assert repository.get_by_isbn(dune.isbn).stock == dune.stock
        assert repository.saved == []

    def test_rejection_message_contains_amount(self, repository: FakeBookRepository) -> None:
        use_case = ManualStockReturn(repository)
        book = next(iter(repository.books.values()))
        with pytest.raises(ValueError, match="-2"):
            use_case(book.isbn, -2)
