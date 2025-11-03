# Performance Rules for Java Spring Boot

## Overview

Rules for identifying performance issues and optimization opportunities in Java Spring Boot applications.

---

## Database Performance

### Rule 1: N+1 Query Detection

#### Severity: CRITICAL

#### Description
Detect N+1 query problem where lazy-loaded relationships cause multiple database queries.

#### Patterns to Detect

```java
// BAD: N+1 queries
@Service
public class OrderService {
    public List<OrderDto> getAllOrders() {
        List<Order> orders = orderRepository.findAll(); // 1 query
        return orders.stream()
            .map(order -> {
                List<Item> items = order.getItems(); // N queries! (lazy loading)
                return new OrderDto(order, items);
            })
            .collect(Collectors.toList());
    }
}
```

#### Correct Patterns

```java
// GOOD: JOIN FETCH
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    @Query("SELECT o FROM Order o LEFT JOIN FETCH o.items")
    List<Order> findAllWithItems();
}

// GOOD: @EntityGraph
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    @EntityGraph(attributePaths = {"items", "customer"})
    List<Order> findAll();
}

// GOOD: Batch fetching
@Entity
public class Order {
    @OneToMany(fetch = FetchType.LAZY)
    @BatchSize(size = 10) // Fetch 10 at a time instead of one by one
    private List<Item> items;
}
```

#### Auto-fix Capability: Yes (can suggest @EntityGraph)

---

### Rule 2: Missing Query Projections

#### Severity: MEDIUM

#### Description
Fetching full entities when only few fields are needed wastes memory and bandwidth.

#### Patterns to Detect

```java
// BAD: Loading full entity for just one field
@Service
public class UserService {
    public List<String> getAllUsernames() {
        return userRepository.findAll().stream()
            .map(User::getUsername)
            .collect(Collectors.toList());
    }
}
```

#### Correct Pattern

```java
// GOOD: Projection query
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    @Query("SELECT u.username FROM User u")
    List<String> findAllUsernames();
    
    // Or use projection interface
    interface UsernameOnly {
        String getUsername();
    }
    
    List<UsernameOnly> findAllProjectedBy();
}
```

#### Auto-fix Capability: Yes

---

### Rule 3: Inefficient Pagination

#### Severity: MEDIUM

#### Description
Missing pagination on large result sets causes memory issues.

#### Patterns to Detect

```java
// BAD: No pagination
@GetMapping("/users")
public List<User> getAllUsers() {
    return userRepository.findAll(); // Could be thousands of records!
}
```

#### Correct Pattern

```java
// GOOD: Paginated query
@GetMapping("/users")
public Page<UserDto> getAllUsers(
    @RequestParam(defaultValue = "0") int page,
    @RequestParam(defaultValue = "20") int size
) {
    Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());
    return userRepository.findAll(pageable)
        .map(UserDto::from);
}
```

#### Auto-fix Capability: Partial

---

### Rule 4: SELECT * Queries

#### Severity: LOW

#### Description
Avoid SELECT * when specific columns needed.

#### Patterns to Detect

```java
// BAD: Native query with SELECT *
@Query(value = "SELECT * FROM users WHERE status = ?1", nativeQuery = true)
List<User> findByStatus(String status);
```

#### Correct Pattern

```java
// GOOD: Specify columns
@Query(value = "SELECT id, username, email FROM users WHERE status = ?1", 
       nativeQuery = true)
List<UserProjection> findByStatus(String status);
```

---

## Caching

### Rule 5: Missing Caching for Expensive Operations

#### Severity: MEDIUM

#### Description
Cache results of expensive computations or frequently accessed data.

#### Patterns to Detect

```java
// BAD: Expensive operation without caching
@Service
public class ProductService {
    public List<Product> getFeaturedProducts() {
        // Complex query with multiple joins
        return productRepository.findFeaturedWithDetailsAndReviews();
    }
}
```

#### Correct Pattern

```java
// GOOD: Cached result
@Service
public class ProductService {
    @Cacheable(value = "featuredProducts", unless = "#result.isEmpty()")
    public List<Product> getFeaturedProducts() {
        return productRepository.findFeaturedWithDetailsAndReviews();
    }
    
    @CacheEvict(value = "featuredProducts", allEntries = true)
    public void updateFeaturedProducts() {
        // Update logic
    }
}

// Enable caching
@Configuration
@EnableCaching
public class CacheConfig {
    @Bean
    public CacheManager cacheManager() {
        return new ConcurrentMapCacheManager("featuredProducts");
    }
}
```

---

## Stream API

### Rule 6: Inefficient Stream Operations

#### Severity: LOW

#### Description
Optimize stream operation order and avoid unnecessary operations.

#### Patterns to Detect

```java
// BAD: map before filter (processes more elements)
list.stream()
    .map(User::getProfile) // Maps all users
    .filter(profile -> profile.isActive()) // Then filters
    .collect(Collectors.toList());

// BAD: Multiple iterations
list.stream().filter(x -> x > 0).count();
list.stream().filter(x -> x > 0).max(); // Iterates twice!
```

#### Correct Pattern

```java
// GOOD: filter before map
list.stream()
    .filter(user -> user.getProfile() != null)
    .filter(user -> user.getProfile().isActive())
    .map(User::getProfile)
    .collect(Collectors.toList());

// GOOD: Single iteration
IntSummaryStatistics stats = list.stream()
    .filter(x -> x > 0)
    .mapToInt(Integer::intValue)
    .summaryStatistics();
long count = stats.getCount();
int max = stats.getMax();
```

