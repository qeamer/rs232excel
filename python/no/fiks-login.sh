#!/usr/bin/env bash
# fiks-login.sh — HARD fiks for hengende login + tastatur på HDMI-meny
#
# Kjør via SSH:
#   cd ~/rs232excel && git pull origin cursor/pakkemaskin-cli-ef03
#   cd python/no && bash fiks-login.sh
#
set -euo pipefail

BRUKER="${SUDO_USER:-${USER}}"
if [[ "$BRUKER" == "root" ]]; then
  echo "Kjør som pi (ikke root)." >&2
  exit 1
fi
HJEM="$(getent passwd "$BRUKER" | cut -d: -f6)"
KATALOG="$(cd "$(dirname "$0")" && pwd)"

echo "=== HARD fiks: HDMI-meny med fungerende tastatur ==="
echo

# ── 1) cloud-init (støyen som ødela login) ────────────────────────────────
echo "1/4  Skrur av cloud-init …"
sudo mkdir -p /etc/cloud
sudo touch /etc/cloud/cloud-init.disabled
for svc in cloud-init cloud-init-local cloud-config cloud-final \
           cloud-init.service cloud-init-local.service \
           cloud-config.service cloud-final.service; do
  sudo systemctl disable --now "$svc" 2>/dev/null || true
done
echo "  cloud-init.disabled OK"

# ── 2) Stille konsoll ─────────────────────────────────────────────────────
echo "2/4  Stille oppstart …"
echo 'kernel.printk = 3 4 1 3' | sudo tee /etc/sysctl.d/20-pakkemaskin-quiet.conf >/dev/null
for kandidat in /boot/firmware/cmdline.txt /boot/cmdline.txt; do
  if [[ -f "$kandidat" ]]; then
    sudo cp -n "$kandidat" "${kandidat}.bak.pakkemaskin" 2>/dev/null || true
    cmdline="$(tr -s ' ' < "$kandidat" | sed 's/[[:space:]]*$//')"
    grep -qw quiet <<<"$cmdline" || cmdline="$cmdline quiet"
    grep -q 'loglevel=' <<<"$cmdline" || cmdline="$cmdline loglevel=3"
    grep -qw logo.nologo <<<"$cmdline" || cmdline="$cmdline logo.nologo"
    echo "$cmdline" | sudo tee "$kandidat" >/dev/null
    echo "  $kandidat oppdatert"
    break
  fi
done

# ── 3) Kommandoer + meny ──────────────────────────────────────────────────
echo "3/4  Installerer meny og kommandoer …"
sudo cp "$KATALOG/meny" /usr/local/bin/meny
sudo chmod +x /usr/local/bin/meny
sudo cp "$KATALOG/pakkemaskin" /usr/local/bin/pakkemaskin
sudo chmod +x /usr/local/bin/pakkemaskin
sudo cp "$KATALOG/pakkemaskin-autologin.sh" /usr/local/sbin/pakkemaskin-autologin.sh
sudo chmod +x /usr/local/sbin/pakkemaskin-autologin.sh
# Sørg for at autologin-scriptet bruker riktig hjemmemappe
echo "PAKKEMASKIN_DIR=${KATALOG}" | sudo tee /etc/pakkemaskin.conf >/dev/null
for navn in start stopp restart status logg sjekk excel porter; do
  sudo ln -sf /usr/local/bin/pakkemaskin "/usr/local/bin/$navn"
done

# ── 4) agetty autologin → meny (RIKTIG TTY = tastatur virker) ─────────────
echo "4/4  Setter opp HDMI via agetty (ikke egen TTY-service) …"

# Fjern den gamle konsoll-tjenesten som tok tty1 uten skikkelig tastatur-init
sudo systemctl disable --now pakkemaskin-konsoll.service 2>/dev/null || true
sudo rm -f /etc/systemd/system/pakkemaskin-konsoll.service
sudo rm -f /etc/systemd/system/pakkemaskin-frisk-konsoll.service
sudo systemctl disable pakkemaskin-frisk-konsoll.service 2>/dev/null || true
sudo rm -f /etc/profile.d/pakkemaskin-meny.sh

# Avmasker getty@tty1 om den ble maskert tidligere
sudo systemctl unmask getty@tty1.service 2>/dev/null || true

# agetty setter opp tastatur/TTY, hopper over login, kjører meny direkte
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d
sudo tee /etc/systemd/system/getty@tty1.service.d/pakkemaskin.conf >/dev/null <<'EOF'
[Service]
ExecStart=
# -n = skip login prompt, -l = vårt script (meny) i stedet for /bin/login
# agetty initialiserer tty1 riktig → tastatur fungerer
ExecStart=-/sbin/agetty --noclear -n -l /usr/local/sbin/pakkemaskin-autologin.sh tty1 linux
Type=idle
Restart=always
EOF

sudo systemctl daemon-reload
sudo systemctl enable getty@tty1.service
sudo systemctl enable getty@tty2.service 2>/dev/null || true
sudo systemctl restart getty@tty1.service

echo
echo "=== Status ==="
echo -n "  cloud-init.disabled: "; [[ -f /etc/cloud/cloud-init.disabled ]] && echo JA || echo NEI
echo -n "  getty@tty1:          "; systemctl is-enabled getty@tty1.service 2>&1 || true
echo -n "  autologin-script:    "; [[ -x /usr/local/sbin/pakkemaskin-autologin.sh ]] && echo JA || echo NEI
echo -n "  meny:                "; [[ -x /usr/local/bin/meny ]] && echo JA || echo NEI
systemctl --no-pager -l status getty@tty1.service 2>&1 | head -n 15 || true
echo
echo "Forventet på HDMI:"
echo "  • Meny (ikke login)"
echo "  • Tastatur skal virke (skriv 1, 2, 3 …)"
echo "  • Nød-shell: Alt+F2"
echo
echo "Rebooter om 3 sekunder … (Ctrl+C for å avbryte)"
sleep 3
sudo reboot
