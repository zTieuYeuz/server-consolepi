#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console System - chay 1 PHIEN KET NOI ben trong tmux (goi tu phien-mo.sh).

Doc dinh nghia phien tu <du lieu>/phien.json (do trang "Phien ket noi" ghi,
xem ui/phien.py) roi chay dung chuong trinh bang DANH SACH DOI SO - khong qua
shell, nen host/user la gi di nua cung khong chen lenh duoc.

Ket noi rot / thiet bi khoi dong lai -> KHONG dong phien: hien thong bao va
cho bam Enter de ket noi lai (giong nut "R" cua MobaXterm), q de dong.

Telnet: Debian khong cai san lenh telnet, va quy tac du an la khong them goi
he thong khi tu lam duoc -> tu viet 1 trinh telnet nho (du cho switch/router:
tra loi thuong luong IAC, dat che do ky tu tung phim).
"""
import json
import os
import re
import select
import socket
import subprocess
import sys
import termios
import time
import tty

DU_LIEU = os.environ.get("CONSOLE_PI_DATA", "/var/lib/console-pi")
FILE_PHIEN = os.path.join(DU_LIEU, "phien.json")
MAU = {"xanh": "\033[1;32m", "vang": "\033[1;33m", "do": "\033[1;31m", "xam": "\033[0;37m",
       "het": "\033[0m"}


def doc_phien(ma):
    if ma.startswith("serial-"):
        cong = ma[len("serial-"):]
        d = {"ma": ma, "loai": "serial", "cong": cong, "baud": 9600, "ten": cong}
        try:
            for p in json.load(open(FILE_PHIEN, encoding="utf-8")).get("phien", []):
                if p.get("loai") == "serial" and p.get("cong") == cong:
                    d["baud"] = int(p.get("baud") or 9600)
        except (OSError, ValueError):
            pass
        return d
    try:
        for p in json.load(open(FILE_PHIEN, encoding="utf-8")).get("phien", []):
            if p.get("ma") == ma:
                return p
    except (OSError, ValueError):
        pass
    return None


def in_ra(s, mau="xam"):
    sys.stdout.write(f"{MAU[mau]}{s}{MAU['het']}\r\n")
    sys.stdout.flush()


# ------------------------------------------------------------ telnet
IAC, DONT, DO, WONT, WILL, SB, SE = 255, 254, 253, 252, 251, 250, 240
ECHO, SGA, NAWS, TTYPE = 1, 3, 31, 24


def telnet(host, cong):
    """Trinh telnet toi gian: dong y ECHO/SGA cua may kia, tu choi cac tuy chon khac."""
    s = socket.create_connection((host, cong), timeout=10)
    s.settimeout(None)
    fd = sys.stdin.fileno()
    cu = termios.tcgetattr(fd)
    tty.setraw(fd)
    try:
        dem = b""
        while True:
            r, _, _ = select.select([s, fd], [], [])
            if s in r:
                du = s.recv(4096)
                if not du:
                    break
                dem += du
                ra = bytearray()
                i = 0
                while i < len(dem):
                    b = dem[i]
                    if b != IAC:
                        ra.append(b); i += 1; continue
                    if i + 1 >= len(dem):
                        break
                    lenh = dem[i + 1]
                    if lenh == IAC:
                        ra.append(IAC); i += 2; continue
                    if lenh in (DO, DONT, WILL, WONT):
                        if i + 2 >= len(dem):
                            break
                        opt = dem[i + 2]
                        if lenh == WILL:
                            s.sendall(bytes([IAC, DO if opt in (ECHO, SGA) else DONT, opt]))
                        elif lenh == DO:
                            s.sendall(bytes([IAC, WILL if opt == SGA else WONT, opt]))
                        i += 3; continue
                    if lenh == SB:
                        j = dem.find(bytes([IAC, SE]), i)
                        if j < 0:
                            break
                        i = j + 2; continue
                    i += 2
                dem = dem[i:]
                os.write(sys.stdout.fileno(), bytes(ra))
            if fd in r:
                du = os.read(fd, 1024)
                if not du:
                    break
                if b"\x1d" in du:          # Ctrl+] = thoat telnet (nhu telnet chuan)
                    break
                s.sendall(du.replace(bytes([IAC]), bytes([IAC, IAC])))
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, cu)
        s.close()


# ------------------------------------------------------------ chay
def lenh_cua(p):
    loai = p.get("loai")
    if loai == "ssh":
        host, user = p.get("host", ""), p.get("user", "")
        cong = str(int(p.get("port") or 22))
        dich = f"{user}@{host}" if user else host
        return ["ssh", "-o", "StrictHostKeyChecking=accept-new", "-o", "ServerAliveInterval=30",
                "-p", cong, "--", dich]
    if loai == "serial":
        return ["/usr/bin/microcom", "-s", str(int(p.get("baud") or 9600)), "-p", f"/dev/{p['cong']}"]
    return None


def mot_lan(p):
    loai = p.get("loai")
    ten = p.get("ten") or p.get("host") or p.get("cong")
    if loai == "telnet":
        cong = int(p.get("port") or 23)
        in_ra(f"== Telnet {p['host']}:{cong}  ({ten}) ==", "xanh")
        in_ra("Thoát telnet: Ctrl+]", "xam")
        try:
            telnet(p["host"], cong)
        except OSError as e:
            in_ra(f"Không kết nối được: {e}", "do")
        return
    argv = lenh_cua(p)
    if loai == "ssh":
        in_ra(f"== SSH {argv[-1]} cổng {argv[argv.index('-p') + 1]}  ({ten}) ==", "xanh")
    else:
        in_ra(f"== Cổng console /dev/{p['cong']} · {p.get('baud', 9600)} baud  ({ten}) ==", "xanh")
        in_ra("Thoát microcom: Ctrl+X", "xam")
    subprocess.call(argv)


def main():
    ma = sys.argv[1] if len(sys.argv) > 1 else ""
    if not re.fullmatch(r"[a-z0-9][a-zA-Z0-9-]{0,47}", ma):
        in_ra("Mã phiên không hợp lệ.", "do"); time.sleep(5); return
    while True:
        p = doc_phien(ma)
        if not p:
            in_ra("Phiên này không còn (đã bị xoá?).", "do"); time.sleep(8); return
        mot_lan(p)
        in_ra("")
        in_ra("Phiên đã kết thúc.  Enter = kết nối lại   ·   q = đóng phiên", "vang")
        try:
            chon = sys.stdin.readline().strip().lower()
        except KeyboardInterrupt:
            return
        if chon == "q":
            return


if __name__ == "__main__":
    main()
