# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console System - PHIEN KET NOI kieu MobaXterm (27/09/2026, anh Thoai: "lam lai
phan console ssh de nguoi ta de cau hinh hon, giong MobaXterm").

Truoc day Console, SSH, Terminal la 3 trang rieng, moi trang 1 khung, SSH chi
mo duoc 1 thiet bi 1 luc va phai go lai IP moi lan. Nay 1 trang duy nhat:
  - Danh sach PHIEN DA LUU (ten, nhom, SSH/Telnet/Serial) + cong console tu
    nhan + terminal cua may - bam 1 cai la mo.
  - Nhieu TAB cung luc; dong tab / tai lai trang khong mat phien (tmux).
  - Ket noi nhanh: go "ssh admin@10.0.0.1", "telnet 10.0.0.1", "ttyUSB0".
  - Moi tab: gui tap lenh (thu vien lenh, dan tung dong an toan), go mat
    khau giup, luu log man hinh, ngat phien, mo toan man hinh.
  - Rot ket noi -> Enter de ket noi lai (xem scripts/phien-chay.py).

Terminal that su: ttyd console-pi-term-phien (cong 8012, sau nginx
/term-phien/?arg=<ma>) chay scripts/phien-mo.sh -> tmux.

BAO MAT:
  - host/user loc giong ssh.py (ky tu dau phai la chu/so - chan chen co lenh
    kieu "-oProxyCommand=..."), chay bang danh sach doi so, khong qua shell.
  - Mat khau luu CHI KHI nguoi dung tich "Luu mat khau": file phien.json quyen
    600 (chi root doc duoc), khong bao gio tra ve trinh duyet (API chi tra co
    "co_mat_khau"). Go mat khau = tmux send-keys -l khi thay dau nhac.
