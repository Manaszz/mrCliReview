"""
Unit tests for JSON Schema Validator
"""

import pytest
from app.utils.json_validator import ReviewResultValidator, validate_review_result


class TestReviewResultValidator:
    """Tests for ReviewResultValidator"""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return ReviewResultValidator()
    
    def test_valid_minimal_result(self, validator):
        """Test validation of minimal valid result"""
        data = {
            "review_type": "ERROR_DETECTION",
            "issues": [],
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert is_valid
        assert len(errors) == 0
    
    def test_valid_result_with_issues(self, validator):
        """Test validation of result with issues"""
        data = {
            "review_type": "ERROR_DETECTION",
            "changed_files": ["src/UserService.java"],
            "files_analyzed_count": 1,
            "issues": [
                {
                    "file": "src/UserService.java",
                    "line": 42,
                    "severity": "HIGH",
                    "category": "Null Safety",
                    "message": "Potential NPE",
                    "suggestion": "Add null check",
                    "auto_fixable": True
                }
            ],
            "summary": {
                "total_issues": 1,
                "critical": 0,
                "high": 1,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert is_valid
        assert len(errors) == 0
    
    def test_missing_required_field(self, validator):
        """Test validation fails when required field missing"""
        data = {
            "review_type": "ERROR_DETECTION",
            "issues": []
            # Missing "summary"
        }
        
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert len(errors) > 0
        assert any("summary" in err.lower() for err in errors)
    
    def test_invalid_severity(self, validator):
        """Test validation fails for invalid severity"""
        data = {
            "review_type": "ERROR_DETECTION",
            "issues": [
                {
                    "file": "test.java",
                    "severity": "VERY_HIGH",  # Invalid
                    "category": "Test",
                    "message": "Test",
                    "suggestion": "Fix",
                    "auto_fixable": False
                }
            ],
            "summary": {
                "total_issues": 1,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("severity" in err.lower() for err in errors)
    
    def test_invalid_review_type(self, validator):
        """Test validation fails for invalid review type"""
        data = {
            "review_type": "INVALID_TYPE",
            "issues": [],
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("review_type" in err.lower() for err in errors)
    
    def test_count_mismatch(self, validator):
        """Test semantic validation catches count mismatch"""
        data = {
            "review_type": "ERROR_DETECTION",
            "issues": [
                {
                    "file": "test.java",
                    "severity": "HIGH",
                    "category": "Test",
                    "message": "Test",
                    "suggestion": "Fix",
                    "auto_fixable": False
                }
            ],
            "summary": {
                "total_issues": 5,  # Mismatch: should be 1
                "critical": 0,
                "high": 1,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("mismatch" in err.lower() for err in errors)
    
    def test_severity_count_mismatch(self, validator):
        """Test semantic validation catches severity count mismatch"""
        data = {
            "review_type": "ERROR_DETECTION",
            "issues": [
                {
                    "file": "test.java",
                    "severity": "CRITICAL",
                    "category": "Test",
                    "message": "Test",
                    "suggestion": "Fix",
                    "auto_fixable": False
                },
                {
                    "file": "test.java",
                    "severity": "HIGH",
                    "category": "Test",
                    "message": "Test",
                    "suggestion": "Fix",
                    "auto_fixable": False
                }
            ],
            "summary": {
                "total_issues": 2,
                "critical": 0,  # Should be 1
                "high": 2,      # Should be 1
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("severity" in err.lower() and "mismatch" in err.lower() for err in errors)
    
    def test_absolute_file_path(self, validator):
        """Test semantic validation catches absolute paths"""
        data = {
            "review_type": "ERROR_DETECTION",
            "issues": [
                {
                    "file": "/home/user/project/test.java",  # Absolute path
                    "severity": "HIGH",
                    "category": "Test",
                    "message": "Test",
                    "suggestion": "Fix",
                    "auto_fixable": False
                }
            ],
            "summary": {
                "total_issues": 1,
                "critical": 0,
                "high": 1,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("absolute" in err.lower() for err in errors)
    
    def test_invalid_line_number(self, validator):
        """Test semantic validation catches invalid line numbers"""
        data = {
            "review_type": "ERROR_DETECTION",
            "issues": [
                {
                    "file": "test.java",
                    "line": -5,  # Invalid line number
                    "severity": "HIGH",
                    "category": "Test",
                    "message": "Test",
                    "suggestion": "Fix",
                    "auto_fixable": False
                }
            ],
            "summary": {
                "total_issues": 1,
                "critical": 0,
                "high": 1,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert not is_valid
        assert any("line" in err.lower() for err in errors)
    
    def test_refactoring_result(self, validator):
        """Test validation of refactoring result with suggestions"""
        data = {
            "review_type": "REFACTORING",
            "issues": [],
            "refactoring_suggestions": [
                {
                    "file": "src/Service.java",
                    "line": 10,
                    "severity": "MEDIUM",
                    "category": "Code Smell",
                    "message": "Long method",
                    "suggestion": "Extract method",
                    "impact": "MINOR",
                    "effort": "LOW",
                    "auto_fixable": False
                }
            ],
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert is_valid
        assert len(errors) == 0
    
    def test_documentation_result(self, validator):
        """Test validation of documentation result"""
        data = {
            "review_type": "DOCUMENTATION",
            "issues": [],
            "documentation": [
                {
                    "file": "src/Service.java",
                    "line": 5,
                    "type": "METHOD_JAVADOC",
                    "generated_doc": "/** \n * Method description\n */",
                    "reason": "Missing method documentation"
                }
            ],
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validator.validate(data)
        assert is_valid
        assert len(errors) == 0
    
    def test_error_result(self, validator):
        """Test validation of error result"""
        data = {
            "review_type": "ERROR_DETECTION",
            "issues": [],
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "error": "Git diff failed",
            "error_type": "GIT_ERROR"
        }
        
        is_valid, errors = validator.validate(data)
        assert is_valid
        assert len(errors) == 0
    
    def test_convenience_function(self):
        """Test convenience function"""
        data = {
            "review_type": "ERROR_DETECTION",
            "issues": [],
            "summary": {
                "total_issues": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        
        is_valid, errors = validate_review_result(data)
        assert is_valid
        assert len(errors) == 0

