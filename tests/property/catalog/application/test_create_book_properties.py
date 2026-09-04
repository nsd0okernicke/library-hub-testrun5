"""Property tests for the CreateBook use case (in-memory fake repository)."""

from typing import Any

from hypothesis import given, settings
from hypothesis import strategies as st

from catalog.application.create_book import CreateBook
from catalog.domain.book import Book
from catalog.domain.exceptions import BookAlreadyExists


class InMemoryBookRepository:
    """In-memory fake of the BookRepository port."""

    def __init__(self) -> None:
        self.books: dict[str, Book] = {}

    def save(self, book: Book) -> None:
        self.books[book.isbn] = book

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.books.get(isbn)

    def count_by_isbn(self, isbn: str) -> int:
        return 1 if isbn in self.books else 0


request_data = st.builds(
    lambda isbn, title, author, genre, description, stock: (
        isbn,
        title,
        author,
        genre,
        description,
        stock,
    ),
    isbn=st.from_regex(r"97[89]-[0-9]-[0-9]{1,7}-[0-9]{1,7}-[0-9]", fullmatch=True),
    title=st.text(min_size=1, max_size=50),
    author=st.text(min_size=1, max_size=50),
    genre=st.text(min_size=1, max_size=30),
    description=st.one_of(st.none(), st.text(max_size=200)),
    stock=st.integers(min_value=0, max_value=10_000),
)


class TestCreateBookProperties:
    @given(request=request_data)
    @settings(max_examples=50)
    def test_created_book_is_retrievable_with_identical_fields(self, request: Any) -> None:
        repository = InMemoryBookRepository()
        use_case = CreateBook(repository)
        isbn, title, author, genre, description, stock = request
        result = use_case(isbn, title, author, genre, description, stock)
        fetched = repository.get_by_isbn(isbn)
        assert fetched is not None
        assert (
            fetched.isbn,
            fetched.title,
            fetched.author,
            fetched.genre,
            fetched.description,
            fetched.stock,
        ) == (isbn, title, author, genre, description, stock)
        assert fetched == result

    @given(request=request_data)
    @settings(max_examples=50)
    def test_second_creation_with_same_isbn_is_always_rejected(self, request: Any) -> None:
        repository = InMemoryBookRepository()
        use_case = CreateBook(repository)
        isbn, title, author, genre, description, stock = request
        first = use_case(isbn, title, author, genre, description, stock)
        try:
            use_case(isbn, title, author, genre, description, stock)
            raise AssertionError("expected BookAlreadyExists")
        except BookAlreadyExists:
            pass
        assert repository.get_by_isbn(isbn) == first
        assert repository.count_by_isbn(isbn) == 1
