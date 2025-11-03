# Air-Gap Transfer Guide

## Overview

This guide provides step-by-step instructions for deploying the code review system in an air-gapped (isolated) environment without internet access.

---

## Prerequisites

### Connected Environment Requirements
- Internet access
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- npm 9+
- 20GB free disk space for archives

### Isolated Environment Requirements
- Docker and Docker Compose installed
- Access to internal model API
- Access to internal GitLab instance
- 20GB free disk space
- Internal container registry (optional but recommended)

---

## Phase 1: Preparation (Connected Environment)

### Step 1: Export Docker Images

```bash
# Navigate to project directory
cd code-review-system

# Build Docker image
docker-compose build

# Export review API image
docker save -o review-api.tar review-api:latest

# Export base Python image (if not available in isolated environment)
docker pull python:3.11-slim
docker save -o python-3.11-slim.tar python:3.11-slim

# Verify archives
ls -lh *.tar
```

Expected output:
```
-rw-r--r-- 1 user user 1.2G Nov  3 10:00 review-api.tar
-rw-r--r-- 1 user user 150M Nov  3 10:05 python-3.11-slim.tar
```

---

### Step 2: Download npm Packages

```bash
# Create packages directory
mkdir -p air-gap-packages/npm

# Download Cline CLI
cd air-gap-packages/npm
npm pack @cline/cli
npm pack @qwen-code/qwen-code

# Download dependencies
mkdir cline-deps qwen-deps

# Cline dependencies
cd cline-deps
npm install @cline/cli --no-save
tar -czf ../cline-dependencies.tar.gz node_modules/
cd ..

# Qwen Code dependencies
cd qwen-deps
npm install @qwen-code/qwen-code --no-save
tar -czf ../qwen-dependencies.tar.gz node_modules/
cd ../..

# Verify packages
ls -lh air-gap-packages/npm/
```

---

### Step 3: Create Python Offline Repository

```bash
# Create pip packages directory
mkdir -p air-gap-packages/pip

# Download all Python dependencies
pip download \
  -r requirements.txt \
  -d air-gap-packages/pip/

# Verify packages
ls -lh air-gap-packages/pip/ | wc -l
# Should show 20-30 packages
```

---

### Step 4: Archive Application Files

```bash
# Create archive of application code
tar -czf code-review-app.tar.gz \
  --exclude='.git' \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='venv' \
  --exclude='node_modules' \
  app/ \
  prompts/ \
  rules/ \
  docs/ \
  tests/ \
  docker-compose.yml \
  Dockerfile \
  requirements.txt \
  .env.example \
  README.md
```

---

### Step 5: Create Transfer Package

```bash
# Create final transfer directory
mkdir -p air-gap-transfer

# Move all artifacts
mv review-api.tar air-gap-transfer/
mv python-3.11-slim.tar air-gap-transfer/
mv code-review-app.tar.gz air-gap-transfer/
mv air-gap-packages air-gap-transfer/

# Create installation script
cat > air-gap-transfer/install.sh << 'EOF'
#!/bin/bash
set -e

echo "=== Code Review System Air-Gap Installation ==="

# Load Docker images
echo "Loading Docker images..."
docker load -i review-api.tar
docker load -i python-3.11-slim.tar

# Extract application
echo "Extracting application files..."
tar -xzf code-review-app.tar.gz

# Install npm packages
echo "Installing CLI tools..."
npm install -g air-gap-packages/npm/cline-cli-*.tgz
npm install -g air-gap-packages/npm/qwen-code-*.tgz

# Verify installations
cline --version
qwen-code --version

echo "=== Installation Complete ==="
echo "Next steps:"
echo "1. Configure .env file"
echo "2. Run: docker-compose up -d"
echo "3. Check logs: docker-compose logs -f"
EOF

chmod +x air-gap-transfer/install.sh

# Create README
cat > air-gap-transfer/README.txt << 'EOF'
Code Review System - Air-Gap Transfer Package
==============================================

Contents:
- review-api.tar: Docker image for review API
- python-3.11-slim.tar: Base Python Docker image
- code-review-app.tar.gz: Application code and configuration
- air-gap-packages/: npm and pip packages
- install.sh: Installation script

Installation:
1. Transfer this entire directory to isolated environment
2. Run: ./install.sh
3. Follow post-installation instructions

For detailed instructions, see docs/AIR_GAP_TRANSFER.md
EOF

# Create manifest
cat > air-gap-transfer/MANIFEST.txt << 'EOF'
Package Manifest - Generated $(date)
====================================

Docker Images:
- review-api:latest
- python:3.11-slim

NPM Packages:
- @cline/cli@2.1.0
- @qwen-code/qwen-code@1.5.0

Python Packages:
$(ls -1 air-gap-packages/pip/ | head -20)
...

Total Size: $(du -sh air-gap-transfer | cut -f1)
EOF

# Create final archive
cd ..
tar -czf code-review-air-gap-$(date +%Y%m%d).tar.gz air-gap-transfer/

echo "=== Package Ready ==="
ls -lh code-review-air-gap-*.tar.gz
```

