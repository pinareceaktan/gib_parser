from abc import ABC

import time
import os

from gib_parser.helpers.abstract_classes import AbstractPageHandler, AbstractParsingClient, AbstractComponentManager
from gib_parser.globals import SOURCE_URL
from gib_parser import get_logger
from gib_parser.helpers.io import save_pdf
base_logger = get_logger(__name__)

import requests
class PresidentialDecreeHandler(AbstractPageHandler, ABC):
    def __init__(self):
        super().__init__()

    def handle(self,
               parser:AbstractParsingClient,
               component_manager:AbstractComponentManager,
               law_name: str,
               section_name: str,
               sections_folder: str,
               laws_folder: str):


        # Click on the tab to open the href table
        by, cid = component_manager.get_component_id_by_tag("level_3_ck_karari_tab")

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

