import cv2
import numpy as np
from paddleocr import PaddleOCR
import streamlit as st

@st.cache_resource
def load_ocr_model():
    return PaddleOCR(use_angle_cls=True, lang='en')

def extract_text_from_image(image_bytes):
    ocr = load_ocr_model()
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Performance optimization: Downscale high-res images
    height, width = img.shape[:2]
    if width > 1000:
        new_width = 1000
        new_height = int(height * (1000 / width))
        img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
    result = ocr.ocr(processed, cls=True)

    extracted_items = []
    CONFIDENCE_THRESHOLD = 0.80 # Safety safeguard
    if result and result[0]:
        for line in result[0]:
            text = line[1][0]
            conf = float(line[1][1])
            if conf >= CONFIDENCE_THRESHOLD:
                extracted_items.append({'text': text, 'confidence': conf})
            else:
                extracted_items.append({'text': f"[FLAGGED: Unclear text '{text}']", 'confidence': conf})
    return extracted_items
