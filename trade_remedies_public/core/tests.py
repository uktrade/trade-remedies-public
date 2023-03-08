from django.conf import settings
from django.template import Template, Context
from django.test import TestCase, override_settings
from django.utils.html import escape
from django.urls import reverse
from unittest.mock import patch, MagicMock

from core.utils import (
    internal_redirect,
    split_public_documents,
)


class TestPublicDocumentSplitting(TestCase):
    @staticmethod
    def _get_docs():
        return [
            {
                "id": "50de8062-03fd-4908-a08d-95473fb5db8e",  # /PS-IGNORE
                "name": "letter-of-authorisation-template-110918.docx",
                "size": 398535,
                "confidential": False,
                "block_from_public_file": False,
                "block_reason": None,
                "index_state": 3,
                "is_tra": True,
                "created_by": {
                    "id": "0dcab3f3-743e-4fde-a50d-0301a40b7835",  # /PS-IGNORE
                    "name": "Minnie Mouse",  # /PS-IGNORE
                    "email": "minnie@mouse.com",  # /PS-IGNORE
                    "tra": True,
                    "initials": "MM",
                    "colour": "#B500B5",
                    "active": True,
                },
                "created_at": "2020-05-14T10:16:32+0000",
                "virus_scanned_at": "2020-05-14T10:16:40+0000",
                "parent_id": None,
                "checksum": "207b2135a75c97ed4c16368868d66cfd-1",  # /PS-IGNORE
                "type": {
                    "id": 1,
                    "name": f"{settings.ORGANISATION_INITIALISM} Document",
                    "key": "caseworker",
                },
                "downloads": 1,
                "deficient": False,
                "sufficient": False,
                "issued": False,
                "issued_at": None,
                "issued_by": None,
                "downloadable": True,
            },
            {
                "id": "8a736af0-9e0c-4e2b-8cca-81b667930f70",  # /PS-IGNORE
                "name": "first-party-conf.txt",
                "size": 16,
                "confidential": True,
                "block_from_public_file": False,
                "block_reason": None,
                "index_state": 3,
                "is_tra": False,
                "created_by": {
                    "id": "efa9826e-8de4-4703-86bf-156c58bc9fe1",  # /PS-IGNORE
                    "name": "Test User",  # /PS-IGNORE
                    "email": "test.tester@example.com",  # /PS-IGNORE
                    "tra": False,
                    "initials": "MHL",
                    "colour": "#00AA55",
                    "active": True,
                },
                "created_at": "2020-07-23T14:19:44+0000",
                "virus_scanned_at": None,
                "parent_id": None,
                "checksum": "94ea43a364905e2b1358a02ccd68e107-1",  # /PS-IGNORE
                "type": {"id": 2, "name": "Customer Document", "key": "respondent"},
                "downloads": 0,
                "deficient": False,
                "sufficient": True,
                "issued": False,
                "issued_at": None,
                "issued_by": None,
                "downloadable": False,
            },
            {
                "id": "456335de-5fb2-47ed-abca-302240a53bc7",  # /PS-IGNORE
                "name": "first-party-public.txt",
                "size": 19,
                "confidential": False,
                "block_from_public_file": False,
                "block_reason": None,
                "index_state": 3,
                "is_tra": False,
                "created_by": {
                    "id": "efa9826e-8de4-4703-86bf-156c58bc9fe1",  # /PS-IGNORE
                    "name": "Test User",  # /PS-IGNORE
                    "email": "test.tester@example.com",  # /PS-IGNORE
                    "tra": False,
                    "initials": "MHL",
                    "colour": "#00AA55",
                    "active": True,
                },
                "created_at": "2020-07-23T14:19:57+0000",
                "virus_scanned_at": None,
                "parent_id": "8a736af0-9e0c-4e2b-8cca-81b667930f70",  # /PS-IGNORE
                "checksum": "dedfaea9a2e753fd52251cd14ee52ecf-1",  # /PS-IGNORE
                "type": {"id": 2, "name": "Customer Document", "key": "respondent"},
                "downloads": 0,
                "deficient": False,
                "sufficient": True,
                "issued": False,
                "issued_at": None,
                "issued_by": None,
                "downloadable": True,
            },
            {
                "id": "d35a6208-7c0f-4ce0-842a-32778f4046d1",
                "name": "extra-doc-conf.txt",
                "size": 2962,
                "confidential": True,
                "block_from_public_file": False,
                "block_reason": None,
                "index_state": 3,
                "is_tra": False,
                "created_by": {
                    "id": "efa9826e-8de4-4703-86bf-156c58bc9fe1",  # /PS-IGNORE
                    "name": "Test User",  # /PS-IGNORE
                    "email": "test.tester@example.com",  # /PS-IGNORE
                    "tra": False,
                    "initials": "MHL",
                    "colour": "#00AA55",
                    "active": True,
                },
                "created_at": "2020-07-23T14:20:08+0000",
                "virus_scanned_at": None,
                "parent_id": None,
                "checksum": "3f3be286819bfd1fe0f6a3fea8b0b0fd-1",  # /PS-IGNORE
                "type": {"id": 2, "name": "Customer Document", "key": "respondent"},
                "downloads": 0,
                "deficient": False,
                "sufficient": True,
                "issued": False,
                "issued_at": None,
                "issued_by": None,
                "downloadable": False,
            },
            {
                "id": "44be4a8f-3bfb-4a1b-9be0-7dcfa3a4daed",  # /PS-IGNORE
                "name": "extra-doc-public.txt",
                "size": 2956,
                "confidential": False,
                "block_from_public_file": True,
                "block_reason": "GDPR failure",
                "index_state": 3,
                "is_tra": False,
                "created_by": {
                    "id": "efa9826e-8de4-4703-86bf-156c58bc9fe1",  # /PS-IGNORE
                    "name": "Test User",  # /PS-IGNORE
                    "email": "test.tester@example.com",  # /PS-IGNORE
                    "tra": False,
                    "initials": "MHL",
                    "colour": "#00AA55",
                    "active": True,
                },
                "created_at": "2020-07-23T14:20:17+0000",
                "virus_scanned_at": None,
                "parent_id": "d35a6208-7c0f-4ce0-842a-32778f4046d1",  # /PS-IGNORE
                "checksum": "9ce0a3c8374a366933d82a2bdada2c22-1",  # /PS-IGNORE
                "type": {"id": 2, "name": "Customer Document", "key": "respondent"},
                "downloads": 0,
                "deficient": False,
                "sufficient": True,
                "issued": False,
                "issued_at": None,
                "issued_by": None,
                "downloadable": True,
            },
        ]

    def test_public_docs_count(self):
        docs = self._get_docs()
        template_docs, public_docs = split_public_documents(docs)
        self.assertEquals(1, len(public_docs))

    def test_template_docs(self):
        docs = self._get_docs()

        template_docs, public_docs = split_public_documents(docs)
        self.assertEquals(1, len(template_docs))


