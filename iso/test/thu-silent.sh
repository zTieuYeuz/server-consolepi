#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# ====================================================================
# THU NHANH 1 PHAN MEM CAI IM LANG (chay tren MAY BUILD, can KVM + nbd)
#
# VI SAO CO: de biet 1 bo cai chay im lang dung tham so nao, truoc day phai cai lai
# CA Windows (~40 phut) cho moi lan thu. Gio: cai Windows 1 LAN lam "may mau", moi lan
# thu chi tao 1 o dia phu (qcow2 backing file, tuc thi), chep bo cai vao, bat may,
# chay bo cai bang quyen SYSTEM y het Console System that, doc ket qua, xoa o phu.
# Moi lan thu ~3-5 phut tuy bo cai.
#
#   thu-silent.sh tao-vang <o dia qcow2 da cai xong> <mat khau Administrator>
#       Dung may mau (1 lan). O dia da cai bang kich ban Windows (tat Fast Startup -
#       tuy chon "tat_fast_startup"), tat sach may truoc khi dua vao day.
#   thu-silent.sh <bo cai> "<tham so>" [giay toi da = 600]
#       Thu 1 tham so. Vd: thu-silent.sh /tmp/vlc.exe "/S"
#   thu-silent.sh <bo cai> --tu-do [giay toi da = 420]
#       Tu doan loai bo cai (NSIS/Inno/MSI/WiX...) va thu LAN LUOT cac tham so thuong
#       gap tren cac o phu moi, dung o tham so dau tien chay im lang thanh cong.
#   Them bien GO_CAI=auto (hoac GO_CAI="<lenh go>") de thu luon pha GO CAI DAT sau khi cai:
#       "auto" doc UninstallString cua cac muc moi roi suy ra lenh go im lang (in ra "go goi y"),
#       chay thu lenh do va kiem tra go sach chua. Ket qua luu o /build/test/ket-qua-phan-mem/.
#
# Ket qua: ket_luan = xong | khong_tu_thoat | loi | qua_gio | dung_bat_thuong
#   xong / khong_tu_thoat + co muc go cai dat moi = IM LANG DUNG.
#   qua_gio = bo cai van mo (cho nguoi bam nut) = THAM SO KHONG IM LANG.
# ====================================================================
set -u
VANG=/build/test/vang
LAM=/build/test/thu-silent-tam
HERE=$(cd "$(dirname "$0")" && pwd)
GUEST=$HERE/thu-silent-guest.ps1
[ -f "$GUEST" ] || GUEST=/build/test/thu-silent-guest.ps1

if [ "${1:-}" = "tao-vang" ]; then
  SRC=${2:?thieu o dia qcow2}; MK=${3:?thieu mat khau Administrator}
  mkdir -p $VANG
  [ -f /build/test/pi-that/uefi/vars.fd ] || { echo "thieu vars.fd cua may mau"; exit 1; }
  CON=$(df -BG --output=avail /build | tail -1 | tr -dc 0-9)
  [ "$CON" -lt 12 ] && { echo "Het cho: con ${CON}G"; exit 1; }
  cp --sparse=always "$SRC" $VANG/disk.qcow2
  cp /build/test/pi-that/uefi/vars.fd $VANG/vars.fd
  modprobe nbd max_part=8
  qemu-nbd -c /dev/nbd0 $VANG/disk.qcow2; sleep 2
  mkdir -p /mnt/vang
  mount -t ntfs-3g -o rw,remove_hiberfile /dev/nbd0p3 /mnt/vang || { qemu-nbd -d /dev/nbd0; echo "khong mount rw duoc (Windows chua tat sach?)"; exit 1; }
  # Tu dang nhap MAI MAI vao Administrator (may mau chi dung de thu, khong phai may that)
  MK="$MK" python3 - <<'E'
import hivex, os
h = hivex.Hivex("/mnt/vang/Windows/System32/config/SOFTWARE", write=True)
n = h.root()
for p in ("Microsoft", "Windows NT", "CurrentVersion", "Winlogon"):
    n = h.node_get_child(n, p)
def dat(ten, gt):
    h.node_set_value(n, {"key": ten, "t": 1, "value": (gt + "\0").encode("utf-16-le")})
dat("AutoAdminLogon", "1"); dat("DefaultUserName", "Administrator")
dat("DefaultPassword", os.environ["MK"]); dat("DefaultDomainName", ".")
# AutoLogonCount=0 (con lai tu LogonCount=1 cua unattend) la "het luot" -> Windows khong tu
# dang nhap nua du AutoAdminLogon=1; AutoLogonSID cu cung phai bo (lab 04/10/2026).
con_lai = []
for v in h.node_values(n):
    k = h.value_key(v)
    if k in ("AutoLogonCount", "AutoLogonSID"):
        continue
    t, b = h.value_value(v)
    con_lai.append({"key": k, "t": t, "value": b})
