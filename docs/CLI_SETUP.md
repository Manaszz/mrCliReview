# CLI Setup Guide

## Overview

This guide explains how to set up Cline CLI and Qwen Code CLI for the code review system, including installation, configuration, and troubleshooting.

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+) or macOS 12+
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **Network**: Access to model API endpoints

### Software Requirements

- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher
- **Python**: 3.11 or higher
- **Git**: v2.30 or higher

---

## Installing Cline CLI

### Method 1: npm Global Install (Recommended)

```bash
# Install Cline CLI globally
npm install -g @cline/cli

# Verify installation
cline --version
```

Expected output:
```
cline version 2.1.0
```

---

### Method 2: From Source

```bash
# Clone repository
git clone https://github.com/cline-dev/cline-cli.git
cd cline-cli

# Install dependencies
npm install

# Build
npm run build

# Link globally
npm link

# Verify
cline --version
```

---

### Configuration

Create Cline configuration file:

```bash
mkdir -p ~/.config/cline
cat > ~/.config/cline/config.json << 'EOF'
{
  "model": {
    "provider": "openai-compatible",
    "baseURL": "https://your-model-api.example.com/v1",
    "apiKey": "${MODEL_API_KEY}",
    "model": "deepseek-v3.1-terminus"
  },
  "parallelTasks": 5,
  "timeout": 300000,
  "logging": {
    "level": "info",
    "file": "/var/log/cline/cline.log"
  }
}
EOF
```

---

### Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
export MODEL_API_KEY="your-api-key-here"
export CLINE_CONFIG_PATH="$HOME/.config/cline/config.json"
```

---

## Installing Qwen Code CLI

### Method 1: npm Global Install (Recommended)

```bash
# Install Qwen Code CLI globally
npm install -g @qwen-code/qwen-code

# Verify installation
qwen-code --version
```

Expected output:
```
qwen-code version 1.5.0
```

---

### Method 2: From Source

```bash
# Clone repository
git clone https://github.com/QwenLM/Qwen-Code-CLI.git
cd Qwen-Code-CLI

# Install dependencies
npm install

# Build
npm run build

# Link globally
npm link

# Verify
qwen-code --version
```

---

### Configuration

Create Qwen Code configuration file:

```bash
mkdir -p ~/.config/qwen-code
cat > ~/.config/qwen-code/config.json << 'EOF'
{
  "model": {
    "provider": "openai-compatible",
    "baseURL": "https://your-model-api.example.com/v1",
    "apiKey": "${MODEL_API_KEY}",
    "model": "qwen3-coder-32b"
  },
  "parallelTasks": 3,
  "timeout": 180000,
  "logging": {
    "level": "info",
    "file": "/var/log/qwen-code/qwen-code.log"
  }
}
EOF
```

---

## Model API Configuration

### OpenAI Compatible API

Both CLIs use OpenAI-compatible API endpoints. Configure your model deployment:

#### DeepSeek V3.1 Terminus (for Cline)

```json
{
  "baseURL": "https://your-api.example.com/v1",
  "model": "deepseek-v3.1-terminus",
  "apiKey": "${MODEL_API_KEY}"
}
```

#### Qwen3-Coder-32B (for Qwen Code)

```json
{
  "baseURL": "https://your-api.example.com/v1",
  "model": "qwen3-coder-32b",
  "apiKey": "${MODEL_API_KEY}"
}
```

---

### Testing Model Connection

```bash
# Test Cline connection
cline --test-connection

# Test Qwen Code connection
qwen-code --test-connection
```

Expected output:
```
✓ Connected to model API
✓ Model: deepseek-v3.1-terminus
✓ Status: operational
```

---

## Docker Installation

### Dockerfile

The Dockerfile includes CLI installation:

```dockerfile
FROM python:3.11-slim

# Install Node.js
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install CLIs
RUN npm install -g @cline/cli@latest
RUN npm install -g @qwen-code/qwen-code@latest

# Verify installations
RUN cline --version
RUN qwen-code --version

# Copy configuration
COPY config/cline-config.json /root/.config/cline/config.json
COPY config/qwen-config.json /root/.config/qwen-code/config.json

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### docker-compose.yml

