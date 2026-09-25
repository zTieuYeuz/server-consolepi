"""CHI DE TEST: sinh file cau hinh dnsmasq + menu.ipxe cho pxe-lab.sh bang
CHINH code cua ui/pxe.py va ui/pxemenu.py (khong viet tay - test dung thu
se chay that). Du lieu tam, khong dung toi /var/lib/console-pi.
    CONSOLE_PI_DATA=$(mktemp -d) python3 sinh-cau-hinh.py <repo/src> <thu_muc_ra>
Ra them <thu_muc_ra>/boot/ = BOOT_DIR (file boot kem san + _pxe/<kich ban>/)
de phuc vu qua HTTP trong lab."""
import json, os, shutil, sys
sys.path.insert(0, sys.argv[1]); RA = sys.argv[2]
from ui import pxe, deployos as d, pxemenu as m, unattend as u
os.makedirs(d.KICHBAN_DIR, exist_ok=True); os.makedirs(d.BOOT_DIR, exist_ok=True)
w = d.duong_boot_wim("win10"); os.makedirs(os.path.dirname(w), exist_ok=True)
open(w, "w").write("x"); open(d.duong_install_wim("win10"), "w").write("x")
base = dict(os_ho="windows", os_id="win10", ten_may="A", username="admin", password="x")
for f, t in [("A.json", "Xuong san xuat"), ("B.json", "Ke toan")]:
    json.dump(dict(base, ten_kichban=t), open(os.path.join(d.KICHBAN_DIR, f), "w"))
u._doc_mat_khau_samba = lambda: "khong-that"
m.luu_cauhinh(cho_giay=15)
pxe._mang_that = lambda c=None: ("192.168.110.0", 24)
pxe.cong = lambda: "eth0"
print("chep file boot:", pxe._chep_file_boot())
for kieu, ip in [("mang_co_dhcp", "192.168.110.14"), ("mang_khong_dhcp", "192.168.98.1"),
                 ("truc_tiep", "192.168.98.1")]:
    pxe.DNSMASQ_CONF = os.path.join(RA, kieu + ".conf")
    pxe._dia_chi_pi_that = lambda k, ip=ip: ip
    print(kieu, pxe._ghi_dnsmasq_conf(kieu), m.chuan_bi_menu(ip, kieu))
    open(os.path.join(RA, kieu + ".ipxe"), "w").write(m.sinh_script(f"http://{ip}/deployos/pxeboot"))
shutil.copytree(d.BOOT_DIR, os.path.join(RA, "boot"), dirs_exist_ok=True)
