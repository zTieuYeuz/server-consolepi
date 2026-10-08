#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# THU THAT cai-font.ps1 tren may mau Windows 10 (/build/test/vang - xem thu-silent.sh tao-vang).
#   thu-font.sh [so_font = 12]
# Dung 1 bo font thu tu font co san tren may build (+ 1 file .ttc, 1 file ten tieng Viet, 1 file TRUNG TEN
# arial.ttf noi dung khac), chep vao o phu qcow2 NHU deploy.cmd lam, bat may, chay cai-font.ps1 bang SYSTEM
# 2 lan, khoi dong lai, doc ket qua. Chi 1 lan thu tai 1 thoi diem (chung khoa voi thu-silent.sh).
set -u
VANG=/build/test/vang; LAM=/build/test/thu-font-tam; HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd); N=${1:-12}
[ -f $VANG/disk.qcow2 ] || { echo "Chua co may mau $VANG"; exit 1; }
exec 9>/build/test/thu-silent.lock; flock 9
modprobe nbd max_part=8
rm -rf $LAM; mkdir -p $LAM/bo; cd $LAM
# --- dung bo font thu
python3 - "$N" "$REPO" <<'E'
import os, sys, shutil, struct, json, subprocess, glob
n, repo = int(sys.argv[1]), sys.argv[2]
sys.path.insert(0, repo + "/src")
from ui import fontinfo as F
dst = "/build/test/thu-font-tam/bo"
ttf = sorted(glob.glob("/usr/share/fonts/truetype/**/*.ttf", recursive=True))
ttf = [p for p in ttf if "Emoji" not in p][:n]
for p in ttf: shutil.copy(p, dst)
otf = sorted(glob.glob("/usr/share/fonts/**/*.otf", recursive=True))[:2]
for p in otf: shutil.copy(p, dst)
# .ttc 2 kieu
def dich(data, delta):
    k = struct.unpack(">H", data[4:6])[0]; b = bytearray(data)
    for i in range(k):
        o = 12 + i * 16 + 8; v = struct.unpack(">I", b[o:o+4])[0]; b[o:o+4] = struct.pack(">I", v + delta)
    return bytes(b)
