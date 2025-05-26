from functools import wraps

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from gib_parser.utils import logger

base_logger = logger.get_logger(__name__)


def wait_for_children(timeout: int = 20):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Örnek: process_presidential_decree --> presidential_decree
            method_name = func.__name__
            section = method_name.replace("process_", "")

            # web_component_registry içinde anahtarları bu isme göre bul
            tab_tag = f"level_3_{section}_tab"
            body_tag = f"level_3_{section}_body"

            # Main component gelene kadar bekle
            by_tab, cid_tab = self.component_manager.get_component_id_by_tag(tab_tag)
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by_tab, cid_tab)))

            # Eğer body için de doluluk bekleniyorsa
            by_body, cid_body = self.component_manager.get_component_id_by_tag(body_tag)
            WebDriverWait(self.driver, timeout).until(
                lambda d: len(d.find_elements(by_body, cid_body)) > 0
            )

            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def wait_for_element(timeout=15, wait_for_options=False):
    def decorator(func):
        @wraps(func)
        def wrapper(self, by, cid, *args, **kwargs):
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, cid)))

            if wait_for_options:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: len(Select(d.find_element(by, cid)).options) > 1
                )

            return func(self, by, cid, *args, **kwargs)
        return wrapper
    return decorator


# singleton driver
class SeleniumClient:
    def __init__(self, source_web_page, headless=False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.implicitly_wait(3)
        self._pass_page_to_driver(source_web_page)
        base_logger.info("Driver initialized")

    def _pass_page_to_driver(self, source_web_page):
        self.driver.get(source_web_page)
        base_logger.info(f"Passed {source_web_page} to driver")


    def get_driver(self):
        return self.driver


    def make_driver_wait(self):
        base_logger.info("make driver wait")
        WebDriverWait(self.driver, 20)

    @wait_for_element(wait_for_options=True)
    def find_and_select_single_element(self, by, component_id):
        return Select(self.driver.find_element(by, component_id))

    @staticmethod
    def get_single_element_options(component: webdriver):
        return component.options


    def select_component(self):
        pass

    def click_component(self):
        pass

    def find_element(self):
        pass

    def find_elements(self):
        pass

