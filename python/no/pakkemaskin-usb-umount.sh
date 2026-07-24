#!/bin/bash
# Avmonter /media/usb0 når minnepennen trekkes ut
set -euo pipefail
if mountpoint -q /media/usb0 2>/dev/null; then
  umount /media/usb0 2>/dev/null || umount -l /media/usb0 2>/dev/null || true
  logger -t pakkemaskin-usb "Avmontert /media/usb0"
fi
