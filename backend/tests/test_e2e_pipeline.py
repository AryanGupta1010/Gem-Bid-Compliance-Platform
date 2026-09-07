import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models import (
    User, UserRole, Tender, TenderVersion, Requirement, Bidder, Bid,
    Document, DocumentVersion, RuleType, Operator, Severity, BidStatus, generate_uuid
)
from app.utils.hashing import compute_sha3_512
from app.workers.pipeline import run_bid_evaluation_pipeline

def test_end_to_end_pipeline():
    # In-memory SQLite engine for fast reproducible unit test
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()

    # 1. Create Officer
    user = User(
        id=generate_uuid(),
        email="test_officer@gem.gov.in",
        full_name="Test Officer",
        hashed_password="hash",
        role=UserRole.PROCUREMENT_OFFICER
    )
    db.add(user)

    # 2. Create Tender
    tender = Tender(
        id=generate_uuid(),
        tender_number="TEST/TENDER/01",
        title="Test Laptop Procurement",
        procuring_organization="Test Org",
        status="ACTIVE"
    )
    db.add(tender)
    db.commit()

    # 3. Create Requirements
    req1 = Requirement(
        id=generate_uuid(),
        tender_id=tender.id,
        name="Turnover",
        rule_type=RuleType.NUMERIC,
        operator=Operator.GTE,
        expected_value="10",
        unit="Cr",
        evidence_type="turnover",
        severity=Severity.HIGH,
        mandatory=True,
        weight=20.0
    )
    req2 = Requirement(
        id=generate_uuid(),
        tender_id=tender.id,
        name="GST Validity",
        rule_type=RuleType.VERIFICATION,
        operator=Operator.EQ,
        expected_value="VALID",
        evidence_type="GST",
        severity=Severity.HIGH,
        mandatory=True,
        weight=20.0
    )
    db.add_all([req1, req2])
    db.commit()

    # 4. Create Bidder & Bid
    bidder = Bidder(
        id=generate_uuid(),
        name="Test Bidder Alpha",
        registration_number="ALPHA_001",
        gstin="07AAAAA0000A1Z5",
        contact_email="alpha@test.com"
    )
    db.add(bidder)
    db.commit()

    bid = Bid(
        id=generate_uuid(),
        tender_id=tender.id,
        bidder_id=bidder.id,
        bid_number="BID-TEST-001",
        status=BidStatus.SUBMITTED
    )
    db.add(bid)
    db.commit()

    # 5. Attach Document with metadata
    doc_bytes = b"Sample audited financial statement"
    doc_hash = compute_sha3_512(doc_bytes)
    doc = Document(
        id=generate_uuid(),
        bid_id=bid.id,
        document_type="FINANCIAL",
        filename="Turnover_FY24.pdf",
        file_path="mock/path.pdf",
        file_size=len(doc_bytes),
        document_hash=doc_hash,
        metadata_json={"turnover": 12.0}
    )
    db.add(doc)
    db.commit()

    # 6. Run full evaluation pipeline
    result = run_bid_evaluation_pipeline(db, bid.id, user.id)

    assert result["status"] == "COMPLETED"
    assert result["score"] == 100.0
    assert result["risk_level"] == "LOW"
    assert result["recommendation"] == "PASS"

    db.close()
