from django.urls import path
from documents import views

urlpatterns = [
    path("document/", views.DocumentView.as_view(), name="document"),
    path("document/<uuid:document_id>", views.DocumentView.as_view(), name="download_document"),
    path("document/without-js", views.DocumentWithoutJsView.as_view(), name="document_without_js"),
    path(
        "document/without-js/remove/<uuid:document_id>",
        views.DocumentWithoutJsView.as_view(),
        name="remove_document_without_js",
    ),
    path(
        "document/without-js/remove",
        views.DocumentWithoutJsView.as_view(),
        name="remove_documents_without_js",
    ),
]
