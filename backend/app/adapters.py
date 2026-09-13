"""
Verification Adapters for ProcureGuard.

Each adapter wraps an external verification source (GST, CPPP, Udyam, UDIN, BIS).
In demo mode, deterministic fixtures are used.

CRITICAL RULE: UNAVAILABLE → REVIEW (never FAIL).
"""
import time
from datetime import datetime, timezone
from typing import Dict, Any
from app.config import settings


class VerificationAdapter:
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class GSTAdapter(VerificationAdapter):
    """GST verification — checks if GSTIN is active."""
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        gstin = data.get("gstin", "").upper()
        time.sleep(0.1)

        # Offline Demo Fixtures based on EXTRACTED identifier
        if gstin == "27AADCB2230M1Z2":
            return {"status": "ACTIVE", "source": "GSTN Offline Demo", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}
        elif gstin == "07BBPCA1120K1Z1":
            return {"status": "SUSPENDED", "source": "GSTN Offline Demo", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}
        elif "UNREADABLE" in gstin or not gstin:
            return {"status": "UNAVAILABLE", "source": "GSTN Offline Demo", "response_code": 503, "checked_at": datetime.now(timezone.utc).isoformat()}

        return {"status": "NOT_FOUND", "source": "GSTN Offline Demo", "response_code": 404, "checked_at": datetime.now(timezone.utc).isoformat()}

class CPPPAdapter(VerificationAdapter):
    """CPPP / Central Procurement Portal debarment check."""
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        company_name = data.get("company_name", "")
        time.sleep(0.1)

        if "Apex" in company_name:
            return {"debarred": True, "reason": "Late delivery in past government contracts.", "source": "CPPP Offline Demo", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}

        return {"debarred": False, "reason": "No record found on debarment list.", "source": "CPPP Offline Demo", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}

class UdyamAdapter(VerificationAdapter):
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        udyam_no = data.get("udyam_no", "")
        time.sleep(0.1)
        if "UDYAM" in udyam_no.upper():
            return {"valid": True, "category": "MICRO", "source": "Udyam Offline Demo", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}
        return {"valid": False, "source": "Udyam Offline Demo", "response_code": 404, "checked_at": datetime.now(timezone.utc).isoformat()}

class UDINAdapter(VerificationAdapter):
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.1)
        return {"status": "UNAVAILABLE", "source": "UDIN Stub", "response_code": 503, "message": "UDIN service offline.", "checked_at": datetime.now(timezone.utc).isoformat()}

class BISAdapter(VerificationAdapter):
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.1)
        return {"status": "UNAVAILABLE", "source": "BIS Stub", "response_code": 503, "message": "BIS service offline.", "checked_at": datetime.now(timezone.utc).isoformat()}

def get_adapter(name: str) -> VerificationAdapter:
    adapters = {
        "GST": GSTAdapter(),
        "CPPP": CPPPAdapter(),
        "UDYAM": UdyamAdapter(),
        "UDIN": UDINAdapter(),
        "BIS": BISAdapter(),
    }
    adapter = adapters.get(name)
    if not adapter:
        raise ValueError(f"Unknown adapter: {name}")
    return adapter
