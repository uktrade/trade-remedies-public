from django.urls import path
from documents import views

urlpatterns = [
    path(
        "document/",
        views.DocumentView.as_view(),
        name="document"
    ),
]
