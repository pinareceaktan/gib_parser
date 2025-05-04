import time
import os
import sys

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import hashlib
import requests

from gib_parser import DriverManager
from gib_parser import get_logger
from gib_parser.helpers.io import save_text, save_pdf, save_csv


base_logger = get_logger(__name__)

SOURCE_URL =  "https://www.gib.gov.tr/"


# Keep them globally so you can change the by and id easily if it gets changed
web_components = {"level_1_combobox": {"by": "id", "component_id": "m_kanun"},
                  "level_2_left_tabs": {"by": By.CSS_SELECTOR, "component_id": "div.solSutun ul li"},
                  "level_3_maddeler_combobox": {"by": By.ID, "component_id": "km-select"},
                  "level_3_maddeler_body": {"by": By.ID, "component_id": "div-icerik-maddeler"},
                  "level_3_gerekceler_href_comp": {"by": By.ID, "component_id": "div-liste-gerekce"},
                  "level_3_gerekceler_body": {"by": By.XPATH, "component_id": "//ul/li[@onclick[contains(., 'div-icerik-gerekce')]]"},
                  "level_3_gerekceler_href": {"by": By.XPATH, "component_id": "//a[contains(text(), 'Buraya')]"},
                  "level_3_ck_karari_tab": {"by": By.ID, "component_id": "mevzuat_ck"},
                  "level_3_ck_karari_body": {"by": By.XPATH, "component_id": "//tr[@class='mevzuat-liste-baslik-satir']"},
                  "level_3_ck_karari_table_header": {"by": By.TAG_NAME, "component_id": "td"},
                  "level_3_ck_karari_table_row": {"by": By.XPATH, "component_id": "//tr[@onclick[contains(., 'div-icerik-ck')]]"},
                  "level_3_ck_karari_table_popup": {"by": By.ID, "component_id": "div-icerik-ck"},
                  "level_3_ck_karari_table_popup_pdf_text": {"by": By.XPATH, "component_id": ".//a[contains(text(), 'tıklayınız')]"},
                  "y": {"by": "", "component_id": ""},
                  "yb": {"by": "", "component_id": ""},

                  }


class ComponentManager:
    def __init__(self, mapping):
        self.mapping = mapping

    def get(self, tag):
        comp = self.mapping[tag]
        return comp["by"], comp["component_id"]



