"""
Tests for ReviewService
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from app.services.review_service import ReviewService
from app.services.cline_cli_manager import ClineCLIManager
from app.services.qwen_code_cli_manager import QwenCodeCLIManager
from app.services.custom_rules_loader import CustomRulesLoader
from app.models import (
    ReviewRequest,
    ReviewType,
    CLIAgent,
    Language,
    IssueSeverity
)


@pytest.fixture
def mock_cline_manager():
    """Create mock ClineCLIManager"""
    manager = MagicMock(spec=ClineCLIManager)
    manager.agent_type = CLIAgent.CLINE
    manager.execute_parallel_reviews = AsyncMock(return_value=[
        {
            "review_type": "ERROR_DETECTION",
            "issues": [
                {
                    "file": "Test.java",
                    "line": 10,
                    "severity": "HIGH",
                    "category": "NullPointer",
                    "message": "Possible NPE",
                    "suggestion": "Add null check",
                    "auto_fixable": True
                }
            ],
            "summary": {"total_issues": 1}
        }
    ])
    manager.check_availability = AsyncMock(return_value=True)
    manager.test_model_connection = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_qwen_manager():
    """Create mock QwenCodeCLIManager"""
    manager = MagicMock(spec=QwenCodeCLIManager)
    manager.agent_type = CLIAgent.QWEN_CODE
    manager.execute_parallel_reviews = AsyncMock(return_value=[])
    manager.check_availability = AsyncMock(return_value=True)
    manager.test_model_connection = AsyncMock(return_value=True)
    return manager


@pytest.fixture
def mock_rules_loader():
    """Create mock CustomRulesLoader"""
    loader = MagicMock(spec=CustomRulesLoader)
    loader.load_rules = MagicMock(return_value={
        "error_detection": "Error rules",
        "best_practices": "Best practices rules"
    })
    loader.get_combined_rules_content = MagicMock(return_value="Combined rules content")
    return loader


@pytest.fixture
def review_service(mock_cline_manager, mock_qwen_manager, mock_rules_loader, tmp_path):
    """Create ReviewService instance"""
    prompts_path = tmp_path / "prompts"
    prompts_path.mkdir()
    
    # Create prompt directories
    (prompts_path / "cline").mkdir()
    (prompts_path / "qwen").mkdir()
    (prompts_path / "additional").mkdir()
    
    # Create a test prompt file
    prompt_file = prompts_path / "cline" / "error_detection.md"
    prompt_file.write_text("# Error Detection\nTest prompt {repo_path} {language}")
    
    service = ReviewService(
        cline_manager=mock_cline_manager,
        qwen_manager=mock_qwen_manager,
        rules_loader=mock_rules_loader,
        prompts_base_path=str(prompts_path)
    )
    return service


@pytest.mark.asyncio
async def test_execute_review_success(review_service, mock_cline_manager, tmp_path):
    """Test successful review execution"""
    request = ReviewRequest(
        agent=CLIAgent.CLINE,
        review_types=[ReviewType.ERROR_DETECTION],
        project_id=123,
        merge_request_iid=1,
        language=Language.JAVA
    )
    
    repo_path = str(tmp_path / "test_repo")
    
    result = await review_service.execute_review(request, repo_path)
    
    assert result.agent == CLIAgent.CLINE
    assert result.summary.total_issues == 1
    assert len(result.issues) == 1
    assert result.issues[0].severity == IssueSeverity.HIGH
    
    # Verify managers were called
    mock_cline_manager.execute_parallel_reviews.assert_called_once()


@pytest.mark.asyncio
async def test_execute_review_with_all_types(review_service, mock_cline_manager, tmp_path):
    """Test review with ALL review type"""
    request = ReviewRequest(
        agent=CLIAgent.CLINE,
        review_types=[ReviewType.ALL],
        project_id=123,
        merge_request_iid=1,
        language=Language.JAVA
    )
    
    repo_path = str(tmp_path / "test_repo")
    
    result = await review_service.execute_review(request, repo_path)
    
    # Verify that ALL was expanded to specific types
    call_args = mock_cline_manager.execute_parallel_reviews.call_args[1]
    review_types = call_args["review_types"]
    assert len(review_types) > 1
    assert ReviewType.ERROR_DETECTION in review_types
    assert ReviewType.BEST_PRACTICES in review_types


@pytest.mark.asyncio
async def test_execute_review_qwen_agent(review_service, mock_qwen_manager, tmp_path):
    """Test review with Qwen Code agent"""
    request = ReviewRequest(
        agent=CLIAgent.QWEN_CODE,
        review_types=[ReviewType.SECURITY_AUDIT],
        project_id=123,
        merge_request_iid=1,
        language=Language.JAVA
    )
    
    repo_path = str(tmp_path / "test_repo")
    
    result = await review_service.execute_review(request, repo_path)
    
    assert result.agent == CLIAgent.QWEN_CODE
    mock_qwen_manager.execute_parallel_reviews.assert_called_once()


def test_get_cli_manager_cline(review_service):
    """Test getting Cline CLI manager"""
    manager = review_service._get_cli_manager(CLIAgent.CLINE)
    assert manager.agent_type == CLIAgent.CLINE


def test_get_cli_manager_qwen(review_service):
    """Test getting Qwen Code CLI manager"""
    manager = review_service._get_cli_manager(CLIAgent.QWEN_CODE)
    assert manager.agent_type == CLIAgent.QWEN_CODE


def test_get_cli_manager_invalid(review_service):
    """Test getting invalid CLI manager"""
    with pytest.raises(ValueError, match="Unknown CLI agent"):
        review_service._get_cli_manager("INVALID_AGENT")


def test_expand_review_types_all(review_service):
    """Test expanding ALL review type"""
    review_types = [ReviewType.ALL]
    expanded = review_service._expand_review_types(review_types)
    
    assert len(expanded) > 1
    assert ReviewType.ERROR_DETECTION in expanded
    assert ReviewType.BEST_PRACTICES in expanded
    assert ReviewType.SECURITY_AUDIT in expanded
    assert ReviewType.ALL not in expanded


def test_expand_review_types_specific(review_service):
    """Test expanding specific review types"""
    review_types = [ReviewType.ERROR_DETECTION, ReviewType.SECURITY_AUDIT]
    expanded = review_service._expand_review_types(review_types)
    
    assert expanded == review_types


def test_load_prompts_success(review_service, tmp_path):
    """Test loading prompts successfully"""
    prompts = review_service._load_prompts(
        agent=CLIAgent.CLINE,
        review_types=[ReviewType.ERROR_DETECTION]
    )
    
    assert ReviewType.ERROR_DETECTION in prompts
    assert "Test prompt" in prompts[ReviewType.ERROR_DETECTION]


def test_load_prompts_fallback(review_service):
    """Test loading prompts with fallback"""
    prompts = review_service._load_prompts(
        agent=CLIAgent.CLINE,
        review_types=[ReviewType.ARCHITECTURE]  # File doesn't exist
    )
    
    assert ReviewType.ARCHITECTURE in prompts
    # Should contain fallback prompt
    assert "ARCHITECTURE" in prompts[ReviewType.ARCHITECTURE]


def test_get_fallback_prompt(review_service):
    """Test generating fallback prompt"""
    prompt = review_service._get_fallback_prompt(ReviewType.SECURITY_AUDIT)
    
    assert "SECURITY_AUDIT" in prompt
    assert "{repo_path}" in prompt
    assert "{language}" in prompt
    assert "json" in prompt.lower()


@pytest.mark.asyncio
async def test_health_check_success(review_service, mock_cline_manager, mock_qwen_manager):
    """Test health check success"""
    health = await review_service.health_check()
    
    assert health["cline_available"] is True
    assert health["cline_model_connected"] is True
    assert health["qwen_available"] is True
    assert health["qwen_model_connected"] is True
    assert health["model_api_connected"] is True


@pytest.mark.asyncio
async def test_health_check_partial_failure(review_service, mock_cline_manager, mock_qwen_manager):
    """Test health check with partial failure"""
    mock_cline_manager.check_availability = AsyncMock(return_value=False)
    
    health = await review_service.health_check()
    
    assert health["cline_available"] is False
    assert health["qwen_available"] is True
    assert health["model_api_connected"] is True  # Qwen is still connected


def test_aggregate_results_success(review_service):
    """Test aggregating review results"""
    raw_results = [
        {
            "review_type": "ERROR_DETECTION",
            "issues": [
                {
                    "file": "Test.java",
                    "line": 10,
                    "severity": "CRITICAL",
                    "category": "Bug",
                    "message": "Critical bug",
                    "suggestion": "Fix it",
                    "auto_fixable": True
                }
            ],
            "refactoring_suggestions": [],
            "documentation": []
        },
        {
            "review_type": "SECURITY_AUDIT",
            "issues": [
                {
                    "file": "Security.java",
                    "line": 20,
                    "severity": "HIGH",
                    "category": "Security",
                    "message": "Security issue",
                    "suggestion": "Fix security",
                    "auto_fixable": False
                }
            ],
            "refactoring_suggestions": [],
            "documentation": []
        }
    ]
    
    result = review_service._aggregate_results(
        raw_results=raw_results,
        agent=CLIAgent.CLINE,
        start_time=0
    )
    
    assert result.summary.total_issues == 2
    assert result.summary.critical == 1
    assert result.summary.high == 1
    assert result.summary.auto_fixable_count == 1
    assert len(result.issues) == 2
