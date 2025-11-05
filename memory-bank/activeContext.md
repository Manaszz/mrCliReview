# Active Context

## Current Work Focus

### Recent Changes (2025-11-05)

**Latest**: Prompt File Embedding Feature

#### Prompt File Embedding (2025-11-05)
- **Implemented**: Automatic embedding of referenced files into prompts
- **Purpose**: CLI agents now receive complete, self-contained instructions
- **Mechanism**: `ReviewService._embed_referenced_files()` method
- **Files Embedded**: 
  - `prompts/common/critical_json_requirements.md` (315 lines)
  - `prompts/common/git_diff_instructions.md` (145 lines)
  - `schemas/review_result_schema.json` (261 lines)
- **Coverage**: All 12 prompts (7 Cline + 5 Qwen) now include JSON Schema reference
- **Removed**: `prompts/common/json_output_requirements.md` (duplicate, unused)
- **Tests**: 9 comprehensive tests in `tests/test_prompt_embedding.py` ✅
- **Documentation**: `docs/PROMPT_FILE_EMBEDDING.md`

---

### Previous Changes (2025-11-04)

Latest modifications:

#### New Features
- **Added**: Two new ReviewType enums:
  - `UNIT_TEST_COVERAGE` (обязательный) - Automated test coverage analysis and generation
  - `MEMORY_BANK` (опциональный) - Project Memory Bank initialization and validation
  
- **Created**: Prompt templates for new review types:
  - `prompts/cline/unit_test_coverage.md`
  - `prompts/cline/memory_bank.md`
  - `prompts/qwen/unit_test_coverage.md`
  - `prompts/qwen/memory_bank.md`

- **Enhanced**: System prompt (`prompts/system_prompt.md`):
  - Added Memory Bank integration instructions
  - Agents now check for `memory-bank/` directory
  - Automatic context loading from Memory Bank files

- **Improved**: MR creation logic (`app/services/mr_creator.py`):
  - Clarified comments: fix/refactor MRs target source_branch (not target_branch)
  - Flow: `fix branch -> source_branch -> target_branch`
  - Allows developers to accept fixes before merging to target

#### Bug Fixes & Improvements
- **Fixed**: Active review tracking (`app/services/git_repository_manager.py`):
  - Added concurrency control to prevent duplicate reviews
  - Now returns error if MR review already in progress
  - Proper cleanup of review tracking on repository cleanup

#### Documentation
- **New**: `docs/NEW_REVIEW_TYPES.md` - Comprehensive guide for new review types
- **Updated**: Memory Bank files to reflect current state

Previous changes:
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
- ✅ 13 review types implemented (added UNIT_TEST_COVERAGE, MEMORY_BANK)
- ✅ Git repository management with concurrency control
- ✅ GitLab integration (minimal API usage)
- ✅ Smart refactoring classification
- ✅ System prompt with Memory Bank integration
- ✅ Docker and Kubernetes deployment configs
- ✅ Comprehensive documentation (Russian)

### Next Steps

1. **Testing New Review Types** (Next)
   - Test UNIT_TEST_COVERAGE with real MRs
   - Test MEMORY_BANK initialization
   - Validate generated test code quality
   - Validate Memory Bank content accuracy

2. **Testing & Validation**
   - Complete test coverage for new features
   - Integration testing with GitLab
   - Performance testing with new review types

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

### Decision: Fix/Refactor MR Target Branch

**Context**: Where should fix and refactor MRs be merged?

**Decision**: Target the **original MR source branch**, NOT the target branch.

**Rationale**:
- Developers can review and accept fixes in their feature branch
- Then merge the complete, fixed feature branch to target (e.g., develop)
- Flow: `fix/mr-X-ai-fixes` → `feature/developer-branch` → `develop`

**Implementation**:
- `MRCreator.create_fixes_mr()` sets `target_branch=source_branch`
- `MRCreator.create_refactoring_mr()` sets `target_branch=source_branch`
- Documented in code comments

### Decision: Concurrent Review Prevention

**Context**: Multiple review requests for the same MR can cause conflicts.

**Decision**: Block concurrent reviews of the same MR.

**Rationale**:
- Prevents repository clone conflicts
- Avoids duplicate work
- Ensures clean review state

**Implementation**:
- `GitRepositoryManager` tracks active reviews via `_active_reviews` set
- `_review_lock` ensures atomic check-and-add operations
- Returns error if review already in progress
- Cleanup removes from tracking set

### Decision: Memory Bank Integration

**Context**: How to provide project context to CLI agents?

**Decision**: Use Cursor's Memory Bank (v1.2 Final) methodology with automatic detection and MR-based updates.

**Rationale**:
- Structured knowledge base improves review quality
- Agents can understand project-specific patterns
- Preserves architectural decisions and rationale
- Living documentation that evolves with project
- **Automatic updates keep Memory Bank current**

**Implementation**:
- System prompt instructs agents to check for `memory-bank/` directory
- If exists, agents read key files for context
- MEMORY_BANK review type has 3 modes:
  1. **Update** (PRIMARY): Analyzes MR changes and updates Memory Bank
  2. **Validate** (rare): Checks structure completeness
  3. **Initialize**: Creates new Memory Bank from scratch
- **Architecture** (follows CLI/FastAPI separation):
  - CLI Agent: Analyzes MR, WRITES updated content to files
  - FastAPI: Detects changes, commits with `[skip ci]`, pushes to MR branch
- Documented in `docs/NEW_REVIEW_TYPES.md`

### Decision: Unit Test Coverage Automation

**Context**: Many MRs lack adequate test coverage.

**Decision**: Add mandatory UNIT_TEST_COVERAGE review type.

**Rationale**:
- Automated test generation improves code quality
- Reduces manual test writing burden
- Ensures consistent test patterns
- Follows project conventions (JUnit5, Mockito, TestContainers)

**Implementation**:
- New ReviewType: `UNIT_TEST_COVERAGE`
- Generates complete, ready-to-use test code
- Uses project's `*Base` test classes (JupiterBase, etc.)
- Documented in `docs/NEW_REVIEW_TYPES.md`

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

### Git Commit Policy

- **NEVER commit without explicit user request**
- User must explicitly say: "commit", "закоммить", "commit and push", or similar
- After making changes: show what changed and WAIT for user decision
- This rule applies to ALL changes, including documentation updates

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

