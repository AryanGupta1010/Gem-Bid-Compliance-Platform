# ProcureGuard Status Report

This is a complete, evidence-based status report of the ProcureGuard project based on a deep inspection of the current repository structure, code paths, runtime flows, and integrations.

## 1. EXECUTIVE SUMMARY

- **What ProcureGuard currently does**: ProcureGuard is an automated procurement compliance evaluation platform. It ingests bidder documents, extracts evidence using targeted OCR and visual retrieval, and evaluates compliance deterministically against specific rules (Turnover, GST, CPPP Debarment, Local Content, OEM Authorization). It adheres to the principle that AI finds evidence, code verifies facts, and the human officer makes the final decision.
- **Overall completion percentage estimate**: ~80% (MVP / Demo-ready).
- **Current maturity**: Demo-ready MVP. The core architecture (Next.js + FastAPI + DB + Redis/RQ + MinIO) is in place, and the "Golden Demo" flow is fully operational.
- **Biggest strengths**: Excellent separation of concerns (deterministic engine vs. heuristic AI services). Strong architectural foundation with background jobs for heavy PDF processing. Graceful degradation mechanisms for AI models and external APIs.
- **Biggest weaknesses**: Real AI integration (Surya/ColPali) relies on fallbacks when endpoints aren't running. Missing robust authentication. The database is currently configured for SQLite by default rather than a resilient PostgreSQL setup.
- **Most important remaining work**: Connecting live, real AI model endpoints instead of relying on the network fallbacks. Hardening frontend error handling. Migrating the active database to PostgreSQL for production readiness.

---

## 2. ACTUAL REPOSITORY STRUCTURE

The repository has been successfully cleaned and reorganized into a strictly professional structure. All dead code, duplicate directories (like the old ASTRA folders), and obsolete files have been removed.

```text
SIH 2026/
├── .git/
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── run_server.py
│   ├── worker.py
│   ├── app/                    # Core FastAPI Application
│   │   ├── __init__.py
│   │   ├── adapters.py         # Gov API integrations (GST, CPPP)
│   │   ├── config.py           # Pydantic settings management
│   │   ├── database.py         # SQLAlchemy setup
│   │   ├── engine.py           # Deterministic Rule Engine
│   │   ├── main.py             # FastAPI routes
│   │   ├── models.py           # Database schemas
│   │   ├── schemas.py          # Pydantic request/response models
│   │   ├── seed.py             # Demo data seeder
│   │   ├── storage.py          # MinIO client wrapper
│   │   ├── tasks.py            # RQ background worker pipeline
│   │   └── services/
│   │       ├── extractor.py    # Regex-based data extraction
│   │       ├── ocr.py          # Surya OCR / Demo mock
│   │       ├── renderer.py     # PyMuPDF renderer
│   │       └── retriever.py    # ColPali / Text retrieval
│   ├── demo_documents/         # Golden Demo PDF assets
│   ├── gov_api/                # Mock Government APIs
│   │   └── main.py
│   ├── scripts/                # Utility scripts
│   │   └── test_golden_demo.py
│   └── tests/                  # Backend unit tests
└── frontend/                   # Next.js Frontend Application
    ├── package.json
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── app/                    # Next.js App Router
    │   ├── globals.css
    │   ├── layout.tsx
    │   ├── page.tsx            # Dashboard
    │   ├── bids/[id]/          # Bid details route
    │   ├── evaluations/[id]/   # Core Evaluation UI
    │   └── tenders/            # Tenders listing
    ├── components/
    │   ├── audit/              # Audit timeline components
    │   ├── dashboard/          # Dashboard overviews
    │   ├── evaluations/        # Evaluation Viewer, Rule Results, Officer Panel
    │   ├── layout/             # App shell, navigation
    │   ├── tenders/            # Tender and bid lists
    │   └── ui/                 # Reusable UI primitives (buttons, badges)
    └── lib/
        ├── services.ts         # Backend API fetch wrappers
        └── utils.ts
```

---

## 3. FRONTEND STATUS

The frontend is built with Next.js (App Router), TailwindCSS, and React. 

- **Dashboard (`/`)**
  - **Status**: IMPLEMENTED
  - **Features**: Fetches active tenders and audit trails from the backend API via `services.ts`. Displays aggregate metrics and the "Officer decision queue". Fully working with live DB data.
