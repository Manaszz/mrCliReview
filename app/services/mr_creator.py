"""
MR Creator

Creates merge requests for documentation, fixes, and refactoring.
"""

from typing import List, Optional
from app.models import (
    ReviewIssue,
    RefactoringSuggestion,
    DocumentationAddition,
    MRType,
    MRCreationRequest,
    MRCreationResult,
    IssueSeverity
)
from app.services.gitlab_service import GitLabService
from app.services.git_repository_manager import GitRepositoryManager
import logging

logger = logging.getLogger(__name__)


class MRCreator:
    """Creator for different types of merge requests"""
    
    def __init__(
        self,
        gitlab_service: GitLabService,
        git_manager: GitRepositoryManager
    ):
        """
        Initialize MR creator
        
        Args:
            gitlab_service: GitLab API service
            git_manager: Git repository manager
        """
        self.gitlab = gitlab_service
        self.git = git_manager
    
    async def create_documentation_commit(
        self,
        repo_path: str,
        source_branch: str,
        documentation: List[DocumentationAddition],
        project_id: int
    ) -> Optional[str]:
        """
        Commit documentation improvements directly to source branch
        
        Args:
            repo_path: Path to cloned repository
            source_branch: MR source branch
            documentation: List of documentation additions
            project_id: GitLab project ID
            
        Returns:
            Commit SHA or None if no documentation
        """
        if not documentation:
            return None
        
        logger.info(f"Committing {len(documentation)} documentation improvements to {source_branch}")
        
        # TODO: Apply documentation changes to files
        # For now, create a simple commit with documentation summary
        
        commit_message = self._generate_documentation_commit_message(documentation)
        
        # Commit via GitLab API (safer than local git)
        file_actions = []
        for doc in documentation:
            # Read current file content
            # Add documentation
            # Create update action
            # This is simplified - full implementation would parse and insert documentation
            pass
        
        if file_actions:
            commit_data = await self.gitlab.commit_file_changes(
                project_id=project_id,
                branch=source_branch,
                commit_message=commit_message,
                files=file_actions
            )
            return commit_data.get('id')
        
        return None
    
    async def create_fixes_mr(
        self,
        project_id: int,
        source_branch: str,
        target_branch: str,
        mr_iid: int,
        issues: List[ReviewIssue],
        minor_refactoring: Optional[List[RefactoringSuggestion]] = None
    ) -> MRCreationResult:
        """
        Create MR with fixes (and optional minor refactoring)
        
        Args:
            project_id: GitLab project ID
            source_branch: Original MR source branch
            target_branch: Original MR target branch
            mr_iid: Original MR IID
            issues: List of issues to fix
            minor_refactoring: Minor refactoring suggestions (optional)
            
        Returns:
            MR creation result
        """
        try:
            # Filter auto-fixable critical and high issues
            fixable_issues = [
                i for i in issues
                if i.auto_fixable and i.severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]
            ]
            
            if not fixable_issues:
                logger.info("No auto-fixable critical/high issues, skipping fixes MR")
                return MRCreationResult(success=False, error="No auto-fixable issues")
            
            # Create fix branch
            fix_branch = f"fix/mr-{mr_iid}-ai-review-fixes"
            title = f"🔧 AI Review Fixes for MR !{mr_iid}"
            description = self._generate_fixes_description(fixable_issues, minor_refactoring)
            
            # TODO: Apply fixes to files
            # For now, create MR with description only
            
            mr_data = await self.gitlab.create_merge_request(
                project_id=project_id,
                source_branch=fix_branch,
                target_branch=source_branch,  # Target is original MR branch
                title=title,
                description=description,
                labels=["ai-review", "fixes"]
            )
            
            logger.info(f"Created fixes MR: !{mr_data['iid']}")
            return MRCreationResult(
                success=True,
                mr_iid=mr_data['iid'],
                mr_url=mr_data['web_url']
            )
            
        except Exception as e:
            logger.error(f"Failed to create fixes MR: {str(e)}")
            return MRCreationResult(success=False, error=str(e))
    
    async def create_refactoring_mr(
        self,
        project_id: int,
        source_branch: str,
        target_branch: str,
        mr_iid: int,
        refactorings: List[RefactoringSuggestion]
    ) -> MRCreationResult:
        """
        Create MR with significant refactoring suggestions
        
        Args:
            project_id: GitLab project ID
            source_branch: Original MR source branch
            target_branch: Original MR target branch
            mr_iid: Original MR IID
            refactorings: Refactoring suggestions
            
        Returns:
            MR creation result
        """
        try:
            refactor_branch = f"refactor/mr-{mr_iid}-ai-suggestions"
            title = f"♻️ AI Refactoring Suggestions for MR !{mr_iid}"
            description = self._generate_refactoring_description(refactorings)
            
            # TODO: Apply refactorings to files
            # For now, create MR with description only
            
            mr_data = await self.gitlab.create_merge_request(
                project_id=project_id,
                source_branch=refactor_branch,
                target_branch=source_branch,  # Target is original MR branch
                title=title,
                description=description,
                labels=["ai-review", "refactoring"]
            )
            
            logger.info(f"Created refactoring MR: !{mr_data['iid']}")
            return MRCreationResult(
                success=True,
                mr_iid=mr_data['iid'],
                mr_url=mr_data['web_url']
            )
            
        except Exception as e:
            logger.error(f"Failed to create refactoring MR: {str(e)}")
            return MRCreationResult(success=False, error=str(e))
    
    def _generate_documentation_commit_message(
        self,
        documentation: List[DocumentationAddition]
    ) -> str:
        """Generate commit message for documentation improvements"""
        files = set(doc.file for doc in documentation)
        return f"docs: Add Javadoc and comments ({len(documentation)} additions in {len(files)} files) [skip ci]"
    
    def _generate_fixes_description(
        self,
        issues: List[ReviewIssue],
        minor_refactoring: Optional[List[RefactoringSuggestion]] = None
    ) -> str:
        """Generate MR description for fixes"""
        lines = [
            "# 🔧 AI Review Fixes",
            "",
            "This MR contains automatic fixes for critical and high-severity issues found by AI code review.",
            "",
            "## Fixed Issues",
            ""
        ]
        
        # Group by severity
        for severity in [IssueSeverity.CRITICAL, IssueSeverity.HIGH]:
            severity_issues = [i for i in issues if i.severity == severity]
            if severity_issues:
                icon = "🔴" if severity == IssueSeverity.CRITICAL else "🟠"
                lines.append(f"### {icon} {severity.value} Issues")
                lines.append("")
                for issue in severity_issues:
                    lines.append(f"- **{issue.category}** in `{issue.file}:{issue.line}`")
                    lines.append(f"  - Issue: {issue.message}")
                    lines.append(f"  - Fix: {issue.suggestion}")
                    lines.append("")
        
        if minor_refactoring:
            lines.append("## Minor Refactoring")
            lines.append("")
            lines.append("The following minor refactoring improvements are also included:")
            lines.append("")
            for refactor in minor_refactoring[:5]:  # Limit to 5
                lines.append(f"- {refactor.message} (`{refactor.file}`)")
            if len(minor_refactoring) > 5:
                lines.append(f"- ... and {len(minor_refactoring) - 5} more")
            lines.append("")
        
        lines.append("---")
        lines.append("*Generated by AI Code Review System*")
        
        return "\n".join(lines)
    
    def _generate_refactoring_description(
        self,
        refactorings: List[RefactoringSuggestion]
    ) -> str:
        """Generate MR description for refactoring"""
        lines = [
            "# ♻️ AI Refactoring Suggestions",
            "",
            "This MR contains significant refactoring suggestions to improve code quality and maintainability.",
            "",
            "⚠️ **Important**: These are suggestions, not critical fixes. Review carefully before merging.",
            "",
            "## Refactoring Summary",
            ""
        ]
        
        # Group by file
        files_map = {}
        for refactor in refactorings:
            if refactor.file not in files_map:
                files_map[refactor.file] = []
            files_map[refactor.file].append(refactor)
        
        for file, file_refactors in files_map.items():
            lines.append(f"### `{file}`")
            lines.append("")
            for refactor in file_refactors:
                effort_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(refactor.effort, "⚪")
                lines.append(f"- {effort_icon} **{refactor.category}** (Effort: {refactor.effort})")
                lines.append(f"  - {refactor.message}")
                lines.append(f"  - Suggestion: {refactor.suggestion}")
                lines.append("")
        
        lines.append("## Review Checklist")
        lines.append("")
        lines.append("- [ ] All suggestions reviewed and understood")
        lines.append("- [ ] Tests updated if needed")
        lines.append("- [ ] No breaking changes introduced")
        lines.append("- [ ] Code still meets requirements")
        lines.append("")
        lines.append("---")
        lines.append("*Generated by AI Code Review System*")
        
        return "\n".join(lines)


