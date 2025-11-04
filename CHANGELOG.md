# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Memory Bank initialization with 6 core documentation files
- Active review tracking to prevent concurrent reviews of same MR
- System prompt with static code style rules (loaded once, cached)
- Lombok usage guidelines in system prompt
- Git diff instructions in all prompts
- Comprehensive SYSTEM_PROMPT_GUIDE.md documentation

### Changed
- **BREAKING**: Removed `changed_files` parameter from all CLI managers
- Updated all 14 prompts to use git diff for detecting changed files
- GitRepositoryManager now tracks active reviews and prevents conflicts
- System prompt is now prepended to all review requests automatically
- Default target branch changed to `develop` in prompts

### Fixed
- Concurrent review conflict when multiple requests for same MR
- Changed files parameter no longer needed (CLI detects via git diff)

## [2.0.0] - 2025-11-04

### Initial Release
- Multi-agent code review system with Cline and Qwen Code CLI
- 11 review types (ERROR_DETECTION, BEST_PRACTICES, REFACTORING, etc.)
- GitLab integration with minimal API usage
- Docker and Kubernetes deployment support
- Hierarchical rules system (project/Confluence/default)
- Smart refactoring classification (SIGNIFICANT/MINOR)

