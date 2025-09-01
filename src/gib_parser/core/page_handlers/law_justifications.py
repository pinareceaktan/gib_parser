from abc import ABC

import time
import os

from gib_parser.helpers.abstract_classes import AbstractPageHandler, AbstractParsingClient, AbstractComponentManager
from gib_parser.globals import SOURCE_URL
from gib_parser import get_logger
from gib_parser.helpers.io import save_pdf
base_logger = get_logger(__name__)

import requests


class LawJustificationHandler(AbstractPageHandler, ABC):
    def __init__(self):
        super().__init__()


    def handle(self,
               parser:AbstractParsingClient,
               component_manager:AbstractComponentManager,
               law_name: str,
               section_name: str,
               sections_folder: str,
               laws_folder: str):


        by, cid = component_manager.get_component_id_by_tag("level_3_gerekceler_href_comp")
        link_el = parser.find_element(by, cid)
        by, cid = component_manager.get_component_id_by_tag("level_3_gerekceler_href_spider")
        li_el = parser.find_element_in_element(link_el, by, cid)
        parser.click_on_click_inner_elements(li_el)


        by, cid = component_manager.get_component_id_by_tag("level_3_gerekceler_body")
        justification_elements = parser.find_elements(by, cid)

        for jel in justification_elements:

            try:
                # Fetch justification title
                justification_law_name = jel.text.strip().replace(" ", "_")

                # Click and wait for content to get loaded
                parser.click_component(jel)

                # Find Buraya word to fetch embedded href
                by, cid = component_manager.get_component_id_by_tag("level_3_gerekceler_href")
                pdf_link_element = parser.find_element(by, cid)
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