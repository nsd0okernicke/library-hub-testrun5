Feature: CAT-4 - Automatic stock increase on book returned
  As a catalog operator
  I want the catalog to automatically add a book back to the stock when the loan service reports a return
  So the available stock stays correct without any manual stock correction

  Note: the catalog consumes book returned events from the shared message broker. Each
  received event increases the stock of the returned ISBN by exactly one copy; events are
  applied in the order they are received. Book metadata (title, author, genre, description)
  is never touched. An event for an ISBN that is not registered in the catalog is ignored:
  no book is created, no other book is changed, and the event must not block the
  processing of later events.

  Background:
    Given the catalog service is running
    And the loan and catalog services share a message broker

  Scenario: A book returned event increases the stock of a registered book
    Given a book with ISBN <isbn>, title <title>, author <author>, genre <genre> and stock <previous_stock> is registered
    When a book returned event for user <name> and book <isbn> is received
    Then the book with ISBN <isbn> has stock <expected_stock>
    And the book still has title <title>, author <author> and genre <genre>

  Scenarios:
    | isbn              | title       | author         | genre    | name  | previous_stock | expected_stock |
    | 978-0-20-163361-0 | Dune        | Frank Herbert  | Sci-Fi   | Alice | 0              | 1              |
    | 978-3-16-148410-0 | The Hobbit  | J.R.R. Tolkien | Fantasy  | Bob   | 3              | 4              |
    | 978-0-13-468599-1 | Refactoring | Martin Fowler  | Software | Carol | 12             | 13             |

  Scenario: Several book returned events for the same ISBN each add one copy
    Given a book with ISBN <isbn> and stock <previous_stock> is registered
    When <event_count> book returned events for book <isbn> are received
    Then the book with ISBN <isbn> has stock <expected_stock>

  Scenarios:
    | isbn              | previous_stock | event_count | expected_stock |
    | 978-0-20-163361-0 | 1              | 2           | 3              |
    | 978-3-16-148410-0 | 0              | 3           | 3              |
    | 978-0-13-468599-1 | 5              | 2           | 7              |

  Scenario: A book returned event for an unregistered ISBN is ignored
    Given a book with ISBN <registered_isbn> is registered with stock <stock>
    When a book returned event for user <name> and book <requested_isbn> is received
    Then no book with ISBN <requested_isbn> is registered
    And the book with ISBN <registered_isbn> still has stock <stock>

  Scenarios:
    | registered_isbn   | stock | name  | requested_isbn  |
    | 978-0-20-163361-0 | 4     | Alice | 978-1-40-289462-6 |
    | 978-3-16-148410-0 | 0     | Bob   | 978-3-10-017746-1 |
    | 978-0-13-468599-1 | 7     | Carol | 978-0-59-652812-4 |

  Scenario: Later events keep being processed after an unregistered ISBN event
    Given a book with ISBN <isbn> and stock <previous_stock> is registered
    When a book returned event for user <name> and book 978-1-40-289462-6 is received
    And a book returned event for user <name> and book <isbn> is received
    Then no book with ISBN 978-1-40-289462-6 is registered
    And the book with ISBN <isbn> has stock <expected_stock>

  Scenarios:
    | isbn              | previous_stock | name  | expected_stock |
    | 978-0-20-163361-0 | 2              | Alice | 3              |
    | 978-0-13-468599-1 | 0              | Bob   | 1              |
