# Technical Context

## Technology Stack

### Backend Framework

- **FastAPI 0.104+**: Modern async web framework
- **Python 3.11**: Programming language
- **Uvicorn**: ASGI server
- **Pydantic 2.5+**: Data validation and settings

### CLI Agents

- **Cline CLI**: Latest stable version (npm global package)
  - Model: DeepSeek V3.1 Terminus
  - Parallel tasks: 5
  
- **Qwen Code CLI**: Latest stable version (npm global package)
  - Model: Qwen3-Coder-32B
  - Parallel tasks: 3

### Models (Pre-deployed)

- **DeepSeek V3.1 Terminus**: Via OpenAI-compatible API
- **Qwen3-Coder-32B**: Via OpenAI-compatible API

### Git Integration

- **Git CLI**: System git installation
- **GitPython 3.1.40**: Python Git library (for advanced operations)
- **python-gitlab 4.4.0**: GitLab API client

### HTTP Client

- **httpx 0.25.1**: Async HTTP client

### Logging

- **loguru 0.7.2**: Structured logging

### Testing

- **pytest 7.4.3**: Testing framework
- **pytest-asyncio 0.21.1**: Async test support
- **pytest-httpx 0.26.0**: HTTP mocking

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for CLI tools)
- Git
- Docker and Docker Compose (for deployment)

### Environment Variables

Required environment variables (see `env.example.annotated`):

```bash
# Application
VERSION=2.0.0
LOG_LEVEL=INFO

# Model API (OpenAI-compatible)
MODEL_API_URL=https://api.example.com/v1
MODEL_API_KEY=your-api-key
DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
QWEN3_MODEL_NAME=qwen3-coder-32b

# CLI Configuration
DEFAULT_CLI_AGENT=CLINE  # CLINE or QWEN_CODE
CLINE_PARALLEL_TASKS=5
QWEN_PARALLEL_TASKS=3
REVIEW_TIMEOUT=300

# GitLab Configuration
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your-gitlab-token

# Paths
WORK_DIR=/tmp/review
PROMPTS_PATH=prompts
DEFAULT_RULES_PATH=rules/java-spring-boot
DEFAULT_LANGUAGE=java

# Optional: Confluence Rules
CONFLUENCE_RULES_ENABLED=false
CONFLUENCE_URL=
CONFLUENCE_API_TOKEN=

# Optional: MCP RAG
MCP_RAG_ENABLED=false
MCP_SERVER_URL=
```

### Installation

```bash
# Python dependencies
pip install -r requirements.txt

# CLI tools (global npm packages)
npm install -g @cline/cli @qwen-code/qwen-code

# Verify installation
cline --version
qwen-code --version
```

## Development Tools

### Code Quality

- Python type hints throughout
- Pydantic models for validation
- Structured logging with correlation IDs

### Testing

- Unit tests in `tests/` directory
- Health check tests
- Rules loader tests
- Refactoring classifier tests

### Debugging

- **Debug Mode**: Set `DEBUG_MODE=true` to save CLI output
- **Interactive Shell**: `docker exec -it code-review-api /bin/bash`
- **Correlation IDs**: Track requests through entire flow
- **Structured Logs**: JSON format for parsing

## Deployment

### Docker Compose (Development/Testing)

```bash
docker-compose up -d
```

### Kubernetes (Production)

- Deployment manifests in `deployment/kubernetes/`
- HPA for auto-scaling (3-20 replicas)
- ConfigMap for prompts and rules
- Secrets for sensitive data

### Air-Gap Transfer

- Docker image export/import
- npm package archives
- Python package repository
- See `docs/AIR_GAP_TRANSFER.md`

## Technical Constraints

### Resource Limits

- **Max MR size**: 10,000 lines
- **Review timeout**: 5 minutes
- **Parallel reviews**: 10 per pod
- **Memory**: Node.js heap size configurable

### Performance Targets

- Average review time: <5 minutes
- API response time: p95 < 30 seconds
- Throughput: ~100 reviews/hour on 3 pods

### Scalability

- **Horizontal scaling**: Kubernetes HPA
- **Min replicas**: 3
- **Max replicas**: 20
- **Autoscaling triggers**: CPU >70%, Memory >80%

## Dependencies

### Python Packages

See `requirements.txt` for complete list:
- FastAPI ecosystem (fastapi, uvicorn, pydantic)
- HTTP client (httpx)
- GitLab integration (python-gitlab, GitPython)
- Logging (loguru)
- Testing (pytest, pytest-asyncio)

### System Dependencies

- Git CLI (for repository operations)
- Node.js runtime (for CLI tools)
- Docker (for containerization)

## Tool Usage Patterns

### CLI Execution

- Subprocess execution via `asyncio.create_subprocess_exec`
- Working directory set to cloned repository
- Timeout handling via `asyncio.wait_for`
- Output parsing from stdout/stderr

### Git Operations

- Clone via Git CLI: `git clone --branch <branch> <url>`
- Diff via Git CLI: `git diff <target_branch>`
- Commit via Git CLI: `git commit -m <message>`
- Push via Git CLI: `git push origin <branch>`

### GitLab API

- Minimal usage: Only for MR metadata, clone URL, creating MRs, posting comments
- Rate limiting handled via retry logic
- Idempotent operations for MR creation

## Environment Template

```bash
# .env.template
MODEL_API_URL=https://your-api.example.com/v1
MODEL_API_KEY=your-api-key
DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
QWEN3_MODEL_NAME=qwen3-coder-32b
GITLAB_URL=https://gitlab.example.com
GITLAB_TOKEN=your-gitlab-token
DEFAULT_CLI_AGENT=CLINE
LOG_LEVEL=INFO
WORK_DIR=/tmp/review
```

## CI/CD Integration

- GitLab CI/CD for testing
- Docker image build and push
- Kubernetes deployment automation
- Health check monitoring

