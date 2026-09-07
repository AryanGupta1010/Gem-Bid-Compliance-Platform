import enum
from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

# Enums
class UserRole(str, enum.Enum):
    PROCUREMENT_OFFICER = "PROCUREMENT_OFFICER"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"

class TenderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    UNDER_EVALUATION = "UNDER_EVALUATION"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"

class RuleType(str, enum.Enum):
    NUMERIC = "NUMERIC"
    DATE = "DATE"
    BOOLEAN = "BOOLEAN"
    STATUS = "STATUS"
    TEXT_MATCH = "TEXT_MATCH"
    DOCUMENT_PRESENT = "DOCUMENT_PRESENT"
    DOCUMENT_EXPIRY = "DOCUMENT_EXPIRY"
    VERIFICATION = "VERIFICATION"
    MANUAL_REVIEW = "MANUAL_REVIEW"

class Operator(str, enum.Enum):
    EQ = "EQ"
    NEQ = "NEQ"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
    EXISTS = "EXISTS"
    NOT_EXISTS = "NOT_EXISTS"
    IN = "IN"
    NOT_IN = "NOT_IN"
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    CONTAINS = "CONTAINS"

class Severity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class RuleStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW = "REVIEW"
    UNAVAILABLE = "UNAVAILABLE"

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class VerificationStatus(str, enum.Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"
    NOT_FOUND = "NOT_FOUND"
    UNAVAILABLE = "UNAVAILABLE"

class OfficerDecisionType(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"

class BidStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    EVALUATING = "EVALUATING"
    EVALUATED = "EVALUATED"
    REVIEWED = "REVIEWED"

# 1. User
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PROCUREMENT_OFFICER, nullable=False)
    department = Column(String(255), default="Procurement Division")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    audit_events = relationship("AuditEvent", back_populates="user")
    reviews = relationship("ReviewDecision", back_populates="officer")

# 2. Tender
class Tender(Base):
    __tablename__ = "tenders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tender_number = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    procuring_organization = Column(String(255), nullable=False)
    status = Column(Enum(TenderStatus), default=TenderStatus.ACTIVE, nullable=False)
    estimated_value = Column(Float, nullable=True)
    currency = Column(String(10), default="INR")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    versions = relationship("TenderVersion", back_populates="tender", cascade="all, delete-orphan")
    bids = relationship("Bid", back_populates="tender", cascade="all, delete-orphan")
    requirements = relationship("Requirement", back_populates="tender", cascade="all, delete-orphan")

# 3. TenderVersion
class TenderVersion(Base):
    __tablename__ = "tender_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tender_id = Column(String(36), ForeignKey("tenders.id"), nullable=False)
    version_number = Column(Integer, default=1, nullable=False)
    source_document_id = Column(String(36), nullable=True)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    tender = relationship("Tender", back_populates="versions")
    requirements = relationship("Requirement", back_populates="tender_version")

# 4. Requirement
class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tender_id = Column(String(36), ForeignKey("tenders.id"), nullable=False)
    tender_version_id = Column(String(36), ForeignKey("tender_versions.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(Enum(RuleType), nullable=False)
    operator = Column(Enum(Operator), nullable=False)
    expected_value = Column(String(255), nullable=False)
    unit = Column(String(50), nullable=True)
    evidence_type = Column(String(100), nullable=True) # e.g. "financial_statement", "gst_certificate"
    severity = Column(Enum(Severity), default=Severity.HIGH, nullable=False)
    mandatory = Column(Boolean, default=True)
    enabled = Column(Boolean, default=True)
    weight = Column(Float, default=20.0)
    exception_logic = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=utc_now)

    tender = relationship("Tender", back_populates="requirements")
    tender_version = relationship("TenderVersion", back_populates="requirements")
    rule_results = relationship("RuleResult", back_populates="requirement", cascade="all, delete-orphan")

# 5. Bidder
class Bidder(Base):
    __tablename__ = "bidders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(100), unique=True, index=True, nullable=False)
    gstin = Column(String(50), nullable=True)
    pan = Column(String(20), nullable=True)
    udyam_number = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=True)
    is_msme = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    bids = relationship("Bid", back_populates="bidder", cascade="all, delete-orphan")

# 6. Bid
class Bid(Base):
    __tablename__ = "bids"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tender_id = Column(String(36), ForeignKey("tenders.id"), nullable=False)
    bidder_id = Column(String(36), ForeignKey("bidders.id"), nullable=False)
    bid_number = Column(String(100), unique=True, index=True, nullable=False)
    bid_amount = Column(Float, nullable=True)
    status = Column(Enum(BidStatus), default=BidStatus.SUBMITTED, nullable=False)
    submitted_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    tender = relationship("Tender", back_populates="bids")
    bidder = relationship("Bidder", back_populates="bids")
    documents = relationship("Document", back_populates="bid", cascade="all, delete-orphan")
    rule_results = relationship("RuleResult", back_populates="bid", cascade="all, delete-orphan")
    compliance_assessment = relationship("ComplianceAssessment", back_populates="bid", uselist=False, cascade="all, delete-orphan")
    review_decisions = relationship("ReviewDecision", back_populates="bid", cascade="all, delete-orphan")
    verification_requests = relationship("VerificationRequest", back_populates="bid", cascade="all, delete-orphan")

# 7. Document
class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    bid_id = Column(String(36), ForeignKey("bids.id"), nullable=False)
    document_type = Column(String(100), nullable=False) # e.g. "FINANCIAL", "GST", "MSME", "OEM_AUTH", "LOCAL_CONTENT", "DEBARMENT_DECLARATION"
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), default="application/pdf")
    file_size = Column(Integer, nullable=False)
    document_hash = Column(String(128), nullable=False) # SHA-3-512
    page_count = Column(Integer, default=1)
    metadata_json = Column(JSON, nullable=True)
    uploaded_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    uploaded_at = Column(DateTime, default=utc_now)

    bid = relationship("Bid", back_populates="documents")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    evidences = relationship("Evidence", back_populates="document", cascade="all, delete-orphan")

