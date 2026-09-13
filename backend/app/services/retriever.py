import hashlib
from typing import Dict, Any, List
import io
import re
import pymupdf
import pytesseract
from PIL import Image

from app.config import settings
from app.storage import minio_client
from app.database import SessionLocal
from app import models

class VisualRetriever:
    """Interface for visual document retrieval models (e.g. ColPali)."""
    def retrieve(self, document_id: str, document_hash: str, rule_id: str,
                 page_count: int = 7) -> Dict[str, Any]:
        raise NotImplementedError

class TextRetriever(VisualRetriever):
    def __init__(self):
        self.keywords = {
            "RULE-GST": ["gstin", "gst identification", "goods and services tax", "registration"],
            "RULE-TURNOVER": ["turnover", "annual turnover", "financial turnover", "financial overview"],
            "RULE-CPPP": ["debarred", "blacklisted", "banned", "suspension", "cppp debarment status"],
            "RULE-LOCAL-CONTENT": ["local content", "percentage", "class-i", "indigenous"],
            "RULE-OEM": ["oem authorization", "authorized oem", "manufacturer authorization", "authorization letter"]
        }

    def _extract_blocks(self, doc_bytes: bytes) -> List[Dict]:
        doc = pymupdf.open("pdf", doc_bytes)
        blocks = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text").strip()
            
            if len(text) < 20: # Fallback to OCR if scanned
                try:
                    pix = page.get_pixmap(dpi=150)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    text = pytesseract.image_to_string(img).strip()
                except Exception as e:
                    pass
                    
            if text:
                blocks.append({
                    "page_number": page_num + 1,
                    "bbox": [0, 0, page.rect.width, page.rect.height],
                    "text": text,
                    "source": "PyMuPDF Page"
                })
        return blocks

    def retrieve(self, document_id: str, document_hash: str, rule_id: str,
                 page_count: int = 7) -> Dict[str, Any]:
        
        db = SessionLocal()
        try:
            doc = db.query(models.Document).filter(models.Document.id == document_id).first()
            if not doc:
                raise ValueError("Document not found")
            pdf_bytes = minio_client.download_file_bytes(doc.minio_path)
        finally:
            db.close()

        blocks = self._extract_blocks(pdf_bytes)
        
        rule_keywords = self.keywords.get(rule_id, [])
        best_block = None
        best_score = -1

        for block in blocks:
            text_lower = block["text"].lower()
            score = 0
            for kw in rule_keywords:
                if kw in text_lower:
                    score += 10
            
            if score > 0:
                score += len(re.findall(r'\d+', text_lower))
                
            if score > best_score:
                best_score = score
                best_block = block
                
        if best_block and best_score > 0:
            return {
                "document_id": document_id,
                "page_number": best_block["page_number"],
                "bounding_box": best_block["bbox"],
                "retrieved_text": best_block["text"].replace('\n', ' ').strip(),
                "retrieval_score": round(min(0.5 + (best_score / 50.0), 0.99), 2),
                "model": f"TextRetriever ({best_block['source']})"
            }
        
        return {
            "document_id": document_id,
            "page_number": 1,
            "bounding_box": [0,0,0,0],
            "retrieved_text": "",
            "retrieval_score": 0.0,
            "model": "TextRetriever (No Match)"
        }

class ColPaliRetriever(VisualRetriever):
    """Stub for real ColPali visual retrieval via external endpoint."""
    def retrieve(self, document_id: str, document_hash: str, rule_id: str,
                 page_count: int = 7) -> Dict[str, Any]:
        raise NotImplementedError(
            "Real ColPali inference requires a configured MODEL_ENDPOINT. "
            "Set AI_MODE=demo or auto to use TextRetriever."
        )

def get_retriever() -> VisualRetriever:
    if settings.AI_MODE == 'real':
        return ColPaliRetriever()
    return TextRetriever()
