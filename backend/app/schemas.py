from datetime import date
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal

# ── Auth ──────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)

# ── Document ──────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    id: str
    filename: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    hash_sha3_512: Optional[str] = None
    minio_path: Optional[str] = None
    status: str
    processing_stage: Optional[str] = None
    page_count: Optional[int] = None

    class Config:
        from_attributes = True

class PageImageResponse(BaseModel):
    id: str
    page_number: int
    minio_path: str
    width: Optional[int] = None
    height: Optional[int] = None

    class Config:
        from_attributes = True

# ── Rule Result ───────────────────────────────────────────────────────

class RuleResultResponse(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    description: Optional[str] = None
    extracted_value: Optional[str] = None
    expected_value: Optional[str] = None
    result: str
    confidence: Optional[float] = None
    evidence: Optional[str] = None
    document_name: Optional[str] = None
    document_id: Optional[str] = None
    page: Optional[int] = None
    bounding_box: Optional[list] = None
    source: Optional[str] = None
    timestamp: Optional[str] = None
    model_version: Optional[str] = None
    rule_version: Optional[str] = None

    class Config:
        from_attributes = True

# ── Bid ───────────────────────────────────────────────────────────────

class BidResponse(BaseModel):
    id: str
    tender_id: str
    bidder_name: str
    gstin: Optional[str] = None
    score: int
    risk: str
    status: str
    failed_rules: int
    review_rules: int
    summary: Optional[str] = None
    reviewer_decision: Optional[str] = None
    reviewer_note: Optional[str] = None
    reviewed_at: Optional[str] = None

    documents: List[DocumentResponse] = []
    rules: List[RuleResultResponse] = []

    class Config:
        from_attributes = True

# ── Tender ────────────────────────────────────────────────────────────

class TenderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=250)
    department: str = Field(min_length=1, max_length=250)
    deadline: str
    budget: str = Field(min_length=1, max_length=100)

    @field_validator("title", "department", "budget", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("deadline")
    @classmethod
    def valid_date(cls, value):
        return date.fromisoformat(value).isoformat()

class BidCreate(BaseModel):
    tender_id: str = Field(min_length=1)
    bidder_name: str = Field(min_length=1, max_length=250)
    gstin: Optional[str] = Field(default=None, max_length=15)

    @field_validator("bidder_name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value

class TenderResponse(BaseModel):
    id: str
    title: str
    department: str
    published: str
    deadline: str
    budget: str
    status: str
    tender_number: Optional[str] = None
    quantity: Optional[str] = None
    delivery_period: Optional[str] = None
    warranty: Optional[str] = None
    emd: Optional[str] = None
    bids: List[BidResponse] = []
    requirements: List["TenderRequirementResponse"] = []
    documents: List[DocumentResponse] = []

    class Config:
        from_attributes = True

# ── Tender Requirement ──────────────────────────────────────────────────

class TenderRequirementSchema(BaseModel):
    rule_id: str
    name: str
    rule_type: str
    field: str
    operator: str
    expected_value: str
    unit: Optional[str] = None
    period: Optional[str] = None
    evidence_type: str
    mandatory: bool = True
    severity: str = "HIGH"
    description: str

class TenderRequirementResponse(TenderRequirementSchema):
    id: str
    tender_id: str
    source_page: Optional[int] = None
    source_text: Optional[str] = None
    confidence: Optional[float] = None
    status: str

    class Config:
        from_attributes = True

# ── Audit ─────────────────────────────────────────────────────────────

class AuditEventResponse(BaseModel):
    id: str
    time: str
    actor: str
    action: str
    document: Optional[str] = None
    rule: Optional[str] = None
    result: Optional[str] = None
    source: Optional[str] = None
    hash: Optional[str] = None

    class Config:
        from_attributes = True

# ── Officer Decision ─────────────────────────────────────────────────

class DecisionRequest(BaseModel):
    decision: Literal["Approve", "Reject", "Request Clarification", "Keep Under Review"]
    note: str = Field(min_length=1, max_length=4000)

    @field_validator("note", mode="before")
    @classmethod
    def strip_note(cls, value):
        return value.strip() if isinstance(value, str) else value
