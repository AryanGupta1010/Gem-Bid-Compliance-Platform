from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Document
from app.schemas import DocumentOut
from app.storage import storage_service

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.get("/{id}", response_model=DocumentOut)
def get_document_metadata(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.get("/{id}/download")
def download_document(id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        content = storage_service.get_file(doc.file_path)
    except Exception:
        raise HTTPException(status_code=404, detail="Document file content not found in storage")

    return Response(
        content=content,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'}
    )