class TestTextElement(TestCase):
    def test_value_is_escaped(self):
        img_tag_str = '<img src="test" />'

        rendered = Template(
            "{% load text_element %}" "{% text_element id='test' label='Test' value=img_tag_str %}"
        ).render(Context({"img_tag_str": img_tag_str}))

        assert escape(img_tag_str) in rendered
        assert rendered.count("src") == 1


class UtilsTestCases(TestCase):
    @override_settings(
        ALLOWED_HOSTS=[
            "trade-remedies.com",
        ]
    )
    def internal_redirect(self):
        test_redirect = internal_redirect(
            "https://trade-remedies.com/test",
            "/dashboard/",
        )

        assert test_redirect.url == "https://trade-remedies.com/test"

        test_redirect = internal_redirect(
            "https://www.google.com/?test=1",
            "/dashboard/",
        )

        assert test_redirect.url == "/dashboard/"


class DataLayerTestCase(TestCase):
    def setUp(self):
        post_data = {
            "email": "test@example.com",  # /PS-IGNORE
            "name": "test",
            "terms_and_conditions_accept": True,
        }
        self.client.post(reverse("v2_register_start"), data=post_data)

    @patch("trade_remedies_client.client.Client", return_value=MagicMock())
    def test_datalayer_integration_password_reset(self, mock_client):
        # Get the URL for the password reset success page that implements the DataLayer
        url = reverse("reset_password_success")

        # Make a GET request to the URL
        response = self.client.get(url)

        # Check that the response has a status code of 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check that the DataLayer script is present in the response
        self.assertContains(
            response,
            "window.dataLayer",
        )

        self.assertEqual(url, "/accounts/password/reset/success/")

    @patch("trade_remedies_client.client.Client", return_value=MagicMock())
    def test_datalayer_integration_two_factor(self, mock_client):
        # Get the URL for the sign in page that implements the DataLayer
        url = reverse("two_factor")

        # Make a GET request to the URL
        response = self.client.get(url)

        # Check that the response has a status code of 200 (OK)
        self.assertEqual(response.status_code, 200)

        # Check that the DataLayer script is present in the response
        self.assertContains(
            response,
            "window.dataLayer",
        )

        self.assertEqual(url, "/twofactor/")
