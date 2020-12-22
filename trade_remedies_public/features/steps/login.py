from behave import then, when
from features.steps import shared
from selenium.webdriver.support.ui import WebDriverWait
from features.api_test_objects import create_test_object
from features.steps import shared
from features.steps.utils import get_element_by_id


@when("the user supplies wrong credentials")
def step_impl(context):
    shared.text_is_visible(context, "Email address")
    username_input = context.browser.find_element_by_name("email")
    username_input.send_keys("a@a.com")
    password_input = context.browser.find_element_by_name("password")
    password_input.send_keys("wrong")
    context.browser.find_element_by_name("btn-action").click()


@then('the message "Please correct the following errors" is displayed')
def step_impl(context):
    context.browser.find_element_by_class_name("error-summary")
    shared.text_is_visible(context, "Please correct the following errors")



@when("the user supplies correct credentials")
def enter_account_details(context):
    # Generate test objects
    # create_test_object("case")
    shared.text_is_visible(context, "Email address")
    email_element = get_element_by_id(context, "email")
    email_element.send_keys("foo")
    password_element = get_element_by_id(context, "password_id")
    password_element.send_keys("secret")
    submit_element = get_element_by_id(context, "bdd-submit")
    submit_element.click()


# wait.until(
#         lambda driver: driver.current_url == desired_url)

@then("the user dashboard is displayed")
def see_dashboard(context):
    shared.text_is_visible(context, "This is your dashboard to interact")


