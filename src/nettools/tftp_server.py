# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi Network Tools - May chu TFTP (sao luu/phuc hoi config, firmware)

Dung khi lam viec truc tiep voi switch/router: lenh Cisco kinh dien
`copy running-config tftp://<ip-cua-pi>/backup.cfg` (sao luu cau hinh len
Pi) va `copy tftp://<ip-cua-pi>/firmware.bin flash:` (nap firmware tu Pi
xuong switch).

QUYET DINH QUAN TRONG DA SUA GIUA CHUNG (khong phai gia dinh ban dau):
Ban dau du dinh dung TFTP tich hop san trong `dnsmasq` (da co san, khong
can cai goi moi) - nhung DOC KY man dnsmasq moi phat hien no CHI HO TRO
DOC (download tu Pi ve thiet bi khac), khong ho tro GHI (thiet bi khac day
file LEN Pi). Trich nguyen van man dnsmasq: "Only reading is allowed".
Dieu do co nghia lenh quan trong nhat - `copy running-config tftp://...`
(switch GHI cau hinh len Pi) - se KHONG BAO GIO chay duoc voi dnsmasq.

Vi vay phai dung `tftpd-hpa` (goi TFTP chuan cua Debian, ho tro ca doc lan
ghi qua co `--create`) - CAN CAI THEM 1 GOI MOI, khac voi du dinh ban dau
la khong can cai gi ca. Day la vi du cu the cho nguyen tac "do dac truoc
khi ket luan" cua du an - neu khong doc ky tai lieu se giao mot tinh nang
"TFTP" nhung thuc ra khong lam duoc viec chinh no duoc tao ra de lam.

AN TOAN: TFTP khong co xac thuc gi ca (ai gui goi UDP/69 dung dinh dang
cung doc/ghi duoc). Vi vay:
  - Mac dinh TAT, chi bat khi nguoi dung chu dong bam nut
  - Chi lang nghe tren eth0 (kich ban dung la cam day thang vao switch)
  - `--create` cho phep TAO file moi nhung KHONG cho doc file ngoai thu muc
    goc (co --secure di kem), va thu muc goc la MOT thu muc RIENG BIET
    (/opt/console-pi/tftp), khong chung voi kho luu ISO/firmware chinh
    (storage.py) - tranh lam ro dia chi hoac de lo file nhay cam khac

