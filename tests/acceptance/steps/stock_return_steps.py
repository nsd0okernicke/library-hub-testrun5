"""Acceptance step definitions for features/cat-6-manual-stock-return.feature.

Executes the Gherkin scenarios against the catalog service via the public API
and verifies the persisted state through the repository fixture.
"""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "cat-6-manual-stock-return.feature"))


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


@given(
    parsers.parse(
        "a book with ISBN {isbn}, title {title}, author {author}, "
        "genre {genre} and stock {stock:d} is registered"
    )
)
def book_with_stock_is_registered(client, isbn, title, author, genre, stock):
    """Given: register a book with explicit metadata and starting stock."""
    _register(client, isbn, title, author, genre, stock)


@given(parsers.parse("a book with ISBN {isbn} is registered"))
def book_is_registered(client, isbn):
    """Given: register a book with default metadata and stock 1."""
    _register(client, isbn, f"Book {isbn}", "Some Author", "Fiction", 1)


@given(parsers.parse("a book with ISBN {isbn} is registered with stock {stock:d}"))
def book_is_registered_with_stock(client, isbn, stock):
    """Given: register a book with default metadata and explicit stock."""
    _register(client, isbn, f"Book {isbn}", "Some Author", "Fiction", stock)


@when(parsers.parse("an operator adds {copies:d} copies to the book with ISBN {isbn}"))
def operator_adds_copies(client, scenario_state, isbn, copies):
    """When: submit the manual stock return through the public API."""
    scenario_state["response"] = client.post(
        f"/books/{isbn}/stock-returns", json={"copies": copies}
    )
    scenario_state["isbn"] = isbn


@then(parsers.parse("the stock return request returns status code {status:d}"))
def stock_return_status(scenario_state, status):
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@then(parsers.parse("the book with ISBN {isbn} has stock {stock:d}"))
def book_has_stock(client, isbn, stock):
    repository = client.repository  # type: ignore[attr-defined]
    book = repository.get_by_isbn(isbn)
    assert book is not None
    assert book.stock == stock


@then(parsers.parse("the book with ISBN {isbn} still has stock {stock:d}"))
def book_still_has_stock(client, isbn, stock):
    repository = client.repository  # type: ignore[attr-defined]
    book = repository.get_by_isbn(isbn)
    assert book is not None
    assert book.stock == stock


@then(parsers.parse("the book still has title {title}, author {author} and genre {genre}"))
def book_metadata_unchanged(client, scenario_state, title, author, genre):
    repository = client.repository  # type: ignore[attr-defined]
    book = repository.get_by_isbn(scenario_state["isbn"])  # type: ignore[index]
    assert book is not None
    assert book.title == title
    assert book.author == author
    assert book.genre == genre


@then(parsers.parse("no book with ISBN {isbn} is registered"))
def no_book_registered(client, isbn):
    repository = client.repository  # type: ignore[attr-defined]
    assert repository.get_by_isbn(isbn) is None
