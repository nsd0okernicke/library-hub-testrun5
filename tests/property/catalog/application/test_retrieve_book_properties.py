"""Property tests for the RetrieveBook use case (in-memory fake repository)."""

from hypothesis import given, settings
from hypothesis import strategies as st

from catalog.application.create_book import CreateBook
from catalog.application.retrieve_book import RetrieveBook
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


class TestRetrieveBookProperties:
    @settings(max_examples=50)
    @given(
        isbn=isbn_data,
        title=st.text(min_size=1, max_size=50),
        author=st.text(min_size=1, max_size=50),
        genre=st.text(min_size=1, max_size=30),
        description=st.one_of(st.none(), st.text(max_size=200)),
        stock=st.integers(min_value=0, max_value=10_000),
    )
    def test_retrieved_book_has_identical_fields(
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
        fetched = RetrieveBook(repository)(isbn)
        assert (
            fetched.isbn,
            fetched.title,
            fetched.author,
            fetched.genre,
            fetched.description,
            fetched.stock,
        ) == (isbn, title, author, genre, description, stock)

    @given(isbn=isbn_data, other_isbn=isbn_data)
    @settings(max_examples=50)
    def test_retrieving_an_unregistered_isbn_always_raises(
        self, isbn: str, other_isbn: str
    ) -> None:
        repository = InMemoryBookRepository()
        CreateBook(repository)(isbn, "Dune", "Frank Herbert", "Sci-Fi", None, 3)
        if other_isbn == isbn:
            return
        try:
            RetrieveBook(repository)(other_isbn)
            raise AssertionError("expected BookNotFound")
        except BookNotFound as exc:
            assert exc.isbn == other_isbn

    @given(isbn=isbn_data)
    @settings(max_examples=25)
    def test_retrieval_is_read_only(self, isbn: str) -> None:
        repository = InMemoryBookRepository()
        CreateBook(repository)(isbn, "Dune", "Frank Herbert", "Sci-Fi", None, 3)
        before = repository.books.get(isbn)
        RetrieveBook(repository)(isbn)
        RetrieveBook(repository)(isbn)
        assert repository.books.get(isbn) is before
        assert repository.count_by_isbn(isbn) == 1
