import easyocr
import numpy as np
from PIL import Image

_reader = None


def _get_reader():
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
    return _reader


def ocr_extract(image_path: str) -> str:
    try:
        reader = _get_reader()
        img = Image.open(image_path).convert("RGB")
        img_np = np.array(img)
        results = reader.readtext(img_np)
        if not results:
            return "No text detected in the image."
        texts = [item[1] for item in results]
        return ' '.join(texts)
    except Exception as e:
        return f"OCR failed: {e}"
