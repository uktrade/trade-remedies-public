from behave import then, when
from features.steps import shared
from selenium.webdriver.support.ui import WebDriverWait


@when("the user tries to log in with correct credentials")
def step_impl(context):
    shared.text_is_visible(context, "Email address")
    username_input = context.browser.find_element_by_name("email")
    username_input.send_keys("luisella21@hotmail.com")
    password_input = context.browser.find_element_by_name("password")
    password_input.send_keys("a-pAssword1")
    context.browser.find_element_by_name("btn-action").click()
    # raise NotImplementedError(u'STEP: When the user tries to log in with wrong credentials')
    # WebDriverWait(context.browser, 5000).until(
    #     ec.presence_of_element_located((By.ID, "foo"))
    # )
    pass
    # raise NotImplementedError(u'STEP: When the user tries to log in with correct credentials')


@then("the user dashboard is displayed")
def step_impl(context):
    shared.text_is_visible(context, "This is your dashboard to interact")


@when("the user tries to log in with wrong credentials")
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
