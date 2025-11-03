FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including Node.js and Git
RUN apt-get update && apt-get install -y \
    curl \
    git \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_18.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Verify Node.js and npm installation
RUN node --version && npm --version

# Install CLI tools globally
# Option 1: Online installation (requires internet)
# Uncomment if you have internet access during build
# RUN npm install -g @cline/cli
# RUN npm install -g @qwen-code/qwen-code

# Option 2: Offline installation (for air-gapped environments)
# Place *.tgz packages in offline-packages/ directory before build
COPY offline-packages/*.tgz /tmp/npm-packages/ 2>/dev/null || echo "No offline packages found, skipping..."
RUN if [ -f /tmp/npm-packages/*.tgz ]; then \
        npm install -g /tmp/npm-packages/cline-*.tgz && \
        npm install -g /tmp/npm-packages/qwen-code-*.tgz && \
        rm -rf /tmp/npm-packages; \
    else \
        echo "WARNING: CLI tools not installed. System will not work properly!"; \
    fi

# Verify CLI installation
RUN which cline && cline --version || echo "ERROR: Cline CLI not found!"
RUN which qwen-code && qwen-code --version || echo "ERROR: Qwen Code CLI not found!"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Copy prompts and rules
COPY prompts/ ./prompts/
COPY rules/ ./rules/

# Create work directory for repository clones
RUN mkdir -p /tmp/review

# Create user and set permissions
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app \
    && chown -R appuser:appuser /tmp/review

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5)"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
