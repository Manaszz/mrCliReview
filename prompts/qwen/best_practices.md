# Best Practices Prompt for Qwen Code CLI

## Objective

Analyze Java Spring Boot code for adherence to SOLID principles, Spring conventions, and modern Java features.

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

### 1. SOLID Principles
- Single Responsibility: Classes doing multiple things
- Dependency Inversion: Depending on concrete implementations

### 2. Spring Boot Conventions
- Field injection vs constructor injection
- @Transactional placement (service, not repository)
- Proper use of @Service, @Repository, @Controller

### 3. Code Quality
- Long methods (>50 lines)
- Deep nesting (>3 levels)
- Magic numbers (should be constants)
- Code duplication (DRY violations)

### 4. Modern Java Features
- POJOs that could be Records (Java 16+)
- instanceof with cast that could use pattern matching (Java 17+)
- Raw types that should use generics

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
  "review_type": "BEST_PRACTICES",
  "issues": [
    {
      "file": "path/to/file.java",
      "line": 23,
      "severity": "HIGH|MEDIUM|LOW",
      "category": "Category Name",
      "message": "Issue description",
      "code_snippet": "code sample",
      "suggestion": "improvement suggestion",
      "auto_fixable": true|false
    }
  ],
  "summary": {
    "total_issues": 0,
    "solid_violations": 0,
    "files_analyzed": 0
  }
}
```

## Instructions

1. Focus on architectural improvements
2. Suggest modern Java features where applicable
3. Check Spring Boot annotations usage
4. Output JSON format



