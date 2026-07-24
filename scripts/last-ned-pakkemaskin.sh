#!/usr/bin/env bash
# Alias → python/no/install.sh (norsk curl-klar install).
set -euo pipefail
BRANCH="${BRANCH:-main}"

SRC="${BASH_SOURCE[0]:-}"
if [[ -n "$SRC" && "$SRC" != "-" && "$SRC" != "bash" && -f "$SRC" ]]; then
  ROOT="$(cd "$(dirname "$SRC")/.." && pwd)"
  if [[ -f "$ROOT/python/no/install.sh" ]]; then
    exec bash "$ROOT/python/no/install.sh"
  fi
fi

curl -fsSL "https://raw.githubusercontent.com/qeamer/rs232excel/${BRANCH}/python/no/install.sh" | bash
