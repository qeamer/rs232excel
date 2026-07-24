#!/usr/bin/env bash
# Installer Pakkemaskin Skriver som tjeneste på Raspberry Pi.
# Kjør fra denne mappen:  bash installer.sh
set -euo pipefail

KATALOG="$(cd "$(dirname "$0")" && pwd)"
BRUKER="${SUDO_USER:-${USER}}"
if [[ "$BRUKER" == "root" ]]; then
  echo "Kjør som vanlig bruker (f.eks. pi), ikke som root." >&2
  exit 1
fi

cd "$KATALOG"

echo "1/4  Avhengigheter …"
pip3 install --break-system-packages pyserial openpyxl pillow 2>/dev/null \
  || pip3 install --break-system-packages pyserial openpyxl
if ! id -nG "$BRUKER" | grep -qw dialout; then
  sudo usermod -aG dialout "$BRUKER" || true
  echo "  Lagt $BRUKER i dialout (logg ut/inn eller reboot for full effekt)."
fi
sudo mkdir -p /media/usb0
sudo chown "$BRUKER:$BRUKER" /media/usb0 2>/dev/null || true

echo "2/4  systemd-tjeneste …"
# Oppdater stier til faktisk katalog/bruker
sudo tee /etc/systemd/system/pakkemaskin-skriver.service >/dev/null <<EOF
[Unit]
Description=Pakkemaskin Skriver - pakkelapp-fangst
After=multi-user.target

[Service]
Type=simple
User=${BRUKER}
WorkingDirectory=${KATALOG}
ExecStart=/usr/bin/python3 ${KATALOG}/read_package.py --port /dev/ttyUSB0 --baud 9600 --usb-sti /media/usb0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable pakkemaskin-skriver.service

echo "3/4  Enkel kommando: pakkemaskin …"
echo "PAKKEMASKIN_DIR=${KATALOG}" | sudo tee /etc/pakkemaskin.conf >/dev/null
sudo cp "$KATALOG/pakkemaskin" /usr/local/bin/pakkemaskin
sudo chmod +x /usr/local/bin/pakkemaskin

echo "4/4  Ferdig."
echo
echo "  Fra hvor som helst:"
echo "    pakkemaskin status"
echo "    pakkemaskin start"
echo "    pakkemaskin restart     # ved kræsj"
echo "    pakkemaskin logg"
echo "    pakkemaskin test        # første gang / feilsøking"
echo "    pakkemaskin excel"
echo
echo "  Start tjenesten når USB-adapter er koblet:"
echo "    pakkemaskin start"
