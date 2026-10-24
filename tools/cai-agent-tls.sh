#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# Bat cong mTLS 8443 cho AGENT cua Quan ly may tram: tao CA rieng + chung chi may chu (neu chua co), ghi
# /etc/nginx/conf.d/console-pi-agent-tls.conf, nginx -t, nap lai. Loi thi tra ban cu. Chay: sudo bash cai-agent-tls.sh
[ "$(id -u)" = 0 ] || { echo "Chay bang sudo."; exit 1; }
D=${CONSOLE_PI_DIR:-/opt/console-pi}
[ -d "$D/ui" ] || D="$(cd "$(dirname "$0")/.." && pwd)/src"
cd "$D" || exit 1
PYTHONPATH="$D" python3 - <<'PYEOF'
import sys
from ui import uem_pki
ok, tb = uem_pki.bat_tls()
print(tb)
sys.exit(0 if ok else 1)
PYEOF
