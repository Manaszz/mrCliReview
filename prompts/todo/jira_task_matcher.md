# JIRA Task Matcher Prompt (TODO)

## Objective

Verify that code changes fully implement the requirements from the associated JIRA task.

## Context

- **Repository Path**: {repo_path}
- **JIRA Task ID**: {jira_task_id}
- **JIRA Description**: {jira_context}
- **Changed Files**: {changed_files}
- **Custom Rules**: {custom_rules}

## Analysis Approach

### 1. Extract Requirements
- Parse JIRA description for acceptance criteria
- Identify functional requirements
- Identify non-functional requirements
- Extract expected behaviors

### 2. Match to Code Changes
- Verify each requirement has corresponding code change
- Check for missing implementations
- Distinguish task work from refactoring

### 3. Assess Completeness
- Calculate completion percentage
- List unimplemented requirements
- Suggest missing implementations

## Completion Criteria

### Fully Complete (100%)
- All acceptance criteria met
- All functional requirements implemented
- Tests present for new functionality

### Partially Complete (50-99%)
- Some requirements implemented
- Core functionality present but missing features

### Not Matching (<50%)
- Changes don't align with task description
- Different functionality implemented
- Major requirements missing

## Considerations

- Refactoring changes may not directly relate to task
- Bug fixes as part of implementation are acceptable
- Technical debt improvements alongside features are good

## Output Format

```json
{
  "review_type": "JIRA_TASK_MATCHER",
  "analysis": {
    "completion_percentage": 85,
    "requirements_found": 10,
    "requirements_implemented": 8,
    "requirements_missing": 2,
    "unimplemented": [
      {
        "requirement": "Email notification on order completion",
        "priority": "HIGH",
        "suggestion": "Add EmailService call in OrderService.completeOrder()"
      },
      {
        "requirement": "Admin dashboard widget",
        "priority": "MEDIUM",
        "suggestion": "Create DashboardWidget component for orders"
      }
    ],
    "refactoring_detected": [
      "Extracted PaymentService from OrderService",
      "Renamed methods for clarity"
    ],
    "assessment": "MOSTLY_COMPLETE",
    "recommendation": "Create follow-up MR for missing email notification feature"
  }
}
```

## Integration Note

This is a TODO feature. Implementation requires:
1. JIRA API integration (via n8n workflow)
2. Natural language processing for requirement extraction
3. Code-to-requirement mapping algorithm
4. Integration with MR creation service for follow-up tasks



