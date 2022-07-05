from .library import APIClient


class APIClientMixin:
    @property
    def client(self, *args, **kwargs):
        return APIClient(*args, **kwargs)
