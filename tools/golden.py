#!/usr/bin/env python3
"""Golden output: sinh file tu kich ban CO DINH, ghi/so sanh tung byte.
    golden.py ghi    -> ghi mau vao tests/golden/
    golden.py kiem   -> so sanh voi mau (thoat 1 neu khac)
Chi dung du lieu gia, khong doc/ghi du lieu that cua may."""
import hashlib
import os
import re
import sys

GOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(GOC, "src"))
from ui import datten, pxemenu, uem_agent_goi, unattend as u  # noqa: E402

PI = "192.168.98.1"
THU_MUC = os.path.join(GOC, "tests", "golden")


def kich_ban():
    tat_ca = [t[0] for t in u.TUY_CHON_WINDOWS]
    co_ban = {"os_id": "windows_10_pro", "ten_may": "T1-COBAN", "username": "nhanvien",
              "password": "Mau@1234", "mui_gio": "Asia/Ho_Chi_Minh",
              "o_dia_che_do": "tu_dong", "o_dia_so": "0"}
    day_du = dict(co_ban, ten_may="T2-DAYDU", username="ketoan", ngon_ngu="vi-VN",
                  ban_phim="0409:00000409", tu_dang_nhap="1", bat_admin="1", mk_admin="Mau@1234",
                  o_dia_che_do="chia_tay", tuy_chon=tat_ca,
                  go_app=[a[0] for a in u.APP_RAC[:3]],
                  tu_dong_c_gb="100", tu_dong_d="1",
                  phan_vung=[{"fs": "fat32", "cd": "260"}, {"fs": "msr", "cd": "16"},
                             {"fs": "ntfs", "cd": "100", "nhan": "Windows"},
                             {"fs": "ntfs", "cd": "con_lai", "nhan": "DuLieu"}],
                  lenh_them="echo xin chao\necho dong hai")
    domain = dict(co_ban, ten_may="T3-DOMAIN", domain="congty.local",
                  domain_ou="OU=May,DC=congty,DC=local")
    dong = dict(co_ban, ten_may_che_do=[k for k in datten.CHE_DO if k != "co_dinh"][0])
    return {"co-ban": co_ban, "day-du": day_du, "domain": domain, "ten-dong": dong}


def sinh():
    ra = {}
    for ten, d in kich_ban().items():
        for f, nd in u.sinh_file_nhung(d, PI).items():
            ra[f"unattend/{ten}/{f}"] = nd
        ra[f"unattend/{ten}/autounattend-wizard.xml"] = u.sinh_autounattend_xml(d, PI)
    ra["pxe/menu.ipxe"] = pxemenu.sinh_script("http://%s/deployos/pxeboot" % PI)
    ra["agent/cai-agent.ps1"] = uem_agent_goi._script("http://%s:8880/uem/agent" % PI, "123456", "MA-MAU", "May Mau")
    ra["agent/cai-agent-pk.ps1"] = uem_agent_goi._script("http://%s:8880/uem/agent" % PI, "123456", "MA-MAU", "May Mau", "p1:1000:%s:%s" % ("ab" * 16, "cd" * 32))
    # chuan hoa gio tao (dau ra chua thoi diem sinh)
    return {k: re.sub(r"\(tạo \d\d/\d\d/\d{4} \d\d:\d\d\)", "(tạo <GIO>)", v) for k, v in ra.items()}


def main():
    cheDo = sys.argv[1] if len(sys.argv) > 1 else "kiem"
    mau = sinh()
    if cheDo == "ghi":
        for ten, nd in mau.items():
            p = os.path.join(THU_MUC, ten)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(nd)
        print("da ghi", len(mau), "file mau")
        return 0
    khac = 0
    for ten, nd in mau.items():
        p = os.path.join(THU_MUC, ten)
        cu = open(p, encoding="utf-8", newline="").read() if os.path.exists(p) else None
        if cu != nd:
            khac += 1
            print("KHAC", ten, hashlib.sha1(nd.encode()).hexdigest()[:8])
    print("tong %d file, khac %d" % (len(mau), khac))
    return 1 if khac else 0


if __name__ == "__main__":
    sys.exit(main())
