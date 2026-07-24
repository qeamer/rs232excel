#!/usr/bin/env bash
# Download and install the package-label capture stack on a Raspberry Pi.
# Run after first SSH login (Pi OS already installed):
#
#   curl -fsSL https://raw.githubusercontent.com/qeamer/rs232excel/main/scripts/bootstrap-package-machine.sh | bash
#
# Or manually:
#   bash scripts/bootstrap-package-machine.sh
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/qeamer/rs232excel.git}"
REPO_DIR="${REPO_DIR:-$HOME/rs232excel}"
BRANCH="${BRANCH:-main}"

echo "=== Package machine — download ==="
echo "User: $USER  Home: $HOME"
echo

echo "1/4  System update and packages..."
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  git python3 python3-pip

echo
echo "2/4  Cloning repo..."
if [[ -d "$REPO_DIR/.git" ]]; then
  echo "  Repo already present: $REPO_DIR — pulling latest"
  git -C "$REPO_DIR" fetch origin
  git -C "$REPO_DIR" checkout "$BRANCH"
  git -C "$REPO_DIR" pull --ff-only origin "$BRANCH"
else
  git clone --branch "$BRANCH" "$REPO_URL" "$REPO_DIR"
fi

echo
echo "3/4  Running English installer..."
cd "$REPO_DIR/python/en"
bash install.sh

echo
echo "4/4  Smoke test (simulation, no PLC)..."
python3 read_package.py --simulate example.txt
echo
echo "=== Done ==="
echo "Next steps:"
echo "  1. Connect USB-serial adapter (and optional flash drive) — see docs/en/INSTALLATION.md"
echo "  2. Verify:  python3 read_package.py --raw-capture --port /dev/ttyUSB0"
echo "  3. Production: sudo systemctl start read-package"
echo "  4. Logs:       journalctl -u read-package -f"
