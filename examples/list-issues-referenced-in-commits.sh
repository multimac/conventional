#!/usr/bin/env bash

set -e

FILENAME=${1}
FROM=${2}

apk add --no-progress jq

conventional list-commits --parse ${FROM:+ --from "${FROM}"} \
    | jq --raw-output '.data.metadata.closes[]' | sort -n | uniq \
    > "${FILENAME}"
