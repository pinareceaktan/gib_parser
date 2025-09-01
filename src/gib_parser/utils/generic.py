import yaml
import os
from typing import Any, Dict
import hashlib
import re


def generate_hash_from_dict(dict_el) -> str:
    base_string = "|".join(list(dict_el.values()))
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

def prep_name(text):
    return text.lower().strip().replace(" ", "_")

def read_yaml(file_path: str) -> Dict[str, Any]:

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
            return data if data else {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format in {file_path}: {e}")


def get_law_details(component_text: str) -> Dict[str, Any]:
    """

    """
    KANUN_NO_RE = re.compile(r"Kanun Numarası:\s*(\d+)")
    RG_SAYI_RE  = re.compile(r"Resmi Gazete Sayısı:\s*(\d+)")
    KABUL_RE    = re.compile(r"Kabul Tarihi\s*:\s*(\d{2}\.\d{2}\.\d{4})")
    RG_TRH_RE   = re.compile(r"Resmi Gazete Tarihi:\s*(\d{2}\.\d{2}\.\d{4})")

    kanun_no = KANUN_NO_RE.search(component_text)
    rg_sayi = RG_SAYI_RE.search(component_text)
    kabul = KABUL_RE.search(component_text)
    rg_trh = RG_TRH_RE.search(component_text)

    meta = dict()
    meta.update({
        "kanun_adi": component_text.split("\n")[1],
        "kanun_numarasi": kanun_no.group(1) if kanun_no else None,
        "resmi_gazete_sayisi": rg_sayi.group(1) if rg_sayi else None,
        "kabul_tarihi": kabul.group(1) if kabul else None,
        "resmi_gazete_tarihi": rg_trh.group(1) if rg_trh else None,
    })
    return meta