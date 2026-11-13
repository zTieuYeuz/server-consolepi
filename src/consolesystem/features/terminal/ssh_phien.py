# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Terminal SSH NHIEU NGUOI (2.0.7 cum 2): moi nguoi dung mot phien tmux RIENG, moi may dich chi mot nguoi DIEU KHIEN (khoa tu het han),
nguoi vao sau chi XEM (tmux attach -r) va co nut "xin dieu khien". Truoc day ca Console dung chung MOT phien tmux "consolepi-ssh":
hai nguoi gui lenh vao cung man hinh, mat khau go cho nguoi nay hien cho nguoi kia.

Du lieu (ssh-phien.json, quyen 600): phien: {ma: {chu, tmux, chi_xem}} - `ma` la chuoi NGAU NHIEN (16 hex) chi chu phien biet (nam trong URL
iframe) nen khong ai doan ra de gan vao phien nguoi khac; khoa: {may: {chu, luc, xin, xin_luc}}. scripts/ssh-phien-tra.py doc file nay cho phien-mo.sh.
Moi ham nhan `gio` de test, khong goi tmux (viec tmux nam o ssh.py / phien-mo.sh).
"""
import json
import os
import re
import secrets
import threading
import time

from ui.duongdan import THU_MUC_DU_LIEU

FILE = os.path.join(THU_MUC_DU_LIEU, "ssh-phien.json")
HAN_KHOA = 180            # giay khong hoat dong thi khoa tu het han (mat ket noi / bo di)
HAN_XIN = 90              # giay cho chu phien nhuong sau khi co nguoi xin
TOI_DA_PHIEN = 4          # so nguoi dung SSH dong thoi (Pi yeu)
_KHOA = threading.Lock()


def _doc():
    try:
        with open(FILE, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            d.setdefault("phien", {})
            d.setdefault("khoa", {})
            return d
    except (OSError, ValueError):
        pass
    return {"phien": {}, "khoa": {}}


def _ghi(d):
    from consolesystem.core.store import ghi_json
    ghi_json(FILE, d, mode=0o600)


def _an_toan(nguoi):
    return re.sub(r"[^a-z0-9]", "", (nguoi or "khach").lower())[:24] or "khach"


def _nhat_ky(viec, chi_tiet, nguoi):
    try:
        from ui.errlog import ghi_thao_tac
        ghi_thao_tac(viec, chi_tiet, nguoi=nguoi)
    except Exception as e:                  # nhat ky la phu: khong duoc lam hong viec chinh
        print("[ssh-phien] khong ghi duoc nhat ky: %s" % type(e).__name__, flush=True)


def phien_cua(nguoi, gio=time.time, dang_chay=lambda t: True):
    """(ma, ten_tmux) phien RIENG cua nguoi nay (tao neu chua co). Loi ValueError neu da du TOI_DA_PHIEN nguoi khac dang dung.
    dang_chay(ten_tmux) -> phien tmux con song khong (de don phien da chet khoi han muc)."""
    an = _an_toan(nguoi)
    with _KHOA:
        d = _doc()
        for ma, p in d["phien"].items():
            if p["chu"] == nguoi and not p.get("chi_xem"):
                return ma, p["tmux"]
        song = {p["chu"] for p in d["phien"].values() if not p.get("chi_xem") and dang_chay(p["tmux"])}
        if len(song) >= TOI_DA_PHIEN:
            raise ValueError("Đã có %d người dùng terminal SSH cùng lúc (tối đa %d, Pi yếu). Thử lại sau." % (len(song), TOI_DA_PHIEN))
        ma, ten = secrets.token_hex(8), "ssh-" + an
        d["phien"] = {k: v for k, v in d["phien"].items() if v["chu"] != nguoi}
        d["phien"]["ssh-" + ma] = {"chu": nguoi, "tmux": ten, "chi_xem": False}
        _ghi(d)
        return "ssh-" + ma, ten


HAN_MA_XEM = 600          # ma xem terminal nguoi khac song 10 phut (NV8-04)


def ma_xem(chu, nguoi_xem="", gio=time.time, dang_chay=lambda t: True):
    """Ma (ngau nhien, NGAN HAN, gan voi nguoi xem) de XEM phien cua `chu` o che do chi doc; None neu chu khong co phien dang chay.
    Moi lan xin cap ma moi va thu hoi ma cu cua cung cap (chu, nguoi_xem); co ghi nhat ky 'A xem terminal cua B'."""
    now = gio()
    with _KHOA:
        d = _doc()
        goc = next((p for p in d["phien"].values() if p["chu"] == chu and not p.get("chi_xem")), None)
        if not goc or not dang_chay(goc["tmux"]):
            return None
        d["phien"] = {k: v for k, v in d["phien"].items()
                      if not (v.get("chi_xem") and (v.get("het", 0) < now or (v["chu"] == chu and v.get("cho") == nguoi_xem)))}
        ma = "xem-" + secrets.token_hex(8)
        d["phien"][ma] = {"chu": chu, "tmux": goc["tmux"], "chi_xem": True, "cho": nguoi_xem, "het": now + HAN_MA_XEM}
        _ghi(d)
    _nhat_ky("Terminal SSH: %s xem terminal của %s (chỉ đọc)" % (nguoi_xem or "?", chu), "", nguoi_xem or "-")
    return ma


def chuan_may(may):
    """Dua ve dang chuan 'host:cong' de khoa khong bi lach: chu thuong, bo user@, localhost/::1/127.x -> 127.0.0.1, thieu cong -> 22.
    Chua phan giai ten mien sang IP (hai ten khac nhau cung tro mot may van la hai khoa)."""
    may = (may or "").strip().lower()
    if "@" in may:
        may = may.rsplit("@", 1)[1]
    host, _, cong = may.rpartition(":") if ":" in may and may.count(":") == 1 else (may, "", "")
    if not host:
        host, cong = may, ""
    host = host.strip("[]")
    if host in ("localhost", "::1", "0.0.0.0") or host.startswith("127."):
        host = "127.0.0.1"
    return "%s:%s" % (host, cong or "22")


def lay_khoa(may, nguoi, gio=time.time):
    """Xin/giu quyen DIEU KHIEN may dich. Tra ("dieu_khien", nguoi) hoac ("chi_xem", chu_dang_giu). Goi lai de gia han (nhip)."""
    may = chuan_may(may)
    now = gio()
    with _KHOA:
        d = _doc()
        k = d["khoa"].get(may)
        if not k or k["chu"] == nguoi or now - k["luc"] > HAN_KHOA:
            if not k or k["chu"] != nguoi:
                _nhat_ky("Terminal SSH: nhận quyền điều khiển máy " + may, "", nguoi)
            d["khoa"][may] = {"chu": nguoi, "luc": now}
            _ghi(d)
            return "dieu_khien", nguoi
        return "chi_xem", k["chu"]


def xin(may, nguoi, gio=time.time):
    """Nguoi dang chi xem xin dieu khien: ghi yeu cau; neu chu da bo di (het han) thi nhan luon. Tra (da_nhan, thong_diep)."""
    may = chuan_may(may)
    now = gio()
    with _KHOA:
        d = _doc()
        k = d["khoa"].get(may)
        if not k or now - k["luc"] > HAN_KHOA or k["chu"] == nguoi:
            d["khoa"][may] = {"chu": nguoi, "luc": now}
            _ghi(d)
            _nhat_ky("Terminal SSH: nhận quyền điều khiển máy " + may, "", nguoi)
            return True, "Bạn đang điều khiển máy này."
        k["xin"], k["xin_luc"] = nguoi, now
        _ghi(d)
        _nhat_ky("Terminal SSH: xin điều khiển máy " + may, "đang do " + k["chu"], nguoi)
        return False, "Đã gửi yêu cầu cho %s (chờ tối đa %d giây)." % (k["chu"], HAN_XIN)


def nhuong(may, chu, gio=time.time):
    """Chu dang dieu khien dong y nhuong cho nguoi dang xin. Tra (ok, thong_diep)."""
    may = chuan_may(may)
    now = gio()
    with _KHOA:
        d = _doc()
        k = d["khoa"].get(may)
        if not k or k["chu"] != chu or not k.get("xin") or now - k.get("xin_luc", 0) > HAN_XIN:
            return False, "Không có yêu cầu nào đang chờ."
        moi = k["xin"]
        d["khoa"][may] = {"chu": moi, "luc": now}
        _ghi(d)
    _nhat_ky("Terminal SSH: %s nhường điều khiển máy %s cho %s" % (chu, may, moi), "", chu)
    return True, "Đã nhường điều khiển cho %s." % moi


def tha(may, nguoi):
    may = chuan_may(may)
    with _KHOA:
        d = _doc()
        if d["khoa"].get(may, {}).get("chu") == nguoi:
            d["khoa"].pop(may)
            _ghi(d)
            _nhat_ky("Terminal SSH: thôi điều khiển máy " + may, "", nguoi)
            return True
    return False


def trang_thai(nguoi, gio=time.time):
    """Cho giao dien: cac may dang co nguoi dieu khien + yeu cau xin dang cho toi."""
    now = gio()
    with _KHOA:
        d = _doc()
    ra = []
    for may, k in d["khoa"].items():
        if now - k["luc"] > HAN_KHOA:
            continue
        xin_toi = bool(k.get("xin")) and now - k.get("xin_luc", 0) <= HAN_XIN
        ra.append({"may": may, "chu": k["chu"], "cua_toi": k["chu"] == nguoi, "xin": k.get("xin") if xin_toi else "", "luc": int(now - k["luc"])})
    return ra
