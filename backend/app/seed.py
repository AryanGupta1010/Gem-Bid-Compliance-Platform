import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.core.security import get_password_hash
from app.models import (
    User, UserRole, Tender, TenderVersion, TenderStatus, Requirement,
    RuleType, Operator, Severity, Bidder, Bid, Document, DocumentVersion,
    BidStatus, generate_uuid, utc_now
)
from app.utils.hashing import compute_sha3_512
from app.workers.pipeline import run_bid_evaluation_pipeline
from app.audit.service import audit_service
from app.storage import storage_service

def seed_database():
    print("Initializing GeM Compliance Database Schema...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Procurement Officer User
        officer = db.query(User).filter(User.email == "officer@gem.gov.in").first()
        if not officer:
            officer = User(
                id=generate_uuid(),
                email="officer@gem.gov.in",
                full_name="Col. Rajesh Verma (Retd.)",
                hashed_password=get_password_hash("officer123"),
                role=UserRole.PROCUREMENT_OFFICER,
                department="Directorate General of Supplies & Disposals (GeM)",
                is_active=True
            )
            db.add(officer)
            db.commit()
            print("Created Officer user: officer@gem.gov.in / officer123")

        # 2. Seed Tender: "Supply of 100 Enterprise Laptops"
        tender_number = "GEM/2026/B/89410"
        tender = db.query(Tender).filter(Tender.tender_number == tender_number).first()
        if not tender:
            tender = Tender(
                id=generate_uuid(),
                tender_number=tender_number,
                title="Procurement of 100 Enterprise Laptops for Ministry of Electronics & IT (MeitY)",
                description="High-performance laptops conforming to BIS safety standards with 3-year onsite OEM warranty and Class-I Local Content requirement under Make in India policy.",
                procuring_organization="Ministry of Electronics & Information Technology (MeitY)",
                status=TenderStatus.UNDER_EVALUATION,
                estimated_value=8500000.0,
                currency="INR"
            )
            db.add(tender)
            db.commit()

            # Tender Version 1
            version = TenderVersion(
                id=generate_uuid(),
                tender_id=tender.id,
                version_number=1,
                change_summary="Original RFP Published on GeM 4.0 Portal"
            )
            db.add(version)
            db.commit()

            # 3. Seed 7 Deterministic Requirements
            requirements_data = [
                {
                    "name": "Minimum Average Annual Turnover",
                    "description": "Bidder must have minimum average annual financial turnover of ₹10.00 Crore in the last 3 audited financial years.",
                    "rule_type": RuleType.NUMERIC,
                    "operator": Operator.GTE,
                    "expected_value": "10",
                    "unit": "Cr",
                    "evidence_type": "turnover",
                    "severity": Severity.HIGH,
                    "mandatory": True,
                    "weight": 20.0,
                    "display_order": 1
                },
                {
                    "name": "GSTIN Registration & Filing Validity",
                    "description": "Bidder must possess active and compliant GSTIN registered in India with up-to-date return filings.",
                    "rule_type": RuleType.VERIFICATION,
                    "operator": Operator.EQ,
                    "expected_value": "VALID",
                    "unit": None,
                    "evidence_type": "GST",
                    "severity": Severity.HIGH,
                    "mandatory": True,
                    "weight": 20.0,
                    "display_order": 2
                },
                {
                    "name": "MSME / Udyam Enterprise Verification",
                    "description": "Verified Udyam registration for MSME purchase preference eligibility as per Public Procurement Policy.",
                    "rule_type": RuleType.VERIFICATION,
                    "operator": Operator.EQ,
                    "expected_value": "VALID",
                    "unit": None,
                    "evidence_type": "Udyam",
                    "severity": Severity.MEDIUM,
                    "mandatory": False,
                    "weight": 10.0,
                    "display_order": 3
                },
                {
                    "name": "Make in India Class-I Local Content",
                    "description": "Bidder must offer minimum 50% local value addition in accordance with DPIIT Order P-45021/2/2017-PP (BE-II).",
                    "rule_type": RuleType.NUMERIC,
                    "operator": Operator.GTE,
                    "expected_value": "50",
                    "unit": "%",
                    "evidence_type": "local_content",
                    "severity": Severity.HIGH,
                    "mandatory": True,
                    "weight": 20.0,
                    "display_order": 4
                },
                {
                    "name": "OEM Manufacturer Authorization (MAF)",
                    "description": "Mandatory manufacturer authorization form from OEM guaranteeing genuine hardware supply and direct SLA warranty.",
                    "rule_type": RuleType.DOCUMENT_PRESENT,
                    "operator": Operator.EXISTS,
                    "expected_value": "OEM_AUTH",
                    "unit": None,
                    "evidence_type": "OEM_AUTH",
                    "severity": Severity.HIGH,
                    "mandatory": True,
                    "weight": 15.0,
                    "display_order": 5
                },
                {
                    "name": "Central Debarment / Blacklist Check",
                    "description": "Bidder must not be debarred, blacklisted, or suspended by GeM, CPPP, or any Central/State Ministry.",
                    "rule_type": RuleType.VERIFICATION,
                    "operator": Operator.EQ,
                    "expected_value": "VALID",
                    "unit": None,
                    "evidence_type": "Debarment",
                    "severity": Severity.CRITICAL,
                    "mandatory": True,
                    "weight": 30.0,
                    "display_order": 6
                },
                {
                    "name": "Audited Financial Statement Completeness",
                    "description": "Submission of complete audited balance sheet & profit/loss statements certified by practicing Chartered Accountant.",
                    "rule_type": RuleType.DOCUMENT_PRESENT,
                    "operator": Operator.EXISTS,
                    "expected_value": "FINANCIAL",
                    "unit": None,
                    "evidence_type": "FINANCIAL",
                    "severity": Severity.MEDIUM,
                    "mandatory": True,
                    "weight": 10.0,
                    "display_order": 7
                },
            ]

            for req_d in requirements_data:
                r = Requirement(
                    id=generate_uuid(),
                    tender_id=tender.id,
                    tender_version_id=version.id,
                    **req_d
                )
                db.add(r)
            db.commit()
            print("Created Tender & 7 Deterministic Requirements")

        # 4. Seed the 3 Benchmark Bidders
        bidders_data = [
            # BIDDER A: Fully Compliant (PASS / LOW RISK)
            {
                "name": "Alpha Technologies India Pvt Ltd",
                "registration_number": "ALPHA_TECH_001",
                "gstin": "07AAAAA0000A1Z5",
                "pan": "AAAAA0000A",
                "udyam_number": "UDYAM-DL-01-008912",
                "contact_email": "bids@alphatechindia.com",
                "contact_phone": "+91-11-23456789",
                "is_msme": True,
                "bid_number": "BID/2026/001-ALPHA",
                "bid_amount": 8250000.0,
                "docs": [
                    {
                        "type": "FINANCIAL",
                        "filename": "Alpha_Audited_Turnover_FY23_24.pdf",
                        "metadata": {"turnover": 12.5, "turnover_page": 4, "turnover_box": [0.12, 0.40, 0.88, 0.52]}
                    },
                    {
                        "type": "OEM_AUTH",
                        "filename": "Alpha_Dell_OEM_MAF_Authorization.pdf",
                        "metadata": {"oem_authorization": "VALID", "oem_name": "Dell Technologies India"}
                    },
                    {
                        "type": "LOCAL_CONTENT",
                        "filename": "Alpha_MakeInIndia_Local_Content_65pct.pdf",
                        "metadata": {"local_content_percentage": 65.0, "lc_page": 1, "lc_box": [0.10, 0.25, 0.90, 0.40]}
                    },
                    {
                        "type": "GST",
                        "filename": "Alpha_GST_Registration_Certificate.pdf",
                        "metadata": {"gstin": "07AAAAA0000A1Z5"}
                    }
                ]
            },
            # BIDDER B: Turnover Threshold Failure (FAIL / HIGH RISK)
            {
                "name": "Beta Infotech Solutions LLP",
                "registration_number": "BETA_INFO_002",
                "gstin": "27BBBBB1111B2Z8",
                "pan": "BBBBB1111B",
                "udyam_number": "UDYAM-MH-02-004521",
                "contact_email": "tenders@betainfotech.in",
                "contact_phone": "+91-22-98765432",
                "is_msme": True,
                "bid_number": "BID/2026/002-BETA",
                "bid_amount": 7900000.0,
                "docs": [
                    {
                        "type": "FINANCIAL",
                        "filename": "Beta_CA_Turnover_Statement_FY24.pdf",
                        "metadata": {"turnover": 7.2, "turnover_page": 3, "turnover_box": [0.15, 0.48, 0.85, 0.60]} # 7.2 Cr < 10 Cr!
                    },
                    {
                        "type": "OEM_AUTH",
                        "filename": "Beta_HP_Manufacturer_Authorization.pdf",
                        "metadata": {"oem_authorization": "VALID", "oem_name": "HP Enterprise India"}
                    },
                    {
                        "type": "LOCAL_CONTENT",
                        "filename": "Beta_MII_Class1_Declaration_55pct.pdf",
                        "metadata": {"local_content_percentage": 55.0, "lc_page": 1, "lc_box": [0.10, 0.30, 0.90, 0.45]}
                    }
                ]
            },
            # BIDDER C: Unavailable GST & Missing OEM (REVIEW / MEDIUM-HIGH RISK)
            {
                "name": "Gamma Global Electronics & Systems",
                "registration_number": "GAMMA_ELEC_003",
                "gstin": "GST123DOWN", # Triggers UNAVAILABLE status in adapter
                "pan": "CCCCC2222C",
                "udyam_number": None,
                "contact_email": "contact@gammaglobal.org",
                "contact_phone": "+91-80-45678901",
                "is_msme": False,
                "bid_number": "BID/2026/003-GAMMA",
                "bid_amount": 8100000.0,
                "docs": [
                    {
                        "type": "FINANCIAL",
                        "filename": "Gamma_Audited_Accounts_FY24.pdf",
                        "metadata": {"turnover": 14.0, "turnover_page": 2, "turnover_box": [0.10, 0.35, 0.90, 0.50]}
                    },
                    {
                        "type": "LOCAL_CONTENT",
                        "filename": "Gamma_Local_Content_Self_Affidavit.pdf",
                        "metadata": {"local_content_percentage": 52.0, "lc_page": 1, "lc_box": [0.10, 0.25, 0.90, 0.40]}
                    }
                    # Missing OEM Auth Document!
                ]
            }
        ]

        dummy_pdf_bytes = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"

        for b_data in bidders_data:
            bidder = db.query(Bidder).filter(Bidder.registration_number == b_data["registration_number"]).first()
            if not bidder:
                bidder = Bidder(
                    id=generate_uuid(),
                    name=b_data["name"],
                    registration_number=b_data["registration_number"],
                    gstin=b_data["gstin"],
                    pan=b_data["pan"],
                    udyam_number=b_data["udyam_number"],
                    contact_email=b_data["contact_email"],
                    contact_phone=b_data["contact_phone"],
                    is_msme=b_data["is_msme"]
                )
                db.add(bidder)
                db.commit()

            bid = db.query(Bid).filter(Bid.bid_number == b_data["bid_number"]).first()
            if not bid:
                bid = Bid(
                    id=generate_uuid(),
                    tender_id=tender.id,
                    bidder_id=bidder.id,
                    bid_number=b_data["bid_number"],
                    bid_amount=b_data["bid_amount"],
                    status=BidStatus.SUBMITTED
                )
                db.add(bid)
                db.commit()

                # Upload docs
                for d_info in b_data["docs"]:
                    doc_hash = compute_sha3_512(dummy_pdf_bytes)
                    storage_path = f"bids/{bid.id}/{doc_hash[:16]}_{d_info['filename']}"
                    storage_service.save_file(dummy_pdf_bytes, storage_path)

                    doc = Document(
                        id=generate_uuid(),
                        bid_id=bid.id,
                        document_type=d_info["type"],
                        filename=d_info["filename"],
                        file_path=storage_path,
                        mime_type="application/pdf",
                        file_size=len(dummy_pdf_bytes),
                        document_hash=doc_hash,
                        page_count=4,
                        metadata_json=d_info["metadata"],
                        uploaded_by_id=officer.id
                    )
                    db.add(doc)
                    db.commit()

                    doc_v = DocumentVersion(
                        id=generate_uuid(),
                        document_id=doc.id,
                        version_number=1,
                        document_hash=doc_hash,
                        file_path=storage_path
                    )
                    db.add(doc_v)
                    db.commit()

                # Run evaluation pipeline for the bid
                eval_res = run_bid_evaluation_pipeline(db, bid.id, officer.id)
                print(f"Evaluated Bid '{bid.bid_number}' ({bidder.name}): Score={eval_res['score']}%, Risk={eval_res['risk_level']}, Rec={eval_res['recommendation']}")

        audit_service.record_event(
            db=db,
            action="DEMO_DATABASE_SEEDED",
            entity_type="System",
            entity_id="GLOBAL",
            user_id=officer.id,
            metadata_json={"tender": tender_number, "bidders_seeded": 3}
        )

        print("\nDemo Seed Completed Successfully!")
        print(f"Tender ID: {tender.id} ({tender.tender_number})")
        print("Officer Credentials: officer@gem.gov.in / officer123")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
