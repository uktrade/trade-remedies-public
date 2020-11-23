"""Shared step logic."""
from behave import then, when
from features.steps import utils


@when('navigates to "{url_name}"')
@when('the user navigates to "{url_name}"')
@when('an anonymous user navigates to "{url_name}"')
def navigate(context, url_name):
    utils.go_to_page(context, url_name)


@when('"{username}" navigates to "{url_name}"')
def user_navigates(context, username, url_name):
    utils.go_to_page(context, url_name)


@then('the "{text}" button is visible')
def button_visible(context, text):
    assert utils.find_element_by_text(context, text, 'button'), f'button {text} not found!'


@then('the "{text}" link is visible')
def link_visible(context, text):
    assert utils.find_element_by_text(context, text, 'a'), f'link {text} not found!'


@then('text "{text}" is visible')
def text_is_visible(context, text):
    assert utils.find_element_by_text(context, text), f'could not find text {text} in page'
