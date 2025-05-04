import sys
import time
import requests
import os
import logging
from pathlib import Path


sys.path.append(str(Path(__file__).resolve().parents[1])+ "/src")


os.environ["DEFAULT_LOG_LEVEL"] = "info"
os.environ["FLUSH_TO_CONSOLE"] = "True"
os.environ["SOURCE_WEB_PATH"] = "https://www.gib.gov.tr/gibmevzuat"

from gib_parser import get_logger
from gib_parser import GibParser

logger = get_logger("gib_parser")


# Definitions
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "..", "output")

os.environ["OUTPUT_DIR"] = os.getenv("OUTPUT_DIR") if os.getenv("OUTPUT_DIR") else DEFAULT_OUTPUT_DIR
os.makedirs(os.getenv("OUTPUT_DIR"), exist_ok=True)

sections_folder = os.path.join(os.getenv("OUTPUT_DIR"), "sections")
os.makedirs(sections_folder, exist_ok=True)
logger.info("sections created" if "sections" in os.listdir(
    os.getenv('OUTPUT_DIR')) else "failed while creating sections folder")

laws_folder = os.path.join(os.getenv("OUTPUT_DIR"), "laws")
os.makedirs(laws_folder, exist_ok=True)
logger.info(
    "laws created" if "sections" in os.listdir(os.getenv('OUTPUT_DIR')) else "failed while creating laws folder")


logger.debug(f"Source web path is set to: {os.getenv('SOURCE_WEB_PATH')}")
logger.debug(f"Output file path is set to: {os.getenv('OUTPUT_DIR')}")


if __name__ == '__main__':
    gib_parser = GibParser(source_web_path = os.getenv("SOURCE_WEB_PATH"),
                           sections_folder=sections_folder,
                           laws_folder=laws_folder)
    gib_parser.parse()


