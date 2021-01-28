from behave import given, when

from features.steps.shared import text_is_visible, assert_dashboard_visible
import features.steps.utils as utils


@when("the user selects the 'Manage Team' link")  # noqa: F811
def step_impl(context):
    assert_dashboard_visible(context)
    ref = utils.get_element_by_id(context, "lnk_manage_your_team")
    ref.click()


@when("the user selects the 'Invite colleague' link")  # noqa: F811
def step_impl(context):
    text_is_visible(context, "Manage your team")
    ref = utils.get_element_by_id(context, "lnk_invite_colleague")
    ref.click()


@when("the user selects the 3rd Party option on the form")  # noqa: F811
@given("the user selects the 3rd Party option on the form")
def step_impl(context):
    text_is_visible(
        context,
        "Regular (3rd Party) user who is representing "
        "your organisation on a particular case (e.g. Lawyer)",
    )
    ref = utils.get_element_by_id(context, "role_3")
    ref.click()
