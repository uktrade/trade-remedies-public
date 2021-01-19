"""Shared step logic."""
from behave import given, then, when
from behave_django.decorators import fixtures

from features.steps.utils import (
    find_element_by_text,
    get_element_by_id,
    go_to_page,
    login,
    testuser_login,
)

from features.fixtures import public_logged_user

@given('the user navigates to "{view_name}"')
@when('navigates to "{view_name}"')
@when('the user navigates to "{view_name}"')
@when('an anonymous user navigates to "{view_name}"')
def navigate(context, view_name):
    go_to_page(context, view_name)


@given('"{username}" navigates to "{view_name}"')
@when('"{username}" navigates to "{view_name}"')
def user_navigates(context, username, view_name):
    go_to_page(context, view_name)


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


@given(u'the logged in user navigates to the "{view_name}" page')
@given('the logged in user is on the "{view_name}" page')
@when('the logged in user is on the "{view_name}" page')
def step_impl(context, view_name):
    testuser_login(context)
    go_to_page(context, view_name)


