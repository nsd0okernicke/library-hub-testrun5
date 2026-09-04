Feature: CAT-5 - Retrieve a single book by ISBN
  As a catalog user
  I want to look up a book by its ISBN
  So I can see its full metadata and current availability

  Background:
    Given the catalog service is running

  Scenario: A registered book is retrieved by ISBN
    Given a book with ISBN <isbn>, title <title>, author <author>, genre <genre>, description <description> and stock <stock> is registered
    When a book is retrieved by ISBN <isbn>
    Then the book is returned with status code 200
    And the response contains ISBN <isbn>, title <title>, author <author>, genre <genre>, description <description> and available stock <stock>

  Scenarios:
    | isbn              | title       | author         | genre    | description  | stock |
    | 978-0-20-163361-0 | Dune        | Frank Herbert  | Sci-Fi   | Arrakis saga | 3     |
    | 978-0-13-468599-1 | Refactoring | Martin Fowler  | Software | (none)       | 0     |
    | 978-3-16-148410-0 | The Hobbit  | J.R.R. Tolkien | Fantasy  | (none)       | 12    |

  Scenario: Retrieving a book by an unregistered ISBN is not found
    Given a book with ISBN <registered_isbn> is already registered
    When a book is retrieved by ISBN <requested_isbn>
    Then the request returns status code 404
    And no book data is returned

  Examples:
    | registered_isbn   | requested_isbn  |
    | 978-0-20-163361-0 | 978-1-40-289462-6 |
    | 978-0-13-468599-1 | 978-3-10-017746-1 |
