# Security Rules for Java Spring Boot

## Overview

Comprehensive security rules to prevent vulnerabilities and enforce secure coding practices.

---

## Rule 1: SQL Injection Prevention

### Severity: CRITICAL

### Description
Never concatenate user input into SQL queries. Always use parameterized queries.

### Patterns to Detect

```java
// CRITICAL: SQL Injection vulnerability
@Repository
public class UserRepository {
    @Autowired
    private JdbcTemplate jdbc;
    
    public User findByUsername(String username) {
        String sql = "SELECT * FROM users WHERE username = '" + username + "'";
        // Attack: username = "admin' OR '1'='1"
        return jdbc.queryForObject(sql, new UserRowMapper());
    }
}
```

### Correct Pattern

```java
// GOOD: Parameterized query
public User findByUsername(String username) {
    String sql = "SELECT * FROM users WHERE username = ?";
    return jdbc.queryForObject(sql, new UserRowMapper(), username);
}

// GOOD: JPA repository (safe by default)
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByUsername(String username);
}

// GOOD: JPQL with named parameters
@Query("SELECT u FROM User u WHERE u.username = :username")
Optional<User> findByUsername(@Param("username") String username);
```

### Auto-fix Capability: Yes

---

## Rule 2: XSS Prevention

### Severity: CRITICAL

### Description
Always encode user input before outputting in HTML. Use appropriate escaping.

### Patterns to Detect

```java
// BAD: Unencoded output in Thymeleaf
<div th:utext="${userInput}"></div> // XSS if userInput contains <script>

// BAD: Direct output in JSP
<div><%= request.getParameter("name") %></div>
```

### Correct Pattern

```html
<!-- GOOD: Thymeleaf auto-escapes by default -->
<div th:text="${userInput}"></div>

<!-- GOOD: Explicit encoding -->
<div th:text="${@encoder.encodeForHTML(userInput)}"></div>
```

```java
// GOOD: Use OWASP Encoder
import org.owasp.encoder.Encode;

@Controller
public class ProfileController {
    @GetMapping("/profile")
    public String showProfile(@RequestParam String name, Model model) {
        String safeName = Encode.forHtml(name);
        model.addAttribute("username", safeName);
        return "profile";
    }
}
```

### Auto-fix Capability: Yes (for obvious cases)

---

## Rule 3: CSRF Protection

### Severity: CRITICAL

### Description
Never disable CSRF protection. Use proper CSRF tokens for state-changing operations.

### Patterns to Detect

```java
// CRITICAL: CSRF disabled
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf().disable() // Dangerous!
            .build();
    }
}

// BAD: State-changing GET request
@GetMapping("/delete-user")
public String deleteUser(@RequestParam Long id) {
    userService.delete(id); // Vulnerable to CSRF!
    return "redirect:/users";
}
```

### Correct Pattern

```java
// GOOD: CSRF enabled (default)
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf().csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
            .and()
            .build();
    }
}

// GOOD: Use POST for state changes
@PostMapping("/delete-user")
public String deleteUser(@RequestParam Long id) {
    userService.delete(id);
    return "redirect:/users";
}
```

### Auto-fix Capability: Yes

---

## Rule 4: Authentication & Authorization

### Severity: CRITICAL

### Description
Secure all sensitive endpoints with proper authentication and authorization checks.

### Patterns to Detect

```java
// BAD: Missing authorization
@PostMapping("/admin/users")
public ResponseEntity<User> createUser(@RequestBody UserDto dto) {
    // Anyone can access this!
    return ResponseEntity.ok(userService.create(dto));
}

// BAD: Manual role check (error-prone)
@GetMapping("/admin/dashboard")
public String dashboard(Principal principal) {
    User user = userService.findByUsername(principal.getName());
    if (!user.getRole().equals("ADMIN")) { // Manual check
        throw new AccessDeniedException("Not admin");
    }
    return "admin-dashboard";
}
```

### Correct Pattern

```java
// GOOD: Declarative authorization
@PostMapping("/admin/users")
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<User> createUser(@RequestBody UserDto dto) {
    return ResponseEntity.ok(userService.create(dto));
}

// GOOD: Method-level security
@Service
public class UserService {
    @PreAuthorize("hasRole('ADMIN') or #id == principal.id")
    public User getUser(Long id) {
        return userRepository.findById(id).orElseThrow();
    }
}

// GOOD: Global method security
@Configuration
@EnableMethodSecurity
public class SecurityConfig {
    // Enables @PreAuthorize, @PostAuthorize, @Secured
}
```

### Auto-fix Capability: No (requires understanding of business rules)

