# Smart Hive AI — One-Click Demo Bootstrap (Windows PowerShell)
#
# Usage (from project root):
#   .\demo\bootstrap.ps1
#
# What this does:
#   1. Creates .env.demo from template if it doesn't exist
#   2. Creates conda environment "smart-hive-demo" from demo/environment.yml
#   3. Detects Docker → runs docker-compose (recommended)
#      No Docker  → runs services directly via conda env

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║      Smart Hive AI — Demo Setup       ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Must be run from project root ─────────────────────────────────────────────
if (-not (Test-Path "demo\bootstrap.ps1")) {
    Write-Host "❌  Run this script from the project root directory:" -ForegroundColor Red
    Write-Host "    .\demo\bootstrap.ps1"
    exit 1
}

# ── Step 1: environment file ──────────────────────────────────────────────────
Write-Host "▶  Step 1: Environment file" -ForegroundColor Cyan
if (-not (Test-Path ".env.demo")) {
    Copy-Item "demo\.env.demo.example" ".env.demo"
    Write-Host "   Created .env.demo from template." -ForegroundColor Green
    Write-Host "   Default password is: smarthive  (edit .env.demo to change)" -ForegroundColor Yellow
} else {
    Write-Host "   .env.demo already exists — skipping."
}
Write-Host ""

# ── Step 2: conda environment ─────────────────────────────────────────────────
Write-Host "▶  Step 2: Conda environment" -ForegroundColor Cyan

try {
    $null = Get-Command conda -ErrorAction Stop
} catch {
    Write-Host "❌  conda not found." -ForegroundColor Red
    Write-Host "   Install Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
}

$ENV_NAME = "smart-hive-demo"
$envList = conda env list 2>&1
if ($envList -match "(?m)^$ENV_NAME\s") {
    Write-Host "   Conda env '$ENV_NAME' already exists — skipping creation."
} else {
    Write-Host "   Creating conda env '$ENV_NAME' (~2 minutes on first run)..."
    conda env create -f demo\environment.yml
    Write-Host "   Environment created." -ForegroundColor Green
}
Write-Host ""

# ── Step 3: run ───────────────────────────────────────────────────────────────
Write-Host "▶  Step 3: Starting the demo" -ForegroundColor Cyan

$dockerAvailable = $false
try {
    docker compose version 2>&1 | Out-Null
    $dockerAvailable = $true
} catch {}

if ($dockerAvailable) {
    Write-Host "   Docker detected — starting full multi-container stack." -ForegroundColor Green
    Write-Host "   Dashboard will be available at: http://localhost:5000"
    Write-Host "   Default password: smarthive  (change in .env.demo)" -ForegroundColor Yellow
    Write-Host ""
    docker compose -f demo\docker-compose.demo.yml --env-file .env.demo up --build
} else {
    Write-Host "   Docker not found — starting services directly via conda env." -ForegroundColor Yellow
    Write-Host "   Dashboard will be available at: http://localhost:5000"
    Write-Host "   Default password: smarthive  (change in .env.demo)" -ForegroundColor Yellow
    Write-Host ""
    conda run -n $ENV_NAME --no-capture-output python demo\run_demo.py
}
