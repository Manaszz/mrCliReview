# Project Brief: AI Code Review System v2.0

**Version:** 2.0.0  
**Created:** 2025-11-04  
**Status:** Active Development  
**Target Language:** Java Spring Boot (extensible to other languages)

---

## Changelog

| Version | Date | Summary |
|---------|------|---------|
| 2.0.0 | 2025-11-04 | Initial Memory Bank initialization |

---

## Executive Summary

A multi-agent automated code review system that leverages CLI-based AI agents (Cline and Qwen Code) to provide comprehensive analysis of Java Spring Boot merge requests. The system integrates with GitLab and n8n for full automation of the code review process.

## Core Requirements

### Primary Goals

1. **Comprehensive Code Review**: Support 11 specialized review types covering errors, security, performance, architecture, and best practices
2. **Dual Agent Architecture**: Choice between Cline CLI (DeepSeek V3.1 Terminus) and Qwen Code CLI (Qwen3-Coder) for different use cases
3. **Smart MR Creation**: Automatically generate fix MRs with intelligent separation of critical fixes from refactoring suggestions
4. **Customizability**: Support project-specific rules and conventions through hierarchical rule system
5. **Production Ready**: Docker Compose deployment with Kubernetes support and air-gap transfer capability

### Key Constraints

- **Minimal GitLab API Usage**: Primary work through Git CLI, API only for MR operations
- **Single Agent Execution**: Always execute either Cline OR Qwen Code, never both simultaneously
- **CLI-Based Agents**: Use CLI tools instead of direct model calls for better context management
- **Repository Cloning**: Clone entire MR source branch for each review to enable full context analysis

## Target Users

- **Primary**: Java Spring Boot development teams working with GitLab
- **Secondary**: DevOps teams managing code quality pipelines
- **Tertiary**: Technical leads and architects enforcing coding standards

## Success Criteria

- Review time: Average <5 minutes per review
- Developer acceptance rate: >70% of fix MRs merged
- Refactoring adoption: >50% of refactoring MRs merged
- False positive rate: <10%
- False negative rate: <5%

## Project Scope

### In Scope

- 11 review types (ERROR_DETECTION, BEST_PRACTICES, REFACTORING, SECURITY_AUDIT, DOCUMENTATION, PERFORMANCE, ARCHITECTURE, TRANSACTION_MANAGEMENT, CONCURRENCY, DATABASE_OPTIMIZATION)
- Dual CLI agent support (Cline/Qwen Code)
- GitLab integration (minimal API usage)
- n8n workflow integration
- Docker and Kubernetes deployment
- Hierarchical rules system (project/Confluence/default)
- Smart refactoring classification (SIGNIFICANT/MINOR)

### Out of Scope (Future Phases)

- JIRA Task Matcher Agent (Phase 2)
- Changelog Generator Agent (Phase 2)
- Library Updater Agent (Phase 2)
- Multi-language support beyond Java (Phase 3)
- Custom review type development framework (Phase 3)

---

## Project Structure

```
mrCliReview/
├── app/                    # FastAPI application
│   ├── api/               # REST endpoints
│   ├── services/          # Business logic (13 services)
│   ├── utils/             # Helpers
│   └── models.py          # Pydantic models
├── deployment/            # Deployment configurations
│   └── kubernetes/        # K8s manifests
├── docs/                  # Documentation (Russian)
├── prompts/               # 13 prompt templates
├── rules/                 # Rule definitions
│   └── java-spring-boot/  # Java-specific rules
├── tests/                 # Test suites
├── memory-bank/           # Memory Bank (this directory)
└── scripts/               # Utility scripts
```

---

## Key Architectural Decisions

1. **CLI-Based Agents**: Use CLI tools (Cline/Qwen Code) instead of direct API calls for better code understanding and context management
2. **Single Agent Execution**: Always use either Cline OR Qwen Code, never both, to avoid conflicting recommendations
3. **Minimal GitLab API**: Clone repositories locally and use Git CLI for most operations; GitLab API only for MR operations
4. **Repository Cloning Strategy**: Clone entire MR source branch for each review to enable full context analysis
5. **Parallel Execution**: Cline supports 5 parallel tasks, Qwen supports 3 parallel tasks
6. **Smart MR Creation**: Separate documentation commits, fix MRs, and refactoring MRs based on impact classification

---

## Reference Documents

- [PRD](/docs/PRD.md) - Product Requirements Document
- [Architecture](/docs/ARCHITECTURE_RU.md) - Detailed architecture documentation
- [Deployment Guide](/docs/DEPLOYMENT_GUIDE_RU.md) - Deployment instructions
- [Summary](/SUMMARY.md) - Project completion summary

