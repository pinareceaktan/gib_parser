from abc import ABC

import time
import os

from gib_parser.helpers.abstract_classes import AbstractPageHandler
from gib_parser.utils.generic import prep_name
from gib_parser.helpers.io import save_text
from gib_parser import get_logger

base_logger = get_logger(__name__)


class LawMattersHandler(AbstractPageHandler, ABC):
    def __init__(self):
        super().__init__()

    def handle(self,
               parser,
               component_manager,
               law_name,
               section_name,
               sections_folder,
               laws_folder):
        """
        Download law matter htmls as txt
        """

        by, cid = component_manager.get_component_id_by_tag("level_3_maddeler_combobox")
        select_lv2 = parser.find_and_select_single_element(by, cid)
        # Fetch entire list in combobox
        combobox_options_lv2 = parser.get_single_element_options(select_lv2)

        for ix, web_element in enumerate(combobox_options_lv2):
            # skip first line
            if ix == 0:
                continue

            list_component_name = prep_name(web_element.text)

            if list_component_name.lower() == "hepsi":
                # Click item in the combobox
                try:
                    select_lv2.select_by_index(ix)
                    time.sleep(5)

                    by, cid = component_manager.get_component_id_by_tag("level_3_maddeler_body")
                    element = parser.find_element(by, cid)
                    content = element.text

                    # Save it under sections dir
                    sections_path = os.path.join(sections_folder, section_name)
                    os.makedirs(sections_path, exist_ok=True)
                    filename = os.path.join(sections_path, f"{law_name}_{section_name}.txt")
                    save_text(content, filename)

                    # Save it under laws dir
                    laws_path = os.path.join(laws_folder, law_name)
                    os.makedirs(laws_path, exist_ok=True)
                    filename = os.path.join(laws_path, f"{law_name}_{section_name}.txt")
                    save_text(content, filename)


                except Exception as e:
                    base_logger.info(f"❌ {list_component_name.strip()} sayfa yüklenemedi: {e}")