DUONG DAN CO DINH: khac voi storage.py/pcap.py (uu tien USB, doi lai duoc
giua chung), TFTP server can 1 duong dan ON DINH tu luc bat den luc tat -
`in.tftpd` doc thu muc goc MOT LAN luc khoi dong, doi USB giua chung se lam
sai lech hoan toan. Vi vay dung co dinh /opt/console-pi/tftp, khong lien
quan gi USB.
"""
from consolesystem.core import taisan as _taisan
import os
import re
import subprocess
import time

from flask import request, render_template_string, send_from_directory, abort

from . import nettools_bp
from ui import duongdan as _DD

TFTP_ROOT = _DD.DIR_TFTP
STATE_FLAG = _DD.FLAG_TFTP
# Chi la nhan hien thi: in.tftpd chay voi --address 0.0.0.0:69 (xem
# systemd/console-pi-tftp.service) nen nghe tren MOI cong. Truoc day ghi
# "eth0" - sai ca tren Pi lan may x86 (cong ten ens3/enp1s0...).
IFACE = "mọi cổng mạng"
DON_VI_SYSTEMD = "console-pi-tftp"


def _sh(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)


def dang_bat():
    return os.path.exists(STATE_FLAG)


def da_cai_dat():
    return os.path.exists("/usr/sbin/in.tftpd")


def bat_tftp():
    if not da_cai_dat():
        return False, ("Chưa cài tftpd-hpa. Chạy: sudo apt install -y tftpd-hpa "
                       "(chi can cai 1 lan, khong tu dong bat)")
    if dang_bat():
        return True, "TFTP đang bật sẵn."

    os.makedirs(TFTP_ROOT, exist_ok=True)
    # world-writable co chu dich: tftpd-hpa chay duoi user rieng "tftp",
    # can ghi duoc vao thu muc nay de nhan file tu switch gui len.
    os.chmod(TFTP_ROOT, 0o777)

    ok, out = _sh(["systemctl", "start", DON_VI_SYSTEMD])
    if not ok:
        return False, f"Không bật được dịch vụ TFTP: {out[:200]}"

    open(STATE_FLAG, "w").close()
    return True, f"Đã bật TFTP trên {IFACE}. Thư mục nhận file: {TFTP_ROOT}"


def tat_tftp():
    if not dang_bat():
        return True, "TFTP vốn đã tắt."
    _sh(["systemctl", "stop", DON_VI_SYSTEMD])
    try:
        os.remove(STATE_FLAG)
    except OSError:
        pass
    return True, "Đã tắt TFTP."


def danh_sach_file():
    if not os.path.isdir(TFTP_ROOT):
        return []
    ra = []
    for ten in sorted(os.listdir(TFTP_ROOT)):
        duong = os.path.join(TFTP_ROOT, ten)
        if not os.path.isfile(duong):
            continue
        try:
            st = os.stat(duong)
            ra.append({"ten": ten, "kich_thuoc": st.st_size,
                      "thoi_gian": time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime))})
        except OSError:
            continue
    return sorted(ra, key=lambda x: x["thoi_gian"], reverse=True)


def duong_dan_an_toan(ten):
    """
    Doi ten file nguoi dung gui len thanh duong dan that, hoac None neu
    khong hop le. Dung CHUNG cho ca xoa lan tai ve - file trong thu muc nay
    do THIET BI KHAC tu ghi len (khong phai nguoi dung tu dat ten), nen phai
    canh giac hon ca upload thong thuong: chan moi kieu vuot thu muc
    (../, duong dan tuyet doi, symlink tro ra ngoai).
    """
    ten = os.path.basename((ten or "").strip())
    if not ten or ten in (".", ".."):
        return None
    duong = os.path.join(TFTP_ROOT, ten)
    # Kiem tra lai duong dan that su sau khi giai symlink
    if os.path.realpath(duong) != os.path.join(os.path.realpath(TFTP_ROOT), ten):
        return None
    if not os.path.isfile(duong):
        return None
    return duong


def xoa_file(ten):
    """Xoa 1 file da nhan."""
    duong = duong_dan_an_toan(ten)
    if not duong:
        return False, "Tên file không hợp lệ hoặc không tìm thấy file."
    try:
        os.remove(duong)
    except OSError as e:
        return False, f"Không xóa được: {e}"
    return True, f"Đã xóa {os.path.basename(duong)}."


def ip_theo_giao_dien():
    """IP hien tai cua may tren tung cong that - de nguoi dung go vao lenh switch.

    Khong viet cung eth0/wlan0: tren may x86 cong ten ens3/enp1s0... nen
    phan huong dan tung khong hien IP nao (bat duoc khi thu ban ISO)."""
    from ui.layout import _ipv4_of
    from ui.phancung import danh_sach_cong
    ra = []
    for ten in [c["ten"] for c in danh_sach_cong()]:
        ip = _ipv4_of(ten)
        if ip:
            ra.append({"iface": ten, "ip": ip})
    return ra


TFTP_TEMPLATE = _taisan.doc("nettools/tftp_server.TFTP_TEMPLATE.html")


def _render(msg="", ok=True):
    return render_template_string(
        TFTP_TEMPLATE, msg=msg, ok=ok, da_cai=da_cai_dat(), dang_bat=dang_bat(),
        iface=IFACE, tftp_root=TFTP_ROOT, danh_sach_ip=ip_theo_giao_dien(),
        files=danh_sach_file(),
    )


@nettools_bp.route("/nettools/tftp")
def tftp_route():
    return _render()


@nettools_bp.route("/nettools/tftp/bat", methods=["POST"])
def tftp_bat_route():
    ok, msg = bat_tftp()
    return _render(msg=msg, ok=ok)


@nettools_bp.route("/nettools/tftp/tat", methods=["POST"])
def tftp_tat_route():
    ok, msg = tat_tftp()
    return _render(msg=msg, ok=ok)


@nettools_bp.route("/nettools/tftp/xoa", methods=["POST"])
def tftp_xoa_route():
    ok, msg = xoa_file(request.form.get("ten", ""))
    return _render(msg=msg, ok=ok)


@nettools_bp.route("/nettools/tftp/tai/<path:ten>")
def tftp_tai_route(ten):
    """
    Tai file switch da day len ve may dang xem web.

    Truoc day file nam tren dia ma khong co duong nao lay ve tu giao dien -
    phai SSH vao Pi moi copy ra duoc, rat bat tien khi dang o hien truong
    voi may tinh bang.

    as_attachment=True: bat trinh duyet TAI XUONG thay vi mo trong tab. File
    o day la cau hinh/firmware cua thiet bi mang (co the la .cfg, .bin, .txt)
    - mo trong tab vua khong huu ich vua co the bi trinh duyet dien giai
    nham thanh HTML.
    """
    duong = duong_dan_an_toan(ten)
    if not duong:
        abort(404)
    return send_from_directory(TFTP_ROOT, os.path.basename(duong),
                               as_attachment=True)


if __name__ == "__main__":
    print("Da cai tftpd-hpa:", da_cai_dat())
    print("Dang bat:", dang_bat())
    print("IP theo giao dien:", ip_theo_giao_dien())
    print("File hien co:", danh_sach_file())
