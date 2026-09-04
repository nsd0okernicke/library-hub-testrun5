Feature: CAT-3 - Create a new book in the catalog
  As a catalog user
  I want to register a new book with its metadata and initial stock
  So the catalog reflects available books

  Background:
    Given the catalog service is running

  Scenario: A new book is created
    When a book is created with ISBN <isbn>, title <title>, author <author>, genre <genre>, description <description> and initial stock <stock>
    Then the book is created with status code 201
    And the book is registered with ISBN <isbn>, title <title>, author <author>, genre <genre>, description <description> and stock <stock>

  Scenarios:
    | isbn              | title       | author         | genre    | description  | stock |
    | 978-3-16-148410-0 | Dune        | Frank Herbert  | Sci-Fi   | Arrakis saga | 5     |
    | 978-3-49-961840-5 | Neuromancer | William Gibson | Sci-Fi   | (none)       | 12    |
    | 978-0-14-118776-1 | 1984        | George Orwell  | Dystopia | (none)       | 0     |

  Scenario: Creating a book with an already registered ISBN is rejected
    Given a book with ISBN <isbn> is already registered
    When a book is created with ISBN <isbn>, title "Dune", author "Frank Herbert", genre "Sci-Fi", description "Arrakis saga" and initial stock 5
    Then the creation is rejected with status code 409
    And no second book with ISBN <isbn> is registered

  Examples:
    | isbn              |
    | 978-3-16-148410-0 |
    | 978-0-14-118776-1 |
