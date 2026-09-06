"""
Console Pi Network Tools - Sao luu cau hinh QUA DAY CONSOLE (khong can mang)

CAU HOI THUC TE DAN TOI TINH NANG NAY: "trong tftp, neu anh chi co cam day
console vao thoi thi backup kieu gi?"

TFTP bat buoc phai co duong IP giua Pi va thiet bi (lenh
`copy running-config tftp://...` la thiet bi TU MO ket noi mang toi Pi).
Nhung dung cach hay gap nhat cua Console Pi lai la: switch/router VUA HONG
cau hinh, mat IP quan ly, khong vao duoc bang mang - chi con cong console.
Luc do TFTP vo dung.

BA PHUONG AN, va vi sao chon phuong an 3:

  1. USB cam THANG VAO SWITCH (`copy running-config usbflash0:`): nhanh va
     sach nhat KHI thiet bi co cong USB va IOS ho tro. Nhung rat nhieu thiet
     bi khong co (2960 doi cu, cac switch nho, thiet bi hang khac), va luc
     do van phai co cach khac. Khong the dua vao.

  2. USB cam vao PI roi bang cach nao do "hut" file qua console: KHONG lam
     duoc theo nghia den. Cong console la duong noi tiep chi truyen KY TU,
     khong phai duong truyen file - khong co giao thuc nao san co tren
     IOS/switch de day mot file nhi phan qua day console (xmodem co tren
     mot so thiet bi nhung la de NAP firmware VAO thiet bi luc cuu ho, rat
     cham va khong phai de lay config ra).

  3. DOC MAN HINH (cach nay dung): bao thiet bi in cau hinh ra man hinh
     console (`show running-config`) roi HUNG toan bo chu do luu thanh file.
     Chay voi MOI thiet bi co cong console, khong can IP, khong can USB,
     khong can thiet bi ho tro gi them. Day chinh la cach ky su van lam tay
     bang PuTTY (bat "session logging" roi go show run) - o day chi la lam
     tu dong lai.

Lam duoc de dang la nho san co tmux: moi phien console cua Console Pi deu
chay trong tmux (xem scripts/ttyd-one.sh), nen co the:
  - `tmux send-keys`     -> go lenh ho thiet bi
  - `tmux capture-pane`  -> hung lai toan bo chu da hien ra man hinh
Khong can them thu vien hay tien trinh nao moi.

LUU O DAU: thu muc rieng /opt/console-pi/backups, KHONG dung chung thu muc
TFTP. Ly do that: file cau hinh switch chua mat khau (ke ca dang ma hoa
yeu kieu type 7), ma thu muc TFTP khi bat dich vu len thi BAT KY thiet bi
nao cam vao eth0 cung tai ve duoc, khong can xac thuc. De ban luu o do la
tu tay lam ro thong tin nhay cam.
"""
import os
import re
import subprocess
import time

from flask import request, render_template_string, send_from_directory, abort

from . import nettools_bp

BACKUP_DIR = "/opt/console-pi/backups"

# Cac lenh in cau hinh theo tung dong thiet bi. Truoc khi in phai TAT PHAN
# TRANG (khong co thi thiet bi dung lai o "--More--" va cho bam phim, ban
# luu se cut giua chung).
#
# can_enable: LOI THAT DA GAP (anh Thoai bao chup khong ra, gui anh chup man
# hinh) - Cisco/HP-Aruba yeu cau vao CHE DO DAC QUYEN (dau nhac "Switch#",
# go lenh "enable") truoc khi "show running-config" hoat dong duoc. Neu con
# o che do nguoi dung (dau nhac "Switch>") thi thiet bi tra loi "% Invalid
# input detected" - dung nhu anh Thoai gap. Truoc day code khong kiem tra
# dieu nay, cu go lenh dai roi luu luon ca thong bao loi vao file.
# Juniper/MikroTik KHONG co khai niem "che do dac quyen" rieng kieu nay -
# dang nhap xong la du quyen xem cau hinh ngay, nen khong can kiem tra.
HO_THIET_BI = {
    "cisco": {
        "ten": "Cisco IOS / IOS-XE (va cac dong tuong thich)",
        "can_enable": True,
        "tat_phan_trang": "terminal length 0",
        "lenh": "show running-config",
    },
    "cisco_nxos": {
        "ten": "Cisco NX-OS (Nexus)",
        "can_enable": True,
        "tat_phan_trang": "terminal length 0",
        "lenh": "show running-config",
    },
    "hp_aruba": {
        "ten": "HP / Aruba ProCurve",
        "can_enable": True,
        "tat_phan_trang": "no page",
        "lenh": "show running-config",
    },
    "juniper": {
        "ten": "Juniper JunOS",
        "can_enable": False,
        "tat_phan_trang": "set cli screen-length 0",
        "lenh": "show configuration | display set",
    },
    "mikrotik": {
        "ten": "MikroTik RouterOS",
        "can_enable": False,
        "tat_phan_trang": "",
        "lenh": "/export",
    },
}

