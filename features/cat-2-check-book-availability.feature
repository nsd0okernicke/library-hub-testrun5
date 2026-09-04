Feature: CAT-2 - Check book availability by ISBN
  As a catalog user
  I want to check the current availability of a book by its ISBN
  So I can get a lightweight availability answer without fetching full book metadata

  Background:
    Given the catalog service is running

  Scenario: The availability of a registered book is reported
    Given a book with ISBN <isbn> and stock <stock> is registered
    When the availability of ISBN <isbn> is checked
    Then the check returns status code 200
    And the response contains ISBN <isbn> and available count <stock>
    And the response contains no other book details

  Scenarios:
    | isbn              | stock |
    | 978-0-20-163361-0 | 3     |
    | 978-0-13-468599-1 | 0     |
    | 978-3-16-148410-0 | 12    |

  Scenario: Checking the availability of an unregistered ISBN is not found
    Given a book with ISBN <registered_isbn> is already registered
    When the availability of ISBN <requested_isbn> is checked
    Then the check returns status code 404
    And no availability data is returned

  Examples:
    | registered_isbn   | requested_isbn  |
    | 978-0-20-163361-0 | 978-1-40-289462-6 |
    | 978-0-13-468599-1 | 978-3-10-017746-1 |
