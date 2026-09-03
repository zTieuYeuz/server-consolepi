"""
Console Pi Network Tools - MTU / Path MTU Discovery

Tim MTU THAT cua duong truyen toi 1 dia chi, bang cach gui ping mang co
DF (Don't Fragment) voi kich thuoc tang dan/giam dan (tim nhi phan). Neu
mot router giua duong khong the chuyen tiep goi qua kho ma khong duoc phep
phan manh, no se tra ve ICMP "Fragmentation needed" kem theo MTU THAT cua
doan mang do - day la thong tin dang tin cay nhat, dung ngay khong can do
them.

VI SAO CAN CONG CU NAY: MTU bi giam (thuong thay 1492 do PPPoE, ~1436-1400
do VPN/GRE/IPsec) gay ra loai loi rat kho chiu - goi nho (ping, duyet web
co ban) van chay binh thuong, nhung truyen file lon/tai video lai cham hoac
treo hoan toan, vi cac goi lon bi phan manh sai hoac bi loai bo am tham boi
mot thiet bi khong gui ICMP loi (nhieu firewall/middlebox lam vay).

DA KIEM CHUNG TREN MAY THAT (quan trong, giai thich 2 dang loi khac nhau):
  - `ping -M do -s <n>` KHONG co `-I <iface>`: neu he thong co san 1 tuyen
    duong dac biet cho dia chi dich (vi du mot router Wifi cap rieng tuyen
    cho 8.8.8.8 qua interface khac - da gap that o cong cu DHCP test truoc
    day), ket qua bi anh huong boi duong di SAI, khong phai loi MTU that
    cua duong dang muon do. PHAI luon co `-I iface` de ep dung cong.
  - Loi "sendmsg: Message too long" (khong co "Frag needed") xay ra NGAY
    LAP TUC (0ms) khi kich thuoc goi vuot qua MTU cau hinh CUA CHINH
    interface Pi - day la loi cuc bo, khong lien quan gi den mang, va PHAI
    duoc loai tru bang cach kep tran tim kiem theo MTU that cua interface
    (doc tu /sys/class/net/<iface>/mtu) truoc khi bat dau do.
  - Loi "Frag needed and DF set (mtu = X)" la ICMP THAT tu mot router giua
    duong - no NOI THANG mtu dung, dung luon khong can do them.
"""
import random
import re
import subprocess

from flask import request, render_template_string

from . import nettools_bp

# Nguong duoi day - bat cu MTU nao duoi day deu coi la hong nang, khong con
# y nghia thuc te (chuan Ethernet toi thieu la 68, nhung thap hon 576 la
# gan nhu chac chan co van de nghiem trong o dau do).
MTU_TOI_THIEU = 68
MTU_TRAN_MAC_DINH = 1500

# MTU tim duoc thap hon 1500 (chuan Ethernet) thi goi y nguyen nhan pho
# bien nhat - giup nguoi dung khong phai tu doan.
GOI_Y_NGUYEN_NHAN = [
    (1492, 1500, "Co the do PPPoE (ISP dial-up qua Ethernet) - PPPoE tru di 8 byte."),
    (1436, 1465, "Co the do VPN/GRE/IPsec - cac giao thuc dong goi nay thuong tru 20-64 byte."),
    (1400, 1436, "Kha nang do VPN/tunnel voi overhead lon hon binh thuong."),
    (0,    1400, "MTU rat thap - kiem tra ca cau hinh MTU tren chinh thiet bi mang gan Pi."),
]


def _chay(cmd, timeout=6):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", "khong-cai-dat"
    except subprocess.TimeoutExpired:
        return -1, "", "qua-thoi-gian-cho"
    except Exception as e:
        return -1, "", str(e)


def _mtu_cua_interface(iface):
    try:
        with open(f"/sys/class/net/{iface}/mtu") as f:
            return int(f.read().strip())
    except Exception:
        return MTU_TRAN_MAC_DINH