a = open("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "rb").read()
b = open("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "rb").read()
h = 12 + 8
open(dst + "/liberation-gop.ttc", "wb").write(b"ttcf" + struct.pack(">HHI", 1, 0, 2) + struct.pack(">II", h, h + len(a)) + dich(a, h) + dich(b, h + len(a)))
# ten file tieng Viet
shutil.copy("/usr/share/fonts/truetype/quicksand/Quicksand-Bold.ttf", dst + "/Phông Việt Thử.ttf")
# TRUNG TEN arial.ttf nhung la font khac -> phai bi canh bao, KHONG ghi de font he thong
shutil.copy("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", dst + "/arial.ttf")
ds = F.lam_moi_danh_sach(dst)
ho = set()
for m in ds:
    if m["file"] == "arial.ttf": continue
    out = subprocess.run(["fc-scan", "--format", "%{family[0]}\n", os.path.join(dst, m["file"])], capture_output=True, text=True).stdout.splitlines()
    ho.update(x.strip() for x in out if x.strip())
json.dump({"ho_mong_doi": sorted(ho), "so_font": len(ds)}, open("/build/test/thu-font-tam/mong-doi.json", "w"))
print(f"bo thu: {len(ds)} font ({len(ho)} ho chu mong doi), co ttc + ten Viet + arial.ttf gia")
E
# --- o phu
umount /mnt/vang 2>/dev/null; qemu-nbd -d /dev/nbd0 >/dev/null 2>&1; sleep 1
qemu-img create -q -f qcow2 -b $VANG/disk.qcow2 -F qcow2 $LAM/o.qcow2
cp $VANG/vars.fd $LAM/vars.fd
qemu-nbd -c /dev/nbd0 $LAM/o.qcow2; sleep 2
mkdir -p /mnt/vang
try=0; until mount -t ntfs-3g -o rw,remove_hiberfile /dev/nbd0p3 /mnt/vang 2>/dev/null; do try=$((try+1)); [ $try -ge 5 ] && { qemu-nbd -d /dev/nbd0; echo "mount loi"; exit 2; }; sleep 4; done
# chep DUNG nhu deploy.cmd: cai-font.ps1 + thu muc bo font (bo _thongtin.json)
rm -rf /mnt/vang/ConsolePi/fonts /mnt/vang/ConsolePi/thuf /mnt/vang/ConsolePi/cai-font.ps1
mkdir -p /mnt/vang/ConsolePi/fonts /mnt/vang/ConsolePi/thuf
cp -r $LAM/bo /mnt/vang/ConsolePi/fonts/thuf
python3 - "$REPO" <<'E'
import sys; sys.path.insert(0, sys.argv[1] + "/src")
import tempfile
from ui import unattend as U
open("/mnt/vang/ConsolePi/cai-font.ps1", "w", encoding="utf-8-sig", newline="").write(U.sinh_ps_cai_font())
E
cp "$HERE/thu-font-guest.ps1" /mnt/vang/ConsolePi/thuf/cs-thuf.ps1
python3 - <<'E'
import json, subprocess
m = json.load(open("/build/test/thu-font-tam/mong-doi.json"))
h = subprocess.run(["sha256sum", "/mnt/vang/Windows/Fonts/arial.ttf"], capture_output=True, text=True).stdout.split()[0].upper()
m["arial_hash"] = h
json.dump(m, open("/mnt/vang/ConsolePi/thuf/cau-hinh.json", "w"), ensure_ascii=True)
E
mkdir -p "/mnt/vang/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp"
printf '@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\\ConsolePi\\thuf\\cs-thuf.ps1\r\n' \
  > "/mnt/vang/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp/cs-thuf.cmd"
sync; umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null
rm -f $LAM/q.pid $LAM/mon.sock
qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m 3072 -display none -vga std \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=$LAM/vars.fd \
  -netdev user,id=n0 -device e1000,netdev=n0 \
  -drive file=$LAM/o.qcow2,if=none,id=d0 -device ahci,id=ah -device ide-hd,drive=d0,bus=ah.0 \
  -monitor unix:$LAM/mon.sock,server,nowait -pidfile $LAM/q.pid -daemonize || { echo "QEMU loi"; exit 2; }
pid=$(cat $LAM/q.pid); han=$(( $(date +%s) + 1500 ))
echo "may mau dang chay (pha 1 -> khoi dong lai -> pha 2 -> tat), toi da 25 phut..."
while kill -0 "$pid" 2>/dev/null; do
  [ "$(date +%s)" -gt "$han" ] && { echo "(het gio - ep tat)"; kill "$pid"; sleep 3; break; }
  sleep 5
done
qemu-nbd -r -c /dev/nbd0 $LAM/o.qcow2; sleep 2
mount -o ro /dev/nbd0p3 /mnt/vang 2>/dev/null
KQ=/mnt/vang/ConsolePi/thuf/ket-qua.json; rc=1
if [ -f $KQ ]; then
  cp $KQ $LAM/ket-qua.json
  python3 - "$LAM/ket-qua.json" <<'E'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8-sig"))
ok = True
def dat(c, t):
    global ok
    ok = ok and c
    print(("DAT  " if c else "LOI  ") + t)
lan = d.get("lan") or []
dat(len(lan) == 2, "pha 1 chay du 2 lan")
for x in lan:
    print(f"     lan {x['lan']}: ma thoat tac vu={x['ma_thoat']}  da cai {x['da_cai']}/{x['tong']}  loi={x['loi']}  canh bao={x['canh_bao']}")
if len(lan) == 2:
    dat(all(x["ma_thoat"] == 0 for x in lan), "ca 2 lan thoat ma 0 (khong loi)")
    dat(lan[0]["da_cai"] == lan[1]["da_cai"] == lan[0]["tong"] - 1, "da cai = tong - 1 (chi arial.ttf trung ten bi bo) o ca 2 lan -> chay lap on dinh")
    dat(len(lan[0]["canh_bao"]) == 1 and "arial.ttf" in lan[0]["canh_bao"][0], "arial.ttf trung ten font he thong: CANH BAO, khong ghi de")
dat(d.get("hoan_tat") is True, "pha 2 (sau khoi dong lai) chay xong")
f = d.get("pha2_font") or []
thieu = [x["file"] for x in f if x["file"] != "arial.ttf" and not (x["file_co"] and x["reg_co"])]
dat(f and not thieu, f"sau khoi dong lai: {len(f)-1} font deu co file trong C:\\Windows\\Fonts + registry dung" + (f" - THIEU {thieu}" if thieu else ""))
dat(not d.get("ho_thieu"), f"ung dung (GDI+) thay du {len(d.get('ho_mong_doi', []))} ho chu" + (f" - THIEU {d['ho_thieu']}" if d.get("ho_thieu") else ""))
dat(d.get("arial_con_nguyen") is True, "font he thong arial.ttf con nguyen")
print("=> THANH CONG" if ok else "=> KHONG DAT")
sys.exit(0 if ok else 1)
E
  rc=$?
else
  echo "(khong co ket qua - may mau khong chay duoc runner)"
fi
umount /mnt/vang 2>/dev/null; qemu-nbd -d /dev/nbd0 >/dev/null
[ "${GIU:-0}" = 1 ] || rm -f $LAM/o.qcow2
exit $rc
