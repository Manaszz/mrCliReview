"""
Tests for ClineCLIManager
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from app.services.cline_cli_manager import ClineCLIManager
from app.models import ReviewType, CLIAgent


@pytest.fixture
def cline_manager(tmp_path):
    """Create ClineCLIManager instance"""
    # Mock system prompt loading
    with patch('builtins.open', mock_open(read_data="")):
        with patch('pathlib.Path.exists', return_value=False):
            manager = ClineCLIManager(
                model_api_url="https://api.example.com/v1",
                model_name="deepseek-v3.1-terminus",
                api_key="test-api-key",
                parallel_tasks=5,
                timeout_seconds=300,
                system_prompt_path="prompts/system_prompt.md"
            )
    return manager


def test_agent_type(cline_manager):
    """Test that agent type is CLINE"""
    assert cline_manager.agent_type == CLIAgent.CLINE


def test_cli_command(cline_manager):
    """Test that CLI command is 'cline'"""
    assert cline_manager.cli_command == "cline"


def test_parallel_tasks(cline_manager):
    """Test that parallel tasks is set to 5"""
    assert cline_manager.parallel_tasks == 5


@pytest.mark.asyncio
async def test_execute_review_success(cline_manager, tmp_path):
    """Test successful review execution"""
    repo_path = str(tmp_path / "test_repo")
    Path(repo_path).mkdir(exist_ok=True)
    
    # Mock result
    mock_result = {
        "review_type": "ERROR_DETECTION",
        "issues": [
            {
                "file": "Test.java",
                "line": 10,
                "severity": "HIGH",
                "category": "NullPointerException",
                "message": "Possible NPE",
                "suggestion": "Add null check"
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
        
        result = await cline_manager.execute_review(
            review_type=ReviewType.ERROR_DETECTION,
            repo_path=repo_path,
            prompt_content="Test prompt {repo_path} {language}",
            custom_rules="Test rules"
        )
    
    assert result["review_type"] == "ERROR_DETECTION"
    assert len(result["issues"]) == 1
    assert result["summary"]["total_issues"] == 1


@pytest.mark.asyncio
async def test_execute_review_timeout(cline_manager, tmp_path):
    """Test review execution timeout"""
    repo_path = str(tmp_path / "test_repo")
    Path(repo_path).mkdir(exist_ok=True)
    
    # Mock timeout
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError)
    mock_process.kill = MagicMock()
    mock_process.wait = AsyncMock()
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('asyncio.wait_for', side_effect=asyncio.TimeoutError), \
         patch('os.unlink'):
        
        with pytest.raises(TimeoutError, match="Cline CLI timed out"):
            await cline_manager.execute_review(
                review_type=ReviewType.ERROR_DETECTION,
                repo_path=repo_path,
                prompt_content="Test prompt",
                custom_rules=None
            )


@pytest.mark.asyncio
async def test_execute_review_failure(cline_manager, tmp_path):
    """Test review execution failure"""
    repo_path = str(tmp_path / "test_repo")
    Path(repo_path).mkdir(exist_ok=True)
    
    # Mock failure
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(b"", b"CLI error"))
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('os.unlink'):
        
        with pytest.raises(RuntimeError, match="Cline CLI failed"):
            await cline_manager.execute_review(
                review_type=ReviewType.ERROR_DETECTION,
                repo_path=repo_path,
                prompt_content="Test prompt",
                custom_rules=None
            )


def test_get_review_type_distribution_all(cline_manager):
    """Test review type distribution for ALL"""
    review_types = [ReviewType.ALL]
    distribution = cline_manager.get_review_type_distribution(review_types)
    
    # Cline has 5 parallel tasks
    assert len(distribution) == 5
    assert ReviewType.ERROR_DETECTION in distribution[0]
    assert ReviewType.BEST_PRACTICES in distribution[1]


def test_get_review_type_distribution_custom(cline_manager):
    """Test review type distribution for custom types"""
    review_types = [
        ReviewType.ERROR_DETECTION,
        ReviewType.SECURITY_AUDIT,
        ReviewType.PERFORMANCE
    ]
    distribution = cline_manager.get_review_type_distribution(review_types)
    
    # Should distribute across available slots
    assert len(distribution) == 3
    total_types = sum(len(group) for group in distribution)
    assert total_types == 3


@pytest.mark.asyncio
async def test_check_availability_success(cline_manager):
    """Test CLI availability check success"""
    with patch('shutil.which', return_value='/usr/bin/cline'):
        mock_process = AsyncMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"cline version 1.0.0\n", b""))
        
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            available = await cline_manager.check_availability()
            assert available is True


@pytest.mark.asyncio
async def test_check_availability_not_found(cline_manager):
    """Test CLI availability check when CLI not found"""
    with patch('shutil.which', return_value=None):
        available = await cline_manager.check_availability()
        assert available is False


@pytest.mark.asyncio
async def test_test_model_connection_success(cline_manager):
    """Test model API connection success"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        connected = await cline_manager.test_model_connection()
        assert connected is True


@pytest.mark.asyncio
async def test_test_model_connection_failure(cline_manager):
    """Test model API connection failure"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("Connection error"))
        connected = await cline_manager.test_model_connection()
        assert connected is False


