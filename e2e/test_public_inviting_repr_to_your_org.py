import os
import io
import tempfile
import pytest

from playwright.sync_api import expect

from e2e.utils import get_base_url, retry, login_user, generate_test_name

BASE_URL = get_base_url()

@retry()
@pytest.mark.order(3)
def test_public_invite_repr_to_your_org(page):

    email = os.environ.get("TEST_USER_EMAIL")
    password = os.environ.get("TEST_USER_PASSWORD")
    case_name = os.environ.get("TEST_REPR_INVITE_CASE_NAME")

    login_user(page, email, password, BASE_URL)

    page.locator("#lnk_manage_your_team").click()
    page.get_by_role("link", name="Invite user").click()
    page.get_by_label("A representative, for example").check()
    page.get_by_role("button", name="Continue").click()
    page.get_by_role("link", name="Select a Trade Remedies case").click()
    

    # Select a random case
    page.get_by_label(case_name).check()
    page.get_by_role("button", name="Continue").click()

    page.get_by_role("link", name="Organisation details").click()
    page.get_by_label("Organisation name").click()
    page.get_by_label("Organisation name").fill("Representitive 365 LTD")
    page.get_by_label("Contact name").click()
    page.get_by_label("Contact name").fill(generate_test_name())

    page.wait_for_timeout(200)
    page.get_by_label("Contact email address").click()
    page.get_by_role("button", name="Continue").click()
    page.get_by_role("link", name="Letter of Authority").click()

    pdf_buffer = io.BytesIO()
    pdf_buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<</Type /Catalog\n/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type /Pages\n/Kids [3 0 R]\n/Count 1>>\nendobj\n3 0 obj\n<</Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R>>\nendobj\n4 0 obj\n<</Length 21>>\nstream\nBT /F1 12 Tf 100 700 Td (Test) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000015 00000 n \n0000000061 00000 n \n0000000114 00000 n \n0000000189 00000 n \ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n259\n%%EOF")
    
    # Write PDF to temp file
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_pdf:
        temp_pdf.write(pdf_buffer.getvalue())
        temp_pdf.flush()

        # Upload the PDF
        page.set_input_files("input[data-type='confidential']", temp_pdf.name)

    # wait 3secs for input file check before clicking continue
    page.wait_for_timeout(3000)

    page.get_by_role("button", name="Continue").click()
    page.get_by_role("link", name="Review and submit").click()
    page.get_by_role("button", name="Confirm and submit invite").click()
    expect(page.get_by_role("heading", name="Invite sent")).to_be_visible()
    page.get_by_role("link", name="Manage team").click()
    page.locator("ol").get_by_role("link", name="Home").click()
    expect(page.get_by_text("You have pending invites:")).to_be_visible()
