from django.test.testcases import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class MyTestCase(LiveServerTestCase):
    def setUp(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        self.browser = webdriver.Chrome(chrome_options=chrome_options)

    def tearDown(self):
        print("we made it")
        self.browser.quit()

    def test_smoke(self):
        self.browser.get("%s%s" % (self.live_server_url, "/"))
