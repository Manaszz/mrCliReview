# Refactoring Suggestions Prompt for Cline CLI

## Objective

Analyze Java Spring Boot code changes and suggest refactoring opportunities to improve code maintainability, readability, and design quality.


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

### 1. Circular Dependencies

**Check for**:
- Beans depending on each other directly or transitively
- Service A → Service B → Service A cycles
- Package-level circular dependencies

**Example patterns**:
```java
// BAD: Circular dependency
@Service
public class UserService {
    @Autowired
    private OrderService orderService; // UserService depends on OrderService
    
    public void processUser(User user) {
        orderService.processUserOrders(user);
    }
}

@Service
public class OrderService {
    @Autowired
    private UserService userService; // OrderService depends on UserService - CIRCULAR!
    
    public void processOrder(Order order) {
        User user = userService.getUser(order.getUserId());
    }
}

// GOOD: Break cycle with event-driven approach
@Service
public class UserService {
    private final ApplicationEventPublisher eventPublisher;
    
    public void processUser(User user) {
        eventPublisher.publishEvent(new UserProcessedEvent(user));
    }
}

@Service
public class OrderService {
    @EventListener
    public void onUserProcessed(UserProcessedEvent event) {
        processUserOrders(event.getUser());
    }
}
```

### 2. Business Logic in Controllers

**Check for**:
- Controllers performing data validation
- Controllers containing business logic
- Controllers directly accessing repositories
- Controllers constructing domain objects

**Example patterns**:
```java
// BAD: Business logic in controller
@RestController
@RequestMapping("/orders")
public class OrderController {
    @Autowired
    private OrderRepository orderRepository;
    @Autowired
    private UserRepository userRepository;
    @Autowired
    private EmailService emailService;
    
    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody OrderDto dto) {
        // Validation in controller - BAD!
        if (dto.getItems() == null || dto.getItems().isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        
        // Business logic in controller - BAD!
        User user = userRepository.findById(dto.getUserId())
            .orElseThrow(() -> new UserNotFoundException());
            
        Order order = new Order();
        order.setUser(user);
        order.setItems(dto.getItems());
        order.setTotal(calculateTotal(dto.getItems())); // Business logic!
        order.setStatus(OrderStatus.PENDING);
        order.setCreatedAt(LocalDateTime.now());
        
        Order saved = orderRepository.save(order);
        
        // More business logic - BAD!
        emailService.sendOrderConfirmation(saved);
        
        return ResponseEntity.ok(saved);
    }
    
    private BigDecimal calculateTotal(List<OrderItem> items) {
        // Complex calculation logic in controller!
        return items.stream()
            .map(item -> item.getPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}

// GOOD: Controller delegates to service
@RestController
@RequestMapping("/orders")
@RequiredArgsConstructor
public class OrderController {
    private final OrderService orderService;
    
    @PostMapping
    public ResponseEntity<OrderDto> createOrder(@Valid @RequestBody CreateOrderRequest request) {
        Order order = orderService.createOrder(request);
        return ResponseEntity.ok(OrderDto.from(order));
    }
}

@Service
@RequiredArgsConstructor
public class OrderService {
    private final OrderRepository orderRepository;
    private final UserRepository userRepository;
    private final EmailService emailService;
    
    @Transactional
    public Order createOrder(CreateOrderRequest request) {
        User user = userRepository.findById(request.getUserId())
            .orElseThrow(() -> new UserNotFoundException(request.getUserId()));
            
        Order order = Order.builder()
            .user(user)
            .items(request.getItems())
            .total(calculateTotal(request.getItems()))
            .status(OrderStatus.PENDING)
            .createdAt(LocalDateTime.now())
            .build();
            
        Order saved = orderRepository.save(order);
        emailService.sendOrderConfirmation(saved);
        
        return saved;
    }
    
    private BigDecimal calculateTotal(List<OrderItem> items) {
        return items.stream()
            .map(item -> item.getPrice().multiply(BigDecimal.valueOf(item.getQuantity())))
            .reduce(BigDecimal.ZERO, BigDecimal::add);
    }
}
```

### 3. Code Smells

#### Long Methods
**Check for**: Methods longer than 50 lines

**Refactoring**: Extract method

#### Deep Nesting
**Check for**: Nesting depth > 3 levels

**Refactoring**: Extract method, early return, guard clauses

