import sys
import os
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from app.config import settings

def test_service(name: str, url: str, expected_models: list = None):
    try:
        resp = requests.get(f"{url}/health", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"✅ {name} is ONLINE. Model: {data.get('model_name', 'Unknown')}, Status: {data.get('status')}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ {name} is OFFLINE or unreachable at {url}. Error: {e}")
        return False

def run_tests():
    logger.info("Starting AI Stack Verification...")
    
    services = [
        ("ColPali", settings.COLPALI_URL),
        ("Surya OCR", settings.SURYA_URL),
        ("Saul LM", settings.SAUL_URL),
        ("NLI Context", settings.NLI_URL),
    ]
    
    all_passed = True
    for name, url in services:
        passed = test_service(name, url)
        if not passed:
            all_passed = False
            
    if all_passed:
        logger.info("🎉 All AI Model Services are verified and responding.")
        sys.exit(0)
    else:
        logger.error("⚠️ Some AI Model Services failed verification. Check docker-compose logs.")
        sys.exit(1)

if __name__ == "__main__":
    # Ensure run from backend root
    if not os.path.exists("app/config.py"):
        logger.error("Run this script from the backend directory.")
        sys.exit(1)
    run_tests()