---

## Rule 5: Hardcoded Credentials

### Severity: CRITICAL

### Description
Never hardcode passwords, API keys, or secrets. Use external configuration.

### Patterns to Detect

```java
// CRITICAL: Hardcoded password
@Configuration
public class DatabaseConfig {
    @Bean
    public DataSource dataSource() {
        DriverManagerDataSource ds = new DriverManagerDataSource();
        ds.setUrl("jdbc:postgresql://localhost:5432/mydb");
        ds.setUsername("admin");
        ds.setPassword("admin123"); // Hardcoded!
        return ds;
    }
}

// BAD: API key in code
public class PaymentService {
    private static final String API_KEY = "sk_live_abc123def456"; // Exposed!
}
```

### Correct Pattern

```java
// GOOD: External configuration
@Configuration
public class DatabaseConfig {
    @Value("${spring.datasource.url}")
    private String url;
    
    @Value("${spring.datasource.username}")
    private String username;
    
    @Value("${spring.datasource.password}")
    private String password;
    
    @Bean
    public DataSource dataSource() {
        DriverManagerDataSource ds = new DriverManagerDataSource();
        ds.setUrl(url);
        ds.setUsername(username);
        ds.setPassword(password);
        return ds;
    }
}

// GOOD: Environment variables
@Service
public class PaymentService {
    @Value("${payment.api.key}")
    private String apiKey;
}
```

### Auto-fix Capability: Partial (can detect, but cannot infer config keys)

---

## Rule 6: Input Validation

### Severity: HIGH

### Description
Always validate and sanitize user input. Use Bean Validation.

### Patterns to Detect

```java
// BAD: No validation
@PostMapping("/users")
public ResponseEntity<User> createUser(@RequestBody UserDto dto) {
    // Accepts any input!
    return ResponseEntity.ok(userService.create(dto));
}

// BAD: File upload without validation
@PostMapping("/upload")
public ResponseEntity<String> upload(@RequestParam MultipartFile file) {
    fileService.save(file); // No size/type validation!
    return ResponseEntity.ok("Uploaded");
}
```

### Correct Pattern

```java
// GOOD: Bean Validation
public record UserDto(
    @NotBlank(message = "Username is required")
    @Size(min = 3, max = 50)
    @Pattern(regexp = "^[a-zA-Z0-9]+$", message = "Alphanumeric only")
    String username,
    
    @NotBlank
    @Email(message = "Valid email required")
    String email,
    
    @NotBlank
    @Size(min = 8, message = "Password must be at least 8 characters")
    String password
) {}

@PostMapping("/users")
public ResponseEntity<User> createUser(@Valid @RequestBody UserDto dto) {
    return ResponseEntity.ok(userService.create(dto));
}

// GOOD: File validation
@PostMapping("/upload")
public ResponseEntity<String> upload(@RequestParam MultipartFile file) {
    // Validate type
    List<String> allowed = Arrays.asList("image/jpeg", "image/png", "image/gif");
    if (!allowed.contains(file.getContentType())) {
        return ResponseEntity.badRequest().body("Invalid file type");
    }
    
    // Validate size (10MB max)
    if (file.getSize() > 10 * 1024 * 1024) {
        return ResponseEntity.badRequest().body("File too large");
    }
    
    fileService.save(file);
    return ResponseEntity.ok("Uploaded");
}
```

### Auto-fix Capability: Partial

---

## Rule 7: Sensitive Data Logging

### Severity: HIGH

### Description
Never log passwords, tokens, PII, or other sensitive data.

### Patterns to Detect

```java
// BAD: Logging password
@Service
public class AuthService {
    public User login(String username, String password) {
        log.info("Login attempt: {} / {}", username, password); // BAD!
        // ...
    }
}

// BAD: Logging full user object (might contain sensitive data)
log.info("User created: {}", user); // User.toString() might expose password
```

### Correct Pattern

```java
// GOOD: Don't log sensitive data
@Service
public class AuthService {
    public User login(String username, String password) {
        log.info("Login attempt for user: {}", username);
        // ...
    }
}

// GOOD: Log only non-sensitive fields
log.info("User created: id={}, username={}", user.getId(), user.getUsername());

// GOOD: Override toString to exclude sensitive fields
@Entity
public class User {
    private String username;
    
    @JsonIgnore
    private String password;
    
    @Override
    public String toString() {
        return "User{id=" + id + ", username='" + username + "'}";
        // Password excluded
    }
}
```

### Auto-fix Capability: Yes (can detect patterns)

---

## Rule 8: Weak Cryptography

