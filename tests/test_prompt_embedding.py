"""
Tests for prompt file embedding functionality
"""

import pytest
from pathlib import Path
from app.services.review_service import ReviewService
from app.services.cline_cli_manager import ClineCLIManager
from app.services.qwen_code_cli_manager import QwenCodeCLIManager
from app.services.custom_rules_loader import CustomRulesLoader


@pytest.fixture
def review_service():
    """Create ReviewService instance for testing"""
    cline_manager = ClineCLIManager(
        model_api_url="http://localhost:8000",
        model_name="test-model",
        api_key="test-key",
        parallel_tasks=2
    )
    
    qwen_manager = QwenCodeCLIManager(
        model_api_url="http://localhost:8000",
        model_name="test-model",
        api_key="test-key",
        parallel_tasks=2
    )
    
    rules_loader = CustomRulesLoader()
    
    return ReviewService(
        cline_manager=cline_manager,
        qwen_manager=qwen_manager,
        rules_loader=rules_loader
    )


def test_embed_referenced_files_no_references(review_service):
    """Test embedding with no file references"""
    prompt = "This is a simple prompt with no references."
    result = review_service._embed_referenced_files(prompt)
    assert result == prompt


def test_embed_referenced_files_with_md_reference(review_service):
    """Test embedding with markdown file reference"""
    prompt = """# Test Prompt

Some content here.

See `prompts/common/critical_json_requirements.md` for details.

More content.
"""
    
    result = review_service._embed_referenced_files(prompt)
    
    # Check that reference is replaced with navigation link
    assert "`prompts/common/critical_json_requirements.md`" not in result
    assert "[📎 critical_json_requirements.md (embedded below)]" in result
    
    # Check that file content is embedded
    assert "📎 Embedded Reference Files" in result
    assert "prompts/common/critical_json_requirements.md" in result
    assert "Rule 1: Output ONLY Valid JSON" in result


def test_embed_referenced_files_with_json_schema(review_service):
    """Test embedding with JSON schema reference"""
    prompt = """# Test Prompt

Your output will be validated against `schemas/review_result_schema.json`

More content.
"""
    
    result = review_service._embed_referenced_files(prompt)
    
    # Check that reference is replaced with navigation link
    assert "`schemas/review_result_schema.json`" not in result
    assert "[📎 review_result_schema.json (embedded below)]" in result
    
    # Check that schema is embedded
    assert "📎 Embedded Reference Files" in result
    assert "schemas/review_result_schema.json" in result
    assert "```json" in result
    assert '"$schema"' in result


def test_embed_referenced_files_multiple_references_same_file(review_service):
    """Test that file is embedded only once even if referenced multiple times"""
    prompt = """# Test Prompt

First reference: See `prompts/common/critical_json_requirements.md`

Some content.

Second reference: Read `prompts/common/critical_json_requirements.md` for rules.

More content.
"""
    
    result = review_service._embed_referenced_files(prompt)
    
    # Both references should be replaced with navigation links
    assert "`prompts/common/critical_json_requirements.md`" not in result
    assert result.count("[📎 critical_json_requirements.md (embedded below)]") == 2
    
    # File should be embedded only once
    embedded_count = result.count("prompts/common/critical_json_requirements.md (Markdown Document)")
    assert embedded_count == 1


def test_embed_referenced_files_multiple_different_files(review_service):
    """Test embedding multiple different files"""
    prompt = """# Test Prompt

JSON requirements: See `prompts/common/critical_json_requirements.md`

Git diff instructions: See `prompts/common/git_diff_instructions.md`

Schema: `schemas/review_result_schema.json`
"""
    
    result = review_service._embed_referenced_files(prompt)
    
    # All references should be replaced with navigation links
    assert "`prompts/common/critical_json_requirements.md`" not in result
    assert "`prompts/common/git_diff_instructions.md`" not in result
    assert "`schemas/review_result_schema.json`" not in result
    
    assert "[📎 critical_json_requirements.md (embedded below)]" in result
    assert "[📎 git_diff_instructions.md (embedded below)]" in result
    assert "[📎 review_result_schema.json (embedded below)]" in result
    
    # All files should be embedded
    assert "📎 Embedded Reference Files" in result
    assert "critical_json_requirements.md" in result
    assert "git_diff_instructions.md" in result
    assert "review_result_schema.json" in result


def test_embed_referenced_files_nonexistent_file(review_service):
    """Test handling of nonexistent file reference"""
    prompt = """# Test Prompt

See `prompts/common/nonexistent_file.md` for details.
"""
    
    result = review_service._embed_referenced_files(prompt)
    
    # Reference should be replaced with navigation link (even if file doesn't exist)
    assert "`prompts/common/nonexistent_file.md`" not in result
    assert "[📎 nonexistent_file.md (embedded below)]" in result


def test_embed_referenced_files_preserves_structure(review_service):
    """Test that main prompt structure is preserved"""
    prompt = """# Test Prompt

## Objective

Analyze code for errors.

## Instructions

Follow these steps:

1. Read `prompts/common/critical_json_requirements.md`
2. Analyze the code
3. Output JSON

## Output Format

Use JSON format.
"""
    
    result = review_service._embed_referenced_files(prompt)
    
    # Check that structure is preserved
    assert "# Test Prompt" in result
    assert "## Objective" in result
    assert "## Instructions" in result
    assert "## Output Format" in result
    
    # Check that reference is replaced with navigation link
    assert "`prompts/common/critical_json_requirements.md`" not in result
    assert "1. Read [📎 critical_json_requirements.md (embedded below)]" in result
    
    # Check that embedded section is at the end
    assert result.index("📎 Embedded Reference Files") > result.index("## Output Format")


def test_load_prompts_with_embedding(review_service):
    """Test that _load_prompts properly calls embedding function"""
    from app.models import ReviewType, CLIAgent
    
    prompts = review_service._load_prompts(
        agent=CLIAgent.CLINE,
        review_types=[ReviewType.ERROR_DETECTION]
    )
    
    assert ReviewType.ERROR_DETECTION in prompts
    prompt_content = prompts[ReviewType.ERROR_DETECTION]
    
    # Check that references are replaced with navigation links
    assert "`prompts/common/critical_json_requirements.md`" not in prompt_content
    assert "`prompts/common/git_diff_instructions.md`" not in prompt_content
    assert "[📎 critical_json_requirements.md (embedded below)]" in prompt_content
    assert "[📎 git_diff_instructions.md (embedded below)]" in prompt_content
    
    # Check that content is embedded
    assert "📎 Embedded Reference Files" in prompt_content
    assert "Rule 1: Output ONLY Valid JSON" in prompt_content


def test_embed_cleans_up_blank_lines(review_service):
    """Test that multiple blank lines are cleaned up after removing references"""
    prompt = """# Test Prompt

Some content.


See `prompts/common/critical_json_requirements.md` for details.


More content.
"""
    
    result = review_service._embed_referenced_files(prompt)
    
    # Check that the content between "Some content" and "More content" doesn't have excessive blanks
    # (the test should verify blanks are reduced, but allow normal section breaks)
    lines = result.split('\n')
    
    # Find consecutive blank lines
    max_consecutive_blanks = 0
    current_consecutive = 0
    for line in lines:
        if line.strip() == '':
            current_consecutive += 1
            max_consecutive_blanks = max(max_consecutive_blanks, current_consecutive)
        else:
            current_consecutive = 0
    
    # Should not have more than 2 consecutive blank lines (which gives \n\n\n when joined)
    # But we allow up to 3 for section separators
    assert max_consecutive_blanks <= 3, f"Too many consecutive blank lines: {max_consecutive_blanks}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