```yaml
services:
  review-api:
    build: .
    environment:
      - MODEL_API_KEY=${MODEL_API_KEY}
      - MODEL_API_URL=${MODEL_API_URL}
      - DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
      - QWEN3_MODEL_NAME=qwen3-coder-32b
    volumes:
      - ./prompts:/app/prompts:ro
      - ./rules:/app/rules:ro
      - ./logs:/app/logs
    ports:
      - "8000:8000"
```

---

## Configuration Options

### Cline CLI Options

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `model.provider` | Model provider type | `openai-compatible` | `CLINE_MODEL_PROVIDER` |
| `model.baseURL` | API base URL | - | `CLINE_MODEL_BASE_URL` |
| `model.apiKey` | API key | - | `CLINE_API_KEY` or `MODEL_API_KEY` |
| `model.model` | Model name | `deepseek-v3.1-terminus` | `CLINE_MODEL_NAME` |
| `parallelTasks` | Max parallel tasks | `5` | `CLINE_PARALLEL_TASKS` |
| `timeout` | Request timeout (ms) | `300000` | `CLINE_TIMEOUT` |
| `maxContextSize` | Max context tokens | `100000` | `CLINE_MAX_CONTEXT` |

---

### Qwen Code CLI Options

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `model.provider` | Model provider type | `openai-compatible` | `QWEN_MODEL_PROVIDER` |
| `model.baseURL` | API base URL | - | `QWEN_MODEL_BASE_URL` |
| `model.apiKey` | API key | - | `QWEN_API_KEY` or `MODEL_API_KEY` |
| `model.model` | Model name | `qwen3-coder-32b` | `QWEN_MODEL_NAME` |
| `parallelTasks` | Max parallel tasks | `3` | `QWEN_PARALLEL_TASKS` |
| `timeout` | Request timeout (ms) | `180000` | `QWEN_TIMEOUT` |

---

## Usage Examples

### Basic Code Review with Cline

```bash
# Clone repository
git clone https://gitlab.example.com/myproject.git
cd myproject

# Checkout branch
git checkout feature/new-feature

# Run review
cline review \
  --prompt prompts/cline/error_detection.md \
  --files "src/**/*.java" \
  --output review-results.json
```

---

### Basic Code Review with Qwen Code

```bash
# Same setup
cd myproject
git checkout feature/new-feature

# Run review
qwen-code review \
  --prompt prompts/qwen/error_detection.md \
  --files "src/**/*.java" \
  --output review-results.json
```

---

### Advanced Usage

#### Parallel Task Execution (Cline)

```bash
# Run multiple review types in parallel
cline review \
  --prompts prompts/cline/error_detection.md,prompts/cline/security_audit.md \
  --files "src/**/*.java" \
  --parallel 5 \
  --output reviews/
```

#### Custom Context (Qwen Code)

```bash
# Provide additional context
qwen-code review \
  --prompt prompts/qwen/best_practices.md \
  --files "src/**/*.java" \
  --context "JIRA-123: Implement user authentication" \
  --rules .project-rules/ \
  --output review-results.json
```

---

## Troubleshooting

### Issue: CLI Not Found

**Symptoms**:
```bash
cline --version
# bash: cline: command not found
```

**Solutions**:
1. **Check npm global path**:
```bash
npm config get prefix
# Should be in your PATH
```

2. **Add to PATH**:
```bash
export PATH="$(npm config get prefix)/bin:$PATH"
```

3. **Reinstall globally**:
```bash
npm uninstall -g @cline/cli
npm install -g @cline/cli
```

---

### Issue: Model Connection Failed

**Symptoms**:
```
Error: Connection to model API failed
Status: 401 Unauthorized
```

**Solutions**:
1. **Check API key**:
```bash
echo $MODEL_API_KEY
# Should not be empty
```

2. **Test API manually**:
```bash
curl -H "Authorization: Bearer $MODEL_API_KEY" \
  https://your-api.example.com/v1/models
```

3. **Check baseURL**:
```bash
# Verify URL in config
cat ~/.config/cline/config.json | jq '.model.baseURL'
```

