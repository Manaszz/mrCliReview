"""
Tests for API routes
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from app.main import app
from app.models import ReviewResult, ReviewSummary, ReviewType, CLIAgent


client = TestClient(app)


@pytest.fixture
def mock_review_service():
    """Create mock ReviewService"""
    from app.services.review_service import ReviewService
    
    service = MagicMock(spec=ReviewService)
    service.execute_review = AsyncMock(return_value=ReviewResult(
        review_type=ReviewType.ALL,
        agent=CLIAgent.CLINE,
        issues=[],
        refactoring_suggestions=[],
        documentation_additions=[],
        summary=ReviewSummary(
            total_issues=0,
            critical=0,
            high=0,
            medium=0,
            low=0,
            info=0,
            files_analyzed=0,
            auto_fixable_count=0
        ),
        execution_time_seconds=5.0
    ))
    service.health_check = AsyncMock(return_value={
        "cline_available": True,
        "cline_model_connected": True,
        "qwen_available": True,
        "qwen_model_connected": True,
        "model_api_connected": True
    })
    return service


@pytest.fixture
def mock_gitlab_service():
    """Create mock GitLabService"""
    from app.services.gitlab_service import GitLabService
    
    service = MagicMock(spec=GitLabService)
    service.get_merge_request = AsyncMock(return_value={
        "id": 12345,
        "iid": 1,
        "source_branch": "feature-branch",
        "target_branch": "main",
        "title": "Test MR"
    })
    service.get_project = AsyncMock(return_value={
        "id": 123,
        "http_url_to_repo": "https://gitlab.example.com/project.git"
    })
    service.get_clone_url = MagicMock(return_value="https://oauth2:token@gitlab.example.com/project.git")
    service.post_mr_comment = AsyncMock(return_value={"id": 999})
    service.test_connection = AsyncMock(return_value=True)
    return service


@pytest.fixture
def mock_git_manager():
    """Create mock GitRepositoryManager"""
    from app.services.git_repository_manager import GitRepositoryManager
    
    manager = MagicMock(spec=GitRepositoryManager)
    manager.clone_repository = AsyncMock(return_value="/tmp/repo-123-mr-1")
    manager.cleanup_repository = AsyncMock()
    return manager


def test_health_check_endpoint_with_mocks(mock_review_service, mock_gitlab_service):
    """Test detailed health check endpoint with mocks"""
    with patch('app.api.routes.get_review_service', return_value=mock_review_service), \
         patch('app.api.routes.get_gitlab_service', return_value=mock_gitlab_service):
        
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["cline_available"] is True
        assert data["qwen_available"] is True
        assert data["model_api_connected"] is True
        assert data["gitlab_connected"] is True


def test_validate_mr_success(mock_gitlab_service):
    """Test MR validation success"""
    mock_gitlab_service.get_merge_request = AsyncMock(return_value={
        "id": 12345,
        "iid": 1,
        "title": "PROJECT-123: Test feature",
        "description": "This is a detailed description that is more than 50 characters long and provides context"
    })
    
    with patch('app.api.routes.get_gitlab_service', return_value=mock_gitlab_service):
        response = client.post("/api/v1/validate-mr", json={
            "project_id": 123,
            "merge_request_iid": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["jira_ticket"] == "PROJECT-123"
        assert data["completeness_score"] == 100


def test_validate_mr_missing_jira(mock_gitlab_service):
    """Test MR validation with missing JIRA ticket"""
    mock_gitlab_service.get_merge_request = AsyncMock(return_value={
        "id": 12345,
        "iid": 1,
        "title": "Test feature",  # No JIRA ticket
        "description": "This is a detailed description that is more than 50 characters long"
    })
    
    with patch('app.api.routes.get_gitlab_service', return_value=mock_gitlab_service):
        response = client.post("/api/v1/validate-mr", json={
            "project_id": 123,
            "merge_request_iid": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "Missing JIRA ticket" in data["errors"][0]


def test_validate_mr_short_description(mock_gitlab_service):
    """Test MR validation with short description"""
    mock_gitlab_service.get_merge_request = AsyncMock(return_value={
        "id": 12345,
        "iid": 1,
        "title": "PROJECT-123: Test",
        "description": "Short"  # Too short
    })
    
    with patch('app.api.routes.get_gitlab_service', return_value=mock_gitlab_service):
        response = client.post("/api/v1/validate-mr", json={
            "project_id": 123,
            "merge_request_iid": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "Description too short" in data["errors"][0]


def test_validate_mr_placeholder_warning(mock_gitlab_service):
    """Test MR validation with placeholder text"""
    mock_gitlab_service.get_merge_request = AsyncMock(return_value={
        "id": 12345,
        "iid": 1,
        "title": "PROJECT-123: Test feature",
        "description": "This is a detailed description with TODO: add more details here"
    })
    
    with patch('app.api.routes.get_gitlab_service', return_value=mock_gitlab_service):
        response = client.post("/api/v1/validate-mr", json={
            "project_id": 123,
            "merge_request_iid": 1
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True  # Still valid, but has warning
        assert len(data["warnings"]) > 0
        assert "placeholder" in data["warnings"][0].lower()


def test_generate_review_comment_passed():
    """Test generating review comment for passed review"""
    from app.api.routes import generate_review_comment
    from datetime import datetime
    
    result = ReviewResult(
        review_type=ReviewType.ALL,
        agent=CLIAgent.CLINE,
        issues=[],
        refactoring_suggestions=[],
        documentation_additions=[],
        summary=ReviewSummary(
            total_issues=0,
            critical=0,
            high=0,
            medium=0,
            low=0,
            info=0,
            files_analyzed=5,
            auto_fixable_count=0
        ),
        execution_time_seconds=10.5,
        timestamp=datetime.utcnow()
    )
    
    comment = generate_review_comment(result)
    
    assert "✅" in comment
    assert "PASSED" in comment
    assert "CLINE" in comment
    assert "10.5s" in comment


def test_generate_review_comment_failed():
    """Test generating review comment for failed review"""
    from app.api.routes import generate_review_comment
    from app.models import ReviewIssue, IssueSeverity
    from datetime import datetime
    
    result = ReviewResult(
        review_type=ReviewType.ALL,
        agent=CLIAgent.CLINE,
        issues=[
            ReviewIssue(
                file="Test.java",
                line=10,
                severity=IssueSeverity.CRITICAL,
                category="Security",
                message="Critical security issue",
                suggestion="Fix immediately",
                auto_fixable=True
            )
        ],
        refactoring_suggestions=[],
        documentation_additions=[],
        summary=ReviewSummary(
            total_issues=1,
            critical=1,
            high=0,
            medium=0,
            low=0,
            info=0,
            files_analyzed=1,
            auto_fixable_count=1
        ),
        execution_time_seconds=15.0,
        timestamp=datetime.utcnow()
    )
    
    comment = generate_review_comment(result)
    
    assert "❌" in comment
    assert "FAILED" in comment
    assert "Critical" in comment
    assert "Security" in comment


def test_review_endpoint_invalid_request():
    """Test review endpoint with invalid request"""
    response = client.post("/api/v1/review", json={
        "project_id": 0,  # Invalid: must be > 0
        "merge_request_iid": 1
    })
    
    assert response.status_code == 422  # Validation error


def test_review_endpoint_missing_fields():
    """Test review endpoint with missing required fields"""
    response = client.post("/api/v1/review", json={})
    
    assert response.status_code == 422  # Validation error
