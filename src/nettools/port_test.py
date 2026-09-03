"""
Console Pi Network Tools - Kiem tra cong mang day (RJ45)

Gop tat ca thong tin huu ich khi cam mot soi day vao switch/router chua
biet gi ve no:
  1. Toc do/duplex THAT ma cong da thuong luong (ethtool) - phat hien ngay
     loi kinh dien "duplex mismatch" hay switch gioi han toc do
  2. Nang luc phia ben kia quang bao (link partner) - so sanh voi nang luc
     cua chinh Pi de biet ai la nguoi "ep" toc do thap hon
  3. Thong ke loi duong truyen (CRC, drop, collision...) - cap day kem hay
     nhieu se hien ra o day truoc ca khi nguoi dung nhan ra mang cham
  4. PoE - doc duoc neu phan cung ho tro (hien tai Pi thuong khong co mach
     PoE, code chi tu bao "khong phat hien" thay vi bia du lieu)
  5. Bang thong THAT: uu tien Cloudflare speed test (khong can chuan bi gi
     o dau kia - hop khi cong dang cam vao switch/router bat ky), hoac
     iperf3 toi mot may cu the neu nguoi dung co san server o dau kia.
"""
import json
import re
import subprocess
import time

from flask import request, render_template_string

from . import nettools_bp

CLOUDFLARE_SPEEDTEST_BYTES = 25_000_000  # 25MB - du de co so lieu on dinh, khong qua nang


