"""Behave-Django.

Behave-Django environment module.
"""
import datetime
import os

from behave_django.testcase import BehaviorDrivenTestCase
from django.conf import settings
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


CAPTURE_PATH = '/app/test-reports/bdd-screenshots/'


def before_scenario(context, scenario):  # no-qa
    BehaviorDrivenTestCase.host = settings.SELENIUM_HOST
    context.timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()


def after_feature(context, feature):  # no-qa
    context.browser.quit()


def configure(context):
    browser = DesiredCapabilities.CHROME
    if "firefox" == settings.SELENIUM_BROWSER:
        browser = DesiredCapabilities.FIREFOX

    context.browser = webdriver.Remote(
        command_executor=f'http://{settings.SELENIUM_HUB_HOST}:4444/wd/hub',
        desired_capabilities=browser,
    )
    context.browser.implicitly_wait(5)
    make_dir(CAPTURE_PATH)


def before_feature(context, feature):  # no-qa
    configure(context)


def after_step(context, step):
    if step.status == 'failed':
        assert context.browser.save_screenshot(
            f'{CAPTURE_PATH}{context.timestamp}-{context.scenario.name}-{step.name}.png'
        )


def make_dir(path):
    """Make directory.

    Checks if directory exists, if not make a directory.
    :param (str) path: Directory to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)