---

### Rule 7: Incorrect Parallel Stream Usage

#### Severity: MEDIUM

#### Description
Parallel streams have overhead; only use for CPU-intensive operations on large datasets.

#### Patterns to Detect

```java
// BAD: Parallel stream on small collection
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);
numbers.parallelStream() // Overhead > benefit for small list
    .map(n -> n * 2)
    .collect(Collectors.toList());

// BAD: Parallel stream with I/O operations
users.parallelStream() // I/O-bound, not CPU-bound
    .forEach(user -> externalApiClient.notify(user));
```

#### Correct Pattern

```java
// GOOD: Sequential for small collections
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);
numbers.stream()
    .map(n -> n * 2)
    .collect(Collectors.toList());

// GOOD: Parallel for CPU-intensive on large dataset
largeList.parallelStream() // 10,000+ elements, CPU-bound
    .filter(item -> complexCpuIntensiveCheck(item))
    .collect(Collectors.toList());

// GOOD: CompletableFuture for I/O operations
List<CompletableFuture<Void>> futures = users.stream()
    .map(user -> CompletableFuture.runAsync(() -> externalApiClient.notify(user)))
    .collect(Collectors.toList());
CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
```

---

## Connection Pooling

### Rule 8: Inadequate Connection Pool Configuration

#### Severity: HIGH

#### Description
Properly configure HikariCP connection pool for optimal performance.

#### Patterns to Detect

```properties
# BAD: Default settings for high-traffic application
spring.datasource.hikari.maximum-pool-size=10
spring.datasource.hikari.minimum-idle=10
# No connection timeout set
```

#### Correct Pattern

```properties
# GOOD: Tuned for production
# Formula: connections = ((core_count * 2) + effective_spindle_count)
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.idle-timeout=600000
spring.datasource.hikari.max-lifetime=1800000
spring.datasource.hikari.leak-detection-threshold=60000
```

---

## Reactive Programming

### Rule 9: Blocking Calls in Reactive Code

#### Severity: CRITICAL

#### Description
Never block in reactive pipelines; use proper reactive patterns.

#### Patterns to Detect

```java
// BAD: Blocking call in reactive pipeline
@Service
public class UserService {
    public Mono<User> getUser(Long id) {
        return Mono.fromCallable(() -> {
            return userRepository.findById(id).orElse(null); // Blocking JDBC!
        });
    }
}

// BAD: Thread.sleep in reactive
public Mono<String> delayedResponse() {
    return Mono.fromCallable(() -> {
        Thread.sleep(1000); // Blocks thread!
        return "response";
    });
}
```

#### Correct Pattern

```java
// GOOD: Use reactive repository
@Service
public class UserService {
    private final R2dbcUserRepository userRepository; // Reactive repository
    
    public Mono<User> getUser(Long id) {
        return userRepository.findById(id);
    }
}

// GOOD: Non-blocking delay
public Mono<String> delayedResponse() {
    return Mono.delay(Duration.ofSeconds(1))
        .thenReturn("response");
}

// If blocking unavoidable, use proper scheduler
public Mono<User> getUser(Long id) {
    return Mono.fromCallable(() -> blockingUserRepository.findById(id))
        .subscribeOn(Schedulers.boundedElastic()); // Dedicated scheduler for blocking
}
```

---

## Collection Operations

### Rule 10: Large Objects in Loops

#### Severity: MEDIUM

#### Description
Avoid creating large objects inside loops.

#### Patterns to Detect

```java
// BAD: Creating objects in loop
for (int i = 0; i < 1000; i++) {
    StringBuilder sb = new StringBuilder(); // New object each iteration
    sb.append("Value: ").append(i);
    results.add(sb.toString());
}
```

#### Correct Pattern

```java
// GOOD: Reuse StringBuilder
StringBuilder sb = new StringBuilder();
for (int i = 0; i < 1000; i++) {
    sb.setLength(0); // Reset
    sb.append("Value: ").append(i);
    results.add(sb.toString());
}
```

---

### Rule 11: String Concatenation in Loops

#### Severity: MEDIUM

#### Description
Use StringBuilder for string concatenation in loops.

#### Patterns to Detect

```java
// BAD: String concatenation in loop
String result = "";
for (String item : items) {
    result += item + ", "; // Creates new String object each iteration!
}
```

#### Correct Pattern

```java
// GOOD: StringBuilder
StringBuilder result = new StringBuilder();
for (String item : items) {
    result.append(item).append(", ");
}
return result.toString();

// BETTER: String.join or Collectors.joining
String result = String.join(", ", items);

// Or with streams
String result = items.stream().collect(Collectors.joining(", "));
```

---

## Summary

Total Rules: 11

### By Severity
- CRITICAL: 2 rules (18%)
- HIGH: 1 rule (9%)
- MEDIUM: 6 rules (55%)
- LOW: 2 rules (18%)

### By Category
- Database Performance: 4 rules
- Caching: 1 rule
- Stream API: 3 rules
- Connection Pooling: 1 rule
- Reactive Programming: 1 rule
- Collection Operations: 2 rules

### Auto-fix Capability
- Fully Auto-fixable: 3 rules (27%)
- Partially Auto-fixable: 2 rules (18%)
- Manual Fix Required: 6 rules (55%)

### Performance Impact
- **High Impact** (fix immediately): Rules 1, 8, 9
- **Medium Impact** (fix soon): Rules 2, 3, 5, 7
- **Low Impact** (optimize when convenient): Rules 4, 6, 10, 11


