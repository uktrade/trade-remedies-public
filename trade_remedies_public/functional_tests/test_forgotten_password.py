from django.test.testcases import LiveServerTestCase
from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class ForgottenPasswordTestCase(LiveServerTestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.browser = webdriver.Chrome(chrome_options=chrome_options)

    def tearDown(self):
        self.browser.quit()

    def test_forgotten_password_button_redirects_to_forgot_password_page(self):
        self.browser.get(f"{self.live_server_url}/")
        self.browser.find_element(By.ID, "sign_in_button").click()
        self.browser.find_element(By.ID, "forgot_password_link").click()
        self.assertIn(reverse("forgot_password"), self.browser.current_url)
