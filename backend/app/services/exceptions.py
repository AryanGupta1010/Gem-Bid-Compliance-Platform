"""
Exceptions for ProcureGuard AI Service Pipelines.
"""

class AIModelUnavailableError(Exception):
    """Raised when an AI model service (ColPali, Surya, Saul, NLI) is unreachable or fails."""
    def __init__(self, service_name: str, message: str):
        self.service_name = service_name
        self.message = message
        super().__init__(f"[{service_name.upper()}_UNAVAILABLE] {message}")

class RequirementExtractionFailedError(Exception):
    """Raised when tender requirement extraction fails and cannot be recovered."""
    pass
