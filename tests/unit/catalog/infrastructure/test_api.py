"""Unit tests for the catalog FastAPI application (fake repository, no I/O)."""

from fastapi.testclient import TestClient

from catalog.domain.book import Book
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
