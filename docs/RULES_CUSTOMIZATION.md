# Rules Customization Guide

## Overview

The code review system uses a hierarchical rules system that allows customization at project, team, and organization levels. This guide explains how to customize rules for your specific needs.

---

## Rule Priority Hierarchy

Rules are loaded in priority order (highest to lowest):

```
1. Project-Specific Rules (.project-rules/ in repository)
   ↓
2. Confluence Rules (team/org standards)
   ↓
3. Default Rules (rules/java-spring-boot/)
```

**Override Behavior**: Higher priority rules completely override lower priority rules for the same category.

---

## Project-Specific Rules

### Setup

Create `.project-rules/` directory in your repository root:

```bash
cd your-project
mkdir .project-rules
```

### Structure

```
your-project/
├── .project-rules/
│   ├── error_detection.md
│   ├── best_practices.md
│   ├── security.md
│   ├── refactoring_criteria.md
│   ├── performance.md
│   └── README.md (optional)
├── src/
├── pom.xml
└── README.md
```

### Creating Custom Rules

Custom rule files follow the same format as default rules.

**Example**: `.project-rules/security.md`

```markdown
# Custom Security Rules for ProjectX

## Overview
Additional security requirements specific to ProjectX beyond standard rules.

---

## Rule 1: Internal API Authentication

### Severity: CRITICAL

### Description
All calls to internal APIs must include our custom X-Internal-Auth token.

### Patterns to Detect

```java
// BAD: Missing authentication header
RestTemplate restTemplate = new RestTemplate();
ResponseEntity<String> response = restTemplate.getForEntity(
    "http://internal-api.company.com/users",
    String.class
);
```

### Correct Pattern

```java
// GOOD: Include authentication header
RestTemplate restTemplate = new RestTemplate();
HttpHeaders headers = new HttpHeaders();
headers.set("X-Internal-Auth", authTokenProvider.getToken());

HttpEntity<String> entity = new HttpEntity<>(headers);
ResponseEntity<String> response = restTemplate.exchange(
    "http://internal-api.company.com/users",
    HttpMethod.GET,
    entity,
    String.class
);
```

### Auto-fix Capability: No
```

---

## Confluence Rules

### Configuration

Confluence rules are loaded via n8n workflow. Configure in `.env`:

```env
CONFLUENCE_RULES_ENABLED=true
CONFLUENCE_SPACE_KEY=DEVSTD
CONFLUENCE_PAGE_ID=123456789
CONFLUENCE_CACHE_TTL=3600
```

### Page Structure

Create a Confluence page with this structure:

```markdown
# Development Standards - Code Review Rules

## Java Spring Boot

### Error Detection

[Error detection rules content...]

### Best Practices

[Best practices content...]

### Security

[Security rules...]
```

### n8n Workflow

The n8n workflow:
1. Receives review request
2. Checks cache for Confluence rules (1 hour TTL)
3. If not cached, fetches from Confluence REST API
4. Parses markdown content
5. Passes to review API as `confluence_rules` parameter

---

## Rule File Format

### Structure

```markdown
# [Category] Rules for [Project/Team Name]

## Overview
Brief description of these rules.

---

## Rule N: Rule Name

### Severity: CRITICAL | HIGH | MEDIUM | LOW

### Description
What this rule checks.

### Patterns to Detect
Code examples showing anti-patterns (BAD).

### Correct Pattern
Code examples showing correct patterns (GOOD).

### Auto-fix Capability: Yes | Partial | No

### References (optional)
Links to documentation, internal wiki, etc.

---
```

### Severity Levels

- **CRITICAL**: Must fix before merge (blocks MR)
- **HIGH**: Should fix before merge (strong recommendation)
- **MEDIUM**: Should address soon (tracked)
- **LOW**: Nice-to-have improvement

---

## Common Customization Scenarios

### Scenario 1: Company-Specific Logging Standard

**Requirement**: All log statements must use SLF4J with MDC for correlation IDs.

**Solution**: Create `.project-rules/best_practices.md`

```markdown
## Rule: Logging Standards

### Severity: HIGH

### Description
All logging must use SLF4J with MDC correlation IDs for distributed tracing.

### Patterns to Detect

```java
// BAD: System.out
System.out.println("User logged in: " + userId);

// BAD: Log without MDC
log.info("User logged in: {}", userId);
```

### Correct Pattern

```java
// GOOD: SLF4J with MDC
MDC.put("correlationId", correlationIdProvider.get());
MDC.put("userId", userId);
log.info("User logged in");
MDC.clear();

