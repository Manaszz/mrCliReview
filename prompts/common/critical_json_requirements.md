# CRITICAL: JSON Output Requirements

## ⚠️ MANDATORY OUTPUT FORMAT ⚠️

This section is **CRITICAL** for proper system operation. Follow these rules **EXACTLY**.

---

## Rule 1: Output ONLY Valid JSON

✅ **CORRECT**:
```json
{
  "review_type": "ERROR_DETECTION",
  "issues": [],
  "summary": {"total_issues": 0}
}
```

❌ **WRONG** - Has explanatory text:
```
Here are the results of my analysis:
{
  "review_type": "ERROR_DETECTION",
  "issues": []
}
Analysis complete!
```

❌ **WRONG** - Has markdown code blocks:
```markdown
```json
{
  "review_type": "ERROR_DETECTION",
  "issues": []
}
```
```

❌ **WRONG** - Has comments in JSON:
```json
{
  "review_type": "ERROR_DETECTION",  // This is the review type
  "issues": []  // No issues found
}
```

---

## Rule 2: Include ALL Required Fields

**MANDATORY fields that MUST always be present**:

```json
{
  "review_type": "string (REQUIRED)",
  "issues": "array (REQUIRED - can be empty [])",
  "summary": {
    "total_issues": "integer (REQUIRED)",
    "critical": "integer (REQUIRED)",
    "high": "integer (REQUIRED)",
    "medium": "integer (REQUIRED)",
    "low": "integer (REQUIRED)"
  }
}
```

**Even if no issues found**, return complete structure:
```json
{
  "review_type": "ERROR_DETECTION",
  "issues": [],
  "summary": {
    "total_issues": 0,
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  }
}
```

---

## Rule 3: Use Exact Field Names and Types

### Issue Object Structure

Each issue **MUST** have these fields:

```json
{
  "file": "string (REQUIRED) - relative path from repo root",
  "line": "integer (OPTIONAL) - positive integer only",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO (REQUIRED)",
  "category": "string (REQUIRED)",
  "message": "string (REQUIRED)",
  "code_snippet": "string (OPTIONAL)",
  "suggestion": "string (REQUIRED)",
  "auto_fixable": "boolean (REQUIRED - true or false, not string)"
}
```

✅ **CORRECT**:
```json
{
  "file": "src/main/java/UserService.java",
  "line": 42,
  "severity": "HIGH",
  "category": "Null Safety",
  "message": "Potential NullPointerException",
  "suggestion": "Add null check",
  "auto_fixable": true
}
```

❌ **WRONG** - Missing required fields:
```json
{
  "file": "UserService.java",
  "message": "Potential NPE"
  // Missing: severity, category, suggestion, auto_fixable
}
```

❌ **WRONG** - Wrong types:
```json
{
  "line": "42",  // Should be integer: 42
  "auto_fixable": "true"  // Should be boolean: true
}
```

---

## Rule 4: Valid Severity Values

**ONLY** use these exact severity values:
- `CRITICAL`
- `HIGH`
- `MEDIUM`
- `LOW`
- `INFO`

❌ **WRONG**:
- ~~`VERY_HIGH`~~
- ~~`Critical`~~ (lowercase)
- ~~`critical`~~
- ~~`SEVERE`~~

---

## Rule 5: Error Handling

If analysis **completely fails**, return this structure:

```json
{
  "review_type": "ERROR_DETECTION",
  "issues": [],
  "summary": {
    "total_issues": 0,
    "critical": 0,
    "high": 0,
    "medium": 0,
    "low": 0
  },
  "error": "Detailed description of what went wrong",
  "error_type": "GIT_ERROR"
}
```

Valid `error_type` values:
- `GIT_ERROR` - Git operations failed
- `PARSE_ERROR` - Cannot parse source files
- `TIMEOUT` - Analysis timed out
- `FILE_NOT_FOUND` - Required file not found
- `UNKNOWN` - Unknown error

---

## Rule 6: No Trailing Commas

❌ **WRONG**:
```json
{
  "issues": [],
  "summary": {"total_issues": 0},  // <- Remove this comma
}
```

✅ **CORRECT**:
```json
{
  "issues": [],
  "summary": {"total_issues": 0}
}
```

---

## Rule 7: File Paths Must Be Relative

✅ **CORRECT**:
```json
{
  "file": "src/main/java/com/example/UserService.java"
}
```

❌ **WRONG** - Absolute path:
```json
{
  "file": "/home/user/repo/src/main/java/UserService.java"
}
```

---

## Pre-Output Validation Checklist

Before outputting JSON, **verify**:

- [ ] JSON syntax is valid (all brackets/braces closed)
- [ ] NO text before JSON
- [ ] NO text after JSON
- [ ] NO markdown code blocks around JSON
- [ ] NO comments in JSON
- [ ] All required fields present (`review_type`, `issues`, `summary`)
- [ ] Summary has all required fields (`total_issues`, `critical`, `high`, `medium`, `low`)
- [ ] Each issue has all required fields
- [ ] Severity values are from allowed list
- [ ] `auto_fixable` is boolean (true/false), not string
- [ ] Line numbers are positive integers (if present)
- [ ] File paths are relative to repository root
- [ ] No trailing commas
- [ ] Strings are properly quoted
- [ ] `total_issues` matches actual count in `issues` array

---

## Testing Your Output

**Test JSON validity** before submitting:

```bash
# Method 1: Python
echo 'YOUR_JSON' | python -m json.tool

# Method 2: Node.js
echo 'YOUR_JSON' | node -e "JSON.parse(require('fs').readFileSync(0))"
```

If command succeeds → ✅ Valid JSON  
If command fails → ❌ Fix syntax errors

---

## Common Mistakes - Avoid These!

### Mistake #1: Extra text
```
I found 5 issues:
{"issues": [...]}
```

### Mistake #2: Markdown formatting
```markdown
```json
{"issues": []}
```
```

### Mistake #3: Invalid severity
```json
{"severity": "VERY_HIGH"}
```

### Mistake #4: Missing required field
```json
{
  "review_type": "ERROR_DETECTION",
  "issues": []
  // Missing "summary" - REQUIRED!
}
```

### Mistake #5: Wrong boolean type
```json
{
  "auto_fixable": "true"  // Should be: true (no quotes)
}
```

---

## Summary: The 3 Golden Rules

1. 📝 **Output ONLY valid JSON, nothing else**
2. ✅ **Include ALL required fields**
3. 🔍 **Validate before outputting**

Following these rules ensures your analysis results can be reliably parsed and processed by the review system.

**Failure to follow these rules will result in analysis being rejected.**

---

## JSON Schema Reference

Full JSON Schema is available at: `schemas/review_result_schema.json`

Your output will be validated against this schema.