h.node_set_values(n, con_lai)
h.commit(None)
print("da dat tu dang nhap Administrator")
E
  sync; umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null
  echo "MAY MAU SAN SANG: $VANG"; exit 0
fi

# Chi 1 lan thu tai 1 thoi diem (dung chung /dev/nbd0 va /mnt/vang): xep hang bang khoa.
exec 9>/build/test/thu-silent.lock
flock 9
BO_CAI=${1:?thieu duong dan bo cai}; THAMSO=${2:?thieu tham so hoac --tu-do}; TOIDA=${3:-}
[ -f "$BO_CAI" ] || { echo "Khong thay $BO_CAI"; exit 1; }
[ -f $VANG/disk.qcow2 ] || { echo "Chua co may mau - chay: $0 tao-vang <o dia> <mat khau>"; exit 1; }
[ -f "$GUEST" ] || { echo "thieu thu-silent-guest.ps1"; exit 1; }
modprobe nbd max_part=8

thu_mot() {   # $1=tham so  $2=toi da  -> in ket qua, tra 0 neu im lang dung
  local ts="$1" td="$2" ten tep
  ten=$(basename "$BO_CAI")
  mkdir -p $LAM
  # don sach moi thu con sot tu lan truoc (nbd/mount) roi moi tao o phu moi
  umount /mnt/vang 2>/dev/null; qemu-nbd -d /dev/nbd0 >/dev/null 2>&1; sleep 1
  rm -f $LAM/o.qcow2
  qemu-img create -q -f qcow2 -b $VANG/disk.qcow2 -F qcow2 $LAM/o.qcow2
  cp $VANG/vars.fd $LAM/vars.fd
  qemu-nbd -c /dev/nbd0 $LAM/o.qcow2; sleep 2
  mkdir -p /mnt/vang
  local lan_mount=0
  until mount -t ntfs-3g -o rw,remove_hiberfile /dev/nbd0p3 /mnt/vang 2>/dev/null; do
    lan_mount=$((lan_mount + 1))
    [ $lan_mount -ge 5 ] && { qemu-nbd -d /dev/nbd0 >/dev/null 2>&1; echo "mount loi"; return 2; }
    sleep 4
  done
  rm -rf /mnt/vang/ConsolePi/thu; mkdir -p /mnt/vang/ConsolePi/thu
  cp "$BO_CAI" "/mnt/vang/ConsolePi/thu/$ten"
  cp "$GUEST" /mnt/vang/ConsolePi/thu/cs-thu.ps1
  TS="$ts" TD="$td" TEN="$ten" GO="${GO_CAI:-}" python3 - <<'E'
import json, os
json.dump({"tep": "C:\\ConsolePi\\thu\\" + os.environ["TEN"], "tham_so": os.environ["TS"],
           "toi_da": int(os.environ["TD"]), "go_cai": os.environ.get("GO", "")},
          open("/mnt/vang/ConsolePi/thu/cau-hinh.json", "w"), ensure_ascii=True)
E
  mkdir -p "/mnt/vang/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp"
  printf '@echo off\r\npowershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File C:\\ConsolePi\\thu\\cs-thu.ps1\r\n' \
    > "/mnt/vang/ProgramData/Microsoft/Windows/Start Menu/Programs/StartUp/cs-thu.cmd"
  sync; umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null
  rm -f $LAM/q.pid $LAM/mon.sock
  qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m 3072 -display none -vga std \
    -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
    -drive if=pflash,format=raw,file=$LAM/vars.fd \
    -netdev user,id=n0 -device e1000,netdev=n0 \
    -drive file=$LAM/o.qcow2,if=none,id=d0 -device ahci,id=ah -device ide-hd,drive=d0,bus=ah.0 \
    -monitor unix:$LAM/mon.sock,server,nowait -pidfile $LAM/q.pid -daemonize || { echo "QEMU loi"; return 2; }
  local pid; pid=$(cat $LAM/q.pid)
  local han=$(( $(date +%s) + td + 420 ))     # +7 phut cho Windows bat may + tat may
  while kill -0 "$pid" 2>/dev/null; do
    [ "$(date +%s)" -gt "$han" ] && { echo "(het gio cho may ao - ep tat)"; kill "$pid"; sleep 3; break; }
    sleep 5
  done
  qemu-nbd -r -c /dev/nbd0 $LAM/o.qcow2; sleep 2
  mount -o ro /dev/nbd0p3 /mnt/vang 2>/dev/null
  local kq=/mnt/vang/ConsolePi/thu/ket-qua.json rc=1
  if [ -f $kq ]; then
    mkdir -p /build/test/ket-qua-phan-mem
    cp $kq "/build/test/ket-qua-phan-mem/$(basename "$BO_CAI")-$(date +%m%d-%H%M%S).json"
    python3 - "$kq" <<'E'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8-sig"))
print(f"  tham so : {d['tham_so']}")
print(f"  ket luan: {d['ket_luan']}   ma thoat: {d['ma_thoat']}   {d['giay']} giay")
if d.get("ghi_chu"): print(f"  ghi chu : {d['ghi_chu']}")
for k, nhan in (("muc_go_cai_moi", "go cai dat moi"), ("thu_muc_moi", "thu muc moi"), ("loi_tat_moi", "loi tat moi")):
    for x in d.get(k) or []: print(f"  + {nhan}: {x}")
for g in d.get("goi_y_go") or []:
    print(f"  go goi y: {g['ten']} -> {g['goi_y_go_im_lang']}")
for g in d.get("go") or []:
    print(f"  GO: {g['lenh']}  => {g['ket_luan']} (ma {g['ma_thoat']}, {g['giay']} giay) {g.get('ghi_chu') or ''}")
if d.get("sau_go"):
    print("  sau go: " + ("SACH" if d["sau_go"]["sach"] else f"CON LAI {d['sau_go']['muc_go_cai_con_lai']} {d['sau_go']['thu_muc_con_lai']}"))
# BANG CHUNG DA CAI THAT (anh Thoai 04/10/2026: "chay xong ma khong cai gi thi chet" - phan mem se ban):
# ma thoat 0 khong du. Phai co it nhat 1: muc go cai dat MOI trong registry, thu muc moi co chua
# chuong trinh (.exe/.dll that, khong chi thu muc rong), hoac loi tat moi tro toi file con ton tai.
import os
def duong(p): return "/mnt/vang/" + p[3:].replace("\\", "/")
bang_chung = []
for m in d.get("muc_go_cai_moi") or []:
    bang_chung.append(f"muc go cai dat: {m}")
for f in d.get("thu_muc_moi") or []:
    tong = chuong_trinh = 0
    for r, _ds, fs in os.walk(duong(f)):
        for x in fs:
            tong += 1
            if x.lower().endswith((".exe", ".dll")) and not x.lower().startswith("unins"): chuong_trinh += 1
    if chuong_trinh: bang_chung.append(f"thu muc {f}: {tong} file, {chuong_trinh} exe/dll")
for l in d.get("loi_tat_moi") or []:
    if os.path.exists(duong(l)): bang_chung.append(f"loi tat: {l}")
for b in bang_chung: print(f"  bang chung: {b}")
chay_ok = d["ket_luan"] in ("xong", "khong_tu_thoat")
ok = chay_ok and bool(bang_chung)
if chay_ok and not bang_chung:
    print("  !! CHAY XONG NHUNG KHONG THAY GI DUOC CAI (khong co muc go cai dat, thu muc, loi tat moi)")
print("  => IM LANG DUNG, DA CAI THAT" if ok else "  => KHONG DAT")
sys.exit(0 if ok else 1)
E
    rc=$?
  else
    echo "  (khong co file ket qua - may mau khong chay duoc runner; kiem tra tu dang nhap Administrator)"
  fi
  umount /mnt/vang 2>/dev/null; qemu-nbd -d /dev/nbd0 >/dev/null
  [ "${GIU:-0}" = 1 ] || rm -f $LAM/o.qcow2
  return $rc
}