// BETTER: Use try-with-resources pattern
try (MDC.MDCCloseable mdc = MDC.putCloseable("correlationId", correlationId)) {
    log.info("User logged in: {}", userId);
}
```
```

---

### Scenario 2: Stricter Transaction Isolation

**Requirement**: All financial transactions must use SERIALIZABLE isolation.

**Solution**: Create `.project-rules/transaction_management.md`

```markdown
## Rule: Financial Transaction Isolation

### Severity: CRITICAL

### Description
Financial transactions MUST use SERIALIZABLE isolation level to prevent concurrent modification issues.

### Patterns to Detect

```java
// BAD: Default isolation for financial transaction
@Transactional
public void transferFunds(Long fromId, Long toId, BigDecimal amount) {
    // ...
}
```

### Correct Pattern

```java
// GOOD: SERIALIZABLE isolation
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transferFunds(Long fromId, Long toId, BigDecimal amount) {
    // ...
}
```

### Affected Services
- PaymentService
- AccountService
- TransactionService
```

---

### Scenario 3: Mandatory Code Ownership Annotations

**Requirement**: All services must have @TeamOwner annotation.

**Solution**: Create `.project-rules/best_practices.md`

```markdown
## Rule: Service Ownership

### Severity: MEDIUM

### Description
All @Service classes must have @TeamOwner annotation for accountability.

### Patterns to Detect

```java
// BAD: Missing @TeamOwner
@Service
public class UserService {
    // ...
}
```

### Correct Pattern

```java
// GOOD: Has @TeamOwner
@Service
@TeamOwner(team = "USER_MANAGEMENT_TEAM")
public class UserService {
    // ...
}
```

### Implementation

```java
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface TeamOwner {
    String team();
}
```
```

---

### Scenario 4: Refactoring Size Limits

**Requirement**: Any refactoring affecting >5 files must be separate MR.

**Solution**: Create `.project-rules/refactoring_criteria.md`

```markdown
# Refactoring Classification Criteria - ProjectX

## SIGNIFICANT Refactoring (Separate MR Required)

### Criterion 1: Scope - More than 5 Classes Affected

**Description**: Refactoring touches more than 5 classes or files (stricter than default).

**Rationale**: Our team prefers smaller, more focused MRs for easier review.
```

---

## Partial Overrides

### Option 1: Complete Replacement
Place a file in `.project-rules/` to completely replace default rules.

### Option 2: Additive Rules
Use different filename to add rules without replacing:

```
.project-rules/
├── security.md                    # Replaces default security rules
└── custom_api_standards.md        # Additional rules (doesn't replace anything)
```

**Note**: Currently, the system loads all `.md` files in `.project-rules/`. To add without replacing, use a unique filename that doesn't match default rule files.

---

## Testing Custom Rules

### Local Testing

1. **Create test repository**:
```bash
mkdir test-project
cd test-project
git init
mkdir .project-rules
```

2. **Add custom rule**:
```bash
cat > .project-rules/security.md << 'EOF'
# Custom Security Rules

## Rule 1: Test Rule
[rule content]
EOF
```

3. **Create test code**:
```bash
mkdir -p src/main/java/com/example
cat > src/main/java/com/example/Test.java << 'EOF'
public class Test {
    // Code that violates your custom rule
}
EOF
```

4. **Commit and push**:
```bash
git add .
git commit -m "Test custom rules"
```

5. **Create MR and trigger review**:
- The review system will detect `.project-rules/` and use your custom rules

---

### Validation

Check that custom rules are loaded:

1. **Review API logs**:
```bash
docker logs review-api 2>&1 | grep "Loading custom rules"
```

Expected output:
```
2025-11-03 10:15:23 INFO Loading custom rules from .project-rules/
2025-11-03 10:15:23 INFO Found 3 custom rule files
2025-11-03 10:15:23 INFO Custom rules override default rules for: security, best_practices
```

2. **Review results**:
Check if issues reference your custom rules:
```json
{
  "issues": [
    {
      "rule_source": "project_custom",
      "category": "Custom API Standards",
      ...
    }
  ]
}
```

---

## Best Practices

### 1. Start with Defaults
Don't override rules unnecessarily. Only customize what's truly project-specific.

### 2. Document Why
Include rationale for each custom rule:
```markdown
### Rationale
We use this pattern because:
1. Our infrastructure requires it
2. Past incidents showed the risk
3. Compliance requirement XYZ
```

