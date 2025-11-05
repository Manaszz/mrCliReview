# Error Detection Prompt for Qwen Code CLI

## Objective

Analyze Java Spring Boot code changes to identify bugs, potential crashes, and logical errors.

---

## ⚠️ CRITICAL: Read These Instructions First ⚠️

**MANDATORY**: Before proceeding with analysis, read these critical instruction files:

1. **JSON Output Requirements**: See `prompts/common/critical_json_requirements.md`
   - Explains EXACT JSON format required
   - Common mistakes to avoid
   - Validation checklist

2. **Git Diff Analysis**: See `prompts/common/git_diff_instructions.md`
   - How to identify changed files
   - What to analyze vs what to use for context
   - Proper reporting strategy

**Failure to follow these instructions will result in analysis being rejected.**

---

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Custom Rules**: {custom_rules}

## Focus Areas

### 1. NullPointerException Risks
- Dereferencing potentially null values
- Missing null checks at boundaries
- Unsafe Optional usage (calling .get() without check)

### 2. Exception Handling
- Empty catch blocks
- Generic Exception catches without logging
- Missing resource cleanup (no try-with-resources)

### 3. Type Safety
- Unchecked casts
- Raw types usage
- ClassCastException risks

### 4. Logical Errors
- String comparison with == instead of .equals()
- Incorrect loop conditions
- Boolean logic errors

## Output Format

### ⚠️ CRITICAL: JSON Output Requirements ⚠️

**READ**: `prompts/common/critical_json_requirements.md` for complete rules.

**Key Points**:
1. Output ONLY valid JSON, no other text
2. NO markdown code blocks (no ```json)
3. Include ALL required fields
4. Use exact field names and types
5. Validate before outputting

**Validation**: Your output will be validated against `schemas/review_result_schema.json`

### Required JSON Structure

```json
{
  "review_type": "ERROR_DETECTION",
  "issues": [
    {
      "file": "path/to/file.java",
      "line": 45,
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "category": "Category Name",
      "message": "Issue description",
      "code_snippet": "problematic code",
      "suggestion": "how to fix",
      "auto_fixable": true|false
    }
  ],
  "summary": {
    "total_issues": 0,
    "critical": 0,
    "files_analyzed": 0
  }
}
```

## Instructions

1. Analyze changed files only
2. Focus on runtime errors and crashes
3. Provide specific line numbers and fixes
4. Mark auto-fixable issues
5. Output JSON format



