from behave import then, when

from features.steps import shared
from features.steps.utils import get_element_by_id


@when("the user supplies wrong credentials")
def step_wrong_credentials(context):
    email = "a@a.com"
    password = "wrong"
    shared.text_is_visible(context, "Email address")
    email_element = get_element_by_id(context, "email")
    email_element.send_keys(email)
    password_element = get_element_by_id(context, "password_id")
    password_element.send_keys(password)
    submit_element = get_element_by_id(context, "login-submit")
    submit_element.click()


@then('the message "Please correct the following errors" is displayed')
def step_impl(context):
    context.browser.find_element_by_class_name("error-summary")
    shared.text_is_visible(context, "Please correct the following errors")


@when("the user supplies correct credentials")
def enter_account_details(context):
    email = context.public_user
    password = context.password
    shared.text_is_visible(context, "Email address")
    email_element = get_element_by_id(context, "email")
    email_element.send_keys(email)
    password_element = get_element_by_id(context, "password_id")
    password_element.send_keys(password)
    submit_element = get_element_by_id(context, "login-submit")
    submit_element.click()


@then("the user dashboard is displayed")
def see_dashboard(context):
    shared.text_is_visible(context, "This is your dashboard to interact")


@when("the user click it")
def user_logout(context):
    context.browser.find_element_by_link_text("Logout").click()
