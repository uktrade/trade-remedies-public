import os

from django.core.files.uploadedfile import TemporaryUploadedFile
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

    def create_extract_document_metadata_handler(self):
        self.extract_document_metadata_handler_file_handler = ExtractMetadataFileUploadHandler(
            request=self.request,
        )
        self.extract_document_metadata_handler_file_handler.new_file(
            "file",
            "file.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            100,
        )

    def test_chunk_is_received(self):
        self.create_extract_document_metadata_handler()

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

    def test_check_file_size(self):
        file = TemporaryUploadedFile("large.txt", "application/text", 36700160, charset="utf-8")

        response = self.client.post(reverse("document"), {"file": file})

        assert "The selected file must be smaller than 30MB" in str(response.content)

    def create_xlsx_document(self):
        self.xlsx = Workbook()
        self.xlsx_metadata = self.xlsx.properties
        self.xlsx_metadata.creator = "TRA"
        self.xlsx_metadata.title = "TITLE"

        self.xlsx_file = os.path.join(os.path.dirname(__file__), "fixture.xlsx")
        self.xlsx.save(self.xlsx_file)
