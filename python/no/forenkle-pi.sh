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
  cmdline="$(tr -s ' ' < "$CMDLINE" | sed 's/[[:space:]]*$//')"
  grep -qw quiet <<<"$cmdline" || cmdline="$cmdline quiet"
  grep -q 'loglevel=' <<<"$cmdline" || cmdline="$cmdline loglevel=3"
  grep -qw logo.nologo <<<"$cmdline" || cmdline="$cmdline logo.nologo"
  echo "$cmdline" | sudo tee "$CMDLINE" >/dev/null
  echo "  Oppdatert $CMDLINE"
else
  echo "  Fant ikke cmdline.txt — hopper over"
fi
echo 'kernel.printk = 3 4 1 3' | sudo tee /etc/sysctl.d/20-pakkemaskin-quiet.conf >/dev/null

# 2) HDMI via agetty → meny (riktig TTY = tastatur virker)
echo "2/5  HDMI-meny med agetty …"
sudo cp "$KATALOG/meny" /usr/local/bin/meny
sudo chmod +x /usr/local/bin/meny
sudo cp "$KATALOG/pakkemaskin-autologin.sh" /usr/local/sbin/pakkemaskin-autologin.sh
sudo chmod +x /usr/local/sbin/pakkemaskin-autologin.sh

# cloud-init skriver «Completed socket interaction…» og ødelegger konsollen
echo "  Skrur av cloud-init …"
sudo mkdir -p /etc/cloud
sudo touch /etc/cloud/cloud-init.disabled
for svc in cloud-init cloud-init-local cloud-config cloud-final \
           cloud-init.service cloud-init-local.service \
           cloud-config.service cloud-final.service; do
  sudo systemctl disable --now "$svc" 2>/dev/null || true
done

# Fjern gamle forsøk (egen TTY-service uten tastatur-init)
sudo systemctl disable --now pakkemaskin-konsoll.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/pakkemaskin-konsoll.service
sudo rm -f /etc/systemd/system/pakkemaskin-frisk-konsoll.service
sudo systemctl disable pakkemaskin-frisk-konsoll.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
sudo rm -f /etc/profile.d/pakkemaskin-meny.sh
sudo systemctl unmask getty@tty1.service 2>/dev/null || true

sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/pakkemaskin.conf >/dev/null <<'EOF'
[Service]
ExecStart=
ExecStart=-/sbin/agetty --noclear -n -l /usr/local/sbin/pakkemaskin-autologin.sh tty1 linux
Type=idle
Restart=always
EOF

sudo systemctl daemon-reload
sudo systemctl enable getty@tty1.service
sudo systemctl enable getty@tty2.service 2>/dev/null || true

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
for navn in start stopp restart status logg sjekk excel porter usb integritet meny; do
  if [[ "$navn" == "meny" ]]; then
    sudo cp "$KATALOG/meny" /usr/local/bin/meny
    sudo chmod +x /usr/local/bin/meny
  else
    sudo ln -sf /usr/local/bin/pakkemaskin "/usr/local/bin/$navn"
  fi
done
# USB hotplug-mount
if [[ -f "$KATALOG/fiks-usb.sh" ]]; then
  bash "$KATALOG/fiks-usb.sh" || true
fi

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
echo "        1 USB  2 sjekk  3 logg  4 status"
echo "        5 start  6 stopp  7 restart  8 excel"
echo "    • Nød-login: Alt+F2"
echo "    • SSH som før: ssh ${BRUKER}@pakkemaskin.local"
echo
echo "  Reboot:   sudo reboot"
