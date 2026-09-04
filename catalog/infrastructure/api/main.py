"""FastAPI application for the catalog service."""

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine

from catalog.application.create_book import CreateBook
from catalog.domain.exceptions import BookAlreadyExists
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


def create_app(repository: BookRepository) -> FastAPI:
    """Build the catalog FastAPI application around the given repository."""
    app = FastAPI(title="Catalog Service")
    create_book = CreateBook(repository)

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
        return {
            "isbn": book.isbn,
            "title": book.title,
            "author": book.author,
            "genre": book.genre,
            "description": book.description,
            "stock": book.stock,
        }

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
