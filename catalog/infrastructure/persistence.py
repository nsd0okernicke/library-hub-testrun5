"""SQLAlchemy persistence for books."""

from sqlalchemy import Integer, String, Text, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from catalog.domain.book import Book
from catalog.domain.ports import BookRepository


class Base(DeclarativeBase):
    """Declarative base for catalog persistence models."""


class BookModel(Base):
    """Table model for registered books (one row per ISBN)."""

    __tablename__ = "books"

    isbn: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255))
    genre: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stock: Mapped[int] = mapped_column(Integer)

    def to_domain(self) -> Book:
        """Convert the row into the domain Book entity."""
        return Book(
            isbn=self.isbn,
            title=self.title,
            author=self.author,
            genre=self.genre,
            description=self.description,
            stock=self.stock,
        )


class SqlAlchemyBookRepository(BookRepository):
    """BookRepository backed by a SQLAlchemy engine (one session per call)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def save(self, book: Book) -> None:
        """Persist a new book."""
        row = BookModel(
            isbn=book.isbn,
            title=book.title,
            author=book.author,
            genre=book.genre,
            description=book.description,
            stock=book.stock,
        )
        with Session(self._engine) as session, session.begin():
            session.add(row)

    def get_by_isbn(self, isbn: str) -> Book | None:
        """Return the registered book for an ISBN, or None."""
        with Session(self._engine) as session:
            row = session.get(BookModel, isbn)
            return row.to_domain() if row is not None else None

    def count_by_isbn(self, isbn: str) -> int:
        """Return how many books are registered under an ISBN."""
        with Session(self._engine) as session:
            return session.execute(
                select(func.count()).select_from(BookModel).where(BookModel.isbn == isbn)
            ).scalar_one()
