from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from v2_api_client.encoders import TRSObjectJsonEncoder
from v2_api_client.mixins import APIClientMixin

from core.decorators import catch_form_errors
from documents.forms import DocumentForm


@method_decorator(csrf_exempt, name="dispatch")
class DocumentView(View, APIClientMixin):
    """
    Generic file upload view, validates and uploads the file. Can also delete provided an ID.

    Documents are actually uploaded directly through the public platform to AWS, however we then
    create a record of the document via the API which contains the information required to retrieve
    it at a later date.

    We need to make this view CSRF exempt as the actual
    file is passed here from ClamAV which does not include a CSRF token.  PS-IGNORE
    """

    @catch_form_errors()
    def post(self, request, *args, **kwargs):
        uploaded_files = []
        for file in request.FILES.getlist("files"):
            form = DocumentForm(data={"file": file}, user=request.user)
            # Checking the file is valid (size, virus, extension)
            if form.is_valid():
                uploaded_files.append(
                    # Sending it to the API for storage
                    self.client.documents(
                        {
                            "type": request.POST["type"],
                            "stored_name": file.name,
                            "original_name": file.original_name,
                            "file_size": file.file_size,
                            "submission_id": request.POST["submission_id"],
                            "parent": request.POST.get("parent", None),
                            "submission_document_type": request.POST.get(
                                "submission_document_type", None
                            ),
                        }
                    )
                )
                # if this file is replacing another, let's delete the replacement
                if replace_document_id := request.POST.get("replace_document_id"):
                    self.client.documents(replace_document_id).delete()
                return JsonResponse(
                    {
                        "uploaded_files": uploaded_files,
                    },
                    encoder=TRSObjectJsonEncoder,
                    status=201,
                )
            else:
                # First we delete the file from S3
                file.obj.delete()
                return JsonResponse(data={"errors": form.errors}, status=400)

    def delete(self, request, *args, **kwargs):
        self.client.documents(request.GET["document_to_delete"]).delete()
        return HttpResponse(status=204)

    def get(self, request, *args, **kwargs):
        document = self.client.documents(self.kwargs["document_id"])
        return redirect(document["file"])
