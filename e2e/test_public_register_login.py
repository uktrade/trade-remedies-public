import pytest

from playwright.sync_api import expect

from e2e.utils import get_base_url, retry, generate_test_name, generate_test_email, generate_test_password, generate_test_address, genetrate_test_postcode

BASE_URL = get_base_url()

@retry()
@pytest.mark.order(1)
def test_public_login(page):
    page.goto(BASE_URL)
    expect(page.get_by_role("heading", name="Trade Remedies Service: sign")).to_be_visible()
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_role("button", name="Sign in")).to_be_visible()


@retry()
@pytest.mark.order(1)
def test_public_register(page):
    page.goto(BASE_URL)
    expect(page.get_by_role("heading", name="Trade Remedies Service: sign")).to_be_visible()
    expect(page.get_by_role("link", name="Create an account")).to_be_visible()
    page.get_by_role("link", name="Create an account").click()
    page.get_by_role("heading", name="Has anyone else from your").click()
    page.get_by_label("No").check()
    page.get_by_role("button", name="Continue").click()
    expect(page.get_by_role("heading", name="Create an account")).to_be_visible()


@retry()
@pytest.mark.order(1)
@pytest.mark.dependency(name="test_register_user_with_new_org", scope="session")
def test_register_user_with_new_org(page, session_data):

    email = generate_test_email()
    name = generate_test_name()
    password = generate_test_password()
    address = generate_test_address()
    postcode = genetrate_test_postcode()

    page.goto(BASE_URL)
    expect(page.get_by_role("heading", name="Trade Remedies Service: sign")).to_be_visible()
    expect(page.get_by_role("link", name="Create an account")).to_be_visible()
    page.get_by_role("link", name="Create an account").click()
    page.get_by_role("heading", name="Has anyone else from your").click()
    page.get_by_label("No").check()
    page.get_by_role("button", name="Continue").click()
    page.get_by_label("Enter your name").click()
    page.get_by_label("Enter your name").fill(name)
    page.get_by_label("Your email address").click()
    page.get_by_label("Your email address").fill(email)
    page.get_by_label("I have read and understood").check()
    page.get_by_role("button", name="Continue").click()
    page.get_by_label("Enter Password").click()
    page.get_by_label("Enter Password").fill(password)
    page.get_by_role("button", name="Continue").click()
    expect(page.get_by_role("heading", name="Two-factor authentication")).to_be_visible()
    expect(page.get_by_text("How would you like to receive")).to_be_visible()
    page.locator('input.govuk-radios__input[id="email"]').click()
    page.get_by_role("button", name="Continue").click()
    expect(page.get_by_text("Is your organisation a UK")).to_be_visible()
    page.get_by_label("No").check()
    page.get_by_role("button", name="Continue").click()
    page.get_by_label("Name of your organisation").click()
    page.get_by_label("Name of your organisation").fill(f"{name} LTD")
    page.get_by_label("Street address").click()
    page.get_by_label("Street address").fill(address)
    page.get_by_label("Postcode or zip code").click()
    page.get_by_label("Postcode or zip code").fill(postcode)
    page.get_by_label("Country").select_option("GB")
    page.get_by_label("Organisation registration").click()
    page.get_by_label("Organisation registration").fill("12345678")
    page.get_by_role("button", name="Continue").click()
    expect(page.get_by_role("heading", name="Further details about your")).to_be_visible()
    expect(page.get_by_role("button", name="Create my account")).to_be_visible()
    page.get_by_role("button", name="Create my account").click()
    page.locator("#main-content").get_by_role("link", name="Sign in").click()
    expect(page.get_by_role("heading", name="Sign in to Trade Remedies")).to_be_visible()

    # store user name and password for later use in another test
    session_data["email"] = email
    session_data["password"] = password


@retry()
@pytest.mark.order(1)
def test_login_with_invalid_credentials(page):
    page.goto(BASE_URL)
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_role("heading", name="Sign in to Trade Remedies")).to_be_visible()
    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill("test@email.com")
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("123456789")
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_label("There is a problem")).to_be_visible()


@retry()
@pytest.mark.order(1)
@pytest.mark.dependency(depends=["test_register_user_with_new_org"], scope="session")
@pytest.mark.dependency(name="test_login_with_valid_credentials", scope="session")
def test_login_with_valid_credentials(page, session_data):
    email = session_data["email"]
    password = session_data["password"]
    page.goto(BASE_URL)
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_role("heading", name="Sign in to Trade Remedies")).to_be_visible()

    page.get_by_label("Email address").click()
    page.get_by_label("Email address").fill(email)
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Sign in").click()
    expect(page.get_by_text("Verify your email address", exact=True)).to_be_visible()
