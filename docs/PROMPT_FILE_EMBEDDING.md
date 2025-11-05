# Prompt File Embedding Feature

## Overview

Automated embedding of referenced files into prompts ensures CLI agents receive complete, self-contained instructions without relying on filesystem access.

**Date**: November 5, 2025  
**Version**: 2.0

---

## Problem

CLI agents run inside cloned repositories and cannot access files from the Review Service:
- ❌ `prompts/common/critical_json_requirements.md` doesn't exist in developer's repo
- ❌ `schemas/review_result_schema.json` doesn't exist in developer's repo
- ❌ References like "See `prompts/common/file.md`" don't work

---

## Solution

**Automatic File Embedding**: When loading prompts, the ReviewService automatically:
1. Finds all file references in prompts (pattern: `` `prompts/...` `` or `` `schemas/...` ``)
2. Loads referenced files from Review Service filesystem
3. Removes reference lines from the original prompt
4. Appends embedded file contents at the end of the prompt

---

## How It Works

### 1. File Reference Detection

The system detects references in prompts:
```markdown
1. **JSON Output Requirements**: See `prompts/common/critical_json_requirements.md`
2. **Git Diff Analysis**: See `prompts/common/git_diff_instructions.md`

**Validation**: Your output will be validated against `schemas/review_result_schema.json`
```

### 2. Embedding Process

```python
# In ReviewService._load_prompts()
prompt_content = self._embed_referenced_files(prompt_content)
```

**Steps**:
1. Parse prompt for references matching pattern: `` `(prompts|schemas)/[^`]+\.(md|json)` ``
2. Remove ALL reference lines from prompt (even if file doesn't exist)
3. Load each referenced file:
   - For `.md` files: Embed as-is (also remove nested references)
   - For `.json` files: Format with proper indentation
4. Append embedded section at the end:

```markdown
---

## 📎 Embedded Reference Files

*The following files are embedded for your reference (originally referenced in this prompt):*

### 📄 prompts/common/critical_json_requirements.md (Markdown Document)

[Full file content here]

### 📄 schemas/review_result_schema.json (JSON Schema)

```json
{
  "$schema": "...",
  ...
}
```
```

### 3. De-duplication

- Each file is embedded **only once** per prompt
- Multiple references to the same file result in single embedding
- Nested references are removed (e.g., if `critical_json_requirements.md` references `schema.json`)

---

## Referenced Files

### Currently Embedded Files

All 12 prompts (7 Cline + 5 Qwen) now embed:

#### 1. `prompts/common/critical_json_requirements.md`
- **Purpose**: Complete JSON output requirements
- **Size**: 315 lines
- **Content**: 
  - 7 validation rules
  - DO/DON'T examples
  - Common mistakes
  - Testing instructions
  - Pre-output checklist

#### 2. `prompts/common/git_diff_instructions.md`
- **Purpose**: Strategy for analyzing changed files
- **Size**: 145 lines
- **Content**:
  - How to use `git diff`
  - Primary vs supporting analysis
  - What to report vs what to skip
  - Metadata requirements

#### 3. `schemas/review_result_schema.json`
- **Purpose**: JSON Schema for validation
- **Size**: 261 lines
- **Content**:
  - Complete schema definition
  - All required fields
  - Valid severity/enum values
  - Structure for all review types

---

## Benefits

### ✅ Self-Contained Prompts

CLI agents receive everything they need in a single prompt:
- No filesystem dependencies
- No missing file errors
- Works in any environment

### ✅ Consistent Information

All agents see the same instructions:
- No version mismatches
- Single source of truth
- Automatic updates when reference files change

### ✅ Improved Maintainability

Centralized instruction files:
- Update once in `prompts/common/`
- Changes automatically propagate to all prompts
- Easier to keep docs in sync

### ✅ Automatic De-duplication

Smart handling of multiple references:
- No bloated prompts
- Nested references handled
- Optimal prompt size

---

## Implementation Details

### Code Location

- **File**: `app/services/review_service.py`
- **Method**: `_embed_referenced_files(prompt_content: str) -> str`
- **Called From**: `_load_prompts()` method

### Reference Pattern

```python
pattern = r'`((?:prompts|schemas)/[^`]+\.(md|json))`'
```

Matches:
- `` `prompts/common/critical_json_requirements.md` ``
- `` `prompts/common/git_diff_instructions.md` ``
- `` `schemas/review_result_schema.json` ``

### Cleaning Process

1. **Remove references**: All lines containing `` `file.md` `` are removed
2. **Clean blanks**: Multiple consecutive newlines reduced to single blank line
3. **Embed content**: Referenced files appended with clear section headers

---

## Testing

### Test Suite

**File**: `tests/test_prompt_embedding.py`  
**Tests**: 9 comprehensive tests

Coverage includes:
- ✅ No references handling
- ✅ Single file embedding
- ✅ Multiple references to same file (de-duplication)
- ✅ Multiple different files
- ✅ Nonexistent file handling (graceful degradation)
- ✅ Structure preservation
- ✅ Integration with prompt loading
- ✅ Blank line cleanup
- ✅ JSON schema embedding

### Running Tests

```bash
python -m pytest tests/test_prompt_embedding.py -v
```

All tests passing ✅

---

## Troubleshooting

### Problem: Referenced file not found

**Symptom**: Warning in logs: `Referenced file not found: prompts/common/file.md`

**Solution**: 
- Reference is automatically removed from prompt
- No embedding occurs
- CLI receives cleaned prompt without broken references

### Problem: Nested references

**Example**: `critical_json_requirements.md` references `schema.json`

**Solution**: Automatically handled - nested references are removed from embedded content

### Problem: Prompt too long

**Symptom**: Model context limit exceeded

**Solution**: 
- Review which files are being embedded
- Consider splitting large reference files
- Check if all embeddings are necessary

---

## Migration Notes

### Before This Feature

Prompts contained unusable references:
```markdown
See `prompts/common/critical_json_requirements.md` for complete rules.
```

CLI couldn't access the file → Reference ignored

### After This Feature

Prompts contain embedded content:
```markdown
---

## 📎 Embedded Reference Files

### 📄 prompts/common/critical_json_requirements.md

[Complete file content is here, CLI can read it]
```

CLI has everything → No missing information

---

## Future Enhancements

### Potential Improvements

1. **Caching**: Cache embedded prompts to avoid re-processing on each request
2. **Selective Embedding**: Allow prompts to specify which sections to embed
3. **Compression**: Compress embedded content for models with small context windows
4. **Versioning**: Track embedded file versions for debugging

### Not Needed Currently

- ✅ Current solution works reliably
- ✅ Performance is acceptable (embedding happens once per review)
- ✅ No complaints about prompt size

---

## References

- Original issue discussion: `docs/CLI_PROMPT_ANALYSIS.md`
- Implementation: `app/services/review_service.py` (lines 212-303)
- Tests: `tests/test_prompt_embedding.py`
- JSON Schema: `schemas/review_result_schema.json`

---

## Changelog

### 2025-11-05 - v2.0 (Initial Implementation)

**Added**:
- ✅ Automatic file embedding in `ReviewService._embed_referenced_files()`
- ✅ JSON Schema embedding for all prompts
- ✅ Reference removal and cleanup
- ✅ Nested reference handling
- ✅ Comprehensive test suite (9 tests)

**Removed**:
- ❌ `prompts/common/json_output_requirements.md` (duplicate, unused)

**Updated**:
- ✅ All 12 prompts now include JSON Schema reference
- ✅ All prompts now embed 3 files: critical_json, git_diff, schema

