"""
Pydantic models for Code Review API

Defines request/response models for the multi-agent code review system.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ========================
# Enums
# ========================

class CLIAgent(str, Enum):
    """CLI agents for code review"""
    CLINE = "CLINE"  # DeepSeek V3.1 Terminus, 5 parallel tasks
    QWEN_CODE = "QWEN_CODE"  # Qwen3-Coder-32B, 3 parallel tasks


class ReviewType(str, Enum):
    """Types of code review checks"""
    ERROR_DETECTION = "ERROR_DETECTION"
    BEST_PRACTICES = "BEST_PRACTICES"
    REFACTORING = "REFACTORING"
    SECURITY_AUDIT = "SECURITY_AUDIT"
    DOCUMENTATION = "DOCUMENTATION"
    PERFORMANCE = "PERFORMANCE"
    ARCHITECTURE = "ARCHITECTURE"
    TRANSACTION_MANAGEMENT = "TRANSACTION_MANAGEMENT"
    CONCURRENCY = "CONCURRENCY"
    DATABASE_OPTIMIZATION = "DATABASE_OPTIMIZATION"
    UNIT_TEST_COVERAGE = "UNIT_TEST_COVERAGE"  # Check unit test coverage and generate missing tests
    MEMORY_BANK = "MEMORY_BANK"  # Initialize or validate project memory bank
    ALL = "ALL"  # Execute all review types


class Language(str, Enum):
    """Supported programming languages"""
    JAVA = "java"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    KOTLIN = "kotlin"
    SCALA = "scala"


class IssueSeverity(str, Enum):
    """Issue severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RefactoringImpact(str, Enum):
    """Refactoring impact classification"""
    SIGNIFICANT = "SIGNIFICANT"  # Separate MR required
    MINOR = "MINOR"  # Can combine with fixes


class MRType(str, Enum):
    """Types of merge requests created by the system"""
    DOCUMENTATION = "DOCUMENTATION"  # Documentation improvements
    FIXES = "FIXES"  # Critical bug fixes
    REFACTORING = "REFACTORING"  # Significant refactoring
    COMBINED = "COMBINED"  # Fixes + minor refactoring


# ========================
# Request Models
# ========================

class ReviewRequest(BaseModel):
    """Request for code review via CLI agent"""
    agent: CLIAgent = Field(
        default=CLIAgent.CLINE,
        description="CLI agent to use for review (CLINE or QWEN_CODE)"
    )
    review_types: List[ReviewType] = Field(
        default=[ReviewType.ALL],
        description="Types of checks to perform. If ALL is included, all checks are executed."
    )
    project_id: int = Field(
        ...,
        description="GitLab project ID",
        gt=0
    )
    merge_request_iid: int = Field(
        ...,
        description="Merge request IID (internal ID)",
        gt=0
    )
    language: Language = Field(
        default=Language.JAVA,
        description="Primary programming language of the project"
    )
    jira_context: Optional[str] = Field(
        None,
        description="JIRA task ID and context for understanding intent"
    )
    confluence_rules: Optional[str] = Field(
        None,
        description="Custom rules from Confluence (markdown content)"
    )

    @field_validator('review_types')
    @classmethod
    def validate_review_types(cls, v: List[ReviewType]) -> List[ReviewType]:
        """Ensure at least one review type is specified"""
        if not v:
            return [ReviewType.ALL]
        return v


class ValidateMRRequest(BaseModel):
    """Request for MR validation (used by n8n LangChain Code Node)"""
    project_id: int = Field(..., gt=0)
    merge_request_iid: int = Field(..., gt=0)


# ========================
# Issue Models
# ========================

class ReviewIssue(BaseModel):
    """A single issue found during review"""
    file: str = Field(..., description="File path relative to repository root")
    line: Optional[int] = Field(None, description="Line number where issue occurs", ge=1)
    severity: IssueSeverity = Field(..., description="Issue severity level")
    category: str = Field(..., description="Issue category (e.g., 'NullPointerException Risk')")
    message: str = Field(..., description="Description of the issue")
    code_snippet: Optional[str] = Field(None, description="Code snippet showing the issue")
    suggestion: str = Field(..., description="How to fix the issue")
    auto_fixable: bool = Field(False, description="Whether issue can be automatically fixed")
    cwe: Optional[str] = Field(None, description="CWE reference for security issues (e.g., 'CWE-89')")
    rule_source: str = Field(
        default="default",
        description="Source of rule: 'default', 'project_custom', 'confluence'"
    )


class RefactoringSuggestion(BaseModel):
    """A refactoring suggestion"""
    file: str
    line: Optional[int] = None
    severity: IssueSeverity
    category: str
    message: str
    code_snippet: Optional[str] = None
    suggestion: str
    impact: RefactoringImpact = Field(..., description="SIGNIFICANT or MINOR")
    effort: str = Field(..., description="Estimated effort: LOW, MEDIUM, HIGH")
    auto_fixable: bool = False


