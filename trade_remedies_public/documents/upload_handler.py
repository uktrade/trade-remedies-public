import django.core.files.uploadhandler
from django.core.files.uploadhandler import FileUploadHandler
from v2_api_client.shared.upload_handler.metadata import Extractor
from django.core.files.uploadhandler import SkipFile

django.core.files.uploadhandler.FileUploadHandler.chunk_size = 33554432  # 32 Megabytes


class ExtractMetadataFileUploadHandler(FileUploadHandler):
    def file_complete(self, file_size):
        pass

    def receive_data_chunk(self, raw_data, start):
        if len(raw_data) > 31457280:  # 30 Megabytes
            raise SkipFile("The selected file must be smaller than 30MB")

        extractor = Extractor()
        sanitised_data = extractor(raw_data, self.content_type)

        return sanitised_data.getvalue()
