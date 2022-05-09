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

    def test_forgotten_password_button_redirects_to_page(self):
        self.browser.get(f"{self.live_server_url}/")
        self.browser.find_element(By.ID, "forgotten_password_button").click()
        self.assertIn(reverse("forgotten_password"), self.browser.current_url)

