# Product Requirements Document: Multi-Agent Code Review System

**Version:** 2.0.0  
**Date:** November 2025  
**Status:** Active Development  
**Target:** Java Spring Boot Applications (extensible to other languages)

---

## Executive Summary

### Vision

Create an intelligent, automated code review system that leverages state-of-the-art CLI-based AI agents (Cline and Qwen Code) to provide comprehensive, multi-dimensional analysis of Java Spring Boot merge requests. The system aims to reduce manual review burden, catch critical issues before production, and enforce coding standards consistently across development teams.

### Goals

1. **Comprehensive Coverage**: Support 11 specialized review types covering errors, security, performance, architecture, and best practices
2. **Flexibility**: Allow selection of specific review types based on context and urgency
3. **Dual Agent Architecture**: Provide choice between Cline CLI (DeepSeek V3.1 Terminus) and Qwen Code CLI (Qwen3-Coder) for different use cases
4. **Smart MR Creation**: Automatically generate fix MRs with intelligent separation of critical fixes from refactoring suggestions
5. **Customizability**: Support project-specific rules and conventions through hierarchical rule system
6. **Production Ready**: Docker Compose deployment with Kubernetes support and air-gap transfer capability

### Target Users

- **Primary**: Java Spring Boot development teams working with GitLab
- **Secondary**: DevOps teams managing code quality pipelines
- **Tertiary**: Technical leads and architects enforcing coding standards

---

## Architecture Overview

### System Architecture

```
GitLab MR Event
    ↓
n8n Workflow (validation)
    ↓
Review API (FastAPI)
    ↓
Review Service (agent selection)
    ↓
┌─────────────────┬──────────────────┐
│  Cline CLI      │  Qwen Code CLI   │
│  (DeepSeek V3.1)│  (Qwen3-Coder)   │
└─────────────────┴──────────────────┘
    ↓
Cloned Repository (local analysis)
    ↓
Results Aggregation
    ↓
┌──────────────────┬─────────────────┬────────────────┐
│ Javadoc Commit   │ Fixes MR        │ Refactoring MR │
│ (source branch)  │ (critical)      │ (if significant)│
└──────────────────┴─────────────────┴────────────────┘
    ↓
GitLab Comments & Notifications
```

### Key Architectural Decisions

#### 1. CLI-Based Agents (Not Direct Model Calls)

**Decision**: Use Cline CLI and Qwen Code CLI instead of direct API calls to language models.

**Rationale**:
- CLI agents have built-in context management and memory
- Better code understanding through native repository indexing
- Multi-file analysis and cross-reference capabilities
- Ability to work with large codebases through intelligent chunking
- Built-in diff analysis and change detection

#### 2. Single Agent Execution (Not Combined)

**Decision**: Always execute either Cline OR Qwen Code, never both simultaneously.

**Rationale**:
- Prevents conflicting recommendations
- Simpler result interpretation
- Lower resource consumption
- Clearer responsibility attribution
- Easier debugging and issue tracking

#### 3. Minimal GitLab API Usage

**Decision**: Clone repository locally and perform all analysis on cloned code.

**Rationale**:
- Reduces API rate limit concerns
- Enables CLI agents to use native git operations
- Better performance for large diffs
- CLI agents work best with local repositories
- Simpler error handling

#### 4. Repository Cloning Strategy

**Decision**: Clone entire MR source branch for each review.

**Rationale**:
- CLI agents require full repository context
- Enables accurate cross-file analysis
- Allows agents to understand project structure
- Supports refactoring suggestions that span multiple files
- Cleanup after review maintains isolation

---

## Core Features

### 1. Multi-Type Review System (11 Types)

#### ERROR_DETECTION
**Purpose**: Identify bugs, potential crashes, and logical errors

**Checks**:
- NullPointerException prevention patterns
- Optional usage correctness
- Exception handling anti-patterns (empty catch blocks, swallowing exceptions)
- Try-with-resources for AutoCloseable resources
- Type safety violations
- Unchecked casts and raw types
- Missing null checks at boundaries

