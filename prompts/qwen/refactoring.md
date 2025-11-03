# Refactoring Suggestions Prompt for Qwen Code CLI

## Objective

Suggest refactoring opportunities to improve code maintainability and readability.

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Changed Files**: {changed_files}
- **Custom Rules**: {custom_rules}

## Focus Areas

### 1. Code Smells
- Long methods (>50 lines) - suggest extract method
- Deep nesting (>3 levels) - suggest guard clauses
- Duplicate code - suggest extract to common method
- Complex boolean expressions - suggest extract to named methods
- Magic numbers - suggest extract to constants

### 2. Design Issues
- God objects / classes doing too much - suggest split by responsibility
- Anemic domain models - suggest move logic to domain objects
- Long parameter lists (>3 params) - suggest parameter object

### 3. Business Logic in Wrong Layer
- Controllers containing business logic - should move to services
- Direct repository access from controllers - should use services

## Output Format

```json
{
  "review_type": "REFACTORING",
  "suggestions": [
    {
      "file": "path/to/file.java",
      "line": 45,
      "severity": "HIGH|MEDIUM|LOW",
      "category": "Category Name",
      "message": "Refactoring suggestion",
      "code_snippet": "current code",
      "suggestion": "how to refactor",
      "impact": "SIGNIFICANT|MINOR",
      "effort": "HIGH|MEDIUM|LOW",
      "auto_fixable": false
    }
  ],
  "summary": {
    "total_suggestions": 0,
    "significant_refactorings": 0,
    "files_analyzed": 0
  },
  "classification": "SIGNIFICANT|MINOR"
}
```

## Refactoring Classification

**SIGNIFICANT** (separate MR):
- >3 classes affected
- Breaking changes
- >200 LOC changed
- DI structure modifications

**MINOR** (combine with fixes):
- Renames
- Extract constants
- Formatting
- Local method refactoring

## Instructions

1. Focus on improved maintainability
2. Classify each as SIGNIFICANT or MINOR
3. Estimate effort
4. Output JSON format



