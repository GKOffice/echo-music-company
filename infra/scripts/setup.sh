#!/usr/bin/env bash
set -euo pipefail

BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

echo -e "${BOLD}🎵 ECHO — Setup${RESET}"
echo "=================================="

# 1. Check for docker
if ! command -v docker &> /dev/null; then
  echo -e "${RED}✗ Docker not found. Install Docker Desktop: https://www.docker.com/products/docker-desktop${RESET}"
  exit 1
fi
echo -e "${GREEN}✓ Docker found${RESET}"

# 2. Check for docker-compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
  echo -e "${RED}✗ docker-compose not found. Install Docker Compose.${RESET}"
  exit 1
fi
echo -e "${GREEN}✓ Docker Compose found${RESET}"

# 3. Copy .env.example to .env if .env doesn't exist
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ ! -f "$ROOT_DIR/.env" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo -e "${YELLOW}⚠  Created .env from .env.example — fill in your API keys before starting${RESET}"
else
  echo -e "${GREEN}✓ .env already exists${RESET}"
fi

# 4. Start postgres and redis
echo ""
echo -e "${BOLD}Starting PostgreSQL and Redis...${RESET}"
cd "$ROOT_DIR"
docker compose up -d postgres redis 2>/dev/null || docker-compose up -d postgres redis

# 5. Wait for postgres to be healthy
echo -n "Waiting for PostgreSQL"
for i in $(seq 1 30); do
  if docker compose exec -T postgres pg_isready -U echo -d echo &>/dev/null 2>&1 || \
     docker-compose exec -T postgres pg_isready -U echo -d echo &>/dev/null 2>&1; then
    echo -e " ${GREEN}ready!${RESET}"
    break
  fi
  echo -n "."
  sleep 2
  if [ $i -eq 30 ]; then
    echo -e " ${RED}timed out${RESET}"
    echo "Check: docker compose logs postgres"
    exit 1
  fi
done

echo ""
echo -e "${GREEN}${BOLD}✓ Infrastructure ready!${RESET}"
echo ""
echo "Next steps:"
echo "  1. Edit .env and fill in your API keys"
echo "  2. Run: docker compose up"
echo "  3. API docs: http://localhost:8000/docs"
echo "  4. Web app:  http://localhost:3000"
echo ""
