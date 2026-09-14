"""
Verification Adapters for ProcureGuard.

Each adapter wraps an external verification source (GST, CPPP, Udyam, UDIN, BIS).
We are now using real HTTP requests to external government APIs (simulated by our gov_api service).

CRITICAL RULE: UNAVAILABLE -> REVIEW (never FAIL).
"""
import time
import requests
from datetime import datetime, timezone
from typing import Dict, Any
from app.config import settings

# In a real environment, these would be in settings
GST_API_URL = "http://localhost:8001/api/v1/gstin"
CPPP_API_URL = "http://localhost:8001/api/v1/cppp/status"

class VerificationAdapter:
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class GSTAdapter(VerificationAdapter):
    """GST verification via external API."""
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        gstin = (data.get("gstin") or "").upper()
        if not gstin or "UNREADABLE" in gstin or "NOT FOUND" in gstin:
            return {"status": "UNAVAILABLE", "source": "GSTN API", "response_code": 400, "checked_at": datetime.now(timezone.utc).isoformat()}
            
        try:
            resp = requests.get(f"{GST_API_URL}/{gstin}", timeout=5)
            if resp.status_code == 200:
                result = resp.json()
                return {
                    "status": result.get("status"), 
                    "source": "GSTN API", 
                    "response_code": 200, 
                    "checked_at": result.get("last_updated")
                }
            elif resp.status_code == 404:
                return {"status": "NOT_FOUND", "source": "GSTN API", "response_code": 404, "checked_at": datetime.now(timezone.utc).isoformat()}
            else:
                return {"status": "UNAVAILABLE", "source": "GSTN API", "response_code": resp.status_code, "checked_at": datetime.now(timezone.utc).isoformat()}
        except Exception as e:
            return {"status": "UNAVAILABLE", "source": "GSTN API (Timeout/Error)", "response_code": 503, "checked_at": datetime.now(timezone.utc).isoformat()}

class CPPPAdapter(VerificationAdapter):
    """CPPP debarment check via external API."""
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        company_name = (data.get("company_name") or "").strip()
        try:
            resp = requests.post(CPPP_API_URL, json={"company_name": company_name}, timeout=5)
            if resp.status_code == 200:
                result = resp.json()
                return {
                    "debarred": result.get("debarred"),
                    "reason": result.get("reason"),
                    "source": "CPPP API",
                    "response_code": 200,
                    "checked_at": result.get("checked_at")
                }
            elif resp.status_code == 404:
                return {
                    "status": "UNAVAILABLE",
                    "debarred": None,
                    "reason": resp.json().get("detail", "Not found"),
                    "source": "CPPP API",
                    "response_code": 404
                }
            else:
                return {"status": "UNAVAILABLE", "debarred": None, "reason": "API Error", "source": "CPPP API", "response_code": resp.status_code}
        except Exception as e:
            return {"status": "UNAVAILABLE", "debarred": None, "reason": str(e), "source": "CPPP API (Timeout/Error)", "response_code": 503}

class UdyamAdapter(VerificationAdapter):
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        udyam_no = data.get("udyam_no", "")
        time.sleep(0.1)
        if "UDYAM" in udyam_no.upper():
            return {"valid": True, "category": "MICRO", "source": "Udyam API (Stub)", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}
        return {"valid": False, "source": "Udyam API (Stub)", "response_code": 404, "checked_at": datetime.now(timezone.utc).isoformat()}

class UDINAdapter(VerificationAdapter):
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.1)
        return {"status": "UNAVAILABLE", "source": "UDIN API (Stub)", "response_code": 503, "message": "UDIN service offline.", "checked_at": datetime.now(timezone.utc).isoformat()}

class BISAdapter(VerificationAdapter):
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.1)
        return {"status": "UNAVAILABLE", "source": "BIS API (Stub)", "response_code": 503, "message": "BIS service offline.", "checked_at": datetime.now(timezone.utc).isoformat()}

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
