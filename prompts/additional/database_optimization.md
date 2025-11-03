# Database Optimization Prompt

## Objective

Identify database performance issues and suggest optimizations for JPA/Hibernate code.

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Changed Files**: {changed_files}
- **Custom Rules**: {custom_rules}

## Analysis Scope

### 1. Query Optimization
**Check for**:
- SELECT * instead of specific columns
- Missing indexes on frequently queried columns
- Inefficient JOIN strategies
- Cartesian products in queries

### 2. Lazy/Eager Loading
**Check for**:
- Inappropriate eager loading (loading too much)
- Missing @EntityGraph for controlled fetching
- Lazy loading causing N+1 queries

### 3. Batch Operations
**Check for**:
- Individual saves in loops (should use batch)
- Missing pagination on large result sets

### 4. Query Projections
**Check for**:
- Loading full entities when only few fields needed
- Missing DTO projections

## Output Format

```json
{
  "review_type": "DATABASE_OPTIMIZATION",
  "issues": [
    {
      "file": "path/to/file.java",
      "line": 34,
      "severity": "HIGH|MEDIUM",
      "category": "Database Performance",
      "message": "Issue description",
      "impact": "Performance impact",
      "suggestion": "Optimization approach"
    }
  ]
}
```



