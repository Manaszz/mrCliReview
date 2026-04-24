#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  echo "Usage: $0 <project_id> <mr_iid> <markdown_file>" >&2
  exit 2
fi

PROJECT_ID="$1"
MR_IID="$2"
MARKDOWN_FILE="$3"

: "${GITLAB_URL:?GITLAB_URL is required}"
: "${GITLAB_TOKEN:?GITLAB_TOKEN is required}"

if [[ ! -f "$MARKDOWN_FILE" ]]; then
  echo "Markdown file not found: $MARKDOWN_FILE" >&2
  exit 3
fi

BODY_JSON=$(python3 - <<'PY' "$MARKDOWN_FILE"
import json
import pathlib
import sys
p = pathlib.Path(sys.argv[1])
print(json.dumps({"body": p.read_text(encoding="utf-8")}, ensure_ascii=False))
PY
)

curl --fail --silent --show-error \
  --request POST \
  --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  --header "Content-Type: application/json" \
  --data "$BODY_JSON" \
  "${GITLAB_URL%/}/api/v4/projects/${PROJECT_ID}/merge_requests/${MR_IID}/notes" >/dev/null

echo "GitLab note posted to project=${PROJECT_ID} mr=${MR_IID}"