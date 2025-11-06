"""
JSON Schema Validator for CLI Review Results

Validates CLI agent output against the defined JSON schema to ensure
proper structure and required fields are present.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

try:
    import jsonschema
    from jsonschema import Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from loguru import logger


class ReviewResultValidator:
    """Validator for code review results from CLI agents"""
    
    def __init__(self, schema_path: Optional[Path] = None):
        """
        Initialize validator with JSON schema
        
        Args:
            schema_path: Path to JSON schema file. If None, uses default schema location.
        """
        if schema_path is None:
            # Default schema location
            schema_path = Path(__file__).parent.parent.parent / "schemas" / "review_result_schema.json"
        
        self.schema_path = schema_path
        self.schema = self._load_schema()
        self.validator = None
        
        if JSONSCHEMA_AVAILABLE and self.schema:
            self.validator = Draft7Validator(self.schema)
    
    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Load JSON schema from file"""
        try:
            if not self.schema_path.exists():
                logger.warning(f"JSON schema not found at {self.schema_path}")
                return None
            
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            logger.debug(f"Loaded JSON schema from {self.schema_path}")
            return schema
        except Exception as e:
            logger.error(f"Failed to load JSON schema: {e}")
            return None
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate review result data against schema
        
        Args:
            data: Review result data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        if not JSONSCHEMA_AVAILABLE:
            logger.warning("jsonschema library not available, skipping validation")
            return self._basic_validation(data)
        
        if not self.validator:
            logger.warning("No schema loaded, performing basic validation only")
            return self._basic_validation(data)
        
        errors = []
        
        try:
            # Validate against schema
            for error in self.validator.iter_errors(data):
                error_msg = self._format_validation_error(error)
                errors.append(error_msg)
            
            if errors:
                return False, errors
            
            # Additional semantic validations
            semantic_errors = self._semantic_validation(data)
            if semantic_errors:
                return False, semantic_errors
            
            logger.debug("Review result passed validation")
            return True, []
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False, [f"Validation exception: {str(e)}"]
    
    def _basic_validation(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Basic validation without jsonschema library
        Checks for required fields and basic structure
        """
        errors = []
        
        # Check required top-level fields
        required_fields = ["review_type", "issues", "summary"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check review_type is valid
        valid_review_types = [
            "ERROR_DETECTION", "BEST_PRACTICES", "REFACTORING",
            "SECURITY_AUDIT", "DOCUMENTATION", "PERFORMANCE",
            "ARCHITECTURE", "TRANSACTION_MANAGEMENT", "CONCURRENCY",
            "DATABASE_OPTIMIZATION", "UNIT_TEST_COVERAGE", "MEMORY_BANK", "ALL"
        ]
        if "review_type" in data and data["review_type"] not in valid_review_types:
            errors.append(f"Invalid review_type: {data['review_type']}")
        
        # Check issues is array
        if "issues" in data and not isinstance(data["issues"], list):
            errors.append("Field 'issues' must be an array")
        
        # Check summary structure
        if "summary" in data:
            summary = data["summary"]
            if not isinstance(summary, dict):
                errors.append("Field 'summary' must be an object")
            else:
                required_summary_fields = ["total_issues", "critical", "high", "medium", "low"]
                for field in required_summary_fields:
                    if field not in summary:
                        errors.append(f"Missing required summary field: {field}")
        
        # Check each issue has required fields
        if "issues" in data and isinstance(data["issues"], list):
            for i, issue in enumerate(data["issues"]):
                required_issue_fields = ["file", "severity", "category", "message", "suggestion", "auto_fixable"]
                for field in required_issue_fields:
                    if field not in issue:
                        errors.append(f"Issue #{i+1}: Missing required field '{field}'")
                
                # Check severity is valid
                valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
                if "severity" in issue and issue["severity"] not in valid_severities:
                    errors.append(f"Issue #{i+1}: Invalid severity '{issue['severity']}'")
        
        return (len(errors) == 0, errors)
    
    def _semantic_validation(self, data: Dict[str, Any]) -> List[str]:
        """
        Additional semantic validations beyond schema
        """
        errors = []
        
        # Check total_issues matches actual count
        if "issues" in data and "summary" in data:
            actual_count = len(data["issues"])
            reported_count = data["summary"].get("total_issues", 0)
            
            if actual_count != reported_count:
                errors.append(
                    f"Mismatch: summary.total_issues ({reported_count}) "
                    f"!= actual issues count ({actual_count})"
                )
        
        # Check severity counts
        if "issues" in data and "summary" in data:
            severity_counts = {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
                "INFO": 0
            }
            
            for issue in data["issues"]:
                severity = issue.get("severity", "").upper()
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            summary = data["summary"]
            for severity, actual_count in severity_counts.items():
                reported_count = summary.get(severity.lower(), 0)
                if actual_count != reported_count:
                    errors.append(
                        f"Severity count mismatch for {severity}: "
                        f"summary reports {reported_count}, actual is {actual_count}"
                    )
        
        # Check file paths are relative (not absolute)
        if "issues" in data:
            for i, issue in enumerate(data["issues"]):
                file_path = issue.get("file", "")
                if file_path.startswith("/") or (len(file_path) > 2 and file_path[1] == ":"):
                    errors.append(
                        f"Issue #{i+1}: File path should be relative, not absolute: {file_path}"
                    )
        
        # Check line numbers are positive integers
        if "issues" in data:
            for i, issue in enumerate(data["issues"]):
                if "line" in issue:
                    line = issue["line"]
                    if not isinstance(line, int) or line < 1:
                        errors.append(
                            f"Issue #{i+1}: Line number must be positive integer, got: {line}"
                        )
        
        return errors
    
    def _format_validation_error(self, error) -> str:
        """Format jsonschema validation error for readability"""
        path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        return f"Validation error at {path}: {error.message}"
    
    def validate_and_log(self, data: Dict[str, Any]) -> bool:
        """
        Validate and log results
        
        Args:
            data: Review result data to validate
            
        Returns:
            True if valid, False otherwise
        """
        is_valid, errors = self.validate(data)
        
        if not is_valid:
            logger.warning("Review result validation failed:")
            for error in errors:
                logger.warning(f"  - {error}")
        else:
            logger.debug("Review result validation passed")
        
        return is_valid


# Global validator instance
_validator_instance = None


def get_validator() -> ReviewResultValidator:
    """Get or create global validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ReviewResultValidator()
    return _validator_instance


def validate_review_result(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate review result
    
    Args:
        data: Review result data to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    validator = get_validator()
    return validator.validate(data)

