# AI-Powered Integrated Bid Compliance Verification Platform for GeM (SIH26100)

> **Phase 1 & Phase 2 MVP/Prototype**  
> Complete Production-Quality Full-Stack Application for Government e-Marketplace (GeM) Procurement Officers.

---

## 🏛️ System Overview

The **GeM Bid Compliance Verification Platform** is an enterprise decision-support tool engineered for Procurement Officers evaluating complex public procurement bids. It automates deterministic rule checking, external government adapter verification (GST, Udyam/MSME, Debarment, UDIN, BIS), cryptographic document sealing (SHA-3-512), and explainable risk scoring while strictly keeping the final procurement authority in human hands.

### Core Workflow
$$\text{Tender Creation} \longrightarrow \text{Rule Specification} \longrightarrow \text{Bidder Submission} \longrightarrow \text{SHA-3-512 Hashing} \longrightarrow \text{Adapters + Rule Engine} \longrightarrow \text{Scoring \& Risk} \longrightarrow \text{Evidence Grounding} \longrightarrow \text{Officer Human Decision} \longrightarrow \text{Audit Trail}$$

---

## ⚡ Key Features

- 🎯 **Deterministic Rule Engine**: 100% reproducible evaluations for numeric thresholds, dates, boolean logic, document completeness, and status checks.
- 🔌 **Verification Adapter Framework**: Pluggable adapters with deterministic fixtures for **GSTN**, **Ministry of MSME (Udyam)**, **Central Debarment Registry (CPPP)**, **ICAI UDIN**, and **BIS Standards**.
- 🛡️ **Explainable Compliance Scoring & Risk Engine**: Weighted severity model (Critical: 30, High: 20, Medium: 10, Low: 5) and 4-tier risk classification (LOW, MEDIUM, HIGH, CRITICAL).
- 📜 **Cryptographic Document Management**: SHA-3-512 hash generation on ingestion with PyMuPDF (fitz) metadata extraction.
- 🔍 **Visual Evidence Grounding**: Traceable linking of rule results to exact document files, page numbers, and bounding box coordinates.
- 👨‍💼 **Human-in-the-Loop Decision Console**: Separate persistence of human officer decisions (`APPROVED`, `REJECTED`, `NEEDS_REVIEW`) with mandatory justification notes.
- 🔒 **Immutable Audit Trail**: Chronological, timestamped log of all tender, evaluation, and review actions.
- 🤖 **AI-Ready Interfaces**: Clean service abstractions (`DocumentRetrievalService`, `FieldExtractionService`, `RequirementExtractionService`, `ContextualInferenceService`) ready for Phase 3 drop-in of ColPali, Surya OCR, Saul-7B, and NLI.

---

## 🚀 Quick Start with Docker

The fastest way to start the complete stack (Postgres + pgvector, Redis, MinIO, FastAPI Backend, Next.js Frontend):

```bash
# 1. Clone repository & navigate to directory
cd SIH_2026

# 2. Start all containerized services
docker compose up --build
```

Access the applications:
- **Frontend Web Dashboard**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MinIO Object Storage Console**: [http://localhost:9001](http://localhost:9001)

---

## 💻 Standalone Local Setup (Without Docker)

### 1. Backend Setup (FastAPI)

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run seed script (Creates demo tender, rules, and 3 benchmark bidders)
python -m app.seed

# Run automated tests
python -m pytest tests -v

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup (Next.js 14)

```bash
cd frontend

# Install dependencies
npm install

# Build for production validation
npm run build

# Start Next.js development server
npm run dev
```

---

## 📊 Live 3-Bidder Evaluation Benchmark

The system comes pre-seeded with Tender **GEM/2026/B/89410 - Procurement of 100 Enterprise Laptops for MeitY** and 3 deterministic scenario bidders:

| Bidder | Key Conditions | Expected Result | Risk Level | Rationale |
| :--- | :--- | :---: | :---: | :--- |
| **Alpha Technologies** | Turnover: ₹12.5 Cr (Req: ₹10 Cr), GST Valid, Udyam Valid, OEM MAF Present, Local Content: 65% | **PASS** | `LOW` | 100% Compliance across all 7 mandatory clauses. |
| **Beta Infotech** | Turnover: ₹7.2 Cr (Req: ₹10 Cr), GST Valid, OEM MAF Present, Local Content: 55% | **FAIL** | `HIGH` | Failed mandatory minimum turnover threshold ($7.2 < 10$). |
| **Gamma Global** | Turnover: ₹14.0 Cr, **GST API Unavailable**, **OEM Doc Missing** | **REVIEW** | `HIGH` | GST service timeout + Missing OEM authorization letter requires officer discretion. |

---

## 🧪 Automated Testing

Run the full suite of 13 automated unit & integration tests covering numeric pass/fail, date pass/fail, verification status mapping, scoring weights, risk tiers, officer review persistence, and end-to-end evaluation:

```bash
cd backend
python -m pytest tests -v -p no:cacheprovider
```

---

## 📁 Repository Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI Application & Middleware
│   │   ├── core/                    # Security, Database, Logging, Errors, Config
│   │   ├── models/                  # SQLAlchemy 2.0 Database Models
│   │   ├── schemas/                 # Pydantic v2 Request/Response DTOs
│   │   ├── rules/                   # Deterministic Rule Engine
│   │   ├── verification/            # GST, Udyam, Debarment, UDIN, BIS Adapters
│   │   ├── services/                # Scoring, Risk, Audit, AI Mock Interfaces
│   │   ├── storage/                 # Local & MinIO / S3 Object Storage Service
│   │   ├── workers/                 # Complete Evaluation Pipeline Runner
│   │   ├── utils/                   # SHA-3-512 Hashing & PyMuPDF Handler
│   │   ├── api/                     # REST API Endpoints
│   │   └── seed.py                  # Database Seeder & Demo Generator
│   ├── tests/                       # Pytest Automated Test Suite
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── dashboard/               # Executive KPI Dashboard
│   │   ├── tenders/                 # Tenders Listing & Tender Details Console
│   │   ├── bids/[id]/               # Hero Bidder Evaluation & Review Screen
│   │   ├── verification/            # Direct Adapter Testing Sandbox
│   │   └── audit/                   # Full System Audit Trail View
│   ├── components/                  # Reusable UI & Evidence Box Viewers
│   ├── lib/                         # API Client
│   ├── types/                       # TypeScript Definitions
│   ├── package.json
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

---

## 🏛️ GeM Officer Default Credentials
- **Email**: `officer@gem.gov.in`
- **Password**: `officer123`
- **Role**: `PROCUREMENT_OFFICER`
