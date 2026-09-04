"""Acceptance step definitions for features/cat-3-create-book.feature.

pytest-bdd 8.x matches plain string step names *exactly*; parameterized steps
must be registered with an explicit parser. ``parsers.parse`` uses the `parse`
library: ``{name}`` matches any (non-greedy) text and ``{name:d}`` an integer.
"""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "cat-1-search-books.feature"))
scenarios(str(FEATURES_DIR / "cat-3-create-book.feature"))
scenarios(str(FEATURES_DIR / "cat-5-retrieve-book-by-isbn.feature"))


def _description(value: str) -> str | None:
    """Map the Gherkin '(none)' placeholder to a missing description."""
    return None if value in ("(none)", "None") else value


@given("the catalog service is running")
def catalog_service_running(client):
    """Background: the TestClient is wired to the catalog service by the fixture."""
    assert client is not None


CATALOG_SEED = [
    ("978-0-20-163361-0", "Dune", "Frank Herbert", "Sci-Fi", 3),
    ("978-0-13-468599-1", "Refactoring", "Martin Fowler", "Software", 2),
    ("978-3-16-148410-0", "The Hobbit", "J.R.R. Tolkien", "Fantasy", 1),
]


@given(
    "the catalog is seeded with Dune (978-0-20-163361-0, Frank Herbert, Sci-Fi), "
    "Refactoring (978-0-13-468599-1, Martin Fowler, Software) "
    "and The Hobbit (978-3-16-148410-0, J.R.R. Tolkien, Fantasy)"
)
def catalog_seeded(client):
    """Background: register the three known books through the public API."""
    for isbn, title, author, genre, stock in CATALOG_SEED:
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


@when("books are searched with no filters")
def search_without_filters(client, scenario_state):
    scenario_state["response"] = client.get("/books")


@when(parsers.parse('books are searched with title "{title}"'))
def search_with_quoted_title(client, scenario_state, title):
    scenario_state["response"] = client.get("/books", params={"title": title})


@when(parsers.re(r"books are searched with (?P<filter_field>[\w-]+) (?P<filter_value>[\w-]+)"))
def search_with_single_filter(client, scenario_state, filter_field, filter_value):
    scenario_state["response"] = client.get("/books", params={filter_field: filter_value})


@when(parsers.parse("books are searched with title {title}, author {author} and genre {genre}"))
def search_with_multiple_filters(client, scenario_state, title, author, genre):
    params = {
        field: value
        for field, value in (("title", title), ("author", author), ("genre", genre))
        if value != "(none)"
    }
    scenario_state["response"] = client.get("/books", params=params)


@when(
    parsers.parse("books are searched with no filters, page {page:d} and page size {page_size:d}")
)
def search_paged(client, scenario_state, page, page_size):
    scenario_state["response"] = client.get("/books", params={"page": page, "page_size": page_size})


@then(parsers.parse("the search returns status code {status:d}"))
def search_status(scenario_state, status):
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@then(parsers.parse("the result page contains exactly {count:d} books"))
def result_page_size(scenario_state, count):
    books = scenario_state["response"].json()["books"]
    assert len(books) == count


@then("the result page contains no books")
def result_page_empty(scenario_state):
    books = scenario_state["response"].json()["books"]
    assert books == []


@then(parsers.parse("the first book is {title}"))
def first_book_is(scenario_state, title):
    books = scenario_state["response"].json()["books"]
    assert books[0]["title"] == title


@then("the books are returned in the order Dune, Refactoring, The Hobbit")
def books_in_expected_order(scenario_state):
    books = scenario_state["response"].json()["books"]
    assert [book["title"] for book in books] == ["Dune", "Refactoring", "The Hobbit"]


@then("each book includes its ISBN, title, author, genre and available stock")
def books_include_all_fields(scenario_state):
    books = scenario_state["response"].json()["books"]
    assert books  # the no-filter scenario always returns books
    for book in books:
        assert isinstance(book["isbn"], str) and book["isbn"]
        assert isinstance(book["title"], str) and book["title"]
        assert isinstance(book["author"], str) and book["author"]
        assert isinstance(book["genre"], str) and book["genre"]
        assert isinstance(book["stock"], int) and book["stock"] >= 0


@then(parsers.parse("the total result count is {total:d}"))
def total_result_count(scenario_state, total):
    assert scenario_state["response"].json()["total"] == total


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
