import pytest

from playwright.sync_api import expect

from e2e.utils import get_base_url, retry, generate_test_name, generate_test_email, generate_test_password, generate_test_address, genetrate_test_postcode

@retry()
@pytest.mark.dependency(depends=["test_login_with_valid_credentials"])
def test_public_register_interest_in_case(page, session_data):
    pass
