from v2_api_client.client import BaseAPIClient


class APIClient(BaseAPIClient):
    def get_cases(self):
        return self.get(self.url("cases"))
