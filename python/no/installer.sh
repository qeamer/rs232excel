#!/usr/bin/env bash
# Installer Pakkemaskin Skriver som tjeneste på Raspberry Pi.
# Kjør fra denne mappen:  bash installer.sh
#
# Forventet: allerede klonet repo (se scripts/last-ned-pakkemaskin.sh).
set -euo pipefail

KATALOG="$(cd "$(dirname "$0")" && pwd)"
BRUKER="${SUDO_USER:-${USER}}"
if [[ "$BRUKER" == "root" ]]; then
  echo "Kjør som vanlig bruker (f.eks. pi), ikke som root." >&2
  exit 1
fi
HJEM="$(getent passwd "$BRUKER" | cut -d: -f6)"
SERVICE_NAVN="pakkemaskin-skriver"
SERVICE_FIL="/etc/systemd/system/${SERVICE_NAVN}.service"

cd "$KATALOG"

echo "1/4  Systempakker …"
sudo apt-get update -y
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip
# Serieport-tilgang uten sudo
if ! id -nG "$BRUKER" | grep -qw dialout; then
  sudo usermod -aG dialout "$BRUKER"
  echo "  Lagt $BRUKER i gruppen dialout (logg ut/inn eller reboot for full effekt)."
fi

echo "2/4  Python-avhengigheter …"
python3 -m pip install --break-system-packages -r requirements.txt

echo "3/4  USB-speilmappe …"
sudo mkdir -p /media/usb0
sudo chown "$BRUKER:$BRUKER" /media/usb0

echo "4/4  systemd-tjeneste …"
# Bygg unit med faktisk bruker og katalog (mal i repoet er kun referanse)
sudo tee "$SERVICE_FIL" >/dev/null <<EOF
[Unit]
Description=Pakkemaskin Skriver - pakkelapp-fangst
After=multi-user.target

[Service]
Type=simple
User=${BRUKER}
WorkingDirectory=${KATALOG}
# Juster --port og --baud. Bruk --bare-fangst første gang for å se lappformatet.
ExecStart=/usr/bin/python3 ${KATALOG}/read_package.py --port /dev/ttyUSB0 --baud 9600 --usb-sti /media/usb0
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
# Aktiver autostart, men start ikke ennå — hardware/verifisering kommer etterpå
sudo systemctl enable "${SERVICE_NAVN}.service"

echo
echo "Ferdig. Installert for bruker ${BRUKER} i ${KATALOG}"
echo "  Status:   systemctl status ${SERVICE_NAVN}"
echo "  Start:    sudo systemctl start ${SERVICE_NAVN}"
echo "  Logg:     journalctl -u ${SERVICE_NAVN} -f"
echo "  Excel:    python3 read_package.py --eksporter-xlsx"
echo "  Simuler:  python3 read_package.py --simuler eksempel.txt"
if [[ "$HJEM" != "/home/pi" ]] || [[ "$BRUKER" != "pi" ]]; then
  echo
  echo "Merk: tjenesten bruker User=${BRUKER} og WorkingDirectory=${KATALOG}"
fi
