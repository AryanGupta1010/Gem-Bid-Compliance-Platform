import os
import json
import time
import urllib.request
import urllib.parse

API_URL = "http://localhost:8000"

def test_pipeline():
    print("Testing ProcureGuard E2E Pipeline...")
    
    # 1. Fetch bidders
    req = urllib.request.Request(f"{API_URL}/tenders")
    with urllib.request.urlopen(req) as response:
        tenders = json.loads(response.read().decode())
    
    tender = tenders[0]
    technova = next((b for b in tender['bids'] if b['bidder_name'] == "TechNova Solutions"), None)
    
    if not technova:
        print("TechNova not found.")
        return
        
    print(f"Found TechNova: ID={technova['id']}")
    
    # 2. Upload dummy PDF
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f"Content-Disposition: form-data; name=\"file\"; filename=\"dummy.pdf\"\r\n"
        f"Content-Type: application/pdf\r\n\r\n"
        f"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\r\n"
        f"--{boundary}--\r\n"
    ).encode('utf-8')

    req = urllib.request.Request(
        f"{API_URL}/upload/{technova['id']}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    
    with urllib.request.urlopen(req) as response:
        doc = json.loads(response.read().decode())
        
    print(f"Uploaded successfully. Document ID: {doc['id']}")
    print(f"File status: {doc['status']}")
    
    # 3. Wait
    print("Waiting for RQ worker to process pipeline...")
    for _ in range(5):
        time.sleep(2)
        print("Polling...")
        
    # 4. Check bid status
    req = urllib.request.Request(f"{API_URL}/bids/{technova['id']}")
    with urllib.request.urlopen(req) as response:
        bid_res = json.loads(response.read().decode())
        
    print("============================")
    print(f"Final Status: {bid_res['status']}")
    print(f"Final Risk: {bid_res['risk']}")
    print(f"Final Score: {bid_res['score']}")
    
    print("\nEvaluated Rules:")
    for r in bid_res['rules']:
        extracted = r['extracted_value'].encode('ascii', 'ignore').decode() if r.get('extracted_value') else ''
        print(f"- {r['rule_name']}: {r['result']} (Extracted: {extracted})")
        
    print("\nCheck the UI at http://localhost:3000 to see the evidence viewer updates!")
    
if __name__ == "__main__":
    test_pipeline()
