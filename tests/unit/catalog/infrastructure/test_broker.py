"""Unit tests for the in-process broker adapter and its catalog app wiring."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from catalog.domain.book import Book
from catalog.domain.search import BookSearchCriteria, BookSearchResult
from catalog.infrastructure.api.main import create_app
from catalog.infrastructure.broker import InMemoryBroker


class InMemoryBookRepository:
    """In-memory fake of the BookRepository port for API unit tests."""

    def __init__(self) -> None:
        self.books: dict[str, Book] = {}

    def save(self, book: Book) -> None:
        self.books[book.isbn] = book

    def get_by_isbn(self, isbn: str) -> Book | None:
        return self.books.get(isbn)

    def count_by_isbn(self, isbn: str) -> int:
        return 1 if isbn in self.books else 0

    def search(self, criteria: BookSearchCriteria) -> BookSearchResult:
        """Filter by case-insensitive substring (AND), order by title, paginate."""
        matches = [b for b in self.books.values() if self._matches(b, criteria)]
        matches.sort(key=lambda b: b.title)
        start = (criteria.page - 1) * criteria.page_size
        return BookSearchResult(
            items=matches[start : start + criteria.page_size], total_count=len(matches)
        )

    @staticmethod
    def _matches(book: Book, criteria: BookSearchCriteria) -> bool:
        """Return True when every given filter matches the book's fields."""
        filters = (
            (criteria.title, "title"),
            (criteria.author, "author"),
            (criteria.genre, "genre"),
        )
        for value, field_name in filters:
            if value is not None and value.lower() not in getattr(book, field_name).lower():
                return False
        return True


def make_book(isbn: str, stock: int) -> Book:
    """Build a book with the given ISBN and stock."""
    return Book(
        isbn=isbn,
        title="Dune",
        author="Frank Herbert",
        genre="Sci-Fi",
        description=None,
        stock=stock,
    )


def returned_event(isbn: str) -> SimpleNamespace:
    """Build a loan-service shaped BookReturned wire event."""
    return SimpleNamespace(loan_id="loan-1", user_id="alice", isbn=isbn)


class TestInMemoryBroker:
    def test_publish_reaches_subscribers_in_order(self) -> None:
        broker = InMemoryBroker()
        received: list[object] = []
        broker.subscribe(lambda event: received.append(f"a:{event}"))
        broker.subscribe(lambda event: received.append(f"b:{event}"))

        broker.publish("evt")

        assert received == ["a:evt", "b:evt"]

    def test_publish_without_subscribers_is_a_noop(self) -> None:
        broker = InMemoryBroker()

        broker.publish("evt")


class TestAppBrokerWiring:
    def setup_method(self) -> None:
        self.repository = InMemoryBookRepository()
        self.broker = InMemoryBroker()
        self.app = create_app(self.repository, broker=self.broker)
        self.client = TestClient(self.app)

    def test_published_return_event_increases_stock(self) -> None:
        self.repository.save(make_book("978-0-20-163361-0", 0))

        self.broker.publish(returned_event("978-0-20-163361-0"))

        assert self.repository.get_by_isbn("978-0-20-163361-0") is not None
        assert self.repository.get_by_isbn("978-0-20-163361-0").stock == 1

    def test_multiple_events_each_add_one_copy(self) -> None:
        self.repository.save(make_book("978-0-20-163361-0", 1))

        self.broker.publish(returned_event("978-0-20-163361-0"))
        self.broker.publish(returned_event("978-0-20-163361-0"))

        assert self.repository.get_by_isbn("978-0-20-163361-0").stock == 3

    def test_unregistered_isbn_is_ignored(self) -> None:
        self.repository.save(make_book("978-0-20-163361-0", 4))

        self.broker.publish(returned_event("978-1-40-289462-6"))

        assert self.repository.get_by_isbn("978-1-40-289462-6") is None
        assert self.repository.get_by_isbn("978-0-20-163361-0").stock == 4

    def test_later_events_processed_after_unknown_isbn(self) -> None:
        self.repository.save(make_book("978-0-20-163361-0", 2))

        self.broker.publish(returned_event("978-1-40-289462-6"))
        self.broker.publish(returned_event("978-0-20-163361-0"))

        assert self.repository.get_by_isbn("978-1-40-289462-6") is None
        assert self.repository.get_by_isbn("978-0-20-163361-0").stock == 3

    def test_foreign_events_without_isbn_are_ignored(self) -> None:
        self.repository.save(make_book("978-0-20-163361-0", 5))

        self.broker.publish(SimpleNamespace(topic="other"))
        self.broker.publish(returned_event("978-0-20-163361-0"))

        assert self.repository.get_by_isbn("978-0-20-163361-0").stock == 6

    def test_app_without_broker_keeps_working(self) -> None:
        client = TestClient(create_app(InMemoryBookRepository()))

        assert client.get("/health").status_code == 200
