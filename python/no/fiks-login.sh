#!/usr/bin/env bash
# fiks-login.sh — HARD fiks for hengende «pakkemaskin login:» + cloud-init-støy
#
# Kjør via SSH (HDMI-login kan være ødelagt):
#   ssh pi@192.168.1.53
#   cd ~/rs232excel/python/no && bash fiks-login.sh
#
set -euo pipefail

BRUKER="${SUDO_USER:-${USER}}"
if [[ "$BRUKER" == "root" ]]; then
  echo "Kjør som pi (ikke root)." >&2
  exit 1
fi
HJEM="$(getent passwd "$BRUKER" | cut -d: -f6)"
KATALOG="$(cd "$(dirname "$0")" && pwd)"

echo "=== HARD fiks: fjern login-bug på HDMI ==="
echo

# ── 1) cloud-init er synderen («Completed socket interaction…») ───────────
echo "1/4  Skrur av cloud-init (kilden til boot-støyen) …"
sudo mkdir -p /etc/cloud
sudo touch /etc/cloud/cloud-init.disabled
# Stopp og disable alle cloud-init-tjenester som finnes
for svc in cloud-init cloud-init-local cloud-config cloud-final \
           cloud-init.service cloud-init-local.service \
           cloud-config.service cloud-final.service; do
  sudo systemctl disable --now "$svc" 2>/dev/null || true
done
echo "  /etc/cloud/cloud-init.disabled er på plass"

# ── 2) Stille konsoll ─────────────────────────────────────────────────────
echo "2/4  Stille oppstart …"
echo 'kernel.printk = 3 4 1 3' | sudo tee /etc/sysctl.d/20-pakkemaskin-quiet.conf >/dev/null
for kandidat in /boot/firmware/cmdline.txt /boot/cmdline.txt; do
  if [[ -f "$kandidat" ]]; then
    sudo cp -n "$kandidat" "${kandidat}.bak.pakkemaskin" 2>/dev/null || true
    nå="$(tr -s ' ' < "$kandidat" | sed 's/[[:space:]]*$//')"
    grep -qw quiet <<<"$nå" || nå="$nå quiet"
    grep -q 'loglevel=' <<<"$nå" || nå="$nå loglevel=3"
    grep -qw logo.nologo <<<"$nå" || nå="$nå logo.nologo"
    echo "$nå" | sudo tee "$kandidat" >/dev/null
    echo "  $kandidat oppdatert"
    break
  fi
done

# ── 3) Installer meny + korte kommandoer ──────────────────────────────────
echo "3/4  Installerer meny og kommandoer …"
sudo cp "$KATALOG/meny" /usr/local/bin/meny
sudo chmod +x /usr/local/bin/meny
sudo cp "$KATALOG/pakkemaskin" /usr/local/bin/pakkemaskin
sudo chmod +x /usr/local/bin/pakkemaskin
echo "PAKKEMASKIN_DIR=${KATALOG}" | sudo tee /etc/pakkemaskin.conf >/dev/null
for navn in start stopp restart status logg sjekk excel porter; do
  sudo ln -sf /usr/local/bin/pakkemaskin "/usr/local/bin/$navn"
done

# ── 4) MASKER getty@tty1 — ingen login på HDMI ────────────────────────────
echo "4/4  Fjerner login på HDMI (maskerer getty@tty1) …"
sudo mkdir -p /etc/systemd/system
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

# Fjern gamle autologin-hack
sudo rm -f /etc/systemd/system/getty@tty1.service.d/autologin.conf
sudo rm -f /etc/systemd/system/pakkemaskin-frisk-konsoll.service
sudo systemctl disable pakkemaskin-frisk-konsoll.service 2>/dev/null || true
sudo rm -f /etc/profile.d/pakkemaskin-meny.sh

# MASK — viktigere enn disable (hindrer at getty.target starter den igjen)
sudo systemctl stop getty@tty1.service 2>/dev/null || true
sudo systemctl disable getty@tty1.service 2>/dev/null || true
sudo systemctl mask getty@tty1.service
sudo systemctl daemon-reload
sudo systemctl enable pakkemaskin-konsoll.service
sudo systemctl enable getty@tty2.service 2>/dev/null || true

echo
echo "=== Status ==="
echo -n "  cloud-init.disabled: "; [[ -f /etc/cloud/cloud-init.disabled ]] && echo JA || echo NEI
echo -n "  getty@tty1:          "; systemctl is-enabled getty@tty1.service 2>&1 || true
echo -n "  pakkemaskin-konsoll: "; systemctl is-enabled pakkemaskin-konsoll.service 2>&1 || true
echo
echo "Forventet etter reboot:"
echo "  • INGEN «pakkemaskin login:»"
echo "  • Tallmeny direkte (1 porter, 2 sjekk, 3 logg, …)"
echo "  • Nød-shell: Alt+F2"
echo
echo "Rebooter om 3 sekunder … (Ctrl+C for å avbryte)"
sleep 3
sudo reboot