---

## Phase 2: Transfer

### Physical Transfer Options

#### Option 1: External Drive
```bash
# Copy to USB drive
cp code-review-air-gap-*.tar.gz /media/usb-drive/

# Eject safely
sync
umount /media/usb-drive
```

#### Option 2: Internal File Transfer System
```bash
# Upload to internal transfer system
# (Specific to your organization's process)
```

#### Option 3: CD/DVD
```bash
# For smaller packages
brasero code-review-air-gap-*.tar.gz
```

---

## Phase 3: Installation (Isolated Environment)

### Step 1: Extract Transfer Package

```bash
# Transfer file to isolated server
scp code-review-air-gap-20251103.tar.gz isolated-server:/opt/

# SSH to isolated server
ssh isolated-server

# Extract package
cd /opt
tar -xzf code-review-air-gap-20251103.tar.gz
cd air-gap-transfer
```

---

### Step 2: Run Installation Script

```bash
# Make script executable (if needed)
chmod +x install.sh

# Run installation
sudo ./install.sh
```

Expected output:
```
=== Code Review System Air-Gap Installation ===
Loading Docker images...
Loaded image: review-api:latest
Loaded image: python:3.11-slim
Extracting application files...
Installing CLI tools...
/usr/local/bin/cline -> ...
/usr/local/bin/qwen-code -> ...
cline version 2.1.0
qwen-code version 1.5.0
=== Installation Complete ===
```

---

### Step 3: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit configuration
nano .env
```

Required configuration for isolated environment:

```env
# Model API (internal endpoint)
MODEL_API_URL=https://internal-model-api.company.local/v1
MODEL_API_KEY=your-internal-api-key

# Model names (must be available in internal deployment)
DEEPSEEK_MODEL_NAME=deepseek-v3.1-terminus
QWEN3_MODEL_NAME=qwen3-coder-32b

# GitLab (internal instance)
GITLAB_URL=https://gitlab.company.local
GITLAB_TOKEN=your-gitlab-token

# CLI configuration
DEFAULT_CLI_AGENT=CLINE
CLINE_PARALLEL_TASKS=5
QWEN_PARALLEL_TASKS=3

# Application
LOG_LEVEL=INFO
REVIEW_TIMEOUT=300
```

---

### Step 4: Configure CLIs

```bash
# Configure Cline CLI
mkdir -p ~/.config/cline
cat > ~/.config/cline/config.json << EOF
{
  "model": {
    "provider": "openai-compatible",
    "baseURL": "https://internal-model-api.company.local/v1",
    "apiKey": "\${MODEL_API_KEY}",
    "model": "deepseek-v3.1-terminus"
  },
  "parallelTasks": 5,
  "timeout": 300000
}
EOF

# Configure Qwen Code CLI
mkdir -p ~/.config/qwen-code
cat > ~/.config/qwen-code/config.json << EOF
{
  "model": {
    "provider": "openai-compatible",
    "baseURL": "https://internal-model-api.company.local/v1",
    "apiKey": "\${MODEL_API_KEY}",
    "model": "qwen3-coder-32b"
  },
  "parallelTasks": 3,
  "timeout": 180000
}
EOF
```

---

### Step 5: Start Services

```bash
# Start with docker-compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f review-api
```

Expected output:
```
review-api_1  | INFO:     Started server process
review-api_1  | INFO:     Waiting for application startup.
review-api_1  | INFO:     Application startup complete.
review-api_1  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

### Step 6: Verify Installation

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Expected response
{
  "status": "healthy",
  "version": "2.0.0",
  "cline_available": true,
  "qwen_available": true,
  "model_api_connected": true
}

# Test CLI connections
cline --test-connection
qwen-code --test-connection
```

---

## Phase 4: Internal Container Registry (Optional)

For easier management, push images to internal registry:

### Setup

```bash
# Tag images for internal registry
docker tag review-api:latest registry.company.local/code-review/review-api:2.0.0
docker tag review-api:latest registry.company.local/code-review/review-api:latest

