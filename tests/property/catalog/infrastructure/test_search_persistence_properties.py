"""Property tests for the SQLAlchemy repository search (in-process SQLite, no container)."""

from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from catalog.domain.book import Book
from catalog.domain.search import BookSearchCriteria
from catalog.infrastructure.persistence import Base, SqlAlchemyBookRepository


def _repository_with_books(books: list[Book]) -> SqlAlchemyBookRepository:
    """Build an in-memory repository seeded with the given books."""
    engine = create_engine(
        "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    repository = SqlAlchemyBookRepository(engine)
    for book in books:
        repository.save(book)
    return repository


book_strategy = st.builds(
    Book,
    isbn=st.from_regex(r"978-0-0-[0-9]{6}-[0-9]{5}", fullmatch=True),
    title=st.text(min_size=1, max_size=30, alphabet=st.sampled_from("abcXYZ-")),
    author=st.text(min_size=1, max_size=20, alphabet=st.sampled_from("abcdXY-")),
    genre=st.text(min_size=1, max_size=20, alphabet=st.sampled_from("efghZ-")),
    description=st.none(),
    stock=st.integers(min_value=0, max_value=100),
)

criteria_strategy = st.builds(
    BookSearchCriteria,
    title=st.one_of(st.none(), st.text(max_size=10, alphabet=st.sampled_from("abcXYZ-"))),
    author=st.one_of(st.none(), st.text(max_size=10, alphabet=st.sampled_from("abcdXY-"))),
    genre=st.one_of(st.none(), st.text(max_size=10, alphabet=st.sampled_from("efghZ-"))),
    page=st.integers(min_value=1, max_value=10),
    page_size=st.integers(min_value=1, max_value=10),
)


def _reference_matches(book: Book, criteria: BookSearchCriteria) -> bool:
    """Reference implementation: case-insensitive substring, AND across filters."""
    for value, field_name in (
        (criteria.title, "title"),
        (criteria.author, "author"),
        (criteria.genre, "genre"),
    ):
        if value is not None and value.lower() not in getattr(book, field_name).lower():
            return False
    return True


class TestRepositorySearchProperties:
    @given(
        books=st.lists(book_strategy, min_size=0, max_size=15, unique_by=lambda b: b.isbn),
        criteria=criteria_strategy,
    )
    @settings(max_examples=50, deadline=None)
    def test_total_count_equals_the_reference_match_count(
        self, books: list[Book], criteria: BookSearchCriteria
    ) -> None:
        repository = _repository_with_books(books)
        result = repository.search(criteria)
        expected = sum(1 for book in books if _reference_matches(book, criteria))
        assert result.total_count == expected

    @given(
        books=st.lists(book_strategy, min_size=0, max_size=15, unique_by=lambda b: b.isbn),
        criteria=criteria_strategy,
    )
    @settings(max_examples=50, deadline=None)
    def test_page_items_are_sorted_by_title_ascending(
        self, books: list[Book], criteria: BookSearchCriteria
    ) -> None:
        repository = _repository_with_books(books)
        result = repository.search(criteria)
        titles = [book.title for book in result.items]
        assert titles == sorted(titles)

    @given(
        books=st.lists(book_strategy, min_size=0, max_size=15, unique_by=lambda b: b.isbn),
        criteria=criteria_strategy,
    )
    @settings(max_examples=50, deadline=None)
    def test_page_never_returns_more_than_page_size_items(
        self, books: list[Book], criteria: BookSearchCriteria
    ) -> None:
        repository = _repository_with_books(books)
        result = repository.search(criteria)
        assert len(result.items) <= criteria.page_size

    @given(
        books=st.lists(book_strategy, min_size=0, max_size=15, unique_by=lambda b: b.isbn),
        criteria=criteria_strategy,
    )
    @settings(max_examples=50, deadline=None)
    def test_searching_far_beyond_the_last_page_keeps_the_total(
        self, books: list[Book], criteria: BookSearchCriteria
    ) -> None:
        repository = _repository_with_books(books)
        normal = repository.search(criteria)
        beyond = repository.search(
            BookSearchCriteria(
                title=criteria.title,
                author=criteria.author,
                genre=criteria.genre,
                page=criteria.page + len(books) + 1,
                page_size=criteria.page_size,
            )
        )
        assert beyond.items == []
        assert beyond.total_count == normal.total_count
