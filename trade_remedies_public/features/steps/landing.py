from behave import then
from features.steps import shared


@then("the Create an account page is displayed")
def create_acct_page(context):
    shared.text_is_visible(context, "Create an account")


@then("the Forgotten password page is displayed")
def forgotten_password_page(context):
    shared.text_is_visible(context, "Forgotten password")
