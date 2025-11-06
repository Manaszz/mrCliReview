"""
Dependencies for FastAPI Dependency Injection
"""

from functools import lru_cache
from app.services.review_service import ReviewService
from app.services.cline_cli_manager import ClineCLIManager
from app.services.qwen_code_cli_manager import QwenCodeCLIManager
from app.services.custom_rules_loader import CustomRulesLoader
from app.config import get_settings

settings = get_settings()


@lru_cache()
def get_review_service_instance() -> ReviewService:
    """
    Get singleton ReviewService instance
    
    Returns:
        ReviewService configured with CLI managers and rules loader
    """
    # Initialize CLI managers
    cline_manager = ClineCLIManager(
        model_api_url=settings.MODEL_API_URL,
        model_name=settings.DEEPSEEK_MODEL_NAME,
        api_key=settings.MODEL_API_KEY,
        parallel_tasks=settings.CLINE_PARALLEL_TASKS,
        timeout_seconds=settings.REVIEW_TIMEOUT
    )
    
    qwen_manager = QwenCodeCLIManager(
        model_api_url=settings.MODEL_API_URL,
        model_name=settings.QWEN3_MODEL_NAME,
        api_key=settings.MODEL_API_KEY,
        parallel_tasks=settings.QWEN_PARALLEL_TASKS,
        timeout_seconds=settings.REVIEW_TIMEOUT
    )
    
    # Initialize rules loader
    rules_loader = CustomRulesLoader(
        default_rules_path=settings.DEFAULT_RULES_PATH
    )
    
    # Create ReviewService
    return ReviewService(
        cline_manager=cline_manager,
        qwen_manager=qwen_manager,
        rules_loader=rules_loader,
        prompts_base_path=settings.PROMPTS_PATH
    )