class DocumentationAddition(BaseModel):
    """Generated documentation to be added"""
    file: str
    line: int
    type: str = Field(..., description="Type: CLASS_JAVADOC, METHOD_JAVADOC, INLINE_COMMENT")
    generated_doc: str = Field(..., description="Generated documentation content")
    reason: str = Field(..., description="Why this documentation was generated")


# ========================
# Result Models
# ========================

class ReviewSummary(BaseModel):
    """Summary of review results"""
    total_issues: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    files_analyzed: int = 0
    auto_fixable_count: int = 0


class ReviewResult(BaseModel):
    """Complete result of code review"""
    review_type: ReviewType
    agent: CLIAgent
    issues: List[ReviewIssue] = Field(default_factory=list)
    refactoring_suggestions: List[RefactoringSuggestion] = Field(default_factory=list)
    documentation_additions: List[DocumentationAddition] = Field(default_factory=list)
    summary: ReviewSummary
    
    # Actions taken
    documentation_committed: bool = Field(
        False,
        description="Whether documentation improvements were committed to source branch"
    )
    doc_commit_sha: Optional[str] = Field(None, description="Git commit SHA for documentation")
    
    fix_mr_created: bool = Field(False, description="Whether fix MR was created")
    fix_mr_url: Optional[str] = Field(None, description="URL of created fix MR")
    fix_mr_iid: Optional[int] = Field(None, description="IID of created fix MR")
    
    refactoring_mr_created: bool = Field(
        False,
        description="Whether separate refactoring MR was created (for SIGNIFICANT refactoring)"
    )
    refactoring_mr_url: Optional[str] = Field(None, description="URL of created refactoring MR")
    refactoring_mr_iid: Optional[int] = Field(None, description="IID of created refactoring MR")
    
    # Metadata
    execution_time_seconds: float = Field(0.0, description="Time taken for review")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Result of MR validation"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    jira_ticket: Optional[str] = None
    completeness_score: int = Field(0, ge=0, le=100)
    warnings: List[str] = Field(default_factory=list)


# ========================
# MR Models
# ========================

class MRCreationRequest(BaseModel):
    """Request to create a merge request"""
    project_id: int = Field(..., gt=0)
    source_branch: str
    target_branch: str
    title: str
    description: str
    mr_type: MRType
    labels: List[str] = Field(default_factory=list)
    assignee_id: Optional[int] = None


class MRCreationResult(BaseModel):
    """Result of MR creation"""
    success: bool
    mr_iid: Optional[int] = None
    mr_url: Optional[str] = None
    error: Optional[str] = None


# ========================
# Configuration Models
# ========================

class CLIConfig(BaseModel):
    """CLI agent configuration"""
    agent: CLIAgent
    model_api_url: str
    model_name: str
    api_key: str
    parallel_tasks: int = Field(ge=1, le=10)
    timeout_seconds: int = Field(300, ge=60, le=1800)
    max_context_size: int = Field(100000, ge=10000, le=200000)


class RulesConfig(BaseModel):
    """Rules loading configuration"""
    default_rules_path: str = "rules/java-spring-boot"
    project_rules_path: Optional[str] = None
    confluence_rules_enabled: bool = False
    confluence_rules_content: Optional[str] = None


# ========================
# Health Check Models
# ========================

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="healthy or unhealthy")
    version: str = Field(..., description="API version")
    cline_available: bool = Field(..., description="Whether Cline CLI is available")
    qwen_available: bool = Field(..., description="Whether Qwen Code CLI is available")
    model_api_connected: bool = Field(..., description="Whether model API is reachable")
    gitlab_connected: bool = Field(..., description="Whether GitLab API is reachable")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ========================
# Error Response Models
# ========================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Standard success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ========================
# Statistics Models
# ========================

class ReviewStatistics(BaseModel):
    """Statistics about reviews performed"""
    total_reviews: int = 0
    total_issues_found: int = 0
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    auto_fixed_issues: int = 0
    average_review_time_seconds: float = 0.0
    fix_mrs_created: int = 0
    refactoring_mrs_created: int = 0
    documentation_commits: int = 0


# ========================
# TODO Agent Models (Stubs)
# ========================

class JiraTaskMatchResult(BaseModel):
    """Result of JIRA task matching analysis (TODO)"""
    completion_percentage: int = Field(0, ge=0, le=100)
    requirements_found: int = 0
    requirements_implemented: int = 0
    requirements_missing: int = 0
    unimplemented: List[Dict[str, str]] = Field(default_factory=list)
    assessment: str = Field("NOT_ANALYZED", description="FULLY_COMPLETE, MOSTLY_COMPLETE, PARTIALLY_COMPLETE, NOT_MATCHING")
    recommendation: Optional[str] = None


class ChangelogEntry(BaseModel):
    """Generated changelog entry (TODO)"""
    version: str
    date: str
    sections: Dict[str, List[str]]  # Added, Changed, Fixed, Security, etc.
    markdown: str
    commit_message: str


class LibraryUpdateSuggestion(BaseModel):
    """Library update suggestion (TODO)"""
    library: str
    current_version: str
    latest_version: str
    breaking_changes: bool
    security_fixes: List[str] = Field(default_factory=list)
    migration_notes: Optional[str] = None
    priority: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL")
