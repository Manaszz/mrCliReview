"""
API Routes

REST API endpoints for code review system.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, Any
import logging

from app.models import (
    ReviewRequest,
    ReviewResult,
    ValidateMRRequest,
    ValidationResult,
    HealthCheckResponse,
    ErrorResponse
)
from app.services.review_service import ReviewService
from app.services.gitlab_service import GitLabService
from app.services.git_repository_manager import GitRepositoryManager
from app.services.refactoring_classifier import RefactoringClassifier
from app.services.mr_creator import MRCreator
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["review"])

settings = get_settings()


# Dependency injection
def get_review_service() -> ReviewService:
    """Get ReviewService instance"""
    from app.dependencies import get_review_service_instance
    return get_review_service_instance()


def get_gitlab_service() -> GitLabService:
    """Get GitLabService instance"""
    return GitLabService(
        gitlab_url=settings.GITLAB_URL,
        gitlab_token=settings.GITLAB_TOKEN
    )


def get_git_manager() -> GitRepositoryManager:
    """Get GitRepositoryManager instance"""
    return GitRepositoryManager(work_dir=settings.WORK_DIR)


@router.post(
    "/review",
    response_model=ReviewResult,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Execute Code Review",
    description="Выполнить code review для GitLab merge request с помощью CLI агентов"
)
async def review_merge_request(
    request: ReviewRequest,
    background_tasks: BackgroundTasks,
    review_service: ReviewService = Depends(get_review_service),
    gitlab_service: GitLabService = Depends(get_gitlab_service),
    git_manager: GitRepositoryManager = Depends(get_git_manager)
) -> ReviewResult:
    """
    Выполнить code review для merge request
    
    Процесс:
    1. Получить данные MR из GitLab
    2. Клонировать репозиторий
    3. Выполнить review через CLI агент (changed_files определяются CLI автоматически)
    4. Создать documentation commit
    5. Создать fix и/или refactoring MRs
    6. Опубликовать результаты в комментарий MR
    """
    repo_path = None
    
    try:
        logger.info(f"Starting review for project {request.project_id}, MR !{request.merge_request_iid}")
        
        # Get MR data
        mr_data = await gitlab_service.get_merge_request(
            project_id=request.project_id,
            mr_iid=request.merge_request_iid
        )
        
        # Get project data for clone URL
        project_data = await gitlab_service.get_project(request.project_id)
        clone_url = gitlab_service.get_clone_url(project_data)
        
        # Clone repository with target branch for diff
        repo_path = await git_manager.clone_repository(
            clone_url=clone_url,
            branch=mr_data['source_branch'],
            project_id=request.project_id,
            mr_iid=request.merge_request_iid,
            target_branch=mr_data['target_branch']  # For git diff comparison
        )
        
        logger.info(f"Repository cloned to {repo_path}")
        
        # Execute review (CLI determines changed files automatically via git diff)
        result = await review_service.execute_review(
            request=request,
            repo_path=repo_path
        )
        
        # Process results in background
        background_tasks.add_task(
            process_review_results,
            result=result,
            request=request,
            mr_data=mr_data,
            repo_path=repo_path,
            gitlab_service=gitlab_service,
            git_manager=git_manager
        )
        
        logger.info(f"Review completed: {result.summary.total_issues} issues found")
        return result
        
    except Exception as e:
        logger.error(f"Error during review: {str(e)}", exc_info=True)
        # Cleanup on error
        if repo_path:
            background_tasks.add_task(git_manager.cleanup_repository, repo_path)
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")


async def process_review_results(
    result: ReviewResult,
    request: ReviewRequest,
    mr_data: Dict[str, Any],
    repo_path: str,
    gitlab_service: GitLabService,
    git_manager: GitRepositoryManager
):
    """
    Process review results (runs in background):
    - Commit documentation
    - Create fix/refactoring MRs
    - Post comment to original MR
    - Cleanup repository
    """
    try:
        # Initialize MR creator
        mr_creator = MRCreator(gitlab_service, git_manager)
        refactor_classifier = RefactoringClassifier()
        
        # 1. Commit documentation if any
        if result.documentation_additions:
            doc_sha = await mr_creator.create_documentation_commit(
                repo_path=repo_path,
                source_branch=mr_data['source_branch'],
                documentation=result.documentation_additions,
                project_id=request.project_id
            )
            result.documentation_committed = True
            result.doc_commit_sha = doc_sha
            logger.info(f"Documentation committed: {doc_sha}")
        
        # 2. Classify refactoring
        if result.refactoring_suggestions:
            refactor_impact = refactor_classifier.classify(result.refactoring_suggestions)
            significant, minor = refactor_classifier.separate_refactorings(result.refactoring_suggestions)
            
            # 3. Create fixes MR (with minor refactoring if any)
            if result.issues:
                fix_mr_result = await mr_creator.create_fixes_mr(
                    project_id=request.project_id,
                    source_branch=mr_data['source_branch'],
                    target_branch=mr_data['target_branch'],
                    mr_iid=request.merge_request_iid,
                    issues=result.issues,
                    minor_refactoring=minor if minor else None
                )
                if fix_mr_result.success:
                    result.fix_mr_created = True
                    result.fix_mr_url = fix_mr_result.mr_url
                    result.fix_mr_iid = fix_mr_result.mr_iid
                    logger.info(f"Fixes MR created: !{fix_mr_result.mr_iid}")
            
            # 4. Create refactoring MR if significant
            if significant:
                refactor_mr_result = await mr_creator.create_refactoring_mr(
                    project_id=request.project_id,
                    source_branch=mr_data['source_branch'],
                    target_branch=mr_data['target_branch'],
                    mr_iid=request.merge_request_iid,
                    refactorings=significant
                )
                if refactor_mr_result.success:
                    result.refactoring_mr_created = True
                    result.refactoring_mr_url = refactor_mr_result.mr_url
                    result.refactoring_mr_iid = refactor_mr_result.mr_iid
                    logger.info(f"Refactoring MR created: !{refactor_mr_result.mr_iid}")
        
        # 5. Post summary comment to original MR
        comment = generate_review_comment(result)
        await gitlab_service.post_mr_comment(
            project_id=request.project_id,
            mr_iid=request.merge_request_iid,
            comment=comment
        )
        logger.info(f"Posted review comment to MR !{request.merge_request_iid}")
        
    except Exception as e:
        logger.error(f"Error processing review results: {str(e)}", exc_info=True)
    finally:
        # Always cleanup repository
        await git_manager.cleanup_repository(repo_path)
        logger.info(f"Cleaned up repository: {repo_path}")


def generate_review_comment(result: ReviewResult) -> str:
    """Generate markdown comment for MR"""
    status_icon = "❌" if result.summary.critical > 0 else ("⚠️" if result.summary.high > 0 else "✅")
    status_text = "FAILED" if result.summary.critical > 0 else ("WARNING" if result.summary.high > 0 else "PASSED")
    
    lines = [
        f"## {status_icon} Code Review Results - {status_text}",
        "",
        f"**Agent**: {result.agent.value}",
        f"**Review Types**: {result.review_type.value}",
        f"**Execution Time**: {result.execution_time_seconds:.1f}s",
        "",
        "### Issue Summary",
        "",
        "| Severity | Count |",
        "|----------|-------|",
        f"| 🔴 Critical | {result.summary.critical} |",
        f"| 🟠 High | {result.summary.high} |",
        f"| 🟡 Medium | {result.summary.medium} |",
        f"| 🔵 Low | {result.summary.low} |",
        f"| **Total** | **{result.summary.total_issues}** |",
        "",
    ]
    
    # Show first 5 critical issues
    critical_issues = [i for i in result.issues if i.severity.value == "CRITICAL"]
    if critical_issues:
        lines.append("### 🔴 Critical Issues")
        lines.append("")
        for issue in critical_issues[:5]:
            lines.append(f"#### {issue.category}")
            lines.append(f"**File**: `{issue.file}:{issue.line}`")
            lines.append(f"**Issue**: {issue.message}")
            lines.append(f"**Fix**: {issue.suggestion}")
            lines.append("")
        if len(critical_issues) > 5:
            lines.append(f"*... and {len(critical_issues) - 5} more critical issues*")
            lines.append("")
    
    # Actions taken
    lines.append("### Actions Taken")
    lines.append("")
    if result.documentation_committed:
        lines.append(f"- ✅ Documentation improvements committed to source branch")
    if result.fix_mr_created:
        lines.append(f"- ✅ Fix MR created: !{result.fix_mr_iid}")
    if result.refactoring_mr_created:
        lines.append(f"- ✅ Refactoring MR created: !{result.refactoring_mr_iid}")
    if not any([result.documentation_committed, result.fix_mr_created, result.refactoring_mr_created]):
        lines.append("- ℹ️ No automated actions required")
    lines.append("")
    
    lines.append("---")
    lines.append("*Powered by AI Code Review System v2.0.0*")
    
    return "\n".join(lines)


@router.post(
    "/validate-mr",
    response_model=ValidationResult,
    summary="Validate Merge Request",
    description="Валидация MR (для n8n LangChain Code Node)"
)
async def validate_merge_request(
    request: ValidateMRRequest,
    gitlab_service: GitLabService = Depends(get_gitlab_service)
) -> ValidationResult:
    """
    Validate merge request completeness
    Used by n8n workflow before triggering review
    """
    try:
        mr_data = await gitlab_service.get_merge_request(
            project_id=request.project_id,
            mr_iid=request.merge_request_iid
        )
        
        errors = []
        warnings = []
        
        # Check JIRA ticket in title
        import re
        jira_pattern = r'([A-Z]+-\d+)'
        jira_match = re.search(jira_pattern, mr_data.get('title', ''))
        jira_ticket = jira_match.group(1) if jira_match else None
        
        if not jira_ticket:
            errors.append("Missing JIRA ticket in title (format: PROJECT-123)")
        
        # Check description length
        description = mr_data.get('description', '')
        if len(description) < 50:
            errors.append("Description too short (minimum 50 characters)")
        
        # Check for placeholder text
        if any(placeholder in description for placeholder in ['TODO', 'TBD', 'FIXME']):
            warnings.append("Description contains placeholder text")
        
        completeness_score = 100
        if errors:
            completeness_score -= len(errors) * 30
        if warnings:
            completeness_score -= len(warnings) * 10
        completeness_score = max(0, completeness_score)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            jira_ticket=jira_ticket,
            completeness_score=completeness_score,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Проверка работоспособности сервиса и зависимостей"
)
async def health_check(
    review_service: ReviewService = Depends(get_review_service),
    gitlab_service: GitLabService = Depends(get_gitlab_service)
) -> HealthCheckResponse:
    """Health check endpoint"""
    try:
        # Check CLI agents
        cli_health = await review_service.health_check()
        
        # Check GitLab connection
        gitlab_connected = await gitlab_service.test_connection()
        
        status = "healthy" if all([
            cli_health.get('cline_available') or cli_health.get('qwen_available'),
            cli_health.get('model_api_connected'),
            gitlab_connected
        ]) else "unhealthy"
        
        return HealthCheckResponse(
            status=status,
            version=settings.VERSION,
            cline_available=cli_health.get('cline_available', False),
            qwen_available=cli_health.get('qwen_available', False),
            model_api_connected=cli_health.get('model_api_connected', False),
            gitlab_connected=gitlab_connected
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
