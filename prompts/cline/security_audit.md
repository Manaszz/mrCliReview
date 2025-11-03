# Security Audit Prompt for Cline CLI

## Objective

Perform comprehensive security analysis of Java Spring Boot code changes to identify vulnerabilities, security misconfigurations, and compliance issues.

## Context

- **Repository Path**: {repo_path}
- **Language**: {language}
- **Changed Files**: {changed_files}
- **Custom Rules**: {custom_rules}
- **JIRA Context**: {jira_context}

## Analysis Scope

### 1. SQL Injection Prevention

**Check for**:
- String concatenation in SQL queries
- Non-parameterized queries
- Dynamic query construction without validation
- Native SQL queries without parameter binding

**Example patterns**:
```java
// CRITICAL: SQL Injection vulnerability
@Repository
public class UserRepository {
    @Autowired
    private JdbcTemplate jdbc;
    
    public User findByUsername(String username) {
        String sql = "SELECT * FROM users WHERE username = '" + username + "'";
        // Attacker can inject: admin' OR '1'='1
        return jdbc.queryForObject(sql, new UserRowMapper());
    }
}

// GOOD: Parameterized query
@Repository
public class UserRepository {
    @Autowired
    private JdbcTemplate jdbc;
    
    public User findByUsername(String username) {
        String sql = "SELECT * FROM users WHERE username = ?";
        return jdbc.queryForObject(sql, new UserRowMapper(), username);
    }
}

// GOOD: JPA/JPQL (automatically parameterized)
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByUsername(String username);
}
```

### 2. XSS (Cross-Site Scripting) Prevention

**Check for**:
- Unencoded user input in HTML responses
- Direct output of user data in templates
- innerHTML usage with user data
- Missing content-type headers

**Example patterns**:
```java
// BAD: XSS vulnerability
@GetController
public class ProfileController {
    @GetMapping("/profile")
    public String showProfile(@RequestParam String name, Model model) {
        model.addAttribute("username", name); // No encoding!
        return "profile";
    }
}

// In profile.html (Thymeleaf):
// BAD: Unescaped output
<div th:utext="${username}"></div> // XSS if name contains <script>

// GOOD: Escaped output (Thymeleaf default)
<div th:text="${username}"></div> // Automatically HTML-escaped

// GOOD: Explicit encoding in Java
import org.owasp.encoder.Encode;

@GetController
public class ProfileController {
    @GetMapping("/profile")
    public String showProfile(@RequestParam String name, Model model) {
        String safeUsername = Encode.forHtml(name);
        model.addAttribute("username", safeUsername);
        return "profile";
    }
}
```

### 3. CSRF Protection

**Check for**:
- POST/PUT/DELETE endpoints without CSRF protection
- CSRF disabled in security config
- State-changing GET requests
- Missing CSRF tokens in forms

**Example patterns**:
```java
// BAD: CSRF protection disabled
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

// GOOD: CSRF enabled (default in Spring Security)
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

// BAD: State-changing GET
@GetMapping("/delete-account")
public String deleteAccount(@RequestParam Long userId) {
    userService.delete(userId); // State change via GET - vulnerable to CSRF!
    return "redirect:/";
}

// GOOD: Use POST/DELETE for state changes
@PostMapping("/delete-account")
public String deleteAccount(@RequestParam Long userId) {
    userService.delete(userId);
    return "redirect:/";
}
```

### 4. Authentication & Authorization

**Check for**:
- Missing @PreAuthorize / @Secured annotations
- Hardcoded credentials
- Weak password policies
- Missing authentication on sensitive endpoints
- Improper role checks

**Example patterns**:
```java
// BAD: No authorization check
@PostMapping("/admin/users")
public ResponseEntity<User> createUser(@RequestBody UserDto dto) {
    // Anyone can create users!
    return ResponseEntity.ok(userService.create(dto));
}

// GOOD: Proper authorization
@PostMapping("/admin/users")
@PreAuthorize("hasRole('ADMIN')")
public ResponseEntity<User> createUser(@RequestBody UserDto dto) {
    return ResponseEntity.ok(userService.create(dto));
}

// BAD: Hardcoded credentials
@Configuration
public class DatabaseConfig {
    @Bean
    public DataSource dataSource() {
        DriverManagerDataSource ds = new DriverManagerDataSource();
        ds.setPassword("admin123"); // Hardcoded!
        return ds;
    }
}

// GOOD: External configuration
@Configuration
public class DatabaseConfig {
    @Value("${spring.datasource.password}")
    private String dbPassword;
    
    @Bean
    public DataSource dataSource() {
        DriverManagerDataSource ds = new DriverManagerDataSource();
        ds.setPassword(dbPassword); // From environment
        return ds;
    }
}
```

