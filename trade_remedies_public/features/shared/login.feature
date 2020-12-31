Feature: Login Process
  Public portal entry point. When a user navigates to the site it should
  be possible to log in as an existing user.


  Scenario: A user cannot log into the site
    When an anonymous user navigates to "initial"
    And the user supplies wrong credentials
    Then the message "Please correct the following errors" is displayed

  @fixture.public.user
  Scenario: A user logs into the site
    When an anonymous user navigates to "initial"
    And the user supplies correct credentials
    Then the user dashboard is displayed


