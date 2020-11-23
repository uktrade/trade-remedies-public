Feature: Landing Page
  Public portal entry point. When a user navigates to the site it should
  be possible to log in as an existing user, reset password or create an
  account.

  @home
  Scenario: An anonymous user navigates to the site
    When an anonymous user navigates to "initial"
    Then the "Sign in" button is visible
    And the "Create an account" link is visible

  @home
  Scenario: A user has forgotten their password
    When an anonymous user navigates to "forgot_password"
    Then the Forgotten password page is displayed
    And the "Request password reset" button is visible

  @home
  Scenario: A user does not have an account
    When an anonymous user navigates to "register"
    Then the Create an account page is displayed