**Example patterns**:
```java
// BAD: Deep nesting
public void processOrder(Order order) {
    if (order != null) {
        if (order.getUser() != null) {
            if (order.getUser().isActive()) {
                if (order.getTotal().compareTo(BigDecimal.ZERO) > 0) {
                    // Process order
                }
            }
        }
    }
}

// GOOD: Guard clauses with early return
public void processOrder(Order order) {
    if (order == null) return;
    if (order.getUser() == null) return;
    if (!order.getUser().isActive()) return;
    if (order.getTotal().compareTo(BigDecimal.ZERO) <= 0) return;
    
    // Process order
}
```

#### Duplicate Code
**Check for**: Similar code blocks in multiple places

**Refactoring**: Extract to common method, use template method pattern

#### Large Classes
**Check for**: Classes with too many responsibilities (>500 lines)

**Refactoring**: Split by responsibility

#### Long Parameter Lists
**Check for**: Methods with >3 parameters

**Refactoring**: Introduce parameter object, use Builder pattern

**Example patterns**:
```java
// BAD: Long parameter list
public Order createOrder(String userId, List<Item> items, 
                        String shippingAddress, String billingAddress,
                        PaymentMethod paymentMethod, String couponCode,
                        boolean giftWrap, String giftMessage) {
    // ...
}

// GOOD: Parameter object
public record CreateOrderRequest(
    String userId,
    List<Item> items,
    Address shippingAddress,
    Address billingAddress,
    PaymentMethod paymentMethod,
    Optional<String> couponCode,
    GiftOptions giftOptions
) {}

public Order createOrder(CreateOrderRequest request) {
    // ...
}
```

#### Magic Numbers
**Check for**: Hardcoded numbers without explanation

**Refactoring**: Extract to named constants

**Example patterns**:
```java
// BAD: Magic numbers
if (user.getAge() > 18 && user.getCredits() < 1000) {
    // ...
}

// GOOD: Named constants
private static final int MINIMUM_AGE = 18;
private static final int CREDIT_LIMIT = 1000;

if (user.getAge() > MINIMUM_AGE && user.getCredits() < CREDIT_LIMIT) {
    // ...
}
```

### 4. Blocking Calls in Reactive Code

**Check for**:
- Blocking I/O operations in reactive pipelines
- Thread.sleep() in reactive code
- Synchronous database calls in WebFlux
- Blocking HTTP clients in reactive context

**Example patterns**:
```java
// BAD: Blocking call in reactive pipeline
@Service
public class UserService {
    public Mono<User> getUser(Long id) {
        return Mono.fromCallable(() -> {
            // Blocking JDBC call in reactive context - BAD!
            return userRepository.findById(id).orElse(null);
        });
    }
}

// GOOD: Use reactive repository
@Service
public class UserService {
    private final R2dbcUserRepository userRepository;
    
    public Mono<User> getUser(Long id) {
        return userRepository.findById(id);
    }
}

// If blocking is unavoidable, use proper scheduler
public Mono<User> getUser(Long id) {
    return Mono.fromCallable(() -> blockingUserRepository.findById(id))
        .subscribeOn(Schedulers.boundedElastic()); // Dedicated scheduler for blocking
}
```

### 5. Complex Boolean Expressions

**Check for**:
- Multiple conditions combined with && and ||
- Negations making logic hard to follow
- Boolean flags controlling method behavior

**Refactoring**: Extract to well-named boolean methods

**Example patterns**:
```java
// BAD: Complex boolean expression
if ((user.isActive() && !user.isLocked() && user.getRole() != Role.GUEST) ||
    (user.isAdmin() && user.getLastLogin().isAfter(LocalDateTime.now().minusDays(1)))) {
    // ...
}

// GOOD: Extract to readable methods
if (isEligibleRegularUser(user) || isRecentAdmin(user)) {
    // ...
}

private boolean isEligibleRegularUser(User user) {
    return user.isActive() && 
           !user.isLocked() && 
           user.getRole() != Role.GUEST;
}

private boolean isRecentAdmin(User user) {
    return user.isAdmin() && 
           user.getLastLogin().isAfter(LocalDateTime.now().minusDays(1));
}
```

### 6. God Objects / Utility Classes

**Check for**:
- Classes with too many unrelated methods
- Static utility classes that could be services
- Classes named "Manager", "Helper", "Utility" doing multiple things

**Refactoring**: Split by responsibility, convert to services with DI

### 7. Anemic Domain Model

