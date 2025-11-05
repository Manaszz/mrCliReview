"""
Tests for GitLabService
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.gitlab_service import GitLabService


@pytest.fixture
def gitlab_service():
    """Create GitLabService instance"""
    return GitLabService(
        gitlab_url="https://gitlab.example.com",
        gitlab_token="test-token-123"
    )


def test_init(gitlab_service):
    """Test GitLabService initialization"""
    assert gitlab_service.gitlab_url == "https://gitlab.example.com"
    assert gitlab_service.api_url == "https://gitlab.example.com/api/v4"
    assert gitlab_service.headers["Private-Token"] == "test-token-123"


@pytest.mark.asyncio
async def test_get_merge_request_success(gitlab_service):
    """Test getting merge request successfully"""
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={
        "id": 12345,
        "iid": 1,
        "title": "Test MR",
        "source_branch": "feature-branch",
        "target_branch": "main"
    })
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await gitlab_service.get_merge_request(project_id=123, mr_iid=1)
        
        assert result["id"] == 12345
        assert result["title"] == "Test MR"
        assert result["source_branch"] == "feature-branch"


@pytest.mark.asyncio
async def test_get_project_success(gitlab_service):
    """Test getting project successfully"""
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={
        "id": 123,
        "name": "test-project",
        "http_url_to_repo": "https://gitlab.example.com/group/project.git"
    })
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await gitlab_service.get_project(project_id=123)
        
        assert result["id"] == 123
        assert result["name"] == "test-project"


@pytest.mark.asyncio
async def test_post_mr_comment_success(gitlab_service):
    """Test posting comment to MR"""
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={"id": 999, "body": "Test comment"})
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await gitlab_service.post_mr_comment(
            project_id=123,
            mr_iid=1,
            comment="Test comment"
        )
        
        assert result["id"] == 999
        assert result["body"] == "Test comment"


@pytest.mark.asyncio
async def test_create_merge_request_success(gitlab_service):
    """Test creating merge request"""
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={
        "iid": 2,
        "title": "Fix MR",
        "web_url": "https://gitlab.example.com/project/-/merge_requests/2"
    })
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await gitlab_service.create_merge_request(
            project_id=123,
            source_branch="fix/mr-1-fixes",
            target_branch="feature-branch",
            title="Fix MR",
            description="Fixes for MR",
            labels=["ai-review", "fixes"]
        )
        
        assert result["iid"] == 2
        assert result["title"] == "Fix MR"


@pytest.mark.asyncio
async def test_get_mr_changes_success(gitlab_service):
    """Test getting MR changes"""
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={
        "changes": [
            {"new_path": "src/Test.java", "old_path": "src/Test.java"},
            {"new_path": "src/Test2.java", "old_path": "src/Test2.java"}
        ]
    })
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await gitlab_service.get_mr_changes(project_id=123, mr_iid=1)
        
        assert len(result) == 2
        assert result[0]["new_path"] == "src/Test.java"


@pytest.mark.asyncio
async def test_test_connection_success(gitlab_service):
    """Test GitLab connection test success"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = MagicMock(return_value={"version": "15.0.0"})
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await gitlab_service.test_connection()
        
        assert result is True


@pytest.mark.asyncio
async def test_test_connection_failure(gitlab_service):
    """Test GitLab connection test failure"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("Connection error"))
        
        result = await gitlab_service.test_connection()
        
        assert result is False


def test_get_clone_url(gitlab_service):
    """Test getting clone URL with authentication"""
    project_data = {
        "http_url_to_repo": "https://gitlab.example.com/group/project.git"
    }
    
    clone_url = gitlab_service.get_clone_url(project_data)
    
    assert "oauth2:test-token-123@" in clone_url
    assert "gitlab.example.com/group/project.git" in clone_url


def test_get_clone_url_missing(gitlab_service):
    """Test getting clone URL with missing URL"""
    project_data = {}
    
    with pytest.raises(ValueError, match="No HTTP clone URL"):
        gitlab_service.get_clone_url(project_data)


@pytest.mark.asyncio
async def test_commit_file_changes_success(gitlab_service):
    """Test committing file changes"""
    mock_response = MagicMock()
    mock_response.json = MagicMock(return_value={"id": "abc123"})
    mock_response.raise_for_status = MagicMock()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        result = await gitlab_service.commit_file_changes(
            project_id=123,
            branch="feature-branch",
            commit_message="Test commit",
            files=[
                {"action": "update", "file_path": "README.md", "content": "Updated"}
            ]
        )
        
        assert result["id"] == "abc123"
