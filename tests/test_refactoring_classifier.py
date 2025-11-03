"""
Tests for RefactoringClassifier
"""

import pytest
from app.models import RefactoringSuggestion, RefactoringImpact, IssueSeverity
from app.services.refactoring_classifier import RefactoringClassifier


def test_classify_no_suggestions():
    """Test classification with no suggestions"""
    classifier = RefactoringClassifier()
    result = classifier.classify([])
    assert result == RefactoringImpact.MINOR


def test_classify_minor_refactoring():
    """Test classification of minor refactoring"""
    classifier = RefactoringClassifier()
    suggestions = [
        RefactoringSuggestion(
            file="Test.java",
            line=10,
            severity=IssueSeverity.LOW,
            category="Naming",
            message="Variable name unclear",
            suggestion="Rename to clearer name",
            impact=RefactoringImpact.MINOR,
            effort="LOW"
        )
    ]
    result = classifier.classify(suggestions)
    assert result == RefactoringImpact.MINOR


def test_classify_significant_many_files():
    """Test classification with many files affected"""
    classifier = RefactoringClassifier()
    suggestions = [
        RefactoringSuggestion(
            file=f"Test{i}.java",
            severity=IssueSeverity.MEDIUM,
            category="Refactoring",
            message="Needs refactoring",
            suggestion="Refactor code",
            impact=RefactoringImpact.MINOR,
            effort="MEDIUM"
        )
        for i in range(5)  # 5 files > threshold of 3
    ]
    result = classifier.classify(suggestions)
    assert result == RefactoringImpact.SIGNIFICANT


def test_separate_refactorings():
    """Test separating refactorings by impact"""
    classifier = RefactoringClassifier()
    suggestions = [
        RefactoringSuggestion(
            file="Test1.java",
            severity=IssueSeverity.HIGH,
            category="Architecture",
            message="Major refactoring",
            suggestion="Restructure",
            impact=RefactoringImpact.SIGNIFICANT,
            effort="HIGH"
        ),
        RefactoringSuggestion(
            file="Test2.java",
            severity=IssueSeverity.LOW,
            category="Naming",
            message="Minor rename",
            suggestion="Rename variable",
            impact=RefactoringImpact.MINOR,
            effort="LOW"
        )
    ]
    
    significant, minor = classifier.separate_refactorings(suggestions)
    assert len(significant) == 1
    assert len(minor) == 1
    assert significant[0].impact == RefactoringImpact.SIGNIFICANT
    assert minor[0].impact == RefactoringImpact.MINOR


