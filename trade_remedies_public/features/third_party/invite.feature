# Created by stronal at 12/01/2021
Feature: # Third party invite

  @fixture.public.user
  Scenario: The user access the 'Manage your team' page
    Given the user is logged in
    When the user selects the 'Manage Team' link
    Then the 'Manage your team' page is displayed

  @fixture.public.user
  Scenario: The user invite a colleague
    Given the logged in user navigates to the "team_view" page
    When the user selects the 'Invite colleague' link
    Then the 'Invite Colleague' page is displayed

  @fixture.public.user
  Scenario: The user prepares to invite a colleague as a third party
    Given the logged in user is on the "user_view" organisation page
    When the user selects the 3rd Party option on the form
    Then the message "You will be prompted for invitee details on the next page" is displayed


  @fixture.public.user
  Scenario: The user wants to invite a colleague as a third party
    Given the logged in user is on the "user_view" organisation page
    And the user selects the 3rd Party option on the form
    When the user submits the form
    Then the "invite_top" page is displayed

