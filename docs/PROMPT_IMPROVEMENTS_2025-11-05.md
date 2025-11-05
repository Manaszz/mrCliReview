# Prompt Improvements - November 5, 2025

## Summary

Implemented critical improvements to CLI prompts to ensure stable, structured JSON output from code review agents.

---

## Changes Implemented

### 1. JSON Schema Validation ✅

**Created**: `schemas/review_result_schema.json`

- Formal JSON Schema (Draft 7) for all review results
- Defines required fields, types, and constraints
- Supports all review types: ERROR_DETECTION, BEST_PRACTICES, REFACTORING, SECURITY_AUDIT, DOCUMENTATION, UNIT_TEST_COVERAGE, MEMORY_BANK, etc.
- Includes validation for:
  - Issue structure (file, line, severity, category, message, suggestion, auto_fixable)
  - Refactoring suggestions with impact/effort
  - Documentation additions
  - Summary statistics
  - Error reporting

**Created**: `app/utils/json_validator.py`

- Python validator using `jsonschema` library
- Validates CLI output against schema
- Provides semantic validation (e.g., total_issues count matching)
- Integrated into `base_cli_manager._parse_cli_output()`
- Graceful degradation if jsonschema not available

**Updated**: `requirements.txt`

- Added `jsonschema==4.20.0` dependency

---

### 2. Critical JSON Output Requirements ✅

**Created**: `prompts/common/critical_json_requirements.md`

Comprehensive guide for CLI agents covering:

- **Rule 1**: Output ONLY valid JSON (no extra text)
- **Rule 2**: Include ALL required fields (even if empty)
- **Rule 3**: Use exact field names and types
- **Rule 4**: Valid severity values (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- **Rule 5**: Error handling format
- **Rule 6**: No trailing commas
- **Rule 7**: Relative file paths only

**Features**:
- ✅ Clear DO/DON'T examples
- ✅ Pre-output validation checklist
- ✅ Common mistakes section
- ✅ Testing instructions
- ✅ JSON Schema reference

---

### 3. Git Diff Analysis Instructions ✅

**Created**: `prompts/common/git_diff_instructions.md`

Clarifies analysis strategy:

**Key Principles**:
- 📚 **Full project visibility**: CLI can browse all files for context
- 🎯 **Primary focus**: Changed files from `git diff`
- ✅ **Report**: Issues in changed files + direct impacts
- ❌ **Avoid**: Pre-existing issues unrelated to MR

**Workflow**:
1. Execute `git diff --name-only` to identify changes
2. Read full project to understand context
3. Analyze changed files deeply
4. Check related unchanged files for impacts
5. Report relevant issues only

**Output Requirements**:
```json
{
  "changed_files": ["file1.java", "file2.java"],
  "files_analyzed_count": 2,
  ...
}
```

---

### 4. Updated All Prompts ✅

**Script**: `scripts/update_prompts_with_critical_instructions.py`

Automated update of 12 prompt files:

**Cline Prompts (7)**:
- best_practices.md
- documentation.md
- error_detection.md
- memory_bank.md
- refactoring.md
- security_audit.md
- unit_test_coverage.md

**Qwen Prompts (5)**:
- best_practices.md
- error_detection.md
- memory_bank.md
- refactoring.md
- unit_test_coverage.md

**Changes per prompt**:

1. **Added Critical Instructions Header** (after Context section):
```markdown
## ⚠️ CRITICAL: Read These Instructions First ⚠️

**MANDATORY**: Before proceeding with analysis, read these critical instruction files:

1. **JSON Output Requirements**: See `prompts/common/critical_json_requirements.md`
2. **Git Diff Analysis**: See `prompts/common/git_diff_instructions.md`

**Failure to follow these instructions will result in analysis being rejected.**
```

2. **Enhanced Instructions Section**:
```markdown
### Step 1: Identify Changed Files

Execute `git diff` to determine which files have changed:

```bash
git diff --name-only origin/<target-branch>
```

**You have full project access** - browse any file for context. 
**But analyze and report issues primarily for changed files.**
```

3. **Added Critical JSON Output Section** (in Output Format):
```markdown
### ⚠️ CRITICAL: JSON Output Requirements ⚠️

**READ**: `prompts/common/critical_json_requirements.md` for complete rules.

**Key Points**:
1. Output ONLY valid JSON, no other text
2. NO markdown code blocks (no ```json)
3. Include ALL required fields
4. Use exact field names and types
5. Validate before outputting

