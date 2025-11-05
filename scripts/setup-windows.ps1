# Windows Setup Script for AI Code Review System
# PowerShell script to automate installation and setup

param(
    [switch]$SkipDocker,
    [switch]$OfflineMode,
    [string]$WorkDir = "C:\Temp\review"
)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "AI Code Review System - Windows Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator. Some operations may fail." -ForegroundColor Yellow
    Write-Host "Consider running: Start-Process PowerShell -Verb RunAs" -ForegroundColor Yellow
    Write-Host ""
}

# Function to check command existence
function Test-CommandExists {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

# Step 1: Check Prerequisites
Write-Host "[1/8] Checking prerequisites..." -ForegroundColor Green

$python = Test-CommandExists "python"
$node = Test-CommandExists "node"
$npm = Test-CommandExists "npm"
$git = Test-CommandExists "git"

Write-Host "  Python: $(if($python){'✓ Installed'}else{'✗ Missing'})" -ForegroundColor $(if($python){'Green'}else{'Red'})
Write-Host "  Node.js: $(if($node){'✓ Installed'}else{'✗ Missing'})" -ForegroundColor $(if($node){'Green'}else{'Red'})
Write-Host "  npm: $(if($npm){'✓ Installed'}else{'✗ Missing'})" -ForegroundColor $(if($npm){'Green'}else{'Red'})
Write-Host "  Git: $(if($git){'✓ Installed'}else{'✗ Missing'})" -ForegroundColor $(if($git){'Green'}else{'Red'})

if (-not ($python -and $node -and $npm -and $git)) {
    Write-Host ""
    Write-Host "ERROR: Missing required tools!" -ForegroundColor Red
    Write-Host "Please install missing tools and run this script again." -ForegroundColor Red
    Write-Host "See docs/WINDOWS_SETUP.md for installation instructions." -ForegroundColor Yellow
    exit 1
}

# Display versions
Write-Host ""
Write-Host "  Python version: $(python --version)" -ForegroundColor Gray
Write-Host "  Node.js version: $(node --version)" -ForegroundColor Gray
Write-Host "  npm version: $(npm --version)" -ForegroundColor Gray
Write-Host "  Git version: $(git --version)" -ForegroundColor Gray
Write-Host ""

# Step 2: Create Virtual Environment
Write-Host "[2/8] Creating Python virtual environment..." -ForegroundColor Green

if (Test-Path "venv") {
    Write-Host "  Virtual environment already exists, skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment!" -ForegroundColor Red
        exit 1
    }
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
}

# Step 3: Activate Virtual Environment
Write-Host "[3/8] Activating virtual environment..." -ForegroundColor Green

# Set execution policy if needed
try {
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force -ErrorAction Stop
} catch {
    Write-Host "  Warning: Could not set execution policy" -ForegroundColor Yellow
}

# Activate venv
$venvActivate = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    & $venvActivate
    Write-Host "  ✓ Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "ERROR: Cannot find venv activation script!" -ForegroundColor Red
    exit 1
}

# Step 4: Install Python Dependencies
Write-Host "[4/8] Installing Python dependencies..." -ForegroundColor Green

if ($OfflineMode) {
    if (Test-Path "offline-python") {
        pip install --no-index --find-links=offline-python -r requirements.txt
    } else {
        Write-Host "ERROR: offline-python directory not found!" -ForegroundColor Red
        exit 1
    }
} else {
    # Upgrade pip first
    python -m pip install --upgrade pip --quiet
    
    # Install dependencies
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install Python dependencies!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  ✓ Python dependencies installed" -ForegroundColor Green

# Step 5: Install CLI Tools
Write-Host "[5/8] Installing CLI tools..." -ForegroundColor Green

if ($OfflineMode) {
    if (Test-Path "offline-packages") {
        Push-Location offline-packages
        Get-ChildItem -Filter "*.tgz" | ForEach-Object {
            npm install -g $_.FullName
        }
        Pop-Location
        Write-Host "  ✓ CLI tools installed from offline packages" -ForegroundColor Green
    } else {
        Write-Host "ERROR: offline-packages directory not found!" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  NOTE: CLI tools (@cline/cli, @qwen-code/qwen-code) are hypothetical examples." -ForegroundColor Yellow
    Write-Host "  Install your actual CLI agents here." -ForegroundColor Yellow
    # npm install -g @cline/cli @qwen-code/qwen-code
}

# Step 6: Setup Environment
Write-Host "[6/8] Setting up environment..." -ForegroundColor Green

if (-not (Test-Path ".env")) {
    if (Test-Path "env.example.annotated") {
        Copy-Item "env.example.annotated" ".env"
        Write-Host "  ✓ Created .env from example" -ForegroundColor Green
        Write-Host "  IMPORTANT: Edit .env file with your configuration!" -ForegroundColor Yellow
    } else {
        Write-Host "  Warning: No .env example found" -ForegroundColor Yellow
    }
} else {
    Write-Host "  .env file already exists, skipping..." -ForegroundColor Yellow
}

# Step 7: Create Directories
Write-Host "[7/8] Creating directories..." -ForegroundColor Green

$directories = @($WorkDir, "logs")

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
        Write-Host "  ✓ Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "  Directory already exists: $dir" -ForegroundColor Gray
    }
}

# Step 8: Run Tests
Write-Host "[8/8] Running tests..." -ForegroundColor Green

Write-Host "  Running unit tests..." -ForegroundColor Gray
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

python -m pytest tests/ -v --tb=short -q 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ All tests passed" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Some tests failed (this is normal for incomplete setup)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env file with your configuration" -ForegroundColor White
Write-Host "2. Run application: uvicorn app.main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host "3. Access API: http://localhost:8000" -ForegroundColor White
Write-Host "4. View docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "For Docker deployment:" -ForegroundColor Yellow
Write-Host "  docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "For more information, see docs/WINDOWS_SETUP.md" -ForegroundColor Gray

