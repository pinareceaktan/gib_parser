from functools import wraps
import time

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
TIMEOUT =10


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


    def click_component(self, by, cid, timeout=TIMEOUT):
        """
        Wait until the element to be clickable and click
        by:
        cid:
        timeout:
        """

        wait = WebDriverWait(self.driver, 10)
        element = wait.until(EC.element_to_be_clickable((by, cid)))
        element.click()


    def find_element(self, by, component_id, timeout=TIMEOUT):
        wait = WebDriverWait(self.driver, 10)
        element = wait.until(EC.presence_of_element_located((by, component_id)))
        return element

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
            try:
                btn = nav.find_element(By.XPATH, f'.//button[normalize-space(text())="{page_num}"]')
            except Exception:
                return False

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

    def get_main_page(self, timeout=TIMEOUT):
        wait = WebDriverWait(self.driver, timeout)
        container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "main")))
        return container


    def collect_all_box_components(self, timeout=TIMEOUT, include_filter_box=False, scope="active_panel")->dict:
        """
        scope: "active_panel" -> sadece görünür tabpanel (önerilen)
               "main"         -> tüm sayfa ana içeriği
        include_filter_box: True ise combobox'ı içeren ilk box'ı da dahil eder
        """
        wait = WebDriverWait(self.driver, timeout)

        # Get to the main page/ active panel
        container = self.get_main_page()

        # 2) Box component için yapısal, metinden bağımsız selector
        # - data-testid="box-component"
        # - içinde gerçek içerik var: (cms-content veya typography-component)
        # - combobox içeren filtre box'ını dışla (istersen include_filter_box=True yap)
        xp = ".//div[@data-testid='box-component']" \
             "[.//div[contains(@class,'cms-content')] or .//*[@data-testid='typography-component']]"
        if not include_filter_box:
            xp = xp.replace("]", "][not(.//input[@role='combobox'])]")  # combobox'lı olanı çıkar

        # 3) Adetini al, her turda locate et (stale riskine karşı)
        boxes_count = len(container.find_elements(By.XPATH, xp))
        # results = []
        texts = ""
        for i in range(1, boxes_count + 1):
            box = container.find_element(By.XPATH, f"({xp})[{i}]")
            html = box.get_attribute("outerHTML")
            text = (box.text or "").strip()
            # Çok boş wrapper'ları at
            if not text and "cms-content" not in html:
                continue
            # results.append({"index": i, "text": text, "html": html})
            texts += text
            # sleep a little
            time.sleep(0.05)
        return {"content": texts}


    def get_law_justification_link_from_arrow(self, timeout=TIMEOUT)->dict:

        wait = WebDriverWait(self.driver, timeout)

        # Keep root to turn back to the old tab later
        root = self.driver.current_window_handle


        # 1) Metne bağlı olmadan: pointer'lı satırda LaunchIcon'u hedefle
        #    (ilk satırı istiyorsan [1], hepsini almak istersen [.] kaldırıp find_elements kullan)
        row = wait.until(EC.presence_of_element_located((
            By.XPATH,
            ".//*[contains(@style,'cursor') and contains(@style,'pointer')]"
            "[.//*[@data-testid='LaunchIcon' or local-name()='svg']][1]"
        )))
        # 2) "XX KANUNU" satırındaki kırmızı ok (LaunchIcon) elemanını bul

        arrow = row.find_element(By.XPATH, ".//*[@data-testid='LaunchIcon' or local-name()='svg']")

        # 3) Tıklanabilir ata (anchor varsa onu; yoksa pointer stiline sahip kapsayıcı) ve tıkla
        try:
            clickable = arrow.find_element(By.XPATH, "ancestor::a[1]")
        except NoSuchElementException:
            # anchor yoksa, pointer stiline sahip en yakın kapsayıcıyı kullan
            try:
                clickable = arrow.find_element(By.XPATH, "ancestor::*[contains(@style,'cursor')][1]")
            except NoSuchElementException:
                clickable = arrow  # son çare: ikonun kendisi

        # 4) Yeni sekmeye geç
        existing = set(self.driver.window_handles)
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", clickable)
        try:
            wait.until(EC.element_to_be_clickable(clickable)).click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", clickable)

        # Get to the new tab
        wait.until(lambda d: len(d.window_handles) > len(existing))
        new_handle = [h for h in self.driver.window_handles if h not in existing][0]
        self.driver.switch_to.window(new_handle)

        # wait for new tab to be loaded
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        # get the new tab's main
        main = self.get_main_page()
        pdf_link = main.find_element(
            By.XPATH,
            ".//a[contains(@href,'.pdf') or contains(@href,'/file/getFile')]"
        )

        pdf_url = pdf_link.get_attribute("href")
        # Get cookies of selenium session
        cookies = {c["name"]: c["value"] for c in self.driver.get_cookies()}
        headers = {"User-Agent": self.driver.execute_script("return navigator.userAgent")}

        # close the new tab
        self.driver.close()
        self.driver.switch_to.window(root)

        return {"pdf_url": pdf_url, "cookies": cookies, "headers": headers}