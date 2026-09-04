"""Unit tests for the user loan listing value objects (pure Python, no I/O)."""

from dataclasses import FrozenInstanceError

import pytest

from loans.domain.user_loans import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    UserLoanPage,
    UserLoanQuery,
)


class TestUserLoanQuery:
    def test_defaults_are_page_one_and_size_20(self) -> None:
        query = UserLoanQuery(user_id="usr-1")
        assert query.page == 1
        assert query.page_size == DEFAULT_PAGE_SIZE == 20

    def test_explicit_page_and_size_are_kept(self) -> None:
        query = UserLoanQuery(user_id="usr-1", page=3, page_size=10)
        assert query.page == 3
        assert query.page_size == 10

    def test_page_size_above_maximum_is_capped_to_100(self) -> None:
        query = UserLoanQuery(user_id="usr-1", page=1, page_size=150)
        assert query.page_size == MAX_PAGE_SIZE == 100

    def test_page_size_at_the_maximum_is_kept(self) -> None:
        query = UserLoanQuery(user_id="usr-1", page=1, page_size=100)
        assert query.page_size == 100

    def test_offset_is_zero_for_page_one(self) -> None:
        assert UserLoanQuery(user_id="u", page=1, page_size=10).offset == 0

    def test_offset_accounts_for_previous_pages(self) -> None:
        assert UserLoanQuery(user_id="u", page=3, page_size=10).offset == 20

    def test_offset_uses_the_capped_page_size(self) -> None:
        assert UserLoanQuery(user_id="u", page=2, page_size=150).offset == 100

    def test_blank_user_id_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            UserLoanQuery(user_id="   ")

    def test_zero_page_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            UserLoanQuery(user_id="u", page=0)

    def test_negative_page_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            UserLoanQuery(user_id="u", page=-1)

    def test_zero_page_size_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            UserLoanQuery(user_id="u", page=1, page_size=0)

    def test_negative_page_size_is_rejected(self) -> None:
        with pytest.raises(ValueError):
            UserLoanQuery(user_id="u", page=1, page_size=-5)

    def test_query_is_frozen(self) -> None:
        query = UserLoanQuery(user_id="u")
        with pytest.raises(FrozenInstanceError):
            query.page = 2


class TestUserLoanPage:
    def test_empty_page_by_default(self) -> None:
        assert UserLoanPage().loans == []

    def test_holds_the_requested_page(self) -> None:
        assert UserLoanPage(page=2, page_size=10).page == 2
        assert UserLoanPage(page=2, page_size=10).page_size == 10

    def test_defaults_are_page_one_and_size_20(self) -> None:
        page = UserLoanPage()
        assert page.page == 1
        assert page.page_size == DEFAULT_PAGE_SIZE == 20

    def test_page_is_frozen(self) -> None:
        with pytest.raises(FrozenInstanceError):
            UserLoanPage().page = 2