# 8. DocumentVersion
class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, default=1, nullable=False)
    document_hash = Column(String(128), nullable=False)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    document = relationship("Document", back_populates="versions")

# 9. Evidence
class Evidence(Base):
    __tablename__ = "evidences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    rule_result_id = Column(String(36), ForeignKey("rule_results.id"), nullable=True)
    page_number = Column(Integer, default=1)
    bounding_box = Column(JSON, nullable=True) # [x1, y1, x2, y2]
    extracted_field = Column(String(100), nullable=False)
    extracted_value = Column(String(500), nullable=False)
    confidence = Column(Float, default=1.0)
    source = Column(String(255), default="Registered bidder document")
    created_at = Column(DateTime, default=utc_now)

    document = relationship("Document", back_populates="evidences")
    rule_result = relationship("RuleResult", back_populates="evidences")

# 10. VerificationRequest
class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    bid_id = Column(String(36), ForeignKey("bids.id"), nullable=False)
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=True)
    source = Column(String(50), nullable=False) # GST, Udyam, UDIN, BIS, Debarment
    request_identifier = Column(String(255), nullable=False)
    request_payload = Column(JSON, nullable=True)
    requested_at = Column(DateTime, default=utc_now)

    bid = relationship("Bid", back_populates="verification_requests")
    results = relationship("VerificationResult", back_populates="request", cascade="all, delete-orphan")

# 11. VerificationResult
class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    verification_request_id = Column(String(36), ForeignKey("verification_requests.id"), nullable=True)
    bid_id = Column(String(36), ForeignKey("bids.id"), nullable=False)
    source = Column(String(50), nullable=False)
    request_identifier = Column(String(255), nullable=False)
    status = Column(Enum(VerificationStatus), nullable=False)
    response_data = Column(JSON, nullable=True)
    verified_at = Column(DateTime, default=utc_now)
    adapter_version = Column(String(50), default="1.0.0")
    success = Column(Boolean, default=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)

    request = relationship("VerificationRequest", back_populates="results")
    rule_results = relationship("RuleResult", back_populates="verification_result")

# 12. RuleResult
class RuleResult(Base):
    __tablename__ = "rule_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    bid_id = Column(String(36), ForeignKey("bids.id"), nullable=False)
    requirement_id = Column(String(36), ForeignKey("requirements.id"), nullable=False)
    compliance_assessment_id = Column(String(36), ForeignKey("compliance_assessments.id"), nullable=True)
    verification_result_id = Column(String(36), ForeignKey("verification_results.id"), nullable=True)
    status = Column(Enum(RuleStatus), nullable=False)
    actual_value = Column(String(500), nullable=True)
    expected_value = Column(String(500), nullable=True)
    explanation = Column(Text, nullable=False)
    severity = Column(Enum(Severity), default=Severity.HIGH, nullable=False)
    weight = Column(Float, default=20.0)
    confidence = Column(Float, default=1.0)
    rule_version = Column(String(50), default="1.0.0")
    evaluated_at = Column(DateTime, default=utc_now)

    bid = relationship("Bid", back_populates="rule_results")
    requirement = relationship("Requirement", back_populates="rule_results")
    compliance_assessment = relationship("ComplianceAssessment", back_populates="rule_results")
    verification_result = relationship("VerificationResult", back_populates="rule_results")
    evidences = relationship("Evidence", back_populates="rule_result", cascade="all, delete-orphan")

# 13. ComplianceAssessment
class ComplianceAssessment(Base):
    __tablename__ = "compliance_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    bid_id = Column(String(36), ForeignKey("bids.id"), unique=True, nullable=False)
    compliance_score = Column(Float, default=0.0)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM, nullable=False)
    recommendation = Column(Enum(RuleStatus), default=RuleStatus.REVIEW, nullable=False)
    total_weight = Column(Float, default=0.0)
    passed_weight = Column(Float, default=0.0)
    failed_weight = Column(Float, default=0.0)
    review_weight = Column(Float, default=0.0)
    summary_metrics = Column(JSON, nullable=True)
    evaluated_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)

    bid = relationship("Bid", back_populates="compliance_assessment")
    rule_results = relationship("RuleResult", back_populates="compliance_assessment")

# 14. ReviewDecision
class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    bid_id = Column(String(36), ForeignKey("bids.id"), nullable=False)
    officer_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    decision = Column(Enum(OfficerDecisionType), nullable=False)
    officer_notes = Column(Text, nullable=False)
    reviewed_at = Column(DateTime, default=utc_now)
    created_at = Column(DateTime, default=utc_now)

    bid = relationship("Bid", back_populates="review_decisions")
    officer = relationship("User", back_populates="reviews")

# 15. AuditEvent
class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, default=utc_now, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)
    request_id = Column(String(100), nullable=True)
    metadata_json = Column(JSON, nullable=True)

    user = relationship("User", back_populates="audit_events")
