#!/usr/bin/env powershell
# DREAM.AI Production Setup Verification Script
# Run this to verify all files are in place and ready for deployment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DREAM.AI Production Setup Verification" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Get-Location
$errors = @()
$warnings = @()
$successes = @()

# Check Docker and Docker Compose
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    $successes += "[OK] Docker installed: $dockerVersion"
} catch {
    $errors += "[FAIL] Docker not found. Install from https://www.docker.com/"
}

try {
    $composeVersion = docker-compose --version
    $successes += "[OK] Docker Compose installed: $composeVersion"
} catch {
    $errors += "[FAIL] Docker Compose not found. Install it."
}

Write-Host ""
Write-Host "Checking required files..." -ForegroundColor Yellow

# Define required files
$requiredFiles = @(
    "Dockerfile.prod",
    "docker-compose.yml",
    "nginx.conf",
    ".env.prod",
    "k8s-deployment.yaml",
    ".dockerignore",
    "dreamai\frontend\Dockerfile",
    "dreamai\requirements.txt",
    "dreamai\backend\api\app.py",
    "dreamai\backend\api\websocket_stream.py",
    "dreamai\backend\api\orchestrator_routes.py"
)

foreach ($file in $requiredFiles) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        $successes += "[OK] Found: $file"
    } else {
        $errors += "[FAIL] Missing: $file"
    }
}

Write-Host ""
Write-Host "Checking file contents..." -ForegroundColor Yellow

# Check docker-compose.yml has nginx service
$dockerComposePath = Join-Path $projectRoot "docker-compose.yml"
if (Test-Path $dockerComposePath) {
    $content = Get-Content $dockerComposePath -Raw
    if ($content -match "nginx:") {
        $successes += "[OK] docker-compose.yml configured with nginx"
    } else {
        $warnings += "[WARN] docker-compose.yml may need nginx service"
    }
}

# Check Dockerfile.prod has health check
$dockerfilePath = Join-Path $projectRoot "Dockerfile.prod"
if (Test-Path $dockerfilePath) {
    $content = Get-Content $dockerfilePath -Raw
    if ($content -match "HEALTHCHECK") {
        $successes += "[OK] Dockerfile.prod has health checks"
    } else {
        $warnings += "[WARN] Dockerfile.prod missing health checks"
    }
}

Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow

# Check if ai2thor is in requirements
$reqPath = Join-Path $projectRoot "dreamai\requirements.txt"
if (Test-Path $reqPath) {
    $content = Get-Content $reqPath -Raw
    if ($content -match "ai2thor") {
        $successes += "[OK] requirements.txt has ai2thor"
    }
    if ($content -match "fastapi") {
        $successes += "[OK] requirements.txt has fastapi"
    }
    if ($content -match "pillow") {
        $successes += "[OK] requirements.txt has pillow"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION RESULTS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($successes.Count -gt 0) {
    Write-Host "SUCCESSES ($($successes.Count)):" -ForegroundColor Green
    foreach ($success in $successes) {
        Write-Host "  $success" -ForegroundColor Green
    }
    Write-Host ""
}

if ($warnings.Count -gt 0) {
    Write-Host "WARNINGS ($($warnings.Count)):" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "  $warning" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($errors.Count -gt 0) {
    Write-Host "ERRORS ($($errors.Count)):" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  $error" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "[FAIL] Setup incomplete. Fix errors above before proceeding." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "[SUCCESS] ALL CHECKS PASSED!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. BUILD DOCKER IMAGES:" -ForegroundColor Yellow
Write-Host "   docker-compose build" -ForegroundColor Gray
Write-Host ""
Write-Host "2. START THE STACK:" -ForegroundColor Yellow
Write-Host "   docker-compose up -d" -ForegroundColor Gray
Write-Host ""
Write-Host "3. VERIFY SERVICES:" -ForegroundColor Yellow
Write-Host "   docker-compose ps" -ForegroundColor Gray
Write-Host ""
Write-Host "4. TEST IN BROWSER:" -ForegroundColor Yellow
Write-Host "   http://localhost" -ForegroundColor Gray
Write-Host ""
Write-Host "5. MONITOR LOGS:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f" -ForegroundColor Gray
Write-Host ""
Write-Host "For more info, see DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
Write-Host ""
