import sys
import time
import requests
import os
import logging
from typing import Dict


from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import hashlib


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_print_handler = logging.StreamHandler(sys.stdout)
handler_format = logging.Formatter("[%(levelname)s|%(filename)s:%(lineno)s] %(asctime)s >> %(message)s")
console_print_handler.setFormatter(handler_format)
logger.addHandler(console_print_handler)


## Helpers
def generate_hash_from_dict(dict_el) -> dict:
    base_string = "|".join(list(dict_el.values()))
    return hashlib.sha256(base_string.encode('utf-8')).hexdigest()

##

# Definitions
DEFAULT_OUTPUT_DIR = os.path.join(os.getcwd(), "..", "output")

os.environ["OUTPUT_DIR"] = os.getenv("OUTPUT_DIR") if os.getenv("OUTPUT_DIR") else DEFAULT_OUTPUT_DIR
os.makedirs(os.getenv("OUTPUT_DIR"), exist_ok=True)

sections_folder = os.path.join(os.getenv("OUTPUT_DIR"), "sections")
os.makedirs(sections_folder, exist_ok=True)
logger.info("sections created" if "sections" in os.listdir(os.getenv('OUTPUT_DIR')) else "failed while creating sections folder")

laws_folder = os.path.join(os.getenv("OUTPUT_DIR"), "laws")
os.makedirs(laws_folder, exist_ok=True)
logger.info("laws created" if "sections" in os.listdir(os.getenv('OUTPUT_DIR')) else "failed while creating laws folder")


SOURCE_WEB_PATH = "https://www.gib.gov.tr/gibmevzuat"

logger.debug(f"Source web path is set to: {SOURCE_WEB_PATH}")
logger.debug(f"Output file path is set to: {os.getenv('OUTPUT_DIR')}")


# Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(SOURCE_WEB_PATH)
driver.implicitly_wait(3)

logger.info("Selenium Driver set")

logger.info("Started processing:||")

# ** Ilk combobox, kanun tipini secer
select_element_lv1 = driver.find_element("id", "m_kanun")
select_lv1 = Select(select_element_lv1)
# Bu comboboxtaki tum elemanlari al
combobox_options_lv1 = select_lv1.options

