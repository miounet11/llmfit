#!/usr/bin/env bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SITE_SOURCE="${ROOT}/site"
BUILD_ROOT="${LLMFIT_CONTENT_BUILD_ROOT:-${ROOT}/.content-build}"
BUILD_SITE="${BUILD_ROOT}/site"
STATE_FILE="${LLMFIT_CONTENT_STATE_FILE:-${ROOT}/site/content-manifest.json}"
DOCROOT="${LLMFIT_CONTENT_DOCROOT:-}"
COUNT="${LLMFIT_CONTENT_DAILY_COUNT:-4}"
DATE_OVERRIDE="${1:-${LLMFIT_CONTENT_DATE:-$(date +%F)}}"
RUN_REPORT_FILE="${LLMFIT_CONTENT_RUN_REPORT_FILE:-${BUILD_ROOT}/last-run.json}"

mkdir -p "${BUILD_ROOT}" "$(dirname "${STATE_FILE}")"
rm -rf "${BUILD_SITE}"
cp -a "${SITE_SOURCE}" "${BUILD_SITE}"

python3 "${ROOT}/scripts/generate_site_content.py" \
  --repo-root "${ROOT}" \
  --site-root "${BUILD_SITE}" \
  --state-file "${STATE_FILE}" \
  --count "${COUNT}" \
  --date "${DATE_OVERRIDE}" \
  --report-file "${RUN_REPORT_FILE}"

if [[ -n "${DOCROOT}" ]]; then
  rsync -av --delete "${BUILD_SITE}/" "${DOCROOT}/"
fi

echo "Run report written to ${RUN_REPORT_FILE}"
echo "Content publish completed for ${DATE_OVERRIDE}"
