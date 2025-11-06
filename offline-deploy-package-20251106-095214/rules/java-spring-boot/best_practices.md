# Best Practices Rules for Java Spring Boot

## Overview

Rules for enforcing SOLID principles, Spring Boot conventions, DRY, KISS, and modern Java features.

---

## SOLID Principles

### Rule 1: Single Responsibility Principle (SRP)

#### Severity: HIGH

#### Description
Each class should have one, and only one, reason to change.

#### Patterns to Detect

**Anti-pattern 1: Business logic in controllers**
```java
// BAD: Controller doing too much
@RestController
public class OrderController {
    @Autowired
    private OrderRepository orderRepository;
    
    @PostMapping("/orders")
    public Order createOrder(@RequestBody OrderDto dto) {
        // Validation - should be in DTO with @Valid
        if (dto.getItems().isEmpty()) {
            throw new IllegalArgumentException("No items");
        }
        
        // Business logic - should be in service
        Order order = new Order();
        order.setItems(dto.getItems());
        order.setTotal(calculateTotal(dto.getItems()));
        
        // Data access - should use service
        return orderRepository.save(order);
    }
}
```

#### Correct Pattern

```java
// GOOD: Proper separation
@RestController
@RequiredArgsConstructor
public class OrderController {
    private final OrderService orderService;
    
    @PostMapping("/orders")
    public OrderDto createOrder(@Valid @RequestBody CreateOrderRequest request) {
        Order order = orderService.createOrder(request);
        return OrderDto.from(order);
    }
}

@Service
@RequiredArgsConstructor
public class OrderService {
    private final OrderRepository orderRepository;
    
    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        // Business logic here
    }
}
```

#### Auto-fix Capability: No

---

### Rule 2: Dependency Inversion Principle (DIP)

#### Severity: HIGH

#### Description
Depend on abstractions, not concrete implementations.

#### Patterns to Detect

```java
// BAD: Depending on concrete implementation
@Service
public class OrderService {
    private final EmailNotificationService emailService; // Concrete class
    
    public void processOrder(Order order) {
        emailService.sendEmail(...); // Tight coupling
    }
}
```

#### Correct Pattern

```java
// GOOD: Depend on interface
public interface NotificationService {
    void sendNotification(String to, String message);
}

@Service
public class OrderService {
    private final NotificationService notificationService; // Interface
    
    public void processOrder(Order order) {
        notificationService.sendNotification(...);
    }
}

@Service
public class EmailNotificationService implements NotificationService {
    @Override
    public void sendNotification(String to, String message) {
        // Implementation
    }
}
```

#### Auto-fix Capability: No

---

## Spring Boot Conventions

### Rule 3: Constructor Injection over Field Injection

#### Severity: MEDIUM

#### Description
Use constructor injection for better testability and immutability.

#### Patterns to Detect

```java
// BAD: Field injection
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private EmailService emailService;
}
```

#### Correct Pattern

```java
// GOOD: Constructor injection with Lombok
@Service
@RequiredArgsConstructor
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
}

// GOOD: Manual constructor (if no Lombok)
@Service
public class UserService {
    private final UserRepository userRepository;
    private final EmailService emailService;
    
    public UserService(UserRepository userRepository, EmailService emailService) {
        this.userRepository = userRepository;
        this.emailService = emailService;
    }
}
```

#### Auto-fix Capability: Yes

---

### Rule 4: @Transactional Placement

#### Severity: HIGH

#### Description
Place @Transactional on service methods, not repository methods.

#### Patterns to Detect

```java
// BAD: @Transactional on repository
public interface UserRepository extends JpaRepository<User, Long> {
    @Transactional
    Optional<User> findByEmail(String email);
}

// BAD: @Transactional on private method (won't work!)
@Service
public class UserService {
    @Transactional
    private void updateUser(User user) {
        // Won't be transactional!
    }
}
```

#### Correct Pattern

```java
// GOOD: @Transactional on service
@Service
public class UserService {
    @Transactional(readOnly = true)
    public User findByEmail(String email) {
        return userRepository.findByEmail(email)
            .orElseThrow(() -> new UserNotFoundException(email));
    }
    
    @Transactional
    public User updateUser(Long id, UserDto dto) {
        // Transactional update
    }
}
```

#### Auto-fix Capability: Partial

---

### Rule 5: Return DTOs from Controllers, Not Entities

#### Severity: MEDIUM

#### Description
Controllers should return DTOs, not JPA entities directly.

#### Patterns to Detect

```java
// BAD: Exposing entity
@RestController
public class UserController {
    @GetMapping("/users/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id); // Exposes entity!
    }
}
```

#### Correct Pattern

```java
// GOOD: Return DTO
@RestController
public class UserController {
    @GetMapping("/users/{id}")
    public UserDto getUser(@PathVariable Long id) {
        User user = userService.findById(id);
        return UserDto.from(user);
    }
}

public record UserDto(Long id, String username, String email) {
    public static UserDto from(User user) {
        return new UserDto(user.getId(), user.getUsername(), user.getEmail());
    }
}
```

#### Auto-fix Capability: No

---

## DRY (Don't Repeat Yourself)

### Rule 6: Duplicate Code Detection

#### Severity: MEDIUM

#### Description
Identify and eliminate code duplication.

#### Patterns to Detect

```java
// BAD: Duplicate validation
public void createUser(UserDto dto) {
    if (dto.getEmail() == null || !dto.getEmail().contains("@")) {
        throw new ValidationException("Invalid email");
    }
    // ...
}

public void updateUser(Long id, UserDto dto) {
    if (dto.getEmail() == null || !dto.getEmail().contains("@")) { // Duplicate!
        throw new ValidationException("Invalid email");
    }
    // ...
}
```

