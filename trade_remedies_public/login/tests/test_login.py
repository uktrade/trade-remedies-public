from django.urls import reverse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class Login:
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.browser = webdriver.Chrome(chrome_options=chrome_options)

    def tearDown(self):
        self.browser.quit()

    def test_landing(self):
        self.browser.get(f"{self.live_server_url}/")
        self.assertIn("Start", self.browser.title)
        self.assertIn(
            "The UK’s Trade Remedies Authority (TRA) investigates whether new trade remedies "
            "are needed to prevent injury to UK industries caused by unfair trading "
            "practices and unforeseen surges in imports.",
            self.browser.find_element_by_tag_name("body").get_attribute("innerText"),
        )

    def test_login_button(self):
        self.browser.get(f"{self.live_server_url}/")
        self.browser.find_element_by_id("sign_in_button").click()
        self.assertIn(reverse("login"), self.browser.current_url)

    def test_password_show_hide(self):
        self.browser.get(f'{self.live_server_url}{reverse("login")}')
        self.assertEqual(
            self.browser.find_element_by_name("password").get_attribute("type"), "password"
        )
        self.browser.find_element_by_id("show_password").click()
        self.assertEqual(
            self.browser.find_element_by_name("password").get_attribute("type"), "text"
        )
