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
from selenium.webdriver.support.expected_conditions import visibility_of


from gib_parser.helpers.abstract_classes import AbstractParsingClient
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
            """
            Wait for the child element represented -> by, cid
            """
            WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located((by, cid)))

            if wait_for_options:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: len(Select(d.find_element(by, cid)).options) > 1
                )

            return func(self, by, cid, *args, **kwargs)
        return wrapper
    return decorator



def wait_for_element_agnostic(timeout=15, wait_for_options=False):
    def decorator(func):
        @wraps(func)
        def wrapper(self, element, *args, **kwargs):
            """
            Wait for the child element represented -> element, agnostic of the child element
            """
            WebDriverWait(self.driver, timeout).until(visibility_of(element))

            if wait_for_options:
                WebDriverWait(self.driver, timeout).until(
                    lambda d: len(element.find_elements(By.XPATH, "./*")) > 0
                )

            return func(self, element, *args, **kwargs)
        return wrapper
    return decorator


def wait_for_id_to_be_filled(timeout=15):
    def decorator(func):
        @wraps(func)
        def wrapper(self, by, component_id, *args, **kwargs):
            """
            Wait for the child element represented -> element, agnostic of the child element
            """
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.find_element(by, component_id).text.strip() != ""
            )

            return func(self, by, component_id , *args, **kwargs)

        return wrapper

    return decorator


# singleton driver
class SeleniumClient(AbstractParsingClient):
    def __init__(self, source_web_page, headless=False, timeout=20):
        super().__init__()
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

    # will be deprecated
    def make_driver_wait(self):
        base_logger.info("make driver wait")
        WebDriverWait(self.driver, 20)


    def make_driver_wait_for_a_text(self, outer_component, inner_component, min_cards, timeout=20):
        """

        """
        outer_component_by, outer_component_cid = outer_component
        inner_component_by, inner_component_cid = inner_component

        WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((outer_component_by, outer_component_cid))
        )
        WebDriverWait(self.driver, timeout).until(
            lambda d: len(d.find_elements(inner_component_by, inner_component_cid)) >= min_cards
        )

    @wait_for_element(wait_for_options=True)
    def find_and_select_single_element(self, by, component_id):
        return Select(self.driver.find_element(by, component_id))

    @staticmethod
    def get_single_element_options(component: webdriver):
        return component.options


    @wait_for_element(wait_for_options=False)
    def find_elements(self, by, component_id):
        return self.driver.find_elements(by, component_id)

    @staticmethod
    @wait_for_element_agnostic
    def click_component(component: webdriver):
        component.click()


    def select_component(self):
        pass

    @wait_for_id_to_be_filled()
    def find_element(self, by, component_id):
        return self.driver.find_element(by, component_id)

    @staticmethod
    def find_element_in_element(element, by, component_id):
        return element.find_elements(by, component_id)

    def click_on_click_inner_elements(self, spider_element):
        for s in spider_element:
            if s.get_attribute("onclick"):
                self.click_component(s)
                break
        self.driver.execute_script("arguments[0].scrollIntoView(true);", s)
        self.driver.execute_script("arguments[0].click();", s)

        return True

    def go_to_page(self, page_num, timeout=10):
        nav = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'nav[aria-label="pagination navigation"]'))
        )

        selectors = [
            f'button[aria-label="Go to page {page_num}"]',
            f'button[aria-label="page {page_num}"]',
        ]

        btn = None
        for sel in selectors:
            try:
                btn = nav.find_element(By.CSS_SELECTOR, sel)
                break
            except Exception:
                pass

        if btn is None:
            # metne göre fallback (daha toleranslı)
            btn = nav.find_element(By.XPATH, f'.//button[normalize-space(text())="{page_num}"]')

        if btn is None:
            return False

        self.driver.execute_script("arguments[0].scrollIntoView(true);", btn)
        WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(btn))
        btn.click()

        return True

    def click_in_new_tab(self, web_element_to_click):
        """
        Open web element to click in new tab
        """
        main_tab = self.driver.current_window_handle
        self.driver.execute_script("arguments[0].click();", web_element_to_click)

        WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > 1)
        new_tab = [h for h in self.driver.window_handles if h != main_tab][0]
        self.driver.switch_to.window(new_tab)

    def click_component_by_xpath(self, xpath, timeout=10):
        wait = WebDriverWait(self.driver, timeout)

        tab = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        tab = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))

        self.driver.execute_script("arguments[0].scrollIntoView({block:'center',inline:'center'});", tab)
        try:
            tab.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", tab)

        # confirm via aria-selected
        try:
            wait.until(EC.presence_of_element_located(
                (By.XPATH, f"{xpath}[@aria-selected='true']")))
        except TimeoutError:
            pass



