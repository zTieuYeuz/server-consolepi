#!/usr/bin/env python3
# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Terminal SSH RIENG moi nguoi - KHONG co shell (2.0.7, LOI-013 goc): chay lam LENH CUA PHIEN tmux (xem phien-mo.sh), thay vi de ttyd mo `bash` root roi go lenh ssh vao.

Vong lap: cho yeu cau ket noi (do Console ghi vao thu muc yeu cau sau khi nguoi dung bam Ket noi tren trang /ssh) -> chay `ssh` bang DANH SACH DOI SO
(khong qua shell, tat ky tu thoat `~`, tat LocalCommand/ProxyCommand tu cau hinh) -> ssh thoat thi quay ve cho, KHONG BAO GIO roi vao shell cua Pi.
Phim go luc cho bi bo, khong an vao ssh ke tiep (tcflush). Chay duoi user khong dac quyen `console-ssh` neu co (phien-mo.sh lo).
"""
import json
import os
import re
import signal
import subprocess
import sys
import termios
import time

DIR_YC = os.environ.get("CS_SSH_YC") or "/var/lib/console-ssh/yeu-cau"
HOME_SSH = os.environ.get("CS_SSH_HOME") or "/var/lib/console-ssh"
RE_HOST = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:\-]{0,254}")
RE_USER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._\-\\]{0,63}")


def lenh_ssh(host, user, cong, known_hosts):
    """argv cua ssh (kiem tra lai dau vao). Tra None neu khong hop le."""
    if not (RE_HOST.fullmatch(host or "") and RE_USER.fullmatch(user or "")):
        return None
    try:
        cong = int(cong)
    except (TypeError, ValueError):
        return None
    if not 1 <= cong <= 65535:
        return None
    return ["ssh", "-F", "/dev/null", "-e", "none", "-o", "PermitLocalCommand=no", "-o", "StrictHostKeyChecking=accept-new",
            "-o", "UserKnownHostsFile=" + known_hosts, "-o", "ServerAliveInterval=30", "-p", str(cong), "--", "%s@%s" % (user, host)]


def doc_yeu_cau(ten):
    f = os.path.join(DIR_YC, ten + ".json")
    try:
        with open(f, encoding="utf-8") as h:
            d = json.load(h)
    except (OSError, ValueError):
        return None
    try:
        os.remove(f)
    except OSError:
        pass
    return d if isinstance(d, dict) else None


def tat_echo(fd, bat):
    try:
        a = termios.tcgetattr(fd)
        if bat:
            a[3] |= termios.ECHO | termios.ICANON
        else:
            a[3] &= ~(termios.ECHO | termios.ICANON)
        termios.tcsetattr(fd, termios.TCSANOW, a)
    except termios.error:
        pass


def main(argv):
    ten = argv[1] if len(argv) > 1 else ""
    if not re.fullmatch(r"ssh-[a-z0-9]{1,24}", ten):
        print("Ten phien khong hop le.")
        time.sleep(5)
        return 1
    if os.geteuid() == 0 and os.environ.get("CS_SSH_CHO_PHEP_ROOT") != "1":
        # FAIL CLOSED (NV8-12): launcher khong bao gio chay bang root (phien-mo.sh ha quyen xuong console-ssh; neu khong ha duoc thi khong mo)
        print("Tu choi: terminal SSH khong duoc chay bang root.")
        time.sleep(8)
        return 1
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    known_hosts = os.path.join(HOME_SSH, "known_hosts")
    fd = sys.stdin.fileno()
    try:
        os.remove(os.path.join(DIR_YC, ten + ".dang-ssh"))      # dau vet cu neu launcher tung bi giet
    except OSError:
        pass
    while True:
        print("\r\nChưa kết nối. Nhập địa chỉ, tài khoản rồi bấm Kết nối ở phía trên trang.\r", flush=True)
        yc = None
        tat_echo(fd, False)
        while yc is None:
            time.sleep(0.3)
            yc = doc_yeu_cau(ten)
        try:
            termios.tcflush(fd, termios.TCIFLUSH)
        except termios.error:
            pass
        tat_echo(fd, True)
        lenh = lenh_ssh(str(yc.get("host", "")), str(yc.get("user", "")), yc.get("port", 22), known_hosts)
        if lenh is None:
            print("Yêu cầu kết nối không hợp lệ.\r", flush=True)
            continue
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        danh_dau = os.path.join(DIR_YC, ten + ".dang-ssh")       # Console doc de biet ssh dang chay (LOI-014: pane_current_command luon la python3)
        try:
            open(danh_dau, "w").close()
        except OSError:
            danh_dau = None
        try:
            subprocess.call(lenh)
        finally:
            if danh_dau:
                try:
                    os.remove(danh_dau)
                except OSError:
                    pass
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        print("\r\n== Kết nối SSH đã kết thúc ==\r", flush=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
