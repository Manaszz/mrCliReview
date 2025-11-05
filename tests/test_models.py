"""
Tests for Pydantic Models
"""

import pytest
from pydantic import ValidationError
from app.models import (
    ReviewRequest,
    ReviewType,
    CLIAgent,
    Language,
    IssueSeverity,
    RefactoringImpact,
    ReviewIssue,
    RefactoringSuggestion,
    DocumentationAddition,
    ReviewSummary,
    ValidationResult
)


def test_review_request_valid():
    """Test valid review request"""
    request = ReviewRequest(
        agent=CLIAgent.CLINE,
        review_types=[ReviewType.ERROR_DETECTION],
        project_id=1,
        merge_request_iid=123,
        language=Language.JAVA
    )
    
    assert request.agent == CLIAgent.CLINE
    assert request.project_id == 1
    assert request.language == Language.JAVA


def test_review_request_defaults():
    """Test review request with default values"""
    request = ReviewRequest(
        project_id=1,
        merge_request_iid=123
    )
    
    assert request.agent == CLIAgent.CLINE
    assert request.review_types == [ReviewType.ALL]
    assert request.language == Language.JAVA


def test_review_request_invalid_project_id():
    """Test review request with invalid project ID"""
    with pytest.raises(ValidationError):
        ReviewRequest(
            project_id=0,  # Must be > 0
            merge_request_iid=123
        )


def test_review_request_empty_review_types():
    """Test review request with empty review types"""
    request = ReviewRequest(
        project_id=1,
        merge_request_iid=123,
        review_types=[]
    )
    
    # Should default to ALL
    assert request.review_types == [ReviewType.ALL]


def test_review_issue_model():
    """Test ReviewIssue model"""
    issue = ReviewIssue(
        file="Test.java",
        line=10,
        severity=IssueSeverity.CRITICAL,
        category="NullPointer",
        message="Potential NPE",
        suggestion="Add null check"
    )
    
    assert issue.file == "Test.java"
    assert issue.line == 10
    assert issue.severity == IssueSeverity.CRITICAL
    assert issue.auto_fixable is False


def test_refactoring_suggestion_model():
    """Test RefactoringSuggestion model"""
    suggestion = RefactoringSuggestion(
        file="Test.java",
        line=20,
        severity=IssueSeverity.MEDIUM,
        category="Architecture",
        message="Extract service",
        suggestion="Create service class",
        impact=RefactoringImpact.SIGNIFICANT,
        effort="HIGH"
    )
    
    assert suggestion.impact == RefactoringImpact.SIGNIFICANT
    assert suggestion.effort == "HIGH"


def test_documentation_addition_model():
    """Test DocumentationAddition model"""
    doc = DocumentationAddition(
        file="Test.java",
        line=5,
        type="CLASS_JAVADOC",
        generated_doc="/** Test class */",
        reason="Missing documentation"
    )
    
    assert doc.type == "CLASS_JAVADOC"
    assert "Test class" in doc.generated_doc


def test_review_summary_model():
    """Test ReviewSummary model"""
    summary = ReviewSummary(
        total_issues=10,
        critical=2,
        high=3,
        medium=4,
        low=1,
        files_analyzed=5,
        auto_fixable_count=6
    )
    
    assert summary.total_issues == 10
    assert summary.critical == 2
    assert summary.auto_fixable_count == 6


def test_validation_result_model():
    """Test ValidationResult model"""
    result = ValidationResult(
        is_valid=True,
        jira_ticket="PROJ-123",
        completeness_score=85,
        warnings=["Minor warning"]
    )
    
    assert result.is_valid is True
    assert result.jira_ticket == "PROJ-123"
    assert result.completeness_score == 85


def test_validation_result_with_errors():
    """Test ValidationResult with errors"""
    result = ValidationResult(
        is_valid=False,
        errors=["Missing JIRA ticket", "Description too short"],
        completeness_score=40
    )
    
    assert result.is_valid is False
    assert len(result.errors) == 2


def test_enum_values():
    """Test enum values"""
    assert CLIAgent.CLINE.value == "CLINE"
    assert ReviewType.ERROR_DETECTION.value == "ERROR_DETECTION"
    assert Language.JAVA.value == "java"
    assert IssueSeverity.CRITICAL.value == "CRITICAL"
    assert RefactoringImpact.SIGNIFICANT.value == "SIGNIFICANT"

