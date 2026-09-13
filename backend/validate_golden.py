import asyncio
from app.database import SessionLocal
from app.engine import DeterministicEngine
from app import models
from app.services.ocr import DemoOCR
import hashlib

def run_validation():
    db = SessionLocal()
    try:
        engine = DeterministicEngine(db)
        
        # We need a dummy document to pass into evaluate_document_evidence
        # TechNova
        doc1 = models.Document(
            bid_id="bid-001",
            filename="technova_doc.pdf",
            mime_type="application/pdf",
            size_bytes=1000,
            hash_sha3_512="fakehash1",
            minio_path="dummy",
            status="completed",
            processing_stage="RENDER"
        )
        # Apex
        doc2 = models.Document(
            bid_id="bid-002",
            filename="apex_doc.pdf",
            mime_type="application/pdf",
            size_bytes=1000,
            hash_sha3_512="fakehash2",
            minio_path="dummy",
            status="completed",
            processing_stage="RENDER"
        )
        # MedCore
        doc3 = models.Document(
            bid_id="bid-003",
            filename="medcore_doc.pdf",
            mime_type="application/pdf",
            size_bytes=1000,
            hash_sha3_512="fakehash3",
            minio_path="dummy",
            status="completed",
            processing_stage="RENDER"
        )
        db.add_all([doc1, doc2, doc3])
        db.commit()

        # TechNova verification
        updated_bid1 = engine.evaluate_document_evidence(doc1.id)
        print(f"TechNova (bid-001) Status: {updated_bid1.status}, Score: {updated_bid1.score}")
        
        # Apex verification
        updated_bid2 = engine.evaluate_document_evidence(doc2.id)
        print(f"Apex (bid-002) Status: {updated_bid2.status}, Score: {updated_bid2.score}")
        
        # MedCore verification
        updated_bid3 = engine.evaluate_document_evidence(doc3.id)
        print(f"MedCore (bid-003) Status: {updated_bid3.status}, Score: {updated_bid3.score}")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_validation()
