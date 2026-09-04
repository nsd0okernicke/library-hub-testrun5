"""Acceptance step definitions for features/cat-2-check-book-availability.feature.

Shares the "catalog service is running" and "book ... is already registered"
steps with conftest.py; pytest-bdd loads conftest steps for every scenario.
"""

from pathlib import Path

from pytest_bdd import given, parsers, scenarios, then, when

FEATURES_DIR = Path(__file__).resolve().parents[3] / "features"

scenarios(str(FEATURES_DIR / "cat-2-check-book-availability.feature"))


@given(parsers.parse("a book with ISBN {isbn} and stock {stock:d} is registered"))
def book_with_stock_is_registered(client, isbn, stock):
    """Register a book with the given stock through the public API."""
    response = client.post(
        "/books",
        json={
            "isbn": isbn,
            "title": f"Book {isbn}",
            "author": "Some Author",
            "genre": "Fiction",
            "stock": stock,
        },
    )
    assert response.status_code == 201, response.text


@when(parsers.parse("the availability of ISBN {isbn} is checked"))
def check_availability(client, scenario_state, isbn):
    scenario_state["response"] = client.get(f"/books/{isbn}/availability")


@then(parsers.parse("the check returns status code {status:d}"))
def availability_status(scenario_state, status):
    response = scenario_state["response"]
    assert response.status_code == status, response.text


@then(parsers.parse("the response contains ISBN {isbn} and available count {stock:d}"))
def availability_contains_isbn_and_count(scenario_state, isbn, stock):
    body = scenario_state["response"].json()
    assert body["isbn"] == isbn
    assert body["available_count"] == stock


@then("the response contains no other book details")
def availability_has_no_other_details(scenario_state):
    body = scenario_state["response"].json()
    assert set(body) == {"isbn", "available_count"}


@then("no availability data is returned")
def availability_has_no_data(scenario_state):
    body = scenario_state["response"].json()
    assert "isbn" not in body
    assert "available_count" not in body
