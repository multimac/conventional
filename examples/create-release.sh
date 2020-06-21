#!/usr/bin/env bash

set -e

VERSION=${1}

# Generate updated changelog for new release
conventional template --unreleased-version "${VERSION}" > CHANGELOG.md

# Commit updated changelog and tag this new commit
git add CHANGELOG.md
git commit -m "chore(release): Version ${VERSION}"
git tag "${VERSION}"

# Can push the release commit and tag to origin now
# git push --tags
