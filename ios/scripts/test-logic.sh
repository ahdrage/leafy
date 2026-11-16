#!/bin/sh
# An isolated cache avoids the installed SwiftPM incremental-cache failure.
set -eu
leafy_ios_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
leafy_test_build=$(mktemp -d /tmp/leafy-swift-tests.XXXXXX)
trap 'rm -rf "$leafy_test_build"' EXIT HUP INT TERM
swift test --package-path "$leafy_ios_dir" --scratch-path "$leafy_test_build"
