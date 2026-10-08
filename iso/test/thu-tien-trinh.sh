#!/bin/bash
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
# THU THAT cua so tien trinh + popup tong ket tren may mau Windows 10 (/build/test/vang), KHONG cai lai
# Windows: sinh tien-trinh.ps1 + bao-cao.ps1 tu 1 kich ban thu, dat vao C:\ConsolePi, chay bang DUNG
# lenh FirstLogonCommands (unattend.LENH_MO_TIEN_TRINH, qua RunOnce cua HKLM - cung chay trong phien
# dang nhap), chup man hinh moi 3 giay vao /build/test/thu-tien-trinh/anh-*.png de XEM TAN MAT:
# khong co cua so console, 1 cua so tien trinh, xong thi chi con popup tong ket.
#   thu-tien-trinh.sh [giay chup = 420]
set -u
VANG=/build/test/vang; LAM=/build/test/thu-tien-trinh; HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd); GIAY=${1:-420}
[ -f $VANG/disk.qcow2 ] || { echo "Chua co may mau $VANG"; exit 1; }
exec 9>/build/test/thu-silent.lock; flock 9
modprobe nbd max_part=8
rm -rf $LAM; mkdir -p $LAM
umount /mnt/vang 2>/dev/null; qemu-nbd -d /dev/nbd0 >/dev/null 2>&1; sleep 1
qemu-img create -q -f qcow2 -b $VANG/disk.qcow2 -F qcow2 $LAM/o.qcow2
cp $VANG/vars.fd $LAM/vars.fd
qemu-nbd -c /dev/nbd0 $LAM/o.qcow2; sleep 2
mkdir -p /mnt/vang
try=0; until mount -t ntfs-3g -o rw,remove_hiberfile /dev/nbd0p3 /mnt/vang 2>/dev/null; do try=$((try+1)); [ $try -ge 5 ] && { qemu-nbd -d /dev/nbd0; echo "mount loi"; exit 2; }; sleep 4; done
rm -rf /mnt/vang/ConsolePi; mkdir -p /mnt/vang/ConsolePi
CONSOLE_PI_DATA=$(mktemp -d) python3 - "$REPO" <<'E'
import sys, glob, shutil, os
sys.path.insert(0, sys.argv[1] + "/src")
from ui import unattend as U, deployos as D, fontinfo as F
d = dict(D._cauhinh_mac_dinh("truc_tiep"))
d.update({"os_ho": "windows", "os_id": "x", "ten_may": "PC-THU", "ten_kichban": "Thu cua so tien trinh"})
zip_ud = os.environ.get("UNGDUNG_ZIP", "")
if zip_ud:
    # Ung dung nhieu file (vd Office 2019 tu kho): giai nen + dat lenh DUNG nhu Console System lam,
    # chep sang may nhu deploy.cmd (robocopy /XF _thongtin.json), cai bang buoc SYSTEM that.
    ok, _m, ud = D.tao_ungdung_moi(os.environ.get("UNGDUNG_TEN", "Ung dung thu"))
    tam = os.path.join(D.UNGDUNG_DIR, ud, os.path.basename(zip_ud)); shutil.copy(zip_ud, tam)
    print("giai nen:", D.giai_nen_ungdung(ud, tam)); print("lenh:", D.dat_lenh_cai_ungdung(ud, os.environ["UNGDUNG_LENH"]))
    shutil.copytree(os.path.join(D.UNGDUNG_DIR, ud), "/mnt/vang/ConsolePi/ungdung/" + ud, ignore=shutil.ignore_patterns("_thongtin.json"))
    d["ungdung"] = [{"id": ud}]
    open("/build/test/thu-tien-trinh/ungdung-id.txt", "w").write(ud)
