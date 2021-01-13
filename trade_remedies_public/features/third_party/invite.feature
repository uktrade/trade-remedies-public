# Created by stronal at 12/01/2021
Feature: # Third party invite
  # Enter feature description here

  @fixture.public.user
  Scenario: The user access the 'Manage your team' page
    Given the user is logged in
    When the user click the 'Manage Team' link
    Then the 'Manage your team' page is displayed
