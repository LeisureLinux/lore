#!/bin/sh
# void-install.sh — https://freelamp.com/void-install.sh
#
# Void live CD 里【敲得最少】的入口。用法（一行）：
#   xbps-uhelper fetch 'https://freelamp.com/void-install.sh>/tmp/v'&&sudo sh /tmp/v --user alice
#
# 为什么用 xbps-uhelper：Void 官方 live CD 自带它，不需要 curl/wget/python3，
# 不需要换源、不需要装任何包。它下载本文件后，再由本文件取回真正的
# bootstrap（scripts/void-bootstrap.sh）并把参数原样交给它。
#
# 场景 B（USB 本机 live CD）：--user alice 即可，不需要 pubkey；
# 重启后用本地 console + 初始口令登录（sshd 仍只认公钥，故无 SSH 登录）。
# 场景 A（从 host 远程驱动虚机）：用 void-live-provision.sh --ip <IP>。
#
# 不带任何参数时只下载 bootstrap 并打印用法，绝不抹盘。

set -eu
# pin 到确定提交，避免 raw.githubusercontent.com 的 master CDN 缓存延迟
PIN=82599d6
BASE="https://raw.githubusercontent.com/LeisureLinux/bilibili/$PIN/scripts"
OUT="${TMPDIR:-/tmp}/void-bootstrap.sh"

xbps-uhelper fetch "$BASE/void-bootstrap.sh>$OUT" >/dev/null 2>&1 || {
  printf '下载失败: %s/void-bootstrap.sh\n' "$BASE" >&2
  exit 1
}
exec sudo sh "$OUT" "$@"