---

### Issue: Timeout Errors

**Symptoms**:
```
Error: Request timeout after 300000ms
```

**Solutions**:
1. **Increase timeout**:
```json
{
  "timeout": 600000  // 10 minutes
}
```

2. **Reduce scope**:
```bash
# Review fewer files at once
cline review --files "src/main/java/Service.java"
```

3. **Check model load**:
- Model may be under heavy load
- Try again later or use alternative model

---

### Issue: Out of Memory

**Symptoms**:
```
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
```

**Solutions**:
1. **Increase Node.js memory**:
```bash
export NODE_OPTIONS="--max-old-space-size=4096"
```

2. **Process files in batches**:
```bash
# Split into smaller batches
for file in src/main/java/*.java; do
  cline review --files "$file" --output "reviews/$(basename $file).json"
done
```

---

### Issue: Invalid Prompt Format

**Symptoms**:
```
Error: Failed to parse prompt file
```

**Solutions**:
1. **Verify markdown syntax**:
```bash
# Check for syntax errors
markdown-lint prompts/cline/error_detection.md
```

2. **Check variable substitution**:
```markdown
# Valid
{repo_path}

# Invalid
{{repo_path}}
{repo path}
```

---

## Performance Tuning

### Parallel Tasks

#### Cline (5 parallel tasks)
- **Optimal for**: Comprehensive reviews (ALL type)
- **Resource usage**: High (CPU + memory)
- **Review time**: ~5 minutes for 50 files

#### Qwen Code (3 parallel tasks)
- **Optimal for**: Fast focused reviews
- **Resource usage**: Medium
- **Review time**: ~3 minutes for 30 files

---

### Context Size

Larger context = better understanding but slower processing:

```json
{
  "maxContextSize": 50000  // Faster, less context
  "maxContextSize": 100000 // Slower, more context (default)
}
```

---

### Caching

Enable repository caching for faster subsequent reviews:

```json
{
  "cache": {
    "enabled": true,
    "path": "/tmp/cline-cache",
    "ttl": 3600
  }
}
```

---

## Air-Gap Installation

For isolated environments without internet access:

### Preparation (Connected Environment)

```bash
# Download CLI packages
npm pack @cline/cli
npm pack @qwen-code/qwen-code

# Download dependencies
cd cline-cli
npm install
cd node_modules
tar -czf cline-dependencies.tar.gz *

cd ../../qwen-code
npm install
cd node_modules
tar -czf qwen-dependencies.tar.gz *
```

### Installation (Isolated Environment)

```bash
# Transfer packages
# - cline-cli-2.1.0.tgz
# - qwen-code-1.5.0.tgz
# - *-dependencies.tar.gz

# Install Cline
tar -xzf cline-cli-2.1.0.tgz
cd package
tar -xzf ../cline-dependencies.tar.gz -C node_modules/
npm link

# Install Qwen Code
tar -xzf qwen-code-1.5.0.tgz
cd package
tar -xzf ../qwen-dependencies.tar.gz -C node_modules/
npm link
```

---

## Monitoring

### Log Files

```bash
# Cline logs
tail -f /var/log/cline/cline.log

# Qwen Code logs
tail -f /var/log/qwen-code/qwen-code.log

# Review API logs
docker logs -f review-api
```

---

### Health Checks

```bash
# Check CLI health
cline health
qwen-code health

# Check model API health
curl https://your-api.example.com/v1/health
```

---

## Upgrades

### Upgrading Cline CLI

```bash
# Check current version
cline --version

# Upgrade to latest
npm update -g @cline/cli

# Verify upgrade
cline --version
```

### Upgrading Qwen Code CLI

```bash
# Check current version
qwen-code --version

# Upgrade to latest
npm update -g @qwen-code/qwen-code

# Verify upgrade
qwen-code --version
```

---

## References

- [Cline CLI Documentation](https://docs.cline.bot)
- [Qwen Code Documentation](https://qwenlm.github.io/qwen-code)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Node.js Documentation](https://nodejs.org/docs/)

---

**Last Updated**: 2025-11-03  
**Version**: 2.0.0


