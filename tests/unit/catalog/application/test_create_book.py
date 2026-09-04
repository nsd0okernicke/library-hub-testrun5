"""Unit tests for the CreateBook use case (mocked repository port)."""

import pytest

from catalog.application.create_book import CreateBook
from catalog.domain.book import Book
from catalog.domain.exceptions import BookAlreadyExists


class FakeBookRepository:
    """In-memory fake of the BookRepository port."""

    def __init__(self) -> None:
        self.saved: list[Book] = []
        self.books: dict[str, Book] = {}

    def save(self, book: Book) -> None:
        self.saved.append(book)
        self.books[book.isbn] = book

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.books.get(isbn)

    def count_by_isbn(self, isbn: str) -> int:
        return sum(1 for b in self.saved if b.isbn == isbn)


@pytest.fixture
def repository() -> FakeBookRepository:
    return FakeBookRepository()


@pytest.fixture
def use_case(repository: FakeBookRepository) -> CreateBook:
    return CreateBook(repository)


class TestCreateBook:
    def test_creates_and_persists_book(
        self, use_case: CreateBook, repository: FakeBookRepository
    ) -> None:
        result = use_case(
            isbn="978-3-16-148410-0",
            title="Dune",
            author="Frank Herbert",
            genre="Sci-Fi",
            description="Arrakis saga",
            stock=5,
        )
        assert result == Book(
            isbn="978-3-16-148410-0",
            title="Dune",
            author="Frank Herbert",
            genre="Sci-Fi",
            description="Arrakis saga",
            stock=5,
        )
        assert len(repository.saved) == 1
        assert repository.get_by_isbn("978-3-16-148410-0") is result

    def test_missing_description_is_stored_as_none(
        self, use_case: CreateBook, repository: FakeBookRepository
    ) -> None:
        result = use_case(
            isbn="978-3-49-961840-5",
            title="Neuromancer",
            author="William Gibson",
            genre="Sci-Fi",
            description=None,
            stock=12,
        )
        assert repository.get_by_isbn("978-3-49-961840-5") == result
        assert result.description is None

    def test_rejects_duplicate_isbn(
        self, use_case: CreateBook, repository: FakeBookRepository
    ) -> None:
        existing = Book(
            isbn="978-3-16-148410-0",
            title="Dune",
            author="Frank Herbert",
            genre="Sci-Fi",
            description="Arrakis saga",
            stock=5,
        )
        repository.save(existing)
        with pytest.raises(BookAlreadyExists):
            use_case(
                isbn="978-3-16-148410-0",
                title="Dune",
                author="Frank Herbert",
                genre="Sci-Fi",
                description="Arrakis saga",
                stock=5,
            )
        assert len(repository.saved) == 1

    def test_invalid_isbn_is_rejected(self, use_case: CreateBook) -> None:
        with pytest.raises(ValueError):
            use_case(
                isbn="",
                title="Dune",
                author="Frank Herbert",
                genre="Sci-Fi",
                description=None,
                stock=1,
            )

    def test_negative_stock_is_rejected(self, use_case: CreateBook) -> None:
        with pytest.raises(ValueError):
            use_case(
                isbn="978-3-16-148410-0",
                title="Dune",
                author="Frank Herbert",
                genre="Sci-Fi",
                description=None,
                stock=-3,
            )
