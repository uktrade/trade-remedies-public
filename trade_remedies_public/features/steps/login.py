from behave import then, when

from features.steps.shared import (text_is_visible)
from features.steps.utils import (
    get_element_by_id,
    login,
    testuser_login,
)


@when("the user supplies wrong credentials")
def step_impl(context):
    email = "a@a.com"
    password = "wrong"
    text_is_visible(context, "Email address")
    login(context, email, password)


@then('the message "Please correct the following errors" is displayed')  # noqa: F811
def step_impl(context):
    context.browser.find_element_by_class_name("error-summary")
    text_is_visible(context, "Please correct the following errors")


@when("the user supplies correct credentials")  # noqa: F811
def step_impl(context):
    text_is_visible(context, "Email address")
    testuser_login(context)


@then("the user dashboard is displayed")  # noqa: F811
def step_impl(context):
    text_is_visible(context, "This is your dashboard to interact")
