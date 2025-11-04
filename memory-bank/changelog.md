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

