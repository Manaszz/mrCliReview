from pydantic import BaseModel, Field
from typing import Optional


class ErrorResponse(BaseModel):
    """Стандартный ответ об ошибке"""
    error: str = Field(..., description="Описание ошибки")
    detail: Optional[str] = Field(None, description="Детали ошибки")


class SuccessResponse(BaseModel):
    """Стандартный ответ об успехе"""
    success: bool = True
    message: str


