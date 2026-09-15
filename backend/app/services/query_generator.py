"""
Query Generator Abstraction for Visual Document Retrieval.

Transforms tender requirements into semantic visual retrieval queries for ColPali.
"""
from typing import Dict, Any
from pydantic import BaseModel

class RetrievalQuery(BaseModel):
    rule_id: str
    query_text: str
    target_evidence_type: str

class QueryGenerator:
    """Interface for generating retrieval queries from structured requirements."""
    def generate_query(self, requirement: Dict[str, Any]) -> RetrievalQuery:
        raise NotImplementedError

class RuleQueryGenerator(QueryGenerator):
    """
    Deterministic rule-to-query generator.
    Can be seamlessly extended to an LLM-based query generator.
    """
    def generate_query(self, requirement: Dict[str, Any]) -> RetrievalQuery:
        rule_id = requirement.get("rule_id", "")
        field = requirement.get("field", "")
        evidence_type = requirement.get("evidence_type", "document")

        if rule_id == "RULE-TURNOVER" or "turnover" in field.lower():
            query_text = "bidder annual turnover audited balance sheet profit loss financial statement last three financial years"
            target_evidence = "financial_statement"
        elif rule_id == "RULE-GST" or "gst" in field.lower():
            query_text = "bidder GST registration certificate GSTIN tax identification legal business name"
            target_evidence = "gst_certificate"
        elif rule_id == "RULE-CPPP" or "debar" in field.lower() or "blacklist" in field.lower():
            query_text = "non-debarment certificate self-declaration not blacklisted suspended CPPP government procurement"
            target_evidence = "debarment_declaration"
        elif rule_id == "RULE-LOCAL-CONTENT" or "local" in field.lower():
            query_text = "Make in India local content declaration percentage calculation Class-I Class-II local supplier"
            target_evidence = "local_content_certificate"
        elif rule_id == "RULE-OEM" or "oem" in field.lower() or "manufacturer" in field.lower():
            query_text = "OEM manufacturer authorization letter MAF authorized distributor bidder name"
            target_evidence = "oem_authorization"
        elif rule_id == "RULE-UDYAM" or "udyam" in field.lower() or "msme" in field.lower():
            query_text = "Udyam registration certificate MSME enterprise category micro small medium"
            target_evidence = "udyam_certificate"
        elif rule_id == "RULE-TENDER-REF" or "reference" in field.lower():
            query_text = "GeM Bid Number Tender Reference Number NIT ID procurement reference"
            target_evidence = "reference_number"
        else:
            query_text = f"bidder evidence verification for requirement {rule_id} {requirement.get('name', '')}"
            target_evidence = evidence_type

        return RetrievalQuery(
            rule_id=rule_id,
            query_text=query_text,
            target_evidence_type=target_evidence
        )

def get_query_generator() -> QueryGenerator:
    return RuleQueryGenerator()
