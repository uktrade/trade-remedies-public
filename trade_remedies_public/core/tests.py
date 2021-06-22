from django.conf import settings
from django.template import Template, Context
from django.test import TestCase
from django.utils.html import escape

from core.utils import split_public_documents


class TestPublicDocumentSplitting(TestCase):
    @staticmethod
    def _get_docs():
        return [
            {
                "id": "50de8062-03fd-4908-a08d-95473fb5db8e",
                "name": "letter-of-authorisation-template-110918.docx",
                "size": 398535,
                "confidential": False,
                "block_from_public_file": False,
                "block_reason": None,
                "safe": True,
                "index_state": 3,
                "is_tra": True,
                "created_by": {
                    "id": "0dcab3f3-743e-4fde-a50d-0301a40b7835",
                    "name": "Minnie Mouse",
                    "email": "minnie@mouse.com",
                    "tra": True,
                    "initials": "MM",
                    "colour": "#B500B5",
                    "active": True,
                },
                "created_at": "2020-05-14T10:16:32+0000",
                "virus_scanned_at": "2020-05-14T10:16:40+0000",
                "parent_id": None,
                "checksum": "207b2135a75c97ed4c16368868d66cfd-1",
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
                "id": "8a736af0-9e0c-4e2b-8cca-81b667930f70",
                "name": "first-party-conf.txt",
                "size": 16,
                "confidential": True,
                "block_from_public_file": False,
                "block_reason": None,
                "safe": True,
                "index_state": 3,
                "is_tra": False,
                "created_by": {
                    "id": "efa9826e-8de4-4703-86bf-156c58bc9fe1",
                    "name": "Test User",
                    "email": "test.tester@example.com",
                    "tra": False,
                    "initials": "MHL",
                    "colour": "#00AA55",
                    "active": True,
                },
                "created_at": "2020-07-23T14:19:44+0000",
                "virus_scanned_at": None,
                "parent_id": None,
                "checksum": "94ea43a364905e2b1358a02ccd68e107-1",
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
                "id": "456335de-5fb2-47ed-abca-302240a53bc7",
                "name": "first-party-public.txt",
                "size": 19,
                "confidential": False,
                "block_from_public_file": False,
                "block_reason": None,
                "safe": True,
                "index_state": 3,
                "is_tra": False,
                "created_by": {
                    "id": "efa9826e-8de4-4703-86bf-156c58bc9fe1",
                    "name": "Test User",
                    "email": "test.tester@example.com",
                    "tra": False,
                    "initials": "MHL",
                    "colour": "#00AA55",
                    "active": True,
                },
                "created_at": "2020-07-23T14:19:57+0000",
                "virus_scanned_at": None,
                "parent_id": "8a736af0-9e0c-4e2b-8cca-81b667930f70",
                "checksum": "dedfaea9a2e753fd52251cd14ee52ecf-1",
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
                "safe": True,
                "index_state": 3,
                "is_tra": False,
                "created_by": {
                    "id": "efa9826e-8de4-4703-86bf-156c58bc9fe1",
                    "name": "Test User",
                    "email": "test.tester@example.com",
                    "tra": False,
                    "initials": "MHL",
                    "colour": "#00AA55",
                    "active": True,
                },
                "created_at": "2020-07-23T14:20:08+0000",
                "virus_scanned_at": None,
                "parent_id": None,
                "checksum": "3f3be286819bfd1fe0f6a3fea8b0b0fd-1",
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
                "id": "44be4a8f-3bfb-4a1b-9be0-7dcfa3a4daed",
                "name": "extra-doc-public.txt",
                "size": 2956,
                "confidential": False,
                "block_from_public_file": True,
                "block_reason": "GDPR failure",
                "safe": True,
                "index_state": 3,
                "is_tra": False,
                "created_by": {
                    "id": "efa9826e-8de4-4703-86bf-156c58bc9fe1",
                    "name": "Test User",
                    "email": "test.tester@example.com",
                    "tra": False,
                    "initials": "MHL",
                    "colour": "#00AA55",
                    "active": True,
                },
                "created_at": "2020-07-23T14:20:17+0000",
                "virus_scanned_at": None,
                "parent_id": "d35a6208-7c0f-4ce0-842a-32778f4046d1",
                "checksum": "9ce0a3c8374a366933d82a2bdada2c22-1",
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
