Feature: CAT-6 - Manual stock return (stock correction)
  As an operations staff
  I want to add copies to a book's stock directly in the catalog
  So I can correct stock after physical returns or deliveries without a loan record

  Note: this is a stock-correction tool, fully independent of loans — no loan record is
  read or created, and no book-returned event is published. The added copies are a
  positive whole number; adding zero or a negative amount is a validation error (422)
  and leaves the book unchanged. Book metadata (title, author, genre, description) is
  never touched.

  Background:
    Given the catalog service is running

  Scenario: Copies are added to the stock of a registered book
    Given a book with ISBN <isbn>, title <title>, author <author>, genre <genre> and stock <previous_stock> is registered
    When an operator adds <added> copies to the book with ISBN <isbn>
    Then the stock return request returns status code 200
    And the book with ISBN <isbn> has stock <expected_stock>
    And the book still has title <title>, author <author> and genre <genre>

  Scenarios:
    | isbn              | title       | author         | genre    | previous_stock | added | expected_stock |
    | 978-0-20-163361-0 | Dune        | Frank Herbert  | Sci-Fi   | 3              | 2     | 5              |
    | 978-3-16-148410-0 | The Hobbit  | J.R.R. Tolkien | Fantasy  | 0              | 5     | 5              |
    | 978-0-13-468599-1 | Refactoring | Martin Fowler  | Software | 12             | 1     | 13             |

  Scenario: Adding copies to an unregistered ISBN is not found
    Given a book with ISBN <registered_isbn> is registered
    When an operator adds <added> copies to the book with ISBN <requested_isbn>
    Then the stock return request returns status code 404
    And no book with ISBN <requested_isbn> is registered

  Examples:
    | registered_isbn   | requested_isbn  | added |
    | 978-0-20-163361-0 | 978-1-40-289462-6 | 3     |
    | 978-0-13-468599-1 | 978-3-10-017746-1 | 7     |

  Scenario: Adding a non-positive number of copies is rejected and leaves the book unchanged
    Given a book with ISBN <isbn> is registered with stock <stock>
    When an operator adds <added> copies to the book with ISBN <isbn>
    Then the stock return request returns status code 422
    And the book with ISBN <isbn> still has stock <stock>

  Scenarios:
    | isbn              | stock | added |
    | 978-0-20-163361-0 | 4     | 0     |
    | 978-3-16-148410-0 | 0     | -2    |
    | 978-0-13-468599-1 | 9     | -1    |
