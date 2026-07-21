#!/usr/bin/env bash
# Install read_package as a systemd service on Raspberry Pi.
# Usage:  bash install.sh
set -e
echo "1/3  Installing dependencies..."; pip3 install --break-system-packages pyserial openpyxl
echo "2/3  Setting up systemd service..."
sudo cp read-package.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now read-package.service
echo "3/3  Done."
echo "  Status:  systemctl status read-package"
echo "  Logs:    journalctl -u read-package -f"
echo "  Export:  python3 read_package.py --export-xlsx"
