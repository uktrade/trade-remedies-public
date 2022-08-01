from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from v2_api_client.mixins import APIClientMixin

from trade_remedies_public.core.decorators import catch_form_errors
from trade_remedies_public.documents.forms import DocumentForm


class DocumentView(View, APIClientMixin):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    @catch_form_errors()
    def post(self, request, *args, **kwargs):
        uploaded_files = []
        for file in request.FILES.getlist("files"):
            form = DocumentForm(data={"file": file})
            if form.is_valid():
                uploaded_files.append(self.call_client(timeout=50).create_document(
                    **{
                        "type": request.POST["type"],
                        "stored_name": file.name,
                        "original_name": file.original_name,
                        "file_size": file.file_size,
                        "submission_id": request.POST["submission_id"],
                        "parent": request.POST.get("parent", None),
                        "submission_document_type": request.POST.get("submission_document_type", None),
                    }
                ))
                return JsonResponse({
                    "uploaded_files": uploaded_files,
                }, status=201)
            else:
                return JsonResponse(data={"errors": form.errors}, status=400)

    def delete(self, request, *args, **kwargs):
        self.client.delete(
            self.client.url(f"documents/{request.GET['document_to_delete']}"),
        )
        return HttpResponse(status=204)
