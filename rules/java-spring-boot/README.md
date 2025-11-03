# Java Spring Boot Code Review Rules

## Overview

This directory contains comprehensive code review rules for Java Spring Boot applications. These rules are used by the AI-powered code review system to analyze merge requests and provide actionable feedback.

---

## Rule Files

### 1. error_detection.md
**Purpose**: Detect bugs, potential crashes, and logical errors

**Coverage**:
- NullPointerException prevention
- Exception handling anti-patterns
- Resource management issues
- Type safety violations
- String comparison errors
- Collection access safety
- Boolean logic errors
- Switch statement completeness

**Rules**: 10 rules (60% auto-fixable)

---

### 2. best_practices.md
**Purpose**: Enforce SOLID principles, Spring conventions, and modern Java features

**Coverage**:
- SOLID principles (SRP, DIP)
- Spring Boot conventions (@Transactional placement, constructor injection)
- DRY violations
- KISS principles (method complexity, nesting depth)
- Modern Java features (Records, Pattern Matching)

**Rules**: 12 rules (42% auto-fixable)

---

### 3. security.md
**Purpose**: Identify security vulnerabilities and enforce secure coding practices

**Coverage**:
- SQL Injection prevention
- XSS prevention
- CSRF protection
- Authentication & Authorization
- Hardcoded credentials
- Input validation
- Sensitive data logging
- Weak cryptography
- Path traversal
- Insecure dependencies

**Rules**: 10 rules (50% auto-fixable)

**Note**: All CRITICAL security rules must be fixed before merge.

---

### 4. refactoring_criteria.md
**Purpose**: Define criteria for classifying refactoring as SIGNIFICANT vs MINOR

**Classification Criteria**:
- **SIGNIFICANT** (separate MR): >3 classes, breaking changes, >200 LOC, DI modifications, pattern migrations
- **MINOR** (can combine): renames, constant extraction, formatting, simple refactoring

**Use**: Referenced by RefactoringClassifier service to determine MR creation strategy.

---

### 5. documentation_style.md
**Purpose**: Standards for JavaDoc, inline comments, and documentation generation

**Coverage**:
- JavaDoc structure and requirements
- Class, method, parameter documentation
- REST endpoint documentation
- Inline comment guidelines
- TODO comment format
- Package documentation (package-info.java)

---

### 6. performance.md
**Purpose**: Identify performance issues and optimization opportunities

**Coverage**:
- N+1 query detection (CRITICAL)
- Query projections and pagination
- Caching strategies
- Stream API optimization
- Connection pool configuration
- Reactive programming patterns
- Collection operation efficiency

**Rules**: 11 rules (27% auto-fixable)

---

## Rule Structure

Each rule follows this structure:

```markdown
### Rule N: Rule Name

#### Severity: CRITICAL | HIGH | MEDIUM | LOW

#### Description
Clear description of what the rule checks.

#### Patterns to Detect
Code examples showing anti-patterns (BAD).

#### Correct Pattern
Code examples showing correct patterns (GOOD).

#### Auto-fix Capability: Yes | Partial | No
```

---

## Severity Levels

### CRITICAL
- Will cause runtime failures or security breaches
- Must be fixed before merge
- Examples: SQL injection, NPE in critical paths, CSRF disabled

### HIGH
- Likely to cause issues under certain conditions
- Should be fixed before merge
- Examples: Improper exception handling, missing authorization

### MEDIUM
- Code smell or best practice violation
- Should be addressed soon
- Examples: Long methods, field injection, missing caching

### LOW
- Minor improvement opportunity
- Can be addressed in future refactoring
- Examples: Magic numbers, unnecessary complexity

---

## Customization

### Project-Specific Rules

Create `.project-rules/` directory in your repository root to override default rules:

```
your-project/
├── .project-rules/
│   ├── error_detection.md          # Overrides default error rules
│   ├── security.md                 # Additional security requirements
│   └── custom_patterns.md          # Project-specific patterns
├── src/
└── pom.xml
```

### Confluence Rules

Rules can also be loaded from Confluence pages (configured via n8n workflow):
- Team-wide standards
- Organization policies
- Shared best practices

