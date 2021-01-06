Feature: Login Process
  Public portal entry point. When a user navigates to the site it should
  be possible to log in as an existing user.


  Scenario: The user cannot log into the site
    Given the user navigates to "initial"
    When the user supplies wrong credentials
    Then the message "Please correct the following errors" is displayed

  @fixture.public.user
  Scenario: The user logs into the site
    Given the user navigates to "initial"
    When the user supplies correct credentials
    Then the user dashboard is displayed


