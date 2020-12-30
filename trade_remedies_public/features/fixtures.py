import requests

from behave import fixture

from django.conf import settings

TEST_PASSWORD = "A7Hhfa!jfaw@f"


@fixture
def public_user(context):
    response = requests.post(f"{settings.API_BASE_URL}/api-test-obj/users/")
    email_response = response.json()["email"]
    context.public_user = email_response
    context.password = TEST_PASSWORD
    yield email_response, TEST_PASSWORD
