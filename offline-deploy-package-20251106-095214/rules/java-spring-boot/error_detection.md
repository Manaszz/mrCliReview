# Error Detection Rules for Java Spring Boot

## Overview

Comprehensive rules for detecting bugs, potential crashes, and logical errors in Java Spring Boot applications.

---

## Rule 1: NullPointerException Prevention

### Severity: CRITICAL

### Description
Detect potential NullPointerException risks where values are dereferenced without null checks.

### Patterns to Detect

**Anti-pattern 1: Chained method calls without null checks**
```java
// BAD
String email = user.getProfile().getEmail().toLowerCase();
```

**Anti-pattern 2: Missing null checks at boundaries**
```java
// BAD
@RestController
public class UserController {
    @PostMapping("/users")
    public User create(@RequestBody UserDto dto) {
        return userService.create(dto.getName()); // No null check on dto.getName()
    }
}
```

**Anti-pattern 3: Unsafe Optional.get()**
```java
// BAD
Optional<User> userOpt = userRepository.findById(id);
return userOpt.get(); // Throws NoSuchElementException if empty
```

### Correct Patterns

```java
// GOOD: Null-safe with Optional
String email = Optional.ofNullable(user)
    .map(User::getProfile)
    .map(Profile::getEmail)
    .map(String::toLowerCase)
    .orElse("unknown@example.com");

// GOOD: Defensive null checks
if (dto == null || dto.getName() == null) {
    throw new IllegalArgumentException("Name is required");
}

// GOOD: Safe Optional usage
return userRepository.findById(id)
    .orElseThrow(() -> new UserNotFoundException(id));
```

### Auto-fix Capability: Partial
- Can add basic null checks
- Cannot infer correct default values or error messages

---

## Rule 2: Exception Handling

### Severity: HIGH

### Description
Detect improper exception handling that swallows errors or loses information.

### Patterns to Detect

**Anti-pattern 1: Empty catch blocks**
```java
// BAD
try {
    processPayment(order);
} catch (PaymentException e) {
    // Silent failure!
}
```

**Anti-pattern 2: Catching generic Exception**
```java
// BAD
try {
    processOrder(order);
} catch (Exception e) {
    log.error("Error processing order");
    return false;
}
```

**Anti-pattern 3: Missing stack trace in logs**
```java
// BAD
catch (PaymentException e) {
    log.error("Payment failed: {}", e.getMessage()); // No stack trace!
}
```

### Correct Patterns

```java
// GOOD: Proper logging with stack trace
try {
    processPayment(order);
} catch (PaymentException e) {
    log.error("Payment processing failed for order {}: {}", 
              order.getId(), e.getMessage(), e); // Include exception
    throw new OrderProcessingException("Failed to process payment", e);
}

// GOOD: Specific exception handling
try {
    processOrder(order);
} catch (PaymentException e) {
    // Handle payment specific
} catch (InventoryException e) {
    // Handle inventory specific
}
```

### Auto-fix Capability: Yes
- Can add logging statements
- Can add proper exception chaining

---

## Rule 3: Resource Management

### Severity: CRITICAL

### Description
Ensure resources (streams, connections, files) are properly closed using try-with-resources.

### Patterns to Detect

**Anti-pattern: Manual resource closing**
```java
// BAD
public String readFile(String path) throws IOException {
    FileReader reader = new FileReader(path);
    BufferedReader buffered = new BufferedReader(reader);
    // ... reading
    buffered.close(); // Won't execute if exception thrown!
}
```

### Correct Patterns

```java
// GOOD: Try-with-resources
public String readFile(String path) throws IOException {
    try (BufferedReader reader = new BufferedReader(new FileReader(path))) {
        return reader.lines().collect(Collectors.joining("\n"));
    }
}

// GOOD: Multiple resources
try (Connection conn = dataSource.getConnection();
     PreparedStatement stmt = conn.prepareStatement(sql);
     ResultSet rs = stmt.executeQuery()) {
    // Use resources
}
```

### Auto-fix Capability: Yes
- Can convert to try-with-resources pattern

---

## Rule 4: Type Safety

### Severity: HIGH

### Description
Prevent ClassCastException and enforce proper generic types.

### Patterns to Detect

**Anti-pattern 1: Unchecked casts**
```java
// BAD
public User getUser(Object obj) {
    return (User) obj; // No instanceof check!
}
```

**Anti-pattern 2: Raw types**
```java
// BAD
List users = new ArrayList(); // Should be List<User>
Map config = new HashMap(); // Should be Map<String, String>
```

### Correct Patterns

```java
// GOOD: instanceof before cast
public User getUser(Object obj) {
    if (!(obj instanceof User)) {
        throw new IllegalArgumentException("Object is not a User");
    }
    return (User) obj;
}

// GOOD: Pattern matching (Java 17+)
public User getUser(Object obj) {
    if (obj instanceof User user) {
        return user;
    }
    throw new IllegalArgumentException("Object is not a User");
}

// GOOD: Proper generics
List<User> users = new ArrayList<>();
Map<String, String> config = new HashMap<>();
```

