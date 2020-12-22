from django.contrib.auth import get_user_model
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec


User = get_user_model()

def get_element_by_id(context, id):
    return WebDriverWait(context.browser, 500).until(
        ec.presence_of_element_located((By.ID, id))
    )


def login(context, email, password):
    """Enter username and password and click on Sign in."""
    username_field = context.browser.find_element(By.ID, "email")
    password_field = context.browser.find_element(By.ID, "password_id")
    submit_button = context.browser.find_element(By.XPATH, '//button[contains(text(),"Sign in")]')
    username_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()


def go_to_page(context, url_name, **kwargs):
    """Navigate to page with given url name."""
    url = context.get_url(url_name, **kwargs)
    context.browser.get(url)


def assert_on_page(context, expected_url_name, **kwargs):
    """Assert current url is the expected url."""
    page_url = context.browser.current_url.split("?")[0]
    expected_url = context.get_url(expected_url_name, **kwargs)
    assert expected_url == page_url, f"expecting url to be {expected_url} but got {page_url}"


def find_element_by_text(context, text, element_type="*"):
    try:
        return context.browser.find_element(
            By.XPATH, f'//{element_type}[contains(text(),"{text}")]'
        )
    except Exception as e:
        print(e)
        return None
