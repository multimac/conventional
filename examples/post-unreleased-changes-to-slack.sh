#!/usr/bin/env bash

set -e

SLACK_TOKEN=${1}
SLACK_CHANNEL=${2}

TITLE="Release Notes"

TEMP_DIR=$(mktemp -d)
pushd "${TEMP_DIR}"

cat << EOF > .conventional.yaml
template:
  config:
    commit-link-pattern: https://github.com/multimac/conventional/commit/{commit}
    issue-link-pattern: https://github.com/multimac/conventional/issues/{issue}
EOF

conventional --config-file .conventional.yaml list-commits \
    | conventional --config-file .conventional.yaml template --input -
    > release-notes.md

curl -F "token=${SLACK_BOT_TOKEN}" -F "channels=${SLACK_CHANNEL}" \
    -F "title=${TITLE}" -F "filetype=post" -F "file=@release-notes.md" \
    https://slack.com/api/files.upload

popd
rm -rf "${TEMP_DIR}"
