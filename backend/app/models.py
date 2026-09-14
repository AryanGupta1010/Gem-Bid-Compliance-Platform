from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, Text, JSON, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Tender(Base):
    __tablename__ = "tenders"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    department = Column(String, nullable=False)
    published = Column(String)
    deadline = Column(String)
    budget = Column(String)
    status = Column(String)
    bids = relationship("Bid", back_populates="tender")

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
    bid_id = Column(String, ForeignKey("bids.id"))
    filename = Column(String, nullable=False)
    mime_type = Column(String, default="application/pdf")
    size_bytes = Column(BigInteger, default=0)
    hash_sha3_512 = Column(String, nullable=False)
    minio_path = Column(String, nullable=False)
    status = Column(String, default="uploaded")           # uploaded / processing / completed / error
    processing_stage = Column(String, default="UPLOAD")   # current pipeline stage
    page_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    bid = relationship("Bid", back_populates="documents")
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
