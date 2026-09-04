"""Property-based tests for the user loan listing value objects."""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from loans.domain.user_loans import MAX_PAGE_SIZE, UserLoanQuery


class TestUserLoanQueryProperties:
    @given(
        page=st.integers(min_value=1, max_value=10**6),
        size=st.integers(min_value=1, max_value=10**6),
    )
    @settings(max_examples=200)
    def test_offset_equals_previous_pages_times_capped_size(self, page: int, size: int) -> None:
        query = UserLoanQuery(user_id="u", page=page, page_size=size)
        assert query.offset == (page - 1) * min(size, MAX_PAGE_SIZE)

    @given(size=st.integers(min_value=1, max_value=10**6))
    @settings(max_examples=200)
    def test_page_size_is_capped_never_rejected(self, size: int) -> None:
        query = UserLoanQuery(user_id="u", page=1, page_size=size)
        assert query.page_size == min(size, MAX_PAGE_SIZE)
        assert 1 <= query.page_size <= MAX_PAGE_SIZE

    @given(size=st.integers(min_value=MAX_PAGE_SIZE, max_value=MAX_PAGE_SIZE))
    @settings(max_examples=50)
    def test_capping_is_idempotent(self, size: int) -> None:
        once = UserLoanQuery(user_id="u", page=1, page_size=size)
        twice = UserLoanQuery(user_id="u", page=1, page_size=once.page_size)
        assert twice.page_size == once.page_size == MAX_PAGE_SIZE

    @given(user_id=st.text(min_size=1, max_size=40))
    @settings(max_examples=100)
    def test_non_blank_user_id_round_trips(self, user_id: str) -> None:
        if not user_id.strip():
            with pytest.raises(ValueError):
                UserLoanQuery(user_id=user_id)
        else:
            assert UserLoanQuery(user_id=user_id).user_id == user_id

    @given(page=st.integers(max_value=0))
    @settings(max_examples=50)
    def test_non_positive_page_is_rejected(self, page: int) -> None:
        with pytest.raises(ValueError):
            UserLoanQuery(user_id="u", page=page)
