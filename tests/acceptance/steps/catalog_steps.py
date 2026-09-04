"""Acceptance step definitions for features/cat-3-create-book.feature.

pytest-bdd 8.x matches plain string step names *exactly*; parameterized steps
must be registered with an explicit parser. ``parsers.parse`` uses the `parse`
library: ``{name}`` matches any (non-greedy) text and ``{name:d}`` an integer.
"""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "cat-3-create-book.feature"))
scenarios(str(FEATURES_DIR / "cat-5-retrieve-book-by-isbn.feature"))


def _description(value: str) -> str | None:
    """Map the Gherkin '(none)' placeholder to a missing description."""
    return None if value in ("(none)", "None") else value


@given("the catalog service is running")
def catalog_service_running(client):
    """Background: the TestClient is wired to the catalog service by the fixture."""
    assert client is not None


@given(parsers.parse("a book with ISBN {isbn} is already registered"))
def book_already_registered(client, isbn):
    response = client.post(
        "/books",
        json={
            "isbn": isbn,
            "title": "Already There",
            "author": "Some Author",
            "genre": "Mystery",
            "stock": 3,
        },
    )
    assert response.status_code == 201, response.text


@when(
    parsers.parse(
        "a book is created with ISBN {isbn}, title {title}, author {author}, "
        "genre {genre}, description {description} and initial stock {stock:d}"
    )
)
def create_book(client, scenario_state, isbn, title, author, genre, description, stock):
    scenario_state["response"] = client.post(
        "/books",
        json={
            "isbn": isbn,
            "title": title,
            "author": author,
            "genre": genre,
            "description": _description(description),
            "stock": stock,
        },
    )


@given(
    parsers.parse(
        "a book with ISBN {isbn}, title {title}, author {author}, "
        "genre {genre}, description {description} and stock {stock:d} is registered"
    )
)
def book_with_full_metadata_is_registered(client, isbn, title, author, genre, description, stock):
    response = client.post(
        "/books",
        json={
            "isbn": isbn,
            "title": title,
            "author": author,
            "genre": genre,
            "description": _description(description),
            "stock": stock,
        },
    )
    assert response.status_code == 201, response.text


@when(parsers.parse("a book is retrieved by ISBN {isbn}"))
def retrieve_book(client, scenario_state, isbn):
    scenario_state["response"] = client.get(f"/books/{isbn}")


@then(parsers.parse("the book is returned with status code {status:d}"))
def retrieved_status(scenario_state, status):
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@then(
    parsers.parse(
        "the response contains ISBN {isbn}, title {title}, author {author}, "
        "genre {genre}, description {description} and available stock {stock:d}"
    )
)
def response_contains_book(scenario_state, isbn, title, author, genre, description, stock):
    response = scenario_state["response"]
    body = response.json()
    assert body["isbn"] == isbn
    assert body["title"] == title
    assert body["author"] == author
    assert body["genre"] == genre
    assert body["description"] == _description(description)
    assert body["stock"] == stock


@then(parsers.parse("the request returns status code {status:d}"))
def request_status(scenario_state, status):
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@then("no book data is returned")
def no_book_data(scenario_state):
    body = scenario_state["response"].json()
    assert "isbn" not in body
    assert "title" not in body


@then(parsers.parse("the book is created with status code {status:d}"))
def created_status(scenario_state, status):
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@then(
    parsers.parse(
        "the book is registered with ISBN {isbn}, title {title}, author {author}, "
        "genre {genre}, description {description} and stock {stock:d}"
    )
)
def book_is_registered(client, isbn, title, author, genre, description, stock):
    repository = client.repository  # type: ignore[attr-defined]
    book = repository.get_by_isbn(isbn)
    assert book is not None
    assert book.title == title
    assert book.author == author
    assert book.genre == genre
    assert book.description == _description(description)
    assert book.stock == stock


@then(parsers.parse("the creation is rejected with status code {status:d}"))
def rejected_status(scenario_state, status):
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@then(parsers.parse("no second book with ISBN {isbn} is registered"))
def no_second_book(client, isbn):
    repository = client.repository  # type: ignore[attr-defined]
    assert repository.count_by_isbn(isbn) == 1
