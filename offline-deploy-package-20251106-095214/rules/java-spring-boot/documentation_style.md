# Documentation Style Guide for Java Spring Boot

## Overview

Standards for JavaDoc, inline comments, and documentation generation in Java Spring Boot projects.

---

## JavaDoc Standards

### Rule 1: Public API Documentation

**Requirement**: ALL public classes, methods, and constants MUST have JavaDoc.

**Minimum Structure**:
```java
/**
 * Brief one-line description ending with period.
 * 
 * <p>Optional detailed explanation in separate paragraph.
 * Can span multiple lines.</p>
 *
 * @param paramName parameter description
 * @return return value description
 * @throws ExceptionType when and why thrown
 */
```

---

### Rule 2: Class-Level JavaDoc

**Required Elements**:
- Purpose of the class
- When to use it
- Key responsibilities
- Usage example (for complex classes)
- Related classes (@see tags)

**Template**:
```java
/**
 * Brief description of what this class does.
 * 
 * <p>More detailed explanation of the class purpose,
 * responsibilities, and key behaviors.</p>
 *
 * <p>Example usage:</p>
 * <pre>{@code
 * MyClass instance = new MyClass();
 * instance.doSomething();
 * }</pre>
 *
 * @see RelatedClass
 * @since 1.0.0
 * @author AI Code Review (or team name)
 */
@Service
public class MyService {
    // ...
}
```

---

### Rule 3: Method JavaDoc

**Required Elements** (when applicable):
- What the method does (not how)
- Each @param with description and constraints
- @return with description (if not void)
- @throws for each checked exception
- Important side effects or state changes

**Good Example**:
```java
/**
 * Creates a new user account with the provided information.
 * 
 * <p>This method performs the following operations:</p>
 * <ul>
 *   <li>Validates user data (via @Valid annotation)</li>
 *   <li>Checks for duplicate username/email</li>
 *   <li>Hashes password using BCrypt</li>
 *   <li>Sets account status to PENDING</li>
 * </ul>
 *
 * @param request the user creation request containing username, email, and password.
 *                Must not be null. All fields are validated against constraints.
 * @return the created User entity with generated ID and timestamps.
 *         Password field will be hashed.
 * @throws DuplicateUserException if username or email already exists in the system
 * @throws ValidationException if request data fails validation constraints
 */
@Transactional
public User createUser(@Valid CreateUserRequest request) {
    // Implementation
}
```

---

### Rule 4: Parameter Documentation

**Format**: `@param name description`

**Guidelines**:
- Start with lowercase (unless proper noun)
- Describe what the parameter represents
- Include valid values or constraints
- Mention null-safety

**Examples**:
```java
/**
 * @param userId the unique identifier of the user. Must not be null or negative.
 * @param email the user's email address. Must be valid email format. Case-insensitive.
 * @param status the desired account status. Must be one of: ACTIVE, PENDING, SUSPENDED.
 * @param includeDeleted if true, includes soft-deleted records in results. Default: false.
 */
```

---

### Rule 5: Return Documentation

**Format**: `@return description`

**Guidelines**:
- Describe what is returned
- Mention possible null or Optional
- Describe empty collections behavior

**Examples**:
```java
/**
 * @return the found user, or throws UserNotFoundException if not found. Never returns null.
 */

/**
 * @return Optional containing the user if found, empty otherwise. Never returns null Optional.
 */

/**
 * @return list of active users. Returns empty list if no users match criteria. Never returns null.
 */

/**
 * @return the calculated total in USD. Always positive or zero. Never returns null.
 */
```

---

### Rule 6: Exception Documentation

**Format**: `@throws ExceptionType description of when thrown`

**Guidelines**:
- Document all checked exceptions
- Document unchecked exceptions if part of contract
- Explain the condition that triggers exception

**Examples**:
```java
/**
 * @throws UserNotFoundException if user with given ID does not exist in the database
 * @throws IllegalArgumentException if userId is null or negative
 * @throws DataAccessException if database error occurs during query execution
 */
```

---

### Rule 7: Record Documentation

**Special considerations** for Records (Java 16+):

```java
/**
 * Data transfer object for user creation requests.
 * 
 * <p>This record encapsulates all required information for creating
 * a new user account. All fields are validated using Bean Validation annotations.</p>
 *
 * <p>Validation rules:</p>
 * <ul>
 *   <li>Username: 3-50 characters, alphanumeric only</li>
 *   <li>Email: Valid email format</li>
 *   <li>Password: Minimum 8 characters, must contain letters and numbers</li>
 * </ul>
 *
 * @param username the desired username for the account. Must be unique in the system.
 * @param email the user's email address. Must be unique and valid format.
 * @param password the plaintext password. Will be hashed before storage. Never logged.
 */
public record CreateUserRequest(
    @NotBlank @Size(min = 3, max = 50) String username,
    @NotBlank @Email String email,
    @NotBlank @Size(min = 8) String password
) {}
```

---

### Rule 8: Controller Endpoint Documentation

**Required for all REST endpoints**:

