from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import datetime, timezone

app = FastAPI(title="Government Integration Mock API", version="1.0.0")

class CPPPRequest(BaseModel):
    company_name: str

@app.get("/api/v1/gstin/{gstin}")
async def check_gstin(gstin: str):
    """Mock external GSTIN registry endpoint."""
    gstin = gstin.upper()
    
    if gstin == "27AADCB2230M1Z2":
        return {
            "status": "ACTIVE",
            "legal_name": "TECHNOVA SYSTEMS PVT. LTD.",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    elif gstin == "07BBPCA1120K1Z1":
        return {
            "status": "SUSPENDED",
            "legal_name": "APEX INDUSTRIAL SOLUTIONS PVT. LTD.",
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
    elif "UNREADABLE" in gstin or not gstin:
        raise HTTPException(status_code=400, detail="Invalid GSTIN format")
        
    raise HTTPException(status_code=404, detail="GSTIN Not Found")

@app.post("/api/v1/cppp/status")
async def check_cppp(req: CPPPRequest):
    """Mock external Central Public Procurement Portal debarment lookup."""
    company = req.company_name.strip().casefold()
    
    # Simulate DB lookup latency
    known = {
        "technova systems pvt. ltd.", "technova solutions", 
        "medcore technologies pvt. ltd.", "medcore systems", 
        "apex industrial solutions pvt. ltd.", "apex enterprises"
    }
    
    if company not in known:
        raise HTTPException(status_code=404, detail="Company not registered in CPPP vendor DB")
        
    if company in {"apex industrial solutions pvt. ltd.", "apex enterprises"}:
        return {
            "debarred": True,
            "reason": "Late delivery in past government contracts.",
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

    return {
        "debarred": False,
        "reason": "No record found on debarment list.",
        "checked_at": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
