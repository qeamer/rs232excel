#!/usr/bin/env bash
# fiks-usb.sh — auto-monter minnepenn på /media/usb0 + sjekk status
set -euo pipefail

KATALOG="$(cd "$(dirname "$0")" && pwd)"
BRUKER="${SUDO_USER:-${USER}}"

echo "=== USB-minnepenn for pakkemaskin ==="
echo

echo "1/3  Installerer auto-mount …"
sudo mkdir -p /media/usb0
sudo chown "$BRUKER:$BRUKER" /media/usb0 2>/dev/null || true
sudo cp "$KATALOG/pakkemaskin-usb-mount.sh" /usr/local/sbin/pakkemaskin-usb-mount.sh
sudo cp "$KATALOG/pakkemaskin-usb-umount.sh" /usr/local/sbin/pakkemaskin-usb-umount.sh
sudo chmod +x /usr/local/sbin/pakkemaskin-usb-mount.sh /usr/local/sbin/pakkemaskin-usb-umount.sh
sudo cp "$KATALOG/99-pakkemaskin-usb.rules" /etc/udev/rules.d/99-pakkemaskin-usb.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "2/3  Prøver å montere nå …"
# Hvis penn allerede sitter i: finn første USB-partisjon og monter
for part in /dev/sd[a-z][0-9]; do
  [[ -b "$part" ]] || continue
  if lsblk -no TRAN "${part%%[0-9]*}" 2>/dev/null | grep -qi usb \
     || udevadm info --query=property --name="$part" 2>/dev/null | grep -q ID_USB; then
    if ! mountpoint -q /media/usb0; then
      sudo /usr/local/sbin/pakkemaskin-usb-mount.sh "$part" && break
    fi
  fi
done
# Fallback: monter første sda1 hvis umontert
if ! mountpoint -q /media/usb0 && [[ -b /dev/sda1 ]]; then
  sudo /usr/local/sbin/pakkemaskin-usb-mount.sh /dev/sda1 || true
fi

echo "3/3  Status …"
echo
echo "USB-enheter (lsusb):"
lsusb 2>/dev/null || echo "  (lsusb ikke tilgjengelig)"
echo
echo "Disker (lsblk):"
lsblk -o NAME,SIZE,TYPE,TRAN,MOUNTPOINT 2>/dev/null || lsblk
echo
if mountpoint -q /media/usb0; then
  echo "OK — minnepenn montert på /media/usb0"
  df -h /media/usb0
  echo
  echo "Innhold:"
  ls -la /media/usb0 | head -n 20
else
  echo "IKKE montert."
  echo "  1. Sjekk at pennen sitter i hubben (samme hub som tastatur)"
  echo "  2. Trekk ut og sett inn igjen"
  echo "  3. Kjør:  status"
fi
echo
echo "Deretter:  restart   (så fangsten speiler til pennen)"
