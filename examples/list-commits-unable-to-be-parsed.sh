#!/usr/bin/env bash

set -e

FILENAME=${1}
FROM=${2}

apk add --no-progress jq

conventional list-commits --parse --include-unparsed ${FROM:+ --from "${FROM}"} \
    | jq --raw-output 'select(.data == null) | .source.rev'
    > "${FILENAME}"
