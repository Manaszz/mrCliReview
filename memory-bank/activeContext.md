# Active Context

## Current Work Focus

### Recent Changes

Based on git status, recent modifications include:

- **Modified**: `app/api/routes.py` - API route updates
- **Modified**: `app/services/git_repository_manager.py` - Git operations improvements
- **Deleted**: `docs/CLI_GITLAB_ACCESS.md` - Documentation cleanup
- **New**: `docs/CLI_DIRECT_GIT_ACCESS.md` - New documentation
- **New**: `docs/CLI_GIT_DIFFS.md` - Git diff documentation
- **New**: `docs/CLI_RESPONSIBILITY_SEPARATION.md` - Responsibility separation docs
- **New**: `CLI_RESPONSIBILITY_QUICK.md` - Quick reference guide

### Current State

The system is in **active development** with core functionality implemented:

- ✅ FastAPI REST API with 3 endpoints
- ✅ Dual CLI agent support (Cline/Qwen Code)
- ✅ 11 review types implemented
- ✅ Git repository management
- ✅ GitLab integration (minimal API usage)
- ✅ Smart refactoring classification
- ✅ Docker and Kubernetes deployment configs
- ✅ Comprehensive documentation (Russian)

### Next Steps

1. **Memory Bank Initialization** (Current)
   - Creating Memory Bank structure
   - Documenting project context
   - Establishing patterns and preferences

2. **Testing & Validation**
   - Complete test coverage
   - Integration testing with GitLab
   - Performance testing

3. **Production Readiness**
   - Security audit
   - Performance optimization
   - Monitoring setup

4. **Phase 2 Features** (Planned)
   - JIRA Task Matcher Agent
   - Changelog Generator Agent
   - Library Updater Agent

## Active Decisions and Considerations

### Decision: CLI Direct Git Access

**Context**: CLI agents should use Git CLI directly rather than relying on API-provided file lists.

**Rationale**:
- CLI agents work best with local Git repositories
- `git diff` provides accurate change detection
- Reduces coupling between API and CLI
- Better performance for large diffs

**Implementation**: 
- Removed `changed_files` parameter from API
- CLI agents automatically detect changes via `git diff`
- Documented in `docs/CLI_DIRECT_GIT_ACCESS.md`

### Decision: Responsibility Separation

**Context**: Clear separation of responsibilities between API layer and CLI agents.

**Rationale**:
- API handles orchestration and GitLab integration
- CLI agents handle code analysis
- Clear boundaries improve maintainability

**Implementation**:
- Documented in `docs/CLI_RESPONSIBILITY_SEPARATION.md`
- Quick reference in `CLI_RESPONSIBILITY_QUICK.md`

### Decision: Git Diff Strategy

**Context**: CLI agents need to understand what changed in the MR.

**Rationale**:
- Compare source branch against target branch
- CLI agents can use `git diff` for context
- More accurate than API-based diffs

**Implementation**:
- Documented in `docs/CLI_GIT_DIFFS.md`
- GitRepositoryManager clones with target branch reference

## Important Patterns and Preferences

### Code Organization

- **Service Layer**: Business logic in `app/services/`
- **API Layer**: REST endpoints in `app/api/routes.py`
- **Models**: Pydantic models in `app/models.py`
- **Utils**: Helpers in `app/utils/`

### Error Handling

- **Structured Logging**: All errors logged with correlation IDs
- **Graceful Degradation**: Partial success better than complete failure
- **Retry Logic**: Exponential backoff for transient failures
- **Fallback**: Switch to alternative agent if primary fails

### Git Operations

- **Prefer Git CLI**: Use Git CLI over GitLab API for repository operations
- **Isolation**: Each review clones to isolated directory
- **Cleanup**: Always cleanup cloned repositories after review
- **Idempotent**: Git operations should be idempotent

### CLI Agent Usage

- **Single Agent**: Always use one agent per review, never both
- **Parallel Execution**: Execute multiple review types in parallel (within agent capacity)
- **Timeout Handling**: 5-minute timeout per review type
- **Output Parsing**: Robust parsing with fallback on malformed output

## Learnings and Project Insights

### Key Learnings

1. **CLI Agents Require Full Context**: CLI agents work best with complete repository clones, not just changed files
2. **Git Diff is Accurate**: Using `git diff` is more reliable than API-provided file lists
3. **Parallel Execution is Critical**: Parallel execution significantly improves review speed
4. **Smart Classification Matters**: Separating SIGNIFICANT refactorings improves developer acceptance

### Project Insights

#### What Works Well

- ✅ Minimal GitLab API usage reduces rate limit issues
- ✅ CLI-based agents provide better code understanding
- ✅ Hierarchical rules system enables customization
- ✅ Smart refactoring classification improves developer workflow

#### Challenges

- ⚠️ CLI output parsing can be brittle
- ⚠️ Model API rate limits require careful management
- ⚠️ Large MRs (>10K lines) can timeout
- ⚠️ Parallel execution requires careful resource management

### Automation Sync

**Consistency Checks**:
- `.cursorrules` should align with `systemPatterns.md`
- Environment variables documented in `techContext.md`
- Project structure matches `projectbrief.md`

## Tags for Quick Navigation

- `#architecture` - System architecture decisions
- `#cli-agents` - CLI agent usage patterns
- `#git-operations` - Git and GitLab integration
- `#error-handling` - Error handling and recovery patterns
- `#deployment` - Deployment and scaling considerations
- `#refactoring` - Refactoring classification logic
- `#rules-system` - Hierarchical rules system

