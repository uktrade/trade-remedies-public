from django.core.files import uploadhandler
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django_chunk_upload_handlers import clam_av
from v2_api_client.encoders import TRSObjectJsonEncoder
from v2_api_client.mixins import APIClientMixin

from v2_api_client.shared.upload_handler.django_upload_handler import FILE_MAX_SIZE_BYTES_ERROR
from config.settings.base import DEFAULT_CHUNK_SIZE
from config.utils import add_form_error_to_session
from core.decorators import catch_form_errors
from documents.forms import DocumentForm

clam_av.ClamAVFileUploadHandler.chunk_size = DEFAULT_CHUNK_SIZE
uploadhandler.FileUploadHandler.chunk_size = DEFAULT_CHUNK_SIZE


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

        # Check if upload handler skipped file due to file size
        if not request.FILES.getlist("files"):
            # Return early with error message
            return JsonResponse(
                data={"errors": {"__all__": [FILE_MAX_SIZE_BYTES_ERROR]}},
                status=400,
            )

        for file in request.FILES.getlist("files"):
            form = DocumentForm(data={"file": file}, user=request.user)
            # Checking the file is valid (size, extension)
            if form.is_valid():
                # Sending it to the API for storage
                new_document_upload = self.client.documents(
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
                        "replace_document_id": request.POST.get("replace_document_id", None),
                    }
                )
                uploaded_files.append(new_document_upload)

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


@method_decorator(csrf_exempt, name="dispatch")
class DocumentWithoutJsView(View, APIClientMixin):
    def get(self, request, *args, **kwargs):
        if request.GET.get("document_ids"):
            for document in request.GET["document_ids"].split(","):
                self.client.documents(document).delete()

            return redirect(request.META["HTTP_REFERER"])

        self.client.documents(self.kwargs["document_id"]).delete()
        return redirect(request.META["HTTP_REFERER"])

    @catch_form_errors()
    def post(self, request, *args, **kwargs):
        if "non_confidential_submit" in request.POST:
            if not request.FILES.getlist("non_confidential_file"):
                return self.construct_error_summary_message(request, "non_confidential")

            for file in request.FILES.getlist("non_confidential_file"):
                form = DocumentForm(data={"file": file}, user=request.user)

                if form.is_valid():
                    self.client.documents(
                        {
                            "type": "non_confidential",
                            "stored_name": file.name,
                            "original_name": file.original_name,
                            "file_size": file.file_size,
                            "submission_id": request.POST["non_confidential_submission_id"],
                            "parent": request.POST.get("parent", None),
                            "submission_document_type": request.POST.get(
                                "submission_document_type", None
                            ),
                            "replace_document_id": request.POST.get("replace_document_id", None),
                        }
                    )
                else:
                    file.obj.delete()
                    form.assign_errors_to_request(request)
                    request.session["form_errors"]["file_type"] = "non_confidential"

        if "confidential_submit" in request.POST:
            if not request.FILES.getlist("confidential_file"):
                return self.construct_error_summary_message(request, "confidential")

            for file in request.FILES.getlist("confidential_file"):
                form = DocumentForm(data={"file": file}, user=request.user)

                if form.is_valid():
                    self.client.documents(
                        {
                            "type": "confidential",
                            "stored_name": file.name,
                            "original_name": file.original_name,
                            "file_size": file.file_size,
                            "submission_id": request.POST["confidential_submission_id"],
                            "parent": request.POST.get("parent", None),
                            "submission_document_type": request.POST.get(
                                "submission_document_type", None
                            ),
                            "replace_document_id": request.POST.get("replace_document_id", None),
                        }
                    )
                else:
                    file.obj.delete()
                    form.assign_errors_to_request(request)
                    request.session["form_errors"]["file_type"] = "confidential"

        return redirect(request.META["HTTP_REFERER"].split("?")[0])

    @staticmethod
    def construct_error_summary_message(request, file_type):
        add_form_error_to_session(
            FILE_MAX_SIZE_BYTES_ERROR, request, "file_type", FILE_MAX_SIZE_BYTES_ERROR
        )
        request.session["form_errors"]["file_type"] = file_type

        return redirect(request.META["HTTP_REFERER"].split("?")[0])
