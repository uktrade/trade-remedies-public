import requests

from django.conf import settings


def create_test_object(path):
    response = requests.get(f"{settings.API_BASE_URL}/api-test-obj/{path}/")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "success"
