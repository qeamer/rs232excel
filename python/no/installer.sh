#!/usr/bin/env bash
# Installer Pakkemaskin Skriver som tjeneste på Raspberry Pi.  Kjør:  bash installer.sh
set -e
echo "1/3  Avhengigheter …"; pip3 install --break-system-packages pyserial openpyxl
echo "2/3  systemd-tjeneste …"
sudo cp pakkemaskin-skriver.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pakkemaskin-skriver.service
echo "3/3  Ferdig."
echo "  Status:  systemctl status pakkemaskin-skriver"
echo "  Logg:    journalctl -u pakkemaskin-skriver -f"
echo "  Excel:   python3 read_package.py --eksporter-xlsx"
