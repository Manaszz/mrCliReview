"""
Tests for CLI Managers (Cline and Qwen)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from app.services.base_cli_manager import BaseCLIManager
from app.services.cline_cli_manager import ClineCLIManager
from app.services.qwen_code_cli_manager import QwenCodeCLIManager
from app.models import ReviewType, CLIAgent


@pytest.fixture
def cline_manager():
    """Create Cline CLI manager"""
    with patch('app.services.base_cli_manager.BaseCLIManager._load_system_prompt', return_value="System prompt"):
        return ClineCLIManager(
            model_api_url="https://api.example.com/v1",
            model_name="deepseek-v3.1",
            api_key="test-key",
            parallel_tasks=5,
            timeout_seconds=300
        )


@pytest.fixture
def qwen_manager():
    """Create Qwen Code CLI manager"""
    with patch('app.services.base_cli_manager.BaseCLIManager._load_system_prompt', return_value="System prompt"):
        return QwenCodeCLIManager(
            model_api_url="https://api.example.com/v1",
            model_name="qwen3-coder-32b",
            api_key="test-key",
            parallel_tasks=3,
            timeout_seconds=300
        )


def test_cline_agent_type(cline_manager):
    """Test Cline agent type property"""
    assert cline_manager.agent_type == CLIAgent.CLINE


def test_cline_cli_command(cline_manager):
    """Test Cline CLI command"""
    assert cline_manager.cli_command == "cline"


def test_qwen_agent_type(qwen_manager):
    """Test Qwen agent type property"""
    assert qwen_manager.agent_type == CLIAgent.QWEN_CODE


def test_qwen_cli_command(qwen_manager):
    """Test Qwen CLI command"""
    assert qwen_manager.cli_command == "qwen-code"


@pytest.mark.asyncio
async def test_check_availability_success(cline_manager):
    """Test CLI availability check success"""
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"cline v1.0.0\n", b""))
    
    with patch('shutil.which', return_value="/usr/bin/cline"):
        with patch('asyncio.create_subprocess_exec', return_value=mock_process):
            result = await cline_manager.check_availability()
    
    assert result is True


@pytest.mark.asyncio
async def test_check_availability_not_found(cline_manager):
    """Test CLI availability check when not found"""
    with patch('shutil.which', return_value=None):
        result = await cline_manager.check_availability()
    
    assert result is False


@pytest.mark.asyncio
async def test_check_availability_timeout(cline_manager):
    """Test CLI availability check timeout"""
    with patch('shutil.which', return_value="/usr/bin/cline"):
        with patch('asyncio.create_subprocess_exec', side_effect=AsyncMock()):
            with patch('asyncio.wait_for', side_effect=TimeoutError):
                result = await cline_manager.check_availability()
    
    assert result is False


@pytest.mark.asyncio
async def test_test_model_connection_success(cline_manager):
    """Test model API connection check success"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await cline_manager.test_model_connection()
    
    assert result is True


@pytest.mark.asyncio
async def test_test_model_connection_failure(cline_manager):
    """Test model API connection check failure"""
    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=Exception("Connection failed"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()
    
    with patch('httpx.AsyncClient', return_value=mock_client):
        result = await cline_manager.test_model_connection()
    
    assert result is False


@pytest.mark.asyncio
async def test_execute_review_cline(cline_manager, tmp_path):
    """Test executing review with Cline CLI"""
    # Mock subprocess execution
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))
    
    # Mock output file with JSON result
    output_json = {
        "review_type": "ERROR_DETECTION",
        "issues": [],
        "summary": {"total_issues": 0}
    }
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = str(tmp_path / "test.json")
            with patch('builtins.open', mock_open(read_data='{"issues": [], "summary": {"total_issues": 0}}')):
                result = await cline_manager.execute_review(
                    review_type=ReviewType.ERROR_DETECTION,
                    repo_path=str(tmp_path),
                    prompt_content="Test prompt"
                )
    
    assert "issues" in result or "summary" in result


@pytest.mark.asyncio
async def test_execute_review_timeout(cline_manager, tmp_path):
    """Test review execution timeout"""
    mock_process = AsyncMock()
    mock_process.kill = MagicMock()
    mock_process.wait = AsyncMock()
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('asyncio.wait_for', side_effect=TimeoutError):
            with patch('tempfile.NamedTemporaryFile') as mock_temp:
                mock_temp.return_value.__enter__.return_value.name = str(tmp_path / "test.json")
                
                with pytest.raises(TimeoutError):
                    await cline_manager.execute_review(
                        review_type=ReviewType.ERROR_DETECTION,
                        repo_path=str(tmp_path),
                        prompt_content="Test prompt"
                    )


@pytest.mark.asyncio
async def test_execute_parallel_reviews(cline_manager, tmp_path):
    """Test parallel review execution"""
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))
    
    prompts = {
        ReviewType.ERROR_DETECTION: "Error detection prompt",
        ReviewType.BEST_PRACTICES: "Best practices prompt"
    }
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = str(tmp_path / "test.json")
            with patch('builtins.open', mock_open(read_data='{"issues": [], "summary": {"total_issues": 0}}')):
                results = await cline_manager.execute_parallel_reviews(
                    review_types=[ReviewType.ERROR_DETECTION, ReviewType.BEST_PRACTICES],
                    repo_path=str(tmp_path),
                    prompts=prompts
                )
    
    assert len(results) == 2


def test_substitute_prompt_variables(cline_manager):
    """Test prompt variable substitution"""
    template = "Repo: {repo_path}, Lang: {language}, Rules: {custom_rules}"
    
    result = cline_manager._substitute_prompt_variables(
        prompt_template=template,
        repo_path="/tmp/repo",
        language="java",
        custom_rules="Custom rules here"
    )
    
    assert "/tmp/repo" in result
    assert "java" in result
    assert "Custom rules here" in result


def test_parse_cli_output_valid_json(cline_manager):
    """Test parsing valid JSON from CLI output"""
    output = '{"issues": [], "summary": {"total_issues": 0}}'
    
    result = cline_manager._parse_cli_output(output)
    
    assert "issues" in result
    assert "summary" in result


def test_parse_cli_output_with_noise(cline_manager):
    """Test parsing JSON with surrounding text"""
    output = 'Some text before\n{"issues": [], "summary": {"total_issues": 0}}\nSome text after'
    
    result = cline_manager._parse_cli_output(output)
    
    assert "issues" in result
    assert "summary" in result


def test_parse_cli_output_invalid(cline_manager):
    """Test parsing invalid JSON"""
    output = "Not valid JSON at all"
    
    with pytest.raises(ValueError, match="No JSON found"):
        cline_manager._parse_cli_output(output)


def test_cline_review_type_distribution(cline_manager):
    """Test Cline review type distribution strategy"""
    distribution = cline_manager.get_review_type_distribution([ReviewType.ALL])
    
    # Cline supports 5 parallel tasks
    assert len(distribution) == 5
    assert ReviewType.ERROR_DETECTION in distribution[0]

