from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.models import VerificationStatus

class VerificationResultDTO:
    def __init__(
        self,
        source: str,
        request_identifier: str,
        status: VerificationStatus,
        response_data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        adapter_version: str = "1.0.0"
    ):
        self.source = source
        self.request_identifier = request_identifier
        self.status = status
        self.response_data = response_data or {}
        self.success = success
        self.error_code = error_code
        self.error_message = error_message
        self.adapter_version = adapter_version
        self.verified_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "request_identifier": self.request_identifier,
            "status": self.status.value,
            "response_data": self.response_data,
            "success": self.success,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "adapter_version": self.adapter_version,
            "verified_at": self.verified_at.isoformat()
        }

class BaseVerificationAdapter(ABC):
    source_name: str = "BASE"
    adapter_version: str = "1.0.0"

    @abstractmethod
    def verify(self, identifier: str, payload: Optional[Dict[str, Any]] = None) -> VerificationResultDTO:
        pass

# 1. GST Verification Adapter
class MockGSTAdapter(BaseVerificationAdapter):
    source_name = "GST"
    adapter_version = "1.0.0"

    def verify(self, identifier: str, payload: Optional[Dict[str, Any]] = None) -> VerificationResultDTO:
        clean_id = (identifier or "").strip().upper()
        
        if "DOWN" in clean_id or clean_id == "GST123DOWN":
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.UNAVAILABLE,
                success=False,
                error_code="GST_PORTAL_TIMEOUT",
                error_message="GSTN Portal API is temporarily unreachable (HTTP 503)",
                adapter_version=self.adapter_version
            )
        
        if "INVALID" in clean_id or clean_id == "GST123INVALID":
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.INVALID,
                response_data={
                    "gstin": identifier,
                    "status": "Cancelled",
                    "reason": "Non-compliance with filing requirements",
                    "taxpayer_type": "Regular",
                    "legal_name": "Unknown Entity"
                },
                success=True,
                adapter_version=self.adapter_version
            )
            
        if "EXPIRED" in clean_id or clean_id == "GST123EXPIRED":
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.EXPIRED,
                response_data={
                    "gstin": identifier,
                    "status": "Expired",
                    "valid_until": "2023-12-31"
                },
                success=True,
                adapter_version=self.adapter_version
            )

        # Default valid match
        payload_data = payload or {}
        return VerificationResultDTO(
            source=self.source_name,
            request_identifier=identifier,
            status=VerificationStatus.VALID,
            response_data={
                "gstin": identifier,
                "legal_name": payload_data.get("legal_name", "Registered Vendor Co."),
                "status": "Active",
                "registration_date": "2018-07-01",
                "taxpayer_type": "Regular",
                "jurisdiction": "State - Delhi, Center - Range 12",
                "filing_status_last_quarter": "FILED"
            },
            success=True,
            adapter_version=self.adapter_version
        )

# 2. MSME / Udyam Verification Adapter
class MockUdyamAdapter(BaseVerificationAdapter):
    source_name = "Udyam"
    adapter_version = "1.0.0"

    def verify(self, identifier: str, payload: Optional[Dict[str, Any]] = None) -> VerificationResultDTO:
        clean_id = (identifier or "").strip().upper()

        if "DOWN" in clean_id:
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.UNAVAILABLE,
                success=False,
                error_code="UDYAM_PORTAL_TIMEOUT",
                error_message="Ministry of MSME Udyam verification service unavailable",
                adapter_version=self.adapter_version
            )

        if "INVALID" in clean_id:
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.INVALID,
                response_data={"udyam_number": identifier, "status": "Deregistered / Invalid"},
                success=True,
                adapter_version=self.adapter_version
            )

        return VerificationResultDTO(
            source=self.source_name,
            request_identifier=identifier,
            status=VerificationStatus.VALID,
            response_data={
                "udyam_number": identifier,
                "enterprise_type": "Small Enterprise",
                "major_activity": "Manufacturing / IT Hardware",
                "social_category": "General",
                "date_of_incorporation": "2019-04-15",
                "msme_verified": True
            },
            success=True,
            adapter_version=self.adapter_version
        )

