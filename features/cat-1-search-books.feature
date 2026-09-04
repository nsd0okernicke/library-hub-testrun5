Feature: CAT-1 - Search books in the catalog
  As a catalog user
  I want to search books by title, author or genre with pagination
  So I can find books in the catalog

  Background:
    Given the catalog service is running
    And the catalog is seeded with Dune (978-0-20-163361-0, Frank Herbert, Sci-Fi), Refactoring (978-0-13-468599-1, Martin Fowler, Software) and The Hobbit (978-3-16-148410-0, J.R.R. Tolkien, Fantasy)

  Scenario: A search without filters returns all books sorted by title ascending
    When books are searched with no filters
    Then the search returns status code 200
    And the result page contains exactly 3 books
    And the books are returned in the order Dune, Refactoring, The Hobbit
    And each book includes its ISBN, title, author, genre and available stock
    And the total result count is 3

  Scenario: A search matches a single field by case-insensitive substring
    When books are searched with <filter_field> <filter_value>
    Then the search returns status code 200
    And the result page contains exactly <total> books
    And the first book is <book_title>
    And the total result count is <total>

  Scenarios:
    | filter_field | filter_value | total | book_title  |
    | title        | une          | 1     | Dune        |
    | title        | the          | 1     | The Hobbit  |
    | author       | fowler       | 1     | Refactoring |
    | author       | HERBERT      | 1     | Dune        |
    | genre        | fantasy      | 1     | The Hobbit  |
    | genre        | SCI-FI       | 1     | Dune        |

  Scenario: Multiple filters combine with AND
    When books are searched with title <title>, author <author> and genre <genre>
    Then the search returns status code 200
    And the result page contains exactly <total> books
    And the total result count is <total>

  Scenarios:
    | title | author   | genre   | total |
    | (none)| herbert  | sci-fi  | 1     |
    | the   | (none)   | fantasy | 1     |
    | the   | fowler   | (none)  | 0     |

  Scenario: A search without a match is empty
    When books are searched with title "nonexistent"
    Then the search returns status code 200
    And the result page contains no books
    And the total result count is 0

  Scenario: A search is paginated
    When books are searched with no filters, page <page> and page size <page_size>
    Then the search returns status code 200
    And the result page contains exactly <page_count> books
    And the first book is <first_title>
    And the total result count is 3

  Scenarios:
    | page | page_size | page_count | first_title |
    | 1    | 1         | 1          | Dune        |
    | 2    | 1         | 1          | Refactoring |
    | 3    | 1         | 1          | The Hobbit  |
    | 1    | 2         | 2          | Dune        |
    | 2    | 2         | 1          | The Hobbit  |

  Scenario: A page beyond the last page is empty
    When books are searched with no filters, page 4 and page size 1
    Then the search returns status code 200
    And the result page contains no books
    And the total result count is 3
