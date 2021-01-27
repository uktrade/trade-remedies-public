Feature: # Third party invite

  @fixture.public.user
  Scenario: The user accesses the 'Manage your team' page
    Given the user is logged in
    When the user selects the 'Manage Team' link
    Then the page showing "Manage your team" is displayed

  @fixture.public.user
  Scenario: The user decides to invite a colleague
    Given the logged in user navigates to the "team_view" page
    When the user selects the 'Invite colleague' link
    Then the page showing "Invite colleague" is displayed

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
    Then the page showing "Invite a 3rd party" is displayed

  @fixture.public.user
  Scenario: The user select a case for the third party invite
    Given the logged in user is on the "user_view" organisation page
    And the user selects the 3rd Party option on the form
    When the user submits the form
    Then the page showing "Invite a 3rd party" is displayed
