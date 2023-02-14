import logging
import os

from django import forms
from django.conf import settings
from django_chunk_upload_handlers.clam_av import VirusFoundInFileException

from config.forms import ValidationForm

logger = logging.getLogger(__name__)


class DocumentForm(ValidationForm):
    """
    Generic form to validate document uploads.
    """

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    file = forms.FileField(required=False)

    def clean_file(self):
        file = self.data["file"]
        if file.size > settings.FILE_MAX_SIZE_BYTES:
            self.add_error(
                None, f"The selected file must be smaller than 30MB: {file.original_name}"
            )

        try:
            file.readline()
        except VirusFoundInFileException:
            logger.warning(f"{self.user.email} just tried to upload a file with a virus")
            self.add_error(None, f"This file contains a virus: {file.original_name}")

        _, file_extension = os.path.splitext(file.original_name)
        if file_extension.lower()[1:] in settings.FILE_DISALLOWED_EXTENSIONS:
            self.add_error(
                None,
                f"The selected file cannot be any of:  "
                f"{', '.join(settings.FILE_DISALLOWED_EXTENSIONS)} - "
                f"{file.original_name}",
            )

        return file
