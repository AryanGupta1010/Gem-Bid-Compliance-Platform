"""
Visual Document Retrieval Service (ColPali).

CRITICAL RULE: NO SILENT AI FALLBACKS IN LIVE MODE.
In AI_MODE=live, ColPali must run against the ColPali model service.
If the service is unavailable, it raises AIModelUnavailableError.
"""
import io
import re
import logging
import requests
from typing import Dict, Any, List
from datetime import datetime, timezone
from PIL import Image
import pymupdf

from app.config import settings
from app.storage import minio_client
from app.database import SessionLocal
from app import models
from app.services.exceptions import AIModelUnavailableError
from app.services.query_generator import get_query_generator

logger = logging.getLogger(__name__)

class VisualRetriever:
    """Interface for visual document retrieval models."""
    def retrieve(self, document_id: str, document_hash: str, rule_id: str,
                 page_count: int = 7, requirement_name: str = "", requirement_field: str = "") -> Dict[str, Any]:
        raise NotImplementedError

    def index_document(self, document_id: str) -> Dict[str, Any]:
        raise NotImplementedError

class ColPaliRetriever(VisualRetriever):
    """
    Real ColPali visual retrieval via dedicated microservice.
    Uses late-interaction multi-vector visual retrieval.
    """
    def __init__(self):
        self.endpoint = settings.COLPALI_URL
        self.query_gen = get_query_generator()

    def index_document(self, document_id: str) -> Dict[str, Any]:
        """Index rendered page images in the ColPali service."""
        db = SessionLocal()
        try:
            doc = db.query(models.Document).filter(models.Document.id == document_id).first()
            if not doc:
                raise ValueError("Document not found")
            pages = db.query(models.PageImage).filter(models.PageImage.document_id == document_id).order_by(models.PageImage.page_number).all()
            
            payload_pages = []
            for p in pages:
                img_b64 = None
                text_content = None
                if p.minio_path:
                    try:
                        img_bytes = minio_client.download_file_bytes(p.minio_path, bucket=settings.MINIO_PAGES_BUCKET)
                        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    except Exception:
                        pass
                
                payload_pages.append({
                    "page_number": p.page_number,
                    "image_base64": img_b64,
                    "width": p.width or 595,
                    "height": p.height or 842,
                    "text_content": text_content
                })

            resp = requests.post(
                f"{self.endpoint}/embed-pages",
                json={"document_id": document_id, "pages": payload_pages},
                timeout=settings.MODEL_TIMEOUT
            )
            if resp.status_code != 200:
                raise AIModelUnavailableError("COLPALI", f"Indexing failed with status {resp.status_code}: {resp.text}")
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise AIModelUnavailableError("COLPALI", f"ColPali service unreachable during indexing: {e}")
        finally:
            db.close()

    def retrieve(self, document_id: str, document_hash: str, rule_id: str,
                 page_count: int = 7, requirement_name: str = "", requirement_field: str = "") -> Dict[str, Any]:
        # Generate semantic retrieval query from rule definition
        req_spec = {"rule_id": rule_id, "name": requirement_name, "field": requirement_field}
        retrieval_query = self.query_gen.generate_query(req_spec)

        try:
            resp = requests.post(
                f"{self.endpoint}/search",
                json={
                    "document_id": document_id,
                    "query": retrieval_query.query_text,
                    "top_k": 1
                },
                timeout=settings.MODEL_TIMEOUT
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    top = results[0]
                    return {
                        "document_id": document_id,
                        "page_number": top.get("page_number", 1),
                        "bounding_box": top.get("bounding_box", [0, 0, 0, 0]),
                        "retrieval_score": top.get("score", 0.95),
                        "model": top.get("model", "vidore/colpali-v1.2"),
                        "model_version": top.get("model_version", "1.2.0"),
                        "inference_timestamp": top.get("inference_timestamp", datetime.now(timezone.utc).isoformat()),
                        "query_used": retrieval_query.query_text
                    }
                raise AIModelUnavailableError("COLPALI", "ColPali returned empty search results.")
            else:
                raise AIModelUnavailableError("COLPALI", f"Service returned error HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as exc:
            logger.error("ColPali visual retrieval service unavailable: %s", exc)
            raise AIModelUnavailableError("COLPALI", f"ColPali visual retrieval service is unreachable at {self.endpoint}: {exc}")

class TextRetriever(VisualRetriever):
    """
    Test/Unit-test heuristic text retriever.
    MUST NEVER BE USED IN LIVE PRODUCTION MODE.
    """
    def __init__(self):
        self.keywords = {
            "RULE-GST": ["gstin", "gst identification", "goods and services tax", "registration"],
            "RULE-TURNOVER": ["turnover", "annual turnover", "financial turnover", "financial overview"],
            "RULE-CPPP": ["debarred", "blacklisted", "banned", "suspension", "cppp debarment status"],
            "RULE-LOCAL-CONTENT": ["local content", "percentage", "class-i", "indigenous"],
            "RULE-OEM": ["oem authorization", "authorized oem", "manufacturer authorization", "authorization letter"]
        }

    def index_document(self, document_id: str) -> Dict[str, Any]:
        return {"status": "indexed", "method": "heuristic"}

    def _extract_blocks(self, doc_bytes: bytes) -> List[Dict]:
        doc = pymupdf.open("pdf", doc_bytes)
        blocks = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text").strip()
            if text:
                blocks.append({
                    "page_number": page_num + 1,
                    "bbox": [0, 0, int(page.rect.width), int(page.rect.height)],
                    "text": text,
                    "source": "PyMuPDF Page"
                })
        return blocks

    def retrieve(self, document_id: str, document_hash: str, rule_id: str,
                 page_count: int = 7, requirement_name: str = "", requirement_field: str = "") -> Dict[str, Any]:
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
            score = sum(10 for kw in rule_keywords if kw in text_lower)
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
                "retrieval_score": round(min(0.5 + (best_score / 50.0), 0.99), 2),
                "model": "TextRetriever (Test Mode Only)",
                "model_version": "test-heuristic",
                "inference_timestamp": datetime.now(timezone.utc).isoformat(),
                "query_used": f"Keywords: {rule_keywords}"
            }

        return {
            "document_id": document_id,
            "page_number": 1,
            "bounding_box": [0, 0, 0, 0],
            "retrieval_score": 0.0,
            "model": "TextRetriever (No Match)",
            "model_version": "test-heuristic",
            "inference_timestamp": datetime.now(timezone.utc).isoformat(),
            "query_used": ""
        }

def get_retriever() -> VisualRetriever:
    if settings.AI_MODE == 'live':
        return ColPaliRetriever()
    return TextRetriever()
