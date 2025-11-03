# Error Detection Prompt for Cline CLI

## Objective

Analyze the provided Java Spring Boot code changes and identify potential bugs, errors, and issues that could lead to runtime failures or unexpected behavior.

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Changed Files**: {changed_files}
- **Custom Rules**: {custom_rules}
- **JIRA Context**: {jira_context}

## Analysis Scope

Perform comprehensive error detection focusing on:

### 1. NullPointerException Prevention

**Check for**:
- Dereferencing potentially null values without checks
- Missing null checks at system boundaries (API inputs, external service responses)
- Incorrect Optional usage (calling `.get()` without `.isPresent()` check)
- Returning null from methods that could return Optional
- Chain calls on potentially null objects

**Example patterns to detect**:
```java
// BAD: Potential NPE
public void process(User user) {
    String name = user.getName().toUpperCase(); // NPE if getName() returns null
    log.info("Processing user: " + name);
}

// BAD: Unsafe Optional usage
public String getUserName(Long userId) {
    Optional<User> user = userRepository.findById(userId);
    return user.get().getName(); // Throws NoSuchElementException if empty
}

// GOOD: Defensive programming
public void process(User user) {
    if (user == null || user.getName() == null) {
        log.warn("Cannot process null user or user with null name");
        return;
    }
    String name = user.getName().toUpperCase();
    log.info("Processing user: " + name);
}

// GOOD: Safe Optional usage
public String getUserName(Long userId) {
    return userRepository.findById(userId)
        .map(User::getName)
        .orElse("Unknown");
}
```

### 2. Exception Handling Anti-Patterns

