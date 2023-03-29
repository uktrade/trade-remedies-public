import django.core.files.uploadhandler
from django.core.files.uploadhandler import FileUploadHandler
from django.core.files.uploadhandler import StopUpload
from v2_api_client.shared.upload_handler.metadata import Extractor

from config.settings.base import FILE_MAX_SIZE_BYTES, FILE_MAX_SIZE_BYTES_ERROR

django.core.files.uploadhandler.FileUploadHandler.chunk_size = 33554432  # 32 Megabytes


class ExtractMetadataFileUploadHandler(FileUploadHandler):
    def file_complete(self, file_size):
        pass

    def receive_data_chunk(self, raw_data, start):
        if len(raw_data) > FILE_MAX_SIZE_BYTES:  # 30 Megabytes
            raise StopUpload(FILE_MAX_SIZE_BYTES_ERROR)

        extractor = Extractor()
        sanitised_data = extractor(raw_data, self.content_type)

        return sanitised_data.getvalue()
