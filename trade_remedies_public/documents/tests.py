import os

from django.core.files.uploadedfile import TemporaryUploadedFile, SimpleUploadedFile
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from openpyxl.workbook import Workbook

from documents.upload_handler import ExtractMetadataFileUploadHandler


@override_settings(
    FILE_UPLOAD_HANDLERS=["documents.upload_handler.ExtractMetadataFileUploadHandler"]
)
class ExtractDocumentMetadataTestCase(TestCase):
    def setUp(self):
        self.request_factory = RequestFactory()
        self.request = self.request_factory.request()

    def test_chunk_is_received(self):
        self.create_extract_document_metadata_handler(
            "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # create XLSX document with metadata
        self.create_xlsx_document()

        with open(os.path.join(os.path.dirname(__file__), "fixture.xlsx"), "rb") as file:
            raw_data = file.read()

        response = self.extract_document_metadata_handler_file_handler.receive_data_chunk(
            raw_data,
            0,
        )

        # remove temporary XLSX document
        os.remove(self.xlsx_file)

        # check response is not the same as raw_data
        assert response != raw_data

    def test_unsupported_file_type(self):
        self.create_extract_document_metadata_handler("txt", "application/text")

        smol_file = SimpleUploadedFile("file.txt", b"smol world")

        raw_data = smol_file.read()

        response = self.extract_document_metadata_handler_file_handler.receive_data_chunk(
            raw_data,
            0,
        )

        # check response is the same as raw_data
        assert response == raw_data

    def test_check_file_size(self):
        file = TemporaryUploadedFile("large.txt", "application/text", 36700160, charset="utf-8")

        response = self.client.post(reverse("document"), {"file": file})

        assert "The selected file must be smaller than 30MB" in str(response.content)

    def create_extract_document_metadata_handler(self, file_extension, file_type):
        self.extract_document_metadata_handler_file_handler = ExtractMetadataFileUploadHandler(
            request=self.request,
        )
        self.extract_document_metadata_handler_file_handler.new_file(
            "file",
            f"file.{file_extension}",
            file_type,
            100,
        )

    def create_xlsx_document(self):
        self.xlsx = Workbook()
        self.xlsx_metadata = self.xlsx.properties
        self.xlsx_metadata.creator = "TRA"
        self.xlsx_metadata.title = "TITLE"

        self.xlsx_file = os.path.join(os.path.dirname(__file__), "fixture.xlsx")
        self.xlsx.save(self.xlsx_file)