### 5. Input Validation

**Check for**:
- Missing @Valid annotation on request bodies
- No validation on path variables
- Accepting any file uploads without validation
- Missing size limits
- No content type validation

**Example patterns**:
```java
// BAD: No validation
@PostMapping("/users")
public ResponseEntity<User> createUser(@RequestBody UserDto dto) {
    // No validation - accepts invalid data!
    return ResponseEntity.ok(userService.create(dto));
}

// GOOD: Bean Validation
public record UserDto(
    @NotBlank(message = "Username is required")
    @Size(min = 3, max = 50)
    String username,
    
    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    String email,
    
    @NotBlank
    @Pattern(regexp = "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{8,}$",
             message = "Password must be at least 8 characters with letters and numbers")
    String password
) {}

@PostMapping("/users")
public ResponseEntity<User> createUser(@Valid @RequestBody UserDto dto) {
    return ResponseEntity.ok(userService.create(dto));
}

// BAD: File upload without validation
@PostMapping("/upload")
public ResponseEntity<String> upload(@RequestParam MultipartFile file) {
    // No validation - accepts any file!
    fileService.save(file);
    return ResponseEntity.ok("Uploaded");
}

// GOOD: File validation
@PostMapping("/upload")
public ResponseEntity<String> upload(@RequestParam MultipartFile file) {
    // Validate file type
    String contentType = file.getContentType();
    if (!Arrays.asList("image/jpeg", "image/png").contains(contentType)) {
        return ResponseEntity.badRequest().body("Invalid file type");
    }
    
    // Validate file size (10MB max)
    if (file.getSize() > 10 * 1024 * 1024) {
        return ResponseEntity.badRequest().body("File too large");
    }
    
    fileService.save(file);
    return ResponseEntity.ok("Uploaded");
}
```

### 6. Secure @Transactional Usage

**Check for**:
- Incorrect isolation levels exposing data
- Missing read-only transactions
- Transaction boundaries exposing uncommitted data

**Example patterns**:
```java
// BAD: Default isolation might not be sufficient for sensitive operations
@Transactional
public void transferMoney(Long fromId, Long toId, BigDecimal amount) {
    Account from = accountRepository.findById(fromId).orElseThrow();
    Account to = accountRepository.findById(toId).orElseThrow();
    // Race condition possible with default isolation!
    from.setBalance(from.getBalance().subtract(amount));
    to.setBalance(to.getBalance().add(amount));
    accountRepository.saveAll(List.of(from, to));
}

// GOOD: Appropriate isolation level
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transferMoney(Long fromId, Long toId, BigDecimal amount) {
    Account from = accountRepository.findById(fromId).orElseThrow();
    Account to = accountRepository.findById(toId).orElseThrow();
    
    if (from.getBalance().compareTo(amount) < 0) {
        throw new InsufficientFundsException();
    }
    
    from.setBalance(from.getBalance().subtract(amount));
    to.setBalance(to.getBalance().add(amount));
    accountRepository.saveAll(List.of(from, to));
}
```

### 7. Sensitive Data Exposure

**Check for**:
- Logging sensitive data (passwords, tokens, PII)
- Returning sensitive fields in API responses
- Storing passwords in plain text
- Sensitive data in error messages

**Example patterns**:
```java
// BAD: Logging sensitive data
@Service
public class AuthService {
    public User login(String username, String password) {
        log.info("Login attempt for user: {} with password: {}", username, password); // BAD!
        // ...
    }
}

// GOOD: Don't log sensitive data
@Service
public class AuthService {
    public User login(String username, String password) {
        log.info("Login attempt for user: {}", username);
        // ...
    }
}

// BAD: Exposing sensitive fields
@Entity
public class User {
    private String username;
    private String password; // Exposed in JSON responses!
    private String ssn;
}

// GOOD: Hide sensitive fields
@Entity
public class User {
    private String username;
    
    @JsonIgnore
    private String password;
    
    @JsonIgnore
    private String ssn;
}
```

### 8. Insecure Dependencies

**Check for**:
- End-of-life Spring Boot versions (< 2.7.x)
- End-of-life Spring Framework versions (< 5.3.x)
- Known vulnerable dependencies
- Outdated security libraries

**Example patterns**:
```xml
<!-- BAD: EOL Spring Boot version -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>1.5.22.RELEASE</version> <!-- EOL since August 2019! -->
</parent>

<!-- GOOD: Current LTS version -->
<parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.2.0</version>
</parent>
```