else:
    # 1 bo font nho -> co 1 buoc chay bang SYSTEM that (tac vu hen gio) + 2 lenh them chay o phien nguoi dung
    ok, _m, bo = D.tao_bo_font("Font thu")
    for p in sorted(glob.glob("/usr/share/fonts/truetype/quicksand/*.ttf")): shutil.copy(p, os.path.join(D.FONTS_DIR, bo))
    F.lam_moi_danh_sach(os.path.join(D.FONTS_DIR, bo))
    shutil.copytree(os.path.join(D.FONTS_DIR, bo), "/mnt/vang/ConsolePi/fonts/" + bo, ignore=shutil.ignore_patterns("_thongtin.json"))
    d.update({"fonts": [bo], "lenh_them": "ping -n 12 127.0.0.1\nping -n 8 127.0.0.1"})
f = U.sinh_file_nhung(d, "127.0.0.9")
for ten in ("tien-trinh.ps1", "bao-cao.ps1", "cai-font.ps1"):
    if ten in f:
        open("/mnt/vang/ConsolePi/" + ten, "w", encoding="utf-8-sig", newline="").write(f[ten])
open("/build/test/thu-tien-trinh/lenh.txt", "w").write(U.LENH_MO_TIEN_TRINH)
print("lenh mo:", U.LENH_MO_TIEN_TRINH)
E
# RunOnce cua HKLM (offline hive) = DUNG lenh FirstLogonCommands se chay
LENH="$(cat $LAM/lenh.txt)" python3 - <<'E'
import hivex, os
h = hivex.Hivex("/mnt/vang/Windows/System32/config/SOFTWARE", write=True)
n = h.root()
for p in ("Microsoft", "Windows", "CurrentVersion"):
    n = h.node_get_child(n, p)
c = h.node_get_child(n, "RunOnce") or h.node_add_child(n, "RunOnce")
h.node_set_value(c, {"key": "ConsolePiThu", "t": 1, "value": (os.environ["LENH"] + "\0").encode("utf-16-le")})
h.commit(None)
print("da dat RunOnce")
E
sync; umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null
qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m 3072 -display none -vga std \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd \
  -drive if=pflash,format=raw,file=$LAM/vars.fd \
  -netdev user,id=n0 -device e1000,netdev=n0 \
  -drive file=$LAM/o.qcow2,if=none,id=d0 -device ahci,id=ah -device ide-hd,drive=d0,bus=ah.0 \
  -monitor unix:$LAM/mon.sock,server,nowait -pidfile $LAM/q.pid -daemonize || { echo "QEMU loi"; exit 2; }
pid=$(cat $LAM/q.pid); t0=$(date +%s); i=0
while kill -0 "$pid" 2>/dev/null && [ $(( $(date +%s) - t0 )) -lt "$GIAY" ]; do
  sleep 3; i=$((i+1))
  echo "screendump $LAM/a.ppm" | socat - UNIX-CONNECT:$LAM/mon.sock >/dev/null 2>&1
  python3 -c "from PIL import Image; Image.open('$LAM/a.ppm').save('$LAM/anh-$(printf %03d $i)-$(( $(date +%s) - t0 ))s.png')" 2>/dev/null
done
echo "system_powerdown" | socat - UNIX-CONNECT:$LAM/mon.sock >/dev/null 2>&1; sleep 40
kill "$pid" 2>/dev/null; sleep 3
qemu-nbd -r -c /dev/nbd0 $LAM/o.qcow2; sleep 2; mount -o ro /dev/nbd0p3 /mnt/vang 2>/dev/null
cp /mnt/vang/ConsolePi/tien-trinh.log /mnt/vang/ConsolePi/bao-cao-day-du.json /mnt/vang/ConsolePi/ket-qua-tien-trinh.json /mnt/vang/ConsolePi/BAO-CAO-TONG-KET.txt $LAM/ 2>/dev/null
ls /mnt/vang/ConsolePi
umount /mnt/vang; qemu-nbd -d /dev/nbd0 >/dev/null
[ "${GIU:-0}" = 1 ] || rm -f $LAM/o.qcow2; rm -f $LAM/a.ppm
echo "XONG: $(ls $LAM/anh-*.png | wc -l) anh trong $LAM"
