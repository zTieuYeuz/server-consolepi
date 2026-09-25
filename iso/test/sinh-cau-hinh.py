"""CHI DE TEST: sinh file cau hinh dnsmasq + menu.ipxe cho pxe-lab.sh bang
CHINH code cua ui/pxe.py va ui/pxemenu.py (khong viet tay - test dung thu
se chay that). Du lieu tam, khong dung toi /var/lib/console-pi.
    CONSOLE_PI_DATA=$(mktemp -d) python3 sinh-cau-hinh.py <repo/src> <thu_muc_ra>"""
import json, os, sys
sys.path.insert(0, sys.argv[1]); RA = sys.argv[2]
from ui import pxe, deployos as d, pxemenu as m
os.makedirs(d.KICHBAN_DIR, exist_ok=True); os.makedirs(d.BOOT_DIR, exist_ok=True)
base = dict(os_ho="windows", os_id="win10", ten_may="A", username="admin", password="x")
for f, t in [("A.json", "Xuong san xuat"), ("B.json", "Ke toan")]:
    json.dump(dict(base, ten_kichban=t), open(os.path.join(d.KICHBAN_DIR, f), "w"))
    open(os.path.join(d.BOOT_DIR, m.ten_anh(f)), "w").write("x")
m.luu_cauhinh(cho_giay=15)
pxe._mang_that = lambda c=None: ("192.168.110.0", 24)
pxe.cong = lambda: "eth0"
for kieu, ip in [("mang_co_dhcp", "192.168.110.14"), ("mang_khong_dhcp", "192.168.98.1"),
                 ("truc_tiep", "192.168.98.1")]:
    pxe.DNSMASQ_CONF = os.path.join(RA, kieu + ".conf")
    pxe._dia_chi_pi_that = lambda k, ip=ip: ip
    print(kieu, pxe._ghi_dnsmasq_conf(kieu))
    open(os.path.join(RA, kieu + ".ipxe"), "w").write(m.sinh_script(f"http://{ip}/deployos/pxeboot"))
