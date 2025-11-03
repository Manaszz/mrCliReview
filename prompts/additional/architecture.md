# Architecture Review Prompt

## Objective

Verify architectural patterns and microservices best practices in Java Spring Boot code.

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Changed Files**: {changed_files}
- **Custom Rules**: {custom_rules}

## Analysis Scope

### 1. Circuit Breaker Implementation
**Check for**:
- Missing circuit breakers on external service calls
- Improper fallback methods
- Resilience4j configuration issues

### 2. API Design
**Check for**:
- Missing API versioning
- Inconsistent REST conventions
- Missing pagination on list endpoints
- CORS configuration issues

### 3. Microservices Patterns
**Check for**:
- Cross-service database access (violates Database per Service)
- Missing service boundaries
- Tight coupling between services

### 4. DTO Usage
**Check for**:
- Exposing entities directly in controllers
- Missing DTO to entity mapping

## Output Format

```json
{
  "review_type": "ARCHITECTURE",
  "issues": [
    {
      "file": "path/to/file.java",
      "line": 45,
      "severity": "HIGH|MEDIUM",
      "category": "Architecture Pattern",
      "message": "Issue description",
      "suggestion": "Architectural improvement"
    }
  ]
}
```



