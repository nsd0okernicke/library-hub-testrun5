"""Catalog use case for searching books by title, author or genre."""

from catalog.domain.ports import BookRepository
from catalog.domain.search import BookSearchCriteria, BookSearchResult


class SearchBooks:
    """Search the catalog by optional case-insensitive substring filters (AND).

    Results are ordered by title ascending and paginated; invalid pagination is
    rejected before the repository is reached.
    """

    def __init__(self, repository: BookRepository) -> None:
        """Store the book repository used to run searches."""
        self._repository = repository

    def __call__(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> BookSearchResult:
        """Run the search and return one page of matching books plus the total count."""
        criteria = BookSearchCriteria(
            title=title,
            author=author,
            genre=genre,
            page=page,
            page_size=page_size,
        )
        return self._repository.search(criteria)