- **Tenders Register (`/tenders`)**
  - **Status**: IMPLEMENTED
  - **Features**: Fetches and lists all tenders.
- **Tender Details (`/tenders/[id]`)**
  - **Status**: IMPLEMENTED
  - **Features**: Displays tender stats and a list of corresponding bids. Data is dynamically fetched.
- **Evaluations / Bid Details (`/evaluations/[id]`)**
  - **Status**: IMPLEMENTED
  - **Features**: This is the most complex page. It fetches the bid details, associated documents, rule evaluations, and audit events. 
  - **Working**: The `officer-decision-panel` successfully POSTs decisions back to the backend. The `rule-result-card` displays extracted evidence.
  - **Non-working/Mocked**: The actual PDF viewer component relies on browser-native rendering or placeholders depending on the MinIO URL accessibility from the client side.

---

## 4. BACKEND API STATUS

All endpoints are defined in `backend/app/main.py`.

- `POST /api/tenders/{tender_id}/bids/{bid_id}/documents`
  - **Status**: IMPLEMENTED
  - **Details**: Handles multipart file uploads. Writes the file to MinIO, calculates SHA3-512, writes a `Document` record to the DB, and enqueues `process_document_pipeline` to the RQ worker.
- `GET /api/tenders`
  - **Status**: IMPLEMENTED
  - **Details**: Reads and returns all Tenders and nested Bids from the database.
- `GET /api/bids/{bid_id}`
  - **Status**: IMPLEMENTED
  - **Details**: Reads a specific Bid from the DB, eagerly loading `documents` and `rules`. Returns the full evaluation state.
- `POST /api/bids/{bid_id}/decision`
  - **Status**: IMPLEMENTED
  - **Details**: Writes the final human Officer Decision (e.g., "Approve", "Reject") to the database and logs an `AuditEvent`.
- `GET /api/audit`
  - **Status**: IMPLEMENTED
  - **Details**: Reads the global audit trail from the `AuditEvent` table.
- `POST /api/seed`
  - **Status**: IMPLEMENTED
  - **Details**: Executes `seed.py` to populate the DB with the Golden Demo tender and the 3 demo bidders.

---

## 5. COMPLIANCE ENGINE & RULES

The compliance evaluation is handled by the `DeterministicEngine` (`app/engine.py`). It adheres strictly to the rule: "AI finds evidence, code verifies facts. UNAVAILABLE evidence results in a REVIEW status, never a FAIL."

- **Rule Extraction**: 
  - Visual retrieval finds the bounding boxes (`app/services/retriever.py`).
  - OCR extracts the text from those boxes (`app/services/ocr.py`).
  - Regex parses the raw text into structured values (`app/services/extractor.py`).
- **Implemented Rules**:
  - `RULE-TURNOVER`: Regex extracts "Crore" amounts. Engine verifies `extracted_value >= 10.0`.
  - `RULE-GST`: Extracts 15-char GSTIN. Engine verifies validity via the external Gov API adapter.
  - `RULE-CPPP`: Extracts debarment status. Engine verifies status via the external Gov API adapter.
  - `RULE-LOCAL-CONTENT`: Extracts percentage. Engine verifies `extracted_value >= 50.0`.
  - `RULE-OEM`: Keyword extraction ("authorization", "mismatch"). Engine checks for missing/mismatch states.
- **Status**: FULLY IMPLEMENTED. The logic successfully aggregates rule results to determine the final Bid Risk (LOW/MEDIUM/HIGH) and Status (PASS/REVIEW/FAIL).

---

## 6. BACKGROUND JOBS & PIPELINE

Document processing is completely offloaded to a Redis/RQ background worker to prevent blocking the FastAPI event loop.

- **Pipeline Trace (`app.tasks.process_document_pipeline`)**:
  - **Stage 1: HASH**: Downloads the file from MinIO and recalculates the SHA3-512 hash to verify integrity.
  - **Stage 2: RENDER**: Uses `PyMuPDF` to render PDF pages into images, uploading them back to MinIO (`pages_bucket`) and creating `PageImage` DB records.
  - **Stage 3: EVALUATE**: Triggers the `DeterministicEngine` which runs retrieval, OCR, extraction, and rule evaluation.