**Check for**:
- Empty catch blocks that swallow exceptions
- Catching generic Exception instead of specific exceptions
- Not logging exception stack traces
- Throwing Exception instead of specific exception types
- Missing @ControllerAdvice for global exception handling in REST controllers
- Catching Throwable (includes Errors which shouldn't be caught)

**Example patterns to detect**:
```java
// BAD: Empty catch block
try {
    processPayment(order);
} catch (Exception e) {
    // Silent failure - bad!
}

// BAD: Generic exception catch without logging
try {
    processPayment(order);
} catch (Exception e) {
    log.error("Payment failed"); // No stack trace!
    return false;
}

// GOOD: Specific exception with proper logging
try {
    processPayment(order);
} catch (PaymentException e) {
    log.error("Payment processing failed for order {}: {}", order.getId(), e.getMessage(), e);
    throw new OrderProcessingException("Failed to process payment", e);
}

// GOOD: Use @ControllerAdvice for centralized exception handling
@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(PaymentException.class)
    public ResponseEntity<ErrorResponse> handlePaymentException(PaymentException e) {
        log.error("Payment error: {}", e.getMessage(), e);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
            .body(new ErrorResponse("PAYMENT_FAILED", e.getMessage()));
    }
}
```

### 3. Resource Management Issues

**Check for**:
- Not using try-with-resources for AutoCloseable resources
- Manual resource closing without proper finally blocks
- Database connections not properly closed
- File handles not closed
- Stream operations not properly closed

**Example patterns to detect**:
```java
// BAD: Manual resource management
public String readFile(String path) throws IOException {
    FileReader reader = new FileReader(path);
    BufferedReader buffered = new BufferedReader(reader);
    StringBuilder content = new StringBuilder();
    String line;
    while ((line = buffered.readLine()) != null) {
        content.append(line);
    }
    buffered.close(); // Won't execute if exception thrown!
    return content.toString();
}

// GOOD: Try-with-resources
public String readFile(String path) throws IOException {
    try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
        return reader.lines()
            .collect(Collectors.joining("\n"));
    }
}
```

### 4. Type Safety Violations

**Check for**:
- Unchecked casts without instanceof check
- Raw types usage (List instead of List<String>)
- Suppressed unchecked warnings without justification
- Type erasure issues in generics
- ClassCastException risks

**Example patterns to detect**:
```java
// BAD: Unchecked cast
public User getUser(Object obj) {
    User user = (User) obj; // ClassCastException if obj is not User!
    return user;
}

// BAD: Raw type
List users = new ArrayList(); // Should be List<User>

// GOOD: Type-safe with instanceof check
public User getUser(Object obj) {
    if (!(obj instanceof User)) {
        throw new IllegalArgumentException("Object is not a User");
    }
    return (User) obj;
}

// GOOD: Proper generics
List<User> users = new ArrayList<>();
```

### 5. Optional Usage Correctness

**Check for**:
- Calling Optional.get() without checking isPresent()
- Using Optional.isPresent() + Optional.get() instead of map/ifPresent
- Optional as method parameter (anti-pattern)
- Optional fields in classes (anti-pattern)
- Returning null instead of Optional.empty()

**Example patterns to detect**:
```java
// BAD: Unsafe get()
Optional<User> userOpt = findUser(id);
return userOpt.get(); // Throws exception if empty

// BAD: Optional as parameter
public void process(Optional<User> user) { // Anti-pattern!
    // ...
}

// GOOD: Safe Optional usage
Optional<User> userOpt = findUser(id);
return userOpt.orElseThrow(() -> new UserNotFoundException(id));

// GOOD: Functional style
return findUser(id)
    .map(User::getName)
    .orElse("Unknown");
```

### 6. Collection Operations Errors

**Check for**:
- Modifying collection while iterating (ConcurrentModificationException)
- Accessing collection elements without size check
- Using wrong collection type (ArrayList for frequent inserts at beginning)
- Not handling empty collections
- Off-by-one errors in array/list access

### 7. Logical Errors

**Check for**:
- Comparison errors (using == instead of .equals() for objects)
- Boolean logic errors (incorrect negation, wrong operator)
- Incorrect loop conditions
- Missing break in switch statements (when intended)
- Unreachable code

**Example patterns to detect**:
```java
// BAD: String comparison with ==
if (status == "ACTIVE") { // Should use .equals()
    // Won't work as expected!
}

// GOOD: Proper string comparison
if ("ACTIVE".equals(status)) { // Null-safe
    // ...
}
```

## Output Format

Provide results in JSON format:

```json
{
  "review_type": "ERROR_DETECTION",
  "issues": [
    {
      "file": "src/main/java/com/example/service/UserService.java",
      "line": 45,
      "severity": "CRITICAL",
      "category": "NullPointerException Risk",
      "message": "Potential NullPointerException: dereferencing user.getName() without null check",
      "code_snippet": "String name = user.getName().toUpperCase();",
      "suggestion": "Add null check or use Optional: Optional.ofNullable(user.getName()).map(String::toUpperCase).orElse(\"UNKNOWN\")",
      "auto_fixable": true
    },
    {
      "file": "src/main/java/com/example/controller/OrderController.java",
      "line": 78,
      "severity": "HIGH",
      "category": "Exception Handling",
      "message": "Empty catch block swallows exception without logging",
      "code_snippet": "try { processOrder(order); } catch (Exception e) { }",
      "suggestion": "Add proper exception logging with stack trace and consider rethrowing or handling appropriately",
      "auto_fixable": false
    }
  ],
  "summary": {
    "total_issues": 2,
    "critical": 1,
    "high": 1,
    "medium": 0,
    "low": 0,
    "files_analyzed": 15
  }
}
```

## Severity Levels

- **CRITICAL**: Will cause runtime failures (NPE, ClassCastException, resource leaks)
- **HIGH**: Likely to cause issues under certain conditions (improper exception handling, type safety violations)
- **MEDIUM**: Code smell that could lead to bugs (missing null checks in non-critical paths)
- **LOW**: Minor issues that are unlikely to cause problems but should be addressed
- **INFO**: Suggestions for improvement without immediate risk

## Instructions

1. Clone the repository to {repo_path}
2. Checkout the merge request branch
3. Identify all changed files from {changed_files}
4. Analyze each file according to the rules above
5. Consider {custom_rules} if provided
6. Use {jira_context} to understand intended behavior
7. Generate comprehensive issue list with specific line numbers and suggestions
8. Prioritize auto-fixable issues
9. Output results in JSON format

## Important Notes

- Focus ONLY on changed files, not the entire codebase
- Consider the context of changes (refactoring, new features, bug fixes)
- Distinguish between intentional patterns and actual errors
- Provide actionable suggestions with code examples
- Mark issues as auto_fixable only if fix is straightforward and safe