class GibParser:
    def __init__(self, source_web_path, sections_folder, laws_folder):
        self.source_web_path = source_web_path
        self.sections_folder = sections_folder
        self.laws_folder = laws_folder
        self.driver = self.setup_driver()
        self.wait = WebDriverWait(self.driver, 20)
        self.component_manager = ComponentManager(web_components)

    def setup_driver(self):
        driver_manager = DriverManager()
        driver = driver_manager.get_driver()
        driver_manager.pass_page_to_driver(self.source_web_path)
        return driver

    def wait_for_component(self):
        pass

    def parse(self):
        """
        Chooses 'kanun tipi' from the main pages' combobox
        :return:
        """

        # --> Parse lv 1 combobox
        by, cid = self.component_manager.get("level_1_combobox")
        select_lv1 = Select(self.driver.find_element(by, cid))

        # Fetch entire list in combobox
        combobox_options_lv1 = select_lv1.options
        for index in range(1, len(combobox_options_lv1)):  # skip first line

            select_lv1.select_by_index(index)
            self.driver.implicitly_wait(2)

            law_name = combobox_options_lv1[index].text.strip().replace(" ", "_")
            base_logger.info(f"\n➡️Processing Law:<<{law_name}>>")

            # --> Parse lv2 sections under each law
            self.process_sections(law_name)

    def process_sections(self, law_name):
        by, cid = self.component_manager.get("level_2_left_tabs")
        left_elements = self.driver.find_elements(by, cid)

        # Apply strategy pattern

        section_handlers = {
            #"maddeler": self.process_law_matters,
            "gerekçeler": self.process_law_justifications,
            "cumhurbaşkanı_kararları":self.process_presidential_decree,
            "yönetmelikler": None,
            "tebliğler": None,
            "iç_genelgeler": None,
            "genel_yazılar": None,
            "sirküler": None,
            "özelgeler": None

        }

        for left_el in left_elements:
            section_name = left_el.text.strip().replace(" ", "_")
            base_logger.info(f"\n➡️Clicking section:<<{section_name}>>")
            left_el.click()
            time.sleep(10)
            handler = section_handlers.get(section_name.lower())

            if handler:
                handler(law_name, section_name)
            else:
                base_logger.info(f"Skipping section {section_name}")

        self.driver.quit()


    def process_law_matters(self, law_name, section_name):
        """
        Convert plain html to text and save
        :param law_name:
        :param section_name:
        :return:
        """

        by, cid = self.component_manager.get("level_3_maddeler_combobox")
        combobox_lv3 = Select(self.driver.find_element(by, cid))


        # Find the drop down that opens after clicked the left tab maddeler
        combobox_lv3_options = combobox_lv3.options

        for lv3_index, lv3_combobox_el in enumerate(combobox_lv3_options):
            # < -- Process each madde
            if lv3_index == 0:  # skip first line
                continue
            combobox_lv3.select_by_index(lv3_index)
            self.driver.implicitly_wait(5)

            madde_name = lv3_combobox_el.text.strip().replace(" ", "_")
            base_logger.info(f"➡️{section_name}/{madde_name} okunuyor..")

            try:
                by, cid = self.component_manager.get("level_3_maddeler_body")

                content = self.driver.find_element(by, cid)
                time.sleep(15)
                text = content.text.strip()
                if len(text) > 10:  # make sure body is not empty
                    # Save it under sections dir
                    sections_path = os.path.join(self.sections_folder, section_name)
                    os.makedirs(sections_path, exist_ok=True)
                    filename = os.path.join(sections_path, f"{law_name}_{section_name}_{madde_name}.txt")
                    save_text(text, filename)

                    # Save it under laws dir
                    laws_path = os.path.join(self.laws_folder, law_name)
                    os.makedirs(laws_path, exist_ok=True)
                    filename = os.path.join(laws_path, f"{law_name}_{section_name}_{madde_name}.txt")
                    save_text(text, filename)

                else:
                    base_logger.warning("⚠️ Empty, didnt write")
            except Exception as e:
                base_logger.warning(f"❌️ No content {e}")

    def process_law_justifications(self, law_name, section_name):
        """
        Download law justifications pdfs embed in Buraya in html body
        """

        # Smart weight to justifications to be filled properly
        wait = WebDriverWait(self.driver, 20)
        by, cid = self.component_manager.get("level_3_gerekceler_href_comp")
        wait.until(EC.presence_of_element_located((by, cid)))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//ul/li[@onclick[contains(., 'div-icerik-gerekce')]]")) > 0)

        by, cid = self.component_manager.get("level_3_gerekceler_body")
        justification_elements = self.driver.find_elements(by, cid)

        time.sleep(10)

        for jel in justification_elements:

            try:
                # Fetch justification title
                justification_law_name = jel.text.strip().replace(" ", "_")

                # Click and wait for content to get loaded
                jel.click()
                time.sleep(10)

                # Find Buraya word to fetch embedded href
                by, cid = self.component_manager.get("level_3_gerekceler_href")
                pdf_link_element = self.driver.find_element(by, cid)
                pdf_url = pdf_link_element.get_attribute("href")

                # Make path absolute, if it comes as relative
                if pdf_url.startswith("fileadmin"):
                    pdf_url = SOURCE_URL + pdf_url

                # Download and save pdf
                response = requests.get(pdf_url)

                # Save it under sections dir
                sections_path = os.path.join(sections_folder, section_name)
                os.makedirs(sections_path, exist_ok=True)
                filename = os.path.join(sections_path, f"{law_name}_{section_name}_{justification_law_name}.pdf")
                save_pdf(response.content, filename)

                # Save it under laws dir
                laws_path = os.path.join(laws_folder, law_name)
                os.makedirs(laws_path, exist_ok=True)
                filename = os.path.join(laws_path, f"{law_name}_{section_name}_{justification_law_name}.pdf")
                save_pdf(response.content, filename)


            except Exception as e:
                base_logger.info(f"❌ {jel.text.strip()} için PDF bulunamadı veya hata oluştu: {e}")

    def process_presidential_decree(self, law_name, section_name):
        """

        """
        by, cid = self.component_manager.get("level_3_ck_karari_tab")

        self.driver.find_element(by, cid).click()

        # Wait until component to be filled properly
        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "div-liste-ck")))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-icerik-ck')]]")) > 0)

        # Start to parsing the table
        by, cid = self.component_manager.get("level_3_ck_karari_body")
        header_row = self.driver.find_element(by, cid)

        by, cid = self.component_manager.get("level_3_ck_karari_table_header")
        header_cols = header_row.find_elements(by, cid)
        headers = [col.text.strip() for col in header_cols]

        # 2. Find content rows, each of them are a tr component with onclick events
        by, cid = self.component_manager.get("level_3_ck_karari_table_row")
        data_rows = self.driver.find_elements(by, cid)
        # Process table
        all_data = []
        for ix, row in enumerate(data_rows):
            by, cid = self.component_manager.get("level_3_ck_karari_table_header")

            cols = row.find_elements(by, cid)

            # Process row and generate unique id
            if len(cols) >= len(headers):
                row_dict = dict()
                for ix, header in enumerate(headers):
                    row_dict.update({header: str(cols[ix].text).strip()})
                unique_id = generate_hash_from_dict(row_dict)
                row_dict.update({"id": unique_id})
                # Get Pop up  texts and pdf link if provided
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                    self.driver.execute_script("arguments[0].click();", row)
                    time.sleep(2)
                    # wait for the content
                    wait = WebDriverWait(self.driver, 10)
                    by, cid = self.component_manager.get("level_3_ck_karari_table_popup")
                    wait.until(EC.presence_of_element_located((by, cid)))

                    content_div = self.driver.find_element(by, cid)
                    # Get the popup text
                    full_text = content_div.text.strip()
                    row_dict.update({"Detay Aciklama": full_text})

                    # Get the link if provided
                    by, cid = self.component_manager.get("level_3_ck_karari_table_popup_pdf_text")
                    link_element = content_div.find_element(by, cid)
                    pdf_url = link_element.get_attribute("href")

                    # Make url absolute if needed
                    if pdf_url.startswith("/"):
                        pdf_url = SOURCE_URL + pdf_url

                    # --> Save related pdfs
                    # Generate file_name from order no
                    ck_order_no = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                    # Download pdf
                    response = requests.get(pdf_url)

                    # Save it under sections dir
                    sections_path = os.path.join(sections_folder, section_name)
                    os.makedirs(sections_path, exist_ok=True)
                    filename = os.path.join(sections_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                    save_pdf(response.content, filename)
                    row_dict.update({"related_pdf_path": filename})


                    # Save it under laws dir
                    laws_path = os.path.join(laws_folder, law_name)
                    os.makedirs(laws_path, exist_ok=True)
                    filename = os.path.join(laws_path, f"{kanun_adi}_{section_title}_{ck_order_no}_{unique_id}.pdf")
                    save_pdf(response.content, filename)

                except Exception as e:
                    logger.debug(f"Failed downloading related pdf, error processing line {ix}: {str(e)}")

                all_data.append(row_dict)

        df = pd.DataFrame(all_data, columns=headers)

        # Save table under sections
        sections_path = os.path.join(sections_folder, section_name)
        os.makedirs(sections_path, exist_ok=True)
        filename = os.path.join(sections_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)

        # Save table under laws
        laws_path = os.path.join(laws_folder, law_name)
        os.makedirs(laws_path, exist_ok=True)
        filename = os.path.join(laws_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)



    def close(self):
        self.driver.quit()
