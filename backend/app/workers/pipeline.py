from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import (
    Bid, Tender, Requirement, Document, Evidence, VerificationRequest,
    VerificationResult, RuleResult, ComplianceAssessment, BidStatus, generate_uuid, utc_now
)
from app.rules.engine import rule_engine
from app.verification.adapters import verification_registry
from app.services.scoring_service import scoring_service
from app.services.risk_service import risk_service
from app.audit.service import audit_service
from app.core.logging import logger

def run_bid_evaluation_pipeline(
    db: Session,
    bid_id: str,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Complete end-to-end evaluation pipeline:
    1. Fetch Bid, Bidder, Tender, and Requirements
    2. Collect structured document & metadata context
    3. Run external Verification Adapters
    4. Run Deterministic Rule Engine
    5. Calculate Explainable Compliance Score
    6. Calculate Risk Level & Recommendation
    7. Persist Results & Evidence
    8. Emit Immutable Audit Event
    """
    logger.info(f"Starting evaluation pipeline for Bid {bid_id}", extra={"bid_id": bid_id, "request_id": request_id})

    bid = db.query(Bid).filter(Bid.id == bid_id).first()
    if not bid:
        raise ValueError(f"Bid with id {bid_id} not found")

    tender = db.query(Tender).filter(Tender.id == bid.tender_id).first()
    if not tender:
        raise ValueError(f"Tender with id {bid.tender_id} not found")

    requirements = db.query(Requirement).filter(
        Requirement.tender_id == tender.id,
        Requirement.enabled == True
    ).order_by(Requirement.display_order).all()

    bidder = bid.bidder
    documents = db.query(Document).filter(Document.bid_id == bid.id).all()

    # Clear previous evaluation results if re-running
    db.query(Evidence).filter(Evidence.rule_result_id.in_(
        db.query(RuleResult.id).filter(RuleResult.bid_id == bid.id)
    )).delete(synchronize_session=False)
    db.query(RuleResult).filter(RuleResult.bid_id == bid.id).delete(synchronize_session=False)
    db.query(ComplianceAssessment).filter(ComplianceAssessment.bid_id == bid.id).delete(synchronize_session=False)
    db.commit()

    # Build context dictionary
    context: Dict[str, Any] = {
        "bid": {
            "id": bid.id,
            "bid_number": bid.bid_number,
            "amount": bid.bid_amount
        },
        "bidder": {
            "id": bidder.id,
            "name": bidder.name,
            "gstin": bidder.gstin,
            "pan": bidder.pan,
            "udyam_number": bidder.udyam_number,
            "is_msme": bidder.is_msme
        },
        "documents": [
            {
                "id": doc.id,
                "document_type": doc.document_type,
                "filename": doc.filename,
                "document_hash": doc.document_hash,
                "metadata": doc.metadata_json or {}
            }
            for doc in documents
        ],
        "extracted_fields": {},
        "verification_results": {}
    }

    # Extract fields from document metadata or bidder properties
    for doc in documents:
        meta = doc.metadata_json or {}
        if "turnover" in meta:
            context["extracted_fields"]["turnover"] = {
                "value": meta["turnover"],
                "confidence": 1.0,
                "evidence": {
                    "document_id": doc.id,
                    "page_number": meta.get("turnover_page", 2),
                    "bounding_box": meta.get("turnover_box", [0.15, 0.45, 0.85, 0.55]),
                    "extracted_field": "turnover",
                    "extracted_value": str(meta["turnover"]),
                    "confidence": 1.0,
                    "source": f"Audited Financial Statement ({doc.filename})"
                }
            }
        if "local_content_percentage" in meta:
            context["extracted_fields"]["local_content"] = {
                "value": meta["local_content_percentage"],
                "confidence": 1.0,
                "evidence": {
                    "document_id": doc.id,
                    "page_number": meta.get("lc_page", 1),
                    "bounding_box": meta.get("lc_box", [0.10, 0.30, 0.90, 0.45]),
                    "extracted_field": "local_content_percentage",
                    "extracted_value": f"{meta['local_content_percentage']}%",
                    "confidence": 1.0,
                    "source": f"Class-I Local Content Declaration ({doc.filename})"
                }
            }
        if "oem_authorization" in meta:
            context["extracted_fields"]["oem_authorization"] = {
                "value": meta["oem_authorization"],
                "confidence": 1.0,
                "evidence": {
                    "document_id": doc.id,
                    "page_number": 1,
                    "bounding_box": [0.08, 0.20, 0.92, 0.40],
                    "extracted_field": "oem_authorization",
                    "extracted_value": str(meta["oem_authorization"]),
                    "confidence": 1.0,
                    "source": f"OEM Authorization Letter ({doc.filename})"
                }
            }

    # Run Verification Adapters
    # 1. GST Verification
    if bidder.gstin:
        v_req = VerificationRequest(
            id=generate_uuid(),
            bid_id=bid.id,
            source="GST",
            request_identifier=bidder.gstin,
            request_payload={"legal_name": bidder.name}
        )
        db.add(v_req)
        db.commit()

        v_res = verification_registry.verify("GST", bidder.gstin, {"legal_name": bidder.name})
        v_record = VerificationResult(
            id=generate_uuid(),
            verification_request_id=v_req.id,
            bid_id=bid.id,
            source="GST",
            request_identifier=bidder.gstin,
            status=v_res.status,
            response_data=v_res.response_data,
            adapter_version=v_res.adapter_version,
            success=v_res.success,
            error_code=v_res.error_code,
            error_message=v_res.error_message
        )
        db.add(v_record)
        db.commit()
        context["verification_results"]["GST"] = v_res.to_dict()
        context["verification_results"]["GST"]["record_id"] = v_record.id

    # 2. Debarment Verification
    v_req_deb = VerificationRequest(
        id=generate_uuid(),
        bid_id=bid.id,
        source="Debarment",
        request_identifier=bidder.registration_number or bidder.name,
        request_payload={"bidder_name": bidder.name, "pan": bidder.pan}
    )
    db.add(v_req_deb)
    db.commit()
    v_res_deb = verification_registry.verify("Debarment", bidder.registration_number or bidder.name)
    v_record_deb = VerificationResult(
        id=generate_uuid(),
        verification_request_id=v_req_deb.id,
        bid_id=bid.id,
        source="Debarment",
        request_identifier=bidder.registration_number or bidder.name,
        status=v_res_deb.status,
        response_data=v_res_deb.response_data,
        adapter_version=v_res_deb.adapter_version,
        success=v_res_deb.success,
        error_code=v_res_deb.error_code,
        error_message=v_res_deb.error_message
    )
    db.add(v_record_deb)
    db.commit()
    context["verification_results"]["Debarment"] = v_res_deb.to_dict()
    context["verification_results"]["Debarment"]["record_id"] = v_record_deb.id

    # 3. Udyam / MSME Verification
    if bidder.udyam_number:
        v_res_udyam = verification_registry.verify("Udyam", bidder.udyam_number)
        v_record_udyam = VerificationResult(
            id=generate_uuid(),
            bid_id=bid.id,
            source="Udyam",
            request_identifier=bidder.udyam_number,
            status=v_res_udyam.status,
            response_data=v_res_udyam.response_data,
            adapter_version=v_res_udyam.adapter_version,
            success=v_res_udyam.success,
            error_code=v_res_udyam.error_code,
            error_message=v_res_udyam.error_message
        )
        db.add(v_record_udyam)
        db.commit()
        context["verification_results"]["Udyam"] = v_res_udyam.to_dict()
        context["verification_results"]["Udyam"]["record_id"] = v_record_udyam.id

    # Evaluate Rule Engine across all requirements
    rule_results_dto = []
    for req in requirements:
        dto = rule_engine.evaluate(req, context)
        rule_results_dto.append(dto)

    # Calculate Score
    score, total_w, passed_w, failed_w, review_w, breakdown = scoring_service.calculate_score(rule_results_dto)

    # Calculate Risk & Recommendation
    risk_level, recommendation, risk_reasons = risk_service.evaluate_risk(rule_results_dto)

    # Persist ComplianceAssessment
    assessment = ComplianceAssessment(
        id=generate_uuid(),
        bid_id=bid.id,
        compliance_score=score,
        risk_level=risk_level,
        recommendation=recommendation,
        total_weight=total_w,
        passed_weight=passed_w,
        failed_weight=failed_w,
        review_weight=review_w,
        summary_metrics={
            "rules_count": len(rule_results_dto),
            "passed_count": sum(1 for r in rule_results_dto if r.status.value == "PASS"),
            "failed_count": sum(1 for r in rule_results_dto if r.status.value == "FAIL"),
            "review_count": sum(1 for r in rule_results_dto if r.status.value in ("REVIEW", "UNAVAILABLE")),
            "breakdown": breakdown,
            "risk_reasons": risk_reasons
        },
        evaluated_at=utc_now()
    )
    db.add(assessment)
    db.commit()

    # Persist RuleResults and Evidence
    for dto in rule_results_dto:
        v_rec_id = None
        if dto.verification_data and "record_id" in dto.verification_data:
            v_rec_id = dto.verification_data["record_id"]

        rule_res = RuleResult(
            id=generate_uuid(),
            bid_id=bid.id,
            requirement_id=dto.requirement_id,
            compliance_assessment_id=assessment.id,
            verification_result_id=v_rec_id,
            status=dto.status,
            actual_value=dto.actual_value,
            expected_value=dto.expected_value,
            explanation=dto.explanation,
            severity=dto.severity,
            weight=dto.weight,
            confidence=dto.confidence,
            rule_version=dto.rule_version,
            evaluated_at=utc_now()
        )
        db.add(rule_res)
        db.commit()

        # Link evidence
        for ev in dto.evidence_data:
            ev_record = Evidence(
                id=generate_uuid(),
                document_id=ev.get("document_id"),
                rule_result_id=rule_res.id,
                page_number=ev.get("page_number", 1),
                bounding_box=ev.get("bounding_box", [0.1, 0.1, 0.9, 0.3]),
                extracted_field=ev.get("extracted_field", "field"),
                extracted_value=ev.get("extracted_value", ""),
                confidence=ev.get("confidence", 1.0),
                source=ev.get("source", "Bidder document")
            )
            db.add(ev_record)
        db.commit()

    # Update bid status
    bid.status = BidStatus.EVALUATED
    db.commit()

    # Record Audit Event
    audit_service.record_event(
        db=db,
        action="BID_EVALUATION_COMPLETED",
        entity_type="Bid",
        entity_id=bid.id,
        user_id=user_id,
        request_id=request_id,
        metadata_json={
            "score": score,
            "risk_level": risk_level.value,
            "recommendation": recommendation.value,
            "rules_evaluated": len(rule_results_dto)
        }
    )

    logger.info(f"Evaluation completed for Bid {bid.id}: Score={score}, Risk={risk_level.value}, Recommendation={recommendation.value}")

    return {
        "bid_id": bid.id,
        "score": score,
        "risk_level": risk_level.value,
        "recommendation": recommendation.value,
        "assessment_id": assessment.id,
        "status": "COMPLETED"
    }
