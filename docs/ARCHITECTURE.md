# AI-Powered Integrated Bid Compliance Verification Platform for GeM (SIH26100)
## Architecture & Technical Specification (Phases 1 & 2)

### 1. Architectural Philosophy
The platform operates on the core principle:
> **"Find evidence, verify facts, apply explicit rules, explain the result, and let the officer make the final decision."**

The system provides intelligent decision support and deterministic evaluation without ever autonomously making binding procurement decisions.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Next.js 14 Web Frontend                          │
│        (Procurement Dashboard • Evaluation Hero Console • Audit Trail)      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / JSON (JWT / Role Auth)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI Backend                                │
├──────────────────────────────────────┬──────────────────────────────────────┤
│  Document Ingestion & Cryptography   │  • PyMuPDF (fitz) page extraction    │
│                                      │  • SHA-3-512 cryptographic hashing   │
├──────────────────────────────────────┼──────────────────────────────────────┤
│  External Verification Adapters      │  • GSTN Taxpayer Verification        │
│                                      │  • Udyam MSME Registry               │
│                                      │  • Central Debarment / CPPP          │
│                                      │  • ICAI UDIN & BIS CRS Standards     │
├──────────────────────────────────────┼──────────────────────────────────────┤
│  Deterministic Rule Engine           │  • 100% Reproducible arithmetic      │
│                                      │  • PASS / FAIL / REVIEW / UNAVAIL    │
├──────────────────────────────────────┼──────────────────────────────────────┤
│  Scoring & Risk Assessment Engine    │  • Explainable weighted severity     │
│                                      │  • LOW / MEDIUM / HIGH / CRITICAL    │
├──────────────────────────────────────┼──────────────────────────────────────┤
│  Human Officer Review Flow           │  • Separate human decision record    │
│                                      │  • Mandatory justification notes     │
├──────────────────────────────────────┼──────────────────────────────────────┤
│  Immutable Audit System              │  • Timestamped actor/action trails   │
└──────────────────────────────────────┴──────────────────────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│     PostgreSQL + pgvector    │              │       MinIO / S3 Storage     │
│  (Relational + Visual Ready) │              │    (Immutable Raw PDFs)      │
└──────────────────────────────┘              └──────────────────────────────┘
```

---

### 2. Phase 3 AI Interface Abstractions
Phase 3 will integrate deep AI layers without modifying the database schema, frontend UI, or rule evaluation pipeline. The abstract interfaces are already defined in `app.services.ai_interfaces`:

1. **`DocumentRetrievalService`**:
   - *Phase 1/2*: Deterministic document coordinate mapper.
   - *Phase 3*: ColPali visual embeddings indexed directly in PostgreSQL via `pgvector`.
2. **`FieldExtractionService`**:
   - *Phase 1/2*: Metadata property extractor.
   - *Phase 3*: Surya OCR and DocQuery layout analysis.
3. **`RequirementExtractionService`**:
   - *Phase 1/2*: Manual & pre-seeded RFP rules.
   - *Phase 3*: Saul-7B legal LLM for automated RFP clause parsing into deterministic rule schemas.
4. **`ContextualInferenceService`**:
   - *Phase 1/2*: Deterministic rule matcher.
   - *Phase 3*: Natural Language Inference (NLI / VLM) for contextual compliance reasoning.

---

### 3. Verification Adapters Semantics
- **`VALID`**: Registry confirms active and compliant status.
- **`INVALID`**: Registry confirms cancelled, disqualified, or non-conforming status.
- **`EXPIRED`**: Certificate or registration past validity date.
- **`UNAVAILABLE`**: External gateway timeout or service interruption.
- **Critical Policy**: `UNAVAILABLE` does **NOT** trigger automatic failure; it flags the bid as `REVIEW` for Procurement Officer human resolution.
