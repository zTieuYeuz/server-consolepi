#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Them dong ban quyen zTieuYeuz vao dau MOI file ma nguon / cau hinh cua repo
(yeu cau 27/09/2026: "ten zTieuYeuz trong moi file"). Chay lai bao nhieu lan
cung duoc - file da co dong ban quyen thi bo qua.

    python3 tools/them-ban-quyen.py [thu-muc-repo]

Giu nguyen dong shebang (#!...), khai bao <?xml ...?> va dong "# -*- coding".
Bo qua: file nhi phan, JSON (khong co cu phap chu thich), VERSION (ma nguon
doc thang noi dung), SHA256SUMS, file du lieu mau, grc-cisco.conf (dinh dang
rieng cua grcat).
"""
import os
import subprocess
import sys

DONG = "Console System - (c) 2026 zTieuYeuz. All rights reserved."
KIEU = {
    ".py": "# {}", ".sh": "# {}", ".service": "# {}", ".timer": "# {}", ".conf": "# {}",
    ".rules": "# {}", ".cfg": "# {}", ".in": "# {}", ".txt": "# {}", ".chroot": "# {}",
    ".ps1": "# {}", ".cmd": "REM {}", ".js": "/* {} */", ".css": "/* {} */", ".qss": "/* {} */",
    ".qml": "// {}", ".svg": "<!-- {} -->", ".html": "<!-- {} -->",
}
TEN_RIENG = {"console-bashrc": "# {}", "console-system-lan-dau": "# {}",
             "console-system-kiosk-ve": "# {}", "console-system-grub-install": "# {}",
             "phien-mo.sh": "# {}"}
BO_QUA = ("VERSION", "SHA256SUMS", "grc-cisco.conf")
BO_QUA_THU_MUC = ("ungdung-mau/", "src/pxe-boot/", "iso/test/tep-kich-ban/")


def them(p):
    ten = os.path.basename(p)
    if ten in BO_QUA or p.startswith(BO_QUA_THU_MUC):
        return False
    mau = TEN_RIENG.get(ten) or KIEU.get(os.path.splitext(ten)[1])
    if not mau:
        return False
    try:
        s = open(p, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return False
    if "zTieuYeuz" in s.split("\n", 6)[:6].__str__():
        return False
    dong = mau.format(DONG)
    L = s.split("\n")
    i = 0
    while i < len(L) and i < 2 and (L[i].startswith("#!") or L[i].startswith("<?xml")
                                    or "coding" in L[i] and L[i].startswith("#")):
        i += 1
    L.insert(i, dong)
    open(p, "w", encoding="utf-8").write("\n".join(L))
    return True


def main():
    goc = sys.argv[1] if len(sys.argv) > 1 else "."
    os.chdir(goc)
    ds = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split()
    n = sum(1 for p in ds if them(p))
    print(f"Da them dong ban quyen vao {n} file.")


if __name__ == "__main__":
    main()
