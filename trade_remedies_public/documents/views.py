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
        print(request.POST)
        print(request.FILES)
        uploaded_files = []
        for file in request.FILES.getlist("files"):
            print(file)
            print("INSIDE LOOP")
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
        print(request.GET["document_to_delete"])
        self.client.documents(request.GET["document_to_delete"]).delete()
        return HttpResponse(status=204)

    def get(self, request, *args, **kwargs):
        document = self.client.documents(self.kwargs["document_id"])
        return redirect(document["file"])


@method_decorator(csrf_exempt, name="dispatch")
class DocumentWithoutJsView(View, APIClientMixin):
    def get(self, request, *args, **kwargs):
        print(request.GET)
        print(request.POST)
        print(self.kwargs["document_id"])
        self.client.documents(self.kwargs["document_id"]).delete()
        HttpResponse(status=204)
        return redirect(request.META["HTTP_REFERER"])

    @catch_form_errors()
    def post(self, request, *args, **kwargs):
        print("files", request.FILES)
        print("post", request.POST)

        if "non_confidential_submit" in request.POST:
            for file in request.FILES.getlist("non_confidential_file"):
                print(file)
                print("file name", file.name)
                print("file size", file.file_size)
                print("original_name", file.original_name)

                form = DocumentForm(data={"file": file}, user=request.user)
                print(form)
                # file.delete()
                # Checking the file is valid (size, virus, extension)
                if form.is_valid():
                    print("VALID")
                    # Sending it to the API for storage
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
                    print("non", form.errors)
                    form.assign_errors_to_request(request)
                    request.session["form_errors"]["file_type"] = "non_confidential"
        if "confidential_submit" in request.POST:
            for file in request.FILES.getlist("confidential_file"):
                print(file)
                print("file name", file.name)
                print("file size", file.file_size)
                print("original_name", file.original_name)

                form = DocumentForm(data={"file": file}, user=request.user)
                print(form)
                # file.delete()
                # Checking the file is valid (size, virus, extension)
                if form.is_valid():
                    print("VALID")
                    # Sending it to the API for storage
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
                    form.assign_errors_to_request(request)
                    request.session["form_errors"]["file_type"] = "confidential"

        return redirect(request.META["HTTP_REFERER"])
