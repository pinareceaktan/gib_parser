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

from gib_parser import save_text, save_pdf, save_csv, generate_hash_from_dict
from gib_parser.core.page_handlers.page_handler_factory import PageHandlerFactory
from gib_parser.core.selenium_client import SeleniumClient
from gib_parser.helpers.abstract_classes import AbstractParsingClient, AbstractComponentManager
from gib_parser.utils.generic import prep_name, get_law_details

from gib_parser import get_logger

base_logger = get_logger(__name__)

from gib_parser.globals import SOURCE_URL

# Gib pages parsing logic

TIMEOUT = 10


class GibPageOrchestrator:
    def __init__(self,
                 parser : SeleniumClient,
                 component_manager: AbstractComponentManager,
                 sections_folder :str,
                 laws_folder: str):

        self.parser = parser
        self.sections_folder = sections_folder
        self.laws_folder = laws_folder
        self.component_manager = component_manager
        self.handler_factory = PageHandlerFactory(selenium_client=self.parser,
                                                  component_manager=self.component_manager)

    def _get_gib_tab_buttons(self):

        """
        Get maddeler, gerekceler blah blah..
        """

        wait = WebDriverWait(self.parser.driver, TIMEOUT)

        main_tab = self.parser.driver.current_window_handle
        self.parser.driver.switch_to.window(main_tab)

        by, container_x_path = self.component_manager.get_component_id_by_tag("level_2_left_container")
        by, buttons_x_path = self.component_manager.get_component_id_by_tag("level_2_left_buttons_on_container")

        container = wait.until(EC.presence_of_element_located((by, container_x_path)))
        items = container.find_elements(by, buttons_x_path)

        if not items:
            # alternatively, look for
            items = container.find_elements(By.XPATH, ".//h6")
        items =  [i for i in items if i.is_displayed()]
        return items


    def parse(self):
        """
        Chooses 'kanun tipi' from the main pages' combobox
        :return:
        """


        page = 1
        while True:
            # Wait for to be loaded
            check_comp = self.component_manager.get_component_id_by_tag("level_1_check")
            inner_comp = self.component_manager.get_component_id_by_tag("level_1_component")

            self.parser.make_driver_wait_for_a_text(check_comp,
                                                    inner_comp,
                                                    min_cards=4,
                                                    timeout=20)
            inner_comp_by, inner_comp_cid = inner_comp
            laws_drop_down = self.parser.find_elements(inner_comp_by, inner_comp_cid)


            print(f"--- Sayfa {page} ---")


            for web_element in laws_drop_down:
                meta_data = get_law_details(web_element.text)
                law_name = prep_name(meta_data["kanun_adi"])
                base_logger.info(f"\n➡️ Processing Law: <<{law_name}>> ")

                # Open the law in new tab and click
                self.parser.click_in_new_tab(web_element_to_click=web_element)

                time.sleep(5)

                # --> Parse lv2 sections under each law : Sections
                # Go for maddeler, gerekceler, ckk, bkk
                # Apply strategy pattern

                left_menu = self._get_gib_tab_buttons()


                for button in left_menu:
                    button_name = button.text
                    section_name = prep_name(button_name)
                    base_logger.info(f"\n➡️ Clicking section:<< {section_name} >>")

                    page_handler = self.handler_factory.get_handler(section_name.lower())

                    if page_handler:

                        button.click()
                        page_handler.handle(parser=self.parser,
                                            component_manager=self.component_manager,
                                            law_name=law_name,
                                            section_name=section_name,
                                            sections_folder=self.sections_folder,
                                            laws_folder=self.laws_folder)

                    print("d")



            page += 1

            moved = self.parser.go_to_page(page)
            if not moved:
                print("Son sayfaya geldik, bitiriyoruz.")
                break