### Severity: CRITICAL

### Description
Use strong cryptographic algorithms. Never use MD5 or SHA-1 for passwords.

### Patterns to Detect

```java
// CRITICAL: Weak hashing
public String hashPassword(String password) {
    MessageDigest md = MessageDigest.getInstance("MD5"); // Weak!
    byte[] hash = md.digest(password.getBytes());
    return Base64.getEncoder().encodeToString(hash);
}

// BAD: SHA-1 for passwords
MessageDigest md = MessageDigest.getInstance("SHA-1"); // Still weak!

// BAD: Insecure random
Random random = new Random(); // Predictable!
int token = random.nextInt();
```

### Correct Pattern

```java
// GOOD: BCrypt for passwords
@Service
public class PasswordService {
    private final PasswordEncoder passwordEncoder = 
        new BCryptPasswordEncoder(12); // BCrypt with strength 12
    
    public String hashPassword(String password) {
        return passwordEncoder.encode(password);
    }
    
    public boolean verifyPassword(String password, String hash) {
        return passwordEncoder.matches(password, hash);
    }
}

// GOOD: Use Spring Security's PasswordEncoder
@Configuration
public class SecurityConfig {
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12);
    }
}

// GOOD: Secure random for tokens
SecureRandom secureRandom = new SecureRandom();
byte[] token = new byte[32];
secureRandom.nextBytes(token);
String tokenString = Base64.getUrlEncoder().encodeToString(token);
```

### Auto-fix Capability: Yes

---

## Rule 9: Path Traversal Prevention

### Severity: HIGH

### Description
Validate and sanitize file paths to prevent directory traversal attacks.

### Patterns to Detect

```java
// BAD: Path traversal vulnerability
@GetMapping("/files/{filename}")
public ResponseEntity<Resource> download(@PathVariable String filename) {
    // Attack: filename = "../../../etc/passwd"
    Path file = Paths.get("/uploads/" + filename);
    Resource resource = new FileSystemResource(file);
    return ResponseEntity.ok(resource);
}
```

### Correct Pattern

```java
// GOOD: Validate and normalize path
@GetMapping("/files/{filename}")
public ResponseEntity<Resource> download(@PathVariable String filename) {
    // Remove any path characters
    String sanitized = filename.replaceAll("[^a-zA-Z0-9.-]", "");
    
    // Resolve against base directory
    Path baseDir = Paths.get("/uploads/").toAbsolutePath().normalize();
    Path file = baseDir.resolve(sanitized).normalize();
    
    // Verify file is within allowed directory
    if (!file.startsWith(baseDir)) {
        throw new SecurityException("Invalid file path");
    }
    
    // Verify file exists and is regular file
    if (!Files.exists(file) || !Files.isRegularFile(file)) {
        throw new FileNotFoundException();
    }
    
    Resource resource = new FileSystemResource(file);
    return ResponseEntity.ok(resource);
}
```

### Auto-fix Capability: Partial

---

## Rule 10: Insecure Dependencies

### Severity: CRITICAL

### Description
Keep Spring Boot and dependencies up-to-date. Avoid EOL versions.

### Patterns to Detect

```xml
<!-- CRITICAL: End-of-life Spring Boot -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>1.5.22.RELEASE</version> <!-- EOL August 2019 -->
</parent>

<!-- BAD: Old Spring Security with known vulnerabilities -->
<dependency>
    <groupId>org.springframework.security</groupId>
    <artifactId>spring-security-core</artifactId>
    <version>4.2.3.RELEASE</version> <!-- Old version -->
</dependency>
```

### Correct Pattern

```xml
<!-- GOOD: Current LTS version -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.0</version> <!-- Current LTS -->
</parent>

<!-- GOOD: Let Spring Boot manage versions -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
    <!-- No version - managed by parent -->
</dependency>
```

### Auto-fix Capability: Yes (with version database)

---

## Summary

Total Rules: 10

### By Severity
- CRITICAL: 6 rules (60%)
- HIGH: 4 rules (40%)

### Auto-fix Capability
- Fully Auto-fixable: 5 rules (50%)
- Partially Auto-fixable: 3 rules (30%)
- Manual Fix Required: 2 rules (20%)

### Critical Rules (Must Fix Before Merge)
1. SQL Injection Prevention
2. XSS Prevention
3. CSRF Protection
4. Authentication & Authorization
5. Hardcoded Credentials
6. Weak Cryptography
7. Insecure Dependencies

### References
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Spring Security: https://spring.io/projects/spring-security
- OWASP Java Encoder: https://owasp.org/www-project-java-encoder/