**Example Issues**:
```java
// BAD: Potential NPE
public void process(User user) {
    String name = user.getName().toUpperCase(); // NPE if getName() returns null
}

// GOOD: Defensive programming
public void process(User user) {
    String name = Optional.ofNullable(user.getName())
        .map(String::toUpperCase)
        .orElse("UNKNOWN");
}
```

#### BEST_PRACTICES
**Purpose**: Enforce SOLID principles, DRY, KISS, and Spring Boot conventions

**Checks**:
- SOLID principles violations (SRP, OCP, LSP, ISP, DIP)
- DRY violations (code duplication)
- Overly complex methods (high cyclomatic complexity)
- Proper use of Records for immutable data classes
- Sealed Classes for controlled inheritance
- Pattern Matching usage (Java 17+)
- Proper Generics usage (avoiding raw types, correct wildcard usage)
- Spring Boot conventions (@Service, @Repository, @Component usage)
- Dependency injection patterns (constructor injection preferred)
- @Transactional placement (service layer, not repository)

**Example Issues**:
```java
// BAD: Business logic in controller
@RestController
public class UserController {
    @Autowired
    private UserRepository repo;
    
    @PostMapping("/users")
    public User createUser(@RequestBody UserDto dto) {
        // Validation logic in controller
        if (dto.getAge() < 18) throw new IllegalArgumentException("Too young");
        
        // Business logic in controller
        User user = new User();
        user.setName(dto.getName());
        user.setAge(dto.getAge());
        user.setCreatedAt(LocalDateTime.now());
        
        return repo.save(user);
    }
}

// GOOD: Separation of concerns
@RestController
public class UserController {
    private final UserService userService;
    
    public UserController(UserService userService) {
        this.userService = userService;
    }
    
    @PostMapping("/users")
    public User createUser(@Valid @RequestBody UserDto dto) {
        return userService.createUser(dto);
    }
}

@Service
public class UserService {
    private final UserRepository userRepository;
    
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
    
    @Transactional
    public User createUser(UserDto dto) {
        // Business logic here
    }
}
```

#### REFACTORING
**Purpose**: Suggest code improvements for maintainability and readability

**Checks**:
- Circular dependency detection
- Business logic in controllers (should be in services)
- Long methods (>50 lines)
- Long classes (>500 lines )
- Deep nesting (>3 levels)
- Magic numbers (should be constants)
- Code duplication
- Complex boolean expressions
- Blocking calls in reactive code

**Classification**:
- **SIGNIFICANT** (separate MR): >3 classes affected, breaking changes, >200 LOC, DI structure changes, pattern migrations
- **MINOR** (combined with fixes): variable renames, constant extraction, formatting, conditional simplification

#### SECURITY_AUDIT
**Purpose**: Identify security vulnerabilities and risks

**Checks**:
- SQL injection (non-parameterized queries)
- XSS vulnerabilities (unencoded output)
- CSRF protection configuration
- Input validation (Bean Validation usage)
- Authentication/authorization checks
- Secure @Transactional usage (proper isolation)
- Hardcoded credentials
- Insecure random number generation
- Path traversal vulnerabilities
- End-of-life dependencies (EOL Spring Boot/Framework versions)

**Example Issues**:
```java
// BAD: SQL Injection vulnerability
@Repository
public class UserRepository {
    @Autowired
    private JdbcTemplate jdbc;
    
    public User findByUsername(String username) {
        String sql = "SELECT * FROM users WHERE username = '" + username + "'";
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
```

#### DOCUMENTATION
**Purpose**: Generate and verify code documentation quality

**Checks**:
- Missing Javadoc on public APIs
- Javadoc completeness (@param, @return, @throws)
- Meaningful comment presence
- Code self-documentation (clear naming)
- API documentation standards
- README updates for new features

**Auto-generation**:
- Javadoc for public methods
- Class-level documentation
- Package-info.java for packages

**Commit Strategy**: Documentation improvements are committed directly to the MR source branch.

#### PERFORMANCE
**Purpose**: Identify performance issues and optimization opportunities

