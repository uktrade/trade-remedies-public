import requests

from django.conf import settings

import logging

logger = logging.getLogger(__name__)


def user(email):
    email_data = {"email": email}
    response = requests.post(f"{settings.API_BASE_URL}/api-test-obj/user/", data=email_data)
    email_response = response.json()["email"]
    assert response.status_code == 201
    assert email_response == email
