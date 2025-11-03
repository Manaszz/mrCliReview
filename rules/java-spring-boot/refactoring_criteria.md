# Refactoring Classification Criteria for Java Spring Boot

## Overview

This document defines criteria for classifying refactoring suggestions as SIGNIFICANT or MINOR, determining whether they require a separate MR or can be combined with fixes.

---

## SIGNIFICANT Refactoring (Separate MR Required)

### Criterion 1: Scope - More than 3 Classes Affected

**Description**: Refactoring touches more than 3 classes or files.

**Rationale**: Changes across multiple classes increase risk and review complexity. Separate MR allows focused review of architectural changes.

**Examples**:
- Extracting a new service that affects 5 controllers
- Renaming a widely-used method across 10 files
- Introducing a new layer (e.g., adding DTOs to all controllers)

---

### Criterion 2: Breaking Changes to Public APIs

**Description**: Modifications change method signatures, class names, or package structure used by other modules.

**Rationale**: Breaking changes require coordination and may affect other teams. Needs careful review and versioning strategy.

**Examples**:
- Changing REST API endpoint paths
- Modifying public method signatures
- Renaming packages
- Changing return types of public methods

---

### Criterion 3: Lines of Code - More than 200 LOC Changed

**Description**: Total lines added + removed exceeds 200.

**Rationale**: Large changes are harder to review thoroughly. Separate MR improves review quality.

**Calculation**:
```
total_changes = lines_added + lines_removed
if total_changes > 200: SIGNIFICANT
```

---

### Criterion 4: Dependency Injection Structure Modifications

**Description**: Changes to how beans are wired or dependency graph structure.

**Rationale**: DI changes can have subtle runtime effects. Requires isolated testing.

**Examples**:
- Introducing new interfaces for dependency inversion
- Changing bean scopes (singleton to prototype)
- Modifying constructor parameters across multiple classes
- Breaking circular dependencies

---

### Criterion 5: Pattern Migrations

**Description**: Migrating from one design pattern to another.

**Rationale**: Pattern migrations represent fundamental approach changes. Need comprehensive testing.

**Examples**:
- Converting callback hell to CompletableFuture
- Migrating from synchronous to reactive (WebFlux)
- Introducing Strategy pattern to replace if-else chains
- Converting to Builder pattern for complex object construction

---

### Criterion 6: Database Schema or Query Changes

**Description**: Refactoring involves database structural changes.

**Rationale**: Database changes require migration scripts and careful rollback planning.

**Examples**:
- Changing entity relationships (@OneToMany to @ManyToMany)
- Modifying column types or names
- Splitting or merging tables
- Changing query fetch strategies (lazy to eager)

---

### Criterion 7: Architecture Layer Violations Fixed

**Description**: Moving code between architectural layers (controller ↔ service ↔ repository).

**Rationale**: Layer changes represent architectural improvements that should be reviewed separately from bug fixes.

**Examples**:
- Moving business logic from controller to service
- Extracting data access from service to repository
- Introducing DTO layer where entities were exposed

---

## MINOR Refactoring (Can Combine with Fixes)

### Criterion 1: Variable or Method Renames (Local Scope)

**Description**: Renaming within a single method or class.

**Examples**:
- Renaming local variables for clarity
- Renaming private methods
- Renaming method parameters

---

### Criterion 2: Constant Extraction

**Description**: Replacing magic numbers/strings with named constants.

**Examples**:
```java
// Before
if (age > 18) { }

// After
private static final int MINIMUM_AGE = 18;
if (age > MINIMUM_AGE) { }
```

---

### Criterion 3: Code Formatting

**Description**: Whitespace, indentation, line breaks.

**Examples**:
- Adding blank lines for readability
- Breaking long lines
- Consistent indentation

---

### Criterion 4: Simple Conditional Simplification

**Description**: Simplifying boolean logic within a single method.

**Examples**:
```java
// Before
if (isActive == true) { }

// After
if (isActive) { }
```

---

### Criterion 5: Extract Small Method (Within Same Class)

**Description**: Extracting 5-10 lines into a private method within the same class.

**Examples**:
```java
// Before
public void process() {
    // 5 lines of validation
    // 10 lines of business logic
}

// After
public void process() {
    validateInput();
    executeBusinessLogic();
}

private void validateInput() {
    // 5 lines of validation
}
```

---

