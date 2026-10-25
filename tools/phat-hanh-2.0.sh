#!/bin/bash
# Dung goi cap nhat (.cspkg) + danh muc da ky TU CAY NGUON HIEN TAI, khong dong vao VERSION/commit cua repo.
#   tools/phat-hanh-2.0.sh --phien-ban 2.0.0 --so-phat-hanh 1 [--ban-truoc 1.9.5] [--kenh on-dinh] [--kien-truc amd64]
#                          [--khoa /root/khoa-that] [--ra /root/phat-hanh-2.0] [--han-ngay 7] [--ghi-chu "..."]
# Hoi MAT KHAU khoa phat-hanh MOT LAN (o nhap an, khong hien, khong luu). Ket qua trong --ra:
#   console-system-<ban>-<kt>.cspkg + .khoa-goi.json (BI MAT - chi dua cho kho) + danh-muc-<kenh>.json + tin-cay.json (neu co)
set -euo pipefail
cd "$(dirname "$0")/.."
PB=""; SO=""; TRUOC=""; KENH="on-dinh"; KT="amd64"; KHOA="/root/khoa-that"; RA=""; HAN=7; GHICHU=""
while [ $# -gt 0 ]; do case "$1" in
  --phien-ban) PB="$2"; shift 2;; --so-phat-hanh) SO="$2"; shift 2;; --ban-truoc) TRUOC="$2"; shift 2;;
  --kenh) KENH="$2"; shift 2;; --kien-truc) KT="$2"; shift 2;; --khoa) KHOA="$2"; shift 2;;
  --ra) RA="$2"; shift 2;; --han-ngay) HAN="$2"; shift 2;; --ghi-chu) GHICHU="$2"; shift 2;;
  *) echo "tham so la: $1"; exit 2;; esac; done
[ -n "$PB" ] && [ -n "$SO" ] || { sed -n 2,8p "$0"; exit 2; }
RA="${RA:-/root/phat-hanh-$PB}"
[ -f "$KHOA/phat-hanh.khoa-rieng.json" ] || { echo "Khong thay $KHOA/phat-hanh.khoa-rieng.json"; exit 1; }
python3 - <<'PY' || { echo "Chua nhung KHOA GOC that vao ma (khoa_goc.json) - chay tools/gan-khoa-goc.py truoc"; exit 1; }
import json,sys
sys.exit(0 if json.load(open("src/consolesystem/core/capnhat/khoa_goc.json")).get("khoa_cong_khai") else 1)
PY
TAM="$(mktemp -d /var/tmp/ph20.XXXXXX)"; trap 'rm -rf "$TAM"' EXIT
mkdir -p "$TAM/nguon" "$RA"; chmod 700 "$RA"
tar --exclude=.git --exclude=__pycache__ --exclude='*.pyc' --exclude=.ruff_cache --exclude=iso -cf - . | tar -xf - -C "$TAM/nguon"
echo "$PB" > "$TAM/nguon/VERSION"; echo "$SO" > "$TAM/nguon/SO_PHAT_HANH"
python3 - "$TAM" <<'PY'
import sys; sys.path.insert(0, "src")
from consolesystem.core import phathanh as PH
tam = sys.argv[1]
ten = PH.tao_ban(tam + "/nguon", tam + "/opt")
print("da dung cay phat hanh:", ten, "| kiem tung file:", PH.kiem_ban(tam + "/opt", ten) or "nguyen ven")
PY
if [ -z "${CS_KHOA_MAT_KHAU_PHAT_HANH:-}" ]; then
  read -r -s -p "Mat khau khoa PHAT-HANH (khong hien khi go): " CS_KHOA_MAT_KHAU_PHAT_HANH; echo
  export CS_KHOA_MAT_KHAU_PHAT_HANH
fi
GOI="$RA/console-system-$PB-$KT.cspkg"
ARGS=(goi --khoa "$KHOA" --ban "$TAM/opt/releases/$PB" --phien-ban "$PB" --so-phat-hanh "$SO" --kien-truc "$KT" --kenh "$KENH" --ha-cap-toi-thieu "${TRUOC:-$PB}" --ra "$GOI")
[ -n "$TRUOC" ] && ARGS+=(--ban-truoc "$TRUOC")
[ -n "$GHICHU" ] && ARGS+=(--ghi-chu "$GHICHU")
python3 tools/phat-hanh-ky.py "${ARGS[@]}"
SOHIEU="$(date +%s)"
python3 tools/phat-hanh-ky.py danh-muc --khoa "$KHOA" --kenh "$KENH" --so-hieu "$SOHIEU" --han-ngay "$HAN" --ra "$RA/danh-muc-$KENH.json" "$GOI"
[ -f "$KHOA/tin-cay.json" ] && cp "$KHOA/tin-cay.json" "$RA/tin-cay.json"
unset CS_KHOA_MAT_KHAU_PHAT_HANH
echo "--- kiem lai goi nhu may khach (chu ky + tai lieu tin cay):"
python3 tools/kiem-goi.py "$GOI" --goc "$KHOA/goc.khoa-cong-khai.json" --tin-cay "$RA/tin-cay.json" || { echo "!!! KIEM LAI THAT BAI - KHONG nap goi nay"; exit 1; }
( cd "$RA" && sha256sum * > SHA256SUMS.txt )
echo; echo "XONG -> $RA"; ls -la "$RA"
echo "Buoc tiep (tren may KHO .34): nap-ban.py goi / danh-muc $KENH / tin-cay. CHI .khoa-goi.json la bi mat: dua cho kho, khong dua len Drive."
