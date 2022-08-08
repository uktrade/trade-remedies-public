import os
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django_chunk_upload_handlers.clam_av import VirusFoundInFileException


class DocumentForm(forms.Form):
    """
    Generic form to validate document uploads.
    """
    file = forms.FileField(required=False)

    def clean_file(self):
        file = self.data["file"]
        if file.size > settings.FILE_MAX_SIZE_BYTES:
            raise ValidationError(
                message=f"The selected file must be smaller than 30MB: {file.original_name}"
            )

        try:
            file.readline()
        except VirusFoundInFileException:
            raise ValidationError(message=f"This file contains a virus: {file.original_name}")

        _, file_extension = os.path.splitext(file.original_name)
        if file_extension.lower() not in settings.FILE_ALLOWED_EXTENSIONS:
            raise ValidationError(
                message=f"The selected file must be either a Doc, Excel, PDF, or ZIP: "
                f"{file.original_name}"
            )

        return file
