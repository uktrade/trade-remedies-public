from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django_chunk_upload_handlers.clam_av import VirusFoundInFileException


class DocumentForm(forms.Form):
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

        if file.content_type not in settings.FILE_ALLOWED_TYPES:
            raise ValidationError(
                message=f"The selected file must be either a Doc, Excel, or PDF: "
                f"{file.original_name}"
            )

        return file
