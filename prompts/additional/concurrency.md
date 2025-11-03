# Concurrency Analysis Prompt

## Objective

Identify concurrency issues and verify correct concurrent programming patterns in Java Spring Boot code.

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Changed Files**: {changed_files}
- **Custom Rules**: {custom_rules}

## Analysis Scope

### 1. Race Conditions
**Check for**:
- Shared mutable state without synchronization
- Check-then-act without atomicity
- Compound operations on shared variables

### 2. Virtual Threads (Java 21+)
**Check for**:
- Opportunities to use virtual threads
- Blocking operations that could benefit from virtual threads

### 3. @Async Usage
**Check for**:
- Missing @EnableAsync
- @Async on private methods (won't work)
- Improper error handling in async methods
- Missing thread pool configuration

### 4. Thread Safety
**Check for**:
- Use of non-thread-safe collections in concurrent context
- Missing volatile on shared flags
- Incorrect double-checked locking

## Output Format

```json
{
  "review_type": "CONCURRENCY",
  "issues": [
    {
      "file": "path/to/file.java",
      "line": 67,
      "severity": "CRITICAL|HIGH|MEDIUM",
      "category": "Concurrency Issue",
      "message": "Description",
      "suggestion": "Safe concurrent pattern"
    }
  ]
}
```



