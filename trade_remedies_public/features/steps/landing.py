from behave import then

from features.api_test_objects import create_test_object
from features.steps import shared


@then("the Create an account page is displayed")
def create_acct_page(context):
    # Generate test objects
    create_test_object("case")

    shared.text_is_visible(context, "Create an account")


@then("the Forgotten password page is displayed")
def forgotten_password_page(context):
    shared.text_is_visible(context, "Forgotten password")
