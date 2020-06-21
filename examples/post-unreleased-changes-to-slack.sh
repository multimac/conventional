#!/usr/bin/env bash

set -e

SLACK_TOKEN=${1}
SLACK_CHANNEL=${2}

TITLE="Release Notes"
TEMP_DIR=$(mktemp -d)

conventional list-commits --from-last-tag \
    | conventional template --template-name "slack.md" --input - \
    > "${TEMP_DIR}/release-notes.md"

pushd "${TEMP_DIR}"
curl -F "token=${SLACK_BOT_TOKEN}" -F "channels=${SLACK_CHANNEL}" \
    -F "title=${TITLE}" -F "filetype=post" -F "file=@release-notes.md" \
    https://slack.com/api/files.upload

popd
rm -rf "${TEMP_DIR}"
