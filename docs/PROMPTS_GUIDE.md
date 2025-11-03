# Prompts System Guide

## Overview

The prompts system provides structured instructions to CLI agents (Cline and Qwen Code) for performing code reviews. Prompts are externalized, version-controlled, and support variable substitution for flexibility.

---

## Directory Structure

```
prompts/
├── cline/                      # Prompts for Cline CLI (DeepSeek V3.1)
│   ├── error_detection.md
│   ├── best_practices.md
│   ├── refactoring.md
│   ├── security_audit.md
│   └── documentation.md
├── qwen/                       # Prompts for Qwen Code CLI
│   ├── error_detection.md
│   ├── best_practices.md
│   └── refactoring.md
├── additional/                 # Prompts for specialized review types
│   ├── performance.md
│   ├── architecture.md
│   ├── transaction_management.md
│   ├── concurrency.md
│   └── database_optimization.md
└── todo/                       # Prompts for future TODO features
    ├── jira_task_matcher.md
    └── changelog_generator.md
```

---

## Prompt Structure

Each prompt file follows this structure:

```markdown
# [Review Type] Prompt for [CLI Agent]

## Objective
Clear statement of what this prompt aims to achieve.

## Context
Variables that will be substituted:
- **Repository Path**: {repo_path}
- **Language**: {language}
- **Changed Files**: {changed_files}
- **Custom Rules**: {custom_rules}
- **JIRA Context**: {jira_context}

## Analysis Scope
Detailed instructions on what to analyze and how.

### Category 1
Specific patterns to detect with examples.

### Category 2
More patterns...

## Output Format
JSON structure expected from CLI agent.

## Instructions
Step-by-step instructions for the CLI agent.
```

---

## Variable Substitution

### Available Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{repo_path}` | Local path to cloned repository | `/tmp/review/project-123-mr-456` |
| `{language}` | Programming language | `java` |
| `{changed_files}` | List of files modified in MR | `["src/main/java/User.java", ...]` |
| `{custom_rules}` | Loaded custom rules content | Content of `.project-rules/` or Confluence |
| `{jira_context}` | JIRA task description and context | Task description, acceptance criteria |
| `{review_types}` | Selected review types | `["ERROR_DETECTION", "SECURITY_AUDIT"]` |

### Substitution Process

1. **Load Prompt**: Read prompt file from `prompts/{agent}/{review_type}.md`
2. **Gather Context**: Collect variable values from request and environment
3. **Substitute**: Replace `{variable}` placeholders with actual values
4. **Send to CLI**: Pass processed prompt to CLI agent

### Example Substitution

**Original Prompt**:
```markdown
## Context
- **Repository Path**: {repo_path}
- **Changed Files**: {changed_files}
```

**After Substitution**:
```markdown
## Context
- **Repository Path**: /tmp/review/project-123-mr-456
- **Changed Files**: ["src/main/java/UserService.java", "src/main/java/OrderService.java"]
```

---

## Prompt Types

### 1. Core Prompts (Cline)

#### error_detection.md
**Purpose**: Identify bugs and potential crashes  
**Key Checks**:
- NullPointerException risks
- Exception handling issues
- Resource leaks
- Type safety violations

**Output**: JSON with issues, severity, and suggestions

---

#### best_practices.md
**Purpose**: Enforce SOLID, Spring conventions, modern Java  
**Key Checks**:
- SOLID principle violations
- Spring Boot anti-patterns
- DRY violations
- KISS compliance
- Modern Java feature opportunities

**Output**: JSON with best practice violations and refactoring suggestions

---

#### refactoring.md
**Purpose**: Suggest code improvements for maintainability  
**Key Checks**:
- Circular dependencies
- Business logic in controllers
- Code smells (long methods, deep nesting)
- Complex boolean expressions

**Output**: JSON with refactoring suggestions classified as SIGNIFICANT or MINOR

---

#### security_audit.md
**Purpose**: Identify security vulnerabilities  
**Key Checks**:
- SQL injection
- XSS
- CSRF
- Authentication/authorization issues
- Hardcoded credentials
- Weak cryptography

**Output**: JSON with vulnerabilities, severity, CWE references, attack scenarios

---

#### documentation.md
**Purpose**: Generate JavaDoc and code comments  
**Key Checks**:
- Missing JavaDoc on public APIs
- Incomplete method documentation
- Complex logic needing comments

**Output**: JSON with generated documentation + git commit to source branch

---

### 2. Specialized Prompts (Additional)

#### performance.md
**Purpose**: Identify performance issues  
**Focus**: N+1 queries, caching, stream optimization, connection pooling

#### architecture.md
**Purpose**: Verify architectural patterns  
**Focus**: Circuit breakers, API design, microservices patterns, DTOs

#### transaction_management.md
**Purpose**: Verify @Transactional usage  
**Focus**: Placement, propagation, isolation levels

#### concurrency.md
**Purpose**: Identify concurrency issues  
**Focus**: Race conditions, thread safety, @Async usage

#### database_optimization.md
**Purpose**: Optimize database queries  
**Focus**: Query optimization, lazy/eager loading, batch operations

---

### 3. Simplified Prompts (Qwen)

Qwen Code CLI uses simplified versions of core prompts:
- Focused on essential patterns
- Less verbose instructions
- Faster execution

---

### 4. TODO Prompts (Future Features)

#### jira_task_matcher.md
**Purpose**: Verify MR implements JIRA task requirements  
**Status**: TODO - requires JIRA API integration

