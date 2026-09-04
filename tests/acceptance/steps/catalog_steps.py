"""Acceptance step definitions for features/cat-3-create-book.feature."""

from pathlib import Path

from pytest_bdd import given, scenarios, then, when

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "cat-3-create-book.feature"))


def _description(value: str) -> str | None:
    """Map the Gherkin '(none)' placeholder to a missing description."""
    return None if value in ("(none)", "None") else value


@given("the catalog service is running")
def catalog_service_running(context):
    """Background: the TestClient is wired to the catalog service by the fixture."""
    assert context.client is not None


@given("a book with ISBN {isbn} is already registered")
def book_already_registered(context, isbn):
    response = context.client.post(
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
    "a book is created with ISBN {isbn}, title {title}, author {author}, "
    "genre {genre}, description {description} and initial stock {stock:int}"
)
def create_book(context, isbn, title, author, genre, description, stock):
    context.response = context.client.post(
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


@then("the book is created with status code {status:int}")
def created_status(context, status):
    assert context.response.status_code == status, context.response.text


@then(
    "the book is registered with ISBN {isbn}, title {title}, author {author}, "
    "genre {genre}, description {description} and stock {stock:int}"
)
def book_is_registered(context, isbn, title, author, genre, description, stock):
    repository = context.client.repository  # type: ignore[attr-defined]
    book = repository.get_by_isbn(isbn)
    assert book is not None
    assert book.title == title
    assert book.author == author
    assert book.genre == genre
    assert book.description == _description(description)
    assert book.stock == stock


@then("the creation is rejected with status code {status:int}")
def rejected_status(context, status):
    assert context.response.status_code == status, context.response.text


@then("no second book with ISBN {isbn} is registered")
def no_second_book(context, isbn):
    repository = context.client.repository  # type: ignore[attr-defined]
    assert repository.count_by_isbn(isbn) == 1