if [ "$THAMSO" != "--tu-do" ]; then
  thu_mot "$THAMSO" "${TOIDA:-600}"; exit $?
fi

# --tu-do: doan loai bo cai roi thu lan luot
TD=${TOIDA:-420}
LOAI=$(python3 - "$BO_CAI" <<'E'
import sys
p = sys.argv[1]
if p.lower().endswith(".msi"): print("msi"); sys.exit()
b = open(p, "rb").read()
for k, v in ((b"Nullsoft", "nsis"), (b"Inno Setup", "inno"), (b"WiX Burn", "burn"), (b".wixburn", "burn"),
             (b"InstallShield", "installshield"), (b"WinRAR SFX", "sfx"), (b"Squirrel", "squirrel")):
    if k in b: print(v); sys.exit()
print("la")
E
)
echo "Loai bo cai doan duoc: $LOAI"
case $LOAI in
  msi)          UNG=("/qn /norestart" "/quiet /norestart") ;;
  nsis)         UNG=("/S") ;;
  inno)         UNG=("/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" "/SILENT /SUPPRESSMSGBOXES /NORESTART") ;;
  burn)         UNG=("/quiet /norestart" "/passive /norestart") ;;
  installshield) UNG=('/s /v"/qn /norestart"' '/s /v"/qn"') ;;
  sfx)          UNG=("-s2 -y" "-s -y" "/S" "-s1") ;;
  squirrel)     UNG=("--silent" "-s") ;;
  *)            UNG=("/S" "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART" "/quiet /norestart" "/qn /norestart" "/silent" "/s /v\"/qn\"" "-s" "--silent") ;;
esac
for ts in "${UNG[@]}"; do
  echo "== Thu: $ts"
  if thu_mot "$ts" "$TD"; then echo; echo "THAM SO IM LANG: $ts"; exit 0; fi
done
echo; echo "KHONG tham so nao trong danh sach chay im lang. Can xem tai lieu cua phan mem."
exit 1
