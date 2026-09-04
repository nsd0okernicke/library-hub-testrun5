"""FastAPI application for the catalog service."""

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine

from catalog.application.check_availability import CheckBookAvailability
from catalog.application.create_book import CreateBook
from catalog.application.retrieve_book import RetrieveBook
from catalog.application.search_books import SearchBooks
from catalog.domain.book import Book
from catalog.domain.exceptions import BookAlreadyExists, BookNotFound
from catalog.domain.ports import BookRepository
from catalog.infrastructure.persistence import Base, SqlAlchemyBookRepository


class CreateBookRequest(BaseModel):
    """Request body for registering a new book."""

    isbn: str
    title: str
    author: str
    genre: str
    description: str | None = None
    stock: int


def _book_payload(book: Book) -> dict[str, object]:
    """Serialize a book into the API response body."""
    return {
        "isbn": book.isbn,
        "title": book.title,
        "author": book.author,
        "genre": book.genre,
        "description": book.description,
        "stock": book.stock,
    }


def create_app(repository: BookRepository) -> FastAPI:
    """Build the catalog FastAPI application around the given repository."""
    app = FastAPI(title="Catalog Service")
    create_book = CreateBook(repository)
    retrieve_book = RetrieveBook(repository)
    check_book_availability = CheckBookAvailability(repository)
    search_books = SearchBooks(repository)

    @app.get("/books")
    def search_books_endpoint(
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, object]:
        """Search books by optional case-insensitive substring filters, paginated."""
        try:
            result = search_books(
                title=title or None,
                author=author or None,
                genre=genre or None,
                page=page,
                page_size=page_size,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return {
            "total": result.total_count,
            "books": [_book_payload(book) for book in result.items],
        }

    @app.get("/books/{isbn}/availability")
    def availability_endpoint(isbn: str) -> dict[str, object]:
        """Return the lightweight availability (ISBN + available count) for an ISBN.

        404 when the ISBN is unregistered.
        """
        try:
            availability = check_book_availability(isbn)
        except BookNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "isbn": availability.isbn,
            "available_count": availability.available_count,
        }

    @app.get("/books/{isbn}")
    def retrieve_book_endpoint(isbn: str) -> dict[str, object]:
        """Return the registered book for an ISBN (404 when unregistered)."""
        try:
            book = retrieve_book(isbn)
        except BookNotFound as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _book_payload(book)

    @app.post("/books", status_code=201)
    def create_book_endpoint(request: CreateBookRequest) -> dict[str, object]:
        """Register a new book (201) or reject a duplicate ISBN (409)."""
        try:
            book = create_book(
                isbn=request.isbn,
                title=request.title,
                author=request.author,
                genre=request.genre,
                description=request.description,
                stock=request.stock,
            )
        except BookAlreadyExists as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _book_payload(book)

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok"}

    return app


def _default_repository() -> SqlAlchemyBookRepository:
    """Build the repository from CATALOG_DATABASE_URL."""
    url = os.environ.get(
        "CATALOG_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/libraryhub_catalog",
    )
    return SqlAlchemyBookRepository(create_engine(url))


def init_db(engine_url: str | None = None) -> None:
    """Create catalog tables in the configured database."""
    url = engine_url or os.environ.get(
        "CATALOG_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/libraryhub_catalog",
    )
    Base.metadata.create_all(create_engine(url))


app = create_app(_default_repository())

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
