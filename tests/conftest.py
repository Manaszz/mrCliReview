"""
Pytest configuration and fixtures
"""

import pytest
import os
from unittest.mock import patch, MagicMock


# Set environment variables BEFORE any imports
def pytest_configure(config):
    """Configure test environment before collection starts"""
    test_env = {
        "MODEL_API_URL": "https://test-api.example.com/v1",
        "MODEL_API_KEY": "test-api-key-12345",
        "DEEPSEEK_MODEL_NAME": "deepseek-v3.1-terminus",
        "QWEN3_MODEL_NAME": "qwen3-coder-32b",
        "DEFAULT_CLI_AGENT": "CLINE",
        "CLINE_PARALLEL_TASKS": "5",
        "QWEN_PARALLEL_TASKS": "3",
        "REVIEW_TIMEOUT": "300",
        "GITLAB_URL": "https://test-gitlab.example.com",
        "GITLAB_TOKEN": "test-gitlab-token-12345",
        "WORK_DIR": "/tmp/test_review",
        "PROMPTS_PATH": "prompts",
        "DEFAULT_RULES_PATH": "rules/java-spring-boot",
        "DEFAULT_LANGUAGE": "java",
        "VERSION": "2.0.0-test",
        "LOG_LEVEL": "INFO",
        "CONFLUENCE_RULES_ENABLED": "false",
        "MCP_RAG_ENABLED": "false"
    }
    
    # Apply test environment
    os.environ.update(test_env)
    
    # Clear settings cache if already loaded
    try:
        from app.config import get_settings
        get_settings.cache_clear()
    except (ImportError, AttributeError):
        pass  # Not yet imported or no cache


@pytest.fixture
def mock_cli_availability():
    """Mock CLI availability checks"""
    with patch('shutil.which', return_value='/usr/local/bin/cli'):
        yield


@pytest.fixture
def mock_subprocess():
    """Mock subprocess calls"""
    from unittest.mock import AsyncMock
    
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(b"", b""))
    
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        yield mock_process


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"status": "ok"})
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        yield mock_client
