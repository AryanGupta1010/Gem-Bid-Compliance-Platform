from app.database import SessionLocal, engine, Base
from app import models

def seed_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Create Tender
    tender = db.query(models.Tender).filter(models.Tender.id == "tnd-2024-8891").first()
    if not tender:
        tender = models.Tender(
            id="tnd-2024-8891",
            title="Procurement of IT Infrastructure for SIH 2026",
            department="Ministry of Education",
            published="2024-09-01",
            deadline="2024-10-15",
            budget="₹15,00,00,000",
            status="active"
        )
        db.add(tender)
        db.flush()

    # Three golden-demo bidders — start in REVIEW with no scores if new,
    # or just update names if they exist so we don't wipe out their rules/documents.
    bidders = [
        {
            "id": "bid-001",
            "name": "TechNova Systems Pvt. Ltd.",
            "gstin": "27AADCB2230M1Z2",
            "summary": "Awaiting document upload and automated compliance evaluation.",
            "status": "PASS",
            "risk": "LOW",
            "score": 95
        },
        {
            "id": "bid-002",
            "name": "Apex Industrial Solutions Pvt. Ltd.",
            "gstin": "07BBPCA1120K1Z1",
            "summary": "Awaiting document upload and automated compliance evaluation.",
            "status": "FAIL",
            "risk": "HIGH",
            "score": 30
        },
        {
            "id": "bid-003",
            "name": "MedCore Technologies Pvt. Ltd.",
            "gstin": "29CCPMD3340L1Z3",
            "summary": "Awaiting document upload and automated compliance evaluation.",
            "status": "REVIEW",
            "risk": "MEDIUM",
            "score": 65
        }
    ]

    for b in bidders:
        bid = db.query(models.Bid).filter(models.Bid.id == b["id"]).first()
        if not bid:
            bid = models.Bid(
                id=b["id"],
                tender_id="tnd-2024-8891",
                bidder_name=b["name"],
                gstin=b["gstin"],
                score=b["score"],
                risk=b["risk"],
                status=b["status"],
                failed_rules=0,
                review_rules=0,
                summary="DEMO preset only — upload the Golden Demo PDF to produce evidence-backed rule results."
            )
            db.add(bid)
        else:
            bid.bidder_name = b["name"]
            # Never overwrite evaluated outcomes or officer decisions on reseed.

    db.commit()
    db.close()
    print("Database seeded successfully with idempotent golden cases.")

if __name__ == "__main__":
    seed_db()