**Checks**:
- N+1 query detection in JPA (@OneToMany, @ManyToOne lazy loading)
- Missing @EntityGraph or JOIN FETCH
- Blocking calls in reactive code (Project Reactor, RxJava)
- Inefficient Stream API usage
- Incorrect parallel stream usage
- Connection pool misconfiguration (HikariCP)
- Missing caching opportunities
- Inefficient collection operations
- Large object allocations in loops

**Example Issues**:
```java
// BAD: N+1 query problem
@Service
public class OrderService {
    public List<OrderDto> getAllOrders() {
        List<Order> orders = orderRepository.findAll(); // 1 query
        return orders.stream()
            .map(order -> {
                List<Item> items = order.getItems(); // N queries (lazy loading)
                return new OrderDto(order, items);
            })
            .collect(Collectors.toList());
    }
}

// GOOD: JOIN FETCH
@Service
public class OrderService {
    public List<OrderDto> getAllOrders() {
        List<Order> orders = orderRepository.findAllWithItems(); // 1 query
        return orders.stream()
            .map(order -> new OrderDto(order, order.getItems()))
            .collect(Collectors.toList());
    }
}

// Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    @Query("SELECT o FROM Order o LEFT JOIN FETCH o.items")
    List<Order> findAllWithItems();
}
```

#### ARCHITECTURE
**Purpose**: Verify architectural patterns and microservices best practices

**Checks**:
- Circuit Breaker implementation (Resilience4j)
- API Gateway patterns
- Database per Service compliance (microservices)
- Service-to-service communication patterns
- Event-driven architecture patterns
- API versioning strategy (URL path vs content negotiation)
- REST API pagination implementation
- CORS configuration
- Proper use of DTOs for layer separation

**Example Issues**:
```java
// BAD: Direct database access across services
@Service
public class OrderService {
    @Autowired
    private UserRepository userRepository; // Cross-service DB access
    
    public Order createOrder(Long userId) {
        User user = userRepository.findById(userId).orElseThrow();
        // ...
    }
}

// GOOD: Service-to-service via API
@Service
public class OrderService {
    private final UserServiceClient userClient;
    
    public OrderService(UserServiceClient userClient) {
        this.userClient = userClient;
    }
    
    @CircuitBreaker(name = "userService", fallbackMethod = "createOrderFallback")
    public Order createOrder(Long userId) {
        UserDto user = userClient.getUser(userId);
        // ...
    }
    
    public Order createOrderFallback(Long userId, Exception e) {
        // Fallback logic
    }
}
```

#### TRANSACTION_MANAGEMENT
**Purpose**: Verify correct transaction configuration and usage

**Checks**:
- @Transactional placement (service layer, not repository)
- Propagation levels correctness (REQUIRED, REQUIRES_NEW, NESTED)
- Isolation levels appropriateness (READ_COMMITTED, REPEATABLE_READ)
- Read-only transaction optimization
- Transaction boundary correctness
- Avoiding @Transactional on private methods
- Proper exception handling in transactions

**Example Issues**:
```java
// BAD: @Transactional overuse
@Service
public class UserService {
    @Transactional // Unnecessary for read-only
    public User findById(Long id) {
        return userRepository.findById(id).orElseThrow();
    }
}

// GOOD: Read-only transaction
@Service
public class UserService {
    @Transactional(readOnly = true)
    public User findById(Long id) {
        return userRepository.findById(id).orElseThrow();
    }
    
    @Transactional // Write operation
    public User createUser(UserDto dto) {
        User user = new User();
        // ... setup user
        return userRepository.save(user);
    }
}
```

#### CONCURRENCY
**Purpose**: Identify concurrency issues and optimize concurrent code

**Checks**:
- Race condition detection
- Proper synchronization usage
- Virtual threads usage (Java 21+)
- @Async configuration and patterns
- CompletableFuture proper usage
- Thread-safe collections usage
- Immutability for concurrent access
- Avoiding shared mutable state

