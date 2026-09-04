"""Acceptance step definitions for features/cat-4-book-returned-stock-increase.feature.

Executes the Gherkin scenarios against the shared in-process broker wired into
the catalog service by the conftest fixtures and verifies the persisted state
through the repository fixture.
"""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

from loans.domain.events import BookReturned

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "cat-4-book-returned-stock-increase.feature"))


def _register(client, isbn: str, title: str, author: str, genre: str, stock: int) -> None:
    """Register a book through the public API and assert success."""
    response = client.post(
        "/books",
        json={
            "isbn": isbn,
            "title": title,
            "author": author,
            "genre": genre,
            "stock": stock,
        },
    )
    assert response.status_code == 201, response.text


def _publish_returned(broker, isbn: str, user_id: str) -> None:
    """Publish one loan-service shaped BookReturned event to the broker."""
    broker.publish(BookReturned(loan_id="loan-acceptance", user_id=user_id, isbn=isbn))


@given("the loan and catalog services share a message broker")
def shared_message_broker(client):
    """Shared Background step: the fixtures wire both services to one broker."""
    assert client.broker is not None  # type: ignore[attr-defined]


@given(
    parsers.parse(
        "a book with ISBN {isbn}, title {title}, author {author}, "
        "genre {genre} and stock {stock:d} is registered"
    )
)
def book_with_metadata_is_registered(client, isbn, title, author, genre, stock):
    """Given: register a book with explicit metadata and starting stock."""
    _register(client, isbn, title, author, genre, int(stock))


@given(parsers.parse("a book with ISBN {isbn} and stock {stock:d} is registered"))
def book_with_stock_is_registered(client, isbn, stock):
    """Given: register a book with default metadata and explicit stock."""
    _register(client, isbn, f"Book {isbn}", "Some Author", "Fiction", int(stock))


@given(parsers.parse("a book with ISBN {isbn} is registered with stock {stock:d}"))
def book_registered_with_stock(client, isbn, stock):
    """Given: register a book with default metadata and explicit stock."""
    _register(client, isbn, f"Book {isbn}", "Some Author", "Fiction", int(stock))


@when(parsers.parse("a book returned event for user {name} and book {isbn} is received"))
def book_returned_event_received(client, scenario_state, name, isbn):
    """When: the broker delivers one book returned event for the book."""
    _publish_returned(client.broker, isbn, name)  # type: ignore[attr-defined]
    scenario_state["isbn"] = isbn


@when(parsers.parse("{count:d} book returned events for book {isbn} are received"))
def book_returned_events_received(client, scenario_state, count, isbn):
    """When: the broker delivers several book returned events for the book."""
    for _ in range(int(count)):
        _publish_returned(client.broker, isbn, "someone")  # type: ignore[attr-defined]
    scenario_state["isbn"] = isbn


@then(parsers.parse("the book with ISBN {isbn} has stock {stock:d}"))
def book_has_stock(client, isbn, stock):
    """Then: the persisted stock matches the expected value."""
    repository = client.repository  # type: ignore[attr-defined]
    book = repository.get_by_isbn(isbn)
    assert book is not None
    assert book.stock == int(stock)


@then(parsers.parse("the book with ISBN {isbn} still has stock {stock:d}"))
def book_still_has_stock(client, isbn, stock):
    """Then: an ignored event left the persisted stock untouched."""
    repository = client.repository  # type: ignore[attr-defined]
    book = repository.get_by_isbn(isbn)
    assert book is not None
    assert book.stock == int(stock)


@then(parsers.parse("the book still has title {title}, author {author} and genre {genre}"))
def book_metadata_unchanged(client, scenario_state, title, author, genre):
    """Then: the event never touched the book's metadata."""
    repository = client.repository  # type: ignore[attr-defined]
    book = repository.get_by_isbn(scenario_state["isbn"])  # type: ignore[index]
    assert book is not None
    assert book.title == title
    assert book.author == author
    assert book.genre == genre


@then(parsers.parse("no book with ISBN {isbn} is registered"))
def no_book_registered(client, isbn):
    """Then: the unregistered ISBN was not created by the ignored event."""
    repository = client.repository  # type: ignore[attr-defined]
    assert repository.get_by_isbn(isbn) is None
