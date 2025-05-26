import time
import os
import sys

from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

import pandas as pd
import hashlib
import requests

from gib_parser import get_logger
from gib_parser import save_text, save_pdf, save_csv, generate_hash_from_dict

base_logger = get_logger(__name__)

SOURCE_URL =  "https://www.gib.gov.tr/"


# Gib pages parsing logic

class GibPageOrchestrator:
    def __init__(self,
                 parser : Optional,
                 component_manager: Optional,
                 sections_folder :str,
                 laws_folder: str):

        self.parser = parser
        self.sections_folder = sections_folder
        self.laws_folder = laws_folder
        self.component_manager = component_manager


    def parse(self):
        """
        Chooses 'kanun tipi' from the main pages' combobox
        :return:
        """

        # --> Parse lv 1 combobox
        by, cid = self.component_manager.get_component_id_by_tag("level_1_combobox")
        select_lv1 = self.parser.find_and_select_single_element(by, cid)

        # Fetch entire list in combobox
        combobox_options_lv1 = self.parser.get_single_element_options(select_lv1)
        for index in range(1, len(combobox_options_lv1)):  # skip first line

            select_lv1.select_by_index(index)
            self.driver.implicitly_wait(2)

            law_name = combobox_options_lv1[index].text.strip().replace(" ", "_")
            base_logger.info(f"\n➡️Processing Law:<<{law_name}>>")

            # --> Parse lv2 sections under each law
            self.process_sections(law_name)

    def process_sections(self, law_name):
        by, cid = self.component_manager.get_component_id_by_tag("level_2_left_tabs")
        left_elements = self.driver.find_elements(by, cid)

        # Apply strategy pattern

        section_handlers = {
            #"maddeler": self.process_law_matters,
            # "gerekçeler": self.process_law_justifications,
            # "cumhurbaşkanı_kararları":self.process_presidential_decree,
            # "b.k.k.":self.process_ministerial_decree,
            # "yönetmelikler": self.process_regulations,
            # "tebliğler": self.process_notices,
            "iç_genelgeler": self.process_internal_circulars,
            "genel_yazılar": self.process_official_letters,
            "sirküler": self.process_circulars,
            "özelgeler": self.process_private_rulings

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


    def process_law_justifications(self, law_name, section_name):
        """
        Download law justifications pdfs embed in Buraya in html body
        """

        # Smart weight to justifications to be filled properly
        wait = WebDriverWait(self.driver, 20)
        by, cid = self.component_manager.get_component_id_by_tag("level_3_gerekceler_href_comp")
        wait.until(EC.presence_of_element_located((by, cid)))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//ul/li[@onclick[contains(., 'div-icerik-gerekce')]]")) > 0)

        by, cid = self.component_manager.get_component_id_by_tag("level_3_gerekceler_body")
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
                by, cid = self.component_manager.get_component_id_by_tag("level_3_gerekceler_href")
                pdf_link_element = self.driver.find_element(by, cid)
                pdf_url = pdf_link_element.get_attribute("href")

                # Make path absolute, if it comes as relative
                if pdf_url.startswith("fileadmin"):
                    pdf_url = SOURCE_URL + pdf_url

                # Download and save pdf
                response = requests.get(pdf_url)

                # Save it under sections dir
                sections_path = os.path.join(self.sections_folder, section_name)
                os.makedirs(sections_path, exist_ok=True)
                filename = os.path.join(sections_path, f"{law_name}_{section_name}_{justification_law_name}.pdf")
                save_pdf(response.content, filename)

                # Save it under laws dir
                laws_path = os.path.join(self.laws_folder, law_name)
                os.makedirs(laws_path, exist_ok=True)
                filename = os.path.join(laws_path, f"{law_name}_{section_name}_{justification_law_name}.pdf")
                save_pdf(response.content, filename)


            except Exception as e:
                base_logger.info(f"❌ {jel.text.strip()} için PDF bulunamadı veya hata oluştu: {e}")

    def process_presidential_decree(self, law_name, section_name):
        """

        """
        # Click on the tab to open the href table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_ck_karari_tab")

        self.driver.find_element(by, cid).click()

        # Wait until component to be filled properly
        wait = WebDriverWait(self.driver, 25)
        wait.until(EC.presence_of_element_located((By.ID, "div-liste-ck")))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-icerik-ck')]]")) > 0)
        time.sleep(15)
        # Start to parsing the table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_ck_karari_body")
        header_row = self.driver.find_element(by, cid)

        by, cid = self.component_manager.get_component_id_by_tag("level_3_ck_karari_table_header")
        header_cols = header_row.find_elements(by, cid)
        headers = [col.text.strip() for col in header_cols]

        # 2. Find content rows, each of them are a tr component with onclick events
        by, cid = self.component_manager.get_component_id_by_tag("level_3_ck_karari_table_row")
        data_rows = self.driver.find_elements(by, cid)
        # Process table
        all_data = []
        for ix, row in enumerate(data_rows):
            by, cid = self.component_manager.get_component_id_by_tag("level_3_ck_karari_table_header")

            cols = row.find_elements(by, cid)

            # Process row and generate unique id
            if len(cols) >= len(headers):
                row_dict = dict()
                for ix, header in enumerate(headers):
                    row_dict.update({header: str(cols[ix].text).strip()})
                unique_id = generate_hash_from_dict(row_dict)
                row_dict.update({"id": unique_id})
                # Get Pop up  texts and pdf link if provided
                self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                self.driver.execute_script("arguments[0].click();", row)
                # wait for the content
                wait = WebDriverWait(self.driver, 10)
                by, cid = self.component_manager.get_component_id_by_tag("level_3_ck_karari_table_popup")
                wait.until(EC.presence_of_element_located((by, cid)))

                content_div = self.driver.find_element(by, cid)
                # Get the popup text
                full_text = content_div.text.strip()
                row_dict.update({"Detay Aciklama": full_text})

                try:
                    # Get the link if provided
                    by, cid = self.component_manager.get_component_id_by_tag("level_3_ck_karari_table_popup_pdf_text")
                    link_element = content_div.find_element(by, cid)

                except NoSuchElementException:
                    base_logger.warning("⚠️ No 'tıklayınız' link provided, wont download the pdf")
                    continue
                pdf_url = link_element.get_attribute("href")

                # Make url absolute if needed
                if pdf_url.startswith("/"):
                    pdf_url = SOURCE_URL + pdf_url

                # --> Save related pdfs
                # Generate file_name from order no
                ck_order_no = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                # Download pdf
                response = requests.get(pdf_url)
                time.sleep(5)
                # Save it under sections dir
                sections_path = os.path.join(self.sections_folder, section_name)
                os.makedirs(sections_path, exist_ok=True)
                filename = os.path.join(sections_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)
                row_dict.update({"related_pdf_path": filename})

                # Save it under laws dir
                laws_path = os.path.join(self.laws_folder, law_name)
                os.makedirs(laws_path, exist_ok=True)
                filename = os.path.join(laws_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)

                all_data.append(row_dict)

        df = pd.DataFrame(all_data, columns=headers)

        # Save table under sections
        sections_path = os.path.join(seßlf.sections_folder, section_name)
        os.makedirs(sections_path, exist_ok=True)
        filename = os.path.join(sections_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)

        # Save table under laws
        laws_path = os.path.join(self.laws_folder, law_name)
        os.makedirs(laws_path, exist_ok=True)
        filename = os.path.join(laws_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)

    def process_ministerial_decree(self, law_name, section_name):
        """

        """
        # Click on the tab to open the href table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_bkk_tab")

        self.driver.find_element(by, cid).click()

        # Wait until component to be filled properly
        wait = WebDriverWait(self.driver, 25)
        wait.until(EC.presence_of_element_located((By.ID, "div-liste-bkk")))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-icerik-bkk')]]")) > 0)
        time.sleep(15)
        # Start to parsing the table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_bkk_body")
        header_row = self.driver.find_element(by, cid)

        by, cid = self.component_manager.get_component_id_by_tag("level_3_bkk_table_header")
        header_cols = header_row.find_elements(by, cid)
        headers = [col.text.strip() for col in header_cols]

        # 2. Find content rows, each of them are a tr component with onclick events
        by, cid = self.component_manager.get_component_id_by_tag("level_3_bkk_table_row")
        data_rows = self.driver.find_elements(by, cid)
        # Process table
        all_data = []
        for ix, row in enumerate(data_rows):
            by, cid = self.component_manager.get_component_id_by_tag("level_3_bkk_table_header")

            cols = row.find_elements(by, cid)

            # Process row and generate unique id
            if len(cols) >= len(headers):
                row_dict = dict()
                for ix, header in enumerate(headers):
                    row_dict.update({header: str(cols[ix].text).strip()})
                unique_id = generate_hash_from_dict(row_dict)
                row_dict.update({"id": unique_id})
                # Get Pop up  texts and pdf link if provided
                self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                self.driver.execute_script("arguments[0].click();", row)
                # wait for the content
                wait = WebDriverWait(self.driver, 10)
                by, cid = self.component_manager.get_component_id_by_tag("level_3_bkk_table_popup")
                wait.until(EC.presence_of_element_located((by, cid)))

                content_div = self.driver.find_element(by, cid)
                # Get the popup text
                full_text = content_div.text.strip()
                row_dict.update({"Detay Aciklama": full_text})
                try:
                    # Get the link if provided
                    by, cid = self.component_manager.get_component_id_by_tag("level_3_bkk_table_popup_pdf_text")
                    link_element = content_div.find_element(by, cid)


                except NoSuchElementException:
                    base_logger.warning("⚠️ No 'tıklayınız' link provided, wont download the pdf")
                    continue
                pdf_url = link_element.get_attribute("href")

                # Make url absolute if needed
                if pdf_url.startswith("/"):
                    pdf_url = SOURCE_URL + pdf_url

                # --> Save related pdfs
                # Generate file_name from order no
                ck_order_no = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                # Download pdf
                response = requests.get(pdf_url)
                time.sleep(5)
                # Save it under sections dir
                sections_path = os.path.join(self.sections_folder, section_name)
                os.makedirs(sections_path, exist_ok=True)
                filename = os.path.join(sections_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)
                row_dict.update({"related_pdf_path": filename})

                # Save it under laws dir
                laws_path = os.path.join(self.laws_folder, law_name)
                os.makedirs(laws_path, exist_ok=True)
                filename = os.path.join(laws_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)

                all_data.append(row_dict)

        df = pd.DataFrame(all_data, columns=headers)

        # Save table under sections
        sections_path = os.path.join(self.sections_folder, section_name)
        os.makedirs(sections_path, exist_ok=True)
        filename = os.path.join(sections_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)

        # Save table under laws
        laws_path = os.path.join(self.laws_folder, law_name)
        os.makedirs(laws_path, exist_ok=True)
        filename = os.path.join(laws_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)

    def process_regulations(self, law_name, section_name):
        """

        """
        # Click on the tab to open the href table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_yonetmelik_tab")

        self.driver.find_element(by, cid).click()

        # Wait until component to be filled properly
        wait = WebDriverWait(self.driver, 25)
        wait.until(EC.presence_of_element_located((By.ID, "div-icerik-yon")))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-icerik-yon')]]")) > 0)
        time.sleep(15)
        # Start to parsing the table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_yonetmelik_body")
        header_row = self.driver.find_element(by, cid)

        by, cid = self.component_manager.get_component_id_by_tag("level_3_yonetmelik_table_header")
        header_cols = header_row.find_elements(by, cid)
        headers = [col.text.strip() for col in header_cols]

        # 2. Find content rows, each of them are a tr component with onclick events
        by, cid = self.component_manager.get_component_id_by_tag("level_3_yonetmelik_table_row")
        data_rows = self.driver.find_elements(by, cid)
        # Process table
        all_data = []
        for ix, row in enumerate(data_rows):
            by, cid = self.component_manager.get_component_id_by_tag("level_3_yonetmelik_table_header")

            cols = row.find_elements(by, cid)

            # Process row and generate unique id
            if len(cols) >= len(headers):
                row_dict = dict()
                for ix, header in enumerate(headers):
                    row_dict.update({header: str(cols[ix].text).strip()})
                unique_id = generate_hash_from_dict(row_dict)
                row_dict.update({"id": unique_id})
                # Get Pop up  texts and pdf link if provided
                self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                self.driver.execute_script("arguments[0].click();", row)
                # wait for the content
                wait = WebDriverWait(self.driver, 10)
                by, cid = self.component_manager.get_component_id_by_tag("level_3_yonetmelik_table_popup")
                wait.until(EC.presence_of_element_located((by, cid)))

                content_div = self.driver.find_element(by, cid)
                # Get the popup text
                full_text = content_div.text.strip()
                row_dict.update({"Detay Aciklama": full_text})
                try:
                    # Get the link if provided
                    by, cid = self.component_manager.get_component_id_by_tag("level_3_yonetmelik_table_popup_pdf_text")
                    link_element = content_div.find_element(by, cid)


                except NoSuchElementException:
                    base_logger.warning("⚠️ No 'tıklayınız' link provided, wont download the pdf")
                    continue
                pdf_url = link_element.get_attribute("href")

                # Make url absolute if needed
                if pdf_url.startswith("/"):
                    pdf_url = SOURCE_URL + pdf_url

                # --> Save related pdfs
                # Generate file_name from order no
                ck_order_no = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                # Download pdf
                response = requests.get(pdf_url)
                time.sleep(5)
                # Save it under sections dir
                sections_path = os.path.join(self.sections_folder, section_name)
                os.makedirs(sections_path, exist_ok=True)
                filename = os.path.join(sections_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)
                row_dict.update({"related_pdf_path": filename})

                # Save it under laws dir
                laws_path = os.path.join(self.laws_folder, law_name)
                os.makedirs(laws_path, exist_ok=True)
                filename = os.path.join(laws_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)

                all_data.append(row_dict)

        df = pd.DataFrame(all_data, columns=headers)

        # Save table under sections
        sections_path = os.path.join(self.sections_folder, section_name)
        os.makedirs(sections_path, exist_ok=True)
        filename = os.path.join(sections_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)

        # Save table under laws
        laws_path = os.path.join(self.laws_folder, law_name)
        os.makedirs(laws_path, exist_ok=True)
        filename = os.path.join(laws_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)


    def process_notices(self, law_name, section_name):
        pass

    def process_internal_circulars(self, law_name, section_name):
        """

        """
        # Click on the tab to open the href table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_ic_genelgeler_tab")

        self.driver.find_element(by, cid).click()

        # Wait until component to be filled properly
        wait = WebDriverWait(self.driver, 25)
        wait.until(EC.presence_of_element_located((By.ID, "div-liste-ig")))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-icerik-ig')]]")) > 0)
        time.sleep(15)
        # Start to parsing the table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_ic_genelgeler_body")
        header_row = self.driver.find_element(by, cid)

        by, cid = self.component_manager.get_component_id_by_tag("level_3_ic_genelgeler_table_header")
        header_cols = header_row.find_elements(by, cid)
        headers = [col.text.strip() for col in header_cols]

        # 2. Find content rows, each of them are a tr component with onclick events
        by, cid = self.component_manager.get_component_id_by_tag("level_3_ic_genelgeler_table_row")
        data_rows = self.driver.find_elements(by, cid)
        # Process table
        all_data = []
        for ix, row in enumerate(data_rows):
            by, cid = self.component_manager.get_component_id_by_tag("level_3_ic_genelgeler_table_header")

            cols = row.find_elements(by, cid)

            # Process row and generate unique id
            if len(cols) >= len(headers):
                row_dict = dict()
                for ix, header in enumerate(headers):
                    row_dict.update({header: str(cols[ix].text).strip()})
                unique_id = generate_hash_from_dict(row_dict)
                row_dict.update({"id": unique_id})
                # Get Pop up  texts and pdf link if provided
                self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                self.driver.execute_script("arguments[0].click();", row)
                # wait for the content
                wait = WebDriverWait(self.driver, 10)
                by, cid = self.component_manager.get_component_id_by_tag("level_3_ic_genelgeler_table_popup")
                wait.until(EC.presence_of_element_located((by, cid)))

                content_div = self.driver.find_element(by, cid)
                # Get the popup text
                full_text = content_div.text.strip()
                row_dict.update({"Detay Aciklama": full_text})
                try:
                    # Get the link if provided
                    by, cid = self.component_manager.get_component_id_by_tag("level_3_ic_genelgeler_table_popup_pdf_text")
                    link_element = content_div.find_element(by, cid)


                except NoSuchElementException:
                    base_logger.warning("⚠️ No 'tıklayınız' link provided, wont download the pdf")
                    continue
                pdf_url = link_element.get_attribute("href")

                # Make url absolute if needed
                if pdf_url.startswith("/"):
                    pdf_url = SOURCE_URL + pdf_url

                # --> Save related pdfs
                # Generate file_name from order no
                ck_order_no = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                # Download pdf
                response = requests.get(pdf_url)
                time.sleep(5)
                # Save it under sections dir
                sections_path = os.path.join(self.sections_folder, section_name)
                os.makedirs(sections_path, exist_ok=True)
                filename = os.path.join(sections_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)
                row_dict.update({"related_pdf_path": filename})

                # Save it under laws dir
                laws_path = os.path.join(self.laws_folder, law_name)
                os.makedirs(laws_path, exist_ok=True)
                filename = os.path.join(laws_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)

                all_data.append(row_dict)



    def process_official_letters(self, law_name, section_name):
        """

        """
        # Click on the tab to open the href table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_genel_yazilar_tab")

        self.driver.find_element(by, cid).click()

        # Wait until component to be filled properly
        wait = WebDriverWait(self.driver, 25)
        wait.until(EC.presence_of_element_located((By.ID, "div-liste-gy")))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-liste-gy')]]")) > 0)
        time.sleep(15)
        # Start to parsing the table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_genel_yazilar_body")
        header_row = self.driver.find_element(by, cid)

        by, cid = self.component_manager.get_component_id_by_tag("level_3_genel_yazilar_table_header")
        header_cols = header_row.find_elements(by, cid)
        headers = [col.text.strip() for col in header_cols]

        # 2. Find content rows, each of them are a tr component with onclick events
        by, cid = self.component_manager.get_component_id_by_tag("level_3_genel_yazilar_table_row")
        data_rows = self.driver.find_elements(by, cid)
        # Process table
        all_data = []
        for ix, row in enumerate(data_rows):
            by, cid = self.component_manager.get_component_id_by_tag("level_3_genel_yazilar_table_header")

            cols = row.find_elements(by, cid)

            # Process row and generate unique id
            if len(cols) >= len(headers):
                row_dict = dict()
                for ix, header in enumerate(headers):
                    row_dict.update({header: str(cols[ix].text).strip()})
                unique_id = generate_hash_from_dict(row_dict)
                row_dict.update({"id": unique_id})
                # Get Pop up  texts and pdf link if provided
                self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                self.driver.execute_script("arguments[0].click();", row)
                # wait for the content
                wait = WebDriverWait(self.driver, 10)
                by, cid = self.component_manager.get_component_id_by_tag("level_3_genel_yazilar_table_popup")
                wait.until(EC.presence_of_element_located((by, cid)))

                content_div = self.driver.find_element(by, cid)
                # Get the popup text
                full_text = content_div.text.strip()
                row_dict.update({"Detay Aciklama": full_text})
                try:
                    # Get the link if provided
                    by, cid = self.component_manager.get_component_id_by_tag("level_3_genel_yazilar_table_popup_pdf_text")
                    link_element = content_div.find_element(by, cid)


                except NoSuchElementException:
                    base_logger.warning("⚠️ No 'tıklayınız' link provided, wont download the pdf")
                    continue
                pdf_url = link_element.get_attribute("href")

                # Make url absolute if needed
                if pdf_url.startswith("/"):
                    pdf_url = SOURCE_URL + pdf_url

                # --> Save related pdfs
                # Generate file_name from order no
                ck_order_no = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                # Download pdf
                response = requests.get(pdf_url)
                time.sleep(5)
                # Save it under sections dir
                sections_path = os.path.join(self.sections_folder, section_name)
                os.makedirs(sections_path, exist_ok=True)
                filename = os.path.join(sections_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)
                row_dict.update({"related_pdf_path": filename})

                # Save it under laws dir
                laws_path = os.path.join(self.laws_folder, law_name)
                os.makedirs(laws_path, exist_ok=True)
                filename = os.path.join(laws_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)

                all_data.append(row_dict)

        df = pd.DataFrame(all_data, columns=headers)

        # Save table under sections
        sections_path = os.path.join(self.sections_folder, section_name)
        os.makedirs(sections_path, exist_ok=True)
        filename = os.path.join(sections_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)

        # Save table under laws
        laws_path = os.path.join(self.laws_folder, law_name)
        os.makedirs(laws_path, exist_ok=True)
        filename = os.path.join(laws_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)


    def process_circulars(self, law_name, section_name):
        """

        """
        # Click on the tab to open the href table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_sirkuler_tab")

        self.driver.find_element(by, cid).click()

        # Wait until component to be filled properly
        wait = WebDriverWait(self.driver, 25)
        wait.until(EC.presence_of_element_located((By.ID, "div-liste-sir")))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-liste-sir')]]")) > 0)
        time.sleep(15)
        # Start to parsing the table
        by, cid = self.component_manager.get_component_id_by_tag("level_3_sirkuler_body")
        header_row = self.driver.find_element(by, cid)

        by, cid = self.component_manager.get_component_id_by_tag("level_3_sirkuler_table_header")
        header_cols = header_row.find_elements(by, cid)
        headers = [col.text.strip() for col in header_cols]

        # 2. Find content rows, each of them are a tr component with onclick events
        by, cid = self.component_manager.get_component_id_by_tag("level_3_sirkuler_table_row")
        data_rows = self.driver.find_elements(by, cid)
        # Process table
        all_data = []
        for ix, row in enumerate(data_rows):
            by, cid = self.component_manager.get_component_id_by_tag("level_3_sirkuler_table_header")

            cols = row.find_elements(by, cid)

            # Process row and generate unique id
            if len(cols) >= len(headers):
                row_dict = dict()
                for ix, header in enumerate(headers):
                    row_dict.update({header: str(cols[ix].text).strip()})
                unique_id = generate_hash_from_dict(row_dict)
                row_dict.update({"id": unique_id})
                # Get Pop up  texts and pdf link if provided
                self.driver.execute_script("arguments[0].scrollIntoView(true);", row)
                self.driver.execute_script("arguments[0].click();", row)
                # wait for the content
                wait = WebDriverWait(self.driver, 10)
                by, cid = self.component_manager.get_component_id_by_tag("level_3_sirkuler_table_popup")
                wait.until(EC.presence_of_element_located((by, cid)))

                content_div = self.driver.find_element(by, cid)
                # Get the popup text
                full_text = content_div.text.strip()
                row_dict.update({"Detay Aciklama": full_text})
                try:
                    # Get the link if provided
                    by, cid = self.component_manager.get_component_id_by_tag("level_3_sirkuler_table_popup_pdf_text")
                    link_element = content_div.find_element(by, cid)


                except NoSuchElementException:
                    base_logger.warning("⚠️ No 'tıklayınız' link provided, wont download the pdf")
                    continue
                pdf_url = link_element.get_attribute("href")

                # Make url absolute if needed
                if pdf_url.startswith("/"):
                    pdf_url = SOURCE_URL + pdf_url

                # --> Save related pdfs
                # Generate file_name from order no
                ck_order_no = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                # Download pdf
                response = requests.get(pdf_url)
                time.sleep(5)
                # Save it under sections dir
                sections_path = os.path.join(self.sections_folder, section_name)
                os.makedirs(sections_path, exist_ok=True)
                filename = os.path.join(sections_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)
                row_dict.update({"related_pdf_path": filename})

                # Save it under laws dir
                laws_path = os.path.join(self.laws_folder, law_name)
                os.makedirs(laws_path, exist_ok=True)
                filename = os.path.join(laws_path, f"{law_name}_{section_name}_{ck_order_no}_{unique_id}.pdf")
                save_pdf(response.content, filename)

                all_data.append(row_dict)

        df = pd.DataFrame(all_data, columns=headers)

        # Save table under sections
        sections_path = os.path.join(self.sections_folder, section_name)
        os.makedirs(sections_path, exist_ok=True)
        filename = os.path.join(sections_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)

        # Save table under laws
        laws_path = os.path.join(self.laws_folder, law_name)
        os.makedirs(laws_path, exist_ok=True)
        filename = os.path.join(laws_path, f"{law_name}_{section_name}_ck_karari.csv")
        save_csv(df, filename)


    def process_private_rulings(self, law_name, section_name):
        pass


    def close(self):
        self.driver.quit()
