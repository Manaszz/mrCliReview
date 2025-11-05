# Best Practices Prompt for Cline CLI

## Objective

Analyze Java Spring Boot code changes to ensure adherence to SOLID principles, DRY, KISS, YAGNI, Spring Boot conventions, and modern Java best practices (Java 11-21 features).


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

### Step 1: Identify Changed Files

Execute `git diff` to determine which files have changed:

```bash
git diff --name-only origin/<target-branch>
```

**You have full project access** - browse any file for context. **But analyze and report issues primarily for changed files.**

See `prompts/common/git_diff_instructions.md` for complete strategy.

## Analysis Scope

### 1. SOLID Principles

#### Single Responsibility Principle (SRP)
**Check for**:
- Classes doing multiple unrelated things
- Business logic mixed with HTTP concerns in controllers
- Data access logic in service classes
- Multiple reasons to change a class

**Example patterns**:
```java
// BAD: Controller doing business logic
@RestController
public class UserController {
    @Autowired
    private UserRepository userRepository;
    
    @PostMapping("/users")
    public User createUser(@RequestBody UserDto dto) {
        // Validation in controller - BAD!
        if (dto.getAge() < 18) {
            throw new IllegalArgumentException("Too young");
        }
        
        // Business logic in controller - BAD!
        User user = new User();
        user.setName(dto.getName());
        user.setAge(dto.getAge());
        user.setCreatedAt(LocalDateTime.now());
        user.setStatus(UserStatus.ACTIVE);
        
        // Direct repository access - BAD!
        return userRepository.save(user);
    }
}

// GOOD: Proper separation
@RestController
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;
    
    @PostMapping("/users")
    public User createUser(@Valid @RequestBody UserDto dto) {
        return userService.createUser(dto);
    }
}

@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    
    @Transactional
    public User createUser(UserDto dto) {
        User user = User.builder()
            .name(dto.getName())
            .age(dto.getAge())
            .createdAt(LocalDateTime.now())
            .status(UserStatus.ACTIVE)
            .build();
        
        return userRepository.save(user);
    }
}
```

#### Open/Closed Principle (OCP)
**Check for**:
- Classes requiring modification to add functionality
- Missing abstraction points
- Hardcoded behavior instead of strategy pattern

#### Liskov Substitution Principle (LSP)
**Check for**:
- Subclasses changing behavior of parent class methods
- Throwing unexpected exceptions in overridden methods
- Weakening preconditions or strengthening postconditions

#### Interface Segregation Principle (ISP)
**Check for**:
- Large interfaces forcing implementations to implement unused methods
- Clients depending on methods they don't use

#### Dependency Inversion Principle (DIP)
**Check for**:
- High-level modules depending on low-level modules
- Dependencies on concrete implementations instead of abstractions
- Missing interfaces for service abstractions

### 2. DRY (Don't Repeat Yourself)

**Check for**:
- Duplicate code blocks
- Repeated validation logic
- Copy-pasted methods with minor differences
- Duplicate constants and magic numbers

**Example patterns**:
```java
// BAD: Duplicate validation
public void createUser(UserDto dto) {
    if (dto.getName() == null || dto.getName().isEmpty()) {
        throw new ValidationException("Name required");
    }
    if (dto.getEmail() == null || !dto.getEmail().contains("@")) {
        throw new ValidationException("Valid email required");
    }
    // ...
}

public void updateUser(Long id, UserDto dto) {
    if (dto.getName() == null || dto.getName().isEmpty()) { // Duplicate!
        throw new ValidationException("Name required");
    }
    if (dto.getEmail() == null || !dto.getEmail().contains("@")) { // Duplicate!
        throw new ValidationException("Valid email required");
    }
    // ...
}

// GOOD: Extract validation
private void validateUserDto(UserDto dto) {
    if (dto.getName() == null || dto.getName().isEmpty()) {
        throw new ValidationException("Name required");
    }
    if (dto.getEmail() == null || !dto.getEmail().contains("@")) {
        throw new ValidationException("Valid email required");
    }
}

// Even BETTER: Use Bean Validation
public record UserDto(
    @NotBlank(message = "Name is required")
    String name,
    
    @NotBlank(message = "Email is required")
    @Email(message = "Valid email required")
    String email
) {}
```

