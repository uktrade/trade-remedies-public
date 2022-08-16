from django.urls import path
from documents import views

urlpatterns = [
    path("document/", views.DocumentView.as_view(), name="document"),
    path("document/<uuid:document_id>", views.DocumentView.as_view(), name="download_document"),
]
