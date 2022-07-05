from apiclient import APIClient, HeaderAuthentication, JsonResponseHandler
from django.conf import settings


class BaseAPIClient(APIClient):

    def __init__(self, *args, **kwargs):
        authentication_method = HeaderAuthentication(
            token=kwargs.get("token") or settings.HEALTH_CHECK_TOKEN,
            parameter="Authorization",
            scheme="Token"
        )
        super().__init__(
            authentication_method=authentication_method,
            response_handler=kwargs.get("response_handler", JsonResponseHandler),
            *args,
            **kwargs
        )

    @staticmethod
    def url(path):
        return f"{settings.API_BASE_URL}/api/v2/{path}"
