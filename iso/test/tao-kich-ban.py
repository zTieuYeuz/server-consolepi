#!/usr/bin/env python3
"""CHI DE TEST: tao bo kich ban test QUA CHINH trinh tu tren web (giong nguoi
dung bam), chay NGAY TREN may Console System (cong kiosk 127.0.0.1:8880).

    python3 tao-kich-ban.py [ten ...]     (khong ten = tao het)

Mat khau trong day la mat khau cua MAY WINDOWS AO dung de test, khong phai
tai khoan that nao. Moi kich ban phu 1 nhom tinh nang de "cai xong" la
kiem duoc tung thu (bao cao tren may + tien trinh gui ve Console System).
"""
import os
import re
import sys

import requests

GOC = os.environ.get("GOC", "http://127.0.0.1:8880")
H = {"X-ConsolePi-Local": "1"}
MK = "Test@1234"

KICH_BAN = {
    # Toi thieu: moi thu mac dinh - chia o tu dong.
    "T1 Co ban": {
        2: {"os_id": "windows_10_pro"},
        3: {"ten_may": "T1-COBAN", "username": "nhanvien", "password": MK,
            "mui_gio": "Asia/Ho_Chi_Minh"},
        4: {"o_dia_che_do": "tu_dong", "o_dia_so": "0"},
        5: {}, 6: {},
    },
    # Day du: chia tay 6 phan vung (BIOS -> MBR phai dung extended/logical),
    # Administrator, tu dang nhap, tieng Viet, phan mem cap may + cap nguoi
    # dung, ung dung thu muc, script, lenh them, nhieu tuy chon, go app.
    "T2 Day du": {
        2: {"os_id": "windows_10_pro"},
        3: {"ten_may": "T2-DAYDU", "username": "ketoan", "password": MK,
            "mui_gio": "Asia/Ho_Chi_Minh", "ngon_ngu": "vi-VN",
            "ban_phim": "0409:00000409", "tu_dang_nhap": "1",
            "bat_admin": "1", "mk_admin": MK},
        4: {"o_dia_che_do": "chia_tay", "o_dia_so": "0",
            "pv_nhan": ["EFI", "MSR", "Windows", "Data", "Data2", "Data3"],
            "pv_cd": ["260", "16", "40000", "5000", "5000", "con_lai"],
            "pv_fs": ["fat32", "msr", "ntfs", "ntfs", "ntfs", "ntfs"],
            "pv_gan": ["EFI", "-", "C:", "D:", "E:", "F:"]},
        5: {"app": ["winrar-x64-580.exe", "VLCmedia.exe"],
            "dich_winrar-x64-580.exe": "may", "dich_VLCmedia.exe": "nguoi_dung",
            "ungdung": ["kiemtra-nhieu-file"], "dich_ud_kiemtra-nhieu-file": "may"},
        6: {"script": ["kiem-tra.ps1", "kiem-tra.cmd"],
            "lenh_them": "echo lenh-them-da-chay > C:\\ConsolePi\\lenh-them.txt",
            "tuy_chon": ["rdp", "ping", "khong_ngu", "hien_duoi_file",
                         "tat_fast_startup", "bat_numlock", "giao_dien_toi"],
            "go_app": ["Microsoft.BingWeather", "Microsoft.MicrosoftSolitaireCollection"]},
    },
    # Windows 11 (may Secure Boot) + cai 1 phan mem.
    "T3 Win11": {
        2: {"os_id": "windows_11_pro"},
        3: {"ten_may": "T3-WIN11", "username": "giamdoc", "password": MK,
            "mui_gio": "Asia/Ho_Chi_Minh"},
        4: {"o_dia_che_do": "tu_dong", "o_dia_so": "0"},
        5: {"app": ["winrar-x64-580.exe"], "dich_winrar-x64-580.exe": "may"},
        6: {"tuy_chon": ["menu_chuot_cu", "taskbar_trai", "tat_widgets"]},
    },
}


def tao(s, ten, buoc):
    r = s.get(f"{GOC}/deployos/wizard/bat-dau", headers=H, allow_redirects=False)
    m = re.search(r"/deployos/wizard/([^/]+)/", r.headers.get("Location", ""))
    if not m:
        return False, f"khong bat dau duoc trinh tu ({r.status_code})"
    ma = m.group(1)
    for b in sorted(buoc):
        r = s.post(f"{GOC}/deployos/wizard/{ma}/{b}", headers=H,
                   data=dict(buoc[b], huong="tiep"), allow_redirects=False)
        if r.status_code != 302:
            loi = re.findall(r'class="msg err"[^>]*>(.*?)</div>', r.text, re.S)
            return False, f"buoc {b}: {r.status_code} {loi[:1]}"
    r = s.post(f"{GOC}/deployos/kichban/luu/{ma}", headers=H, data={"ten": ten})
    ok = r.status_code == 200 and ("Đã lưu" in r.text or "Da luu" in r.text)
    return ok, "" if ok else re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", r.text))[:300]


if __name__ == "__main__":
    s = requests.Session()
    chon = sys.argv[1:] or list(KICH_BAN)
    loi = 0
    for ten in chon:
        ok, msg = tao(s, ten, KICH_BAN[ten])
        print(("DAT " if ok else "LOI ") + ten, msg)
        loi += not ok
    sys.exit(1 if loi else 0)
