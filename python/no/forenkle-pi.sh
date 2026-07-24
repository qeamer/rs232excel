#!/usr/bin/env bash
# forenkle-pi.sh — Pi Zero som pakkemaskin-apparat (INGEN login på HDMI)
#
#  • Stille oppstart
#  • tty1 = direkte meny (getty/login er AV) — fikser hengende login-bug
#  • tty2 = vanlig login (nød: Alt+F2)
#  • Skrur av Bluetooth/modem/apt-støy
#
# Kjør:  bash forenkle-pi.sh
# Kalles også fra installer.sh
set -euo pipefail

BRUKER="${SUDO_USER:-${USER}}"
if [[ "$BRUKER" == "root" ]]; then
  echo "Kjør som vanlig bruker (f.eks. pi), ikke som root." >&2
  exit 1
fi
HJEM="$(getent passwd "$BRUKER" | cut -d: -f6)"
KATALOG="$(cd "$(dirname "$0")" && pwd)"

echo "=== Forenkler Pi til pakkemaskin-apparat ==="
echo "Bruker: $BRUKER"
echo

# 1) Stille boot
echo "1/5  Stille oppstart …"
CMDLINE=""
for kandidat in /boot/firmware/cmdline.txt /boot/cmdline.txt; do
  if [[ -f "$kandidat" ]]; then
    CMDLINE="$kandidat"
    break
  fi
done
if [[ -n "$CMDLINE" ]]; then
  sudo cp -n "$CMDLINE" "${CMDLINE}.bak.pakkemaskin" 2>/dev/null \
    || sudo cp "$CMDLINE" "${CMDLINE}.bak.pakkemaskin"
  nå="$(tr -s ' ' < "$CMDLINE" | sed 's/[[:space:]]*$//')"
  grep -qw quiet <<<"$nå" || nå="$nå quiet"
  grep -q 'loglevel=' <<<"$nå" || nå="$nå loglevel=3"
  grep -qw logo.nologo <<<"$nå" || nå="$nå logo.nologo"
  echo "$nå" | sudo tee "$CMDLINE" >/dev/null
  echo "  Oppdatert $CMDLINE"
else
  echo "  Fant ikke cmdline.txt — hopper over"
fi
echo 'kernel.printk = 3 4 1 3' | sudo tee /etc/sysctl.d/20-pakkemaskin-quiet.conf >/dev/null

# 2) HDMI tty1 = meny DIREKTE (ingen login/getty) — det er fiksen mot hengende login
echo "2/5  HDMI-meny uten login …"
sudo cp "$KATALOG/meny" /usr/local/bin/meny
sudo chmod +x /usr/local/bin/meny

# cloud-init skriver «Completed socket interaction…» oppå login og ødelegger prompten
echo "  Skrur av cloud-init …"
sudo mkdir -p /etc/cloud
sudo touch /etc/cloud/cloud-init.disabled
for svc in cloud-init cloud-init-local cloud-config cloud-final \
           cloud-init.service cloud-init-local.service \
           cloud-config.service cloud-final.service; do
  sudo systemctl disable --now "$svc" 2>/dev/null || true
done

# Fjern gammel autologin/frisk-konsoll om den finnes
sudo rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
sudo rm -f /etc/systemd/system/pakkemaskin-frisk-konsoll.service
sudo systemctl disable pakkemaskin-frisk-konsoll.service 2>/dev/null || true

# Egen konsoll-tjeneste som eier tty1 — bypasser getty helt
sudo tee /etc/systemd/system/pakkemaskin-konsoll.service >/dev/null <<EOF
[Unit]
Description=Pakkemaskin HDMI-meny (ingen login)
After=multi-user.target
Conflicts=getty@tty1.service
ConditionPathExists=/dev/tty1

[Service]
Type=idle
User=${BRUKER}
Group=${BRUKER}
WorkingDirectory=${HJEM}
Environment=PAKKEMASKIN_MENY_KJORT=1
Environment=TERM=linux
ExecStartPre=/bin/sleep 3
ExecStart=/usr/local/bin/meny
Restart=always
RestartSec=1
StandardInput=tty
StandardOutput=tty
StandardError=tty
TTYPath=/dev/tty1
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes

[Install]
WantedBy=multi-user.target
EOF

# MASKER getty på tty1 (disable er ikke nok — getty.target kan starte den igjen)
sudo systemctl stop getty@tty1.service 2>/dev/null || true
sudo systemctl disable getty@tty1.service 2>/dev/null || true
sudo systemctl mask getty@tty1.service
sudo systemctl enable getty@tty2.service 2>/dev/null || true
sudo systemctl daemon-reload
sudo systemctl enable pakkemaskin-konsoll.service

# profile.d trengs ikke lenger for tty1
sudo rm -f /etc/profile.d/pakkemaskin-meny.sh

sudo tee /etc/motd >/dev/null <<'EOF'

  PAKKEMASKIN — Skjåk Trelast
  HDMI: tallmeny (ingen login)
  Nød-login: Alt+F2
  Kommandoer: porter sjekk logg status start stopp restart excel

EOF
if [[ -d /etc/update-motd.d ]]; then
  sudo chmod -x /etc/update-motd.d/* 2>/dev/null || true
fi

# 3) Sørg for korte kommandoer finnes
echo "3/5  Sjekker korte kommandoer …"
if [[ ! -x /usr/local/bin/pakkemaskin ]]; then
  sudo cp "$KATALOG/pakkemaskin" /usr/local/bin/pakkemaskin
  sudo chmod +x /usr/local/bin/pakkemaskin
fi
echo "PAKKEMASKIN_DIR=${KATALOG}" | sudo tee /etc/pakkemaskin.conf >/dev/null
for navn in start stopp restart status logg sjekk excel porter meny; do
  if [[ "$navn" == "meny" ]]; then
    sudo cp "$KATALOG/meny" /usr/local/bin/meny
    sudo chmod +x /usr/local/bin/meny
  else
    sudo ln -sf /usr/local/bin/pakkemaskin "/usr/local/bin/$navn"
  fi
done

# 4) Unødvendige tjenester
echo "4/5  Skrur av unødvendige tjenester …"
for svc in bluetooth hciuart ModemManager apt-daily.timer apt-daily-upgrade.timer; do
  sudo systemctl disable --now "$svc" 2>/dev/null || true
done

# 5) Begrens journal på SD
echo "5/5  Begrenser logger på SD-kort …"
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/pakkemaskin.conf >/dev/null <<'EOF'
[Journal]
SystemMaxUse=50M
RuntimeMaxUse=20M
MaxRetentionSec=14day
EOF
sudo systemctl restart systemd-journald 2>/dev/null || true

echo
echo "=== Ferdig ==="
echo "  Etter reboot på HDMI:"
echo "    • INGEN login-prompt"
echo "    • Meny direkte:"
echo "        1 porter  2 sjekk  3 logg  4 status"
echo "        5 start   6 stopp  7 restart  8 excel"
echo "    • Nød-login: Alt+F2"
echo "    • SSH som før: ssh ${BRUKER}@pakkemaskin.local"
echo
echo "  Reboot:   sudo reboot"
