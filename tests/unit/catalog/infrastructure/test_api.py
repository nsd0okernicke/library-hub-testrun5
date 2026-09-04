"""Unit tests for the catalog FastAPI application (fake repository, no I/O)."""

from fastapi.testclient import TestClient

from catalog.domain.book import Book
from catalog.domain.search import BookSearchCriteria, BookSearchResult
from catalog.infrastructure.api.main import create_app


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
        """Return True when every given filter is a case-insensitive substring of the field."""
        filters = (
            (criteria.title, "title"),
            (criteria.author, "author"),
            (criteria.genre, "genre"),
        )
        for value, field_name in filters:
            if value is not None and value.lower() not in getattr(book, field_name).lower():
                return False
        return True


class TestCreateBookApi:
    def setup_method(self) -> None:
        self.repository = InMemoryBookRepository()
        self.app = create_app(self.repository)
        self.client = TestClient(self.app)

    def test_create_book_returns_201(self) -> None:
        response = self.client.post(
            "/books",
            json={
                "isbn": "978-3-16-148410-0",
                "title": "Dune",
                "author": "Frank Herbert",
                "genre": "Sci-Fi",
                "description": "Arrakis saga",
                "stock": 5,
            },
        )
        assert response.status_code == 201
        assert response.json()["isbn"] == "978-3-16-148410-0"
        assert response.json()["stock"] == 5

    def test_create_book_without_description(self) -> None:
        response = self.client.post(
            "/books",
            json={
                "isbn": "978-3-49-961840-5",
                "title": "Neuromancer",
                "author": "William Gibson",
                "genre": "Sci-Fi",
                "stock": 12,
            },
        )
        assert response.status_code == 201
        assert self.repository.get_by_isbn("978-3-49-961840-5").description is None

    def test_duplicate_isbn_returns_409(self) -> None:
        payload = {
            "isbn": "978-3-16-148410-0",
            "title": "Dune",
            "author": "Frank Herbert",
            "genre": "Sci-Fi",
            "stock": 5,
        }
        first = self.client.post("/books", json=payload)
        second = self.client.post("/books", json=payload)
        assert first.status_code == 201
        assert second.status_code == 409
        assert "already registered" in second.json()["detail"]


class TestRetrieveBookApi:
    def setup_method(self) -> None:
        self.repository = InMemoryBookRepository()
        self.app = create_app(self.repository)
        self.client = TestClient(self.app)
        self.book = Book(
            isbn="978-0-20-163361-0",
            title="Dune",
            author="Frank Herbert",
            genre="Sci-Fi",
            description="Arrakis saga",
            stock=3,
        )
        self.repository.save(self.book)

    def test_retrieve_by_isbn_returns_200_with_full_metadata(self) -> None:
        response = self.client.get("/books/978-0-20-163361-0")
        assert response.status_code == 200
        assert response.json() == {
            "isbn": "978-0-20-163361-0",
            "title": "Dune",
            "author": "Frank Herbert",
            "genre": "Sci-Fi",
            "description": "Arrakis saga",
            "stock": 3,
        }

    def test_retrieve_book_without_description(self) -> None:
        self.repository.save(
            Book(
                isbn="978-0-13-468599-1",
                title="Refactoring",
                author="Martin Fowler",
                genre="Software",
                description=None,
                stock=0,
            )
        )
        response = self.client.get("/books/978-0-13-468599-1")
        assert response.status_code == 200
        assert response.json()["description"] is None
        assert response.json()["stock"] == 0

    def test_retrieve_unknown_isbn_returns_404(self) -> None:
        response = self.client.get("/books/978-1-40-289462-6")
        assert response.status_code == 404

    def test_retrieve_unknown_isbn_returns_no_book_data(self) -> None:
        response = self.client.get("/books/978-1-40-289462-6")
        body = response.json()
        assert "isbn" not in body
        assert "title" not in body


