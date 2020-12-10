from behave import then

import requests

from django.conf import settings

from features.steps import shared


def create_test_object(path):
    response = requests.get(f"{settings.API_TEST_URL}{path}")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "success"


@then("the Create an account page is displayed")
def create_acct_page(context):
    # Generate test objects
    create_test_object("create-test-case/")

    shared.text_is_visible(context, "Create an account")


@then("the Forgotten password page is displayed")
def forgotten_password_page(context):
    shared.text_is_visible(context, "Forgotten password")
