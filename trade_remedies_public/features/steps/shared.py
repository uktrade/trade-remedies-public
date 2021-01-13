"""Shared step logic."""
from behave import given, then, when
from features.steps.utils import (
    find_element_by_text,
    get_element_by_id,
    go_to_page,
    login,
    testuser_login,
)


@given('the user navigates to "{url_name}"')
@when('navigates to "{url_name}"')
@when('the user navigates to "{url_name}"')
@when('an anonymous user navigates to "{url_name}"')
def navigate(context, url_name):
    go_to_page(context, url_name)


@given('"{username}" navigates to "{url_name}"')
@when('"{username}" navigates to "{url_name}"')
def user_navigates(context, username, url_name):
    go_to_page(context, url_name)


@then('the "{text}" button is visible')
def button_visible(context, text):
    assert find_element_by_text(context, text, "button"), f"button {text} not found!"


@then('the "{text}" link is visible')
@when('the "{text}" link is visible')
def link_visible(context, text):
    assert find_element_by_text(context, text, "a"), f"link {text} not found!"


@then('text "{text}" is visible')
def text_is_visible(context, text):
    assert find_element_by_text(context, text), f"could not find text {text} in page"


def assert_dashboard_visible(context):
    text_is_visible(context, "This is your dashboard to interact")


@given ('the user is logged in')
def step_impl(context):
    go_to_page(context, "initial")
    testuser_login(context)
    assert_dashboard_visible(context)

