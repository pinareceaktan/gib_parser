# GİB Parser

**GİB Parser**, [Gelir İdaresi Başkanlığı](https://www.gib.gov.tr/mevzuat/vergi-mevzuati) web sitesindeki **vergi mevzuatı, kanunlar, kararlar ve gerekçeleri** otomatik olarak tarayan, PDF bağlantılarını indiren ve verileri işlenebilir formata dönüştüren bir **Python scraping kütüphanesi**dir.

Proje, uzun vadede **Agentic RAG (Retrieval-Augmented Generation)** tabanlı bir yapay zekâ sistemine içerik sağlayıcı bileşen olmayı hedefler.

---

## 🚀 Özellikler

- **Selenium tabanlı client**  
  - Headless / non-headless Chrome desteği  
  - Komponent tabanlı locator yönetimi (`ComponentManager`)  
  - `WebComponent` dataclass ile merkezi selector kaydı  

- **Dinamik içerik bekleme**  
  - Decorator tabanlı `wait_for_*` fonksiyonları  
  - Tablo, combobox, gerekçe ve karar listeleri için özel bekleme stratejileri  

- **Pagination & navigation**  
  - MUI tabanlı sayfa numaralandırma desteği  
  - Kanun kartlarını ve detay sayfalarını otomatik gezinme  

- **Yeni tab işleme**  
  - `target="_blank"` ile açılan sayfaları tespit etme  
  - Yeni sekmeye geçiş, içerik işleme, geri dönüş akışı  

- **PDF ve içerik çıkarma (planlanan)**  
  - Cumhurbaşkanı kararları ve gerekçelerin PDF indirilmesi  
  - OCR / metin işleme entegrasyonu  

---

## 📦 Kurulum

### Gereksinimler
- Python 3.8+ (test edilmiş: 3.8, 3.10, 3.11)  
- Google Chrome (güncel sürüm)  
- [ChromeDriver](https://chromedriver.chromium.org/) (Selenium ile uyumlu)  

### Ortam kurulumu
```bash
git clone https://github.com/pinareceaktan/gib_parser.git
cd gib_parser

# Conda ile örnek
conda create -n env-scrap python=3.10
conda activate env-scrap

pip install -r requirements.txt

```

## 🧑‍💻 Kullanım  
### Basit örnek
```python
from gib_parser.client import SeleniumClient

URL = "https://www.gib.gov.tr/mevzuat/vergi-mevzuati"

client = SeleniumClient(source_web_page=URL, headless=True)

# Kanun kartlarını listele
laws = client.list_basic_laws()
for law in laws:
    print(law["title"], law["detail_url"])
```

### Pagination üzerinde gezinme
```python
for page_num in range(1, 5):  # örnek ilk 4 sayfa
    client.go_to_page(page_num)
    laws = client.list_basic_laws()
    ...

Yeni tab açılıp scraping yapma
anchors = client.driver.find_elements(By.CSS_SELECTOR, 'a[href^="/mevzuat/kanun/"]')
client.process_links_in_new_tabs(anchors, scrape_fn=my_scraper)
```

## Tam otomatik crawl (scripts/parse.py)

Tüm kanunların içindeki maddeler ve gerekçeler dahil olmak üzere otomatik olarak taramak için:

```python
python scripts/parse.py
```

Bu script:

Tüm pagination sayfalarındaki kanun kartlarını sırayla ziyaret eder,

Her kanun için maddeler ve gerekçeler sayfalarını açar,

İlgili verileri kaydeder (çıktı dizini data/ altında).
```

📂 Proje Yapısı
gib_parser/
├── client/                   # SeleniumClient ve tarama akışları
├── helpers/                  # Abstract sınıflar, decoratorler
├── utils/                    # Logger, yardımcı fonksiyonlar
├── schema.py                 # WebComponent registry (XPATH/CSS seçiciler)
├── scripts/
│   └── parse.py              # Tüm kanun-madde-gerekçe crawl scripti
└── tests/                    # Test senaryoları


SeleniumClient → Tüm sürücü işlemlerini yöneten sınıf

ComponentManager → Registry’den locator yönetimi

Decoratorler (wait_for_*) → Dinamik beklemeler

scripts/parse.py → Tüm vergi kanunlarını, maddeleri ve gerekçeleri otomatik olarak tarar

```

## 📌 Yol Haritası

 [x] Temel kanun kartlarının çıkarılması  
 [x] Yeni tab geçişi ve scraping  
 [x] Pagination desteği  
 [x] Tüm kanun → madde → gerekçe zincirinin otomatik crawl edilmesi  
 [ ] Cumhurbaskani kararlari, bkk, ozelge ve genelgelerin crawel edilmesi  
 [ ] PDF linklerinin indirilmesi ve işlenmesi
 [ ] Text normalizasyon & temizleme
 [ ] Vector DB entegrasyonu (Milvus / FAISS)
 [ ] Agentic RAG pipeline ile entegrasyon

## 🤝 Katkı

Pull request’ler ve issue’lar memnuniyetle karşılanır.
Selector değişiklikleri veya yeni içerik tipleri için schema.py güncellenebilir.

## 📜 Lisans

MIT License. Ayrıntılar için LICENSE
 dosyasına bakınız.