def _thu_mot_kich_thuoc(iface, host, payload, timeout):
    """
    Gui 1 ping DF voi kich thuoc payload cho truoc.
    Tra ve mot trong ba: ("ok", None), ("qua_lon", mtu_that_neu_biet),
    ("khong_ro", None) - truong hop thu ba la mat goi thuong, khong ro
    co phai do MTU hay khong.
    """
    rc, out, err = _chay(
        ["ping", "-M", "do", "-s", str(payload), "-c", "1", "-W", str(timeout),
         "-I", iface, host],
        timeout=timeout + 3,
    )
    toan_bo = out + err

    if "Frag needed and DF set" in toan_bo or "Fragmentation needed" in toan_bo:
        m = re.search(r"mtu\s*=\s*(\d+)", toan_bo)
        return "qua_lon", (int(m.group(1)) if m else None)

    if "sendmsg: Message too long" in toan_bo:
        # Loi cuc bo (vuot MTU cua chinh interface) - khong phai ket qua
        # mang, nhung van coi la "qua lon" de nhi phan tiep tuc dung huong.
        return "qua_lon", None

    if ", 1 received" in toan_bo or "1 packets transmitted, 1 received" in toan_bo:
        return "ok", None

    return "khong_ro", None


def tim_mtu(host, iface="eth0", timeout=2):
    """
    Tra ve {"ok", "error", "mtu": int|None, "chi_tiet": [...], "canh_bao": str|None,
            "tu_router": bool}

    Nhi phan tim kich thuoc payload lon nhat con di qua duoc voi co DF, kep
    tran theo MTU that cua interface. Neu mot router bao thang MTU qua ICMP
    Frag-needed thi dung ngay ket qua do, khong can do tiep.
    """
    if not host or not re.fullmatch(r"[A-Za-z0-9.\-:]{1,255}", host):
        return {"ok": False, "error": "Dia chi/hostname khong hop le.", "mtu": None,
                "chi_tiet": [], "canh_bao": None, "tu_router": False}

    mtu_iface = _mtu_cua_interface(iface)
    chi_tiet = []

    # Kiem tra co ket noi duoc toi dich khong (goi nho, khong DF) truoc khi
    # do MTU - neu host khong phan hoi gi ca thi do MTU vo nghia, va phai
    # noi ro nguyen nhan la "khong toi duoc" chu khong phai "MTU rat thap".
    rc, out, err = _chay(["ping", "-c", "2", "-W", str(timeout), "-I", iface, host],
                         timeout=timeout * 2 + 3)
    if "0 received" in (out + err) or rc != 0 and "received" not in out:
        return {"ok": False,
                "error": f"Khong ping toi duoc {host} qua {iface} - kiem tra dia chi hoac "
                        "ket noi truoc khi do MTU.",
                "mtu": None, "chi_tiet": [], "canh_bao": None, "tu_router": False}

    thap = MTU_TOI_THIEU - 28   # payload thap nhat coi nhu luon thanh cong
    cao = min(9000, mtu_iface) - 28
    payload_tot_nhat = thap
    tu_router = False
    mtu_tu_icmp = None

    for _buoc in range(16):    # du cho khoang 9000, thuc te ~14 la du
        if thap > cao:
            break
        giua = (thap + cao) // 2

        # Thu lai toi da 2 lan cho MOT kich thuoc truoc khi ket luan - tranh
        # nham lan mat goi thuong (thoang qua) voi gioi han MTU that.
        ket_qua, mtu_bao = None, None
        for _lan in range(2):
            ket_qua, mtu_bao = _thu_mot_kich_thuoc(iface, host, giua, timeout)
            if ket_qua != "khong_ro":
                break

        chi_tiet.append({"payload": giua, "mtu_tuong_ung": giua + 28, "ket_qua": ket_qua})

        if ket_qua == "ok":
            payload_tot_nhat = giua
            thap = giua + 1
        elif ket_qua == "qua_lon":
            if mtu_bao:
                # Router noi thang MTU dung - tin ngay, dung do them.
                mtu_tu_icmp = mtu_bao
                tu_router = True
                break
            cao = giua - 1
        else:
            # "khong_ro" sau 2 lan thu - khong the ket luan chac chan o muc
            # nay, coi nhu gioi han (an toan hon la bao qua lon).
            cao = giua - 1

    mtu_cuoi = mtu_tu_icmp if mtu_tu_icmp else (payload_tot_nhat + 28)

    canh_bao = None
    if mtu_cuoi < MTU_TRAN_MAC_DINH:
        for duoi, tren, mo_ta in GOI_Y_NGUYEN_NHAN:
            if duoi <= mtu_cuoi < tren:
                canh_bao = (f"MTU {mtu_cuoi} thap hon chuan Ethernet (1500). {mo_ta}")
                break

    return {"ok": True, "error": None, "mtu": mtu_cuoi, "chi_tiet": chi_tiet,
            "canh_bao": canh_bao, "tu_router": tu_router, "mtu_interface": mtu_iface}


