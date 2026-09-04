"""Search value objects for the catalog domain."""

from dataclasses import dataclass, field

from catalog.domain.book import Book


@dataclass(frozen=True)
class BookSearchCriteria:
    """A book search: optional case-insensitive substring filters combined with AND.

    Results are ordered by title ascending and paginated (1-based page numbers).
    ``None`` means the filter is not applied.
    """

    title: str | None = None
    author: str | None = None
    genre: str | None = None
    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        """Enforce the pagination invariants (1-based page, positive page size)."""
        if self.page < 1:
            raise ValueError(f"page must be >= 1, got {self.page}")
        if self.page_size < 1:
            raise ValueError(f"page_size must be >= 1, got {self.page_size}")


@dataclass(frozen=True)
class BookSearchResult:
    """One page of search results plus the total number of matching books."""

    items: list[Book] = field(default_factory=list)
    total_count: int = 0

    def __post_init__(self) -> None:
        """Enforce the result invariants (non-negative, consistent counts)."""
        if self.total_count < 0:
            raise ValueError(f"total_count must not be negative, got {self.total_count}")
        if len(self.items) > self.total_count:
            raise ValueError(
                f"total_count {self.total_count} must cover the {len(self.items)} returned books"
            )