# Doi output im lang bao lau thi coi la thiet bi da in xong. 3 giay du an
# toan cho ca thiet bi cham (config dai vai nghin dong tren duong 9600 baud
# van in lien tuc, khong ngat qua 3 giay giua chung).
GIAY_IM_LANG = 3.0
GIAY_TOI_DA = 180.0


def _sh(cmd, timeout=20):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return False, str(e)


def phien_tmux(dev):
    """Ten phien tmux cua 1 cong console - PHAI khop scripts/ttyd-one.sh."""
    return f"console-{dev}"


def phien_dang_chay(dev):
    ok, out = _sh(["tmux", "has-session", "-t", phien_tmux(dev)])
    return ok


def danh_sach_cong():
    """Cac cong console dang cam (dung chung logic voi trang Tong quan)."""
    import glob
    ra = []
    for duong in sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")):
        dev = os.path.basename(duong)
        ra.append({"dev": dev, "co_phien": phien_dang_chay(dev)})
    return ra


def _capture(dev, tu_dong=None):
    """Hung lai chu dang co tren man hinh + lich su cuon cua phien tmux."""
    lenh = ["tmux", "capture-pane", "-p", "-J", "-t", phien_tmux(dev),
            "-S", str(tu_dong if tu_dong is not None else "-")]
    ok, out = _sh(lenh, timeout=30)
    return out if ok else ""


def _go(dev, chuoi, enter=True):
    cmd = ["tmux", "send-keys", "-t", phien_tmux(dev), chuoi]
    if enter:
        cmd.append("Enter")
    return _sh(cmd, timeout=10)[0]


def _dau_nhac_cuoi(text):
    """Dong khong rong CUOI CUNG cua ban chup - dung de doan dau nhac hien tai."""
    for dong in reversed(text.splitlines()):
        if dong.strip():
            return dong.strip()
    return ""


def _la_dau_nhac_dac_quyen(dong):
    """True neu dong ket thuc bang '#' (che do dac quyen cua Cisco/HP-Aruba)."""
    return bool(re.search(r"#\s*$", dong))


def _la_dau_nhac_nguoi_dung(dong):
    """True neu dong ket thuc bang '>' (che do nguoi dung, CHUA du quyen)."""
    return bool(re.search(r">\s*$", dong)) and not _la_dau_nhac_dac_quyen(dong)


def _cat_phan_moi(text, lenh_da_go):
    """
    Lay phan NOI DUNG THAT trong ban chup: tim lan xuat hien CUOI CUNG cua
    chinh lenh vua go (thiet bi in lai lenh ngay sau khi nhan Enter), lay tat
    ca o SAU dong do, roi bo dau nhac ket thuc ban chup.

    Dung "lan cuoi cung" (khong phai lan dau) vi neu nguoi dung da tung tu go
    lenh nay truoc do trong cung phien console, ban chup se co NHIEU lan xuat
    hien - chi lay tu lan gan nhat (cua chinh lan chup nay) tro di.
    """
    dong = text.splitlines()
    vi_tri = -1
    for i in range(len(dong) - 1, -1, -1):
        if lenh_da_go and lenh_da_go in dong[i]:
            vi_tri = i
            break
    if vi_tri >= 0:
        dong = dong[vi_tri + 1:]

    while dong and not dong[0].strip():
        dong.pop(0)

    # Bo dau nhac cuoi ("Switch#", "router>", "[admin@MikroTik] >" ...)
    while dong and (not dong[-1].strip() or
                    re.search(r"[#>$]\s*$", dong[-1].strip())):
        if dong[-1].strip() and len(dong[-1].strip()) > 60:
            break        # dong dai the nay la noi dung that, khong phai dau nhac
        dong.pop()

    return "\n".join(dong).rstrip() + "\n"


