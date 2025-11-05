#!/usr/bin/env python3
"""
Script to update all CLI prompts with critical JSON requirements and git diff instructions.
Adds standardized headers to prompts for Cline and Qwen agents.
"""

import os
from pathlib import Path

# Header to add after Context section
CRITICAL_HEADER = """
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
"""

# Instructions section enhancement
GIT_DIFF_INSTRUCTIONS = """
### Step 1: Identify Changed Files

Execute `git diff` to determine which files have changed:

```bash
git diff --name-only origin/<target-branch>
```

**You have full project access** - browse any file for context. **But analyze and report issues primarily for changed files.**

See `prompts/common/git_diff_instructions.md` for complete strategy.
"""

# JSON output requirements header
JSON_OUTPUT_HEADER = r"""
### ⚠️ CRITICAL: JSON Output Requirements ⚠️

**READ**: `prompts/common/critical_json_requirements.md` for complete rules.

**Key Points**:
1. Output ONLY valid JSON, no other text
2. NO markdown code blocks (no ```json)
3. Include ALL required fields
4. Use exact field names and types
5. Validate before outputting

### Required JSON Structure

"""

JSON_OUTPUT_FOOTER = """
**Validation**: Your output will be validated against `schemas/review_result_schema.json`
"""

def add_critical_header(content: str) -> str:
    """Add critical instructions header after Context section"""
    
    # Find Context section end
    lines = content.split('\n')
    result = []
    context_end_found = False
    header_added = False
    
    for i, line in enumerate(lines):
        result.append(line)
        
        # Look for end of Context section (usually followed by ## Instructions or ##)
        if not header_added and '## Context' in content[:i * 50]:
            # Check if next non-empty line starts with ##
            next_lines = lines[i+1:i+5]
            for next_line in next_lines:
                if next_line.strip():
                    if next_line.startswith('##'):
                        # Insert critical header before next section
                        result.append(CRITICAL_HEADER.rstrip())
                        header_added = True
                    break
    
    return '\n'.join(result)


def enhance_instructions_section(content: str) -> str:
    """Enhance Instructions section with git diff guidance"""
    
    # Replace generic git diff instructions with enhanced version
    old_patterns = [
        "**IMPORTANT**: Use `git diff` to automatically determine which files have changed.\nAnalyze only the changed files between the current branch and the target branch.\n\nCommand to detect changes: `git diff --name-only origin/develop` (or use appropriate target branch)",
        "**IMPORTANT**: Use `git diff` to automatically determine which files have changed.\nAnalyze only the changed files between the current branch and the target branch.\n\nCommand to detect changes: `git diff --name-only origin/main` (or use appropriate target branch)",
    ]
    
    for pattern in old_patterns:
        if pattern in content:
            content = content.replace(pattern, GIT_DIFF_INSTRUCTIONS.strip())
            break
    
    return content


def enhance_output_format(content: str) -> str:
    """Add critical JSON requirements to Output Format section"""
    
    # Find "## Output Format" and add critical header after it
    if '## Output Format' in content:
        content = content.replace(
            '## Output Format',
            '## Output Format\n\n' + JSON_OUTPUT_HEADER.strip()
        )
    
    # Add changed_files field to JSON examples
    if '"review_type":' in content and '"changed_files"' not in content:
        # This is approximate - would need more sophisticated parsing for production
        pass
    
    # Add validation footer before severity levels
    if '## Severity Levels' in content and JSON_OUTPUT_FOOTER.strip() not in content:
        content = content.replace(
            '\n\n## Severity Levels',
            '\n\n' + JSON_OUTPUT_FOOTER + '\n## Severity Levels'
        )
    
    return content


def update_prompt_file(file_path: Path) -> bool:
    """Update a single prompt file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if already updated
        if 'prompts/common/critical_json_requirements.md' in content:
            print(f"  [SKIP] {file_path.name} (already updated)")
            return False
        
        original_content = content
        
        # Apply transformations
        content = add_critical_header(content)
        content = enhance_instructions_section(content)
        content = enhance_output_format(content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  [OK] Updated {file_path.name}")
            return True
        else:
            print(f"  [INFO] No changes needed for {file_path.name}")
            return False
            
    except Exception as e:
        print(f"  [ERROR] Failed to update {file_path}: {e}")
        return False


def main():
    """Main function to update all prompts"""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Directories to update
    cline_dir = project_root / 'prompts' / 'cline'
    qwen_dir = project_root / 'prompts' / 'qwen'
    
    print("="  * 60)
    print("Updating CLI Prompts with Critical Instructions")
    print("=" * 60)
    print()
    
    updated_count = 0
    
    # Update Cline prompts
    print("Processing Cline prompts...")
    if cline_dir.exists():
        for prompt_file in sorted(cline_dir.glob('*.md')):
            if update_prompt_file(prompt_file):
                updated_count += 1
    print()
    
    # Update Qwen prompts
    print("Processing Qwen prompts...")
    if qwen_dir.exists():
        for prompt_file in sorted(qwen_dir.glob('*.md')):
            if update_prompt_file(prompt_file):
                updated_count += 1
    print()
    
    print("=" * 60)
    print(f"Complete! Updated {updated_count} prompt files")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Review updated prompts in prompts/cline/ and prompts/qwen/")
    print("2. Test with actual CLI agents")
    print("3. Validate JSON output against schemas/review_result_schema.json")


if __name__ == '__main__':
    main()

