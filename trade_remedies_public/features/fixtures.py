import requests

from behave import fixture

from django.conf import settings

from features.steps.utils import test_user_login

TEST_PASSWORD = "A7Hhfa!jfaw@f"


@fixture
def public_user(context):
    response = requests.post(f"{settings.API_BASE_URL}/api-test-obj/users/")
    response_json = response.json()
    organisation = response_json.get("organisations", [])
    if organisation:
        context.organisation_id = organisation[0].get("id", "Unknown")
    else:
        context.organisation_id = "Unknown"
    context.user = response_json.get("email", "Unknown")
    context.password = TEST_PASSWORD
    return context


@fixture
def public_logged_user(context):
    public_user(context)
    test_user_login(context)
    return context