def chup_cau_hinh(dev, ho="cisco", ten_file=""):
    """
    Bao thiet bi in cau hinh ra console roi hung lai thanh file.

    Tra ve (ok, thong_diep, ten_file_da_luu).
    """
    dev = os.path.basename((dev or "").strip())
    if not re.fullmatch(r"tty(USB|ACM)\d+", dev):
        return False, "Ten cong khong hop le.", ""
    if not os.path.exists(f"/dev/{dev}"):
        return False, f"Khong thay /dev/{dev} - co the cap da bi rut.", ""
    if not phien_dang_chay(dev):
        return False, (f"Chua co phien console cho {dev}. Vao Tong quan bam "
                       f"'Mo Console' cho cong nay truoc roi quay lai."), ""

    cau_hinh = HO_THIET_BI.get(ho) or HO_THIET_BI["cisco"]

    # LOI THAT DA GAP (anh Thoai chup thu, thiet bi tra "% Invalid input
    # detected" vi con dang o dau nhac "Switch>" - chua go "enable"). Kiem
    # tra dau nhac HIEN TAI truoc khi go bat ky lenh nao - neu thieu quyen
    # thi bao ro va DUNG LAI, khong go lenh se chac chan that bai.
    truoc = _capture(dev)
    dong_cuoi = _dau_nhac_cuoi(truoc)
    # dong_cuoi la chu THIET BI THAT gui ve - escape truoc khi nhet vao HTML
    # (msg duoc render voi |safe de cho phep the <code> ta tu viet o duoi).
    dong_cuoi_html = (dong_cuoi.replace("&", "&amp;").replace("<", "&lt;")
                      .replace(">", "&gt;").replace('"', "&quot;"))
    if cau_hinh["can_enable"] and _la_dau_nhac_nguoi_dung(dong_cuoi):
        return False, (
            f"Thiet bi dang o che do nguoi dung (dau nhac \"{dong_cuoi_html}\"), "
            f"chua du quyen xem cau hinh. Mo khung Console cho {dev}, go "
            f"lenh <code>enable</code> (nhap mat khau neu thiet bi hoi) cho "
            f"toi khi dau nhac doi thanh dau # (vd \"Switch#\"), roi quay "
            f"lai bam chup."), ""

    # Danh thuc phien + tat phan trang. KHONG dung "tmux clear-history" de
    # ngan cach truoc/sau - LOI THAT DA GAP: lenh do chi xoa BO DEM CUON cua
    # tmux, KHONG xoa noi dung DANG HIEN TREN MAN HINH, nen chu cua buoc
    # "terminal length 0" van con nguyen trong ban chup va bi lan/lap voi
    # noi dung that. Thay vao do dung _cat_phan_moi() de tim dung vi tri
    # SAU KHI go lenh chinh, khong phu thuoc gi vao viec xoa man hinh.
    _go(dev, "", enter=True)
    time.sleep(0.6)
    if cau_hinh["tat_phan_trang"]:
        _go(dev, cau_hinh["tat_phan_trang"])
        time.sleep(1.0)

    _go(dev, cau_hinh["lenh"])

    # Cho toi khi thiet bi in xong: theo doi do dai ban chup, im lang du lau
    # thi dung. Khong dat thoi gian cho cung vi config dai/ngan rat khac nhau.
    bat_dau = time.time()
    dai_truoc = -1
    lan_cuoi_doi = time.time()
    text = ""
    while time.time() - bat_dau < GIAY_TOI_DA:
        time.sleep(1.0)
        text = _capture(dev)
        if len(text) != dai_truoc:
            dai_truoc = len(text)
            lan_cuoi_doi = time.time()
        elif time.time() - lan_cuoi_doi >= GIAY_IM_LANG:
            break

    text = _cat_phan_moi(text, cau_hinh["lenh"])
    if len(text.strip()) < 20 or "invalid input" in text.lower() or "% unknown" in text.lower():
        return False, (
            "Khong lay duoc cau hinh - co the lenh khong dung voi thiet bi nay "
            "(kiem tra lai da chon dung Dong thiet bi chua), hoac day console "
            "cam sai cong, hoac thiet bi chua dang nhap xong."), ""

    os.makedirs(BACKUP_DIR, exist_ok=True)
    ten = os.path.basename((ten_file or "").strip())
    if not ten or not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", ten):
        ten = f"{dev}-{time.strftime('%Y%m%d-%H%M%S')}.cfg"
    duong = os.path.join(BACKUP_DIR, ten)
    try:
        with open(duong, "w", encoding="utf-8", errors="replace") as f:
            f.write(text)
        os.chmod(duong, 0o600)   # chua mat khau thiet bi - chi root doc duoc
    except OSError as e:
        return False, f"Khong luu duoc file: {e}", ""

    so_dong = text.count("\n")
    return True, f"Da luu {so_dong} dong vao {ten}.", ten