**Example Issues**:
```java
// BAD: Race condition
public class Counter {
    private int count = 0;
    
    public void increment() {
        count++; // Not thread-safe
    }
}

// GOOD: Atomic operations
public class Counter {
    private final AtomicInteger count = new AtomicInteger(0);
    
    public void increment() {
        count.incrementAndGet();
    }
}
```

#### DATABASE_OPTIMIZATION
**Purpose**: Optimize database queries and data access patterns

**Checks**:
- Missing indexes on frequently queried columns
- @EntityGraph usage for fetch optimization
- Lazy vs eager loading strategy
- Batch operations usage
- Query projection for large entities
- Proper pagination implementation
- Connection pool sizing
- Query result caching

**Example Issues**:
```java
// BAD: Fetching full entity when only need few fields
@Service
public class UserService {
    public List<String> getAllUsernames() {
        return userRepository.findAll().stream()
            .map(User::getUsername)
            .collect(Collectors.toList());
    }
}

// GOOD: Projection query
@Service
public class UserService {
    public List<String> getAllUsernames() {
        return userRepository.findAllUsernames();
    }
}

public interface UserRepository extends JpaRepository<User, Long> {
    @Query("SELECT u.username FROM User u")
    List<String> findAllUsernames();
}
```

#### ALL (Default)
**Purpose**: Execute all review types for comprehensive analysis

**Behavior**: When `review_types` parameter contains `ALL` or is not specified, all 10 specialized review types are executed in parallel (based on CLI capacity: 5 for Cline, 3 for Qwen).

---

### 2. Dual CLI Agent Support

#### Cline CLI (Primary)

**Model**: DeepSeek V3.1 Terminus  
**Parallel Tasks**: 5  
**Strengths**:
- Superior context understanding
- Better at complex refactoring suggestions
- Excellent security analysis
- Strong architectural insights
- Comprehensive documentation generation

**Task Distribution**:
1. ERROR_DETECTION
2. BEST_PRACTICES + ARCHITECTURE
3. REFACTORING + PERFORMANCE
4. SECURITY_AUDIT + TRANSACTION_MANAGEMENT
5. DOCUMENTATION + CONCURRENCY + DATABASE_OPTIMIZATION

#### Qwen Code CLI (Alternative)

**Model**: Qwen3-Coder-32B  
**Parallel Tasks**: 3  
**Strengths**:
- Fast execution
- Strong at error detection
- Good code pattern recognition
- Efficient for focused reviews

**Task Distribution**:
1. ERROR_DETECTION + SECURITY_AUDIT
2. BEST_PRACTICES + PERFORMANCE
3. REFACTORING + DATABASE_OPTIMIZATION

#### Agent Selection Strategy

**Default**: Cline (more comprehensive)

**When to use Qwen**:
- Fast turnaround needed
- Focused reviews (1-3 review types)
- Limited compute resources
- Error detection + security focus

**Configuration**: Set via `DEFAULT_CLI_AGENT` environment variable or `agent` parameter in API request.

---

### 3. Smart MR Creation

#### Documentation Commits (Immediate)

**Target**: MR source branch  
**Content**: Javadoc and code comments  
**Timing**: Committed immediately after review completion  
**Rationale**: Documentation improves the original MR quality without changing logic

#### Fixes MR (Critical Issues)

**Target**: New branch from MR source branch  
**Content**: 
- Critical bug fixes (NPE prevention, exception handling)
- Security vulnerability patches
- Performance critical issues (N+1 query fixes)

**Naming**: `fix/mr-{iid}-ai-review-fixes`  
**Description**: Detailed list of fixes with references to original issues  
**Auto-merge**: No (requires developer approval)

#### Refactoring MR (Conditional)

**Decision Logic**:
```python
if refactoring_classifier.classify(suggestions) == "SIGNIFICANT":
    create_separate_refactoring_mr()
else:
    include_in_fixes_mr()
```

**SIGNIFICANT Criteria**:
- More than 3 classes affected
- Breaking changes to public APIs
- More than 200 lines of code changed
- Dependency injection structure modifications
- Pattern migrations (e.g., callback hell to CompletableFuture)

**MINOR Criteria**:
- Variable/method renames
- Constant extraction
- Code formatting
- Conditional simplification
- Local refactoring within methods

