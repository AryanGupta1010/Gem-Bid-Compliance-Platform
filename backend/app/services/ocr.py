import hashlib
from typing import Dict, Any, List
from app.config import settings

# ── Golden demo OCR fixtures ─────────────────────────────────────────
# Keyed by (gstin, rule_id) → extracted value and confidence.
# These simulate what targeted OCR (Surya) would extract from the evidence region.

GOLDEN_OCR_FIXTURES = {
    # ── TechNova Solutions (PASS everything) ─────────────────────────
    ("27AADCB2230M1Z2", "RULE-TURNOVER"): {
        "extracted_value": "₹14.2 Crore",
        "confidence": 0.97,
    },
    ("27AADCB2230M1Z2", "RULE-GST"): {
        "extracted_value": "27AADCB2230M1Z2",
        "confidence": 0.99,
    },
    ("27AADCB2230M1Z2", "RULE-CPPP"): {
        "extracted_value": "No debarment record",
        "confidence": 1.0,
    },
    ("27AADCB2230M1Z2", "RULE-LOCAL-CONTENT"): {
        "extracted_value": "62%",
        "confidence": 0.95,
    },
    ("27AADCB2230M1Z2", "RULE-OEM"): {
        "extracted_value": "Valid OEM Authorization Letter — TechNova Solutions",
        "confidence": 0.94,
    },

    # ── Apex Enterprises (FAIL: turnover, GST, local-content, OEM, debarment) ─
    ("07BBPCA1120K1Z1", "RULE-TURNOVER"): {
        "extracted_value": "₹8.5 Crore",
        "confidence": 0.93,
    },
    ("07BBPCA1120K1Z1", "RULE-GST"): {
        "extracted_value": "07BBPCA1120K1Z1",
        "confidence": 0.96,
    },
    ("07BBPCA1120K1Z1", "RULE-CPPP"): {
        "extracted_value": "Debarment match found",
        "confidence": 1.0,
    },
    ("07BBPCA1120K1Z1", "RULE-LOCAL-CONTENT"): {
        "extracted_value": "31%",
        "confidence": 0.91,
    },
    ("07BBPCA1120K1Z1", "RULE-OEM"): {
        "extracted_value": "OEM Letter — name mismatch: 'Apex Core Technologies' vs 'Apex Enterprises'",
        "confidence": 0.88,
    },

    # ── MedCore Systems (REVIEW: GST unclear, local-content conflicting) ──
    ("29CCPMD3340L1Z3", "RULE-TURNOVER"): {
        "extracted_value": "₹11.4 Crore",
        "confidence": 0.89,
    },
    ("29CCPMD3340L1Z3", "RULE-GST"): {
        "extracted_value": "Unreadable / Illegible scan",
        "confidence": 0.42,
    },
    ("29CCPMD3340L1Z3", "RULE-CPPP"): {
        "extracted_value": "No debarment record",
        "confidence": 1.0,
    },
    ("29CCPMD3340L1Z3", "RULE-LOCAL-CONTENT"): {
        "extracted_value": "Evidence conflicts — forty-eight percent in one section, fifty-two percent in another",
        "confidence": 0.55,
    },
    ("29CCPMD3340L1Z3", "RULE-OEM"): {
        "extracted_value": "Valid OEM Authorization Letter — MedCore Systems",
        "confidence": 0.92,
    },
}


class OCRService:
    """Interface for targeted OCR extraction (e.g. Surya)."""
    def extract_field(self, document_id: str, document_hash: str,
                      bounding_box: List[int], field_type: str,
                      gstin: str = None, rule_id: str = None) -> Dict[str, Any]:
        raise NotImplementedError


class DemoOCR(OCRService):
    """
    Deterministic OCR using golden-demo fixture sets.
    Returns realistic extracted values per (gstin, rule_id).
    """
    def extract_field(self, document_id: str, document_hash: str,
                      bounding_box: List[int], field_type: str,
                      gstin: str = None, rule_id: str = None) -> Dict[str, Any]:

        fixture = GOLDEN_OCR_FIXTURES.get((gstin, rule_id)) if gstin and rule_id else None

        if fixture:
            return {
                "extracted_value": fixture["extracted_value"],
                "confidence": fixture["confidence"],
                "model": "DemoOCR (Golden Fixture)",
                "bounding_box": bounding_box
            }

        # Fallback: hash-deterministic placeholder
        combined = f"{document_hash}_{field_type}".encode('utf-8')
        det_hash = int(hashlib.md5(combined).hexdigest(), 16)
        confidence = 0.75 + ((det_hash % 25) / 100.0)

        return {
            "extracted_value": f"[Demo OCR: {field_type}]",
            "confidence": round(confidence, 2),
            "model": "DemoOCR (Hash Fallback)",
            "bounding_box": bounding_box
        }


class SuryaOCR(DemoOCR):
    """Real Surya OCR via external endpoint. Falls back to DemoOCR if unavailable."""
    def extract_field(self, document_id: str, document_hash: str,
                      bounding_box: List[int], field_type: str,
                      gstin: str = None, rule_id: str = None) -> Dict[str, Any]:
        
        endpoint = settings.MODEL_ENDPOINT
        if endpoint:
            try:
                import requests
                payload = {
                    "document_id": document_id,
                    "bounding_box": bounding_box,
                    "field_type": field_type
                }
                # Short timeout so fallback is quick
                resp = requests.post(f"{endpoint}/v1/ocr", json=payload, timeout=2)
                
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "extracted_value": data.get("extracted_value", ""),
                        "confidence": data.get("confidence", 0.90),
                        "model": "SuryaOCR (Network API)",
                        "bounding_box": bounding_box
                    }
            except Exception as e:
                pass
                
        # Fallback to the deterministic DemoOCR implementation
        result = super().extract_field(document_id, document_hash, bounding_box, field_type, gstin, rule_id)
        if "model" in result:
            result["model"] += " [Network Unavailable Fallback]"
        return result


def get_ocr() -> OCRService:
    if settings.AI_MODE == 'real':
        return SuryaOCR()
    return DemoOCR()

