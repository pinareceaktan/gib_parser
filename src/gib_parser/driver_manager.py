from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from gib_parser.utils import logger

base_logger = logger.get_logger(__name__)


class DriverManager:
    def __init__(self, headless=False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.implicitly_wait(3)
        base_logger.info("Driver initialized")

    def get_driver(self):
        return self.driver

    def pass_page_to_driver(self, source_web_page):
        self.driver.get(source_web_page)
        base_logger.info(f"Passed {source_web_page} to driver")

    def close(self):
        if self.driver:
            self.driver.quit()