def duong_dan_an_toan(ten):
    ten = os.path.basename((ten or "").strip())
    if not ten or ten in (".", ".."):
        return None
    duong = os.path.join(BACKUP_DIR, ten)
    if os.path.realpath(duong) != os.path.join(os.path.realpath(BACKUP_DIR), ten):
        return None
    if not os.path.isfile(duong):
        return None
    return duong


def danh_sach_ban_luu():
    if not os.path.isdir(BACKUP_DIR):
        return []
    ra = []
    for ten in os.listdir(BACKUP_DIR):
        duong = os.path.join(BACKUP_DIR, ten)
        if not os.path.isfile(duong):
            continue
        try:
            st = os.stat(duong)
            ra.append({"ten": ten, "kich_thuoc": st.st_size, "mtime": st.st_mtime,
                       "thoi_gian": time.strftime("%Y-%m-%d %H:%M",
                                                  time.localtime(st.st_mtime))})
        except OSError:
            continue
    return sorted(ra, key=lambda x: x["mtime"], reverse=True)


def xoa_ban_luu(ten):
    duong = duong_dan_an_toan(ten)
    if not duong:
        return False, "Ten file khong hop le hoac khong tim thay."
    try:
        os.remove(duong)
    except OSError as e:
        return False, f"Khong xoa duoc: {e}"
    return True, f"Da xoa {os.path.basename(duong)}."


TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Sao luu qua cap console - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        .hint { color:#8b93a1; font-size:13px; }
        .khoi { background:#1b1e22; border:1px solid #2c3036; border-left:4px solid #4CAF50;
                border-radius:9px; padding:17px 19px; margin-bottom:16px; }
        .nut-tai { display:inline-block; background:#2563eb; color:#fff !important;
                   padding:11px 15px; border-radius:6px; text-decoration:none;
                   margin-right:7px; min-height:44px; line-height:22px; box-sizing:border-box; }
    </style>
</head>
<body>
    <h1>🔌 Sao luu cau hinh qua cap console</h1>
    <p><a href="/nettools">← Network Tools</a></p>

    {% if msg %}<div class="msg {{ 'ok' if ok else 'err' }}">{{ msg | safe }}</div>{% endif %}

    <div class="msg info">
        Dung khi thiet bi <strong>mat IP quan ly / chua cau hinh mang</strong> nen khong
        TFTP duoc - chi con cap console. Console Pi se bao thiet bi in cau hinh ra man
        hinh roi hung lai thanh file (giong bat "session logging" trong PuTTY, nhung tu dong).
    </div>

    {% if not cong %}
    <div class="msg warn">Chua cam cap console nao. Cam cap USB-serial vao Pi roi tai lai trang.</div>
    {% else %}
    <div class="msg warn">
        ⚠️ <strong>Voi Cisco/HP-Aruba: phai vao che do dac quyen truoc</strong> (dau nhac
        ket thuc bang <code>#</code>, vd <code>Switch#</code>) - mo khung Console cho cong
        do, go <code>enable</code> (nhap mat khau neu thiet bi hoi) cho toi khi thay dau
        <code>#</code>, roi moi quay lai bam chup. Neu con dang o dau nhac
        <code>&gt;</code> thi thiet bi se tu choi lenh va Console Pi se bao ro cho anh biet,
        khong luu ban chup loi.
    </div>
    <div class="khoi">
        <h3>Chup cau hinh</h3>
        <form method="POST" action="/nettools/console-backup/chup">
            <label>Cong console</label>
            <select name="dev" required>
                {% for c in cong %}
                <option value="{{ c.dev }}" {{ 'selected' if c.dev == dev_chon else '' }}>
                  {{ c.dev }}{% if not c.co_phien %} (chua mo phien console){% endif %}</option>
                {% endfor %}
            </select>

            <label>Dong thiet bi</label>
            <select name="ho">
                {% for ma, h in ho_thiet_bi.items() %}
                <option value="{{ ma }}">{{ h.ten }}</option>
                {% endfor %}
            </select>

            <label>Ten file (de trong = tu dat theo ngay gio)</label>
            <input type="text" name="ten_file" placeholder="vd: switch-tang3.cfg">

            <div class="row" style="margin-top:14px;">
                <button type="submit" data-busy="Dang chup, co the mat 1-3 phut...">
                    ⬇ Chup cau hinh ngay</button>
                <a class="btn gray" href="/console/{{ dev_chon }}">↗ Mo khung Console (go enable o day)</a>
            </div>
        </form>
        <p class="hint" style="margin-top:12px;">
            Phai <strong>mo phien console</strong> cho cong do truoc (Tong quan &rarr; Mo Console)
            va thiet bi da dang nhap xong, dang o dau nhac lenh. Cong doan chup mat tu vai
            giay den vai phut tuy do dai cau hinh va toc do baud.
        </p>
    </div>

    <h3>Ban da luu ({{ ban_luu|length }})</h3>
    <p class="hint">Luu tai <code>{{ backup_dir }}</code>, quyen 600 (chi root doc) - khong
       nam trong thu muc TFTP nen thiet bi khac cam vao eth0 khong tai ve duoc.</p>
    <table>
        <tr><th>Ten file</th><th style="width:110px;">Kich thuoc</th>
            <th style="width:150px;">Thoi gian</th><th style="width:210px;">Thao tac</th></tr>
        {% for f in ban_luu %}
        <tr>
            <td>{{ f.ten }}</td>
            <td>{{ (f.kich_thuoc / 1024) | round(1) }} KB</td>
            <td class="hint">{{ f.thoi_gian }}</td>
            <td style="white-space:nowrap;">
                <a class="nut-tai" href="/nettools/console-backup/tai/{{ f.ten | urlencode }}" download>⬇ Tai ve</a>
                <form method="POST" action="/nettools/console-backup/xoa" style="display:inline;"
                      onsubmit="return confirm('Xoa {{ f.ten }}?');">
                    <input type="hidden" name="ten" value="{{ f.ten }}">
                    <button type="submit" class="red">Xoa</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
    {% if not ban_luu %}<p class="hint">Chua co ban luu nao.</p>{% endif %}
    {% endif %}

    <h3>Cac cach khac de backup khi khong co mang</h3>
    <div class="khoi" style="border-left-color:#3b82f6;">
        <p style="margin:0 0 9px;"><strong>USB cam thang vao switch</strong> - nhanh nhat
        NEU thiet bi co cong USB va ho tro:</p>
        <pre>copy running-config usbflash0:backup.cfg</pre>
        <p class="hint" style="margin:0 0 11px;">Rat nhieu thiet bi khong co cong USB
        (2960 doi cu, switch nho, nhieu hang khac) - luc do dung cach chup qua console
        o tren, chay duoc voi moi thiet bi co cong console.</p>
        <p style="margin:0 0 9px;"><strong>Khong the</strong> hut file qua cap console
        bang USB cam o Pi: cong console chi truyen KY TU, khong phai duong truyen file -
        khong co giao thuc san co nao tren switch de day file nhi phan qua duong do.</p>
    </div>
</body>
</html>
"""


def _render(msg="", ok=True, dev_chon=""):
    cong = danh_sach_cong()
    if not dev_chon and cong:
        dev_chon = cong[0]["dev"]
    return render_template_string(
        TEMPLATE, msg=msg, ok=ok, cong=cong, ho_thiet_bi=HO_THIET_BI,
        ban_luu=danh_sach_ban_luu(), backup_dir=BACKUP_DIR, dev_chon=dev_chon,
    )


@nettools_bp.route("/nettools/console-backup")
def console_backup_route():
    # ?dev=ttyUSB0 - toi tu trang Console (nut "Sao luu cau hinh") de chon
    # san dung cong dang mo, khong bat go lai.
    return _render(dev_chon=request.args.get("dev", ""))


@nettools_bp.route("/nettools/console-backup/chup", methods=["POST"])
def console_backup_chup_route():
    dev = request.form.get("dev", "")
    ok, msg, _ten = chup_cau_hinh(dev, request.form.get("ho", "cisco"),
                                  request.form.get("ten_file", ""))
    return _render(msg=msg, ok=ok, dev_chon=dev)


@nettools_bp.route("/nettools/console-backup/xoa", methods=["POST"])
def console_backup_xoa_route():
    ok, msg = xoa_ban_luu(request.form.get("ten", ""))
    return _render(msg=msg, ok=ok)


@nettools_bp.route("/nettools/console-backup/tai/<path:ten>")
def console_backup_tai_route(ten):
    duong = duong_dan_an_toan(ten)
    if not duong:
        abort(404)
    return send_from_directory(BACKUP_DIR, os.path.basename(duong), as_attachment=True)


if __name__ == "__main__":
    print("Cong console:", danh_sach_cong())
    print("Ban da luu:", danh_sach_ban_luu())
