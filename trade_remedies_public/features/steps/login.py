from behave import then, when

from features.steps.shared import text_is_visible
from features.steps.utils import (
    login,
    test_user_login,
)


@when("the user supplies wrong credentials")
def step_impl(context):
    email = "a@a.com"
    password = "wrong"
    text_is_visible(context, "Email address")
    login(context, email, password)


@when("the user supplies correct credentials")  # noqa: F811
def step_impl(context):
    text_is_visible(context, "Email address")
    test_user_login(context)


@then("the user dashboard is displayed")  # noqa: F811
def step_impl(context):
    text_is_visible(context, "This is your dashboard to interact")
