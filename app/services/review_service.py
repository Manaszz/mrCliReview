"""
Review Service

Main orchestrator for code reviews. Coordinates CLI managers, rules loading,
GitLab integration, and MR creation.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import time
from datetime import datetime

from app.models import (
    ReviewRequest,
    ReviewResult,
    ReviewSummary,
    ReviewIssue,
    RefactoringSuggestion,
    DocumentationAddition,
    ReviewType,
    CLIAgent,
    IssueSeverity,
    RefactoringImpact
)
from app.services.base_cli_manager import BaseCLIManager
from app.services.cline_cli_manager import ClineCLIManager
from app.services.qwen_code_cli_manager import QwenCodeCLIManager
from app.services.custom_rules_loader import CustomRulesLoader

logger = logging.getLogger(__name__)


class ReviewService:
    """Main service for orchestrating code reviews"""
    
    def __init__(
        self,
        cline_manager: ClineCLIManager,
        qwen_manager: QwenCodeCLIManager,
        rules_loader: CustomRulesLoader,
        prompts_base_path: str = "prompts"
    ):
        """
        Initialize review service
        
        Args:
            cline_manager: Cline CLI manager instance
            qwen_manager: Qwen Code CLI manager instance
            rules_loader: Rules loader instance
            prompts_base_path: Base path for prompt files
        """
        self.cline_manager = cline_manager
        self.qwen_manager = qwen_manager
        self.rules_loader = rules_loader
        self.prompts_base_path = Path(prompts_base_path)
        
    async def execute_review(
        self,
        request: ReviewRequest,
        repo_path: str
    ) -> ReviewResult:
        """
        Execute complete code review
        
        Args:
            request: Review request with parameters
            repo_path: Path to cloned repository
            
        Returns:
            ReviewResult with all findings
            
        Note:
            Changed files are automatically determined by CLI agents via git diff
        """
        start_time = time.time()
        
        # Select CLI manager
        cli_manager = self._get_cli_manager(request.agent)
        logger.info(f"Using {request.agent.value} for review")
        
        # Load rules
        rules = self.rules_loader.load_rules(
            language=request.language.value,
            repo_path=repo_path,
            confluence_rules=request.confluence_rules
        )
        logger.info(f"Loaded {len(rules)} rule categories")
        
        # Get combined rules content for prompts
        combined_rules = self.rules_loader.get_combined_rules_content(rules)
        
        # Expand ALL review type
        review_types = self._expand_review_types(request.review_types)
        logger.info(f"Executing {len(review_types)} review types: {[rt.value for rt in review_types]}")
        
        # Load prompts for review types
        prompts = self._load_prompts(request.agent, review_types)
        
        # Execute reviews in parallel
        # Note: changed_files are automatically determined by CLI via git diff
        raw_results = await cli_manager.execute_parallel_reviews(
            review_types=review_types,
            repo_path=repo_path,
            changed_files=[],  # CLI will determine this automatically
            prompts=prompts,
            custom_rules=combined_rules,
            jira_context=request.jira_context
        )
        
        # Aggregate results
        result = self._aggregate_results(
            raw_results=raw_results,
            agent=request.agent,
            start_time=start_time
        )
        
        logger.info(f"Review completed: {result.summary.total_issues} issues found")
        return result
    
    def _get_cli_manager(self, agent: CLIAgent) -> BaseCLIManager:
        """Get appropriate CLI manager"""
        if agent == CLIAgent.CLINE:
            return self.cline_manager
        elif agent == CLIAgent.QWEN_CODE:
            return self.qwen_manager
        else:
            raise ValueError(f"Unknown CLI agent: {agent}")
    
    def _expand_review_types(self, review_types: List[ReviewType]) -> List[ReviewType]:
        """
        Expand ALL review type to specific types
        
        Args:
            review_types: Requested review types
            
        Returns:
            List of specific review types
        """
        if ReviewType.ALL in review_types:
            return [
                ReviewType.ERROR_DETECTION,
                ReviewType.BEST_PRACTICES,
                ReviewType.REFACTORING,
                ReviewType.SECURITY_AUDIT,
                ReviewType.DOCUMENTATION,
                ReviewType.PERFORMANCE,
                ReviewType.ARCHITECTURE,
                ReviewType.TRANSACTION_MANAGEMENT,
                ReviewType.CONCURRENCY,
                ReviewType.DATABASE_OPTIMIZATION
            ]
        return review_types
    
    def _load_prompts(
        self,
        agent: CLIAgent,
        review_types: List[ReviewType]
    ) -> Dict[ReviewType, str]:
        """
        Load prompt files for review types
        
        Args:
            agent: CLI agent (determines prompt directory)
            review_types: List of review types
            
        Returns:
            Dict mapping review type to prompt content
        """
        prompts = {}
        
        # Determine prompt directory based on agent
        if agent == CLIAgent.CLINE:
            prompt_dir = self.prompts_base_path / "cline"
        elif agent == CLIAgent.QWEN_CODE:
            prompt_dir = self.prompts_base_path / "qwen"
        else:
            raise ValueError(f"Unknown agent: {agent}")
        
        # Additional prompts directory
        additional_dir = self.prompts_base_path / "additional"
        
        for review_type in review_types:
            # Convert review type to filename
            filename = f"{review_type.value.lower()}.md"
            
            # Try agent-specific prompt first
            prompt_path = prompt_dir / filename
            if not prompt_path.exists():
                # Try additional prompts
                prompt_path = additional_dir / filename
            
            if prompt_path.exists():
                try:
                    with open(prompt_path, 'r', encoding='utf-8') as f:
                        prompts[review_type] = f.read()
                    logger.debug(f"Loaded prompt for {review_type.value}: {prompt_path}")
                except Exception as e:
                    logger.error(f"Failed to load prompt {prompt_path}: {str(e)}")
                    prompts[review_type] = self._get_fallback_prompt(review_type)
            else:
                logger.warning(f"Prompt file not found for {review_type.value}: {prompt_path}")
                prompts[review_type] = self._get_fallback_prompt(review_type)
        
        return prompts
    
    def _get_fallback_prompt(self, review_type: ReviewType) -> str:
        """
        Generate fallback prompt if file not found
        
        Args:
            review_type: Review type
            
        Returns:
            Basic prompt content
        """
        return f"""# {review_type.value} Review