**Check for**:
- Entity classes with only getters/setters
- All business logic in services
- Domain objects as data containers only

**Refactoring**: Move behavior into domain objects

**Example patterns**:
```java
// BAD: Anemic domain model
@Entity
public class Order {
    private Long id;
    private BigDecimal total;
    private OrderStatus status;
    // Only getters and setters
}

@Service
public class OrderService {
    public void cancelOrder(Order order) {
        order.setStatus(OrderStatus.CANCELLED);
        order.setCancelledAt(LocalDateTime.now());
        // Business logic in service
    }
}

// GOOD: Rich domain model
@Entity
public class Order {
    private Long id;
    private BigDecimal total;
    private OrderStatus status;
    private LocalDateTime cancelledAt;
    
    public void cancel() {
        if (status == OrderStatus.SHIPPED) {
            throw new IllegalStateException("Cannot cancel shipped order");
        }
        this.status = OrderStatus.CANCELLED;
        this.cancelledAt = LocalDateTime.now();
    }
    
    public boolean canBeCancelled() {
        return status != OrderStatus.SHIPPED && 
               status != OrderStatus.DELIVERED;
    }
}

@Service
public class OrderService {
    @Transactional
    public void cancelOrder(Long orderId) {
        Order order = orderRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));
        order.cancel(); // Business logic in domain object
        orderRepository.save(order);
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

### Required JSON Structure

```json
{
  "review_type": "REFACTORING",
  "suggestions": [
    {
      "file": "src/main/java/com/example/controller/OrderController.java",
      "line": 25,
      "severity": "HIGH",
      "category": "Circular Dependency",
      "message": "Circular dependency detected between OrderService and UserService",
      "code_snippet": "@Autowired private UserService userService;",
      "suggestion": "Break circular dependency using event-driven approach or introduce intermediate service",
      "impact": "SIGNIFICANT",
      "effort": "MEDIUM",
      "auto_fixable": false
    },
    {
      "file": "src/main/java/com/example/service/OrderService.java",
      "line": 45,
      "severity": "MEDIUM",
      "category": "Long Method",
      "message": "Method processOrder() is 78 lines long, should be split",
      "code_snippet": "public void processOrder(Order order) { ... }",
      "suggestion": "Extract methods: validateOrder(), calculateTotal(), sendNotifications()",
      "impact": "MINOR",
      "effort": "LOW",
      "auto_fixable": false
    },
    {
      "file": "src/main/java/com/example/controller/UserController.java",
      "line": 33,
      "severity": "HIGH",
      "category": "Business Logic in Controller",
      "message": "Controller contains business logic that should be in service layer",
      "code_snippet": "BigDecimal total = items.stream()...reduce(...);",
      "suggestion": "Move all business logic to UserService. Controller should only handle HTTP concerns.",
      "impact": "SIGNIFICANT",
      "effort": "MEDIUM",
      "auto_fixable": false
    }
  ],
  "summary": {
    "total_suggestions": 3,
    "significant_refactorings": 2,
    "minor_refactorings": 1,
    "estimated_effort_hours": 4,
    "files_analyzed": 18
  },
  "classification": "SIGNIFICANT"
}
```

## Refactoring Classification

### SIGNIFICANT (Separate MR required)
- More than 3 classes affected
- Breaking changes to public APIs
- More than 200 lines of code changed
- Dependency injection structure modifications
- Pattern migrations (e.g., callback hell to CompletableFuture)
- Architectural changes

### MINOR (Can be combined with fixes)
- Variable/method renames
- Constant extraction
- Code formatting
- Conditional simplification
- Local refactoring within single method
- Comment improvements


**Validation**: Your output will be validated against `schemas/review_result_schema.json`

## Severity Levels

- **CRITICAL**: Severe design flaw blocking maintainability
- **HIGH**: Important refactoring improving code quality significantly
- **MEDIUM**: Useful improvement worth addressing
- **LOW**: Nice-to-have improvement
- **INFO**: Suggestion for potential future enhancement

## Instructions

1. Focus on changed code and its immediate context
2. Consider project architecture in {custom_rules}
3. Use {jira_context} to understand if patterns are intentional workarounds
4. Classify each refactoring as SIGNIFICANT or MINOR
5. Provide clear before/after examples
6. Estimate effort (LOW/MEDIUM/HIGH)
7. Output structured suggestions in JSON format
8. Include overall classification for all suggestions combined