**Naming**: `refactor/mr-{iid}-ai-suggestions`  
**Description**: Rationale for each refactoring with code examples

---

### 4. Hierarchical Rules System

#### Rule Priority (Highest to Lowest)

1. **Project-Specific Rules** (`.project-rules/` in repository root)
2. **Confluence Rules** (fetched via n8n workflow)
3. **Default Rules** (`rules/java-spring-boot/` in review service)

#### Rule Structure

Each rule file contains:
- **Overview**: Purpose and scope
- **Patterns**: Code patterns to detect (positive and negative examples)
- **Severity Levels**: CRITICAL, HIGH, MEDIUM, LOW, INFO
- **Auto-fix Capability**: Whether issue can be auto-fixed
- **Examples**: Before/after code snippets
- **References**: Links to documentation and best practices

#### Project-Specific Rules

**Location**: `.project-rules/` directory in project repository  
**Format**: Markdown files matching default structure  
**Usage**: Automatically detected and loaded during review  
**Override Behavior**: Project rules fully override default rules for the same check

**Example**: Project-specific transaction isolation requirement
```markdown
# transaction_management.md

## Default Isolation Level

**Rule**: All @Transactional methods MUST use READ_COMMITTED isolation level unless explicitly documented otherwise.

**Rationale**: Our database (PostgreSQL) is optimized for READ_COMMITTED. REPEATABLE_READ can cause performance issues under high load.

**Example**:
```java
// REQUIRED
@Transactional(isolation = Isolation.READ_COMMITTED)
public void processOrder(Order order) {
    // ...
}
```
```

#### Confluence Rules

**Integration**: Loaded via n8n workflow  
**Cache**: 1 hour TTL  
**Format**: Markdown exported from Confluence  
**Use Case**: Shared rules across multiple projects/teams
```
---


### 5. Customizable Review Execution

#### Review Type Selection

**API Parameter**: `review_types: List[ReviewType]`  
**Default**: `[ALL]`

**Examples**:

Quick Security Check:
```json
{
  "agent": "QWEN_CODE",
  "review_types": ["ERROR_DETECTION", "SECURITY_AUDIT"],
  "project_id": 123,
  "merge_request_iid": 456
}
```

Performance Focused:
```json
{
  "agent": "CLINE",
  "review_types": ["PERFORMANCE", "DATABASE_OPTIMIZATION"],
  "project_id": 123,
  "merge_request_iid": 456
}
```

Full Review (Default):
```json
{
  "agent": "CLINE",
  "review_types": ["ALL"],
  "project_id": 123,
  "merge_request_iid": 456
}
```

#### Execution Strategy

**Parallel Execution**: Multiple review types execute simultaneously within CLI agent capacity  
**Resource Management**: Automatic throttling if system load exceeds threshold  
**Timeout**: 5 minutes per review type (configurable)  
**Retry**: 1 retry on failure with exponential backoff

---

## Integration Points

### GitLab Integration (Minimal API Usage)

**Required API Calls**:
1. `GET /projects/:id/merge_requests/:iid` - Get MR metadata
2. `GET /projects/:id` - Get clone URL
3. `POST /projects/:id/merge_requests/:iid/notes` - Add summary comment
4. `POST /projects/:id/repository/commits` - Commit documentation
5. `POST /projects/:id/merge_requests` - Create fix/refactoring MRs

**Avoided**:
- Listing files via API (use git locally)
- Getting diffs via API (use git diff locally)
- Complex merge operations via API

### n8n Workflow Integration

**Workflow**: GitLab Webhook → Validation → Review API → Results Processing

**LangChain Code Node** (JavaScript validation):
```javascript
// Validate JIRA ticket and description
const title = $json.body.object_attributes.title;
const description = $json.body.object_attributes.description || '';

const jiraPattern = /([A-Z]+-\d+)/;
const jiraMatch = title.match(jiraPattern);

