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

from gib_parser.driver_manager import DriverManager
from gib_parser.utils import logger

base_logger = logger.get_logger(__name__)

SOURCE_URL =  "https://www.gib.gov.tr/"

# Keep them globally so you can change the by and id easily if it gets changed
web_components = {"level_1_combobox": {"by": "id", "component_id": "m_kanun"},
                  "level_2_left_tabs": {"by": By.CSS_SELECTOR, "component_id": "div.solSutun ul li"},
                  "level_3_maddeler_tab": {"by": By.ID, "component_id": "km-select"},
                  "level_3_maddeler_body": {"by": By.ID, "component_id": "div-icerik-maddeler"},
                  "level_3_gerekceler_tab": {"by": By.ID, "component_id": "mevzuat_ger"},
                  "level_3_gerekceker_wait_comp": {"by": None, "component_id": None},
                  "level_3_gerekceler_body": {"by": By.XPATH, "component_id": "//ul/li[@onclick[contains(., 'div-icerik-gerekce')]]"},
                  "level_3_gerekceler_href": {"by": By.XPATH, "component_id": "//a[contains(text(), 'Buraya')]"},
                  "y": {"by": "", "component_id": ""},
                  "y": {"by": "", "component_id": ""},
                  "y": {"by": "", "component_id": ""},
                  "y": {"by": "", "component_id": ""},

                  }




