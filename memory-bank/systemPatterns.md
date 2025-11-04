# System Patterns

## Architecture Overview

```
┌─────────────────┐
│   GitLab MR     │
│     Event       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  n8n Workflow   │
│  (Validation)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Review API     │
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Review Service  │
│ (Orchestration) │
└────────┬────────┘
         │
    ┌────┴────┐
    │        │
    ▼        ▼
┌────────┐ ┌──────────┐
│ Cline  │ │  Qwen   │
│  CLI   │ │   CLI   │
└────────┘ └──────────┘
    │          │
    └────┬─────┘
         │
         ▼
┌─────────────────┐
│ Cloned Repo     │
│ (Git CLI)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Results Process │
│ - Doc commits   │
│ - Fix MRs       │
│ - Refactor MRs  │
└─────────────────┘
```

## Key Technical Decisions

### 1. CLI-Based Agents (Not Direct Model Calls)

**Pattern**: Use CLI tools (Cline/Qwen Code) instead of direct API calls to language models

**Rationale**:
- CLI agents have built-in context management and memory
- Better code understanding through native repository indexing
- Multi-file analysis and cross-reference capabilities
- Ability to work with large codebases through intelligent chunking
- Built-in diff analysis and change detection

**Implementation**:
```python
# CLI executed via subprocess
process = await asyncio.create_subprocess_exec(
    "cline", "review",
    "--model", model_name,
    "--api-base", api_url,
    cwd=repo_path,  # CLI works inside repository
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE
)
```

### 2. Single Agent Execution (Not Combined)

**Pattern**: Always execute either Cline OR Qwen Code, never both simultaneously

**Rationale**:
- Prevents conflicting recommendations
- Simpler result interpretation
- Lower resource consumption
- Clearer responsibility attribution
- Easier debugging and issue tracking

**Implementation**:
```python
# Agent selection logic
cli_manager = self._get_cli_manager(request.agent)
# Only one manager executes all review types
```

### 3. Minimal GitLab API Usage

**Pattern**: Clone repository locally and perform all analysis on cloned code

**Rationale**:
- Reduces API rate limit concerns
- Enables CLI agents to use native git operations
- Better performance for large diffs
- CLI agents work best with local repositories
- Simpler error handling

**Implementation**:
- Git operations: `git clone`, `git diff`, `git commit`, `git push` via Git CLI
- GitLab API: Only for MR metadata, clone URL, creating MRs, posting comments

### 4. Repository Cloning Strategy

**Pattern**: Clone entire MR source branch for each review

**Rationale**:
- CLI agents require full repository context
- Enables accurate cross-file analysis
- Allows agents to understand project structure
- Supports refactoring suggestions that span multiple files
- Cleanup after review maintains isolation

**Implementation**:
```python
repo_path = await git_manager.clone_repository(
    clone_url=clone_url,
    branch=mr_data['source_branch'],
    project_id=project_id,
    mr_iid=mr_iid,
    target_branch=mr_data['target_branch']  # For git diff comparison
)
```

### 5. Parallel Execution with Semaphore

**Pattern**: Execute multiple review types in parallel with resource limits

**Rationale**:
- Cline supports 5 parallel tasks, Qwen supports 3
- Prevents resource exhaustion
- Faster overall review completion
- Better Model API utilization

**Implementation**:
```python
semaphore = asyncio.Semaphore(parallel_tasks)

async with semaphore:
    result = await cli_manager.execute_review(...)
```

### 6. Smart Refactoring Classification

**Pattern**: Classify refactoring suggestions as SIGNIFICANT or MINOR

**Rationale**:
- SIGNIFICANT refactorings warrant separate MRs (developer choice)
- MINOR refactorings can be included in fix MRs
- Clear criteria for classification

**Criteria**:
- **SIGNIFICANT**: >3 classes affected, breaking changes, >200 LOC, DI structure changes, pattern migrations
- **MINOR**: Variable renames, constant extraction, formatting, conditional simplification

**Implementation**:
```python
if refactoring_classifier.classify(suggestions) == "SIGNIFICANT":
    create_separate_refactoring_mr()
else:
    include_in_fixes_mr()
```

### 7. Hierarchical Rules System

**Pattern**: Three-tier rule priority system

**Priority Order**:
1. Project-specific rules (`.project-rules/` in repository root)
2. Confluence rules (fetched via n8n workflow)
3. Default rules (`rules/java-spring-boot/` in review service)

**Implementation**:
```python
rules = self.rules_loader.load_rules(
    language=request.language.value,
    repo_path=repo_path,
    confluence_rules=request.confluence_rules
)
```

## Component Relationships

### Service Layer

- **ReviewService**: Main orchestrator
  - Coordinates CLI managers
  - Loads rules and prompts
  - Executes reviews in parallel
  - Aggregates results

- **ClineCLIManager / QwenCodeCLIManager**: CLI execution
  - Execute CLI commands
  - Parse outputs
  - Handle errors and timeouts

- **GitRepositoryManager**: Git operations
  - Clone repositories
  - Git diff operations
  - Commit and push changes

- **GitLabService**: GitLab API integration
  - Get MR metadata
  - Create MRs
  - Post comments

- **RefactoringClassifier**: Classification logic
  - Analyze refactoring impact
  - Classify as SIGNIFICANT/MINOR

- **MRCreator**: MR creation
  - Create fix MRs
  - Create refactoring MRs
  - Format descriptions

- **CustomRulesLoader**: Rules management
  - Load project-specific rules
  - Load Confluence rules
  - Load default rules
  - Combine rules by priority

## Critical Implementation Paths

### Review Execution Flow

1. **Request received** → Validate request
2. **Get MR data** → Fetch from GitLab API
3. **Clone repository** → Git CLI operation
4. **Load rules** → Hierarchical rule loading
5. **Load prompts** → Agent-specific prompts
6. **Execute reviews** → Parallel CLI execution
7. **Process results** → Parse and aggregate
8. **Create commits** → Documentation commits
9. **Create MRs** → Fix and refactoring MRs
10. **Post comment** → Summary to original MR
11. **Cleanup** → Remove cloned repository

### Error Handling Patterns

- **CLI Timeout**: Retry with exponential backoff, fallback to other agent
- **Model API Error**: Retry with jitter, switch to backup endpoint
- **GitLab API Error**: Idempotent operations (update if exists)
- **Git Clone Failure**: Authenticated clone URL, check disk space
- **Graceful Degradation**: Partial success if some review types fail

## Design Patterns in Use

### Dependency Injection
- FastAPI dependency injection for services
- Singleton pattern for settings via `@lru_cache()`

### Strategy Pattern
- CLI manager selection (Cline vs Qwen)
- Different strategies for different agents

### Template Method Pattern
- BaseCLIManager defines structure
- Subclasses implement specific details

### Factory Pattern
- ReviewService creates appropriate CLI manager
- MRCreator creates appropriate MR type

### Repository Pattern
- GitRepositoryManager abstracts Git operations
- GitLabService abstracts GitLab API

