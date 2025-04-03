import re
import os
import io
import tempfile
import pytest

from playwright.sync_api import expect

from e2e.utils import get_base_url, retry, login_user

BASE_URL = get_base_url()

@retry()
@pytest.mark.order(2)
def test_public_register_interest_in_case(page):

    email = os.environ.get("TEST_USER_EMAIL")
    password = os.environ.get("TEST_USER_PASSWORD")
    case_id = os.environ.get("TEST_REGISTER_INTEREST_CASE_ID")

    login_user(page, email, password, BASE_URL)

    page.get_by_role("link", name="Register interest in a case").first.click()
    page.get_by_role("link", name="Select a Trade Remedies case").click()

    # get the current case
    case_row = page.locator("tr", has=page.get_by_text(case_id))
    
    # Complete the line that was incomplete - click the Select button for the specific case
    case_row.get_by_role("button", name=re.compile(f"Select.*{case_id}")).click()


    page.get_by_role("button", name="Continue").click()
    page.get_by_role("link", name="Organisation details").click()
    page.get_by_label("I work for the organisation").check()
    page.get_by_role("button", name="Continue").click()
    page.get_by_role("link", name="Registration documentation").click()

    pdf_buffer = io.BytesIO()
    pdf_buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<</Type /Catalog\n/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type /Pages\n/Kids [3 0 R]\n/Count 1>>\nendobj\n3 0 obj\n<</Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R>>\nendobj\n4 0 obj\n<</Length 21>>\nstream\nBT /F1 12 Tf 100 700 Td (Test) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000015 00000 n \n0000000061 00000 n \n0000000114 00000 n \n0000000189 00000 n \ntrailer\n<</Size 5/Root 1 0 R>>\nstartxref\n259\n%%EOF")
    
    # Write PDF to temp file
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_pdf:
        temp_pdf.write(pdf_buffer.getvalue())
        temp_pdf.flush()
        
        # Upload non-confidential version first
        page.set_input_files("input[data-type='non_confidential']", temp_pdf.name)

        page.wait_for_timeout(2000)  # Wait 2 seconds between uploads
        
        # Upload confidential version
        page.set_input_files("input[data-type='confidential']", temp_pdf.name)

    # wait 3secs for input file check before clicking continue
    page.wait_for_timeout(3000)
    
    page.get_by_role("button", name="Continue").click()
    page.get_by_role("link", name="Review and submit").click()
    page.get_by_label("I am authorised to provide").check()
    page.get_by_role("button", name="Confirm and submit").click()
    expect(page.get_by_role("heading", name="Registration complete")).to_be_visible()
    page.get_by_role("button", name="Go to my dashboard").click()
