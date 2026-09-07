from typing import Dict, Any, Optional
import io
import pymupdf as fitz

def extract_pdf_info(file_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts PDF metadata, page count, and dimensions using PyMuPDF (fitz).
    """
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        page_count = doc.page_count
        metadata = doc.metadata or {}
        
        pages_info = []
        for i in range(min(page_count, 10)):  # first 10 pages info
            page = doc.load_page(i)
            rect = page.rect
            pages_info.append({
                "page_number": i + 1,
                "width": rect.width,
                "height": rect.height
            })
            
        doc.close()
        return {
            "page_count": page_count,
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
            },
            "pages": pages_info,
            "is_valid_pdf": True
        }
    except Exception as e:
        return {
            "page_count": 1,
            "metadata": {},
            "pages": [],
            "is_valid_pdf": False,
            "error": str(e)
        }