"""
from consolesystem.core import taisan as _taisan
import sys as _sys
_sys.modules["ui.phien"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import json
import os
import re
import secrets
import subprocess
import time

from flask import Response, jsonify, request

from ui.duongdan import THU_MUC_DU_LIEU
from ui.layout import render_page

FILE_PHIEN = os.path.join(THU_MUC_DU_LIEU, "phien.json")
MAU_HOST = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:\-]{0,254}")
MAU_USER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._\-\\]{0,63}")
MAU_MA = re.compile(r"[a-z0-9][a-zA-Z0-9-]{0,47}")   # chu hoa: serial-ttyUSB0
BAUD = (1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200)
_DAU_NHAC_MK = re.compile(r"(password|passphrase|mat khau|mật khẩu)[^:]*:\s*$", re.I)


# ------------------------------------------------------------------ du lieu
def _doc():
    try:
        with open(FILE_PHIEN, encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d.get("phien"), list):
                return d
    except (OSError, ValueError):
        pass
    return {"phien": []}


def _ghi(d):
    os.makedirs(THU_MUC_DU_LIEU, exist_ok=True)
    tam = FILE_PHIEN + ".tmp"
    old = os.umask(0o077)
    try:
        with open(tam, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tam, FILE_PHIEN)
    finally:
        os.umask(old)


def _cong_serial():
    """Cac cong console dang cam + ten goi nho (neu da dat)."""
    try:
        from ui.home import load_names
        ten = load_names() or {}
    except Exception:
        ten = {}
    ra = []
    for n in sorted(os.listdir("/dev")):
        if re.fullmatch(r"tty(USB|ACM)\d+", n):
            ra.append({"ma": f"serial-{n}", "loai": "serial", "cong": n,
                       "ten": ten.get(n) or f"Cổng console {n}"})
    return ra


def ten_tmux(ma):
    if ma == "local":
        return "consolepi-local"
    if ma.startswith("serial-"):
        return "console-" + ma[len("serial-"):]
    return "phien-" + ma


def _cong_khai(p):
    """Ban an toan de gui ra trinh duyet - KHONG kem mat khau."""
    d = {k: p.get(k, "") for k in ("ma", "ten", "loai", "host", "port", "user", "cong",
                                   "baud", "nhom", "ghi_chu")}
    d["co_mat_khau"] = bool(p.get("mat_khau"))
    return d


def kiem_tra(f):
    """Chuan hoa + kiem tra 1 phien tu form. Tra (loi, phien)."""
    loai = f.get("loai", "ssh")
    if loai not in ("ssh", "telnet", "serial"):
        return "Loại phiên không hợp lệ.", None
    p = {"loai": loai, "ten": (f.get("ten") or "").strip()[:60],
         "nhom": _chuan_nhom(f.get("nhom")), "ghi_chu": (f.get("ghi_chu") or "").strip()[:200]}
    if loai in ("ssh", "telnet"):
        host = (f.get("host") or "").strip()
        if not MAU_HOST.fullmatch(host):
            return "Địa chỉ không hợp lệ (bắt đầu bằng chữ/số; chỉ gồm chữ, số, . - _ :).", None
        try:
            cong = int(f.get("port") or (22 if loai == "ssh" else 23))
        except ValueError:
            return "Cổng phải là số.", None
        if not 1 <= cong <= 65535:
            return "Cổng phải trong khoảng 1-65535.", None
        user = (f.get("user") or "").strip()
        if loai == "ssh" and user and not MAU_USER.fullmatch(user):
            return "Tên đăng nhập không hợp lệ.", None
        p.update(host=host, port=cong, user=user if loai == "ssh" else "")
        p["ten"] = p["ten"] or (f"{user}@{host}" if user else host)
    else:
        cong = (f.get("cong") or "").strip()
        if not re.fullmatch(r"tty(USB|ACM)\d+", cong):
            return "Chọn cổng console (ttyUSB0...).", None
        try:
            baud = int(f.get("baud") or 9600)
        except ValueError:
            baud = 9600
        if baud not in BAUD:
            return "Tốc độ baud không hợp lệ.", None
        p.update(cong=cong, baud=baud)
        p["ten"] = p["ten"] or cong
    return None, p


def luu(f):
    loi, p = kiem_tra(f)
    if loi:
        return False, loi, None
    d = _doc()
    ma = (f.get("ma") or "").strip()
    cu = next((x for x in d["phien"] if x.get("ma") == ma), None) if ma else None
    if cu:
        mk = cu.get("mat_khau", "")
        cu.clear(); cu.update(p); cu["ma"] = ma
    else:
        import unicodedata
        khong_dau = unicodedata.normalize("NFD", p["ten"].replace("đ", "d").replace("Đ", "D"))
        khong_dau = "".join(c for c in khong_dau if unicodedata.category(c) != "Mn")
        goc = re.sub(r"[^a-z0-9]+", "-", khong_dau.lower()).strip("-")[:30] or p["loai"]
        ma = f"{goc}-{secrets.token_hex(2)}"
        mk = ""
        cu = dict(p, ma=ma, tao_luc=time.time())
        d["phien"].append(cu)
    # Mat khau: o trong = giu nguyen; tich "xoa" = bo
    if f.get("xoa_mat_khau"):
        mk = ""
    elif f.get("mat_khau") and f.get("luu_mat_khau"):
        mk = f.get("mat_khau")[:200]
    if mk and cu["loai"] != "serial":
        cu["mat_khau"] = mk
    cu.pop("tam", None)
    if cu.get("nhom"):
        d["nhom_ds"] = _nhom_ds(d)
    _ghi(d)
    return True, "Đã lưu phiên.", ma


# ---- NHOM PHIEN (19/10/2026, anh Thoai: "tao nhom truoc, luc tao phien thi xo xuong cac nhom de chon")
# Danh sach nhom da tao luu trong phien.json (khoa "nhom_ds") - nhom van ton tai khi chua co phien nao.
# Phien chi luu TEN nhom (p["nhom"]); doi ten / xoa nhom cap nhat luon cac phien thuoc nhom do.
NHOM_HE_THONG = {"máy này", "cổng console (tự nhận)", "đã lưu", "kết nối nhanh gần đây"}


def _chuan_nhom(ten):
    ten = re.sub(r"\s+", " ", (ten or "").strip())[:40]
    return "" if re.search(r"[\x00-\x1f<>]", ten) else ten


def _nhom_ds(d):
    """Cac nhom da tao + cac nhom dang duoc phien dung (phien cu tu go tay), khong trung hoa/thuong."""
    ra, thay = [], set()
    for n in list(d.get("nhom_ds") or []) + [p.get("nhom") for p in d["phien"] if p.get("nhom")]:
        n = _chuan_nhom(n)
        if n and n.lower() not in thay:
            thay.add(n.lower()); ra.append(n)
    return sorted(ra, key=str.lower)


def nhom_tao(ten):
    ten = _chuan_nhom(ten)
    if not ten:
        return False, "Hãy đặt tên nhóm (tối đa 40 ký tự, không dùng < >).", None
    if ten.lower() in NHOM_HE_THONG:
        return False, f"Tên \"{ten}\" là tên nhóm của hệ thống, hãy chọn tên khác.", None
    d = _doc()
    co = next((n for n in _nhom_ds(d) if n.lower() == ten.lower()), None)
    if co:
        return True, f"Nhóm \"{co}\" đã có.", co
    d["nhom_ds"] = _nhom_ds(d) + [ten]
    _ghi(d)
    return True, f"Đã tạo nhóm \"{ten}\".", ten


def nhom_doi_ten(cu, moi):
    cu, moi = _chuan_nhom(cu), _chuan_nhom(moi)
    if not moi:
        return False, "Hãy đặt tên nhóm mới."
    if moi.lower() in NHOM_HE_THONG:
        return False, f"Tên \"{moi}\" là tên nhóm của hệ thống, hãy chọn tên khác."
    d = _doc()
    ds = _nhom_ds(d)
    goc = next((n for n in ds if n.lower() == cu.lower()), None)
    if not goc:
        return False, "Không tìm thấy nhóm."
    if moi.lower() != goc.lower() and any(n.lower() == moi.lower() for n in ds):
        return False, f"Đã có nhóm \"{moi}\"."
    d["nhom_ds"] = [moi if n == goc else n for n in ds]
    for p in d["phien"]:
        if (p.get("nhom") or "") == goc:
            p["nhom"] = moi
    _ghi(d)
    return True, f"Đã đổi tên nhóm thành \"{moi}\"."


def nhom_xoa(ten):
    """Xoa nhom: cac phien trong nhom KHONG bi xoa, chi chuyen ve "Da luu" (khong nhom)."""
    ten = _chuan_nhom(ten)
    d = _doc()
    ds = _nhom_ds(d)
    goc = next((n for n in ds if n.lower() == ten.lower()), None)
    if not goc:
        return False, "Không tìm thấy nhóm.", 0
    d["nhom_ds"] = [n for n in ds if n != goc]
    dem = 0
    for p in d["phien"]:
        if (p.get("nhom") or "") == goc:
            p["nhom"] = ""
            dem += 1
    _ghi(d)
    return True, f"Đã xoá nhóm \"{goc}\"." + (f" {dem} phiên được chuyển về \"Đã lưu\"." if dem else ""), dem


def xoa(ma):
    d = _doc()
    d["phien"] = [x for x in d["phien"] if x.get("ma") != ma]
    _ghi(d)
    ngat(ma)


def ngat(ma):
    # Ke ca "Terminal may nay" (19/10/2026, anh Thoai: tat phien roi mo lai van ra man hinh cu): truoc day
    # khong bao gio kill phien "local" nen mo lai luon ra dung noi dung cu. Phien tmux tu tao lai khi mo.
    subprocess.run(["tmux", "kill-session", "-t", ten_tmux(ma)], capture_output=True, timeout=5)


def ket_noi_nhanh(chuoi):
    """
    "ssh admin@10.0.0.1[:2222]", "admin@10.0.0.1", "10.0.0.1" (ssh),
    "telnet 10.0.0.1[:23]", "ttyUSB0". Tao phien TAM (khong hien trong danh
    sach da luu, tu don sau 1 ngay). Tra (ok, thong_bao, ma).
    """
    s = (chuoi or "").strip()
    m = re.fullmatch(r"(tty(?:USB|ACM)\d+)", s)
    if m:
        return True, "", f"serial-{m.group(1)}"
    loai = "ssh"
    m = re.fullmatch(r"(ssh|telnet)\s+(.+)", s, re.I)
    if m:
        loai, s = m.group(1).lower(), m.group(2).strip()
    user, _, host = s.rpartition("@")
    port = ""
    if ":" in host and host.count(":") == 1:
        host, port = host.split(":")
    loi, p = kiem_tra({"loai": loai, "host": host, "user": user, "port": port})
    if loi:
        return False, loi, None
    d = _doc()
    gio = time.time()
    d["phien"] = [x for x in d["phien"] if not (x.get("tam") and gio - x.get("tao_luc", 0) > 86400)]
    for x in d["phien"]:
        if x.get("tam") and all(x.get(k) == p.get(k) for k in ("loai", "host", "port", "user")):
            _ghi(d)
            return True, "", x["ma"]
    ma = "nhanh-" + secrets.token_hex(3)
    d["phien"].append(dict(p, ma=ma, tam=True, tao_luc=gio))
    _ghi(d)
    return True, "", ma


def _man_hinh(tmux):
    r = subprocess.run(["tmux", "capture-pane", "-p", "-t", tmux], capture_output=True, text=True, timeout=5)
    return r.stdout if r.returncode == 0 else ""


def go_mat_khau(ma, mk=None, cho_giay=15):
    """Doi dau nhac mat khau roi go (mk nguoi dung vua nhap, hoac mk da luu)."""
    if mk is None:
        p = next((x for x in _doc()["phien"] if x.get("ma") == ma), None)
        mk = (p or {}).get("mat_khau", "")
    if not mk:
        return False, "Phiên này chưa lưu mật khẩu."
    tmux = ten_tmux(ma)
    het = time.time() + cho_giay
    while time.time() < het:
        dong = [l.rstrip() for l in _man_hinh(tmux).splitlines() if l.strip()]
        if dong and _DAU_NHAC_MK.search(dong[-1]):
            subprocess.run(["tmux", "send-keys", "-t", tmux, "-l", mk], capture_output=True, timeout=5)
            subprocess.run(["tmux", "send-keys", "-t", tmux, "Enter"], capture_output=True, timeout=5)
            return True, "Đã gõ mật khẩu."
        time.sleep(0.4)
    return False, "Không thấy dấu nhắc mật khẩu trên màn hình phiên này."


# ------------------------------------------------------------------ giao dien
TRANG = _taisan.doc("features/terminal/phien.TRANG.html")


JS = _taisan.doc("features/terminal/phien.JS.html")


CSS_GON = """
.main>.status{display:none;}
/* Che do cam ung: chua cho thanh duoi (~90px) de khong che dong lenh cuoi */
body.cd-cu .content{padding-bottom:96px !important;}
body.cd-cu .ph-khung{height:calc(100vh - 168px);}
.content{padding:10px 12px 10px;max-width:none;}
.content>h1,.content>.sub{display:none;}
"""


def _icon_hoa(html):
    """Thay [[i:ten]] / [[i:ten:lop]] trong TRANG bang icon SVG cua khung chung."""
    from ui.layout import svg_icon
    from ui.ph_icons import ph_icon
    html = re.sub(r"\[\[p:([a-z-]+)\]\]", lambda m: ph_icon(m.group(1)), html)
    return re.sub(r"\[\[i:([a-z]+)(?::([a-z]+))?\]\]",
                  lambda m: svg_icon(m.group(1), ("i " + m.group(2)) if m.group(2) else "i"), html)


def register_phien(app):
    @app.route("/phien")
    def phien_trang():
        # Trang terminal: bo thanh trang thai + tieu de lon cua khung chung de
        # khung terminal duoc cao toi da (yeu cau 27/09/2026 - phan tren chiem
        # gan 1/3 man hinh cam ung). Tieu de thu nho nam cung hang Ket noi nhanh.
        return render_page(_icon_hoa(TRANG) + JS, active="/phien", title="Phiên kết nối", extra_css=CSS_GON)

    @app.route("/phien/api/ds")
    def phien_api_ds():
        ds = [dict(p, nhom_hien="Cổng console (tự nhận)") for p in _cong_serial()]
        ds.append({"ma": "local", "loai": "local", "ten": "Terminal máy này", "nhom_hien": "Máy này"})
        luu_ds = [x for x in _doc()["phien"] if not x.get("tam")]
        luu_ds.sort(key=lambda x: ((x.get("nhom") or "~").lower(), x.get("ten", "").lower()))
        for p in luu_ds:
            d = _cong_khai(p)
            d["sua"] = True
            if p.get("loai") == "serial":
                # Dung chung phien cua cong (1 cong serial chi 1 chuong trinh giu)
                d["mo_ma"] = "serial-" + p.get("cong", "")
            d["nhom_hien"] = p.get("nhom") or "Đã lưu"
            ds.append(d)
        for p in _doc()["phien"]:
            if p.get("tam"):
                ds.append(dict(_cong_khai(p), nhom_hien="Kết nối nhanh gần đây"))
        d_doc = _doc()
        nhom = _nhom_ds(d_doc)
        dem = {n: sum(1 for p in luu_ds if (p.get("nhom") or "") == n) for n in nhom}
        return jsonify({"phien": ds, "nhom": nhom, "nhom_dem": dem})

    @app.route("/phien/api/nhom/tao", methods=["POST"])
    def phien_api_nhom_tao():
        ok, msg, ten = nhom_tao((request.get_json(silent=True) or {}).get("ten", ""))
        return jsonify({"ok": ok, "loi": "" if ok else msg, "msg": msg, "ten": ten})

    @app.route("/phien/api/nhom/doi-ten", methods=["POST"])
    def phien_api_nhom_doi_ten():
        j = request.get_json(silent=True) or {}
        ok, msg = nhom_doi_ten(j.get("cu", ""), j.get("moi", ""))
        return jsonify({"ok": ok, "loi": "" if ok else msg, "msg": msg})

    @app.route("/phien/api/nhom/xoa", methods=["POST"])
    def phien_api_nhom_xoa():
        ok, msg, dem = nhom_xoa((request.get_json(silent=True) or {}).get("ten", ""))
        return jsonify({"ok": ok, "loi": "" if ok else msg, "msg": msg, "so_phien": dem})

    @app.route("/phien/api/luu", methods=["POST"])
    def phien_api_luu():
        ok, msg, ma = luu(request.get_json(silent=True) or {})
        return jsonify({"ok": ok, "loi": "" if ok else msg, "ma": ma})

    @app.route("/phien/api/xoa", methods=["POST"])
    def phien_api_xoa():
        ma = (request.get_json(silent=True) or {}).get("ma", "")
        if MAU_MA.fullmatch(ma or ""):
            xoa(ma)
        return jsonify({"ok": True})

    @app.route("/phien/api/nhanh", methods=["POST"])
    def phien_api_nhanh():
        ok, msg, ma = ket_noi_nhanh((request.get_json(silent=True) or {}).get("chuoi", ""))
        return jsonify({"ok": ok, "loi": msg, "ma": ma})

    @app.route("/phien/api/thu-vien")
    def phien_api_thu_vien():
        from ui.commands import load_library
        tap = []
        for t in load_library():
            lenh = t.get("commands", "")
            if isinstance(lenh, list):
                lenh = "\n".join(lenh)
            the = [x.strip() for x in str(t.get("tags", "")).split(",") if x.strip()]
            tap.append({"ten": t.get("name", ""), "mo_ta": t.get("desc", ""), "lenh": lenh, "the": the})
        return jsonify({"tap": tap})

    def _ma_hop_le(ma):
        return MAU_MA.fullmatch(ma or "") is not None

    @app.route("/phien/api/<ma>/mk", methods=["POST"])
    def phien_api_mk(ma):
        if not _ma_hop_le(ma):
            return jsonify({"ok": False, "loi": "Mã phiên không hợp lệ."}), 400
        mk = (request.get_json(silent=True) or {}).get("mat_khau")
        ok, msg = go_mat_khau(ma, mk if mk else None)
        return jsonify({"ok": ok, "loi": "" if ok else msg})

    @app.route("/phien/api/<ma>/dan", methods=["POST"])
    def phien_api_dan(ma):
        from ui.commands import dan_thong_minh
        if not _ma_hop_le(ma):
            return jsonify({"ok": False, "msg": "Mã phiên không hợp lệ."}), 400
        nd = (request.get_json(silent=True) or {}).get("noi_dung", "")
        if not nd.strip():
            return jsonify({"ok": False, "msg": "Chưa có nội dung."})
        ok, msg = dan_thong_minh(ten_tmux(ma), nd)
        return jsonify({"ok": ok, "msg": msg})

    @app.route("/phien/api/<ma>/baud", methods=["POST"])
    def phien_api_baud(ma):
        """Phien serial da luu co baud rieng: chay lai microcom cua cong do dung baud."""
        p = next((x for x in _doc()["phien"] if x.get("ma") == ma and x.get("loai") == "serial"), None)
        if not p:
            return jsonify({"ok": False})
        tmux, baud = "console-" + p["cong"], str(int(p.get("baud") or 9600))
        r = subprocess.run(["tmux", "show-options", "-v", "-t", tmux, "@baud"],
                           capture_output=True, text=True, timeout=5)
        dang = (r.stdout or "").strip() or "9600"
        if r.returncode == 0 and dang == baud:
            return jsonify({"ok": True})
        co = subprocess.run(["tmux", "has-session", "-t", tmux], capture_output=True, timeout=5).returncode == 0
        if co and dang != baud:
            subprocess.run(["tmux", "respawn-pane", "-k", "-t", tmux, "/usr/bin/microcom", "-s", baud,
                            "-p", "/dev/" + p["cong"]], capture_output=True, timeout=5)
        if co:
            subprocess.run(["tmux", "set-option", "-t", tmux, "@baud", baud], capture_output=True, timeout=5)
        return jsonify({"ok": True})

    @app.route("/phien/api/<ma>/ngat", methods=["POST"])
    def phien_api_ngat(ma):
        if _ma_hop_le(ma):
            ngat(ma)
        return jsonify({"ok": True})

    @app.route("/phien/api/<ma>/log")
    def phien_api_log(ma):
        if not _ma_hop_le(ma):
            return "Mã phiên không hợp lệ.", 400
        r = subprocess.run(["tmux", "capture-pane", "-p", "-J", "-S", "-", "-E", "-", "-t", ten_tmux(ma)],
                           capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            return "Phiên chưa mở hoặc đã đóng.", 404
        ten = f"log-{ma}-{time.strftime('%Y%m%d-%H%M')}.txt"
        return Response(r.stdout, mimetype="text/plain; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{ten}"'})

    return app
