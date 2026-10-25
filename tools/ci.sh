#!/bin/bash
# B9: cong chat luong chay MOT LENH truoc khi dong ban. Dung: tools/ci.sh [nhanh]   ("nhanh" bo qua pytest day du ~5 phut)
# Cong cu o /opt/devtools (xem docs/dai-tu-2.0/B9-ghi-chu.md); ghi de duong dan bang DEVTOOLS=...
set -u
cd "$(dirname "$0")/.."
DEV="${DEVTOOLS:-/opt/devtools}"
SP="$(ls -d "$DEV"/lib/python3*/site-packages 2>/dev/null | head -1)"
export PYTHONPATH="${SP:-}${PYTHONPATH:+:$PYTHONPATH}"
loi=0
buoc() { echo; echo "=== $1"; shift; "$@" || { echo "!!! THAT BAI: $*"; loi=$((loi + 1)); }; }

buoc "ruff (loi that + nuot loi)"            "$DEV/bin/ruff" check src tests tools
buoc "kien truc import (import-linter)"      env PYTHONPATH="src:$PYTHONPATH" "$DEV/bin/lint-imports" --config tools/importlinter.ini
buoc "Python 3.11 cu phap (may dich Debian 12)" bash iso/test/kiem-python311.sh
buoc "bandit (muc cao)"                      "$DEV/bin/bandit" -q -r src -ll -ii --exit-zero -f txt -o /tmp/bandit-cs.txt
if [ "${1:-}" != "nhanh" ]; then
  buoc "pytest + do phu (core, services)"    python3 -m coverage run --source=src/consolesystem -m pytest tests -q
  buoc "nguong do phu core"                  python3 -m coverage report --include='src/consolesystem/core/*' --fail-under="${NGUONG_PHU_CORE:-70}"
fi
echo
[ "$loi" = 0 ] && echo "CI XANH" || { echo "CI DO: $loi buoc that bai"; exit 1; }
