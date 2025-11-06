# Git Diff Analysis Instructions

## Context: Full Project Visibility

You have **full access to the entire repository** and should understand the complete project context.
**However**, your **PRIMARY FOCUS** must be on changed files.

---

## Step 1: Identify Changed Files (MANDATORY)

**Before analysis**, execute git diff to identify what changed:

```bash
# Get list of changed files
git diff --name-only origin/<target-branch>

# Get detailed changes with context
git diff origin/<target-branch>
```

**Store the list of changed files** - these are your primary analysis targets.

---

## Step 2: Analysis Strategy

### Primary Analysis (REQUIRED)
**Thoroughly analyze ALL changed files** identified by git diff:
- Every issue in changed files
- All code patterns in changed files
- Complete review according to review type

### Supporting Analysis (OPTIONAL but RECOMMENDED)
**Review related unchanged files** to provide better context:
- Check if changes break existing contracts
- Verify consistency with existing patterns
- Identify impacts on dependent code
- Understand broader architectural implications

**Example**: If `UserService.java` changed and calls `EmailService.java`, you can:
- ✅ Read `EmailService.java` to understand the contract
- ✅ Check if new calls match existing usage patterns
- ✅ Verify the change fits the architecture
- ❌ But don't report issues in `EmailService.java` unless they're directly related to the change

---

## Step 3: Report Only Relevant Issues

**In your output**, focus on:

### ✅ Always Report:
- All issues in changed files (from git diff)
- New issues introduced by the changes
- Violations of existing patterns by new code

### ✅ Optionally Report (if relevant):
- Issues in unchanged files **directly impacted** by changes
- Breaking changes that affect existing code
- Architectural concerns raised by the changes

### ❌ Never Report:
- Pre-existing issues in unchanged files unrelated to this MR
- General code quality issues in the entire codebase
- Issues that existed before these changes

---

## Step 4: Include Analysis Metadata

**In your JSON output**, include:

```json
{
  "review_type": "ERROR_DETECTION",
  "changed_files": [
    "src/main/java/UserService.java",
    "src/main/java/OrderService.java"
  ],
  "files_analyzed_count": 2,
  "issues": [
    // Issues found
  ],
  "summary": {
    "total_issues": 5,
    "files_analyzed": 2
    // ...
  }
}
```

**Purpose**:
- Confirms you used git diff
- Shows which files were analyzed
- Provides transparency in your analysis

---

## Why This Approach?

### Benefits:
1. **Context-Aware**: You understand the full project
2. **Focused**: Primary analysis on changed code
3. **Relevant**: Avoid noise from pre-existing issues
4. **Actionable**: Developer can fix issues in their MR
5. **Fair**: Don't blame new MR for old technical debt

### Example Workflow:

```
1. Execute: git diff --name-only origin/main
   Output: UserService.java, OrderValidator.java

2. Read full project to understand:
   - What UserService does
   - How OrderValidator is used
   - Related patterns and conventions

3. Analyze changed files deeply:
   - UserService.java: 3 issues found
   - OrderValidator.java: 2 issues found

4. Check related unchanged files:
   - EmailService.java (called by UserService): No new issues
   - PaymentService.java (uses OrderValidator): Check if interface changed

5. Report:
   - 5 issues in changed files
   - 1 warning about impact on PaymentService
   - Total: 6 items in report
```

---

## Summary

🎯 **Primary Target**: Changed files from git diff  
📚 **Context Source**: Full repository access  
✅ **Report**: Issues in changed files + direct impacts  
❌ **Avoid**: Pre-existing issues unrelated to MR  

This approach ensures **relevant, actionable feedback** while maintaining **full project awareness**.

