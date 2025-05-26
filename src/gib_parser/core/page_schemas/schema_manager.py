from typing import List

from dataclasses import dataclass

from selenium.webdriver.common.by import By



@dataclass(frozen=True)
class WebComponent:
    tag: str
    by: By
    component_id: str


class ComponentManager:
    def __init__(self):
        self.registry = web_component_registry

    def get_component_id_by_tag(self, tag):
        component = self.registry.get(tag)
        if component is None:
            raise KeyError(f"Component with tag '{tag}' not found in registry.")
        return component.by, component.component_id

    def get_all_tags(self) -> List[str]:
        return list(self.registry.keys())

web_component_registry = {
    "level_1_combobox": WebComponent("level_1_combobox", By.ID, "m_kanun"),
    "level_2_left_tabs": WebComponent("level_2_left_tabs", By.CSS_SELECTOR, "div.solSutun ul li"),

    "level_3_maddeler_combobox": WebComponent("level_3_maddeler_combobox", By.ID, "km-select"),
    "level_3_maddeler_body": WebComponent("level_3_maddeler_body", By.ID, "div-icerik-maddeler"),
    "level_3_gerekceler_href_comp": WebComponent("level_3_gerekceler_href_comp", By.ID, "div-liste-gerekce"),
    "level_3_gerekceler_body": WebComponent("level_3_gerekceler_body", By.XPATH, "//ul/li[@onclick[contains(., 'div-icerik-gerekce')]]"),
    "level_3_gerekceler_href": WebComponent("level_3_gerekceler_href", By.XPATH, "//a[contains(text(), 'Buraya')]"),

    "level_3_ck_karari_tab": WebComponent("level_3_ck_karari_tab", By.ID, "mevzuat_ck"),
    "level_3_ck_karari_body": WebComponent("level_3_ck_karari_body", By.XPATH, "//tr[@class='mevzuat-liste-baslik-satir']"),
    "level_3_ck_karari_table_header": WebComponent("level_3_ck_karari_table_header", By.TAG_NAME, "td"),
    "level_3_ck_karari_table_row": WebComponent("level_3_ck_karari_table_row", By.XPATH, "//tr[@onclick[contains(., 'div-icerik-ck')]]"),
    "level_3_ck_karari_table_popup": WebComponent("level_3_ck_karari_table_popup", By.ID, "div-icerik-ck"),
    "level_3_ck_karari_table_popup_pdf_text": WebComponent("level_3_ck_karari_table_popup_pdf_text", By.XPATH, ".//a[contains(text(), 'tıklayınız')]"),

    "level_3_bkk_tab": WebComponent("level_3_bkk_tab", By.ID, "mevzuat_bkk"),
    "level_3_bkk_body": WebComponent("level_3_bkk_body", By.XPATH, "//tr[@class='mevzuat-liste-baslik-satir']"),
    "level_3_bkk_table_header": WebComponent("level_3_bkk_table_header", By.TAG_NAME, "td"),
    "level_3_bkk_table_row": WebComponent("level_3_bkk_table_row", By.XPATH, "//tr[@onclick[contains(., 'div-icerik-bkk')]]"),
    "level_3_bkk_table_popup": WebComponent("level_3_bkk_table_popup", By.ID, "div-icerik-bkk"),
    "level_3_bkk_table_popup_pdf_text": WebComponent("level_3_bkk_table_popup_pdf_text", By.XPATH, ".//a[contains(text(), 'tıklayınız')]"),

    "level_3_yonetmelik_tab": WebComponent("level_3_yonetmelik_tab", By.ID, "mevzuat_yon"),
    "level_3_yonetmelik_body": WebComponent("level_3_yonetmelik_body", By.XPATH, "//tr[@class='mevzuat-liste-baslik-satir']"),
    "level_3_yonetmelik_table_header": WebComponent("level_3_yonetmelik_table_header", By.TAG_NAME, "td"),
    "level_3_yonetmelik_table_row": WebComponent("level_3_yonetmelik_table_row", By.XPATH, "//tr[@onclick[contains(., 'div-icerik-yon')]]"),
    "level_3_yonetmelik_table_popup": WebComponent("level_3_yonetmelik_table_popup", By.ID, "div-icerik-yon"),
    "level_3_yonetmelik_table_popup_pdf_text": WebComponent("level_3_yonetmelik_table_popup_pdf_text", By.XPATH, ".//a[contains(text(), 'tıklayınız')]"),

    "level_3_ic_genelgeler_tab": WebComponent("level_3_ic_genelgeler_tab", By.ID, "mevzuat_ig"),
    "level_3_ic_genelgeler_body": WebComponent("level_3_ic_genelgeler_body",  By.XPATH, "//tr[@class='mevzuat-liste-baslik-satir']"),
    "level_3_ic_genelgeler_table_header": WebComponent("level_3_genel_yazilar_table_header", By.TAG_NAME, "td"),
    "level_3_ic_genelgeler_table_row": WebComponent("level_3_ic_genelgeler_table_row", By.XPATH, "//tr[@onclick[contains(., 'div-icerik-ig')]]"),
    "level_3_ic_genelgeler_table_popup": WebComponent("level_3_ic_genelgeler_table_popup", By.ID, "div-icerik-ig"),
    "level_3_ic_genelgeler_table_popup_pdf_text": WebComponent("level_3_ic_genelgeler_table_popup_pdf_text", By.XPATH, ".//a[contains(text(), 'tıklayınız')]"),

    "level_3_genel_yazilar_tab": WebComponent("level_3_genel_yazilar_tab", By.ID, "mevzuat_gy"),
    "level_3_genel_yazilar_body": WebComponent("level_3_genel_yazilar_body", By.XPATH, "//tr[@class='mevzuat-liste-baslik-satir']"),
    "level_3_genel_yazilar_table_header": WebComponent("level_3_genel_yazilar_table_header", By.TAG_NAME, "td"),
    "level_3_genel_yazilar_table_row": WebComponent("level_3_genel_yazilar_table_row", By.XPATH, "//tr[@onclick[contains(., 'div-icerik-gy')]]"),
    "level_3_genel_yazilar_table_popup": WebComponent("level_3_genel_yazilar_table_popup", By.ID, "div-icerik-gy"),
    "level_3_genel_yazilar_table_popup_pdf_text": WebComponent("level_3_genel_yazilar_table_popup_pdf_text", By.XPATH, ".//a[contains(text(), 'tıklayınız')]"),

    "level_3_sirkuler_tab": WebComponent("level_3_sirkuler_tab", By.ID, "mevzuat_sir"),
    "level_3_sirkuler_body": WebComponent("level_3_sirkuler_body", By.XPATH, "//tr[@class='mevzuat-liste-baslik-satir']"),
    "level_3_sirkuler_table_header": WebComponent("level_3_sirkuler_table_header", By.TAG_NAME, "td"),
    "level_3_sirkuler_table_row": WebComponent("level_3_sirkuler_table_row", By.XPATH, "//tr[@onclick[contains(., 'div-icerik-sir')]]"),
    "level_3_sirkuler_table_popup": WebComponent("level_3_sirkuler_table_popup", By.ID, "div-icerik-sir"),
    "level_3_sirkuler_table_popup_pdf_text": WebComponent("level_3_sirkuler_table_popup_pdf_text", By.XPATH, ".//a[contains(text(), 'tıklayınız')]"),
    # "level_3_tebligler_tab": WebComponent("level_3_tebligler_tab"),
    # "level_3_tebligler_body": WebComponent("level_3_tebligler_body"),
    # "level_3_tebligler_table_header": WebComponent("level_3_tebligler_table_header"),
    # "level_3_tebligler_table_row": WebComponent("level_3_tebligler_table_row"),
    # "level_3_tebligler_table_popup": WebComponent("level_3_tebligler_table_popup"),
    # "level_3_tebligler_table_popup_pdf_text": WebComponent("level_3_tebligler_table_popup_pdf_text"),
    # "level_3_ozelgeler_tab": {"by": By.ID, "component_id": "mevzuat_oz"},
    # "level_3_ozelgeler_body": {"by": By.ID, "component_id": "mevzuat_oz"},
    # "level_3_ozelgeler_table_header": {"by": By.ID, "component_id": "mevzuat_oz"},
    # "level_3_ozelgeler_table_row": {"by": By.ID, "component_id": "mevzuat_oz"},
    # "level_3_ozelgeler_table_popup": {"by": By.ID, "component_id": "mevzuat_oz"},
    # "level_3_ozelgeler_table_popup_pdf_text": {"by": By.ID, "component_id": "mevzuat_oz"},
}


