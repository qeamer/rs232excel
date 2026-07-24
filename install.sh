#!/usr/bin/env bash
# Rot-install: norsk produksjonsversjon (standard for Skjåk / skandinaviske sagbruk).
#
#   curl -fsSL https://raw.githubusercontent.com/qeamer/rs232excel/main/install.sh | bash
#
# Engelsk speil: python/en/install.sh
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/qeamer/rs232excel.git}"
REPO_DIR="${REPO_DIR:-$HOME/rs232excel}"
BRANCH="${BRANCH:-main}"

echo "=== rs232excel — norsk installasjon ==="

# Last og kjør norsk curl-klar install (kloner hvis nødvendig)
if [[ -f "$(dirname "${BASH_SOURCE[0]:-}")/python/no/install.sh" ]]; then
  bash "$(dirname "${BASH_SOURCE[0]}")/python/no/install.sh"
  exit $?
fi

# Piped via curl — hent norsk install.sh fra samme branch
RAW="https://raw.githubusercontent.com/qeamer/rs232excel/${BRANCH}/python/no/install.sh"
echo "Henter $RAW …"
curl -fsSL "$RAW" | REPO_URL="$REPO_URL" REPO_DIR="$REPO_DIR" BRANCH="$BRANCH" bash