- **Status**: FULLY IMPLEMENTED AND WORKING.

---

## 7. EXTERNAL INTEGRATIONS

- **Gov APIs (GST & CPPP)**
  - **Integration**: `app.adapters.GSTVerificationClient` and `app.adapters.CPPPVerificationClient`.
  - **Status**: MOCKED. Real government APIs are simulated via a lightweight FastAPI server located in `backend/gov_api/main.py` (runs on port 8001).
- **Surya OCR & ColPali Visual Retrieval**
  - **Integration**: `app.services.ocr.SuryaOCR` and `app.services.retriever.ColPaliRetriever`.
  - **Status**: NETWORK FALLBACK. The codebase makes real network requests to the `MODEL_ENDPOINT`. If the endpoint is down (timeout), it gracefully falls back to a robust deterministic mock (`DemoOCR` / `TextRetriever`) so the platform continues to function.

---

## 8. DATABASE SCHEMA

The database uses SQLAlchemy ORM.

- **Tables**:
  - `Tender`: `id`, `title`, `department`, `budget`, `status`
  - `Bid`: `id`, `tender_id`, `bidder_name`, `gstin`, `score`, `risk`, `status`, `reviewer_decision`
  - `Document`: `id`, `bid_id`, `filename`, `minio_path`, `hash_sha3_512`, `processing_stage`, `status`
  - `PageImage`: `id`, `document_id`, `page_number`, `minio_path`
  - `RuleResult`: `id`, `bid_id`, `rule_id`, `extracted_value`, `result` (PASS/FAIL/REVIEW/UNAVAILABLE), `confidence`
  - `AuditEvent`: `id`, `time`, `actor`, `action`, `document`, `hash`
- **Status**: IMPLEMENTED. Relationships are properly configured (e.g., `Bid` cascades to `Documents` and `RuleResults`).

---

## 9. SECURITY & CONFIGURATION

- **Configuration**: Managed via `pydantic-settings` (`app/config.py`). Loads from `.env`.
- **Secrets**: No hardcoded API keys exist in the repository. Redis, Postgres, and MinIO credentials rely entirely on environment variables.
- **Authentication**: MISSING. Currently, there is no JWT/OAuth layer implemented for the API, and the Next.js frontend assumes the user is an authenticated Procurement Officer.

---

## 10. DEMO CAPABILITIES (THE GOLDEN DEMO)

The "Golden Demo" is fully functional and designed to execute a flawless presentation for judges.

- **Demo Bidders**:
  1. **TechNova Systems (PASS)**: Provides perfect evidence.
  2. **Apex Industrial Solutions (FAIL)**: Fails turnover, GST, and is actively debarred on CPPP.
  3. **MedCore Technologies (REVIEW)**: Contains illegible scans and conflicting evidence, triggering the `UNAVAILABLE -> REVIEW` safety mechanism.
- **Execution**: The script `backend/scripts/test_golden_demo.py` orchestrates the entire flow:
  1. Seeds the database.
  2. Uploads `demo_documents/SIH_2026_Procurement_Demo.pdf` to the backend.
  3. Polls the API until the background worker finishes processing.
  4. Asserts that the deterministic engine arrived at the correct PASS/FAIL/REVIEW states.
- **Status**: WORKING. Tested and verified locally.

---

## 11. RECOMMENDED NEXT STEPS

1. **Connect Live AI Models**: Replace the `MODEL_ENDPOINT` fallbacks with real hosted instances of Surya and ColPali to demonstrate true visual document understanding.
2. **Implement Authentication**: Add a lightweight JWT auth layer for the FastAPI backend and a login screen for the Next.js frontend to represent a secure internal portal.
3. **Migrate to PostgreSQL**: While the code supports Postgres, ensure the default `docker-compose.yml` and `.env` use PostgreSQL instead of SQLite for production-grade demonstrations.
4. **Error Boundaries**: Add robust React Error Boundaries to the frontend to prevent the entire UI from crashing if a single MinIO image fails to load.
5. **Real MinIO Proxies**: Ensure the frontend can securely access MinIO images through a backend proxy route rather than exposing the MinIO port directly to the client browser.
