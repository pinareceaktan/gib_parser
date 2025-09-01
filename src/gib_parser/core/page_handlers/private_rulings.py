from abc import ABC

import time
import os

from gib_parser.helpers.abstract_classes import AbstractPageHandler, AbstractParsingClient, AbstractComponentManager
from gib_parser.globals import SOURCE_URL
from gib_parser import get_logger
from gib_parser.helpers.io import save_pdf
base_logger = get_logger(__name__)

import requests


class PrivateRulingsHandler(AbstractPageHandler, ABC):
    def __init__(self):
        super().__init__()

    def handle(self,
               parser:AbstractParsingClient,
               component_manager:AbstractComponentManager,
               law_name: str,
               section_name: str,
               sections_folder: str,
               laws_folder: str):

        pass