### Rule Priority

1. **Project-specific rules** (`.project-rules/` in repo) - highest priority
2. **Confluence rules** (team/org standards) - medium priority
3. **Default rules** (this directory) - lowest priority

Project-specific rules completely override default rules for the same category.

---

## Auto-fix Capability

### Fully Auto-fixable
System can automatically generate correct code:
- Add null checks
- Convert to try-with-resources
- Replace == with .equals()
- Add generic type parameters
- Extract constants
- Fix parameterized queries

### Partially Auto-fixable
System can detect and suggest, but requires manual verification:
- Extract methods (method naming)
- Add missing JavaDoc (parameter descriptions)
- Fix DI structure (understanding dependencies)

### Manual Fix Required
Requires understanding of business logic:
- Architectural refactoring
- Authorization rules
- Complex algorithm optimization
- Breaking API changes

---

## Usage in Code Review

### Review Type Mapping

| Review Type | Primary Rules | Secondary Rules |
|-------------|---------------|----------------|
| ERROR_DETECTION | error_detection.md | - |
| BEST_PRACTICES | best_practices.md | documentation_style.md |
| REFACTORING | best_practices.md | refactoring_criteria.md |
| SECURITY_AUDIT | security.md | - |
| DOCUMENTATION | documentation_style.md | - |
| PERFORMANCE | performance.md | - |
| ALL | All rules | All rules |

### Example: How Rules are Applied

1. **MR Created**: Developer creates MR with Java Spring Boot changes
2. **Validation**: n8n workflow validates MR (JIRA ticket, description)
3. **Review Request**: System calls `/api/v1/review` with review types
4. **Rules Loading**:
   - Check for `.project-rules/` in repository
   - Load Confluence rules (if configured)
   - Fall back to default rules (this directory)
5. **CLI Execution**: Cline or Qwen CLI analyzes code with rules
6. **Results**: Issues categorized by severity and auto-fix capability
7. **MR Creation**:
   - Documentation: Committed to source branch
   - Fixes: New MR created with auto-fixable issues
   - Refactoring: Separate MR if SIGNIFICANT (per refactoring_criteria.md)

---

## Statistics

### Total Rules Across All Files
- **Error Detection**: 10 rules
- **Best Practices**: 12 rules
- **Security**: 10 rules
- **Performance**: 11 rules
- **Refactoring Criteria**: 14 criteria
- **Documentation**: 13 guidelines

**Total**: 70+ rules and guidelines

### Auto-fix Distribution
- Fully Auto-fixable: ~40%
- Partially Auto-fixable: ~20%
- Manual Fix Required: ~40%

### Severity Distribution
- CRITICAL: ~15%
- HIGH: ~25%
- MEDIUM: ~45%
- LOW: ~15%

---

## Contributing

### Adding New Rules

1. Identify the appropriate rule file
2. Follow the rule structure template
3. Include BAD and GOOD examples
4. Specify severity level
5. Indicate auto-fix capability
6. Test with sample code

### Modifying Existing Rules

1. Update rule description
2. Add new pattern examples
3. Update auto-fix capability if changed
4. Document reason for change
5. Update rule count statistics

---

## Integration

### With CLI Agents

Rules are referenced in prompts:
- `prompts/cline/error_detection.md` → uses `rules/java-spring-boot/error_detection.md`
- `prompts/qwen/security_audit.md` → uses `rules/java-spring-boot/security.md`

### With Services

- **CustomRulesLoader** (`app/services/custom_rules_loader.py`): Loads rules with priority
- **RefactoringClassifier** (`app/services/refactoring_classifier.py`): Uses refactoring_criteria.md
- **ReviewService** (`app/services/review_service.py`): Passes rules to CLI agents

---

## References

- [Spring Boot Best Practices](https://spring.io/guides/gs/spring-boot/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Effective Java (3rd Edition) by Joshua Bloch](https://www.oreilly.com/library/view/effective-java-3rd/9780134686097/)

---

## License

These rules are part of the AI Code Review System and are provided for use within the organization's development teams.

---

**Last Updated**: 2025-11-03  
**Version**: 2.0.0  
**Maintainer**: AI Code Review Team


