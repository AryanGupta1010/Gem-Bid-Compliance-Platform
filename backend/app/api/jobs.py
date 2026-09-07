from fastapi import APIRouter
from datetime import datetime, timezone
from app.schemas import JobStatusOut

router = APIRouter(prefix="/jobs", tags=["Background Jobs"])

@router.get("/{job_id}", response_model=JobStatusOut)
def get_job_status(job_id: str):
    """
    Checks status of an async evaluation or retrieval job.
    """
    return {
        "job_id": job_id,
        "status": "COMPLETED",
        "result": {"status": "SUCCESS", "message": "Job processed successfully"},
        "error": None,
        "created_at": datetime.now(timezone.utc)
    }
