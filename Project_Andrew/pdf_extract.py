#V08152026
# =============================================================================
# CAIOS PROJECT ANDREW: PDF Text Extraction
# Shared helper for local file attachments (caios_bridge.py) and web-fetched
# PDFs (os_control.py's fetch_url). Tries native text extraction first
# (fast, exact, no OCR needed for the vast majority of real-world PDFs),
# and falls back to rendering + OCR per-page only for pages with no
# extractable text layer (scanned/image-only PDFs).
# Copyright (c) 2025 Jonathan Schack. License: GPL-3.0 -See LICENSE for details- Contact: X @el_xaber or cai-os.com
# =============================================================================

from typing import Dict, Any, Optional

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("[PDF_EXTRACT] PyMuPDF not installed — PDF support disabled.")
    print("              Install: pip install pymupdf")

# Reuse the same OCR backends caios_bridge.py already has
try:
    import cv2
    from winocr import recognize_cv2_sync
    WINOCR_AVAILABLE = True
except ImportError:
    WINOCR_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False


def _ocr_page_image(pix) -> str:
    """OCR a single rendered PDF page (a PyMuPDF Pixmap)."""
    img_bytes = pix.tobytes("png")

    if WINOCR_AVAILABLE:
        try:
            import numpy as np
            arr = np.frombuffer(img_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is not None:
                result = recognize_cv2_sync(img)
                text = (result.get('text') if isinstance(result, dict) else '') or ''
                text = text.strip()
                if text:
                    return text
        except Exception as e:
            print(f"[PDF_EXTRACT] winocr page OCR failed: {e}")

    if PYTESSERACT_AVAILABLE:
        try:
            import io
            text = pytesseract.image_to_string(Image.open(io.BytesIO(img_bytes))).strip()
            if text:
                return text
        except Exception as e:
            print(f"[PDF_EXTRACT] pytesseract page OCR failed: {e}")

    return ''


def extract_pdf_text(
    source: Any,
    max_pages: int = 30,
    max_chars: int = 12000,
    ocr_dpi: int = 200
) -> Dict[str, Any]:
    """
    Extract text from a PDF, page by page.

    Args:
        source: file path (str/Path) OR raw PDF bytes (e.g. from a web fetch)
        max_pages: cap on pages processed (large PDFs can be slow to OCR)
        max_chars: cap on total returned text length
        ocr_dpi: render resolution for OCR fallback pages

    Returns:
        {
            'status': 'success' | 'unavailable' | 'error',
            'text': str,
            'pages_total': int,
            'pages_processed': int,
            'pages_ocr': int,       # how many pages needed the OCR fallback
            'truncated': bool,
            'error': str (only on 'error'/'unavailable')
        }
    """
    if not PYMUPDF_AVAILABLE:
        return {
            'status': 'unavailable',
            'text': '',
            'error': 'PyMuPDF not installed (pip install pymupdf)'
        }

    try:
        if isinstance(source, (bytes, bytearray)):
            doc = fitz.open(stream=bytes(source), filetype="pdf")
        else:
            doc = fitz.open(str(source))
    except Exception as e:
        return {'status': 'error', 'text': '', 'error': f'Could not open PDF: {e}'}

    pages_total = len(doc)
    pages_to_process = min(pages_total, max_pages)
    parts = []
    pages_ocr = 0

    for i in range(pages_to_process):
        page = doc[i]
        native_text = page.get_text().strip()

        if native_text:
            parts.append(f"--- Page {i+1} ---\n{native_text}")
        elif WINOCR_AVAILABLE or PYTESSERACT_AVAILABLE:
            pix = page.get_pixmap(dpi=ocr_dpi)
            ocr_text = _ocr_page_image(pix)
            pages_ocr += 1
            if ocr_text:
                parts.append(f"--- Page {i+1} (OCR) ---\n{ocr_text}")
            else:
                parts.append(f"--- Page {i+1} ---\n[no extractable text — image page, OCR found nothing]")
        else:
            parts.append(f"--- Page {i+1} ---\n[no extractable text — image page, OCR unavailable]")

    doc.close()

    full_text = "\n\n".join(parts)
    truncated = pages_total > pages_to_process or len(full_text) > max_chars
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars] + "\n[... truncated]"

    return {
        'status': 'success',
        'text': full_text,
        'pages_total': pages_total,
        'pages_processed': pages_to_process,
        'pages_ocr': pages_ocr,
        'truncated': truncated
    }


def is_pdf(content_type: Optional[str] = None, url_or_path: str = '', magic_bytes: Optional[bytes] = None) -> bool:
    """
    Best-effort PDF detection, checked in priority order:
    1. Content-Type header (most reliable for web fetches)
    2. Magic bytes (%PDF- header) — reliable regardless of headers/extension
    3. URL/path extension (weakest signal, reasonable last resort)
    """
    if content_type and 'application/pdf' in content_type.lower():
        return True
    if magic_bytes and magic_bytes[:5] == b'%PDF-':
        return True
    if url_or_path.lower().split('?')[0].endswith('.pdf'):
        return True
    return False
