from fastapi import APIRouter, HTTPException, Depends
from app.schemas import VerificationResultOut, VerificationDirectQuery
from app.verification.adapters import verification_registry
from app.api.deps import get_current_user

router = APIRouter(prefix="/verification", tags=["External Verification"])

@router.post("/query")
def direct_verification_query(
    query: VerificationDirectQuery,
    current_user = Depends(get_current_user)
):
    """
    Direct test query against external government verification adapters (GST, Udyam, Debarment, UDIN, BIS).
    """
    adapter = verification_registry.get_adapter(query.source)
    if not adapter:
        raise HTTPException(status_code=400, detail=f"Unsupported verification source '{query.source}'")

    res = adapter.verify(query.identifier)
    return res.to_dict()