### Criterion 6: Comment Improvements

**Description**: Adding or improving JavaDoc and inline comments.

**Rationale**: Documentation improvements don't change behavior and are always beneficial.

---

### Criterion 7: Import Organization

**Description**: Removing unused imports, organizing imports.

**Rationale**: Cosmetic change with zero risk.

---

## Decision Tree

```
START: Analyze Refactoring Suggestion

├─ Does it affect >3 classes?
│  └─ YES → SIGNIFICANT
│
├─ Does it change public APIs (breaking)?
│  └─ YES → SIGNIFICANT
│
├─ Are >200 LOC changed?
│  └─ YES → SIGNIFICANT
│
├─ Does it modify DI structure?
│  └─ YES → SIGNIFICANT
│
├─ Is it a pattern migration?
│  └─ YES → SIGNIFICANT
│
├─ Does it involve database changes?
│  └─ YES → SIGNIFICANT
│
├─ Does it fix architecture layer violations?
│  └─ YES → SIGNIFICANT
│
└─ NO to all above → MINOR
```

---

## Examples with Classification

### Example 1: Extract UserValidationService

**Changes**:
- Create new UserValidationService class
- Update UserService to use validation service
- Update 3 controllers to inject validation service

**Analysis**:
- Affects: 5 files (1 new + 1 service + 3 controllers)
- LOC: ~150 (new service) + 30 (updates) = 180
- DI structure: Yes, new bean introduced
- Pattern: Introducing service extraction pattern

**Classification**: SIGNIFICANT (affects >3 files, DI changes)

---

### Example 2: Rename Variable for Clarity

**Changes**:
```java
// Before
public void process(User u) {
    String n = u.getName();
    log.info("Processing: {}", n);
}

// After
public void process(User user) {
    String userName = user.getName();
    log.info("Processing: {}", userName);
}
```

**Analysis**:
- Affects: 1 method in 1 file
- LOC: 2 lines changed
- No structural changes

**Classification**: MINOR (local rename only)

---

### Example 3: Convert to CompletableFuture

**Changes**:
- Convert 7 methods from synchronous to asynchronous
- Change return types from T to CompletableFuture<T>
- Update callers to handle async results

**Analysis**:
- Affects: 12 files
- LOC: ~400
- Pattern migration: callback → CompletableFuture
- Breaking changes to method signatures

**Classification**: SIGNIFICANT (pattern migration, >3 files, breaking changes)

---

### Example 4: Extract Constant

**Changes**:
```java
// Before
if (user.getAge() < 18) { }
if (account.getBalance() > 1000) { }

// After
private static final int MINIMUM_AGE = 18;
private static final int BALANCE_THRESHOLD = 1000;

if (user.getAge() < MINIMUM_AGE) { }
if (account.getBalance() > BALANCE_THRESHOLD) { }
```

**Analysis**:
- Affects: 1 file
- LOC: 4 added, 2 modified
- No behavioral change

**Classification**: MINOR (constant extraction only)

---

## Special Cases

### Case 1: Mixed Refactoring

**Scenario**: Refactoring contains both SIGNIFICANT and MINOR changes.

**Decision**: Classify as SIGNIFICANT. The MR should handle significant changes; minor improvements can be included.

---

### Case 2: Borderline Cases (e.g., exactly 3 files, 200 LOC)

**Decision**: Use judgment based on:
- Complexity of changes
- Risk level
- Team's review capacity
- Default to SIGNIFICANT if uncertain

---

### Case 3: Performance Optimization

**Decision**: Usually SIGNIFICANT because:
- May change behavior subtly
- Requires performance testing
- Needs careful review

Exception: If optimization is 100% transparent (e.g., using `StringBuilder` instead of string concatenation in a loop), can be MINOR.

---

## Summary

### SIGNIFICANT Indicators (Any one triggers separate MR)
1. More than 3 classes affected
2. Breaking API changes
3. More than 200 LOC changed
4. DI structure modifications
5. Pattern migrations
6. Database changes
7. Architecture layer fixes

### MINOR Indicators (Can combine with fixes)
1. Local variable/method renames
2. Constant extraction
3. Formatting
4. Simple conditional simplification
5. Small method extraction (same class)
6. Comment improvements
7. Import organization

### When in Doubt
**Default to SIGNIFICANT**. It's better to have an extra MR than to mix complex refactoring with critical bug fixes.


