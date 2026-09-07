from fastapi import HTTPException, status
from typing import Any, Optional, Dict

class GeMException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "GENERIC_ERROR",
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}

class NotFoundException(GeMException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with ID '{identifier}' not found.",
            error_code="RESOURCE_NOT_FOUND",
            extra={"resource": resource, "identifier": str(identifier)}
        )

class ValidationException(GeMException):
    def __init__(self, message: str, field_errors: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
            error_code="VALIDATION_ERROR",
            extra={"field_errors": field_errors or {}}
        )

class UnauthorizedException(GeMException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )

class ForbiddenException(GeMException):
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )
