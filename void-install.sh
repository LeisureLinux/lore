#!/bin/sh
# void-install.sh - https://freelamp.com/void-install.sh
#
# Shortest possible entry point on a Void live CD. Usage (one line):
#   xbps-uhelper fetch 'https://freelamp.com/void-install.sh>/tmp/v'&&sudo sh /tmp/v --user alice
#
# Why xbps-uhelper: it ships with the Void live CD; no curl/wget/python3,
# no mirror change and no package install needed. It fetches this file, which then
# fetches the real bootstrap (scripts/void-bootstrap.sh) and forwards args unchanged.
#
# Scenario B (local USB live CD): --user alice is enough, no pubkey needed;
# after reboot use local console + initial password (sshd is publickey-only, so no SSH login).
# Scenario A (host-driven VM): use void-live-provision.sh --ip <IP>.
#
# With no args it only downloads the bootstrap and prints usage; never wipes the disk.

set -eu
# Pin a commit to avoid raw.githubusercontent.com master CDN cache delay
PIN=6f88f33
BASE="https://raw.githubusercontent.com/LeisureLinux/bilibili/$PIN/scripts"
OUT="${TMPDIR:-/tmp}/void-bootstrap.sh"

xbps-uhelper fetch "$BASE/void-bootstrap.sh>$OUT" >/dev/null 2>&1 || {
  printf 'download failed: %s/void-bootstrap.sh\n' "$BASE" >&2
  exit 1
}
exec sudo sh "$OUT" "$@"