### 3. Team Review
Before committing custom rules, get team consensus:
- Code review the rules
- Test on sample code
- Iterate based on feedback

### 4. Version Control
- Commit `.project-rules/` to your repository
- Track changes with meaningful commit messages
- Tag major rule updates

### 5. Keep Updated
Review and update custom rules when:
- Team standards change
- New technologies adopted
- Lessons learned from incidents

### 6. Reference Docs
Link to internal documentation:
```markdown
### References
- [Internal Wiki: Logging Standards](https://wiki.company.com/logging)
- [Architecture Decision Record: ADR-023](https://wiki.company.com/adr/023)
```

---

## Migration Guide

### Migrating from Manual Reviews

**Step 1**: Document existing standards
- Review past MR comments
- Extract common feedback patterns
- Identify repetitive issues

**Step 2**: Create rule files
- Start with high-severity issues
- Add examples from real code
- Include correct patterns

**Step 3**: Pilot testing
- Test on recent MRs
- Compare AI findings vs manual review
- Refine rules based on results

**Step 4**: Team rollout
- Document custom rules in README
- Train team on rule customization
- Establish process for updating rules

---

## Troubleshooting

### Issue: Custom Rules Not Applied

**Check**:
1. `.project-rules/` directory in repository root?
2. Files named correctly (e.g., `security.md`)?
3. Valid markdown format?
4. Files committed and pushed to branch being reviewed?

**Debug**:
```bash
# Check if directory exists in cloned repo
ls -la /tmp/review/project-{id}-mr-{iid}/.project-rules/

# Check file content
cat /tmp/review/project-{id}-mr-{iid}/.project-rules/security.md
```

---

### Issue: Rules Conflict with Defaults

**Expected Behavior**: Project rules completely override defaults for same category.

**If seeing both project and default rules**:
- Ensure filenames match exactly (case-sensitive)
- Check CustomRulesLoader priority logic
- Verify no duplicate categories in same file

---

### Issue: Confluence Rules Not Loading

**Check**:
1. `CONFLUENCE_RULES_ENABLED=true` in `.env`?
2. Confluence credentials valid?
3. Page ID correct?
4. n8n workflow active?

**Test Confluence connection**:
```bash
curl -u email@example.com:api_token \
  https://yourcompany.atlassian.net/wiki/rest/api/content/123456789?expand=body.storage
```

---

## Examples

### Complete Example: Microservice Team Rules

```markdown
# UserService Team Code Review Rules

## Overview
Custom rules for UserService microservice team, enforcing service-specific patterns.

---

## Rule 1: User Data Access

### Severity: CRITICAL

### Description
All user data access must go through UserRepository. Direct database access prohibited.

### Patterns to Detect
```java
// BAD: Direct JDBC access
Connection conn = dataSource.getConnection();
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
```

### Correct Pattern
```java
// GOOD: Use repository
User user = userRepository.findById(userId).orElseThrow();
```

---

## Rule 2: User PII Logging

### Severity: CRITICAL

### Description
Never log user PII (email, phone, address). Use userId only.

### Patterns to Detect
```java
// BAD: Logging email
log.info("User logged in: {}", user.getEmail());
```

### Correct Pattern
```java
// GOOD: Log userId only
log.info("User logged in: userId={}", user.getId());
```

---

## Rule 3: User State Transitions

### Severity: HIGH

### Description
User status changes must go through UserStateMachine to enforce valid transitions.

### Patterns to Detect
```java
// BAD: Direct status change
user.setStatus(UserStatus.SUSPENDED);
userRepository.save(user);
```

### Correct Pattern
```java
// GOOD: Use state machine
userStateMachine.transition(user, UserStatus.SUSPENDED);
```

---

## Team Contacts
- Owner: @john.doe
- Slack: #user-service-team
- Wiki: https://wiki.company.com/teams/user-service
```

---

## Future Enhancements

### Planned Features
1. **Rule Templates**: Reusable rule snippets
2. **Rule Testing Framework**: Automated testing of custom rules
3. **Rule Analytics**: Track effectiveness of custom rules
4. **Rule Versioning**: Support multiple rule versions per project
5. **Rule Inheritance**: Inherit from team/org rules with modifications

---

## References

- [Default Rules Documentation](../rules/java-spring-boot/README.md)
- [Prompts Guide](PROMPTS_GUIDE.md)
- [Confluence REST API](https://developer.atlassian.com/cloud/confluence/rest/v1/)

---

**Last Updated**: 2025-11-03  
**Version**: 2.0.0


