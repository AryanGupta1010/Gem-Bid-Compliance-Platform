from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, JSON, BigInteger, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, default="")
    role = Column(String, default="PROCUREMENT_OFFICER")  # PROCUREMENT_OFFICER, ADMIN, REVIEWER, AUDITOR
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    published = Column(String)
    deadline = Column(String)
    budget = Column(String)
    status = Column(String)
    
    # Dynamically Extracted Details
    tender_number = Column(String, nullable=True)
    quantity = Column(String, nullable=True)
    delivery_period = Column(String, nullable=True)
    warranty = Column(String, nullable=True)
    emd = Column(String, nullable=True)
    
    bids = relationship("Bid", back_populates="tender")
    requirements = relationship("TenderRequirement", back_populates="tender", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tender", order_by="Document.uploaded_at.desc()")

class Bid(Base):
    __tablename__ = "bids"

    id = Column(String, primary_key=True)
    tender_id = Column(String, ForeignKey("tenders.id"))
    bidder_name = Column(String, nullable=False)
    gstin = Column(String)
    score = Column(Integer, default=0)
    risk = Column(String, default="LOW")
    status = Column(String, default="REVIEW")
    failed_rules = Column(Integer, default=0)
    review_rules = Column(Integer, default=0)
    summary = Column(Text)

    # Officer decision fields
    reviewer_decision = Column(String)   # Approve / Reject / Request Clarification / Keep Under Review
    reviewer_note = Column(Text)
    reviewed_at = Column(String)

    tender = relationship("Tender", back_populates="bids")
    documents = relationship("Document", back_populates="bid", order_by="Document.uploaded_at.desc()")
    rules = relationship("RuleResult", back_populates="bid", order_by="RuleResult.rule_id")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, ForeignKey("bids.id"), nullable=True)
    tender_id = Column(String, ForeignKey("tenders.id"), nullable=True)
    filename = Column(String, nullable=False)
    mime_type = Column(String, default="application/pdf")
    size_bytes = Column(BigInteger, default=0)
    hash_sha3_512 = Column(String, nullable=False)
    minio_path = Column(String, nullable=False)
    status = Column(String, default="uploaded")           # uploaded / processing / completed / error
    processing_stage = Column(String, default="UPLOAD")   # UPLOAD / HASH / RENDER / INDEX / EVALUATE / HUMAN_REVIEW / FAILED
    page_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    bid = relationship("Bid", back_populates="documents")
    tender = relationship("Tender", back_populates="documents")
    pages = relationship("PageImage", back_populates="document")

class PageImage(Base):
    __tablename__ = "page_images"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"))
    page_number = Column(Integer, nullable=False)
    minio_path = Column(String, nullable=False)
    width = Column(Integer)
    height = Column(Integer)

    document = relationship("Document", back_populates="pages")

class RuleResult(Base):
    __tablename__ = "rule_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    bid_id = Column(String, ForeignKey("bids.id"))
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    rule_id = Column(String, nullable=False)
    rule_name = Column(String, nullable=False)
    description = Column(String)
    extracted_value = Column(String)
    expected_value = Column(String)
    result = Column(String, nullable=False)  # PASS, FAIL, REVIEW
    confidence = Column(Float)
    evidence = Column(String)
    document_name = Column(String)
    page = Column(Integer)
    bounding_box = Column(JSON)   # [x1, y1, x2, y2]
    source = Column(String)
    timestamp = Column(String)
    model_version = Column(String)
    rule_version = Column(String)

    bid = relationship("Bid", back_populates="rules")

class TenderRequirement(Base):
    __tablename__ = "tender_requirements"

    id = Column(String, primary_key=True, default=generate_uuid)
    tender_id = Column(String, ForeignKey("tenders.id"))
    rule_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    rule_type = Column(String)
    field = Column(String)
    operator = Column(String)
    expected_value = Column(String)
    unit = Column(String)
    period = Column(String)
    evidence_type = Column(String)
    mandatory = Column(Boolean, default=True)
    severity = Column(String)
    description = Column(String)
    source_page = Column(Integer)
    source_text = Column(String)
    confidence = Column(Float)
    status = Column(String, default="pending")  # pending / approved / rejected

    tender = relationship("Tender", back_populates="requirements")

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    time = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    document = Column(String)
    rule = Column(String)
    result = Column(String)
    source = Column(String)
    hash = Column(String)
