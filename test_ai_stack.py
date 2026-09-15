import requests
import json

SERVICES = {
    "ColPali (8002)": "http://localhost:8002",
    "Surya OCR (8003)": "http://localhost:8003",
    "Saul-7B (8004)": "http://localhost:8004",
    "NLI DeBERTa (8005)": "http://localhost:8005",
}

print("=== 1. Testing GET / Root Endpoints ===")
for name, url in SERVICES.items():
    try:
        r = requests.get(url + "/", timeout=5)
        print(f"[{name}] GET / -> HTTP {r.status_code}: {r.json()}")
    except Exception as e:
        print(f"[{name}] GET / -> ERROR: {e}")

print("\n=== 2. Testing GET /health Endpoints ===")
for name, url in SERVICES.items():
    try:
        r = requests.get(url + "/health", timeout=5)
        print(f"[{name}] GET /health -> HTTP {r.status_code}: {r.json()}")
    except Exception as e:
        print(f"[{name}] GET /health -> ERROR: {e}")

print("\n=== 3. Testing POST Functionality Endpoints ===")

# Test ColPali Search
try:
    payload = {"document_id": "test_doc", "query": "minimum annual turnover", "top_k": 1}
    r = requests.post("http://localhost:8002/search", json=payload, timeout=5)
    print(f"[ColPali] POST /search -> HTTP {r.status_code}: {json.dumps(r.json(), indent=2)}")
except Exception as e:
    print(f"[ColPali] POST /search -> ERROR: {e}")

# Test Surya OCR
try:
    payload = {"document_id": "test_doc", "page_number": 1, "field_type": "TURNOVER", "page_text": "Audited turnover for FY 2024 is INR 25.5 Crore."}
    r = requests.post("http://localhost:8003/ocr", json=payload, timeout=5)
    print(f"[Surya OCR] POST /ocr -> HTTP {r.status_code}: {json.dumps(r.json(), indent=2)}")
except Exception as e:
    print(f"[Surya OCR] POST /ocr -> ERROR: {e}")

# Test Saul-7B Requirement Extractor
try:
    payload = {"tender_id": "test_tender", "tender_text": "Average annual turnover must be at least ₹10 Crore over the last 3 financial years."}
    r = requests.post("http://localhost:8004/extract-requirements", json=payload, timeout=5)
    print(f"[Saul-7B] POST /extract-requirements -> HTTP {r.status_code}: {json.dumps(r.json(), indent=2)}")
except Exception as e:
    print(f"[Saul-7B] POST /extract-requirements -> ERROR: {e}")

# Test NLI DeBERTa Reasoning
try:
    payload = {
        "premise": "Bidder turnover is ₹14.2 Crore",
        "hypothesis": "Bidder complies with minimum ₹10 Crore requirement"
    }
    r = requests.post("http://localhost:8005/evaluate", json=payload, timeout=5)
    print(f"[NLI DeBERTa] POST /evaluate -> HTTP {r.status_code}: {json.dumps(r.json(), indent=2)}")
except Exception as e:
    print(f"[NLI DeBERTa] POST /evaluate -> ERROR: {e}")
