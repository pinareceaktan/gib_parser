import pandas as pd



from gib_parser import get_logger


base_logger = get_logger(__name__)


def save_text(text, path) -> None:
    if not path.endswith("txt"):
        base_logger.error("File name should end with a txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    base_logger.info(f"✅ Saved: {path}")


def save_pdf(content, path):
    if not path.endswith("pdf"):
        base_logger.error("File name should end with a pdf")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content)


def save_csv(table: pd.DataFrame, path: str):
    if not path.endswith("csv"):
        base_logger.error("File name should end with a csv")
    table.to_csv(path, index=True, encoding="utf-8-sig")
    base_logger.info(f"✅ saved: {path}")