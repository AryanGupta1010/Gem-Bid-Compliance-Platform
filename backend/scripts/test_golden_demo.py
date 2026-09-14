import os
import time
import requests

API_URL = "http://localhost:8000"

def get_bids():
    resp = requests.get(f"{API_URL}/bids")
    resp.raise_for_status()
    return resp.json()

def upload_document(bid_id, filepath):
    with open(filepath, "rb") as f:
        files = {"file": (os.path.basename(filepath), f, "application/pdf")}
        resp = requests.post(f"{API_URL}/upload/{bid_id}", files=files)
        resp.raise_for_status()
        return resp.json()

def wait_for_processing(bid_id, doc_id, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{API_URL}/bids/{bid_id}/status")
        resp.raise_for_status()
        data = resp.json()
        
        docs = data.get("documents", [])
        latest = next((d for d in docs if d.get("document_id") == doc_id), None)
        if latest:
            stage = latest.get("processing_stage")
            if stage in ("EVALUATED", "FAILED", "COMPLETED", "HUMAN_REVIEW", "ERROR"):
                # Also trigger a manual verify just to be absolutely sure the engine runs
                # But task queue runs it automatically, so let's check rules_count
                return data
        
        time.sleep(2)
    return None

def test_golden_demo():
    print("Fetching bids...")
    bids = get_bids()
    
    bid_map = {b['bidder_name']: b['id'] for b in bids}
    
    demo_files = [
        ("TechNova Systems Pvt. Ltd.", "demo_documents/technova.pdf"),
        ("Apex Industrial Solutions Pvt. Ltd.", "demo_documents/apex.pdf"),
        ("MedCore Technologies Pvt. Ltd.", "demo_documents/medcore.pdf"),
    ]
    
    for bidder_name, filepath in demo_files:
        if bidder_name not in bid_map:
            print(f"Skipping {bidder_name} - not found in database.")
            continue
            
        bid_id = bid_map[bidder_name]
        print(f"\n--- Testing {bidder_name} ---")
        print(f"Uploading {filepath}...")
        
        try:
            doc_info = upload_document(bid_id, filepath)
            print(f"Upload initiated: Doc ID {doc_info['id']}")
            
            print("Waiting for background processing to complete...")
            final_status = wait_for_processing(bid_id, doc_info['id'])
            
            if not final_status:
                print("Timed out waiting for processing.")
            else:
                docs = final_status.get("documents", [])
                stage = docs[0].get("processing_stage") if docs else "N/A"
                print(f"Final Processing Stage: {stage}")
                
                # Refetch bid to get full details
                bid_resp = requests.get(f"{API_URL}/bids/{bid_id}")
                bid_full = bid_resp.json()
                
                print(f"Result Status: {bid_full.get('status')} | Risk: {bid_full.get('risk')} | Score: {bid_full.get('score')}")
                
                print("Rules Evaluated:")
                for r in bid_full.get("rules", []):
                    ext_val = str(r.get('extracted_value')).encode('ascii', errors='replace').decode('ascii')
                    print(f"  - {r.get('rule_id')}: {r.get('result')} (Extracted: '{ext_val}')")
                    
        except Exception as e:
            print(f"Error testing {bidder_name}: {e}")

if __name__ == "__main__":
    test_golden_demo()