```java
/**
 * Creates a new user account.
 * 
 * <p><b>Endpoint:</b> POST /api/users</p>
 * <p><b>Authentication:</b> Not required (public registration)</p>
 * <p><b>Rate Limit:</b> 10 requests per hour per IP address</p>
 * 
 * <p><b>Request Body Example:</b></p>
 * <pre>{@code
 * {
 *   "username": "johndoe",
 *   "email": "john@example.com",
 *   "password": "SecurePass123"
 * }
 * }</pre>
 *
 * <p><b>Response Codes:</b></p>
 * <ul>
 *   <li>201 Created - User successfully created</li>
 *   <li>400 Bad Request - Invalid request data or validation failure</li>
 *   <li>409 Conflict - Username or email already exists</li>
 *   <li>429 Too Many Requests - Rate limit exceeded</li>
 * </ul>
 *
 * @param request the validated user creation request
 * @return ResponseEntity with created user data (password excluded) and HTTP 201 status
 * @throws DuplicateUserException if username or email already taken
 */
@PostMapping
public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserRequest request) {
    // Implementation
}
```

---

## Inline Comments

### Rule 9: When to Use Inline Comments

**Use inline comments for**:
- Complex algorithms or business rules
- Non-obvious workarounds
- Performance optimizations
- Security considerations
- TODO items with context
- Regex explanations

**DON'T use inline comments for**:
- Obvious code (e.g., `// increment counter` before `count++`)
- Repeating what code does (describe WHY, not WHAT)
- Commented-out code (delete it, use git history)

---

### Rule 10: Inline Comment Style

**Format**:
```java
// Single line comment with proper capitalization and punctuation.

// Multi-line comment explaining
// complex logic across several
// lines with consistent formatting.
```

**Good Examples**:
```java
// WORKAROUND: Payment gateway times out after 30 seconds
// Split large transactions into multiple smaller ones
// See JIRA-1234 for details
if (order.getTotal().compareTo(LARGE_TRANSACTION_THRESHOLD) > 0) {
    processLargeTransaction(order);
    return;
}

// Performance: Use ConcurrentHashMap for thread-safe access
// with better performance than Collections.synchronizedMap()
private final Map<String, User> cache = new ConcurrentHashMap<>();

// Security: Constant-time comparison prevents timing attacks
if (MessageDigest.isEqual(expected, actual)) {
    // ...
}

// Regex explained: ^(?=.*[A-Z])(?=.*[a-z])(?=.*\\d)[A-Za-z\\d]{8,}$
// - At least one uppercase letter
// - At least one lowercase letter
// - At least one digit
// - Minimum 8 characters total
private static final String PASSWORD_PATTERN = "^(?=.*[A-Z])(?=.*[a-z])(?=.*\\d)[A-Za-z\\d]{8,}$";
```

**Bad Examples**:
```java
// BAD: Obvious
// Get user from repository
User user = userRepository.findById(id);

// BAD: Repeating code
// Loop through items
for (Item item : items) {
    // Process the item
    process(item);
}

// BAD: Commented-out code (delete it!)
// user.setOldField("value");
// processOldWay(user);
```

---

### Rule 11: TODO Comments

**Format**:
```java
// TODO(author): Brief description of what needs to be done
// Optionally add more context on next lines
// Reference: JIRA-123
```

**Example**:
```java
// TODO(john): Implement caching for frequently accessed users
// Currently each request hits database. Consider Redis or Caffeine cache.
// Needs performance testing before implementation.
// See JIRA-456 for performance analysis
public User findById(Long id) {
    return userRepository.findById(id).orElseThrow();
}
```

---

## Package Documentation

### Rule 12: package-info.java

**Requirement**: Create package-info.java for major packages (service, repository, controller, dto).

**Template**:
```java
/**
 * User management service layer.
 * 
 * <p>This package contains service classes for user account management,
 * authentication, authorization, and profile operations.</p>
 *
 * <p>Key classes:</p>
 * <ul>
 *   <li>{@link com.example.service.UserService} - Main user management service</li>
 *   <li>{@link com.example.service.AuthService} - Authentication operations</li>
 *   <li>{@link com.example.service.ProfileService} - User profile management</li>
 * </ul>
 *
 * <p>Service layer conventions:</p>
 * <ul>
 *   <li>All services use constructor injection</li>
 *   <li>Annotated with {@code @Service}</li>
 *   <li>Methods are transactional where appropriate</li>
 *   <li>Throw specific business exceptions, not generic ones</li>
 * </ul>
 *
 * @since 1.0.0
 */
package com.example.service;
```

---

## Auto-generated Documentation Tags

### Rule 13: Generation Metadata

**When AI generates documentation**, include:

```java
/**
 * ... documentation ...
 *
 * @author AI Code Review System
 * @generated 2025-11-03
 */
```

This helps track what was auto-generated vs manually written.

---

## Summary

### Mandatory Documentation
1. All public classes
2. All public methods
3. All public constants
4. All REST endpoints
5. Major packages (package-info.java)

### Optional Documentation
1. Private methods (if complex)
2. Protected methods in base classes
3. Configuration classes

### Comment Guidelines
- Use inline comments for WHY, not WHAT
- Document workarounds with context
- Explain complex business rules
- Reference JIRA tickets when relevant
- Never commit commented-out code

### Quality Checklist
- [ ] All public APIs documented
- [ ] All @param described with constraints
- [ ] All @return described with null-safety
- [ ] All @throws documented
- [ ] Example usage for complex classes
- [ ] REST endpoints include HTTP status codes
- [ ] Inline comments explain non-obvious logic
- [ ] TODOs include author and context


