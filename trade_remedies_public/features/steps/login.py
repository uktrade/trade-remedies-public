from behave import then, when

from features.steps.shared import text_is_visible
import features.steps.utils as utils


@when("the user supplies wrong credentials")
def step_impl(context):
    email = "a@a.com"  # /PS-IGNORE
    password = "wrong"
    text_is_visible(context, "Email address")
    utils.login(context, email, password)


@when("the user supplies correct credentials")
def step_impl(context):  # noqa: F811
    text_is_visible(context, "Email address")
    utils.test_user_login(context)


@then("the user dashboard is displayed")
def step_impl(context):  # noqa: F811
    text_is_visible(context, "This is your dashboard to interact")