# Process all elements in dropdown
for index in range(1, len(combobox_options_lv1)):  # skip first line

    select_lv1.select_by_index(index)
    driver.implicitly_wait(2)

    kanun_adi = combobox_options_lv1[index].text.strip().replace(" ", "_")
    logger.info(f"\n➡️Processing Law:<<{kanun_adi}>>")

    # * Simdi level 1 de acilan sayfadaki sol tablodan secim yapacagiz
    left_component_elements = driver.find_elements(By.CSS_SELECTOR, "div.solSutun ul li")
    for left_el in left_component_elements:
        section_title = left_el.text.strip().replace(" ", "_")

        logger.info(f"\n➡️Clicking Section: {section_title}")

        if False:
        # if section_title.lower() == "maddeler":
            # <-- Sayfadaki htmlin texte cevirilip indirilmesi

            left_el.click()
            time.sleep(10)

            # # * Dolmasini bekle
            # wait = WebDriverWait(driver, 10)
            # # Önce combobox'ın gelmesini bekle
            # wait.until(EC.presence_of_element_located((By.ID, "km-select")))
            # # Sonra o combobox'ın içine en az 2 seçenek gelmesini bekle (Hepsi + içerik)
            # wait.until(lambda d: len(Select(d.find_element(By.ID, "km-select")).options) > 1)

            combobox_lv2 = Select(driver.find_element(By.ID, "km-select"))

            # Sol tabdan acilan drop downu bul
            combobox_lv2_options = combobox_lv2.options

            for lv2_index, lv2_combobox_el in enumerate(combobox_lv2_options):
                if lv2_index == 0:# skip first line
                    continue
                combobox_lv2.select_by_index(lv2_index)
                driver.implicitly_wait(5)

                value = lv2_combobox_el.text.strip().replace(" ", "_")
                logger.info(f"➡️{section_title}/{value} okunuyor..")

                try:
                    content = driver.find_element(By.ID, "div-icerik-maddeler")
                    time.sleep(15)
                    text = content.text.strip()
                    if len(text) > 10:  # boş gelmediğine emin ol
                        # Sectionlara kaydet
                        sections_path = os.path.join(sections_folder, section_title)
                        os.makedirs(sections_path, exist_ok=True)
                        filename = os.path.join(sections_path, f"{kanun_adi}_{section_title}_{value}.txt")
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(text)
                        logger.info(f"✅ saved: {filename}")

                        # Laws altina kaydet
                        laws_path = os.path.join(laws_folder, kanun_adi)
                        os.makedirs(laws_path, exist_ok=True)
                        filename = os.path.join(laws_path, f"{kanun_adi}_{section_title}_{value}.txt")
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(text)
                        logger.info(f"✅ saved: {filename}")

                    else:
                        logger.warning("⚠️ Empty, didnt write")
                except Exception as e:
                    logger.warning("❌️ No content {e}")
        if False:
        # if section_title.lower() == "gerekçeler":

            driver.find_element(By.ID, "mevzuat_ger").click()

            wait = WebDriverWait(driver, 20)

            # div-liste-gerekce ID'li div geldi mi?
            wait.until(EC.presence_of_element_located((By.ID, "div-liste-gerekce")))

            # Şimdi gerçekten içi dolmuş mu kontrol et
            wait.until(
                lambda d: len(d.find_elements(By.XPATH, "//ul/li[@onclick[contains(., 'div-icerik-gerekce')]]")) > 0)

            gerekce_elements = driver.find_elements(By.XPATH, "//ul/li[@onclick[contains(., 'div-icerik-gerekce')]]")

            for ci in gerekce_elements:

                try:
                    # Gerekçe başlığı
                    gerekce_kanun_adi = ci.text.strip().replace(" ", "_")

                    # Tıkla ve içeriğin yüklenmesini bekle
                    ci.click()
                    time.sleep(2)

                    # "Buraya" linkini bul
                    pdf_link_element = driver.find_element(By.XPATH, "//a[contains(text(), 'Buraya')]")
                    pdf_url = pdf_link_element.get_attribute("href")

                    # Eğer relative gelirse, absolute yap
                    if pdf_url.startswith("fileadmin"):
                        pdf_url = "https://www.gib.gov.tr/" + pdf_url

                    # PDF'i indir
                    response = requests.get(pdf_url)

                    # Sectionlara kaydet
                    sections_path = os.path.join(sections_folder, section_title)
                    os.makedirs(sections_path, exist_ok=True)
                    filename = os.path.join(sections_path, f"{kanun_adi}_{section_title}_{gerekce_kanun_adi}.pdf")

                    with open(filename, "wb") as f:
                        f.write(response.content)

                    logger.info(f"✅ saved: {filename}")

                    # Laws altina kaydet
                    laws_path = os.path.join(laws_folder, kanun_adi)
                    os.makedirs(laws_path, exist_ok=True)
                    filename = os.path.join(laws_path, f"{kanun_adi}_{section_title}_{gerekce_kanun_adi}.pdf")
                    with open(filename, "wb") as f:
                        f.write(response.content)
                    logger.info(f"✅ saved: {filename}")

                except Exception as e:
                    logger.info(f"❌ {ci.text.strip()} için PDF bulunamadı veya hata oluştu: {e}")

        if section_title.lower() == "cumhurbaşkanı_kararları":
            driver.find_element(By.ID, "mevzuat_ck").click()
            wait = WebDriverWait(driver, 20)
            # Şimdi adet elementinin görünür ve tıklanabilir olmasını bekle
            wait.until(EC.presence_of_element_located((By.ID, "div-liste-ck")))

            # Şimdi gerçekten içi dolmuş mu kontrol et
            wait.until(
                lambda d: len(d.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-icerik-ck')]]")) > 0)

            # 1. Başlık satırını bul
            header_row = driver.find_element(By.XPATH, "//tr[@class='mevzuat-liste-baslik-satir']")
            header_cols = header_row.find_elements(By.TAG_NAME, "td")
            headers = [col.text.strip() for col in header_cols]

            # 2. İçerik satırlarını bul (hepsi onclick içeren tr'ler)
            data_rows = driver.find_elements(By.XPATH, "//tr[@onclick[contains(., 'div-icerik-ck')]]")
            # Process table
            all_data = []
            for ix, row in enumerate(data_rows):
                cols = row.find_elements(By.TAG_NAME, "td")
                # Process row and generate unique id
                if len(cols) >= len(headers):
                    row_dict = dict()
                    for ix, header in enumerate(headers):
                        row_dict.update({header: str(cols[ix].text).strip()})
                    unique_id = generate_hash_from_dict(row_dict)
                    row_dict.update({"id": unique_id})
                    # Get extra texts and pdf link

                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", row)
                        driver.execute_script("arguments[0].click();", row)
                        time.sleep(2)
                        # wait for the content
                        wait = WebDriverWait(driver, 10)
                        wait.until(EC.presence_of_element_located((By.ID, "div-icerik-ck")))
                        content_div = driver.find_element(By.ID, "div-icerik-ck")
                        # Get the extra text
                        full_text = content_div.text.strip()
                        row_dict.update({"Detay Aciklama": full_text})
                        # Get the link
                        link_element = content_div.find_element(By.XPATH, ".//a[contains(text(), 'tıklayınız')]")
                        pdf_url = link_element.get_attribute("href")

                        # Make url absolute if needed
                        if pdf_url.startswith("/"):
                            pdf_url = "https://www.gib.gov.tr" + pdf_url

                        # --> Save related pdfs
                        # Generate file_name from karar
                        karar_no = row.find_elements(By.TAG_NAME, "td")[1].text.strip()

                        # Download pdf
                        response = requests.get(pdf_url)

                        # Under Sections
                        sections_path = os.path.join(sections_folder, section_title)
                        os.makedirs(sections_path, exist_ok=True)
                        filename = os.path.join(sections_path, f"{kanun_adi}_{section_title}_{karar_no}_{unique_id}.pdf")
                        row_dict.update({"related_pdf_path": filename})

                        with open(filename, "wb") as f:
                            f.write(response.content)

                        logger.info(f"✅ saved: {filename}")

                        # Under Laws
                        laws_path = os.path.join(laws_folder, kanun_adi)
                        os.makedirs(laws_path, exist_ok=True)
                        filename = os.path.join(laws_path, f"{kanun_adi}_{section_title}_{karar_no}_{unique_id}.pdf")
                        with open(filename, "wb") as f:
                            f.write(response.content)
                        logger.info(f"✅ saved: {filename}")

                    except Exception as e:
                        logger.debug(f"Failed downloading related pdf, error processing line {ix}: {str(e)}")

                    all_data.append(row_dict)

            df = pd.DataFrame(all_data, columns=headers)

            # Save table under sections
            sections_path = os.path.join(sections_folder, section_title)
            os.makedirs(sections_path, exist_ok=True)
            filename = os.path.join(sections_path, f"{kanun_adi}_{section_title}.csv")
            df.to_csv(filename, index=True, encoding="utf-8-sig")

            logger.info(f"✅ saved: {filename}")

            # Save table under laws
            laws_path = os.path.join(laws_folder, kanun_adi)
            os.makedirs(laws_path, exist_ok=True)
            filename = os.path.join(laws_path, f"{kanun_adi}_{section_title}.csv")
            df.to_csv(filename, index=True, encoding="utf-8-sig")

            logger.info(f"✅ saved: {filename}")

        if section_title.lower() == "yönetmelikler":
            print("ece")
            pass
        if section_title.lower() == "tebliğler":
            print("ece")
            pass
        if section_title.lower() == "iç_genelgeler":
            print("ece")
            pass
        if section_title.lower() == "genel_yazılar":
            print("ece")
            pass
        if section_title.lower() == "sirküler":
            print("ece")
            pass
        if section_title.lower() == "özelgeler":
            print("ece")
            pass

    # # PDF bağlantılarını bul
    # links = driver.find_elements("xpath", "//a[contains(@href, '.pdf')]")
    # for link in links:
    #     pdf_url = link.get_attribute("href")
    #     pdf_name = pdf_url.split("/")[-1]
    #     pdf_path = os.path.join(os.getenv("OUTPUT_DIR"), pdf_name)
    #
    #     # PDF dosyasını indir
    #     response = requests.get(pdf_url)
    #     with open(pdf_path, "wb") as f:
    #         f.write(response.content)
    #     print(f"{pdf_name} indirildi.")

driver.quit()