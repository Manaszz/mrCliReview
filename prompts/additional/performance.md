# Performance Analysis Prompt

## Objective

Identify performance issues and optimization opportunities in Java Spring Boot code.

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Changed Files**: {changed_files}
- **Custom Rules**: {custom_rules}

## Analysis Scope

### 1. N+1 Query Detection
**Check for**:
- Lazy loading in loops
- Missing @EntityGraph or JOIN FETCH
- Fetching collections in iterations

**Example**:
```java
// BAD: N+1 queries
List<Order> orders = orderRepository.findAll(); // 1 query
orders.forEach(order -> {
    List<Item> items = order.getItems(); // N queries (lazy loading)
});

// GOOD: JOIN FETCH
@Query("SELECT o FROM Order o LEFT JOIN FETCH o.items")
List<Order> findAllWithItems();
```

### 2. Caching Issues
**Check for**:
- Missing caching for expensive operations
- Cache configuration problems
- Incorrect cache keys

### 3. Stream API Performance
**Check for**:
- Inefficient stream operations
- Wrong order of operations (filter after map instead of before)
- Unnecessary parallel streams on small data

### 4. Connection Pool Configuration
**Check for**:
- Inadequate pool size
- Missing timeout configuration

## Output Format

```json
{
  "review_type": "PERFORMANCE",
  "issues": [
    {
      "file": "path/to/file.java",
      "line": 45,
      "severity": "CRITICAL|HIGH|MEDIUM",
      "category": "Performance Issue Type",
      "message": "Description",
      "impact": "Performance impact description",
      "suggestion": "Optimization suggestion"
    }
  ]
}
```