const validationErrors = [];
if (!jiraMatch) {
    validationErrors.push('Missing JIRA ticket in title (format: PROJECT-123)');
}
if (description.length < 50) {
    validationErrors.push('Description too short (minimum 50 characters)');
}
if (description.includes('TODO') || description.includes('TBD')) {
    validationErrors.push('Description contains placeholder text');
}

return {
    is_valid: validationErrors.length === 0,
    errors: validationErrors,
    jira_ticket: jiraMatch ? jiraMatch[1] : null,
    score: jiraMatch && description.length >= 50 ? 100 : 50
};
```

**Review API Call**:
```javascript
const response = await $http.request({
    method: 'POST',
    url: 'http://review-api:8000/api/v1/review',
    headers: {
        'Content-Type': 'application/json'
    },
    body: {
        agent: 'CLINE',
        review_types: ['ALL'],
        project_id: $json.body.project.id,
        merge_request_iid: $json.body.object_attributes.iid,
        language: 'java'
    }
});

return response.body;
```

### MCP RAG Integration (Future)

**Purpose**: Query internal knowledge base for library compatibility, API usage patterns  
**Protocol**: SSE/HTTP connection to n8n MCP server  
**Backend**: Qdrant vector database  
**Use Cases**:
- Library compatibility checking (Library Updater Agent)
- Internal API documentation lookup
- Historical issue pattern matching

---

## TODO Features (Planned)

### JIRA Task Matcher Agent

**Purpose**: Verify MR changes fully implement the JIRA task requirements

**Inputs**:
- JIRA task ID (from MR title)
- Task description from JIRA API
- MR code changes

**Analysis**:
- Identify task requirements from description
- Match requirements to code changes
- Detect missing implementations
- Distinguish task work from refactoring

**Outputs**:
- Completion percentage (0-100%)
- List of unimplemented requirements
- Suggestions for missing implementation
- Fix MR if requirements incomplete

**Integration**: Requires JIRA API access via n8n workflow

### Changelog Generator Agent

**Purpose**: Automatically generate/update CHANGELOG.md entries

**Inputs**:
- Git commit history
- MR diff
- Commit messages
- JIRA task information

**Analysis**:
- Categorize changes (Added/Changed/Fixed/Deprecated/Removed/Security)
- Extract meaningful descriptions from commits
- Group related changes
- Follow Keep a Changelog format

**Output**: CHANGELOG.md update committed to MR branch

### Library Updater Agent

**Purpose**: Identify and update outdated dependencies

**Inputs**:
- pom.xml 
- Current dependency versions
- MCP RAG knowledge base (compatibility info)

**Analysis**:
- Identify outdated libraries
- Check compatibility via knowledge base
- Identify breaking changes
- Generate migration notes

**Output**: MR with updated dependencies and migration guide

**Integration**: Requires MCP RAG connection for compatibility checking

---

## Technical Stack

### Backend
- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11
- **Async**: asyncio with uvicorn
- **Validation**: Pydantic 2.5+

### CLI Agents
- **Cline CLI**: Latest stable version
- **Qwen Code CLI**: Latest stable version
- **Installation**: npm global packages

### Models (Pre-deployed)
- **DeepSeek V3.1 Terminus**: via OpenAI compatible API
- **Qwen3-Coder-32B**: via OpenAI compatible API

### GitLab Integration
- **python-gitlab**: 4.4.0
- **GitPython**: 3.1.40

### Deployment
- **Primary**: Docker Compose
- **Production**: Kubernetes (deployment/ directory)
- **Container Registry**: Internal registry for air-gap support

---

## Deployment Architecture

### Docker Compose (Development/Testing)

```yaml
services:
  review-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MODEL_API_URL=${MODEL_API_URL}
      - DEEPSEEK_MODEL_NAME=${DEEPSEEK_MODEL_NAME}
      - QWEN3_MODEL_NAME=${QWEN3_MODEL_NAME}
      - GITLAB_URL=${GITLAB_URL}
      - GITLAB_TOKEN=${GITLAB_TOKEN}
    volumes:
      - ./prompts:/app/prompts
      - ./rules:/app/rules
      - ./logs:/app/logs