# --------------------------------------------------------------- ethtool
def _chay(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", "khong-cai-dat"
    except subprocess.TimeoutExpired:
        return -1, "", "qua-thoi-gian-cho"
    except Exception as e:
        return -1, "", str(e)


def doc_thong_tin_cong(iface):
    """Toc do/duplex thuong luong that, nang luc hai ben, trang thai lien ket."""
    rc, out, err = _chay(["ethtool", iface])
    if rc != 0:
        if "khong-cai-dat" in err:
            return {"ok": False, "loi": "Chua cai ethtool tren may."}
        return {"ok": False, "loi": f"Khong doc duoc thong tin cong: {err.strip()[:150]}"}

    def _lay(nhan, van_ban):
        m = re.search(rf"{nhan}:\s*(.+)", van_ban)
        return m.group(1).strip() if m else ""

    def _lay_khoi(nhan, van_ban):
        """
        Cac muc 'Advertised link modes' / 'Link partner advertised link
        modes' trai dai nhieu dong noi tiep, thut le sau nhan dau tien.

        Khong the dung "dong khong thut le la het khoi" - TOAN BO output
        cua ethtool deu thut le bang 1 tab, kem ca cac truong khac ngay sau
        do (da gap bug that: bat luon ca phan con lai cua output). Cach dung:
        cac dong NOI TIEP cua mot danh sach mode la CHUOI THUAN cac gia tri
        (khong co dau ':'), con moi TRUONG MOI luon co dau ':' o dau dong.
        """
        dong = van_ban.splitlines()
        ket_qua = []
        dang_doc = False
        for d in dong:
            if not dang_doc:
                m = re.match(rf"\s*{nhan}:\s*(.*)$", d)
                if m:
                    dang_doc = True
                    ket_qua += m.group(1).split()
                continue
            # Dang doc phan noi tiep: dong nay co ':' o dau (truong moi) thi dung
            if re.match(r"\s*[A-Za-z][^:]*:", d):
                break
            ket_qua += d.split()
        return ket_qua

    ket_qua = {
        "ok": True, "loi": None,
        "toc_do": _lay("Speed", out) or "?",
        "duplex": _lay("Duplex", out) or "?",
        "auto_neg": _lay("Auto-negotiation", out) or "?",
        "lien_ket": _lay("Link detected", out) or "?",
        "nang_luc_minh": _lay_khoi("Advertised link modes", out),
        "nang_luc_doi_phuong": _lay_khoi(r"Link partner advertised link modes", out),
    }

    rc2, out2, _ = _chay(["ethtool", "-i", iface])
    if rc2 == 0:
        ket_qua["driver"] = _lay("driver", out2) or "?"

    # Canh bao duplex mismatch / bi ep toc do thap: neu ca hai ben deu quang
    # ba ho tro Gigabit ma toc do thuong luong cuoi cung lai thap hon nhieu
    if "1000baseT" in " ".join(ket_qua["nang_luc_minh"]) and \
       "1000baseT" in " ".join(ket_qua["nang_luc_doi_phuong"]) and \
       ket_qua["toc_do"] not in ("1000Mb/s", "?"):
        ket_qua["canh_bao"] = (f"Ca hai ben deu ho tro Gigabit nhung chi thuong luong duoc "
                               f"{ket_qua['toc_do']} - kiem tra lai chat luong day cap hoac "
                               f"cai dat toc do co dinh (fixed speed) tren switch.")
    elif ket_qua["duplex"] == "Half":
        ket_qua["canh_bao"] = ("Dang chay Half Duplex - hau nhu chac chan la loi cau hinh "
                              "(duplex mismatch), gay mat goi va cham ro ret. Kiem tra cai dat "
                              "tren cong switch phia ben kia.")
    else:
        ket_qua["canh_bao"] = None

    return ket_qua


def doc_thong_ke_loi(iface):
    """So goi loi/rot/va cham - cap kem hoac nhieu se hien ra day dau tien."""
    rc, out, err = _chay(["ethtool", "-S", iface])
    if rc != 0:
        return {"ok": False, "loi": "Card mang nay khong ho tro doc thong ke chi tiet."}

    muon_biet = ["rx_errors", "tx_errors", "rx_dropped", "tx_dropped",
                "rx_crc_errors", "rx_length_errors", "rx_over_errors",
                "rx_missed_errors", "collisions", "tx_aborted_errors"]
    so_lieu = {}
    for dong in out.splitlines():
        if ":" not in dong:
            continue
        khoa, _, gia_tri = dong.strip().partition(":")
        khoa = khoa.strip()
        if khoa in muon_biet:
            try:
                so_lieu[khoa] = int(gia_tri.strip())
            except ValueError:
                pass

    tong_loi = sum(so_lieu.values())
    return {"ok": True, "so_lieu": so_lieu, "tong_loi": tong_loi}


def kiem_tra_cap(iface):
    """
    Chan doan cap vat ly (TDR - do khoang cach den cho dut/cham). Nhieu
    driver pho thong (bcmgenet cua Pi la mot vi du) KHONG ho tro tinh nang
    nay - tra ve ro rang thay vi gia vo co ket qua.
    """
    rc, out, err = _chay(["ethtool", "--test", iface], timeout=20)
    if rc != 0 or "not supported" in (err + out).lower() or "Cannot test" in (err + out):
        return {"ho_tro": False, "loi": None}
    return {"ho_tro": True, "ket_qua": out.strip()}


def doc_poe(iface):
    """
    PoE - CHI hien khi phan cung THAT SU co mach do (vi du UPS/PoE HAT gan
    driver rieng). Pi va cac card mang thong thuong KHONG co mach nay -
    tra ve None thay vi bia du lieu.
    """
    ung_vien = [
        f"/sys/class/net/{iface}/device/poe_power",
        "/sys/class/hwmon/hwmon0/poe_watts",
    ]
    for duong in ung_vien:
        try:
            with open(duong) as f:
                return {"phat_hien": True, "gia_tri": f.read().strip()}
        except OSError:
            continue
    return {"phat_hien": False}


# --------------------------------------------------------------- bang thong
def cloudflare_speedtest(so_byte=CLOUDFLARE_SPEEDTEST_BYTES):
    """
    Tai mot luong du lieu tu speed.cloudflare.com - dich vu speedtest cong
    khai chinh chu cua Cloudflare, khong can chuan bi gi o dau kia. Hop
    nhat khi cong dang cam vao switch/router (khong co iperf3 server rieng
    o dau day).
    """
    url = f"https://speed.cloudflare.com/__down?bytes={so_byte}"
    rc, out, err = _chay(
        ["curl", "-s", "-o", "/dev/null", "-m", "20",
         "-w", "%{speed_download} %{http_code} %{time_total}", url],
        timeout=25,
    )
    if rc != 0:
        return {"ok": False, "loi": f"Khong tai duoc: {err.strip()[:150]}"}
    phan = out.split()
    if len(phan) < 2 or phan[1] != "200":
        return {"ok": False, "loi": f"Cloudflare tra ve loi (HTTP {phan[1] if len(phan)>1 else '?'})."}
    bytes_per_s = float(phan[0])
    mbps = bytes_per_s * 8 / 1_000_000
    return {"ok": True, "mbps": round(mbps, 1), "thoi_gian_s": phan[2], "so_mb": so_byte // 1_000_000}


def iperf3_client(target_ip, huong="upload", thoi_luong=5):
    """
    Chay iperf3 toi mot server cu the (nguoi dung tu chay `iperf3 -s` o may
    do). huong='upload': Pi gui di. huong='download' (-R): Pi nhan ve.
    """
    if not re.fullmatch(r"[0-9a-fA-F.:]{3,45}", target_ip or ""):
        return {"ok": False, "loi": "Dia chi IP khong hop le."}
    # --connect-timeout: phat hien nhanh truong hop IP sai/khong co server,
    # khong de nguoi dung ngoi cho ca chuc giay moi biet la that bai.
    cmd = ["iperf3", "-c", target_ip, "-t", str(thoi_luong), "-J",
           "--connect-timeout", "3000"]
    if huong == "download":
        cmd.append("-R")
    rc, out, err = _chay(cmd, timeout=thoi_luong + 6)
    if rc != 0:
        loi = err.strip() or out.strip()
        if "Connection refused" in loi:
            loi = f"Khong ket noi duoc toi {target_ip}:5201 - da chay 'iperf3 -s' o may do chua?"
        elif "khong-cai-dat" in loi:
            loi = "Chua cai iperf3 tren Console Pi."
        elif "qua-thoi-gian-cho" in loi or "timed out" in loi.lower() or not loi:
            loi = (f"Khong nhan duoc phan hoi tu {target_ip} sau vai giay - kiem tra lai IP, "
                  "hoac may do chua bat 'iperf3 -s', hoac tuong lua dang chan cong 5201.")
        return {"ok": False, "loi": loi[:200]}
    try:
        d = json.loads(out)
        mbps = d["end"]["sum_received"]["bits_per_second"] / 1_000_000 \
            if huong == "upload" else d["end"]["sum_sent"]["bits_per_second"] / 1_000_000
        return {"ok": True, "mbps": round(mbps, 1), "huong": huong, "target": target_ip}
    except (json.JSONDecodeError, KeyError) as e:
        return {"ok": False, "loi": f"Khong doc duoc ket qua iperf3: {e}"}


def iperf3_da_cai():
    rc, _, _ = _chay(["which", "iperf3"], timeout=5)
    return rc == 0


# --------------------------------------------------------------- giao dien
PORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Kiem tra cong mang - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; } h3 { color: #4CAF50; margin-top: 24px; }
        a { color: #4CAF50; }
        select, input[type=text], input[type=number] { padding: 8px; background: #333; color: #eee; border: 1px solid #555; }
        button { padding: 9px 16px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button.gray { background: #555; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { padding: 9px 10px; text-align: left; border-bottom: 1px solid #444; vertical-align: top; }
        th { background: #2d2d2d; width: 220px; }
        .card { background:#262626; border:1px solid #3a3a3a; border-left:4px solid #4CAF50;
                border-radius:6px; padding:14px 16px; margin-top:16px; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .warn { background: #4a3d1a; border-left: 4px solid #ffb74d; padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .ok-txt { color: #8fd99a; } .bad-txt { color: #ff8a8a; }
        .hint { color: #999; font-size: 13px; }
        .modes { display:flex; gap:6px; flex-wrap:wrap; }
        .mode-chip { background:#1f1f1f; border:1px solid #444; border-radius:10px; padding:2px 9px; font-size:12px; }
    </style>
</head>
<body>
    <h1>🔌 Kiem tra cong mang day</h1>
    <p><a href="/nettools">← Network Tools</a></p>

    <form method="GET" style="margin-top:12px;">
        <label>Cong:</label>
        <select name="iface" onchange="this.form.submit()">
            <option value="eth0" {{ 'selected' if iface=='eth0' else '' }}>eth0</option>
        </select>
    </form>

    {% if thong_tin.ok %}
    <div class="card">
        <h3 style="margin-top:0;">Toc do / Duplex</h3>
        <table>
            <tr><th>Toc do thuong luong</th><td style="font-size:17px;font-weight:600;">{{ thong_tin.toc_do }}</td></tr>
            <tr><th>Duplex</th><td>{{ thong_tin.duplex }}</td></tr>
            <tr><th>Auto-negotiation</th><td>{{ thong_tin.auto_neg }}</td></tr>
            <tr><th>Lien ket (link)</th><td>{{ thong_tin.lien_ket }}</td></tr>
            <tr><th>Driver</th><td><code>{{ thong_tin.driver }}</code></td></tr>
            <tr><th>Nang luc cua Pi</th><td><div class="modes">{% for m in thong_tin.nang_luc_minh %}<span class="mode-chip">{{ m }}</span>{% endfor %}</div></td></tr>
            <tr><th>Nang luc phia ben kia</th><td><div class="modes">{% for m in thong_tin.nang_luc_doi_phuong %}<span class="mode-chip">{{ m }}</span>{% endfor %}
                {% if not thong_tin.nang_luc_doi_phuong %}<span class="hint">Khong doc duoc (cong co the dang down)</span>{% endif %}</div></td></tr>
        </table>
        {% if thong_tin.canh_bao %}<div class="warn" style="margin-top:11px;">⚠️ {{ thong_tin.canh_bao }}</div>{% endif %}
    </div>
    {% else %}
    <div class="err">{{ thong_tin.loi }}</div>
    {% endif %}

    <div class="card">
        <h3 style="margin-top:0;">Thong ke loi duong truyen</h3>
        {% if loi_truyen.ok %}
        <table>
            {% for khoa, gt in loi_truyen.so_lieu.items() %}
            <tr><th>{{ khoa }}</th><td class="{{ 'bad-txt' if gt > 0 else 'ok-txt' }}">{{ gt }}</td></tr>
            {% endfor %}
        </table>
        <p style="margin-top:9px;" class="{{ 'bad-txt' if loi_truyen.tong_loi > 0 else 'ok-txt' }}">
            {% if loi_truyen.tong_loi == 0 %}🟢 Khong co loi nao duoc ghi nhan{% else %}
            🔴 Tong {{ loi_truyen.tong_loi }} loi - day cap co the kem chat luong hoac bi nhieu{% endif %}</p>
        {% else %}<p class="hint">{{ loi_truyen.loi }}</p>{% endif %}
    </div>

    <div class="card">
        <h3 style="margin-top:0;">Cap vat ly (TDR)</h3>
        {% if cap.ho_tro %}<pre style="background:#111;padding:10px;border-radius:4px;">{{ cap.ket_qua }}</pre>
        {% else %}<p class="hint">Card mang nay ({{ thong_tin.driver }}) khong ho tro do khoang cach den cho dut cap qua phan mem.
        Dung dong ho do cap (cable tester) rieng neu can kiem tra chi tiet day vat ly.</p>{% endif %}
    </div>

    <div class="card">
        <h3 style="margin-top:0;">PoE (nguon qua cap mang)</h3>
        {% if poe.phat_hien %}<p>🟢 Phat hien PoE: {{ poe.gia_tri }}</p>
        {% else %}<p class="hint">Khong phat hien mach do PoE tren phan cung nay (Raspberry Pi khong co san,
        can PoE HAT rieng co ho tro doc gia tri).</p>{% endif %}
    </div>

    <div class="card">
        <h3 style="margin-top:0;">📶 Bang thong that</h3>
        <p class="hint" style="margin:0 0 12px;">Toc do thuong luong o tren chi la GIOI HAN TOI DA cua cong -
        muon biet bang thong THAT phai truyen du lieu that su qua day.</p>

        <h4 style="color:#ccc;margin:0 0 6px;">Cach 1 - Khong can chuan bi gi (qua Internet)</h4>
        <form method="POST" action="/nettools/port-test/speedtest">
            <input type="hidden" name="iface" value="{{ iface }}">
            <button type="submit" data-busy="Dang tai 25MB de do toc do...">🚀 Do toc do qua Cloudflare</button>
        </form>
        {% if speedtest_result %}
            {% if speedtest_result.ok %}
            <div class="ok-txt" style="margin-top:11px;font-size:22px;font-weight:700;">
                ⬇ {{ speedtest_result.mbps }} Mbps</div>
            <p class="hint">Tai {{ speedtest_result.so_mb }}MB trong {{ speedtest_result.thoi_gian_s }}s qua speed.cloudflare.com</p>
            {% else %}<div class="err" style="margin-top:11px;">{{ speedtest_result.loi }}</div>{% endif %}
        {% endif %}

        <h4 style="color:#ccc;margin:20px 0 6px;">Cach 2 - Chinh xac hon, can may thu hai chay iperf3</h4>
        {% if iperf_result and not iperf_result.ok %}
        <div class="err">{{ iperf_result.loi }}</div>
        {% endif %}
        {% if not iperf3_co %}
        <div class="warn">Chua cai <code>iperf3</code> tren Console Pi. Chay:
            <code>sudo apt install -y iperf3</code></div>
        {% else %}
        <p class="hint" style="margin:0 0 9px;">O may thu hai (laptop/server cam chung switch), chay
            <code>iperf3 -s</code> roi dien IP cua may do vao day.</p>
        <form method="POST" action="/nettools/port-test/iperf3">
            <input type="hidden" name="iface" value="{{ iface }}">
            <label>IP may chay iperf3 -s:</label>
            <input type="text" name="target" placeholder="192.168.1.50" value="{{ iperf_target or '' }}" required>
            <div class="row" style="margin-top:11px;display:flex;gap:9px;">
                <button type="submit" name="huong" value="upload" data-busy="Dang do 5 giay...">⬆ Do Upload (Pi → may do)</button>
                <button type="submit" name="huong" value="download" class="gray" data-busy="Dang do 5 giay...">⬇ Do Download (may do → Pi)</button>
            </div>
        </form>
        {% if iperf_result and iperf_result.ok %}
            <div class="ok-txt" style="margin-top:11px;font-size:22px;font-weight:700;">
                {{ '⬆' if iperf_result.huong=='upload' else '⬇' }} {{ iperf_result.mbps }} Mbps
                <span style="font-size:13px;color:#999;">({{ 'Upload' if iperf_result.huong=='upload' else 'Download' }}, toi {{ iperf_result.target }})</span></div>
        {% endif %}
        {% endif %}
    </div>
</body>
</html>
"""


def _render(iface, speedtest_result=None, iperf_result=None, iperf_target=None):
    return render_template_string(
        PORT_TEMPLATE, iface=iface,
        thong_tin=doc_thong_tin_cong(iface),
        loi_truyen=doc_thong_ke_loi(iface),
        cap=kiem_tra_cap(iface),
        poe=doc_poe(iface),
        iperf3_co=iperf3_da_cai(),
        speedtest_result=speedtest_result,
        iperf_result=iperf_result,
        iperf_target=iperf_target,
    )


@nettools_bp.route("/nettools/port-test")
def port_test_route():
    iface = request.args.get("iface", "eth0")
    return _render(iface)


@nettools_bp.route("/nettools/port-test/speedtest", methods=["POST"])
def port_test_speedtest_route():
    iface = request.form.get("iface", "eth0")
    return _render(iface, speedtest_result=cloudflare_speedtest())


@nettools_bp.route("/nettools/port-test/iperf3", methods=["POST"])
def port_test_iperf3_route():
    iface = request.form.get("iface", "eth0")
    target = request.form.get("target", "").strip()
    huong = request.form.get("huong", "upload")
    return _render(iface, iperf_result=iperf3_client(target, huong=huong), iperf_target=target)


if __name__ == "__main__":
    import sys
    iface = sys.argv[1] if len(sys.argv) > 1 else "eth0"
    print(json.dumps({
        "port": doc_thong_tin_cong(iface),
        "loi": doc_thong_ke_loi(iface),
        "cap": kiem_tra_cap(iface),
        "poe": doc_poe(iface),
    }, indent=2, ensure_ascii=False))
