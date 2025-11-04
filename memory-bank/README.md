# Memory Bank

This directory contains the Memory Bank for the AI Code Review System v2.0 project. The Memory Bank serves as persistent documentation that survives between AI sessions.

## Structure

### Core Files (Required)

1. **`projectbrief.md`** - Foundation document
   - Core requirements and goals
   - Project scope
   - Key architectural decisions
   - Reference documents

2. **`productContext.md`** - Product vision
   - Why this project exists
   - Problem statement
   - User experience goals
   - Success metrics

3. **`activeContext.md`** - Current work focus
   - Recent changes
   - Current state
   - Next steps
   - Active decisions
   - Important patterns and preferences
   - Learnings and insights

4. **`systemPatterns.md`** - System architecture
   - Key technical decisions
   - Design patterns in use
   - Component relationships
   - Critical implementation paths

5. **`techContext.md`** - Technical details
   - Technology stack
   - Development setup
   - Deployment information
   - Technical constraints
   - Tool usage patterns

6. **`progress.md`** - Project status
   - What works
   - What's left to build
   - Current status
   - Known issues
   - Evolution of decisions

## Usage

### Reading the Memory Bank

When starting a new task, the AI assistant should:
1. Read `projectbrief.md` first for foundational context
2. Review `activeContext.md` for current work focus
3. Reference other files as needed for specific details

### Updating the Memory Bank

Memory Bank files should be updated when:
- Discovering new project patterns
- After implementing significant changes
- When explicitly requested with "update memory bank"
- When context needs clarification

### Key Updates

- **`activeContext.md`**: Updated frequently with current work
- **`progress.md`**: Updated after major milestones
- **`systemPatterns.md`**: Updated when architectural decisions change
- **`techContext.md`**: Updated when dependencies or setup changes

## Tags

Memory Bank files use tags for quick navigation:
- `#architecture` - System architecture decisions
- `#cli-agents` - CLI agent usage patterns
- `#git-operations` - Git and GitLab integration
- `#error-handling` - Error handling and recovery patterns
- `#deployment` - Deployment and scaling considerations
- `#refactoring` - Refactoring classification logic
- `#rules-system` - Hierarchical rules system

## Related Documentation

- Project documentation: `docs/` directory
- Architecture: `docs/ARCHITECTURE_RU.md`
- PRD: `docs/PRD.md`
- Summary: `SUMMARY.md`

