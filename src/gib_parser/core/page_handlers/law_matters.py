from typing import AnyStr
from abc import ABC
import time
import os

from gib_parser.helpers.abstract_classes import AbstractPageHandler
from gib_parser.helpers.io import save_text
from gib_parser.core.selenium_client import SeleniumClient
from gib_parser.core.page_schemas import ComponentManager
from gib_parser import get_logger


base_logger = get_logger(__name__)



class LawMattersHandler(AbstractPageHandler, ABC):
    def __init__(self):
        super().__init__()

    def handle(self,
               parser: SeleniumClient,
               component_manager: ComponentManager,
               law_name: AnyStr,
               section_name: AnyStr,
               sections_folder: AnyStr,
               laws_folder: AnyStr):
        """
        Download law matter htmls as txt
        """

        by, cid = component_manager.get_component_id_by_tag("level_3_maddeler_combobox_aria")
        parser.click_component(by, cid)

        # by, cid = component_manager.get_component_id_by_tag("level_3_maddeler_tbox")
        # text_box_element = parser.find_element(by, cid)
        try:
            fe_crawl = parser.collect_all_box_components(include_filter_box=False, scope="active_panel")
            content = fe_crawl["content"]

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
            base_logger.error(str(e))
