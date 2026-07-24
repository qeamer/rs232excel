#!/usr/bin/env bash
# Pakkemaskin Skriver — norsk installasjon (Skjåk Trelast)
#
# På Pi (HDMI/tastatur eller SSH), lim inn ÉN av disse:
#
#   curl -fsSL https://raw.githubusercontent.com/qeamer/rs232excel/main/python/no/install.sh | bash
#
#   # eller uten curl (anbefalt hvis nett/curl krangler):
#   sudo apt update && sudo apt install -y git python3-pip
#   git clone https://github.com/qeamer/rs232excel.git
#   cd rs232excel/python/no && bash installer.sh
#
# Denne fila er curl-klar: den kloner repoet om nødvendig, deretter
# kjører den installer.sh i den norske mappen.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/qeamer/rs232excel.git}"
REPO_DIR="${REPO_DIR:-$HOME/rs232excel}"
BRANCH="${BRANCH:-main}"

echo "=== Pakkemaskin Skriver (norsk) ==="
echo "Bruker: ${USER}  Hjem: ${HOME}"
echo

# Hvis vi allerede står i en klonet python/no-mappe, bruk den
SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && "${BASH_SOURCE[0]}" != "-" && "${BASH_SOURCE[0]}" != "bash" ]]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd || true)"
fi

if [[ -n "$SCRIPT_DIR" && -f "$SCRIPT_DIR/read_package.py" && -f "$SCRIPT_DIR/installer.sh" ]]; then
  echo "Kjører lokal installer i $SCRIPT_DIR …"
  cd "$SCRIPT_DIR"
  bash installer.sh
  echo
  echo "Røyktest (simulering) …"
  python3 read_package.py --simuler eksempel.txt
  echo
  echo "=== Ferdig ==="
  echo "Neste: koble USB-serieadapter, deretter:"
  echo "  python3 read_package.py --bare-fangst --port /dev/ttyUSB0"
  echo "  sudo systemctl start pakkemaskin-skriver"
  exit 0
fi

echo "1/4  Systempakker …"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y git python3 python3-pip

echo
echo "2/4  Kloner repo → $REPO_DIR (branch $BRANCH) …"
if [[ -d "$REPO_DIR/.git" ]]; then
  echo "  Repo finnes — oppdaterer"
  git -C "$REPO_DIR" fetch origin
  git -C "$REPO_DIR" checkout "$BRANCH"
  git -C "$REPO_DIR" pull --ff-only origin "$BRANCH" || true
else
  git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi

echo
echo "3/4  Installerer norsk produksjonsversjon …"
cd "$REPO_DIR/python/no"
bash installer.sh

echo
echo "4/4  Røyktest (simulering, uten PLS) …"
python3 read_package.py --simuler eksempel.txt

echo
echo "=== Ferdig ==="
echo "Neste steg:"
echo "  1. Koble USB-serieadapter (+ evt. minnepenn)"
echo "  2. python3 read_package.py --bare-fangst --port /dev/ttyUSB0"
echo "  3. sudo systemctl start pakkemaskin-skriver"
echo "  4. journalctl -u pakkemaskin-skriver -f"
