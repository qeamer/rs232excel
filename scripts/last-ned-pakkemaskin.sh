#!/usr/bin/env bash
# Last ned og installer Pakkemaskin Skriver på Raspberry Pi.
# Kjør etter første SSH-innlogging (Pi OS allerede installert):
#
#   curl -fsSL https://raw.githubusercontent.com/qeamer/rs232excel/main/scripts/last-ned-pakkemaskin.sh | bash
#
# Eller manuelt:
#   bash scripts/last-ned-pakkemaskin.sh
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/qeamer/rs232excel.git}"
REPO_DIR="${REPO_DIR:-$HOME/rs232excel}"
BRANCH="${BRANCH:-main}"

echo "=== Pakkemaskin Skriver — nedlasting ==="
echo "Bruker: $USER  Hjem: $HOME"
echo

echo "1/4  Systemoppdatering og pakker …"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  git python3 python3-pip

echo
echo "2/4  Kloner repo …"
if [[ -d "$REPO_DIR/.git" ]]; then
  echo "  Repo finnes allerede: $REPO_DIR — henter siste endringer"
  git -C "$REPO_DIR" fetch origin
  git -C "$REPO_DIR" checkout "$BRANCH"
  git -C "$REPO_DIR" pull --ff-only origin "$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi

echo
echo "3/4  Kjører norsk installer …"
cd "$REPO_DIR/python/no"
bash installer.sh

echo
echo "4/4  Røyktest (simulering, uten PLS) …"
python3 read_package.py --simuler eksempel.txt
echo
echo "=== Ferdig ==="
echo "Neste steg:"
echo "  1. Koble USB-serieadapter (og eventuelt minnepenn) — se docs/no/INSTALLATION.md"
echo "  2. Verifiser:  python3 read_package.py --bare-fangst --port /dev/ttyUSB0"
echo "  3. Produksjon: sudo systemctl start pakkemaskin-skriver"
echo "  4. Logg:       journalctl -u pakkemaskin-skriver -f"
