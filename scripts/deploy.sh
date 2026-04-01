#!/usr/bin/env bash
# Deploy job-aggregator to Deepthought
# Usage: ./scripts/deploy.sh [--restart]

set -euo pipefail

REMOTE_USER="scon"
REMOTE_HOST="192.168.1.151"
REMOTE_PATH="/srv/docker/deepthought/jobspy"

echo "==> Syncing to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p ${REMOTE_PATH}/postgres"

# rsync is broken on Windows/Git bash (Cygwin dup() conflict); fall back to scp
if [[ "$(uname -s)" == MINGW* ]] || [[ "$(uname -s)" == CYGWIN* ]]; then
  echo "==> Windows detected — using scp instead of rsync"
  scp docker/docker-compose.yml "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/docker-compose.yml"
  scp docker/postgres/init.sql  "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/postgres/init.sql"
else
  rsync -av --exclude='.env' --exclude='*.log' \
    docker/ \
    "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"
fi

echo "==> Sync complete."

if [[ "${1:-}" == "--restart" ]]; then
  echo "==> Restarting services on Deepthought..."
  ssh "${REMOTE_USER}@${REMOTE_HOST}" "cd ${REMOTE_PATH} && docker compose up -d --pull always"
  echo "==> Done."
fi

echo ""
echo "NOTE: First deploy — make sure .env exists on Deepthought at ${REMOTE_PATH}/.env"
echo "      Copy from .env.example and fill in secrets before running --restart"
