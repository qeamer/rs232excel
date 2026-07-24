#!/usr/bin/env bash
# Install read_package as a systemd service on Raspberry Pi.
# Run from this directory:  bash install.sh
#
# Expected: repo already cloned (see scripts/bootstrap-package-machine.sh).
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="${SUDO_USER:-${USER}}"
if [[ "$USER_NAME" == "root" ]]; then
  echo "Run as a normal user (e.g. pi), not as root." >&2
  exit 1
fi
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"
SERVICE_NAME="read-package"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

cd "$DIR"

echo "1/4  System packages..."
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip
if ! id -nG "$USER_NAME" | grep -qw dialout; then
  sudo usermod -aG dialout "$USER_NAME"
  echo "  Added $USER_NAME to dialout (log out/in or reboot for full effect)."
fi

echo "2/4  Python dependencies..."
python3 -m pip install --break-system-packages -r requirements.txt

echo "3/4  USB mirror directory..."
sudo mkdir -p /media/usb0
sudo chown "$USER_NAME:$USER_NAME" /media/usb0

echo "4/4  systemd service..."
sudo tee "$SERVICE_FILE" >/dev/null <<EOF
[Unit]
Description=rs232excel — Package label capture from OKI Microline printer tap
After=multi-user.target

[Service]
Type=simple
User=${USER_NAME}
WorkingDirectory=${DIR}
# Adjust --port and --baud. Use --raw-capture first time to verify label format.
ExecStart=/usr/bin/python3 ${DIR}/read_package.py --port /dev/ttyUSB0 --baud 9600
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
# Enable autostart, but do not start yet — wire/verify hardware first
sudo systemctl enable "${SERVICE_NAME}.service"

echo
echo "Done. Installed for user ${USER_NAME} in ${DIR}"
echo "  Status:   systemctl status ${SERVICE_NAME}"
echo "  Start:    sudo systemctl start ${SERVICE_NAME}"
echo "  Logs:     journalctl -u ${SERVICE_NAME} -f"
echo "  Export:   python3 read_package.py --export-xlsx"
echo "  Simulate: python3 read_package.py --simulate example.txt"
if [[ "$HOME_DIR" != "/home/pi" ]] || [[ "$USER_NAME" != "pi" ]]; then
  echo
  echo "Note: service uses User=${USER_NAME} and WorkingDirectory=${DIR}"
fi
