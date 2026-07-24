#!/usr/bin/env bash
# Startes av agetty på tty1 — TTY/tastatur settes opp riktig, deretter meny.
set -euo pipefail
BRUKER="$(id -un)"
export HOME="$(getent passwd "$BRUKER" | cut -d: -f6)"
export USER="$BRUKER"
export LOGNAME="$BRUKER"
export SHELL=/bin/bash
export TERM="${TERM:-linux}"
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PAKKEMASKIN_MENY_KJORT=1
cd "$HOME" 2>/dev/null || cd /
exec /usr/local/bin/meny