## Objective
Perform {review_type.value.replace('_', ' ').lower()} analysis on the provided code changes.

## Context
- Repository Path: {{repo_path}}
- Changed Files: {{changed_files}}
- Language: {{language}}

## Instructions
1. Analyze the changed files
2. Identify issues related to {review_type.value.replace('_', ' ').lower()}
3. Provide specific, actionable feedback
4. Output results in JSON format

## Output Format
```json
{{
  "review_type": "{review_type.value}",
  "issues": [
    {{
      "file": "path/to/file",
      "line": 123,
      "severity": "HIGH",
      "category": "Category",
      "message": "Issue description",
      "suggestion": "How to fix"
    }}
  ],
  "summary": {{
    "total_issues": 0
  }}
}}
```
"""
    
    def _aggregate_results(
        self,
        raw_results: List[Dict[str, Any]],
        agent: CLIAgent,
        start_time: float
    ) -> ReviewResult:
        """
        Aggregate multiple review results into single ReviewResult
        
        Args:
            raw_results: List of raw review results from CLI
            agent: CLI agent used
            start_time: Review start time
            
        Returns:
            Aggregated ReviewResult
        """
        all_issues = []
        all_refactoring = []
        all_documentation = []
        
        for result in raw_results:
            # Parse issues
            for issue_data in result.get('issues', []):
                try:
                    issue = ReviewIssue(
                        file=issue_data.get('file', 'unknown'),
                        line=issue_data.get('line'),
                        severity=IssueSeverity(issue_data.get('severity', 'MEDIUM')),
                        category=issue_data.get('category', 'Unknown'),
                        message=issue_data.get('message', ''),
                        code_snippet=issue_data.get('code_snippet'),
                        suggestion=issue_data.get('suggestion', ''),
                        auto_fixable=issue_data.get('auto_fixable', False),
                        cwe=issue_data.get('cwe'),
                        rule_source=issue_data.get('rule_source', 'default')
                    )
                    all_issues.append(issue)
                except Exception as e:
                    logger.error(f"Failed to parse issue: {str(e)}")
            
            # Parse refactoring suggestions
            for refactor_data in result.get('refactoring_suggestions', []):
                try:
                    refactor = RefactoringSuggestion(
                        file=refactor_data.get('file', 'unknown'),
                        line=refactor_data.get('line'),
                        severity=IssueSeverity(refactor_data.get('severity', 'MEDIUM')),
                        category=refactor_data.get('category', 'Refactoring'),
                        message=refactor_data.get('message', ''),
                        code_snippet=refactor_data.get('code_snippet'),
                        suggestion=refactor_data.get('suggestion', ''),
                        impact=RefactoringImpact(refactor_data.get('impact', 'MINOR')),
                        effort=refactor_data.get('effort', 'MEDIUM'),
                        auto_fixable=refactor_data.get('auto_fixable', False)
                    )
                    all_refactoring.append(refactor)
                except Exception as e:
                    logger.error(f"Failed to parse refactoring suggestion: {str(e)}")
            
            # Parse documentation
            for doc_data in result.get('documentation', []):
                try:
                    doc = DocumentationAddition(
                        file=doc_data.get('file', 'unknown'),
                        line=doc_data.get('line', 1),
                        type=doc_data.get('type', 'COMMENT'),
                        generated_doc=doc_data.get('generated_doc', ''),
                        reason=doc_data.get('reason', '')
                    )
                    all_documentation.append(doc)
                except Exception as e:
                    logger.error(f"Failed to parse documentation: {str(e)}")
        
        # Calculate summary
        summary = ReviewSummary(
            total_issues=len(all_issues),
            critical=sum(1 for i in all_issues if i.severity == IssueSeverity.CRITICAL),
            high=sum(1 for i in all_issues if i.severity == IssueSeverity.HIGH),
            medium=sum(1 for i in all_issues if i.severity == IssueSeverity.MEDIUM),
            low=sum(1 for i in all_issues if i.severity == IssueSeverity.LOW),
            info=sum(1 for i in all_issues if i.severity == IssueSeverity.INFO),
            files_analyzed=len(set(i.file for i in all_issues)),
            auto_fixable_count=sum(1 for i in all_issues if i.auto_fixable)
        )
        
        execution_time = time.time() - start_time
        
        return ReviewResult(
            review_type=ReviewType.ALL,  # Indicates combined review
            agent=agent,
            issues=all_issues,
            refactoring_suggestions=all_refactoring,
            documentation_additions=all_documentation,
            summary=summary,
            execution_time_seconds=execution_time,
            timestamp=datetime.utcnow()
        )
    
    async def health_check(self) -> Dict[str, bool]:
        """
        Check health of CLI agents and dependencies
        
        Returns:
            Dict with availability status of components
        """
        results = {}
        
        # Check Cline CLI
        try:
            results['cline_available'] = await self.cline_manager.check_availability()
            results['cline_model_connected'] = await self.cline_manager.test_model_connection()
        except Exception as e:
            logger.error(f"Cline health check failed: {str(e)}")
            results['cline_available'] = False
            results['cline_model_connected'] = False
        
        # Check Qwen Code CLI
        try:
            results['qwen_available'] = await self.qwen_manager.check_availability()
            results['qwen_model_connected'] = await self.qwen_manager.test_model_connection()
        except Exception as e:
            logger.error(f"Qwen Code health check failed: {str(e)}")
            results['qwen_available'] = False
            results['qwen_model_connected'] = False
        
        # Overall model API connection
        results['model_api_connected'] = (
            results.get('cline_model_connected', False) or 
            results.get('qwen_model_connected', False)
        )
        
        return results

