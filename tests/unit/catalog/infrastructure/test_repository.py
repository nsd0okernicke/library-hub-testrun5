"""Unit tests for the SQLAlchemy book repository (in-process SQLite, no container)."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from catalog.domain.book import Book
from catalog.domain.search import BookSearchCriteria
from catalog.infrastructure.persistence import Base, BookModel, SqlAlchemyBookRepository


def _repository() -> SqlAlchemyBookRepository:
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    return SqlAlchemyBookRepository(engine)


SEED_BOOKS = [
    Book(
        isbn="978-0-20-163361-0",
        title="Dune",
        author="Frank Herbert",
        genre="Sci-Fi",
        description=None,
        stock=3,
    ),
    Book(
        isbn="978-0-13-468599-1",
        title="Refactoring",
        author="Martin Fowler",
        genre="Software",
        description=None,
        stock=2,
    ),
    Book(
        isbn="978-3-16-148410-0",
        title="The Hobbit",
        author="J.R.R. Tolkien",
        genre="Fantasy",
        description=None,
        stock=1,
    ),
]


def _seeded_repository() -> SqlAlchemyBookRepository:
    """Build a repository seeded with the three known catalog books."""
    repository = _repository()
    for book in SEED_BOOKS:
        repository.save(book)
    return repository


def _titles(result) -> list[str]:
    """Extract the titles of a search result in returned order."""
    return [book.title for book in result.items]


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

    def test_re_save_with_same_isbn_updates_the_existing_row(self) -> None:
        repository = _seeded_repository()
        existing = repository.get_by_isbn("978-0-20-163361-0")
        assert existing is not None
        repository.save(existing.add_copies(2))
        fetched = repository.get_by_isbn("978-0-20-163361-0")
        assert fetched is not None
        assert fetched.stock == 5
        assert fetched.title == "Dune"
        assert repository.count_by_isbn("978-0-20-163361-0") == 1


class TestSqlAlchemyBookRepositorySearch:
    def test_no_filters_returns_all_books_sorted_by_title_ascending(self) -> None:
        repository = _seeded_repository()
        result = repository.search(BookSearchCriteria())
        assert _titles(result) == ["Dune", "Refactoring", "The Hobbit"]
        assert result.total_count == 3

    def test_filters_are_case_insensitive_substrings(self) -> None:
        repository = _seeded_repository()
        assert _titles(repository.search(BookSearchCriteria(title="une"))) == ["Dune"]
        assert _titles(repository.search(BookSearchCriteria(author="HERBERT"))) == ["Dune"]
        assert _titles(repository.search(BookSearchCriteria(genre="sci-fi"))) == ["Dune"]

    def test_filters_combine_with_and(self) -> None:
        repository = _seeded_repository()
        match = repository.search(BookSearchCriteria(title="the", genre="fantasy"))
        assert _titles(match) == ["The Hobbit"]
        no_match = repository.search(BookSearchCriteria(title="the", author="fowler"))
        assert no_match.items == []
        assert no_match.total_count == 0

    def test_pagination_slices_the_sorted_results(self) -> None:
        repository = _seeded_repository()
        first = repository.search(BookSearchCriteria(page=1, page_size=2))
        assert _titles(first) == ["Dune", "Refactoring"]
        assert first.total_count == 3
        second = repository.search(BookSearchCriteria(page=2, page_size=2))
        assert _titles(second) == ["The Hobbit"]
        assert second.total_count == 3

    def test_page_beyond_the_last_page_is_empty_but_total_is_kept(self) -> None:
        repository = _seeded_repository()
        result = repository.search(BookSearchCriteria(page=4, page_size=1))
        assert result.items == []
        assert result.total_count == 3

    def test_search_on_empty_catalog_returns_zero(self) -> None:
        repository = _repository()
        result = repository.search(BookSearchCriteria())
        assert result.items == []
        assert result.total_count == 0
