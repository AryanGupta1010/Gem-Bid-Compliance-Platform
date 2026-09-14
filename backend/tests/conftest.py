import os
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["AI_MODE"] = "demo"

import pytest
import pymupdf
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app import main, models, tasks
from app.database import Base, get_db
from app.services import retriever

@pytest.fixture
def workspace(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)
    def get_test_db():
        with sessions() as db:
            yield db
    main.app.dependency_overrides[get_db] = get_test_db
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(tasks, "SessionLocal", sessions)
    monkeypatch.setattr(retriever, "SessionLocal", sessions)
    objects = {}
    jobs = []
    def upload(file, key, bucket=None):
        path = f"{bucket or 'documents'}/{key}"
        objects[path] = file.read()
        return path
    monkeypatch.setattr(main.minio_client, "upload_fileobj", upload)
    monkeypatch.setattr(main.minio_client, "download_file_bytes", lambda path, bucket=None: objects[path])
    monkeypatch.setattr(main.redis_conn, "ping", lambda: True)
    monkeypatch.setattr(main.task_queue, "enqueue", lambda function, doc_id, **kwargs: jobs.append(doc_id))
    with TestClient(main.app) as client:
        yield client, sessions, jobs, objects
    main.app.dependency_overrides.clear()
    engine.dispose()

@pytest.fixture
def bidder(workspace):
    client, _, _, _ = workspace
    tender = client.post("/tenders", json={"title": "Hospital equipment", "department": "Health", "deadline": "2027-01-01", "budget": "INR 10000000"}).json()
    response = client.post("/bids", json={"tender_id": tender["id"], "bidder_name": "New Bidder"})
    assert response.status_code == 200
    return response.json()

@pytest.fixture
def valid_pdf():
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "Procurement evidence package")
        return doc.tobytes()