class TestSearchBooksApi:
    def setup_method(self) -> None:
        self.repository = InMemoryBookRepository()
        self.app = create_app(self.repository)
        self.client = TestClient(self.app)
        for isbn, title, author, genre in (
            ("978-0-20-163361-0", "Dune", "Frank Herbert", "Sci-Fi"),
            ("978-0-13-468599-1", "Refactoring", "Martin Fowler", "Software"),
            ("978-3-16-148410-0", "The Hobbit", "J.R.R. Tolkien", "Fantasy"),
        ):
            self.repository.save(
                Book(isbn=isbn, title=title, author=author, genre=genre, description=None, stock=1)
            )

    def test_search_without_filters_returns_all_books_sorted_by_title(self) -> None:
        response = self.client.get("/books")
        assert response.status_code == 200
        body = response.json()
        assert [book["title"] for book in body["books"]] == ["Dune", "Refactoring", "The Hobbit"]
        assert body["total"] == 3

    def test_search_payload_includes_isbn_title_author_genre_and_stock(self) -> None:
        response = self.client.get("/books", params={"title": "dune"})
        body = response.json()
        assert body["total"] == 1
        book = body["books"][0]
        assert book["isbn"] == "978-0-20-163361-0"
        assert book["title"] == "Dune"
        assert book["author"] == "Frank Herbert"
        assert book["genre"] == "Sci-Fi"
        assert isinstance(book["stock"], int)

    def test_single_filter_is_case_insensitive_substring(self) -> None:
        for field, value in (
            ("title", "the"),
            ("author", "FOWLER"),
            ("genre", "fantasy"),
        ):
            body = self.client.get("/books", params={field: value}).json()
            assert body["total"] == 1
            assert body["books"][0]["title"] in ("The Hobbit", "Refactoring", "The Hobbit")

    def test_multiple_filters_combine_with_and(self) -> None:
        body = self.client.get(
            "/books", params={"title": "the", "author": "Tolkien", "genre": "fantasy"}
        ).json()
        assert body["total"] == 1
        empty = self.client.get("/books", params={"title": "the", "author": "fowler"}).json()
        assert empty["books"] == []
        assert empty["total"] == 0

    def test_search_without_match_is_empty_with_zero_total(self) -> None:
        response = self.client.get("/books", params={"title": "nonexistent"})
        assert response.status_code == 200
        body = response.json()
        assert body["books"] == []
        assert body["total"] == 0

    def test_pagination_slices_the_sorted_results(self) -> None:
        first = self.client.get("/books", params={"page": 1, "page_size": 2}).json()
        assert [book["title"] for book in first["books"]] == ["Dune", "Refactoring"]
        assert first["total"] == 3
        second = self.client.get("/books", params={"page": 2, "page_size": 2}).json()
        assert [book["title"] for book in second["books"]] == ["The Hobbit"]
        assert second["total"] == 3

    def test_page_beyond_the_last_page_is_empty_with_kept_total(self) -> None:
        body = self.client.get("/books", params={"page": 4, "page_size": 1}).json()
        assert body["books"] == []
        assert body["total"] == 3

    def test_invalid_pagination_returns_422(self) -> None:
        assert self.client.get("/books", params={"page": 0}).status_code == 422
        assert self.client.get("/books", params={"page_size": 0}).status_code == 422


class TestCheckAvailabilityApi:
    def setup_method(self) -> None:
        self.repository = InMemoryBookRepository()
        self.app = create_app(self.repository)
        self.client = TestClient(self.app)
        self.repository.save(
            Book(
                isbn="978-0-20-163361-0",
                title="Dune",
                author="Frank Herbert",
                genre="Sci-Fi",
                description="Arrakis saga",
                stock=3,
            )
        )

    def test_availability_returns_200_with_isbn_and_available_count(self) -> None:
        response = self.client.get("/books/978-0-20-163361-0/availability")
        assert response.status_code == 200
        assert response.json() == {
            "isbn": "978-0-20-163361-0",
            "available_count": 3,
        }

    def test_availability_reports_zero_stock(self) -> None:
        self.repository.save(
            Book(
                isbn="978-0-13-468599-1",
                title="Refactoring",
                author="Martin Fowler",
                genre="Software",
                description=None,
                stock=0,
            )
        )
        response = self.client.get("/books/978-0-13-468599-1/availability")
        assert response.status_code == 200
        assert response.json()["available_count"] == 0

    def test_availability_contains_no_other_book_details(self) -> None:
        body = self.client.get("/books/978-0-20-163361-0/availability").json()
        assert set(body) == {"isbn", "available_count"}

    def test_availability_of_unknown_isbn_returns_404(self) -> None:
        response = self.client.get("/books/978-1-40-289462-6/availability")
        assert response.status_code == 404
        assert "isbn" not in response.json()

    def test_availability_of_unknown_isbn_returns_no_availability_data(self) -> None:
        body = self.client.get("/books/978-1-40-289462-6/availability").json()
        assert "isbn" not in body
        assert "available_count" not in body
