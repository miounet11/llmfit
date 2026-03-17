#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="${LLMFIT_CONTENT_GIT_BRANCH:-main}"
ALLOW_STALE_REPO="${LLMFIT_CONTENT_ALLOW_STALE_REPO:-1}"

if git -C "${ROOT}" fetch origin "${BRANCH}" --tags \
  && git -C "${ROOT}" checkout "${BRANCH}" \
  && git -C "${ROOT}" pull --ff-only origin "${BRANCH}"; then
  echo "Git refresh completed for branch ${BRANCH}"
elif [[ "${ALLOW_STALE_REPO}" == "1" ]]; then
  echo "[content-publisher] warning: git refresh failed for branch ${BRANCH}; continuing with the current checkout"
else
  echo "[content-publisher] error: git refresh failed for branch ${BRANCH}" >&2
  exit 1
fi

"${ROOT}/scripts/publish_site_content.sh" "${1:-}"