#### changelog_generator.md
**Purpose**: Generate CHANGELOG.md entries  
**Status**: TODO - requires git log parsing

---

## Customizing Prompts

### Project-Specific Prompts

Create custom prompts in `.project-prompts/` directory (not yet implemented, future feature):

```
your-project/
├── .project-prompts/
│   ├── error_detection.md      # Override default
│   └── custom_security.md      # Additional prompt
├── src/
└── pom.xml
```

### Modifying Default Prompts

1. **Clone Repository**: Get the review service repository
2. **Edit Prompt**: Modify file in `prompts/` directory
3. **Test**: Run review on sample MR
4. **Deploy**: Rebuild Docker image or update mounted volume

---

## Prompt Best Practices

### 1. Be Specific
❌ **Bad**: "Check for errors"  
✅ **Good**: "Check for NullPointerException risks where methods are called on potentially null objects without null checks"

### 2. Provide Examples
Always include:
- BAD example (anti-pattern)
- GOOD example (correct pattern)
- Explanation of why

### 3. Structured Output
Define exact JSON structure expected:
```json
{
  "review_type": "ERROR_DETECTION",
  "issues": [...],
  "summary": {...}
}
```

### 4. Actionable Suggestions
Each issue should include:
- What's wrong
- Why it's wrong
- How to fix it
- Code example of fix

### 5. Context-Aware
Use variables to provide context:
- `{custom_rules}` for project-specific standards
- `{jira_context}` to understand intent
- `{changed_files}` to focus scope

---

## Integration with Rules

Prompts reference rules from `rules/java-spring-boot/`:

```markdown
## Analysis Scope
Perform checks according to rules defined in {custom_rules}.

### 1. NullPointerException Prevention
Refer to rules/java-spring-boot/error_detection.md Rule 1 for patterns.
```

Rules provide:
- Detailed pattern examples
- Severity levels
- Auto-fix capability

Prompts provide:
- Instructions for CLI agent
- Output format
- Processing workflow

---

## Troubleshooting

### Issue: CLI Agent Not Following Prompt

**Possible Causes**:
1. Prompt too vague or ambiguous
2. JSON output format not clearly specified
3. Too many instructions (information overload)

**Solutions**:
1. Make instructions more specific and actionable
2. Provide exact JSON schema with examples
3. Break complex prompts into focused sections

---

### Issue: Variable Not Substituted

**Check**:
1. Variable name matches exactly (case-sensitive)
2. Variable value is provided in ReviewRequest
3. ReviewService populates variable correctly

**Debug**:
```python
# In ReviewService
processed_prompt = self.substitute_variables(prompt, {
    'repo_path': repo_path,
    'language': language,
    'changed_files': json.dumps(changed_files),
    'custom_rules': custom_rules_content
})
print(f"Processed prompt: {processed_prompt[:500]}")
```

---

### Issue: Inconsistent Results

**Possible Causes**:
1. Prompt too open-ended (allows interpretation)
2. Examples not comprehensive
3. Output format not strictly defined

**Solutions**:
1. Add more specific instructions
2. Provide examples for edge cases
3. Use JSON schema validation

---

## Performance Considerations

### Prompt Length
- **Cline**: Can handle longer prompts (10K+ tokens)
- **Qwen**: Prefer shorter, focused prompts (<5K tokens)

### Variable Substitution Overhead
- Minimal impact (<10ms per substitution)
- Variables are substituted once before sending to CLI

### Caching
- Prompts are loaded from disk each time (not cached)
- Consider caching for high-frequency reviews (future optimization)

---

## Version Control

### Tracking Changes
- All prompts are version-controlled in git
- Use meaningful commit messages when updating prompts
- Tag releases for major prompt changes

### Rollback Strategy
If new prompt causes issues:
1. Revert git commit
2. Rebuild Docker image or update volume
3. Re-run affected reviews

---

## Examples

### Example 1: Adding New Check to Error Detection

**Goal**: Add check for improper use of `@Async` on methods returning void

**Steps**:
1. Open `prompts/cline/error_detection.md`
2. Add new section:
```markdown
### 8. @Async Method Return Type

**Check for**: @Async methods returning void without proper error handling

**Anti-pattern**:
```java
@Async
public void sendEmail(String to, String subject) {
    // If exception thrown, it's silently swallowed!
    emailService.send(to, subject);
}
```

**Correct pattern**:
```java
@Async
public CompletableFuture<Void> sendEmail(String to, String subject) {
    return CompletableFuture.runAsync(() -> {
        emailService.send(to, subject);
    });
}
```
```
3. Test on sample code
4. Deploy updated prompt

---

### Example 2: Creating Custom Prompt for Team

**Goal**: Add company-specific security check

**Steps**:
1. Create `prompts/cline/company_security.md`
2. Define company-specific patterns
3. Update ReviewService to load custom prompt
4. Add to review types enum

---

## Future Enhancements

### Planned Features
1. **Prompt Templates**: Reusable prompt components
2. **Dynamic Prompts**: Adjust based on project type
3. **Prompt Testing**: Automated testing of prompt effectiveness
4. **Prompt Analytics**: Track which prompts find most issues
5. **Multi-language Prompts**: Support for Python, JavaScript, etc.

---

## References

- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Claude Prompt Library](https://docs.anthropic.com/claude/prompt-library)
- [Cline CLI Documentation](https://docs.cline.bot)
- [Qwen Code Documentation](https://qwenlm.github.io)

---

**Last Updated**: 2025-11-03  
**Version**: 2.0.0