#### Correct Pattern

```java
// GOOD: Bean Validation
public record UserDto(
    @NotBlank
    @Email
    String email,
    
    @NotBlank
    @Size(min = 3, max = 50)
    String username
) {}

// Now just use @Valid
public void createUser(@Valid UserDto dto) {
    // Validation automatic
}
```

#### Auto-fix Capability: Partial

---

## KISS (Keep It Simple)

### Rule 7: Method Complexity

#### Severity: MEDIUM

#### Description
Methods should be concise (<50 lines) and have low cyclomatic complexity (<10).

#### Patterns to Detect

```java
// BAD: Long method with high complexity
public void processOrder(Order order) {
    // 80+ lines of code
    // Multiple nested ifs
    // Complex logic
}
```

#### Correct Pattern

```java
// GOOD: Split into smaller methods
public void processOrder(Order order) {
    validateOrder(order);
    calculateTotals(order);
    applyDiscounts(order);
    processPayment(order);
    sendConfirmation(order);
}

private void validateOrder(Order order) {
    // Validation logic
}

private void calculateTotals(Order order) {
    // Calculation logic
}
```

#### Auto-fix Capability: No

---

### Rule 8: Deep Nesting

#### Severity: MEDIUM

#### Description
Avoid nesting deeper than 3 levels. Use guard clauses and early returns.

#### Patterns to Detect

```java
// BAD: Deep nesting
public void process(Order order) {
    if (order != null) {
        if (order.getUser() != null) {
            if (order.getUser().isActive()) {
                if (order.getTotal() != null) {
                    // Finally process!
                }
            }
        }
    }
}
```

#### Correct Pattern

```java
// GOOD: Guard clauses
public void process(Order order) {
    if (order == null) return;
    if (order.getUser() == null) return;
    if (!order.getUser().isActive()) return;
    if (order.getTotal() == null) return;
    
    // Process order
}
```

#### Auto-fix Capability: Yes

---

### Rule 9: Complex Boolean Expressions

#### Severity: LOW

#### Description
Extract complex boolean expressions to well-named methods.

#### Patterns to Detect

```java
// BAD: Unreadable condition
if ((user.isActive() && !user.isLocked() && user.getRole() != Role.GUEST) ||
    (user.isAdmin() && user.getLastLogin().isAfter(LocalDateTime.now().minusDays(1)))) {
    // ...
}
```

#### Correct Pattern

```java
// GOOD: Extracted to readable methods
if (isEligibleUser(user) || isRecentAdmin(user)) {
    // ...
}

private boolean isEligibleUser(User user) {
    return user.isActive() && !user.isLocked() && user.getRole() != Role.GUEST;
}

private boolean isRecentAdmin(User user) {
    return user.isAdmin() && 
           user.getLastLogin().isAfter(LocalDateTime.now().minusDays(1));
}
```

#### Auto-fix Capability: No

---

### Rule 10: Magic Numbers

#### Severity: LOW

#### Description
Replace magic numbers with named constants.

#### Patterns to Detect

```java
// BAD: Magic numbers
if (user.getAge() > 18 && user.getCredits() < 1000) {
    discount = price * 0.15;
}
```

#### Correct Pattern

```java
// GOOD: Named constants
private static final int MINIMUM_AGE = 18;
private static final int CREDIT_LIMIT = 1000;
private static final double DISCOUNT_RATE = 0.15;

if (user.getAge() > MINIMUM_AGE && user.getCredits() < CREDIT_LIMIT) {
    discount = price * DISCOUNT_RATE;
}
```

#### Auto-fix Capability: Yes

---

## Modern Java Features

### Rule 11: Use Records for DTOs

#### Severity: MEDIUM

#### Description
Convert immutable data classes to Records (Java 16+).

#### Patterns to Detect

```java
// BAD: Traditional POJO for DTO
public class UserDto {
    private final String username;
    private final String email;
    
    public UserDto(String username, String email) {
        this.username = username;
        this.email = email;
    }
    
    public String getUsername() { return username; }
    public String getEmail() { return email; }
    
    // equals, hashCode, toString...
}
```

#### Correct Pattern

```java
// GOOD: Record
public record UserDto(String username, String email) {
    // Compact constructor for validation
    public UserDto {
        if (username == null || username.isBlank()) {
            throw new IllegalArgumentException("Username required");
        }
    }
}
```

#### Auto-fix Capability: Yes

---

### Rule 12: Pattern Matching for instanceof

#### Severity: LOW

#### Description
Use pattern matching for instanceof (Java 17+).

#### Patterns to Detect

```java
// BAD: Old style
if (obj instanceof String) {
    String str = (String) obj;
    return str.length();
}
```

#### Correct Pattern

```java
// GOOD: Pattern matching
if (obj instanceof String str) {
    return str.length();
}
```

#### Auto-fix Capability: Yes

---

## Summary

Total Rules: 12

### By Category
- SOLID Principles: 2
- Spring Boot Conventions: 3
- DRY: 1
- KISS: 4
- Modern Java: 2

### By Severity
- HIGH: 4 rules
- MEDIUM: 7 rules
- LOW: 3 rules

### Auto-fix Capability
- Fully Auto-fixable: 5 rules (42%)
- Partially Auto-fixable: 2 rules (17%)
- Manual Fix Required: 5 rules (42%)


