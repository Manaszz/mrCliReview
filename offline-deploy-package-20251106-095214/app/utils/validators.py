from app.config import settings
from app.models import BatchReviewRequest


def validate_code_length(code: str):
    if len(code) > settings.max_code_length:
        raise ValueError(f"Code length exceeds maximum allowed: {settings.max_code_length}")
    if not code.strip():
        raise ValueError("Code cannot be empty")


def validate_batch_request(request: BatchReviewRequest):
    if not request.files:
        raise ValueError("No files provided for review")

    if len(request.files) > 50:
        raise ValueError("Maximum 50 files allowed per batch")

    for file in request.files:
        validate_code_length(file.code)
        if not file.path:
            raise ValueError("File path is required")


