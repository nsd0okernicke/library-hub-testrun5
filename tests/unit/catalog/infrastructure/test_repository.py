"""Unit tests for the SQLAlchemy book repository (in-process SQLite, no container)."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from catalog.domain.book import Book
from catalog.infrastructure.persistence import Base, BookModel, SqlAlchemyBookRepository


def _repository() -> SqlAlchemyBookRepository:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return SqlAlchemyBookRepository(engine)


class TestSqlAlchemyBookRepository:
    def test_save_then_get_by_isbn_roundtrip(self) -> None:
        repository = _repository()
        book = Book(
            isbn="978-3-16-148410-0",
            title="Dune",
            author="Frank Herbert",
            genre="Sci-Fi",
            description="Arrakis saga",
            stock=5,
        )
        repository.save(book)
        assert repository.get_by_isbn("978-3-16-148410-0") == book

    def test_get_by_isbn_missing_returns_none(self) -> None:
        repository = _repository()
        assert repository.get_by_isbn("no-such-isbn") is None

    def test_count_by_isbn(self) -> None:
        repository = _repository()
        assert repository.count_by_isbn("978-3-16-148410-0") == 0
        repository.save(
            Book(
                isbn="978-3-16-148410-0",
                title="Dune",
                author="Frank Herbert",
                genre="Sci-Fi",
                description=None,
                stock=0,
            )
        )
        assert repository.count_by_isbn("978-3-16-148410-0") == 1

    def test_saves_are_persisted_across_sessions(self) -> None:
        repository = _repository()
        repository.save(
            Book(
                isbn="978-0-14-118776-1",
                title="1984",
                author="George Orwell",
                genre="Dystopia",
                description=None,
                stock=0,
            )
        )
        with Session(repository._engine) as session:  # noqa: SLF001
            rows = session.execute(select(BookModel)).scalars().all()
        assert len(rows) == 1
