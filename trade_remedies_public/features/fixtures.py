import requests

from behave import fixture

from django.conf import settings

TEST_PASSWORD = "A7Hhfa!jfaw@f"


@fixture
def public_user(context):
    response = requests.post(f"{settings.API_BASE_URL}/api-test-obj/users/")
    context.user = response.json().get("email", "Unknown")
    context.password = TEST_PASSWORD
    return context