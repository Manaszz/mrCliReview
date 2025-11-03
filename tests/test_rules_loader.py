"""
Tests for CustomRulesLoader
"""

import pytest
from app.services.custom_rules_loader import CustomRulesLoader


def test_load_default_rules():
    """Test loading default Java Spring Boot rules"""
    loader = CustomRulesLoader()
    rules = loader.load_rules(language="java")
    
    assert len(rules) > 0
    assert "error_detection" in rules or "errors" in rules
    assert isinstance(rules, dict)


def test_get_combined_rules():
    """Test combining all rules into single content"""
    loader = CustomRulesLoader()
    rules = loader.load_rules(language="java")
    combined = loader.get_combined_rules_content(rules)
    
    assert isinstance(combined, str)
    assert len(combined) > 0


def test_get_rule_for_review_type():
    """Test getting specific rule for review type"""
    loader = CustomRulesLoader()
    rules = loader.load_rules(language="java")
    
    error_rule = loader.get_rule_for_review_type(rules, "ERROR_DETECTION")
    # May be None if exact category not found, but should not raise error
    assert error_rule is None or isinstance(error_rule, str)


