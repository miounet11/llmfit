#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="${LLMFIT_CONTENT_GIT_BRANCH:-main}"

git -C "${ROOT}" fetch origin "${BRANCH}" --tags
git -C "${ROOT}" checkout "${BRANCH}"
git -C "${ROOT}" pull --ff-only origin "${BRANCH}"

"${ROOT}/scripts/publish_site_content.sh" "${1:-}"
