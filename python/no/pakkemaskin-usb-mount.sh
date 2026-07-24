#!/bin/bash
# Monter USB-minnepenn på /media/usb0 (kalt fra udev)
set -euo pipefail
DEV="${1:-}"
[[ -n "$DEV" ]] || exit 0
[[ "$DEV" == *"/"* ]] || DEV="/dev/$DEV"
# Bare partisjoner (sda1), ikke hele disken (sda)
[[ "$DEV" =~ [0-9]$ ]] || exit 0

# Ikke monter hvis noe annet allerede er på usb0
if mountpoint -q /media/usb0 2>/dev/null; then
  exit 0
fi

mkdir -p /media/usb0
# pi-bruker skal kunne skrive CSV
BRUKER="$(getent passwd pi >/dev/null && echo pi || id -un 1000 2>/dev/null || echo pi)"
mount -o "rw,noatime,uid=$(id -u "$BRUKER"),gid=$(id -g "$BRUKER"),umask=022" "$DEV" /media/usb0 2>/dev/null \
  || mount "$DEV" /media/usb0
logger -t pakkemaskin-usb "Montert $DEV på /media/usb0"
