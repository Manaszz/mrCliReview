# Product Context

## Why This Project Exists

### Problem Statement

Java Spring Boot development teams face challenges in maintaining consistent code quality across merge requests:

1. **Manual Review Burden**: Code reviewers spend significant time on repetitive checks
2. **Inconsistent Standards**: Different reviewers apply different standards and priorities
3. **Missing Critical Issues**: Security vulnerabilities, performance issues, and architectural violations slip through
4. **Documentation Gaps**: Code lacks proper Javadoc and comments
5. **Refactoring Overhead**: Developers hesitate to refactor due to review complexity

### Solution Vision

An intelligent, automated code review system that:

- **Reduces Manual Work**: Automates 11 types of code checks
- **Ensures Consistency**: Applies uniform standards across all MRs
- **Catches Critical Issues**: Identifies security vulnerabilities, bugs, and performance problems before production
- **Enforces Documentation**: Automatically generates and commits Javadoc
- **Facilitates Refactoring**: Intelligently separates critical fixes from refactoring suggestions

## How It Should Work

### User Workflow

1. **Developer creates MR** in GitLab
2. **n8n workflow validates** MR title and description (JIRA ticket format, minimum description length)
3. **Review API receives request** via n8n webhook
4. **System clones repository** locally using Git CLI
5. **CLI agent analyzes code** (Cline or Qwen Code) using git diff to identify changes
6. **Multiple review types execute** in parallel (based on agent capacity)
7. **Results are processed**:
   - Documentation commits to source branch
   - Fix MR created for critical issues
   - Refactoring MR created if changes are SIGNIFICANT
8. **Summary comment posted** to original MR

### Key Interactions

#### CLI Agent Interaction
- CLI agents work inside cloned repository
- Agents automatically detect changed files via `git diff`
- Agents use local Git operations for context
- Results parsed from CLI stdout/stderr

#### GitLab Integration
- Minimal API calls: get MR metadata, get project clone URL, create MRs, post comments
- All Git operations (clone, diff, commit, push) via Git CLI
- Reduces API rate limit concerns

#### Rule System
- Hierarchical priority: Project-specific → Confluence → Default rules
- Rules loaded per review type
- Combined with prompts for CLI agent instructions

## User Experience Goals

### For Developers

- **Transparency**: Clear understanding of what was reviewed and why
- **Actionability**: Fix MRs include specific code changes ready to merge
- **Choice**: Separate refactoring MRs allow developers to choose when to apply improvements
- **Speed**: Reviews complete in <5 minutes

### For Reviewers

- **Comprehensive Coverage**: All 11 review types executed automatically
- **Prioritization**: Critical issues highlighted separately from suggestions
- **Context**: Full rationale provided for each finding

### For DevOps

- **Reliability**: Robust error handling and recovery
- **Observability**: Structured logging with correlation IDs
- **Scalability**: Horizontal scaling via Kubernetes
- **Maintainability**: Clear separation of concerns

## Success Metrics

### Coverage Metrics
- Review types executed per MR
- Issues found per type
- False positive rate (<10% target)

### Performance Metrics
- Average review time (<5 minutes target)
- API response time (p95 < 30 seconds)
- Parallel task utilization

### Quality Metrics
- Critical issues prevented
- Developer acceptance rate (>70% target)
- Refactoring adoption rate (>50% target)

### Developer Satisfaction
- Manual review time saved
- Review quality score (>4.0/5.0 target)
- False negative rate (<5% target)

