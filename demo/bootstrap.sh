#!/usr/bin/env bash
# Smart Hive AI — One-Click Demo Bootstrap (Linux / Mac)
#
# Usage (from project root):
#   bash demo/bootstrap.sh
#
# What this does:
#   1. Creates .env.demo from template if it doesn't exist
#   2. Creates conda environment "smart-hive-demo" from demo/environment.yml
#   3. Detects Docker → runs docker-compose (recommended)
#      No Docker  → runs services directly via conda env

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║      Smart Hive AI — Demo Setup       ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# ── Must be run from project root ─────────────────────────────────────────────
if [ ! -f "demo/bootstrap.sh" ]; then
    echo -e "${RED}❌  Run this script from the project root directory:${NC}"
    echo "    bash demo/bootstrap.sh"
    exit 1
fi

# ── Step 1: environment file ──────────────────────────────────────────────────
echo -e "${CYAN}▶  Step 1: Environment file${NC}"
if [ ! -f ".env.demo" ]; then
    cp demo/.env.demo.example .env.demo
    echo -e "${GREEN}   Created .env.demo from template.${NC}"
    echo -e "${YELLOW}   Default password is: smarthive  (edit .env.demo to change)${NC}"
else
    echo "   .env.demo already exists — skipping."
fi
echo ""

# ── Step 2: conda environment ─────────────────────────────────────────────────
echo -e "${CYAN}▶  Step 2: Conda environment${NC}"

if ! command -v conda &> /dev/null; then
    echo -e "${RED}❌  conda not found.${NC}"
    echo "   Install Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

ENV_NAME="smart-hive-demo"
if conda env list | grep -q "^${ENV_NAME}[[:space:]]"; then
    echo "   Conda env '${ENV_NAME}' already exists — skipping creation."
else
    echo "   Creating conda env '${ENV_NAME}' (~2 minutes on first run)..."
    conda env create -f demo/environment.yml
    echo -e "${GREEN}   Environment created.${NC}"
fi
echo ""

# ── Step 3: run ───────────────────────────────────────────────────────────────
echo -e "${CYAN}▶  Step 3: Starting the demo${NC}"

if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    echo -e "${GREEN}   Docker detected — starting full multi-container stack.${NC}"
    echo "   Dashboard will be available at: http://localhost:5000"
    echo "   Default password: smarthive  (change in .env.demo)"
    echo ""
    docker compose -f demo/docker-compose.demo.yml --env-file .env.demo up --build
else
    echo -e "${YELLOW}   Docker not found — starting services directly via conda env.${NC}"
    echo "   Dashboard will be available at: http://localhost:5000"
    echo "   Default password: smarthive  (change in .env.demo)"
    echo ""
    conda run -n "${ENV_NAME}" --no-capture-output python demo/run_demo.py
fi
