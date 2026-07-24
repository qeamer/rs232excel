#!/bin/bash
# Monter USB-minnepenn på /media/usb0 (kalt fra udev ved innsetting)
set -uo pipefail
DEV="${1:-}"
[[ -n "$DEV" ]] || exit 0
[[ "$DEV" == *"/"* ]] || DEV="/dev/$DEV"
# Bare partisjoner (sda1), ikke hele disken (sda)
[[ "$DEV" =~ [0-9]$ ]] || exit 0

# Ikke monter hvis noe annet allerede er på usb0
if mountpoint -q /media/usb0 2>/dev/null; then
  exit 0
fi

# Kort venting — udev kan fyre før partisjon er klar
sleep 1
[[ -b "$DEV" ]] || exit 0

mkdir -p /media/usb0
BRUKER="pi"
getent passwd pi >/dev/null || BRUKER="$(id -un 1000 2>/dev/null || echo pi)"
UID_NR="$(id -u "$BRUKER" 2>/dev/null || echo 1000)"
GID_NR="$(id -g "$BRUKER" 2>/dev/null || echo 1000)"
if mount -o "rw,noatime,uid=${UID_NR},gid=${GID_NR},umask=022" "$DEV" /media/usb0 2>/dev/null \
   || mount "$DEV" /media/usb0 2>/dev/null; then
  logger -t pakkemaskin-usb "Montert $DEV på /media/usb0"
fi
