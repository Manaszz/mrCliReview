"""
Tests for QwenCodeCLIManager
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from app.services.qwen_code_cli_manager import QwenCodeCLIManager
from app.models import ReviewType, CLIAgent


@pytest.fixture
def qwen_manager(tmp_path):
    """Create QwenCodeCLIManager instance"""
    # Mock system prompt loading
    with patch('builtins.open', mock_open(read_data="")):
        with patch('pathlib.Path.exists', return_value=False):
            manager = QwenCodeCLIManager(
                model_api_url="https://api.example.com/v1",
                model_name="qwen3-coder-32b",
                api_key="test-api-key",
                parallel_tasks=3,
                timeout_seconds=300,
                system_prompt_path="prompts/system_prompt.md"
            )
    return manager


def test_agent_type(qwen_manager):
    """Test that agent type is QWEN_CODE"""
    assert qwen_manager.agent_type == CLIAgent.QWEN_CODE


def test_cli_command(qwen_manager):
    """Test that CLI command is 'qwen-code'"""
    assert qwen_manager.cli_command == "qwen-code"


def test_parallel_tasks(qwen_manager):
    """Test that parallel tasks is set to 3"""
    assert qwen_manager.parallel_tasks == 3


@pytest.mark.asyncio
async def test_execute_review_success(qwen_manager, tmp_path):
    """Test successful review execution"""
    repo_path = str(tmp_path / "test_repo")
    Path(repo_path).mkdir(exist_ok=True)
    
    # Mock result
    mock_result = {
        "review_type": "SECURITY_AUDIT",
        "issues": [
            {
                "file": "Security.java",
                "line": 20,
                "severity": "CRITICAL",
                "category": "SQL Injection",
                "message": "SQL injection vulnerability",
                "suggestion": "Use prepared statements"
            }
        ],
        "summary": {"total_issues": 1}
    }
    
    # Mock subprocess
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
    
    # Mock file operations
    with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('builtins.open', mock_open(read_data=json.dumps(mock_result))), \
         patch('os.unlink'):
        
        result = await qwen_manager.execute_review(
            review_type=ReviewType.SECURITY_AUDIT,
            repo_path=repo_path,
            prompt_content="Test prompt {repo_path}",
            custom_rules=None
        )
    
    assert result["review_type"] == "SECURITY_AUDIT"
    assert len(result["issues"]) == 1


def test_get_review_type_distribution_all(qwen_manager):
    """Test review type distribution for ALL"""
    review_types = [ReviewType.ALL]
    distribution = qwen_manager.get_review_type_distribution(review_types)
    
    # Qwen has 3 parallel tasks
    assert len(distribution) == 3
    assert ReviewType.ERROR_DETECTION in distribution[0]
    assert ReviewType.SECURITY_AUDIT in distribution[0]


def test_get_review_type_distribution_custom(qwen_manager):
    """Test review type distribution for custom types"""
    review_types = [
        ReviewType.ERROR_DETECTION,
        ReviewType.BEST_PRACTICES
    ]
    distribution = qwen_manager.get_review_type_distribution(review_types)
    
    # Should distribute across available slots
    assert len(distribution) == 2
    total_types = sum(len(group) for group in distribution)
    assert total_types == 2


@pytest.mark.asyncio
async def test_check_availability_success(qwen_manager):
    """Test CLI availability check success"""
    with patch('shutil.which', return_value='/usr/bin/qwen-code'):
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"qwen-code version 0.5.0\n", b""))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            available = await qwen_manager.check_availability()
            assert available is True


