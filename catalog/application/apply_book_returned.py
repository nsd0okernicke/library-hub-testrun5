"""Use case for applying a book returned event received from the broker (CAT-4)."""

from catalog.domain.book import Book
from catalog.domain.events import BookReturnedEvent
from catalog.domain.ports import BookRepository


class ApplyBookReturnedEvent:
    """Increase the stock of the returned ISBN by one copy.

    Book metadata (title, author, genre, description) is never touched. An
    event for an ISBN that is not registered is ignored: no book is created,
    nothing is saved, and no exception is raised, so later events keep being
    processed.
    """

    def __init__(self, repository: BookRepository) -> None:
        """Store the book repository used to look up and persist books."""
        self._repository = repository

    def __call__(self, event: BookReturnedEvent) -> Book | None:
        """Add one copy to the returned book's stock and persist it.

        Returns the updated book, or None when the ISBN is unregistered.
        """
        book = self._repository.get_by_isbn(event.isbn)
        if book is None:
            return None
        updated = book.add_copies(1)
        self._repository.save(updated)
        return updated
