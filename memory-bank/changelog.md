# Memory Bank Changelog

Changes to the Memory Bank documentation.

## 2025-11-04 - Initial Setup + Major Updates

### Added
- **Memory Bank Structure**: Created 6 core files
  - `projectbrief.md` - Foundation document
  - `productContext.md` - Product vision
  - `systemPatterns.md` - Architecture patterns
  - `techContext.md` - Technical details
  - `activeContext.md` - Current work
  - `progress.md` - Project status

- **Active Review Tracking**: Prevents concurrent reviews of same MR
  - Added `_active_reviews` set in GitRepositoryManager
  - Lock mechanism with `asyncio.Lock()`
  - Auto-cleanup on review completion

- **System Prompt Implementation**: Static code style rules
  - File: `prompts/system_prompt.md`
  - Loaded once at startup (singleton pattern)
  - Cached at class level for performance
  - Automatically prepended to all prompts

- **Lombok Guidelines**: Comprehensive Lombok usage rules
  - Mandatory annotations (@Data, @Builder, @Slf4j, @RequiredArgsConstructor)
  - When to use and when NOT to use Lombok
  - Code review severity flags

- **Documentation**:
  - `docs/SYSTEM_PROMPT_GUIDE.md` - Complete guide
  - Updated all Memory Bank files

### Changed
- **Removed `changed_files` parameter**: CLI now uses git diff automatically
  - Updated `base_cli_manager.py`
  - Updated `cline_cli_manager.py`
  - Updated `qwen_code_cli_manager.py`
  - Updated `review_service.py`
  - Updated all 14 prompts

- **Git Diff Instructions**: All prompts now include explicit git diff instructions
  - Added "Instructions" section to all prompts
  - Command: `git diff --name-only origin/develop`

### Technical Details
- System prompt overhead: ~0.001ms per request
- Memory usage: Minimal (single string cached)
- Restart required: Yes (to reload system prompt changes)

## 2025-11-04 - New Review Types + Memory Bank Integration

### Added
- **UNIT_TEST_COVERAGE Review Type**: Automated test coverage analysis
  - Detects changed files and corresponding test files
  - Generates missing unit tests following project conventions
  - Uses JUnit5, Mockito, TestContainers
  - Extends project's `*Base` classes (JupiterBase, JupiterArtemisBase, etc.)
  - Prompts: `prompts/cline/unit_test_coverage.md`, `prompts/qwen/unit_test_coverage.md`

- **MEMORY_BANK Review Type**: Project Memory Bank management
  - Validates existing Memory Bank structure (6 core files)
  - Initializes new Memory Bank by analyzing project
  - Based on Cursor's Memory Bank v1.2 Final methodology
  - Prompts: `prompts/cline/memory_bank.md`, `prompts/qwen/memory_bank.md`

- **Memory Bank Integration in System Prompt**:
  - Agents now check for `memory-bank/` directory before review
  - Auto-loads context from: projectbrief.md, systemPatterns.md, techContext.md, activeContext.md
  - Aligns recommendations with documented architectural decisions
  - References Memory Bank in suggestions

- **Documentation**: `docs/NEW_REVIEW_TYPES.md`
  - Comprehensive guide for both new review types
  - Usage examples and configuration
  - Output format specifications

### Changed
- **MR Creation Target Branch**: Fix/refactor MRs now target `source_branch`
  - Previous: `fix branch -> target_branch`
  - New: `fix branch -> source_branch -> target_branch`
  - Allows developers to review fixes in their feature branch first
  - Updated `app/services/mr_creator.py` with clarified comments

- **System Prompt Enhanced**:
  - Added "Project Context: Memory Bank" section
  - Instructions for checking and using Memory Bank
  - Fallback behavior if Memory Bank doesn't exist

- **Memory Bank Files Updated**:
  - `activeContext.md`: Documented all recent changes and decisions
  - `progress.md`: Updated completion status (95% core functionality)
  - `changelog.md`: This file

### Fixed
- **Concurrent Review Prevention**:
  - `GitRepositoryManager` tracks active reviews via `_active_reviews` set
  - Returns error if MR review already in progress
  - Proper cleanup removes tracking on repository cleanup
  - Prevents repository clone conflicts

### Technical Details
- Total Review Types: 13 (was 11)
- Total Prompts: 18 (was 14)
- Core Functionality Completion: 95% (was 90%)
- New files: 5 (4 prompts + 1 documentation)

## 2025-11-04 - Memory Bank Auto-Update Feature

### Enhanced
- **MEMORY_BANK Review Type**: Added auto-update mode (PRIMARY)
  - Now operates in 3 modes: Update (primary), Validate (rare), Initialize (once)
  - **Update Mode**: Analyzes MR changes and updates Memory Bank automatically
    - Always updates: `activeContext.md`, `changelog.md`
    - Conditionally updates: `systemPatterns.md`, `techContext.md`, `progress.md`
    - Commits changes to MR branch with `[skip ci]` tag
  - Keeps Memory Bank current with every MR
  
- **Updated Prompts**:
  - `prompts/cline/memory_bank.md`: Added Step 2 (Update Mode)
  - `prompts/qwen/memory_bank.md`: Added Step 2 (Update Mode)
  - Detailed instructions for which files to update when
  - Git commit and push commands included

- **Updated Documentation**:
  - `docs/NEW_REVIEW_TYPES.md`: Documented all 3 operating modes
  - Added auto-update workflow diagram
  - Added commit details and integration explanation

### Changed
- Memory Bank is now a **living document** that updates with each MR
- Recommended to run MEMORY_BANK on every MR (not just initialization)
- Agent now proactively maintains project context

