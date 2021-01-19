from behave import then, when

from features.steps.shared import (text_is_visible,
                                   assert_dashboard_visible)
from features.steps.utils import (
    get_element_by_id,
    login,
    testuser_login,
)


@when("the user click the 'Manage Team' link")
def step_impl(context):
    assert_dashboard_visible(context)
    ref = get_element_by_id(context, "bdd_manage_your_team")
    ref.click()


@then("the 'Manage your team' page is displayed")
def step_impl(context):
    text_is_visible(context, "Manage your team")


@when("the user click the 'Invite colleague' link")
def step_impl(context):
    text_is_visible(context, "Manage your team")
    ref = get_element_by_id(context, "bdd_invite_colleague")
    ref.click()


@then("the 'Invite Colleague' page is displayed")
@when("the 'Invite Colleague' page is displayed")
def step_impl(context):
    text_is_visible(context, "Manage your team")


@when(u'the user selects the 3rd Party option on the form')
def step_impl(context):
    text_is_visible(context, "Regular (3rd Party) user who is representing your organisation on a particular case (e.g. Lawyer)")
    ref = get_element_by_id(context, "role_3")
    ref.click()


@then(u'the message \'You will be prompted for invitee details on the next page\'')
def step_impl(context):
    text_is_visible(context, "You will be prompted for invitee details on the next page")

