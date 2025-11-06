"""
Custom Rules Loader

Loads code review rules with priority:
1. Project-specific rules (.project-rules/ in repository)
2. Confluence rules (from n8n workflow)
3. Default rules (rules/java-spring-boot/)
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CustomRulesLoader:
    """Loader for code review rules with hierarchy support"""
    
    def __init__(self, default_rules_path: str = "rules/java-spring-boot"):
        """
        Initialize rules loader
        
        Args:
            default_rules_path: Path to default rules directory
        """
        self.default_rules_path = default_rules_path
        
    def load_rules(
        self,
        language: str,
        repo_path: Optional[str] = None,
        confluence_rules: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Load rules with priority hierarchy
        
        Priority:
        1. Project-specific rules (if repo_path provided and .project-rules/ exists)
        2. Confluence rules (if provided)
        3. Default rules
        
        Args:
            language: Programming language (e.g., 'java')
            repo_path: Path to cloned repository (optional)
            confluence_rules: Confluence rules markdown content (optional)
            
        Returns:
            Dict mapping rule category to content
        """
        rules = {}
        
        # Step 1: Load default rules
        default_rules = self._load_default_rules(language)
        rules.update(default_rules)
        logger.info(f"Loaded {len(default_rules)} default rule files")
        
        # Step 2: Override with Confluence rules if provided
        if confluence_rules:
            confluence_parsed = self._parse_confluence_rules(confluence_rules)
            rules.update(confluence_parsed)
            logger.info(f"Loaded Confluence rules, overriding {len(confluence_parsed)} categories")
        
        # Step 3: Override with project-specific rules if present
        if repo_path:
            project_rules = self._load_project_rules(repo_path)
            if project_rules:
                rules.update(project_rules)
                logger.info(f"Loaded project-specific rules, overriding {len(project_rules)} categories")
        
        return rules
    
    def _load_default_rules(self, language: str) -> Dict[str, str]:
        """
        Load default rules for language
        
        Args:
            language: Programming language
            
        Returns:
            Dict of rule category to content
        """
        rules_dir = Path(self.default_rules_path)
        if language != "java":
            # TODO: Add support for other languages
            logger.warning(f"No default rules for language '{language}', using Java rules")
        
        if not rules_dir.exists():
            logger.error(f"Default rules directory not found: {rules_dir}")
            return {}
        
        rules = {}
        for rule_file in rules_dir.glob("*.md"):
            if rule_file.name == "README.md":
                continue
            
            category = rule_file.stem  # e.g., 'error_detection'
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    rules[category] = f.read()
            except Exception as e:
                logger.error(f"Failed to load default rule file {rule_file}: {str(e)}")
        
        return rules
    
    def _load_project_rules(self, repo_path: str) -> Dict[str, str]:
        """
        Load project-specific rules from .project-rules/
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dict of rule category to content
        """
        project_rules_dir = Path(repo_path) / ".project-rules"
        if not project_rules_dir.exists():
            logger.debug(f"No project-specific rules found in {repo_path}")
            return {}
        
        rules = {}
        for rule_file in project_rules_dir.glob("*.md"):
            if rule_file.name == "README.md":
                continue
            
            category = rule_file.stem
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    rules[category] = f.read()
                logger.info(f"Loaded project-specific rule: {category}")
            except Exception as e:
                logger.error(f"Failed to load project rule file {rule_file}: {str(e)}")
        
        return rules
    
    def _parse_confluence_rules(self, confluence_content: str) -> Dict[str, str]:
        """
        Parse Confluence markdown content into rule categories
        
        Expected format:
        # Development Standards - Code Review Rules
        
        ## Java Spring Boot
        
        ### Error Detection
        [content]
        
        ### Best Practices
        [content]
        
        Args:
            confluence_content: Confluence page markdown content
            
        Returns:
            Dict of rule category to content
        """
        import re
        
        rules = {}
        
        # Extract sections by h3 headers (###)
        # Pattern: ### Category Name followed by content until next ### or end
        pattern = r'###\s+([^\n]+)\n(.*?)(?=###|\Z)'
        matches = re.findall(pattern, confluence_content, re.DOTALL)
        
        for category_name, content in matches:
            # Normalize category name to snake_case
            category = category_name.strip().lower().replace(' ', '_')
            rules[category] = content.strip()
            logger.debug(f"Parsed Confluence rule category: {category}")
        
        return rules
    
    def get_combined_rules_content(self, rules: Dict[str, str]) -> str:
        """
        Combine all rules into single markdown content
        
        Args:
            rules: Dict of rule category to content
            
        Returns:
            Combined markdown content
        """
        sections = []
        for category, content in rules.items():
            sections.append(f"# {category.replace('_', ' ').title()}\n\n{content}")
        
        return "\n\n---\n\n".join(sections)
    
    def get_rule_for_review_type(
        self,
        rules: Dict[str, str],
        review_type: str
    ) -> Optional[str]:
        """
        Get rule content for specific review type
        
        Args:
            rules: All loaded rules
            review_type: Review type (e.g., 'ERROR_DETECTION')
            
        Returns:
            Rule content or None
        """
        # Convert review type to rule category name
        # ERROR_DETECTION -> error_detection
        category = review_type.lower()
        
        # Try exact match
        if category in rules:
            return rules[category]
        
        # Try common alternatives
        alternatives = {
            'error_detection': ['errors', 'bugs'],
            'best_practices': ['practices', 'conventions'],
            'security_audit': ['security'],
            'refactoring': ['refactor'],
            'performance': ['optimization', 'perf'],
            'documentation': ['docs', 'javadoc']
        }
        
        if category in alternatives:
            for alt in alternatives[category]:
                if alt in rules:
                    return rules[alt]
        
        logger.warning(f"No rule found for review type: {review_type}")
        return None


