import re
import pdfplumber


class PDFExtractError(Exception):
    pass


def extract_text(file_storage):
    try:
        text = ""
        with pdfplumber.open(file_storage) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    except Exception as e:
        raise PDFExtractError(f"Could not read PDF: {e}")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
