from django.contrib.auth import get_user_model
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

User = get_user_model()


def get_element_by_id(context, id):
    return WebDriverWait(context.browser, 10).until(ec.presence_of_element_located((By.ID, id)))


def login(context, email, password):
    """Enter username and password and click on Sign in."""
    username_field = context.browser.find_element(By.ID, "email")
    password_field = context.browser.find_element(By.ID, "password_id")
    submit_button = context.browser.find_element(By.XPATH, '//button[contains(text(),"Sign in")]')
    username_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()


def testuser_login(context):
    email = context.user
    password = context.password
    login(context, email, password)


def go_to_page(context, view_name, **kwargs):
    """Navigate to page with given url name."""
    url = context.get_url(view_name, **kwargs)
    print(f"==============={view_name}  {url}")
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



# def create_test_user(context):
#     if not hasattr(context, 'user'):
#         test_user_email = "test@test.com"
#         test_password = "test_password"
#
#         test_user, _ = get_user_model().objects.get_or_create(
#             email=test_user_email
#         )
#         test_user.is_staff = True
#         test_user.is_superuser = True
#         test_user.set_password(test_password)
#         test_user.save()
#
#         context.user = test_user
#
#         client = context.test.client
#         client.login(
#             email=test_user_email,
#             password=test_password,
#         )
#
#         # Then create the authenticated session using the new user credentials
#         session = SessionStore()
#         session[SESSION_KEY] = test_user.pk
#         session[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
#         session[HASH_SESSION_KEY] = test_user.get_session_auth_hash()
#         session.save()
#
#         # Finally, create the cookie dictionary
#         cookie = {
#             'name': settings.SESSION_COOKIE_NAME,
#             'value': session.session_key,
#             'secure': False,
#             'path': '/',
#         }
#
#         context.browser.get(f'{context.base_url}/admin/login/')
#         context.browser.add_cookie(cookie)
#         context.browser.refresh()  # need to update page for logged in user
#         context.browser.get(f'{context.base_url}/')