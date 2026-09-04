"""Property tests for the CheckBookAvailability use case (in-memory fake repository)."""

from hypothesis import given, settings
from hypothesis import strategies as st

from catalog.application.check_availability import CheckBookAvailability
from catalog.application.create_book import CreateBook
from catalog.domain.availability import BookAvailability
from catalog.domain.book import Book
from catalog.domain.exceptions import BookNotFound


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


isbn_data = st.from_regex(r"97[89]-[0-9]-[0-9]{1,7}-[0-9]{1,7}-[0-9]", fullmatch=True)


class TestCheckBookAvailabilityProperties:
    @settings(max_examples=50)
    @given(
        isbn=isbn_data,
        title=st.text(min_size=1, max_size=50),
        author=st.text(min_size=1, max_size=50),
        genre=st.text(min_size=1, max_size=30),
        description=st.one_of(st.none(), st.text(max_size=200)),
        stock=st.integers(min_value=0, max_value=10_000),
    )
    def test_availability_matches_the_registered_stock(
        self,
        isbn: str,
        title: str,
        author: str,
        genre: str,
        description: str | None,
        stock: int,
    ) -> None:
        repository = InMemoryBookRepository()
        CreateBook(repository)(isbn, title, author, genre, description, stock)
        result = CheckBookAvailability(repository)(isbn)
        assert result == BookAvailability(isbn=isbn, available_count=stock)

    @given(isbn=isbn_data, other_isbn=isbn_data)
    @settings(max_examples=50)
    def test_checking_an_unregistered_isbn_always_raises(self, isbn: str, other_isbn: str) -> None:
        repository = InMemoryBookRepository()
        CreateBook(repository)(isbn, "Dune", "Frank Herbert", "Sci-Fi", None, 3)
        if other_isbn == isbn:
            return
        try:
            CheckBookAvailability(repository)(other_isbn)
            raise AssertionError("expected BookNotFound")
        except BookNotFound as exc:
            assert exc.isbn == other_isbn

    @given(isbn=isbn_data)
    @settings(max_examples=25)
    def test_checking_availability_is_read_only(self, isbn: str) -> None:
        repository = InMemoryBookRepository()
        CreateBook(repository)(isbn, "Dune", "Frank Herbert", "Sci-Fi", None, 7)
        CheckBookAvailability(repository)(isbn)
        book = repository.get_by_isbn(isbn)
        assert book is not None
        assert book.stock == 7
