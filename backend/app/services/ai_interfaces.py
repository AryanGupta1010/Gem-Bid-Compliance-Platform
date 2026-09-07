from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class DocumentRetrievalService(ABC):
    """
    Interface for visual / multimodal document retrieval.
    Phase 3: Will be implemented via ColPali visual embeddings + pgvector.
    """
    @abstractmethod
    def search(self, query: str, document_ids: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        pass

class FieldExtractionService(ABC):
    """
    Interface for targeted document field extraction.
    Phase 3: Will be implemented via Surya OCR / DocQuery.
    """
    @abstractmethod
    def extract(self, document_id: str, page_number: int, target_field: str, bounding_box: Optional[List[float]] = None) -> Dict[str, Any]:
        pass

class RequirementExtractionService(ABC):
    """
    Interface for extracting structured compliance rules from raw RFP/Tender PDFs.
    Phase 3: Will be implemented via Saul-7B (Legal LLM).
    """
    @abstractmethod
    def extract_requirements(self, tender_document_id: str) -> List[Dict[str, Any]]:
        pass

class ContextualInferenceService(ABC):
    """
    Interface for contextual verification & natural language inference over retrieved evidence clauses.
    Phase 3: Will be implemented via NLI / VLM.
    """
    @abstractmethod
    def evaluate(self, requirement: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
        pass

# --- MOCK IMPLEMENTATIONS FOR PHASE 1 & 2 ---

class MockDocumentRetrievalService(DocumentRetrievalService):
    def search(self, query: str, document_ids: List[str], top_k: int = 3) -> List[Dict[str, Any]]:
        return [
            {
                "document_id": doc_id,
                "page_number": 1,
                "score": 0.95,
                "bounding_box": [0.1, 0.2, 0.9, 0.5],
                "snippet": f"Found section relevant to '{query}' in document {doc_id}"
            }
            for doc_id in document_ids[:top_k]
        ]

class MockFieldExtractionService(FieldExtractionService):
    def extract(self, document_id: str, page_number: int, target_field: str, bounding_box: Optional[List[float]] = None) -> Dict[str, Any]:
        return {
            "field": target_field,
            "value": "Extracted value placeholder",
            "confidence": 0.99,
            "page_number": page_number,
            "bounding_box": bounding_box or [0.1, 0.1, 0.8, 0.3]
        }

class MockRequirementExtractionService(RequirementExtractionService):
    def extract_requirements(self, tender_document_id: str) -> List[Dict[str, Any]]:
        return [
            {
                "name": "Minimum Annual Turnover",
                "rule_type": "NUMERIC",
                "operator": "GTE",
                "expected_value": "10",
                "unit": "Cr",
                "severity": "HIGH",
                "mandatory": True
            }
        ]

class MockContextualInferenceService(ContextualInferenceService):
    def evaluate(self, requirement: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "entailment": "ENTAILS",
            "confidence": 0.98,
            "explanation": "Evidence strictly conforms to required tender specification."
        }

mock_retrieval_service = MockDocumentRetrievalService()
mock_extraction_service = MockFieldExtractionService()
mock_requirement_service = MockRequirementExtractionService()
mock_inference_service = MockContextualInferenceService()
