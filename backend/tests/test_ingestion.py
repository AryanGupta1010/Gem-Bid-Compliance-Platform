import pytest
import io
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import Bid, Document

client = TestClient(app)

def test_ingestion_upload():
    # Find a test bid
    db = SessionLocal()
    bid = db.query(Bid).first()
    db.close()
    assert bid is not None, "Need at least one bid to test upload"

    # Create a dummy PDF file
    file_content = b"%PDF-1.4\nTest PDF content\n%%EOF"
    file_like = io.BytesIO(file_content)
    
    response = client.post(
        f"/upload/{bid.id}",
        files={"file": ("test_doc.pdf", file_like, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_doc.pdf"
    assert data["status"].upper() == "UPLOADED"
    assert "hash_sha3_512" in data
    assert data["hash_sha3_512"] is not None

    # Verify it exists in db
    db = SessionLocal()
    doc = db.query(Document).filter(Document.id == data["id"]).first()
    assert doc is not None
    assert doc.hash_sha3_512 == data["hash_sha3_512"]
    assert doc.minio_path is not None
    db.close()
