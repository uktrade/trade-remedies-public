"""Shared step logic."""

from behave import given, then, when

import features.steps.utils as utils


@given('the user navigates to "{view_name}"')
@when('navigates to "{view_name}"')
@when('the user navigates to "{view_name}"')
@when('an anonymous user navigates to "{view_name}"')
def navigate(context, view_name):
    utils.go_to_page(context, view_name)


@given('"{username}" navigates to "{view_name}"')
@when('"{username}" navigates to "{view_name}"')
def user_navigates(context, username, view_name):
    utils.go_to_page(context, view_name)


@then('the "{text}" button is visible')
def button_visible(context, text):
    assert utils.find_element_by_text(context, text, "button"), f"button {text} not found!"


@then('the "{text}" link is visible')
@when('the "{text}" link is visible')
def link_visible(context, text):
    assert utils.find_element_by_text(context, text, "a"), f"link {text} not found!"


@then('the message "{text}" is displayed')
@then('text "{text}" is visible')
@then('the page showing "{text}" is displayed')
@when('the page showing "{text}" is displayed')
def text_is_visible(context, text):
    assert utils.find_element_by_text(context, text), f"could not find '{text}' in page"


def assert_dashboard_visible(context):
    text_is_visible(context, "This is your dashboard to interact")


@given("the user is logged in")
def step_impl(context):
    utils.go_to_page(context, "initial")
    utils.test_user_login(context)
    assert_dashboard_visible(context)


@given('the logged in user navigates to the "{view_name}" page')  # noqa: F811
@given('the logged in user is on the "{view_name}" page')
@when('the logged in user is on the "{view_name}" page')
def step_impl(context, view_name):  # noqa: F811
    context.execute_steps("given the user is logged in")
    utils.go_to_page(context, view_name)


@given('the logged in user is on the "{view_name}" organisation page')  # noqa: F811
def step_impl(context, view_name):  # noqa: F811
    context.execute_steps("given the user is logged in")
    utils.go_to_page(context, view_name, organisation_id=context.organisation_id)


@when("the user submits the form")
def step_impl(context):  # noqa: F811
    utils.get_element_by_id(context, "btn_submit").click()
