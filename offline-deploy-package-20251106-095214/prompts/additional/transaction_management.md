# Transaction Management Review Prompt

## Objective

Verify correct @Transactional usage and transaction configuration in Java Spring Boot code.

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Custom Rules**: {custom_rules}



## Instructions

**IMPORTANT**: Use `git diff` to automatically determine which files have changed.
Analyze only the changed files between the current branch and the target branch.

Command to detect changes: `git diff --name-only origin/main` (or use appropriate target branch)

## Analysis Scope

### 1. @Transactional Placement
**Check for**:
- @Transactional on repository methods (should be on service)
- @Transactional on private methods (won't work)
- Missing @Transactional on methods that modify data

### 2. Propagation Levels
**Check for**:
- Incorrect propagation for nested transactions
- Using REQUIRES_NEW when not necessary
- Missing REQUIRES_NEW for independent operations

### 3. Isolation Levels
**Check for**:
- Default isolation when stricter needed
- Too strict isolation causing performance issues
- Missing read-only transactions

### 4. Transaction Boundaries
**Check for**:
- Transactions too large (performance)
- Transactions too small (data consistency)

## Output Format

```json
{
  "review_type": "TRANSACTION_MANAGEMENT",
  "issues": [
    {
      "file": "path/to/file.java",
      "line": 23,
      "severity": "HIGH|MEDIUM",
      "category": "Transaction Issue Type",
      "message": "Description",
      "suggestion": "Correct configuration"
    }
  ]
}
```



