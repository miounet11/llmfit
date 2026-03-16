#!/usr/bin/env bash

set -euo pipefail

HOST="${1:?usage: scripts/deploy-site.sh user@host [/remote/path]}"
REMOTE_DIR="${2:-/opt/llmfit}"
BRANCH="${BRANCH:-main}"

ssh "${HOST}" "mkdir -p '${REMOTE_DIR%/*}'"

if ssh "${HOST}" "[ -d '${REMOTE_DIR}/.git' ]"; then
  ssh "${HOST}" "git -C '${REMOTE_DIR}' fetch origin '${BRANCH}' --tags && git -C '${REMOTE_DIR}' checkout '${BRANCH}' && git -C '${REMOTE_DIR}' pull --ff-only origin '${BRANCH}'"
else
  ssh "${HOST}" "git clone --branch '${BRANCH}' https://github.com/miounet11/llmfit.git '${REMOTE_DIR}'"
fi

ssh "${HOST}" "docker compose -f '${REMOTE_DIR}/deploy/site.compose.yml' up -d"

echo "Site deployment requested on ${HOST} using ${REMOTE_DIR}/deploy/site.compose.yml"
