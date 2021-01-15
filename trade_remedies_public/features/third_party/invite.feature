# Created by stronal at 12/01/2021
Feature: # Third party invite

  @fixture.public.user
  Scenario: The user access the 'Manage your team' page
    Given the user is logged in
    When the user click the 'Manage Team' link
    Then the 'Manage your team' page is displayed

#  @fixture.public.user
#  Scenario: The user access the 'Manage your team' page
#    Given the user is logged in
#    When the user click the 'Manage Team' link
#    Then the 'Manage your team' page is displayed


  @fixture.public.user
  Scenario: The user invite a colleague
    Given the user is logged in
    And the user navigates to "team_view"
    When the user click the 'Invite colleague' link
    Then the 'Invite Colleague' page is displayed