**Validation**: Your output will be validated against `schemas/review_result_schema.json`
```

---

## Files Created

```
schemas/
├── review_result_schema.json              # JSON Schema definition

prompts/common/
├── critical_json_requirements.md          # JSON output requirements
└── git_diff_instructions.md               # Git diff analysis strategy

app/utils/
└── json_validator.py                      # Python validator

scripts/
└── update_prompts_with_critical_instructions.py  # Automation script

docs/
└── PROMPT_IMPROVEMENTS_2025-11-05.md      # This document
```

---

## Benefits

### 1. Improved Reliability

**Before**: ~80% successful JSON parsing
**After**: Expected ~95% successful parsing

- Formal schema validation catches errors early
- Clear instructions reduce CLI agent mistakes
- Graceful error handling with detailed logging

### 2. Better Debugging

- Validation errors pinpoint exact issues
- Semantic validation catches logic errors (count mismatches)
- Structured error messages for quick fixes

### 3. Consistency

- All CLI agents follow same output format
- Standardized error reporting
- Consistent severity levels and field names

### 4. Context Awareness

- CLI agents understand full project context
- Focus on changed files reduces noise
- Relevant, actionable feedback

---

## Validation Examples

### Valid Output ✅

```json
{
  "review_type": "ERROR_DETECTION",
  "changed_files": ["src/UserService.java"],
  "files_analyzed_count": 1,
  "issues": [
    {
      "file": "src/UserService.java",
      "line": 42,
      "severity": "HIGH",
      "category": "Null Safety",
      "message": "Potential NullPointerException",
      "suggestion": "Add null check",
      "auto_fixable": true
    }
  ],
  "summary": {
    "total_issues": 1,
    "critical": 0,
    "high": 1,
    "medium": 0,
    "low": 0
  }
}
```

### Invalid Output - Caught by Validator ❌

```json
{
  "review_type": "ERROR_DETECTION",
  "issues": [
    {
      "file": "UserService.java",
      "severity": "VERY_HIGH",  // ❌ Invalid severity
      "message": "Some issue",
      // ❌ Missing: category, suggestion, auto_fixable
    }
  ]
  // ❌ Missing: summary
}
```

**Validation Errors**:
- Invalid severity: 'VERY_HIGH'
- Issue #1: Missing required field 'category'
- Issue #1: Missing required field 'suggestion'
- Issue #1: Missing required field 'auto_fixable'
- Missing required field: summary

---

## Testing

### Manual Testing

```bash
# Test schema validation
python -c "
from app.utils.json_validator import validate_review_result
import json

data = json.loads('''YOUR_JSON_HERE''')
is_valid, errors = validate_review_result(data)
print('Valid:', is_valid)
for error in errors:
    print('  -', error)
"
```

### Integration Testing

Validator is automatically invoked in `base_cli_manager._parse_cli_output()`:
- Logs warnings if validation fails
- Does NOT block processing (backward compatible)
- Helps identify prompt improvements needed

---

## Future Improvements

### Not Implemented Yet (Deferred)

1. **Timeout Handling**: Partial results strategy
2. **Large MR Handling**: Chunking and prioritization
3. **Streaming Results**: Progress indicators for large analyses

These can be added when needed based on real usage patterns.

---

## Migration Notes

### For Developers

1. **No code changes required** - validation is automatic
2. **Review logs** for validation warnings to improve prompts
3. **Use schema** as reference when debugging CLI issues

### For Operations

1. **Install jsonschema**: `pip install -r requirements.txt`
2. **Monitor logs** for validation failures
3. **Report patterns** if certain validation errors are common

---

## References

- JSON Schema Spec: https://json-schema.org/draft-07/schema
- Original Analysis: `docs/CLI_PROMPT_ANALYSIS.md`
- Implementation Discussion: See commit messages with `[PROMPT]` tag

---

## Conclusion

These improvements significantly enhance the reliability and maintainability of the code review system. CLI agents now have clear, unambiguous instructions, and the system can automatically validate their output for correctness.

The changes are backward compatible and provide graceful degradation if issues occur, while giving clear feedback for continuous improvement.

