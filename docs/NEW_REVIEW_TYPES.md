# New Review Types

This document describes the two new review types added to the AI Code Review System.

## 1. UNIT_TEST_COVERAGE (Обязательный)

### Purpose
Automatically checks if code changes are covered by unit tests and generates missing test code.

### What It Does

1. **Analyzes Test Coverage**:
   - Detects all changed files using `git diff`
   - Identifies corresponding test files
   - Checks if new methods/classes have tests
   - Validates test quality and completeness

2. **Generates Missing Tests**:
   - Creates complete, ready-to-use test code
   - Follows project conventions (naming, structure, base classes)
   - Uses modern testing frameworks:
     - JUnit 5
     - Mockito for mocking
     - TestContainers for integration tests
   - Extends project's `*Base` test classes if available:
     - `JupiterBase`
     - `JupiterArtemisBase`
     - `JupiterNuxeoBase`
     - etc.

3. **Test Scenarios Covered**:
   - Happy path (normal execution)
   - Edge cases (null values, empty collections, boundaries)
   - Error cases (exceptions, validation failures)
   - Business logic variants

### When It Runs

- **By default**: Always included in review process
- **Can be disabled**: Set `review_types` without `UNIT_TEST_COVERAGE`

### Output Format

```yaml
coverage_summary:
  total_files_changed: 5
  files_with_tests: 3
  files_without_tests: 2
  status: PARTIAL

missing_tests:
  - file: src/main/java/com/example/UserService.java
    test_file: src/test/java/com/example/UserServiceTest.java
    status: INCOMPLETE
    reason: "New method getUserById() has no tests"
    priority: HIGH
    
generated_tests:
  - test_file: src/test/java/com/example/UserServiceTest.java
    code: |
      @ExtendWith(MockitoExtension.class)
      class UserServiceTest extends JupiterBase {
          @Mock
          private UserRepository userRepository;
          
          @InjectMocks
          private UserService userService;
          
          @Test
          void shouldReturnUserWhenIdExists() {
              // Given
              Long userId = 1L;
              User expectedUser = new User(userId, "John Doe");
              when(userRepository.findById(userId)).thenReturn(Optional.of(expectedUser));
              
              // When
              User actualUser = userService.getUserById(userId);
              
              // Then
              assertThat(actualUser).isNotNull();
              assertThat(actualUser.getId()).isEqualTo(userId);
              verify(userRepository).findById(userId);
          }
      }
    scenarios_covered:
      - "Happy path: user exists"
      - "Error case: user not found"

recommendations:
  - "Use JupiterBase for all new tests"
  - "Consider TestContainers for repository tests"
```

### Configuration

In API request:
```json
{
  "project_id": 123,
  "merge_request_iid": 456,
  "review_types": ["ERROR_DETECTION", "UNIT_TEST_COVERAGE"]
}
```

### Prompts

- Cline: `prompts/cline/unit_test_coverage.md`
- Qwen: `prompts/qwen/unit_test_coverage.md`

---

## 2. MEMORY_BANK (Опциональный)

### Purpose
Initializes or validates a project's Memory Bank - a structured knowledge base for AI-assisted development.

### What Is Memory Bank?

Memory Bank is based on **Cursor's Memory Bank (v1.2 Final)** methodology. It's a collection of markdown files that provide comprehensive project context:

1. **projectbrief.md** - Project scope, objectives, and requirements
2. **productContext.md** - Why the project exists, problems it solves
3. **systemPatterns.md** - Architecture, design patterns, technical decisions
4. **techContext.md** - Technology stack, dependencies, setup
5. **activeContext.md** - Current work focus, recent changes, next steps
6. **progress.md** - What works, what's left, known issues

### What It Does

#### If Memory Bank Exists:
1. **Validates** all core files are present
2. **Checks** content quality and completeness
3. **Reports** status of each file
4. **Suggests** updates if files are outdated or incomplete

#### If Memory Bank Doesn't Exist:
1. **Analyzes** the entire project:
   - Repository structure
   - Build configuration (pom.xml, build.gradle)
   - Main application class
   - Key packages and modules
   - Existing documentation

2. **Identifies** technologies:
   - Programming language and version
   - Framework (Spring Boot, etc.)
   - Database
   - Build tool
   - Testing frameworks

3. **Creates** complete Memory Bank:
   - All 6 core files with actual project data
   - Optional files (changelog.md, tags_index.md)
   - Mermaid diagrams for architecture visualization

### When It Runs

- **Explicitly requested**: Include `MEMORY_BANK` in `review_types`
- **Optional**: Not part of default review flow
- **Recommended**: Run once per project to initialize, then periodically to validate

### Output Format

#### Validation (Existing Memory Bank):
```yaml
memory_bank_status: EXISTS
validation_results:
  - file: projectbrief.md
    status: OK
    notes: "Contains project scope and requirements"
  
  - file: systemPatterns.md
    status: INCOMPLETE
    notes: "Missing recent architectural decisions"

recommendations:
  - "Update activeContext.md to reflect this MR"
  - "Add database optimization patterns to systemPatterns.md"
```

#### Initialization (New Memory Bank):
```yaml
memory_bank_status: CREATED
files_created:
  - projectbrief.md
  - productContext.md
  - systemPatterns.md
  - techContext.md
  - activeContext.md
  - progress.md
  - changelog.md
  - tags_index.md

analysis_summary:
  project_type: "REST API Microservice"
  primary_technology: "Spring Boot 3.2"
  architecture_pattern: "Layered Architecture"
  key_features:
    - "Multi-agent code review system"
    - "GitLab integration"
    - "Automated MR creation"
  confidence: HIGH

recommendations:
  - "Review and refine projectbrief.md with product owner"
  - "Update activeContext.md as work progresses"
```

### Integration with Code Review

Once Memory Bank exists, **all review agents automatically use it**:

1. **System Prompt** instructs agents to check for `memory-bank/` directory
2. If found, agents read key files for context
3. Recommendations align with documented:
   - Architectural decisions
   - Technical constraints
   - Project-specific patterns
   - Current work focus

### Configuration

In API request:
```json
{
  "project_id": 123,
  "merge_request_iid": 456,
  "review_types": ["MEMORY_BANK"]
}
```

Or combined with other reviews:
```json
{
  "project_id": 123,
  "merge_request_iid": 456,
  "review_types": ["ERROR_DETECTION", "BEST_PRACTICES", "MEMORY_BANK"]
}
```

### Prompts

- Cline: `prompts/cline/memory_bank.md`
- Qwen: `prompts/qwen/memory_bank.md`

### Benefits

1. **Faster Onboarding**: New developers understand project quickly
2. **Consistent Reviews**: AI agents use project context for better recommendations
3. **Knowledge Preservation**: Architectural decisions and rationale are documented
4. **Living Documentation**: Updates as project evolves
5. **AI-Friendly**: Structured format optimized for AI comprehension

---

## Summary

| Review Type | Required | Purpose | When to Use |
|------------|----------|---------|-------------|
| **UNIT_TEST_COVERAGE** | ✅ Yes | Ensure code changes have tests | Every MR |
| **MEMORY_BANK** | ❌ Optional | Initialize/validate project knowledge base | Once per project, then periodically |

## Related Documentation

- [System Prompt Guide](SYSTEM_PROMPT_GUIDE.md) - How system prompt works
- [Prompts Guide](PROMPTS_GUIDE.md) - How to customize prompts
- Memory Bank Template: See `prompts/cline/memory_bank.md` or `prompts/qwen/memory_bank.md`