class GibParser:
    def __init__(self, source_web_path, sections_folder, laws_folder):
        self.source_web_path = source_web_path
        self.sections_folder = sections_folder
        self.laws_folder = laws_folder
        self.driver = self.setup_driver()
        self.wait = WebDriverWait(self.driver, 20)

    def setup_driver(self):
        driver_manager = DriverManager()
        driver = driver_manager.get_driver()
        driver_manager.pass_page_to_driver(self.source_web_path)
        return driver

    def parse(self):
        """
        Chooses 'kanun tipi' from the main pages' combobox
        :return:
        """
        # --> Parse lv 1 combobox
        component_tag = "level_1_combobox"
        select_lv1 = Select(self.driver.find_element(web_components[component_tag]["by"],
                                                     web_components[component_tag]["component_id"]))

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
        component_tag = "level_2_left_tabs"
        left_elements = self.driver.find_elements(web_components[component_tag]["by"],
                                                  web_components[component_tag]["component_id"])
        for left_el in left_elements:
            section_name = left_el.text.strip().replace(" ", "_")
            base_logger.info(f"\n➡️Clicking section:<<{section_name}>>")
            left_el.click()

            if section_name.lower() == "maddeler":
                time.sleep(10)
                self.process_law_matters(law_name, section_name)
            elif section_name.lower() == "gerekçeler":
                self.process_law_justifications(law_name, section_name)
            elif section_name.lower() == "cumhurbaşkanı_kararları":
                self.process_presidential_decree(law_name, section_name)
            elif section_name.lower() == "yönetmelikler":
                print("ece")
                pass
            elif section_name.lower() == "tebliğler":
                print("ece")
                pass
            elif section_name.lower() == "iç_genelgeler":
                print("ece")
                pass
            elif section_name.lower() == "genel_yazılar":
                print("ece")
                pass
            elif section_name.lower() == "sirküler":
                print("ece")
                pass
            elif section_name.lower() == "özelgeler":
                print("ece")
                pass

            else:
                base_logger.info(f"Skipping section {section_name}")

    def process_law_matters(self, law_name, section_name):
        """
        Convert plain html to text and save
        :param law_name:
        :param section_name:
        :return:
        """

        component_tag = "level_3_maddeler_tab"
        combobox_lv3 = Select(self.driver.find_element(web_components[component_tag]["by"],
                                                       web_components[component_tag]["component_id"]))

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
                component_tag = "level_3_maddeler_body"

                content = self.driver.find_element(web_components[component_tag]["by"],
                                                   web_components[component_tag]["component_id"])
                time.sleep(15)
                text = content.text.strip()
                if len(text) > 10:  # make sure body is not empty
                    # Save it under sections dir
                    sections_path = os.path.join(self.sections_folder, section_name)
                    os.makedirs(sections_path, exist_ok=True)
                    filename = os.path.join(sections_path, f"{law_name}_{section_name}_{madde_name}.txt")
                    self.save_text(text, filename)

                    # Save it under laws dir
                    laws_path = os.path.join(self.laws_folder, law_name)
                    os.makedirs(laws_path, exist_ok=True)
                    filename = os.path.join(laws_path, f"{law_name}_{section_name}_{madde_name}.txt")
                    self.save_text(text, filename)

                else:
                    base_logger.warning("⚠️ Empty, didnt write")
            except Exception as e:
                base_logger.warning(f"❌️ No content {e}")

    def process_law_justifications(self, law_name, section_name):
        """
        Download law justifications pdfs embed in Buraya in html body
        """
        component_tag = "level_3_gerekceler_tab"

        self.driver.find_element(web_components[component_tag]["by"],
                                 web_components[component_tag]["component_id"]).click()

        # Smart weight to justifications to be filled properly
        wait = WebDriverWait(self.driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "div-liste-gerekce")))
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//ul/li[@onclick[contains(., 'div-icerik-gerekce')]]")) > 0)

        component_tag = "level_3_gerekceler_body"
        justification_elements = driver.find_elements(web_components[component_tag]["by"],
                                                      web_components[component_tag]["component_id"])


        for jel in justification_elements:

            try:
                # Fetch justification title
                justification_law_name = jel.text.strip().replace(" ", "_")

                # Click and wait for content to get loaded
                jel.click()
                time.sleep(2)

                # Find Buraya word to fetch embedded href
                component_tag = "level_3_gerekceler_href"
                pdf_link_element = driver.find_element(web_components[component_tag]["by"],
                                                       web_components[component_tag]["component_id"])
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
                self.save_pdf(response.content, filename)

                # Save it under laws dir
                laws_path = os.path.join(laws_folder, law_name)
                os.makedirs(laws_path, exist_ok=True)
                filename = os.path.join(laws_path, f"{law_name}_{section_name}_{justification_law_name}.pdf")
                self.save_pdf(response.content, filename)


            except Exception as e:
                logger.info(f"❌ {jel.text.strip()} için PDF bulunamadı veya hata oluştu: {e}")

    def process_presidential_decree(self, law_name, section_name):
        """

        """
        driver.find_element(By.ID, "mevzuat_ck").click()
        wait = WebDriverWait(driver, 20)
        # Şimdi adet elementinin görünür ve tıklanabilir olmasını bekle
        wait.until(EC.presence_of_element_located((By.ID, "div-liste-ck")))

        # Şimdi gerçekten içi dolmuş mu kontrol et
        wait.until(
            lambda d: len(d.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-icerik-ck')]]")) > 0)

        # 1. Başlık satırını bul
        header_row = driver.find_element(By.XPATH, "//tr[@class='mevzuat-liste-baslik-satir']")
        header_cols = header_row.find_elements(By.TAG_NAME, "td")
        headers = [col.text.strip() for col in header_cols]

        # 2. İçerik satırlarını bul (hepsi onclick içeren tr'ler)
        data_rows = driver.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-icerik-ck')]]")
        # Process table
        all_data = []
        for ix, row in enumerate(data_rows):
            cols = row.find_elements(By.TAG_NAME, "td")
            # Process row and generate unique id
            if len(cols) >= len(headers):
                row_dict = dict()
                for ix, header in enumerate(headers):
                    row_dict.update({header: str(cols[ix].text).strip()})
                unique_id = generate_hash_from_dict(row_dict)
                row_dict.update({"id": unique_id})
                # Get extra texts and pdf link

                try:
                    driver.execute_script("arguments[0].scrollIntoView(true);", row)
                    driver.execute_script("arguments[0].click();", row)
                    time.sleep(2)
                    # wait for the content
                    wait = WebDriverWait(driver, 10)
                    wait.until(EC.presence_of_element_located((By.ID, "div-icerik-ck")))
                    content_div = driver.find_element(By.ID, "div-icerik-ck")
                    # Get the extra text
                    full_text = content_div.text.strip()
                    row_dict.update({"Detay Aciklama": full_text})
                    # Get the link
                    link_element = content_div.find_element(By.XPATH, ".//a[contains(text(), 'tıklayınız')]")
                    pdf_url = link_element.get_attribute("href")

                    # Make url absolute if needed
                    if pdf_url.startswith("/"):
                        pdf_url = "https://www.gib.gov.tr" + pdf_url

                    # --> Save related pdfs
                    # Generate file_name from karar
                    karar_no = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                    # Download pdf
                    response = requests.get(pdf_url)

                    # Under Sections
                    sections_path = os.path.join(sections_folder, section_title)
                    os.makedirs(sections_path, exist_ok=True)
                    filename = os.path.join(sections_path,
                                            f"{kanun_adi}_{section_title}_{karar_no}_{unique_id}.pdf")
                    row_dict.update({"related_pdf_path": filename})

                    with open(filename, "wb") as f:
                        f.write(response.content)

                    logger.info(f"✅ saved: {filename}")

                    # Under Laws
                    laws_path = os.path.join(laws_folder, kanun_adi)
                    os.makedirs(laws_path, exist_ok=True)
                    filename = os.path.join(laws_path, f"{kanun_adi}_{section_title}_{karar_no}_{unique_id}.pdf")
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    logger.info(f"✅ saved: {filename}")

                except Exception as e:
                    logger.debug(f"Failed downloading related pdf, error processing line {ix}: {str(e)}")

                all_data.append(row_dict)

        df = pd.DataFrame(all_data, columns=headers)

        # Save table under sections
        sections_path = os.path.join(sections_folder, section_title)
        os.makedirs(sections_path, exist_ok=True)
        filename = os.path.join(sections_path, f"{kanun_adi}_{section_title}.csv")
        df.to_csv(filename, index=True, encoding="utf-8-sig")

        logger.info(f"✅ saved: {filename}")

        # Save table under laws
        laws_path = os.path.join(laws_folder, kanun_adi)
        os.makedirs(laws_path, exist_ok=True)
        filename = os.path.join(laws_path, f"{kanun_adi}_{section_title}.csv")
        df.to_csv(filename, index=True, encoding="utf-8-sig")

        logger.info(f"✅ saved: {filename}")

    @static_method
    def save_text(self, text, path) -> None:
        if not path.endswith("txt"):
            base_logger.error("File name should end with a txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        base_logger.info(f"✅ Saved: {path}")

    @static_method
    def save_pdf(self, content, path):
        if not path.endswith("pdf"):
            base_logger.error("File name should end with a pdf")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(content)



    def close(self):
        self.driver.quit()
