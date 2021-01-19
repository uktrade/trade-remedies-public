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
  Scenario: The user wants to invite a colleague as a third party
    Given the logged in user is on the "user_view" organisation page
    When the user selects the 3rd Party option on the form
    Then the message "You will be prompted for invitee details on the next page" is displayed


#  @fixture.public.user
#  Scenario: The user wants to invite a colleague as a third party
#    Given the logged in user is on the 'invite colleague' page
#    And the user selects the 3rd Party option on the form
#    When the user submits the form
#    Then the 'Invite a 3rd party'(put the view name) page is displayed
#
#
#  @fixture.public.user
#  Scenario: The user fill up the invitation for a third party invite
#    Given the logged in user is on the 'Invite a 3rd party' page
#    When the user click 3rd Party
#    Then You will be prompted for invitee details on the next page is displayed
