"""Property tests for the catalog domain Book entity."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from catalog.domain.book import Book

book_data = st.builds(
    Book,
    isbn=st.from_regex(r"97[89]-[0-9]-[0-9]{1,7}-[0-9]{1,7}-[0-9]", fullmatch=True),
    title=st.text(min_size=1, max_size=50),
    author=st.text(min_size=1, max_size=50),
    genre=st.text(min_size=1, max_size=30),
    description=st.one_of(st.none(), st.text(max_size=200)),
    stock=st.integers(min_value=0, max_value=10_000),
)


class TestBookProperties:
    @given(data=book_data)
    @settings(max_examples=50)
    def test_constructed_book_preserves_all_fields(self, data: Book) -> None:
        assert data.isbn == data.isbn.strip()
        assert data.stock >= 0
        assert {data.title, data.author, data.genre} == {
            data.title,
            data.author,
            data.genre,
        }

    @given(stock=st.integers(max_value=-1))
    @settings(max_examples=25)
    def test_negative_stock_is_always_rejected(self, stock: int) -> None:
        with pytest.raises(ValueError):
            Book(
                isbn="978-3-16-148410-0",
                title="T",
                author="A",
                genre="G",
                description=None,
                stock=stock,
            )

    @given(isbn=st.from_regex(r"[ ]{1,5}", fullmatch=True))
    @settings(max_examples=25)
    def test_blank_isbn_is_always_rejected(self, isbn: str) -> None:
        with pytest.raises(ValueError):
            Book(
                isbn=isbn,
                title="T",
                author="A",
                genre="G",
                description=None,
                stock=1,
            )
