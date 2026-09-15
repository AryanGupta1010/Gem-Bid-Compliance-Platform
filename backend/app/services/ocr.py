import io
import base64
import logging
import requests
from typing import Dict, Any, List
from datetime import datetime, timezone
import pymupdf

from app.config import settings
from app.storage import minio_client
from app.database import SessionLocal
from app import models
from app.services.exceptions import AIModelUnavailableError

logger = logging.getLogger(__name__)

class OCRService:
    """Interface for targeted OCR extraction."""
    def extract_field(self, document_id: str, document_hash: str,
                      bounding_box: List[int], field_type: str,
                      page_number: int = 1,
                      gstin: str = None, rule_id: str = None,
                      bidder_hint: str = None) -> Dict[str, Any]:
        raise NotImplementedError

class SuryaOCR(OCRService):
    """
    Real Surya OCR service via dedicated microservice.
    Performs targeted OCR on the specified visual bounding box.
    """
    def __init__(self):
        self.endpoint = settings.SURYA_URL

    def _get_page_image_base64(self, document_id: str, page_number: int) -> tuple:
        """Fetch page image from MinIO or render via PyMuPDF."""
        db = SessionLocal()
        try:
            page = db.query(models.PageImage).filter(
                models.PageImage.document_id == document_id,
                models.PageImage.page_number == page_number
            ).first()
            if page and page.minio_path:
                try:
                    img_bytes = minio_client.download_file_bytes(page.minio_path, bucket=settings.MINIO_PAGES_BUCKET)
                    return base64.b64encode(img_bytes).decode("utf-8"), None
                except Exception:
                    pass

            doc = db.query(models.Document).filter(models.Document.id == document_id).first()
            if doc and doc.minio_path:
                pdf_bytes = minio_client.download_file_bytes(doc.minio_path)
                with pymupdf.open("pdf", pdf_bytes) as pdf:
                    if 0 <= page_number - 1 < len(pdf):
                        p = pdf.load_page(page_number - 1)
                        pix = p.get_pixmap(dpi=150)
                        return base64.b64encode(pix.tobytes("png")).decode("utf-8"), p.get_text("text").strip()
        except Exception as exc:
            logger.warning("Could not extract page %d image for doc %s: %s", page_number, document_id, exc)
        finally:
            db.close()
        return None, None

    def extract_field(self, document_id: str, document_hash: str,
                      bounding_box: List[int], field_type: str,
                      page_number: int = 1,
                      gstin: str = None, rule_id: str = None,
                      bidder_hint: str = None) -> Dict[str, Any]:
        try:
            img_b64, page_text = self._get_page_image_base64(document_id, page_number)

            payload = {
                "document_id": document_id,
                "page_number": page_number,
                "image_base64": img_b64,
                "bounding_box": bounding_box or [0, 0, 0, 0],
                "field_type": field_type,
                "bidder_hint": bidder_hint,
                "page_text": page_text
            }
            resp = requests.post(f"{self.endpoint}/ocr", json=payload, timeout=settings.MODEL_TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "extracted_value": data.get("full_text", ""),
                    "confidence": data.get("confidence", 0.95),
                    "model": data.get("model_name", "vikp/surya_rec"),
                    "model_version": data.get("model_version", "0.4.1"),
                    "inference_timestamp": data.get("inference_timestamp", datetime.now(timezone.utc).isoformat()),
                    "bounding_box": bounding_box,
                    "lines": data.get("lines", [])
                }
            else:
                raise AIModelUnavailableError("SURYA", f"Surya service returned HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as exc:
            logger.error("Surya OCR service unavailable: %s", exc)
            raise AIModelUnavailableError("SURYA", f"Surya OCR service is unreachable at {self.endpoint}: {exc}")

class DemoOCR(OCRService):
    """
    Unit-test and development fixture OCR.
    MUST NEVER BE USED IN LIVE PRODUCTION MODE.
    """
    GOLDEN_OCR_FIXTURES = {
        ("27AADCB2230M1Z2", "RULE-TURNOVER"): {"extracted_value": "Audited Annual Turnover Financial Year 2023-24: ₹14.2 Crore", "confidence": 0.97},
        ("27AADCB2230M1Z2", "RULE-GST"): {"extracted_value": "GST Registration Certificate GSTIN: 27AADCB2230M1Z2 Legal Name: TechNova Systems", "confidence": 0.99},
        ("27AADCB2230M1Z2", "RULE-CPPP"): {"extracted_value": "CPPP Verification: No debarment record found. Status: Active and Compliant", "confidence": 1.0},
        ("27AADCB2230M1Z2", "RULE-LOCAL-CONTENT"): {"extracted_value": "Make in India Certificate: Local Content is 62% Class-I Local Supplier", "confidence": 0.95},
        ("27AADCB2230M1Z2", "RULE-OEM"): {"extracted_value": "Manufacturer Authorization: We hereby authorize TechNova Systems Pvt. Ltd. to supply", "confidence": 0.94},

        ("07BBPCA1120K1Z1", "RULE-TURNOVER"): {"extracted_value": "Audited Annual Turnover Financial Year 2023-24: ₹8.5 Crore", "confidence": 0.93},
        ("07BBPCA1120K1Z1", "RULE-GST"): {"extracted_value": "GST Registration Certificate GSTIN: 07BBPCA1120K1Z1 Legal Name: Apex Industrial Solutions", "confidence": 0.96},
        ("07BBPCA1120K1Z1", "RULE-CPPP"): {"extracted_value": "CPPP Debarment Verification: Debarment match found for Apex Industrial Solutions", "confidence": 1.0},
        ("07BBPCA1120K1Z1", "RULE-LOCAL-CONTENT"): {"extracted_value": "Local Content Declaration: 31% Class-II Supplier", "confidence": 0.91},
        ("07BBPCA1120K1Z1", "RULE-OEM"): {"extracted_value": "Manufacturer Authorization: We hereby authorize Apex Core Technologies to supply", "confidence": 0.88},

        ("29CCPMD3340L1Z3", "RULE-TURNOVER"): {"extracted_value": "Audited Annual Turnover Financial Year 2023-24: ₹11.4 Crore", "confidence": 0.89},
        ("29CCPMD3340L1Z3", "RULE-GST"): {"extracted_value": "GST Certificate scan: unreadable smudged characters 29CCPMD????L1Z?", "confidence": 0.42},
        ("29CCPMD3340L1Z3", "RULE-CPPP"): {"extracted_value": "CPPP Verification: No debarment record found. Status: Active and Compliant", "confidence": 1.0},
        ("29CCPMD3340L1Z3", "RULE-LOCAL-CONTENT"): {"extracted_value": "Local Content Declaration: conflicting certificate stating 48% and 52% in separate annexures", "confidence": 0.55},
        ("29CCPMD3340L1Z3", "RULE-OEM"): {"extracted_value": "Manufacturer Authorization: We hereby authorize MedCore Technologies Pvt. Ltd. to supply", "confidence": 0.92},
    }

    def extract_field(self, document_id: str, document_hash: str,
                      bounding_box: List[int], field_type: str,
                      page_number: int = 1,
                      gstin: str = None, rule_id: str = None,
                      bidder_hint: str = None) -> Dict[str, Any]:
        fixture = self.GOLDEN_OCR_FIXTURES.get((gstin, rule_id)) if gstin and rule_id else None
        if fixture:
            return {
                "extracted_value": fixture["extracted_value"],
                "confidence": fixture["confidence"],
                "model": "DemoOCR (Test Fixture Only)",
                "model_version": "test-mock",
                "inference_timestamp": datetime.now(timezone.utc).isoformat(),
                "bounding_box": bounding_box
            }
        return {
            "extracted_value": f"[Test OCR: {field_type}]",
            "confidence": 0.85,
            "model": "DemoOCR (Fallback)",
            "model_version": "test-mock",
            "inference_timestamp": datetime.now(timezone.utc).isoformat(),
            "bounding_box": bounding_box
        }

def get_ocr() -> OCRService:
    if settings.AI_MODE == 'live':
        return SuryaOCR()
    return DemoOCR()
