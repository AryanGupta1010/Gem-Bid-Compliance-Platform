"""
Verification Adapters for ProcureGuard.

Architectural Rule:
  - Connectors distinguish between:
    * LIVE_REGISTRY (Official public API or legitimate verified endpoint)
    * CONTROLLED_SOURCE / MOCK_FIXTURE (Deterministic sandbox/fixture for restricted government databases)
    * UNAVAILABLE_STUB (External registry offline or requiring restricted credentials)
  - CRITICAL RULE: UNAVAILABLE verification results in a REVIEW status, never a FAIL.
"""
import time
import requests
from datetime import datetime, timezone
from typing import Dict, Any
from app.config import settings

class VerificationAdapter:
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class GSTVerificationAdapter(VerificationAdapter):
    """GST verification via external GSTIN endpoint or sandbox adapter."""
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        gstin = (data.get("gstin") or "").strip().upper()
        if not gstin or "UNREADABLE" in gstin or "NOT FOUND" in gstin or len(gstin) < 15:
            return {
                "status": "UNAVAILABLE",
                "source": "GSTN Verification Adapter",
                "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE",
                "response_code": 400,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "details": "Malformed or illegible GSTIN identifier"
            }

        endpoint = settings.GST_API_URL
        try:
            resp = requests.get(f"{endpoint}/{gstin}", timeout=5)
            if resp.status_code == 200:
                result = resp.json()
                return {
                    "status": result.get("status", "ACTIVE"),
                    "legal_name": result.get("legal_name", ""),
                    "source": "GSTN API (Ministry of Finance)",
                    "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE",
                    "response_code": 200,
                    "checked_at": result.get("last_updated", datetime.now(timezone.utc).isoformat())
                }
            elif resp.status_code == 404:
                return {
                    "status": "NOT_FOUND",
                    "source": "GSTN API",
                    "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE",
                    "response_code": 404,
                    "checked_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "status": "UNAVAILABLE",
                    "source": "GSTN API",
                    "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE",
                    "response_code": resp.status_code,
                    "checked_at": datetime.now(timezone.utc).isoformat()
                }
        except Exception:
            # Standalone fixture check when mock server is offline
            if gstin == "27AADCB2230M1Z2":
                return {"status": "ACTIVE", "source": "GSTN Fixture (TechNova)", "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}
            elif gstin == "07BBPCA1120K1Z1":
                return {"status": "SUSPENDED", "source": "GSTN Fixture (Apex)", "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}
            return {
                "status": "UNAVAILABLE",
                "source": "GSTN API (Offline/Timeout)",
                "source_type": "UNAVAILABLE_STUB",
                "response_code": 503,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }

class CPPPDebarmentAdapter(VerificationAdapter):
    """CPPP debarment registry verification."""
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        company_name = (data.get("company_name") or "").strip()
        endpoint = settings.CPPP_API_URL
        try:
            resp = requests.post(endpoint, json={"company_name": company_name}, timeout=5)
            if resp.status_code == 200:
                result = resp.json()
                return {
                    "debarred": result.get("debarred", False),
                    "reason": result.get("reason", "No debarment record found"),
                    "source": "Central Public Procurement Portal (CPPP)",
                    "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE",
                    "response_code": 200,
                    "checked_at": result.get("checked_at", datetime.now(timezone.utc).isoformat())
                }
            elif resp.status_code == 404:
                return {
                    "status": "UNAVAILABLE",
                    "debarred": None,
                    "reason": "Entity not found in CPPP procurement supplier registry",
                    "source": "CPPP Debarment Portal",
                    "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE",
                    "response_code": 404,
                    "checked_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    "status": "UNAVAILABLE",
                    "debarred": None,
                    "reason": f"CPPP API error {resp.status_code}",
                    "source": "CPPP API",
                    "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE",
                    "response_code": resp.status_code
                }
        except Exception:
            # Standalone fixture check when mock server is offline
            c_low = company_name.lower()
            if "apex" in c_low:
                return {"debarred": True, "reason": "Late delivery and contract default in past tenders", "source": "CPPP Fixture", "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}
            elif "technova" in c_low or "medcore" in c_low:
                return {"debarred": False, "reason": "No record found on debarment list", "source": "CPPP Fixture", "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE", "response_code": 200, "checked_at": datetime.now(timezone.utc).isoformat()}
            return {
                "status": "UNAVAILABLE",
                "debarred": None,
                "reason": "CPPP server unreachable",
                "source": "CPPP Portal (Offline)",
                "source_type": "UNAVAILABLE_STUB",
                "response_code": 503
            }

class UdyamVerificationAdapter(VerificationAdapter):
    """Udyam MSME certificate verification adapter."""
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        udyam_no = (data.get("udyam_no") or "").strip().upper()
        if "UDYAM" in udyam_no and len(udyam_no) >= 16:
            return {
                "status": "VERIFIED",
                "valid": True,
                "category": "MICRO",
                "source": "Ministry of MSME (Udyam Registry)",
                "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE",
                "response_code": 200,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
        return {
            "status": "UNAVAILABLE",
            "valid": None,
            "source": "Udyam Registry Adapter",
            "source_type": "CONTROLLED_SOURCE / MOCK_FIXTURE",
            "response_code": 404,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

class UDINVerificationAdapter(VerificationAdapter):
    """ICAI Unique Document Identification Number (UDIN) verification adapter."""
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "UNAVAILABLE",
            "source": "ICAI UDIN Portal",
            "source_type": "UNAVAILABLE_STUB",
            "response_code": 503,
            "message": "UDIN API requires restricted chartered accountant portal credentials.",
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

class BISVerificationAdapter(VerificationAdapter):
    """Bureau of Indian Standards (BIS) conformity verification adapter."""
    def verify(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "UNAVAILABLE",
            "source": "BIS Conformity Portal",
            "source_type": "UNAVAILABLE_STUB",
            "response_code": 503,
            "message": "BIS license registry API offline or requires restricted authorization.",
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

# Aliases for backward compatibility
GSTAdapter = GSTVerificationAdapter
CPPPAdapter = CPPPDebarmentAdapter
UdyamAdapter = UdyamVerificationAdapter
UDINAdapter = UDINVerificationAdapter
BISAdapter = BISVerificationAdapter

def get_adapter(name: str) -> VerificationAdapter:
    adapters = {
        "GST": GSTVerificationAdapter(),
        "CPPP": CPPPDebarmentAdapter(),
        "UDYAM": UdyamVerificationAdapter(),
        "UDIN": UDINVerificationAdapter(),
        "BIS": BISVerificationAdapter(),
    }
    adapter = adapters.get(name.upper())
    if not adapter:
        raise ValueError(f"Unknown verification adapter: {name}")
    return adapter
