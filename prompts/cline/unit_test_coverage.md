# Unit Test Coverage Analysis


---

## ⚠️ CRITICAL: Read These Instructions First ⚠️

**MANDATORY**: Before proceeding with analysis, read these critical instruction files:

1. **JSON Output Requirements**: See `prompts/common/critical_json_requirements.md`
   - Explains EXACT JSON format required
   - Common mistakes to avoid
   - Validation checklist

2. **Git Diff Analysis**: See `prompts/common/git_diff_instructions.md`
   - How to identify changed files
   - What to analyze vs what to use for context
   - Proper reporting strategy

**Failure to follow these instructions will result in analysis being rejected.**

---
## Context
- **Repository Path**: {repo_path}
- **Language**: {language}
- **Custom Rules**: {custom_rules}
- **JIRA Context**: {jira_context}

## Instructions

Your task is to analyze the changes in this merge request and ensure they are covered by appropriate unit tests. Use `git diff` to detect changed files and analyze both the implementation code and corresponding test files.

### Step 1: Detect Changes
Use `git diff` command to identify:
1. All modified/added files in the source code
2. All modified/added test files
3. Focus on implementation files (not tests themselves)

### Step 2: Analyze Test Coverage

For each changed implementation file:

1. **Identify the corresponding test file(s)**:
   - Follow project conventions (e.g., `Service.java` → `ServiceTest.java`)
   - Check if test file exists
   - Check if test file was updated in this MR

2. **Analyze test quality**:
   - Are new methods/classes covered by tests?
   - Are edge cases tested?
   - Are error scenarios tested?
   - Are tests following project conventions?

3. **Check test infrastructure**:
   - Are appropriate test frameworks used? (JUnit5, Mockito, TestContainers)
   - Are base test classes used if available? (JupiterBase, JupiterArtemisBase, JupiterNuxeoBase, etc.)
   - Are mocks used appropriately?
   - Are integration tests needed?

### Step 3: Generate Missing Tests

If tests are missing or incomplete, generate test code that:

1. **Follows project conventions**:
   - Use the same naming patterns as existing tests
   - Extend appropriate *Base classes if they exist in the project
   - Use the same assertion style (AssertJ, JUnit assertions, etc.)
   - Follow the same package structure

2. **Uses modern testing practices**:
   - JUnit 5 (`@Test`, `@BeforeEach`, `@AfterEach`, lifecycle methods)
   - Mockito for mocking dependencies (`@Mock`, `@InjectMocks`, `when()`, `verify()`)
   - TestContainers for integration tests (if database/external services are involved)
   - Proper test method naming (e.g., `shouldReturnUserWhenIdExists()`)

3. **Covers important scenarios**:
   - Happy path (normal execution)
   - Edge cases (null values, empty collections, boundary values)
   - Error cases (exceptions, validation failures)
   - Business logic variants

4. **Example test structure**:
```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest extends JupiterBase {  // Use *Base class if exists
    
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
        assertThat(actualUser.getName()).isEqualTo("John Doe");
        verify(userRepository).findById(userId);
    }
    
    @Test
    void shouldThrowExceptionWhenUserNotFound() {
        // Given
        Long userId = 999L;
        when(userRepository.findById(userId)).thenReturn(Optional.empty());
        
        // When & Then
        assertThatThrownBy(() -> userService.getUserById(userId))
            .isInstanceOf(EntityNotFoundException.class)
            .hasMessage("User not found: 999");
    }
}
```

### Step 4: Integration Tests

If the code involves:
- Database operations
- External API calls
- Message queues
- File system operations

Consider suggesting integration tests using TestContainers:

```java
@Testcontainers
@SpringBootTest
class UserRepositoryIntegrationTest extends JupiterArtemisBase {
    
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");
    
    @Autowired
    private UserRepository userRepository;
    
    @Test
    void shouldSaveAndRetrieveUser() {
        // Given
        User user = new User(null, "John Doe", "john@example.com");
        
        // When
        User savedUser = userRepository.save(user);
        Optional<User> retrievedUser = userRepository.findById(savedUser.getId());
        
        // Then
        assertThat(retrievedUser).isPresent();
        assertThat(retrievedUser.get().getName()).isEqualTo("John Doe");
    }
}
```

## Output Format

### ⚠️ CRITICAL: JSON Output Requirements ⚠️

**READ**: `prompts/common/critical_json_requirements.md` for complete rules.

**Key Points**:
1. Output ONLY valid JSON, no other text
2. NO markdown code blocks (no ```json)
3. Include ALL required fields
4. Use exact field names and types
5. Validate before outputting

**Validation**: Your output will be validated against `schemas/review_result_schema.json`

### Required JSON Structure

Provide your analysis in this structure:

### 1. Coverage Summary
- Total files changed: X
- Files with tests: X
- Files without tests: X
- Test coverage status: GOOD / PARTIAL / POOR

### 2. Missing Tests
For each file without adequate tests:

```yaml
file: src/main/java/com/example/UserService.java
test_file: src/test/java/com/example/UserServiceTest.java
status: MISSING | INCOMPLETE
reason: "New method getUserById() has no tests"
priority: HIGH | MEDIUM | LOW
```

### 3. Generated Test Code

For each missing test, provide COMPLETE, READY-TO-USE test code:

````markdown
#### Test for UserService.getUserById()

**File**: `src/test/java/com/example/UserServiceTest.java`

```java
// COMPLETE test class or methods to add
```

**Test Scenarios Covered**:
- ✓ Happy path: user exists
- ✓ Error case: user not found
- ✓ Edge case: null ID handling
````

### 4. Recommendations

- Suggest base test classes to use if not used
- Suggest TestContainers if integration tests are needed
- Suggest test refactoring if tests are poorly structured
- Note any test anti-patterns found

## Important Notes

1. **Always check for existing patterns**: Examine existing test files in the project before generating new ones
2. **Use project's base classes**: Look for JupiterBase, JupiterArtemisBase, JupiterNuxeoBase and other *Base test classes
3. **Follow existing conventions**: Match the style, assertions, and structure of existing tests
4. **Prioritize critical code**: Focus on business logic, security-sensitive code, and complex algorithms
5. **Don't over-test**: Simple getters/setters don't always need tests

## Quality Checklist

For each generated test:
- [ ] Uses appropriate test framework (JUnit5)
- [ ] Extends project's base test class if available
- [ ] Uses Mockito for dependencies
- [ ] Follows Given-When-Then structure
- [ ] Has clear, descriptive test method names
- [ ] Tests both success and failure scenarios
- [ ] Uses appropriate assertions (AssertJ preferred)
- [ ] Includes necessary imports
- [ ] Is complete and ready to run