### Auto-fix Capability: Yes
- Can add generic type parameters
- Can add instanceof checks

---

## Rule 5: String Comparison

### Severity: MEDIUM

### Description
Use .equals() for string comparison, not ==.

### Patterns to Detect

```java
// BAD
if (status == "ACTIVE") {
    // ...
}

if (user.getName() == "Admin") {
    // ...
}
```

### Correct Patterns

```java
// GOOD: Use equals (constant first for null safety)
if ("ACTIVE".equals(status)) {
    // ...
}

// GOOD: Use Objects.equals for potential nulls
if (Objects.equals(user.getName(), "Admin")) {
    // ...
}
```

### Auto-fix Capability: Yes
- Can replace == with .equals()

---

## Rule 6: Collection Access Safety

### Severity: MEDIUM

### Description
Check collection size before accessing elements.

### Patterns to Detect

```java
// BAD
List<String> items = getItems();
String first = items.get(0); // IndexOutOfBoundsException if empty!

// BAD: Modifying while iterating
for (String item : items) {
    if (item.isEmpty()) {
        items.remove(item); // ConcurrentModificationException!
    }
}
```

### Correct Patterns

```java
// GOOD: Check before access
List<String> items = getItems();
if (!items.isEmpty()) {
    String first = items.get(0);
}

// GOOD: Use iterator for removal
Iterator<String> it = items.iterator();
while (it.hasNext()) {
    String item = it.next();
    if (item.isEmpty()) {
        it.remove();
    }
}

// GOOD: Stream API
items = items.stream()
    .filter(item -> !item.isEmpty())
    .collect(Collectors.toList());
```

### Auto-fix Capability: Partial
- Can add size checks
- Cannot automatically convert to iterator pattern

---

## Rule 7: Unreachable Code

### Severity: LOW

### Description
Detect code that can never be executed.

### Patterns to Detect

```java
// BAD
public void process() {
    return;
    log.info("Processing complete"); // Unreachable!
}

// BAD
if (true) {
    return "always";
} else {
    return "never"; // Unreachable!
}
```

### Auto-fix Capability: Yes
- Can remove unreachable code

---

## Rule 8: Boolean Logic Errors

### Severity: MEDIUM

### Description
Detect incorrect boolean conditions and unnecessary comparisons.

### Patterns to Detect

```java
// BAD
if (isActive == true) { } // Redundant comparison

// BAD
if (isActive() == false) { } // Use !isActive()

// BAD
return condition ? true : false; // Just return condition
```

### Correct Patterns

```java
// GOOD
if (isActive) { }
if (!isActive()) { }
return condition;
```

### Auto-fix Capability: Yes
- Can simplify boolean expressions

---

## Rule 9: Switch Statement Completeness

### Severity: MEDIUM

### Description
Ensure switch statements handle all cases or have a default.

### Patterns to Detect

```java
// BAD: Missing default
switch (status) {
    case PENDING:
        process();
        break;
    case ACTIVE:
        activate();
        break;
    // No default case!
}
```

### Correct Patterns

```java
// GOOD: With default
switch (status) {
    case PENDING:
        process();
        break;
    case ACTIVE:
        activate();
        break;
    default:
        throw new IllegalStateException("Unexpected status: " + status);
}

// GOOD: Switch expression (Java 14+)
String result = switch (status) {
    case PENDING -> "Processing";
    case ACTIVE -> "Active";
    case CLOSED -> "Closed";
    // Compiler ensures all enum values are covered
};
```

### Auto-fix Capability: Partial
- Can add default case
- Cannot infer correct default behavior

---

## Rule 10: Method Return Consistency

### Severity: MEDIUM

### Description
Ensure all code paths return a value (when required).

### Patterns to Detect

```java
// BAD
public String getStatus(Order order) {
    if (order.isPaid()) {
        return "PAID";
    } else if (order.isShipped()) {
        return "SHIPPED";
    }
    // Missing return for other cases!
}
```

### Correct Patterns

```java
// GOOD
public String getStatus(Order order) {
    if (order.isPaid()) {
        return "PAID";
    } else if (order.isShipped()) {
        return "SHIPPED";
    }
    return "PENDING";
}
```

### Auto-fix Capability: No
- Requires understanding of business logic

---

## Summary

Total Rules: 10

Auto-fixable: 6 (60%)
Partially Auto-fixable: 2 (20%)
Manual Fix Required: 2 (20%)

### Critical Rules
1. NullPointerException Prevention
2. Resource Management

### High Priority Rules
3. Exception Handling
4. Type Safety

### Medium Priority Rules
5. String Comparison
6. Collection Access Safety
7. Boolean Logic Errors
8. Switch Statement Completeness
9. Method Return Consistency

### Low Priority Rules
10. Unreachable Code
