"""
Contextual Reasoning Service (NLI).

CRITICAL RULE: NO SILENT AI FALLBACKS IN LIVE MODE.
Calls dedicated NLI microservice for contextual clause understanding.
"""
import logging
import requests
from typing import Dict, Any
from datetime import datetime, timezone

from app.config import settings
from app.services.exceptions import AIModelUnavailableError

logger = logging.getLogger(__name__)

class NLIService:
    def __init__(self):
        self.endpoint = settings.NLI_URL

    def evaluate(self, premise: str, hypothesis: str) -> Dict[str, Any]:
        """
        Evaluate if evidence (premise) entails, contradicts, or is neutral towards requirement (hypothesis).
        """
        if settings.AI_MODE != 'live':
            # Local heuristic for test mode
            p = premise.lower()
            if "conflict" in p or "unreadable" in p:
                return {"label": "NEUTRAL", "confidence": 0.60, "model": "NLI (Test Heuristic)", "model_version": "test"}
            if "mismatch" in p or "missing" in p or "debarred" in p:
                return {"label": "CONTRADICTION", "confidence": 0.92, "model": "NLI (Test Heuristic)", "model_version": "test"}
            return {"label": "ENTAILMENT", "confidence": 0.95, "model": "NLI (Test Heuristic)", "model_version": "test"}

        try:
            resp = requests.post(
                f"{self.endpoint}/evaluate",
                json={"premise": premise, "hypothesis": hypothesis},
                timeout=settings.MODEL_TIMEOUT
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "label": data.get("label", "NEUTRAL"),
                    "confidence": data.get("confidence", 0.90),
                    "scores": data.get("scores", {}),
                    "model": data.get("model_name", "cross-encoder/nli-deberta-v3-base"),
                    "model_version": data.get("model_version", "v1.0"),
                    "inference_timestamp": data.get("inference_timestamp", datetime.now(timezone.utc).isoformat())
                }
            else:
                raise AIModelUnavailableError("NLI", f"NLI service returned HTTP {resp.status_code}: {resp.text}")
        except requests.exceptions.RequestException as exc:
            logger.error("NLI reasoning service unreachable: %s", exc)
            raise AIModelUnavailableError("NLI", f"NLI reasoning service is unreachable at {self.endpoint}: {exc}")

def get_nli_service() -> NLIService:
    return NLIService()
