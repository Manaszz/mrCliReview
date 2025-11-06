"""
Refactoring Classifier

Classifies refactoring suggestions as SIGNIFICANT (separate MR) or MINOR (combine with fixes).
Based on rules/java-spring-boot/refactoring_criteria.md
"""

from typing import List
from app.models import RefactoringSuggestion, RefactoringImpact
import logging

logger = logging.getLogger(__name__)


class RefactoringClassifier:
    """Classifier for refactoring suggestions"""
    
    # Criteria thresholds
    MAX_MINOR_FILES = 3
    MAX_MINOR_LOC = 200
    
    def classify(self, suggestions: List[RefactoringSuggestion]) -> RefactoringImpact:
        """
        Classify refactoring suggestions as SIGNIFICANT or MINOR
        
        Criteria for SIGNIFICANT:
        - More than 3 files affected
        - More than 200 LOC changed
        - Any breaking changes mentioned
        - DI structure modifications
        - Pattern migrations
        
        Args:
            suggestions: List of refactoring suggestions
            
        Returns:
            SIGNIFICANT or MINOR
        """
        if not suggestions:
            return RefactoringImpact.MINOR
        
        # Count affected files
        affected_files = set(s.file for s in suggestions)
        if len(affected_files) > self.MAX_MINOR_FILES:
            logger.info(f"SIGNIFICANT: {len(affected_files)} files affected (>{self.MAX_MINOR_FILES})")
            return RefactoringImpact.SIGNIFICANT
        
        # Estimate LOC changes
        total_loc = self._estimate_loc_changes(suggestions)
        if total_loc > self.MAX_MINOR_LOC:
            logger.info(f"SIGNIFICANT: ~{total_loc} LOC changes (>{self.MAX_MINOR_LOC})")
            return RefactoringImpact.SIGNIFICANT
        
        # Check for high-impact refactorings
        has_significant = any(s.impact == RefactoringImpact.SIGNIFICANT for s in suggestions)
        if has_significant:
            logger.info("SIGNIFICANT: Contains high-impact refactorings")
            return RefactoringImpact.SIGNIFICANT
        
        # Check for breaking changes keywords
        breaking_keywords = [
            'breaking change',
            'api change',
            'signature change',
            'dependency injection',
            'di structure',
            'pattern migration',
            'circular dependency',
            'architecture change'
        ]
        
        for suggestion in suggestions:
            text = (suggestion.message + " " + suggestion.suggestion).lower()
            if any(keyword in text for keyword in breaking_keywords):
                logger.info(f"SIGNIFICANT: Breaking change keyword found in {suggestion.file}")
                return RefactoringImpact.SIGNIFICANT
        
        # Check effort
        high_effort_count = sum(1 for s in suggestions if s.effort == "HIGH")
        if high_effort_count >= 2:
            logger.info(f"SIGNIFICANT: {high_effort_count} high-effort refactorings")
            return RefactoringImpact.SIGNIFICANT
        
        logger.info("MINOR: Refactorings can be combined with fixes")
        return RefactoringImpact.MINOR
    
    def _estimate_loc_changes(self, suggestions: List[RefactoringSuggestion]) -> int:
        """
        Estimate total lines of code changes
        
        Estimation based on effort and number of suggestions:
        - LOW effort: ~10 LOC per suggestion
        - MEDIUM effort: ~30 LOC per suggestion
        - HIGH effort: ~100 LOC per suggestion
        
        Args:
            suggestions: List of refactoring suggestions
            
        Returns:
            Estimated LOC changes
        """
        loc_map = {
            "LOW": 10,
            "MEDIUM": 30,
            "HIGH": 100
        }
        
        total = 0
        for suggestion in suggestions:
            total += loc_map.get(suggestion.effort, 30)
        
        return total
    
    def separate_refactorings(
        self,
        suggestions: List[RefactoringSuggestion]
    ) -> tuple[List[RefactoringSuggestion], List[RefactoringSuggestion]]:
        """
        Separate refactorings into SIGNIFICANT and MINOR groups
        
        Args:
            suggestions: All refactoring suggestions
            
        Returns:
            Tuple of (significant_suggestions, minor_suggestions)
        """
        significant = []
        minor = []
        
        for suggestion in suggestions:
            if suggestion.impact == RefactoringImpact.SIGNIFICANT:
                significant.append(suggestion)
            else:
                minor.append(suggestion)
        
        return significant, minor