# 3. Debarment Verification Adapter (GeM Debarment / CPPP blacklist)
class MockDebarmentAdapter(BaseVerificationAdapter):
    source_name = "Debarment"
    adapter_version = "1.0.0"

    def verify(self, identifier: str, payload: Optional[Dict[str, Any]] = None) -> VerificationResultDTO:
        clean_id = (identifier or "").strip().upper()

        if "DOWN" in clean_id:
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.UNAVAILABLE,
                success=False,
                error_code="DEBARMENT_REGISTRY_OFFLINE",
                error_message="Central Debarment Registry query timed out",
                adapter_version=self.adapter_version
            )

        # BAD / DEBARRED case
        if "BAD" in clean_id or "DEBARRED" in clean_id:
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.INVALID, # INVALID here means failed debarment check (is debarred)
                response_data={
                    "identifier": identifier,
                    "is_debarred": True,
                    "order_number": "DEB/2024/9912",
                    "authority": "Department of Expenditure",
                    "reason": "Corrupt or fraudulent practice in previous tender",
                    "debarred_from": "2024-01-01",
                    "debarred_until": "2027-01-01"
                },
                success=True,
                adapter_version=self.adapter_version
            )

        # Good vendor
        return VerificationResultDTO(
            source=self.source_name,
            request_identifier=identifier,
            status=VerificationStatus.VALID, # VALID means NOT debarred / clean record
            response_data={
                "identifier": identifier,
                "is_debarred": False,
                "records_checked": ["CPPP_BLACKLIST", "GEM_INCIDENT_MANAGEMENT", "MHA_BAN_LIST"],
                "status": "CLEAR"
            },
            success=True,
            adapter_version=self.adapter_version
        )

# 4. UDIN Verification Adapter (ICAI CA Certificate)
class MockUDINAdapter(BaseVerificationAdapter):
    source_name = "UDIN"
    adapter_version = "1.0.0"

    def verify(self, identifier: str, payload: Optional[Dict[str, Any]] = None) -> VerificationResultDTO:
        clean_id = (identifier or "").strip().upper()

        if "DOWN" in clean_id:
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.UNAVAILABLE,
                success=False,
                error_code="ICAI_UDIN_TIMEOUT",
                error_message="ICAI UDIN verification gateway unavailable",
                adapter_version=self.adapter_version
            )

        if "INVALID" in clean_id:
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.INVALID,
                response_data={"udin": identifier, "status": "Revoked / Unregistered UDIN"},
                success=True,
                adapter_version=self.adapter_version
            )

        return VerificationResultDTO(
            source=self.source_name,
            request_identifier=identifier,
            status=VerificationStatus.VALID,
            response_data={
                "udin": identifier,
                "ca_name": "R. K. Sharma & Associates",
                "ca_membership_no": "048921",
                "document_type": "Annual Turnover & Net Worth Certificate",
                "date_of_signing": "2024-05-10",
                "status": "Active"
            },
            success=True,
            adapter_version=self.adapter_version
        )

# 5. BIS Verification Adapter (Bureau of Indian Standards)
class MockBISAdapter(BaseVerificationAdapter):
    source_name = "BIS"
    adapter_version = "1.0.0"

    def verify(self, identifier: str, payload: Optional[Dict[str, Any]] = None) -> VerificationResultDTO:
        clean_id = (identifier or "").strip().upper()

        if "DOWN" in clean_id:
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.UNAVAILABLE,
                success=False,
                error_code="BIS_PORTAL_TIMEOUT",
                error_message="BIS CRS portal API timed out",
                adapter_version=self.adapter_version
            )

        if "INVALID" in clean_id:
            return VerificationResultDTO(
                source=self.source_name,
                request_identifier=identifier,
                status=VerificationStatus.INVALID,
                response_data={"standard_number": identifier, "status": "Expired / Non-compliant"},
                success=True,
                adapter_version=self.adapter_version
            )

        return VerificationResultDTO(
            source=self.source_name,
            request_identifier=identifier,
            status=VerificationStatus.VALID,
            response_data={
                "standard_number": identifier,
                "product_category": "Information Technology Equipment - Safety",
                "is_active": True,
                "valid_until": "2027-12-31"
            },
            success=True,
            adapter_version=self.adapter_version
        )

# Registry
class VerificationAdapterRegistry:
    def __init__(self):
        self._adapters: Dict[str, BaseVerificationAdapter] = {
            "GST": MockGSTAdapter(),
            "Udyam": MockUdyamAdapter(),
            "MSME": MockUdyamAdapter(),
            "Debarment": MockDebarmentAdapter(),
            "UDIN": MockUDINAdapter(),
            "BIS": MockBISAdapter(),
        }

    def get_adapter(self, source: str) -> Optional[BaseVerificationAdapter]:
        return self._adapters.get(source)

    def register_adapter(self, source: str, adapter: BaseVerificationAdapter):
        self._adapters[source] = adapter

    def verify(self, source: str, identifier: str, payload: Optional[Dict[str, Any]] = None) -> VerificationResultDTO:
        adapter = self.get_adapter(source)
        if not adapter:
            return VerificationResultDTO(
                source=source,
                request_identifier=identifier,
                status=VerificationStatus.UNAVAILABLE,
                success=False,
                error_code="ADAPTER_NOT_FOUND",
                error_message=f"No verification adapter registered for source '{source}'"
            )
        return adapter.verify(identifier, payload)

verification_registry = VerificationAdapterRegistry()