MTU_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>MTU Discovery - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; } h3 { color: #4CAF50; margin-top: 22px; }
        a { color: #4CAF50; }
        select, input[type=text] { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { padding: 9px 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        .card { background:#262626; border:1px solid #3a3a3a; border-left:4px solid #4CAF50;
                border-radius:6px; padding:14px 16px; margin-top:16px; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .warn { background: #4a3d1a; border-left: 4px solid #ffb74d; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .hint { color: #999; font-size: 13px; }
        .big { font-size:34px; font-weight:700; color:#8fd99a; }
        details summary { cursor: pointer; color: #999; margin-top: 16px; }
    </style>
</head>
<body>
    <h1>📏 MTU / Path MTU Discovery</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Tim MTU that cua duong truyen bang ping co co "khong phan manh" (DF), kich
    thuoc tang/giam dan. Huu ich khi mang co trieu chung la: duyet web/ping binh thuong nhung
    tai file lon hoac video hay bi treo/cham - dau hieu kinh dien cua MTU bi giam giua duong
    (VPN, PPPoE...).</p>

    <form method="POST" style="margin-top:16px;">
        <label>Dia chi/hostname can do:</label>
        <input type="text" name="host" value="{{ host or '' }}" placeholder="vd 8.8.8.8 hoac google.com" required>
        <label style="margin-left:10px;">Interface:</label>
        <select name="iface">
            <option value="eth0" {{ 'selected' if iface=='eth0' else '' }}>eth0</option>
            <option value="wlan0" {{ 'selected' if iface=='wlan0' else '' }}>wlan0</option>
        </select>
        <button type="submit" style="margin-left:10px;" data-busy="Dang do MTU...">Do MTU</button>
    </form>

    {% if ran %}
        {% if not result.ok %}
        <div class="err">{{ result.error }}</div>
        {% else %}
        <div class="card">
            <p style="margin:0;color:#8b93a1;">MTU thuc te toi <strong>{{ host }}</strong> qua {{ iface }}:</p>
            <p class="big" style="margin:6px 0;">{{ result.mtu }} bytes</p>
            {% if result.tu_router %}
            <p class="hint">Gia tri nay do mot router giua duong bao thang qua ICMP
            (Frag needed) - dang tin cay nhat, khong phai uoc luong.</p>
            {% endif %}
            <p class="hint">MTU cau hinh cua chinh cong {{ iface }}: {{ result.mtu_interface }} bytes.</p>
        </div>
        {% if result.canh_bao %}<div class="warn">⚠️ {{ result.canh_bao }}</div>{% endif %}

        <details>
            <summary>Xem chi tiet cac buoc do ({{ result.chi_tiet|length }} lan thu)</summary>
            <table>
                <tr><th>Payload</th><th>MTU tuong ung</th><th>Ket qua</th></tr>
                {% for b in result.chi_tiet %}
                <tr>
                    <td>{{ b.payload }}</td>
                    <td>{{ b.mtu_tuong_ung }}</td>
                    <td>{% if b.ket_qua == 'ok' %}<span style="color:#8fd99a;">✔ Qua duoc</span>
                        {% elif b.ket_qua == 'qua_lon' %}<span style="color:#ff8a8a;">✘ Qua lon</span>
                        {% else %}<span style="color:#999;">? Khong ro (mat goi)</span>{% endif %}</td>
                </tr>
                {% endfor %}
            </table>
        </details>
        {% endif %}
    {% endif %}
</body>
</html>
"""


@nettools_bp.route("/nettools/mtu", methods=["GET", "POST"])
def mtu_route():
    host = request.form.get("host", "").strip()
    iface = request.form.get("iface", "eth0")
    ran = request.method == "POST"
    result = tim_mtu(host, iface=iface) if ran else None
    return render_template_string(MTU_TEMPLATE, host=host, iface=iface, ran=ran, result=result)


if __name__ == "__main__":
    import sys
    import json
    iface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    host = sys.argv[2] if len(sys.argv) > 2 else "8.8.8.8"
    print(json.dumps(tim_mtu(host, iface=iface), indent=2, ensure_ascii=False))
