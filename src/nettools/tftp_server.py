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
import os
import re
import subprocess
import time

from flask import request, render_template_string

from . import nettools_bp

TFTP_ROOT = "/opt/console-pi/tftp"
STATE_FLAG = "/run/console-pi-tftp.flag"
IFACE = "eth0"
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
        return False, ("Chua cai tftpd-hpa. Chay: sudo apt install -y tftpd-hpa "
                       "(chi can cai 1 lan, khong tu dong bat)")
    if dang_bat():
        return True, "TFTP dang bat san."

    os.makedirs(TFTP_ROOT, exist_ok=True)
    # world-writable co chu dich: tftpd-hpa chay duoi user rieng "tftp",
    # can ghi duoc vao thu muc nay de nhan file tu switch gui len.
    os.chmod(TFTP_ROOT, 0o777)

    ok, out = _sh(["systemctl", "start", DON_VI_SYSTEMD])
    if not ok:
        return False, f"Khong bat duoc dich vu TFTP: {out[:200]}"

    open(STATE_FLAG, "w").close()
    return True, f"Da bat TFTP tren {IFACE}. Thu muc nhan file: {TFTP_ROOT}"


def tat_tftp():
    if not dang_bat():
        return True, "TFTP von da tat."
    _sh(["systemctl", "stop", DON_VI_SYSTEMD])
    try:
        os.remove(STATE_FLAG)
    except OSError:
        pass
    return True, "Da tat TFTP."


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


def xoa_file(ten):
    """Xoa 1 file da nhan. Kiem tra ky ten file - day la file THIET BI KHAC
    tu ghi len, khong phai nguoi dung tu dat ten, nen phai canh giac hon ca
    upload thong thuong."""
    ten = os.path.basename((ten or "").strip())
    if not ten or ten in (".", ".."):
        return False, "Ten file khong hop le."
    duong = os.path.join(TFTP_ROOT, ten)
    # Kiem tra lai duong dan that su sau khi giai (chan moi kieu vuot thu muc)
    if os.path.realpath(duong) != os.path.join(os.path.realpath(TFTP_ROOT), ten):
        return False, "Ten file khong hop le."
    if not os.path.isfile(duong):
        return False, "Khong tim thay file."
    try:
        os.remove(duong)
    except OSError as e:
        return False, f"Khong xoa duoc: {e}"
    return True, f"Da xoa {ten}."


def ip_theo_giao_dien():
    """IP hien tai cua Pi tren eth0/wlan0 - de hien cho nguoi dung go vao lenh switch."""
    from ui.layout import _ipv4_of
    ra = []
    for ten in ("eth0", "wlan0"):
        ip = _ipv4_of(ten)
        if ip:
            ra.append({"iface": ten, "ip": ip})
    return ra


TFTP_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>May chu TFTP - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; } h3 { color: #4CAF50; margin-top: 22px; }
        a { color: #4CAF50; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 15px; }
        button.red { background: #c0392b; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { padding: 9px 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        .card { background:#262626; border:1px solid #3a3a3a; border-left:4px solid #4CAF50;
                border-radius:6px; padding:14px 16px; margin-top:16px; }
        .warn { background: #4a3d1a; border-left: 4px solid #ffb74d; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; }
        pre { background:#111; padding:10px 12px; border-radius:6px; overflow-x:auto; font-size:13px; }
        code.small { font-size:12px; color:#aaa; }
    </style>
</head>
<body>
    <h1>📤 May chu TFTP</h1>
    <p><a href="/nettools">← Network Tools</a></p>

    {% if msg %}<div class="{{ 'warn' if not ok else 'card' }}">{{ msg }}</div>{% endif %}

    <div class="warn">
        ⚠️ TFTP KHONG co xac thuc - bat ky thiet bi nao cam vao cong <strong>eth0</strong> deu
        doc/ghi duoc file. Chi bat khi dang thuc su lam viec, tat ngay sau khi xong.
    </div>

    {% if not da_cai %}
    <div class="err">Chua cai <code>tftpd-hpa</code> tren Console Pi. Chay lenh sau roi tai lai trang:
        <pre>sudo apt install -y tftpd-hpa
sudo systemctl disable --now tftpd-hpa   # tat dich vu mac dinh cua goi, Console Pi tu quan ly rieng</pre>
    </div>
    {% else %}
    <div class="card">
        {% if dang_bat %}
        <p>🟢 Dang bat tren <strong>{{ iface }}</strong>. Thu muc nhan file: <code>{{ tftp_root }}</code></p>
        <form method="POST" action="/nettools/tftp/tat">
            <button type="submit" class="red" data-busy="Dang tat...">⏏ Tat TFTP</button>
        </form>
        {% else %}
        <p>⚪ Dang tat.</p>
        <form method="POST" action="/nettools/tftp/bat">
            <button type="submit" data-busy="Dang bat...">▶ Bat TFTP tren {{ iface }}</button>
        </form>
        {% endif %}
    </div>

    <h3>Cach dung tren switch Cisco</h3>
    <div class="card">
        <p class="hint">IP cua Pi de dien vao lenh:</p>
        {% for ip in danh_sach_ip %}<code>{{ ip.iface }}: {{ ip.ip }}</code><br>{% endfor %}
        {% if not danh_sach_ip %}<p class="hint">Chua co IP tren interface nao.</p>{% endif %}
        <p style="margin-top:11px;">Sao luu cau hinh len Pi:</p>
        <pre>copy running-config tftp://{{ danh_sach_ip[0].ip if danh_sach_ip else '<IP-cua-Pi>' }}/backup.cfg</pre>
        <p>Nap firmware/cau hinh tu Pi xuong switch (dat file vao thu muc <code>{{ tftp_root }}</code> truoc):</p>
        <pre>copy tftp://{{ danh_sach_ip[0].ip if danh_sach_ip else '<IP-cua-Pi>' }}/firmware.bin flash:</pre>
    </div>

    <h3>File da nhan ({{ files|length }})</h3>
    <table>
        <tr><th>Ten file</th><th style="width:120px;">Kich thuoc</th><th style="width:150px;">Thoi gian</th><th style="width:100px;"></th></tr>
        {% for f in files %}
        <tr>
            <td>{{ f.ten }}</td>
            <td>{{ (f.kich_thuoc / 1024) | round(1) }} KB</td>
            <td class="hint">{{ f.thoi_gian }}</td>
            <td>
                <form method="POST" action="/nettools/tftp/xoa" style="display:inline;"
                      onsubmit="return confirm('Xoa {{ f.ten }}?');">
                    <input type="hidden" name="ten" value="{{ f.ten }}">
                    <button type="submit" class="red" style="padding:4px 10px;">Xoa</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
    {% if not files %}<p class="hint">Chua co file nao.</p>{% endif %}
    {% endif %}
</body>
</html>
"""


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


if __name__ == "__main__":
    print("Da cai tftpd-hpa:", da_cai_dat())
    print("Dang bat:", dang_bat())
    print("IP theo giao dien:", ip_theo_giao_dien())
    print("File hien co:", danh_sach_file())
