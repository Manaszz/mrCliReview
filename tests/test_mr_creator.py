"""
Tests for MRCreator
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.mr_creator import MRCreator
from app.services.gitlab_service import GitLabService
from app.services.git_repository_manager import GitRepositoryManager
from app.models import (
    ReviewIssue,
    RefactoringSuggestion,
    DocumentationAddition,
    IssueSeverity,
    RefactoringImpact
)


@pytest.fixture
def mock_gitlab_service():
    """Create mock GitLabService"""
    service = MagicMock(spec=GitLabService)
    service.create_merge_request = AsyncMock(return_value={
        "iid": 2,
        "web_url": "https://gitlab.example.com/project/-/merge_requests/2"
    })
    service.commit_file_changes = AsyncMock(return_value={"id": "abc123"})
    return service


@pytest.fixture
def mock_git_manager():
    """Create mock GitRepositoryManager"""
    return MagicMock(spec=GitRepositoryManager)


@pytest.fixture
def mr_creator(mock_gitlab_service, mock_git_manager):
    """Create MRCreator instance"""
    return MRCreator(mock_gitlab_service, mock_git_manager)


@pytest.mark.asyncio
async def test_create_fixes_mr_success(mr_creator, mock_gitlab_service):
    """Test creating fixes MR successfully"""
    issues = [
        ReviewIssue(
            file="Test.java",
            line=10,
            severity=IssueSeverity.CRITICAL,
            category="NullPointer",
            message="NPE risk",
            suggestion="Add null check",
            auto_fixable=True
        ),
        ReviewIssue(
            file="Test2.java",
            line=20,
            severity=IssueSeverity.HIGH,
            category="Security",
            message="SQL injection",
            suggestion="Use prepared statement",
            auto_fixable=True
        )
    ]
    
    result = await mr_creator.create_fixes_mr(
        project_id=123,
        source_branch="feature-branch",
        target_branch="main",
        mr_iid=1,
        issues=issues
    )
    
    assert result.success is True
    assert result.mr_iid == 2
    assert "gitlab.example.com" in result.mr_url
    
    # Verify GitLab service was called
    mock_gitlab_service.create_merge_request.assert_called_once()
    call_args = mock_gitlab_service.create_merge_request.call_args[1]
    assert call_args["source_branch"] == "fix/mr-1-ai-review-fixes"
    assert call_args["target_branch"] == "feature-branch"  # Important: targets source branch!
    assert "fixes" in call_args["labels"]


@pytest.mark.asyncio
async def test_create_fixes_mr_no_fixable_issues(mr_creator):
    """Test creating fixes MR with no auto-fixable issues"""
    issues = [
        ReviewIssue(
            file="Test.java",
            line=10,
            severity=IssueSeverity.LOW,
            category="Style",
            message="Minor style issue",
            suggestion="Fix formatting",
            auto_fixable=False
        )
    ]
    
    result = await mr_creator.create_fixes_mr(
        project_id=123,
        source_branch="feature-branch",
        target_branch="main",
        mr_iid=1,
        issues=issues
    )
    
    assert result.success is False
    assert "No auto-fixable issues" in result.error


@pytest.mark.asyncio
async def test_create_fixes_mr_with_minor_refactoring(mr_creator, mock_gitlab_service):
    """Test creating fixes MR with minor refactoring included"""
    issues = [
        ReviewIssue(
            file="Test.java",
            line=10,
            severity=IssueSeverity.CRITICAL,
            category="Bug",
            message="Critical bug",
            suggestion="Fix it",
            auto_fixable=True
        )
    ]
    
    minor_refactoring = [
        RefactoringSuggestion(
            file="Test.java",
            line=5,
            severity=IssueSeverity.LOW,
            category="Naming",
            message="Unclear variable name",
            suggestion="Rename to clearer name",
            impact=RefactoringImpact.MINOR,
            effort="LOW"
        )
    ]
    
    result = await mr_creator.create_fixes_mr(
        project_id=123,
        source_branch="feature-branch",
        target_branch="main",
        mr_iid=1,
        issues=issues,
        minor_refactoring=minor_refactoring
    )
    
    assert result.success is True


@pytest.mark.asyncio
async def test_create_refactoring_mr_success(mr_creator, mock_gitlab_service):
    """Test creating refactoring MR successfully"""
    refactorings = [
        RefactoringSuggestion(
            file="Test1.java",
            line=10,
            severity=IssueSeverity.MEDIUM,
            category="Architecture",
            message="Extract interface",
            suggestion="Create interface for better abstraction",
            impact=RefactoringImpact.SIGNIFICANT,
            effort="HIGH"
        ),
        RefactoringSuggestion(
            file="Test2.java",
            line=20,
            severity=IssueSeverity.MEDIUM,
            category="Design",
            message="Apply strategy pattern",
            suggestion="Refactor to use strategy pattern",
            impact=RefactoringImpact.SIGNIFICANT,
            effort="MEDIUM"
        )
    ]
    
    result = await mr_creator.create_refactoring_mr(
        project_id=123,
        source_branch="feature-branch",
        target_branch="main",
        mr_iid=1,
        refactorings=refactorings
    )
    
    assert result.success is True
    assert result.mr_iid == 2
    
    # Verify GitLab service was called
    mock_gitlab_service.create_merge_request.assert_called_once()
    call_args = mock_gitlab_service.create_merge_request.call_args[1]
    assert call_args["source_branch"] == "refactor/mr-1-ai-suggestions"
    assert call_args["target_branch"] == "feature-branch"  # Important: targets source branch!
    assert "refactoring" in call_args["labels"]


def test_generate_fixes_description(mr_creator):
    """Test generating fixes description"""
    issues = [
        ReviewIssue(
            file="Test.java",
            line=10,
            severity=IssueSeverity.CRITICAL,
            category="Security",
            message="SQL injection risk",
            suggestion="Use prepared statement",
            auto_fixable=True
        )
    ]
    
    description = mr_creator._generate_fixes_description(issues)
    
    assert "🔧 AI Review Fixes" in description
    assert "CRITICAL" in description
    assert "SQL injection risk" in description
    assert "Test.java" in description


def test_generate_refactoring_description(mr_creator):
    """Test generating refactoring description"""
    refactorings = [
        RefactoringSuggestion(
            file="Test.java",
            line=10,
            severity=IssueSeverity.MEDIUM,
            category="Architecture",
            message="Extract service layer",
            suggestion="Create separate service class",
            impact=RefactoringImpact.SIGNIFICANT,
            effort="HIGH"
        )
    ]
    
    description = mr_creator._generate_refactoring_description(refactorings)
    
    assert "♻️ AI Refactoring Suggestions" in description
    assert "Architecture" in description
    assert "Extract service layer" in description
    assert "HIGH" in description


@pytest.mark.asyncio
async def test_create_documentation_commit_empty(mr_creator):
    """Test creating documentation commit with no documentation"""
    result = await mr_creator.create_documentation_commit(
        repo_path="/tmp/repo",
        source_branch="feature-branch",
        documentation=[],
        project_id=123
    )
    
    assert result is None


def test_generate_documentation_commit_message(mr_creator):
    """Test generating documentation commit message"""
    documentation = [
        DocumentationAddition(
            file="Test.java",
            line=1,
            type="CLASS_JAVADOC",
            generated_doc="/** Test class */",
            reason="Missing class documentation"
        ),
        DocumentationAddition(
            file="Test.java",
            line=10,
            type="METHOD_JAVADOC",
            generated_doc="/** Test method */",
            reason="Missing method documentation"
        )
    ]
    
    message = mr_creator._generate_documentation_commit_message(documentation)
    
    assert "docs:" in message
    assert "2 additions" in message
    assert "1 files" in message
    assert "[skip ci]" in message
