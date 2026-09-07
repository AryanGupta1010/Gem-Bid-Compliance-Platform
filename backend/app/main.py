import uuid
import time
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import logger
from app.core.errors import GeMException

# Import routers
from app.api.auth import router as auth_router
from app.api.tenders import router as tenders_router
from app.api.bidders import router as bidders_router
from app.api.bids import router as bids_router
from app.api.documents import router as documents_router
from app.api.review import router as review_router
from app.api.audit import router as audit_router
from app.api.verification import router as verification_router
from app.api.jobs import router as jobs_router

# Initialize FastAPI App
app = FastAPI(
    title="GeM AI Bid Compliance Verification Platform",
    description=(
        "Production-grade decision-support API for Government e-Marketplace (GeM) "
        "Procurement Officers. Implements deterministic rule engines, external verification "
        "adapters (GST, Udyam, Debarment), explainable compliance scoring, risk assessment, "
        "document hashing (SHA-3-512), and immutable audit trails."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID & Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    start_time = time.time()
    
    logger.info(f"Incoming request {request.method} {request.url.path}", extra={"request_id": request_id})
    
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    
    logger.info(f"Completed {request.method} {request.url.path} with status {response.status_code} in {process_time:.2f}ms", extra={"request_id": request_id})
    return response

# Custom Exception Handler
@app.exception_handler(GeMException)
async def gem_exception_handler(request: Request, exc: GeMException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.detail,
            "extra": exc.extra,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# Create tables on startup if not existing
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified/created successfully.")

# Mount Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(tenders_router, prefix=settings.API_V1_STR)
app.include_router(bidders_router, prefix=settings.API_V1_STR)
app.include_router(bids_router, prefix=settings.API_V1_STR)
app.include_router(documents_router, prefix=settings.API_V1_STR)
app.include_router(review_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(verification_router, prefix=settings.API_V1_STR)
app.include_router(jobs_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "GeM Bid Compliance Platform",
        "version": "1.0.0",
        "demo_mode": settings.DEMO_MODE
    }
