from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models import (
    UserRole, TenderStatus, RuleType, Operator, Severity, RuleStatus, 
    RiskLevel, VerificationStatus, OfficerDecisionType, BidStatus
)

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    email: str
    full_name: str
    role: UserRole = UserRole.PROCUREMENT_OFFICER
    department: Optional[str] = "Procurement Division"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserOut(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None

# --- REQUIREMENT SCHEMAS ---
class RequirementBase(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: RuleType
    operator: Operator
    expected_value: str
    unit: Optional[str] = None
    evidence_type: Optional[str] = None
    severity: Severity = Severity.HIGH
    mandatory: bool = True
    enabled: bool = True
    weight: float = 20.0
    exception_logic: Optional[str] = None
    display_order: int = 0

class RequirementCreate(RequirementBase):
    pass

class RequirementUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[RuleType] = None
    operator: Optional[Operator] = None
    expected_value: Optional[str] = None
    unit: Optional[str] = None
    evidence_type: Optional[str] = None
    severity: Optional[Severity] = None
    mandatory: Optional[bool] = None
    enabled: Optional[bool] = None
    weight: Optional[float] = None
    exception_logic: Optional[str] = None
    display_order: Optional[int] = None

class RequirementOut(RequirementBase):
    id: str
    tender_id: str
    tender_version_id: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# --- TENDER SCHEMAS ---
class TenderVersionOut(BaseModel):
    id: str
    tender_id: str
    version_number: int
    change_summary: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class TenderBase(BaseModel):
    tender_number: str
    title: str
    description: Optional[str] = None
    procuring_organization: str
    estimated_value: Optional[float] = None
    currency: str = "INR"

class TenderCreate(TenderBase):
    requirements: Optional[List[RequirementCreate]] = []

class TenderUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    procuring_organization: Optional[str] = None
    status: Optional[TenderStatus] = None
    estimated_value: Optional[float] = None

class TenderOut(TenderBase):
    id: str
    status: TenderStatus
    created_at: datetime
    updated_at: datetime
    requirements_count: Optional[int] = 0
    bids_count: Optional[int] = 0
    class Config:
        from_attributes = True

class TenderDetailOut(TenderOut):
    versions: List[TenderVersionOut] = []
    requirements: List[RequirementOut] = []
    class Config:
        from_attributes = True

# --- BIDDER SCHEMAS ---
class BidderBase(BaseModel):
    name: str
    registration_number: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    udyam_number: Optional[str] = None
    contact_email: str
    contact_phone: Optional[str] = None
    is_msme: bool = False

class BidderCreate(BidderBase):
    pass

class BidderUpdate(BaseModel):
    name: Optional[str] = None
    gstin: Optional[str] = None
    pan: Optional[str] = None
    udyam_number: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    is_msme: Optional[bool] = None

class BidderOut(BidderBase):
    id: str
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

# --- EVIDENCE & DOCUMENT SCHEMAS ---
class EvidenceBase(BaseModel):
    page_number: int = 1
    bounding_box: Optional[List[float]] = None
    extracted_field: str
    extracted_value: str
    confidence: float = 1.0
    source: Optional[str] = "Registered bidder document"

class EvidenceCreate(EvidenceBase):
    document_id: Optional[str] = None
    rule_result_id: Optional[str] = None

class EvidenceOut(EvidenceBase):
    id: str
    document_id: Optional[str] = None
    rule_result_id: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class DocumentOut(BaseModel):
    id: str
    bid_id: str
    document_type: str
    filename: str
    file_path: str
    mime_type: str
    file_size: int
    document_hash: str
    page_count: int
    metadata_json: Optional[Dict[str, Any]] = None
    uploaded_at: datetime
    evidences: List[EvidenceOut] = []
    class Config:
        from_attributes = True

# --- VERIFICATION SCHEMAS ---
class VerificationResultOut(BaseModel):
    id: str
    source: str
    request_identifier: str
    status: VerificationStatus
    response_data: Optional[Dict[str, Any]] = None
    verified_at: datetime
    adapter_version: str
    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    class Config:
        from_attributes = True

class VerificationDirectQuery(BaseModel):
    source: str # GST, Udyam, Debarment, BIS, UDIN
    identifier: str

# --- RULE RESULT & ASSESSMENT SCHEMAS ---
class RuleResultOut(BaseModel):
    id: str
    bid_id: str
    requirement_id: str
    requirement_name: Optional[str] = None
    rule_type: Optional[RuleType] = None
    operator: Optional[Operator] = None
    status: RuleStatus
    actual_value: Optional[str] = None
    expected_value: Optional[str] = None
    unit: Optional[str] = None
    explanation: str
    severity: Severity
    weight: float
    confidence: float
    rule_version: str
    evaluated_at: datetime
    evidences: List[EvidenceOut] = []
    verification_result: Optional[VerificationResultOut] = None
    class Config:
        from_attributes = True

class ScoreBreakdownItem(BaseModel):
    requirement_id: str
    requirement_name: str
    severity: Severity
    weight: float
    status: RuleStatus
    contributed_weight: float

class ComplianceAssessmentOut(BaseModel):
    id: str
    bid_id: str
    compliance_score: float
    risk_level: RiskLevel
    recommendation: RuleStatus
    total_weight: float
    passed_weight: float
    failed_weight: float
    review_weight: float
    summary_metrics: Optional[Dict[str, Any]] = None
    evaluated_at: datetime
    class Config:
        from_attributes = True

# --- REVIEW DECISION SCHEMAS ---
class ReviewDecisionCreate(BaseModel):
    decision: OfficerDecisionType
    officer_notes: str = Field(..., min_length=5, description="Mandatory officer notes justifying the decision")

class ReviewDecisionOut(BaseModel):
    id: str
    bid_id: str
    officer_id: str
    officer_name: Optional[str] = None
    decision: OfficerDecisionType
    officer_notes: str
    reviewed_at: datetime
    created_at: datetime
    class Config:
        from_attributes = True

# --- BID SCHEMAS ---
class BidBase(BaseModel):
    tender_id: str
    bidder_id: str
    bid_number: str
    bid_amount: Optional[float] = None

class BidCreate(BidBase):
    pass

class BidOut(BidBase):
    id: str
    status: BidStatus
    submitted_at: datetime
    created_at: datetime
    bidder: Optional[BidderOut] = None
    documents: List[DocumentOut] = []
    compliance_assessment: Optional[ComplianceAssessmentOut] = None
    review_decisions: List[ReviewDecisionOut] = []
    class Config:
        from_attributes = True

class BidDetailOut(BidOut):
    rule_results: List[RuleResultOut] = []
    class Config:
        from_attributes = True

# --- AUDIT EVENT SCHEMAS ---
class AuditEventOut(BaseModel):
    id: str
    timestamp: datetime
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    request_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    class Config:
        from_attributes = True

# --- JOB STATUS SCHEMAS ---
class JobStatusOut(BaseModel):
    job_id: str
    status: str # QUEUED, PROCESSING, COMPLETED, FAILED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
