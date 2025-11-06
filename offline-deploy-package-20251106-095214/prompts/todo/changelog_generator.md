# Changelog Generator Prompt (TODO)

## Objective

Automatically generate CHANGELOG.md entries from git commits and code changes following Keep a Changelog format.

## Context

- **Repository Path**: {repo_path}
- **Git Log**: {git_log}
- **Diff Summary**: {diff_summary}
- **JIRA Context**: {jira_context}
- **Version**: {version}

## Analysis Approach

### 1. Analyze Changes
- Parse commit messages
- Analyze code diff
- Identify type of changes
- Extract JIRA ticket references

### 2. Categorize Changes
According to Keep a Changelog:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security fixes

### 3. Generate Entries
- Group related changes
- Create human-readable descriptions
- Link to JIRA tickets
- Follow semantic versioning

## Output Format

```json
{
  "review_type": "CHANGELOG_GENERATOR",
  "changelog_entry": {
    "version": "2.1.0",
    "date": "2025-11-03",
    "sections": {
      "Added": [
        "User profile picture upload functionality (#PROJ-123)",
        "Email notification preferences in settings (#PROJ-125)"
      ],
      "Changed": [
        "Improved order processing performance by 40% (#PROJ-120)",
        "Updated user dashboard UI for better mobile experience"
      ],
      "Fixed": [
        "Fixed NullPointerException in PaymentService (#PROJ-127)",
        "Resolved race condition in order status updates (#PROJ-129)"
      ],
      "Security": [
        "Updated Spring Security to 6.2.0 to address CVE-2024-XXXX",
        "Added rate limiting to authentication endpoints"
      ]
    },
    "markdown": "## [2.1.0] - 2025-11-03\n\n### Added\n- User profile picture upload functionality (#PROJ-123)\n...",
    "commit_message": "chore: Update CHANGELOG.md for version 2.1.0"
  }
}
```

## CHANGELOG.md Format Example

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2025-11-03

### Added
- User profile picture upload functionality (#PROJ-123)
- Email notification preferences in settings (#PROJ-125)
- REST API versioning support (v1, v2)

### Changed
- Improved order processing performance by 40% (#PROJ-120)
- Updated user dashboard UI for better mobile experience
- Migrated from Log4j to Logback for logging

### Fixed
- Fixed NullPointerException in PaymentService when processing refunds (#PROJ-127)
- Resolved race condition in order status updates (#PROJ-129)
- Corrected pagination bug in user search (#PROJ-130)

### Security
- Updated Spring Security to 6.2.0 to address CVE-2024-XXXX
- Added rate limiting to authentication endpoints (10 requests/minute)
- Implemented CSRF protection on all state-changing endpoints

## [2.0.0] - 2025-10-15

...
```

## Commit Strategy

- Update CHANGELOG.md in MR branch
- Commit with message: "chore: Update CHANGELOG.md for version X.Y.Z"
- Include change summary in commit description

## Integration Note

This is a TODO feature. Implementation requires:
1. Git log parsing
2. Commit message analysis
3. Semantic versioning logic
4. JIRA ticket reference extraction
5. Change categorization algorithm
6. Markdown file manipulation