# Push to registry
docker push registry.company.local/code-review/review-api:2.0.0
docker push registry.company.local/code-review/review-api:latest
```

### Update docker-compose.yml

```yaml
services:
  review-api:
    image: registry.company.local/code-review/review-api:latest
    # Remove 'build' directive
    environment:
      - MODEL_API_KEY=${MODEL_API_KEY}
      # ... other env vars
```

---

## Troubleshooting

### Issue: Docker Load Failed

**Symptoms**:
```
Error loading image: unexpected EOF
```

**Solutions**:
1. **Verify archive integrity**:
```bash
tar -tzf review-api.tar | head
```

2. **Re-export image**:
```bash
# In connected environment
docker save review-api:latest | gzip > review-api.tar.gz
```

3. **Check disk space**:
```bash
df -h /var/lib/docker
```

---

### Issue: npm Install Failed

**Symptoms**:
```
npm ERR! network request failed
```

**Solutions**:
1. **Install from local tarball**:
```bash
npm install -g /path/to/cline-cli-2.1.0.tgz
```

2. **Extract dependencies manually**:
```bash
cd /usr/local/lib/node_modules
tar -xzf /path/to/cline-dependencies.tar.gz
```

---

### Issue: Python Packages Missing

**Symptoms**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solutions**:
1. **Install from offline repository**:
```bash
pip install --no-index --find-links=/path/to/air-gap-packages/pip/ -r requirements.txt
```

2. **Verify packages downloaded**:
```bash
ls -1 air-gap-packages/pip/*.whl | wc -l
```

---

### Issue: Model API Connection Failed

**Symptoms**:
```
Error: Failed to connect to model API
```

**Solutions**:
1. **Test internal API**:
```bash
curl -H "Authorization: Bearer $MODEL_API_KEY" \
  https://internal-model-api.company.local/v1/models
```

2. **Check network access**:
```bash
telnet internal-model-api.company.local 443
```

3. **Verify certificates** (if HTTPS):
```bash
openssl s_client -connect internal-model-api.company.local:443
```

---

## Updates and Patches

### Updating in Air-Gap Environment

1. **In connected environment**:
```bash
# Pull latest changes
git pull

# Rebuild image
docker-compose build

# Create update package
docker save -o review-api-update.tar review-api:latest
tar -czf update-$(date +%Y%m%d).tar.gz \
  review-api-update.tar \
  app/ \
  prompts/ \
  rules/ \
  requirements.txt
```

2. **Transfer update package**

3. **In isolated environment**:
```bash
# Extract update
tar -xzf update-20251103.tar.gz

# Load new image
docker load -i review-api-update.tar

# Stop current services
docker-compose down

# Start with new image
docker-compose up -d
```

---

## Security Considerations

### Verification

1. **Checksum verification**:
```bash
# In connected environment
sha256sum code-review-air-gap-*.tar.gz > checksums.txt

# In isolated environment
sha256sum -c checksums.txt
```

2. **GPG signature** (if applicable):
```bash
# Sign package
gpg --detach-sign code-review-air-gap-*.tar.gz

# Verify signature
gpg --verify code-review-air-gap-*.tar.gz.sig
```

---

### Access Control

- Restrict access to installation directory
- Use secure credentials for GitLab and model API
- Implement least privilege principles

```bash
# Secure installation directory
chmod 750 /opt/code-review
chown root:code-review /opt/code-review

# Secure env file
chmod 600 .env
```

---

## Backup and Recovery

### Backup

```bash
# Backup configuration
tar -czf backup-config-$(date +%Y%m%d).tar.gz \
  .env \
  docker-compose.yml \
  ~/.config/cline/ \
  ~/.config/qwen-code/

# Backup data
docker-compose exec review-api tar -czf - /app/logs > backup-logs-$(date +%Y%m%d).tar.gz
```

### Recovery

```bash
# Restore configuration
tar -xzf backup-config-20251103.tar.gz

# Restart services
docker-compose restart
```

---

## References

- [Docker Save/Load Documentation](https://docs.docker.com/engine/reference/commandline/save/)
- [npm Offline Installation](https://docs.npmjs.com/cli/v9/commands/npm-install)
- [pip Offline Installation](https://pip.pypa.io/en/stable/cli/pip_download/)

---

**Last Updated**: 2025-11-03  
**Version**: 2.0.0


