# Best Practices Prompt for Qwen Code CLI

## Objective

Analyze Java Spring Boot code for adherence to SOLID principles, Spring conventions, and modern Java features.

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Changed Files**: {changed_files}
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