### 9. Insecure Cryptography

**Check for**:
- Weak hashing algorithms (MD5, SHA-1)
- Hardcoded encryption keys
- Insecure random number generation
- Not using BCrypt for passwords

**Example patterns**:
```java
// BAD: Weak password hashing
public String hashPassword(String password) {
    MessageDigest md = MessageDigest.getInstance("MD5"); // Weak!
    byte[] hash = md.digest(password.getBytes());
    return Base64.getEncoder().encodeToString(hash);
}

// GOOD: BCrypt for passwords
@Service
public class PasswordService {
    private final PasswordEncoder passwordEncoder = new BCryptPasswordEncoder(12);
    
    public String hashPassword(String password) {
        return passwordEncoder.encode(password);
    }
    
    public boolean verifyPassword(String password, String hash) {
        return passwordEncoder.matches(password, hash);
    }
}

// BAD: Insecure random
Random random = new Random(); // Predictable!
int token = random.nextInt();

// GOOD: Secure random
SecureRandom secureRandom = new SecureRandom();
byte[] token = new byte[32];
secureRandom.nextBytes(token);
```

### 10. Path Traversal

**Check for**:
- File operations with user-provided paths
- No path validation
- Directory traversal vulnerabilities

**Example patterns**:
```java
// BAD: Path traversal vulnerability
@GetMapping("/files/{filename}")
public ResponseEntity<Resource> downloadFile(@PathVariable String filename) {
    // Attacker can use: ../../../etc/passwd
    Path file = Paths.get("/uploads/" + filename);
    Resource resource = new FileSystemResource(file);
    return ResponseEntity.ok(resource);
}

// GOOD: Validate and sanitize path
@GetMapping("/files/{filename}")
public ResponseEntity<Resource> downloadFile(@PathVariable String filename) {
    // Sanitize filename
    String sanitized = filename.replaceAll("[^a-zA-Z0-9.-]", "");
    
    Path file = Paths.get("/uploads/").resolve(sanitized).normalize();
    
    // Verify file is within allowed directory
    if (!file.startsWith("/uploads/")) {
        throw new SecurityException("Invalid file path");
    }
    
    Resource resource = new FileSystemResource(file);
    return ResponseEntity.ok(resource);
}
```

## Output Format

```json
{
  "review_type": "SECURITY_AUDIT",
  "vulnerabilities": [
    {
      "file": "src/main/java/com/example/repository/UserRepository.java",
      "line": 25,
      "severity": "CRITICAL",
      "category": "SQL Injection",
      "cwe": "CWE-89",
      "message": "SQL injection vulnerability: user input concatenated directly into query",
      "code_snippet": "String sql = \"SELECT * FROM users WHERE username = '\" + username + \"'\";",
      "attack_scenario": "Attacker can inject: admin' OR '1'='1 to bypass authentication",
      "suggestion": "Use parameterized query with PreparedStatement or JPA repository method",
      "fix_example": "String sql = \"SELECT * FROM users WHERE username = ?\"; jdbc.queryForObject(sql, mapper, username);",
      "auto_fixable": true
    },
    {
      "file": "src/main/java/com/example/config/SecurityConfig.java",
      "line": 18,
      "severity": "CRITICAL",
      "category": "CSRF Protection Disabled",
      "cwe": "CWE-352",
      "message": "CSRF protection is disabled, making application vulnerable to cross-site request forgery",
      "code_snippet": ".csrf().disable()",
      "attack_scenario": "Attacker can trick authenticated user into performing unintended actions",
      "suggestion": "Enable CSRF protection (enabled by default, remove disable() call)",
      "auto_fixable": true
    }
  ],
  "summary": {
    "total_vulnerabilities": 2,
    "critical": 2,
    "high": 0,
    "medium": 0,
    "low": 0,
    "files_analyzed": 25,
    "security_score": 65
  }
}
```

## Severity Levels

- **CRITICAL**: Exploitable vulnerability allowing unauthorized access or data breach
- **HIGH**: Security flaw that could be exploited under certain conditions
- **MEDIUM**: Security weakness that should be addressed
- **LOW**: Minor security concern or best practice violation
- **INFO**: Security recommendation for hardening

## Instructions

1. Prioritize OWASP Top 10 vulnerabilities
2. Consider deployment environment in security assessment
3. Check for compliance with security standards in {custom_rules}
4. Provide attack scenarios for identified vulnerabilities
5. Include CWE (Common Weakness Enumeration) references
6. Suggest specific fixes with code examples
7. Calculate overall security score (0-100)
8. Output comprehensive security report in JSON format



