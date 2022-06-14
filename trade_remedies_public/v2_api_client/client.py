from apiclient import APIClient, HeaderAuthentication
from apiclient.response_handlers import BaseResponseHandler, JsonResponseHandler


class V2APIClient(APIClient):

    def list_customers(self):
        url = "http://example.com/customers"
        return self.get(url)

    def add_customer(self, customer_info):
        url = "http://example.com/customers"
        return self.post(url, data=customer_info)


authentication_method = HeaderAuthentication(
    token="secret_value",
    parameter="apikey",
    scheme="Token",
)

v2_client = V2APIClient(
    authentication_method=authentication_method,
    response_handler=JsonResponseHandler
)
