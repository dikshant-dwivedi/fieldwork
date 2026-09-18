#!/usr/bin/env bash
set -euo pipefail

minimum_lima="2.2.0"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  echo "FAIL: checkpoint 1 currently supports Apple Silicon macOS." >&2
  exit 1
fi

for command in brew make limactl; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "FAIL: missing $command" >&2
    echo "Run 'brew bundle' from the repository root." >&2
    exit 1
  fi
done

actual_lima="$(limactl --version | awk '{print $3}')"
IFS=. read -r actual_major actual_minor actual_patch <<<"$actual_lima"
IFS=. read -r minimum_major minimum_minor minimum_patch <<<"$minimum_lima"

if (( actual_major < minimum_major )) ||
  (( actual_major == minimum_major && actual_minor < minimum_minor )) ||
  (( actual_major == minimum_major && actual_minor == minimum_minor && actual_patch < minimum_patch )); then
  echo "FAIL: Lima $minimum_lima or newer is required; found $actual_lima." >&2
  exit 1
fi

echo "PASS: Apple Silicon macOS"
echo "PASS: Homebrew is available"
echo "PASS: Lima $actual_lima (minimum $minimum_lima)"
echo "No host sudo access is required."
