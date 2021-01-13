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
    import time
    time.sleep(10)
    ref = get_element_by_id(context, "bdd_manage_your_team")
    ref.click()


@then("the 'Manage your team' page is displayed")
def step_impl(context):
    text_is_visible(context, "Manage your team")
