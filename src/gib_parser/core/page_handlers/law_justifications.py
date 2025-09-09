from typing import AnyStr
from abc import ABC

import time
import os

from gib_parser.helpers.abstract_classes import AbstractPageHandler, AbstractComponentManager
from gib_parser.globals import SOURCE_URL
from gib_parser import get_logger
from gib_parser.helpers.io import save_pdf
from gib_parser.core.selenium_client import SeleniumClient



base_logger = get_logger(__name__)

import requests


class LawJustificationHandler(AbstractPageHandler, ABC):
    def __init__(self):
        super().__init__()


    def handle(self,
               parser:SeleniumClient,
               component_manager:AbstractComponentManager,
               law_name: AnyStr,
               section_name: AnyStr,
               sections_folder: AnyStr,
               laws_folder: AnyStr):


        try:
            # Fetch justification title
            fe_crawl = parser.get_law_justification_link_from_arrow()

            pdf_url = fe_crawl["pdf_url"]
            headers = fe_crawl["headers"]
            cookies = fe_crawl["cookies"]

            # Download and save pdf
            response = requests.get(pdf_url, headers=headers, cookies=cookies, stream=True, timeout=90)
            content = response.content

            # Save it under sections dir
            sections_path = os.path.join(sections_folder, section_name)
            os.makedirs(sections_path, exist_ok=True)
            filename = os.path.join(sections_path, f"{law_name}_{section_name}.pdf")
            save_pdf(content, filename)

            # Save it under laws dir
            laws_path = os.path.join(laws_folder, law_name)
            os.makedirs(laws_path, exist_ok=True)
            filename = os.path.join(laws_path, f"{law_name}_{section_name}.pdf")
            save_pdf(content, filename)


        except Exception as e:
            base_logger.info(str(e))