### 3. KISS (Keep It Simple, Stupid)

**Check for**:
- Overly complex methods (>50 lines, >3 nesting levels)
- Unnecessary abstractions
- Complex boolean expressions
- Clever code that's hard to understand

**Example patterns**:
```java
// BAD: Complex conditional
if ((user != null && user.getStatus() != null && 
    (user.getStatus().equals(Status.ACTIVE) || user.getStatus().equals(Status.PENDING))) && 
    (user.getRole() != null && (user.getRole().equals(Role.ADMIN) || user.getRole().equals(Role.MODERATOR))) &&
    user.getLastLogin() != null && user.getLastLogin().isAfter(LocalDateTime.now().minusDays(30))) {
    // ...
}

// GOOD: Extract to meaningful method
if (isActiveUser(user) && hasModeratorRole(user) && hasRecentLogin(user)) {
    // ...
}

private boolean isActiveUser(User user) {
    return user != null && user.getStatus() != null &&
           (user.getStatus() == Status.ACTIVE || user.getStatus() == Status.PENDING);
}
```

### 4. Spring Boot Conventions

**Check for**:
- Incorrect annotation usage (@Service, @Repository, @Component, @Controller, @RestController)
- Field injection instead of constructor injection
- @Transactional on repository methods (should be on service)
- @Transactional on private methods (won't work)
- Missing @RequestBody, @PathVariable, @RequestParam in controllers
- Returning entities from controllers (should return DTOs)
- @Autowired instead of constructor injection

**Example patterns**:
```java
// BAD: Field injection
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository; // Field injection - not ideal
    
    @Autowired
    private EmailService emailService;
}

// GOOD: Constructor injection with Lombok
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
}

// BAD: @Transactional on repository
public interface UserRepository extends JpaRepository<User, Long> {
    @Transactional // Wrong place!
    User findByEmail(String email);
}

// GOOD: @Transactional on service
@Service
public class UserService {
    @Transactional(readOnly = true)
    public User findByEmail(String email) {
        return userRepository.findByEmail(email);
    }
}
```

### 5. Modern Java Features (Java 11-21)

#### Records (Java 16+)
**Check for**:
- Traditional POJOs that could be Records
- DTOs with only getters (immutable data holders)
- Value objects

**Example patterns**:
```java
// BAD: Traditional POJO for immutable data
public class UserDto {
    private final String name;
    private final int age;
    
    public UserDto(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    public String getName() { return name; }
    public int getAge() { return age; }
    
    @Override
    public boolean equals(Object o) { /* ... */ }
    @Override
    public int hashCode() { /* ... */ }
    @Override
    public String toString() { /* ... */ }
}

// GOOD: Use Record
public record UserDto(String name, int age) {
    // Compact constructor for validation
    public UserDto {
        if (age < 0) {
            throw new IllegalArgumentException("Age must be positive");
        }
    }
}
```

#### Sealed Classes (Java 17+)
**Check for**:
- Inheritance hierarchies that should be closed
- Type hierarchies with exhaustive pattern matching needs

**Example patterns**:
```java
// GOOD: Sealed class for closed hierarchy
public sealed interface PaymentMethod 
    permits CreditCard, DebitCard, BankTransfer {}

public record CreditCard(String number, String cvv) implements PaymentMethod {}
public record DebitCard(String number, String pin) implements PaymentMethod {}
public record BankTransfer(String accountNumber) implements PaymentMethod {}

// Now can use exhaustive pattern matching
public double calculateFee(PaymentMethod payment) {
    return switch (payment) {
        case CreditCard c -> 0.03;
        case DebitCard d -> 0.01;
        case BankTransfer b -> 0.00;
        // Compiler ensures all cases covered
    };
}
```

#### Pattern Matching (Java 17+)
**Check for**:
- instanceof checks followed by casts
- Complex type checking logic

**Example patterns**:
```java
// BAD: Old style instanceof
if (obj instanceof String) {
    String str = (String) obj;
    return str.length();
}

// GOOD: Pattern matching for instanceof
if (obj instanceof String str) {
    return str.length();
}

// GOOD: Pattern matching in switch (Java 21)
return switch (obj) {
    case String s -> s.length();
    case Integer i -> i;
    case null -> 0;
    default -> -1;
};
```

#### Proper Generics Usage
**Check for**:
- Raw types (List instead of List<String>)
- Incorrect wildcard usage
- Missing type bounds

**Example patterns**:
```java
// BAD: Raw type
List users = new ArrayList();

// GOOD: Proper generic type
List<User> users = new ArrayList<>();

// GOOD: Bounded wildcard (PECS - Producer Extends Consumer Super)
public void addUsers(List<? extends User> users) { // Producer
    this.allUsers.addAll(users);
}

public void getUsers(List<? super User> destination) { // Consumer
    destination.addAll(this.allUsers);
}
```

### 6. Code Quality

**Check for**:
- Long methods (>50 lines)
- Deep nesting (>3 levels)
- High cyclomatic complexity
- Magic numbers (should be constants)
- Unclear variable names
- Missing JavaDoc on public APIs

## Output Format

### ⚠️ CRITICAL: JSON Output Requirements ⚠️

**READ**: `prompts/common/critical_json_requirements.md` for complete rules.

**Key Points**:
1. Output ONLY valid JSON, no other text
2. NO markdown code blocks (no ```json)
3. Include ALL required fields
4. Use exact field names and types
5. Validate before outputting

### Required JSON Structure

```json
{
  "review_type": "BEST_PRACTICES",
  "issues": [
    {
      "file": "src/main/java/com/example/service/UserService.java",
      "line": 23,
      "severity": "HIGH",
      "category": "SOLID - SRP Violation",
      "message": "Service class contains HTTP-specific logic (ResponseEntity construction)",
      "code_snippet": "return ResponseEntity.ok(user);",
      "suggestion": "Move ResponseEntity construction to controller. Service should return domain objects, controller should handle HTTP concerns.",
      "auto_fixable": false
    },
    {
      "file": "src/main/java/com/example/dto/UserDto.java",
      "line": 5,
      "severity": "MEDIUM",
      "category": "Modern Java - Records",
      "message": "Immutable data class could be converted to Record",
      "code_snippet": "public class UserDto { private final String name; private final int age; ... }",
      "suggestion": "Convert to Record: public record UserDto(String name, int age) {}",
      "auto_fixable": true
    },
    {
      "file": "src/main/java/com/example/service/OrderService.java",
      "line": 45,
      "severity": "MEDIUM",
      "category": "Spring Boot - Injection",
      "message": "Using field injection instead of constructor injection",
      "code_snippet": "@Autowired private UserRepository repo;",
      "suggestion": "Use constructor injection for better testability and immutability. Use @RequiredArgsConstructor with final fields.",
      "auto_fixable": true
    }
  ],
  "summary": {
    "total_issues": 3,
    "solid_violations": 1,
    "dry_violations": 0,
    "spring_conventions": 1,
    "modern_java_opportunities": 1,
    "files_analyzed": 12
  }
}
```


**Validation**: Your output will be validated against `schemas/review_result_schema.json`

## Severity Levels

- **CRITICAL**: Fundamental design flaw requiring immediate attention
- **HIGH**: Violates important principles, should be fixed before merge
- **MEDIUM**: Best practice violation, should be addressed soon
- **LOW**: Minor improvement opportunity
- **INFO**: Suggestion for enhancement

## Instructions

1. Analyze code changes in context of the overall architecture
2. Consider project standards in {custom_rules}
3. Use {jira_context} to understand if patterns are intentional
4. Focus on architectural improvements, not just syntax
5. Suggest modern Java features where applicable
6. Prioritize changes that improve maintainability
7. Output comprehensive analysis in JSON format



