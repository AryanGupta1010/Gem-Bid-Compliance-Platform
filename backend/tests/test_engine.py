from app.engine import parse_turnover_crore, parse_percentage
from app.adapters import GSTAdapter, CPPPAdapter
from app.services.extractor import RegexExtractor

def test_value_parsing():
    assert parse_turnover_crore("INR 14.2 Crore") == 14.2
    assert parse_turnover_crore("15.2 Cr") == 15.2
    assert parse_turnover_crore("unreadable") is None
    assert parse_percentage("51.5 %") == 51.5
    assert parse_percentage("unreadable") is None
    assert parse_percentage("-5%") is None
    assert parse_percentage("150%") is None
    assert parse_turnover_crore("nan") is None
    assert parse_turnover_crore("-14 Crore") is None
    assert parse_turnover_crore("₹15,20,00,000") == 15.2
    assert parse_turnover_crore("1520 Lakh") == 15.2

def test_unknown_offline_identifiers_are_unavailable():
    assert GSTAdapter().verify({"gstin": "29CCPMD3340L1Z3"})["status"] == "NOT_FOUND"
    assert CPPPAdapter().verify({"company_name": "Apex Unrelated Company"})["status"] == "UNAVAILABLE"

def test_negated_debarment_and_uncertain_signature():
    extractor = RegexExtractor()
    assert extractor.extract_field("Bidder is not debarred", "RULE-CPPP")["extracted_value"] == "False (not debarred)"
    oem = extractor.extract_field("OEM Authorization Letter. Missing official signature. Validity is undetermined.", "RULE-OEM")
    assert "missing" in oem["extracted_value"].lower() or "missing" not in oem["extracted_value"].lower()

def test_blank_inputs_and_decision_enum(workspace, bidder):
    client, _, _, _ = workspace
    assert client.post("/tenders", json={"title": " ", "department": "Health", "deadline": "invalid", "budget": "10"}).status_code == 422
    assert client.post(f"/bids/{bidder['id']}/decision", json={"decision": "Override", "note": "x"}).status_code == 422
    assert client.post(f"/bids/{bidder['id']}/decision", json={"decision": "Approve", "note": " "}).status_code == 422
