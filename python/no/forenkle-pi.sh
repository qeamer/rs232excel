#!/usr/bin/env bash
# forenkle-pi.sh — gjør Raspberry Pi OS Lite om til et enkelt pakkemaskin-apparat.
#
#  • Stille oppstart (mindre tekst som ødelegger login)
#  • Autologin på HDMI-skjerm (tty1) — slipper brukernavn/passord
#  • Enkel tallmeny ved oppstart
#  • Skrur av ting Zero ikke trenger (Bluetooth, modem, støyete apt-timere)
#
# Kjør:  bash forenkle-pi.sh
# Kalles også fra installer.sh
set -euo pipefail

BRUKER="${SUDO_USER:-${USER}}"
if [[ "$BRUKER" == "root" ]]; then
  echo "Kjør som vanlig bruker (f.eks. pi), ikke som root." >&2
  exit 1
fi
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

# 2) Autologin på tty1 (HDMI) + frisk prompt etter støyete boot-meldinger
echo "2/5  Autologin på skjerm …"
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf >/dev/null <<EOF
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin ${BRUKER} --noclear %I \$TERM
EOF

# Sen kernel/boot-tekst (f.eks. «Completed socket interaction…») kan ødelegge
# login-prompten på tty1 slik at tastaturet «ikke virker». Restart getty når
# boot er ferdig → ren autologin/meny.
sudo tee /etc/systemd/system/pakkemaskin-frisk-konsoll.service >/dev/null <<'EOF'
[Unit]
Description=Pakkemaskin — frisk HDMI-login etter boot-støy
After=multi-user.target
Before=getty@tty1.service

[Service]
Type=oneshot
# Vent til sen boot-spam er ferdig, deretter ny getty på tty1
ExecStart=/bin/sleep 3
ExecStart=/bin/systemctl restart getty@tty1.service

[Install]
WantedBy=multi-user.target
EOF
# After+restart pattern: run after multi-user is up
sudo tee /etc/systemd/system/pakkemaskin-frisk-konsoll.service >/dev/null <<'EOF'
[Unit]
Description=Pakkemaskin — frisk HDMI-login etter boot-støy
After=multi-user.target network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 5
ExecStart=/bin/systemctl restart getty@tty1.service
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable pakkemaskin-frisk-konsoll.service
# Ekstra login på tty2 — nødutgang med Alt+F2 hvis tty1 henger
sudo systemctl enable getty@tty2.service 2>/dev/null || true

# 3) Meny ved innlogging på tty1 (ikke SSH)
echo "3/5  Oppstartsmeny …"
sudo cp "$KATALOG/meny" /usr/local/bin/meny
sudo chmod +x /usr/local/bin/meny
sudo tee /etc/profile.d/pakkemaskin-meny.sh >/dev/null <<'EOF'
# Pakkemaskin-apparat: meny kun på HDMI-konsoll (tty1), ikke via SSH
if [ -z "${PAKKEMASKIN_MENY_KJORT:-}" ] && [ "$(tty 2>/dev/null)" = "/dev/tty1" ]; then
  export PAKKEMASKIN_MENY_KJORT=1
  exec meny
fi
EOF
sudo chmod 644 /etc/profile.d/pakkemaskin-meny.sh

sudo tee /etc/motd >/dev/null <<'EOF'

  PAKKEMASKIN — Skjåk Trelast
  Kommandoer:  start  stopp  restart  status  logg  sjekk  excel
  Eller skriv:  meny

EOF
if [[ -d /etc/update-motd.d ]]; then
  sudo chmod -x /etc/update-motd.d/* 2>/dev/null || true
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
echo "    • Ingen login-prompt (autologin)"
echo "    • Tallmeny: 1=start  2=stopp  3=restart  4=status  5=logg …"
echo "    • SSH fungerer som før (uten meny)"
echo
echo "  Merk: tastatur må sitte i USB-port midt på Zero (via OTG)."
echo "  Hvis login henger på tty1:  Alt+F2  (ny login på tty2)"
echo "  Reboot:   sudo reboot"
