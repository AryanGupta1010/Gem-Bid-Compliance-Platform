import pytest
import io
from fastapi.testclient import TestClient
from app.models import Document

def test_ingestion_upload(workspace, bidder, valid_pdf):
    client, sessions, jobs, objects = workspace
    bid_id = bidder["id"]
    
    file_like = io.BytesIO(valid_pdf)
    
    response = client.post(
        f"/upload/{bid_id}",
        files={"file": ("test_doc.pdf", file_like, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_doc.pdf"
    assert data["status"].upper() == "UPLOADED"
    assert "hash_sha3_512" in data
    assert data["hash_sha3_512"] is not None

    # Verify it exists in db
    with sessions() as db:
        doc = db.query(Document).filter(Document.id == data["id"]).first()
        assert doc is not None
        assert doc.hash_sha3_512 == data["hash_sha3_512"]
        assert doc.minio_path is not None