```

### Kubernetes (Production)

**Components**:
- Deployment: 3 replicas for high availability
- Service: ClusterIP for internal access
- Ingress: External access with TLS
- ConfigMap: Prompts and rules
- Secret: GitLab token, model API key
- PersistentVolume: Log storage

### Air-Gap Transfer

**Preparation** (Connected Environment):
1. Export Docker images: `docker save -o review-api.tar review-api:latest`
2. Download npm packages: `npm pack @cline/cli @qwen-code/qwen-code`
3. Create Python offline repository: `pip download -r requirements.txt -d packages/`
4. Archive prompts and rules: `tar -czf rules-prompts.tar.gz prompts/ rules/`

**Installation** (Isolated Environment):
1. Load Docker images: `docker load -i review-api.tar`
2. Install npm packages: `npm install -g cline-cli.tgz qwen-code.tgz`
3. Install Python packages: `pip install --no-index --find-links=packages/ -r requirements.txt`
4. Extract rules/prompts: `tar -xzf rules-prompts.tar.gz`
5. Configure environment variables
6. Deploy with docker-compose or kubectl

---

## Success Metrics

### Coverage Metrics
- **Review Types Executed**: Track which review types are most used
- **Issues Found per Type**: Measure effectiveness of each review type
- **False Positive Rate**: Track issues marked as incorrect by developers (<10% target)

### Performance Metrics
- **Review Time**: Average time per review (<5 minutes target)
- **API Response Time**: p95 < 30 seconds
- **Parallel Task Efficiency**: Utilization of parallel task slots

### Quality Metrics
- **Critical Issues Prevented**: Number of security/bug issues caught before production
- **Developer Acceptance Rate**: Percentage of fix MRs merged (>70% target)
- **Refactoring Adoption**: Percentage of refactoring MRs merged (>50% target)

### Developer Satisfaction
- **Manual Review Time Saved**: Hours saved per week
- **Review Quality Score**: Developer rating of review usefulness (1-5 scale, >4.0 target)
- **False Negative Rate**: Issues missed by review but found later (<5% target)

---

## Future Enhancements

### Phase 2 (Q2 2026)
- JIRA Task Matcher Agent implementation
- Changelog Generator Agent implementation
- Library Updater Agent with MCP RAG

### Phase 3 (Q3 2026)
- Support for Python, JavaScript/TypeScript codebases
- Custom check development framework
- Integration with SonarQube for additional metrics

### Phase 4 (Q4 2026)
- AI-powered code generation for common patterns
- Interactive review mode (developer can ask questions)
- Historical issue learning (avoid repeating past mistakes)

---

## Appendices

### A. Glossary

- **CLI Agent**: Command-line AI tool (Cline or Qwen Code) that performs code analysis
- **Review Type**: Specific category of code analysis (ERROR_DETECTION, SECURITY_AUDIT, etc.)
- **Fix MR**: Merge request automatically created with issue fixes
- **Refactoring MR**: Merge request with refactoring suggestions (if significant)
- **SIGNIFICANT Refactoring**: Large-scale refactoring requiring separate MR (>3 classes, breaking changes, >200 LOC)
- **MINOR Refactoring**: Small-scale refactoring included in fix MR (renames, constant extraction)

### B. References

- [Spring Boot Documentation](https://spring.io/projects/spring-boot)
- [Java Language Specification](https://docs.oracle.com/javase/specs/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Cline CLI Documentation](https://docs.cline.bot)
- [Qwen Code Documentation](https://qwenlm.github.io)

### C. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11 | Use CLI agents instead of direct model calls | Better code understanding, context management |
| 2025-11 | Single agent execution (not combined) | Avoid conflicting recommendations |
| 2025-11 | Minimal GitLab API usage | Reduce rate limits, better performance |
| 2025-11 | 11 review types | Comprehensive coverage based on research |
| 2025-11 | Separate refactoring MRs for significant changes | Give developers choice |

---

**Document Status**: Living document, updated as features are implemented and requirements evolve.

**Feedback**: Submit feedback and suggestions via GitLab issues in the review service repository.

