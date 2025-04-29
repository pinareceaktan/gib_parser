import sys
import time
import requests
import os
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import hashlib

sys.path.append(str(Path(__file__).resolve().parents[1]))

from gib_parser.utils.logger import get_logger
from gib_parser.utils import generate_hash_from_dict
from gib_parser.driver_manager import DriverManager


os.environ["DEFAULT_LOG_LEVEL"] = "info"
os.environ["FLUSH_TO_CONSOLE"] = "True"
os.environ["SOURCE_WEB_PATH"] = "https://www.gib.gov.tr/gibmevzuat"

logger = get_logger(__name__)


# Definitions
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "..", "output")

os.environ["OUTPUT_DIR"] = os.getenv("OUTPUT_DIR") if os.getenv("OUTPUT_DIR") else DEFAULT_OUTPUT_DIR
os.makedirs(os.getenv("OUTPUT_DIR"), exist_ok=True)

sections_folder = os.path.join(os.getenv("OUTPUT_DIR"), "sections")
os.makedirs(sections_folder, exist_ok=True)
logger.info("sections created" if "sections" in os.listdir(
    os.getenv('OUTPUT_DIR')) else "failed while creating sections folder")

laws_folder = os.path.join(os.getenv("OUTPUT_DIR"), "laws")
os.makedirs(laws_folder, exist_ok=True)
logger.info(
    "laws created" if "sections" in os.listdir(os.getenv('OUTPUT_DIR')) else "failed while creating laws folder")


logger.debug(f"Source web path is set to: {SOURCE_WEB_PATH}")
logger.debug(f"Output file path is set to: {os.getenv('OUTPUT_DIR')}")

# Selenium


# ** Ilk combobox, kanun tipini secer
select_element_lv1 = driver.find_element("id", "m_kanun")
select_lv1 = Select(select_element_lv1)
# Bu comboboxtaki tum elemanlari al
combobox_options_lv1 = select_lv1.options

# Process all elements in dropdown
for index in range(1, len(combobox_options_lv1)):  # skip first line

    select_lv1.select_by_index(index)
    driver.implicitly_wait(2)

    kanun_adi = combobox_options_lv1[index].text.strip().replace(" ", "_")
    logger.info(f"\n➡️Processing Law:<<{kanun_adi}>>")

    # * Simdi level 1 de acilan sayfadaki sol tablodan secim yapacagiz
    left_component_elements = driver.find_elements(By.CSS_SELECTOR, "div.solSutun ul li")
    for left_el in left_component_elements:
        section_title = left_el.text.strip().replace(" ", "_")

        logger.info(f"\n➡️Clicking Section: {section_title}")



        if section_title.lower() == "cumhurbaşkanı_kararları":


        if section_title.lower() == "yönetmelikler":
            print("ece")
            pass
        if section_title.lower() == "tebliğler":
            print("ece")
            pass
        if section_title.lower() == "iç_genelgeler":
            print("ece")
            pass
        if section_title.lower() == "genel_yazılar":
            print("ece")
            pass
        if section_title.lower() == "sirküler":
            print("ece")
            pass
        if section_title.lower() == "özelgeler":
            print("ece")
            pass

    # # PDF bağlantılarını bul
    # links = driver.find_elements("xpath", "//a[contains(@href, '.pdf')]")
    # for link in links:
    #     pdf_url = link.get_attribute("href")
    #     pdf_name = pdf_url.split("/")[-1]
    #     pdf_path = os.path.join(os.getenv("OUTPUT_DIR"), pdf_name)
    #
    #     # PDF dosyasını indir
    #     response = requests.get(pdf_url)
    #     with open(pdf_path, "wb") as f:
    #         f.write(response.content)
    #     print(f"{pdf_name} indirildi.")

driver.quit()
