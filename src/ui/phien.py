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
import json
import os
import re
import secrets
import subprocess
import time

from flask import Response, jsonify, request

from .duongdan import THU_MUC_DU_LIEU
from .layout import render_page

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
        from .home import load_names
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
         "nhom": (f.get("nhom") or "").strip()[:40], "ghi_chu": (f.get("ghi_chu") or "").strip()[:200]}
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
    _ghi(d)
    return True, "Đã lưu phiên.", ma


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
TRANG = r"""
<style>
.ph-modal [hidden],.ph-cong[hidden],.ph-trong[hidden],.ph-tv[hidden]{display:none !important;}
.ph-khung{display:flex;gap:12px;height:calc(100dvh - 84px);min-height:440px;}
.ph-trai,.ph-phai{background:var(--the);border:1px solid var(--vien);border-radius:var(--bo);overflow:hidden;}
.ph-trai{width:272px;flex:0 0 272px;display:flex;flex-direction:column;}
.ph-trai .dau{padding:10px;border-bottom:1px solid var(--vien);}
.ph-trai input{margin:0;max-width:none;}
.ph-ds{overflow:auto;flex:1;padding:6px 8px 10px;}
.ph-nhom{font-size:12px;font-weight:500;color:var(--chu-mo2);padding:14px 8px 5px;}
.ph-muc{display:flex;align-items:center;gap:10px;padding:8px;border-radius:8px;cursor:pointer;
  transition:background-color .15s;}
.ph-muc:hover{background:var(--the-noi);}
.ph-muc.mo{background:var(--nhan-mo);}
.ph-muc .ic{min-width:34px;height:26px;border-radius:6px;display:flex;align-items:center;justify-content:center;
  font:600 11px var(--mono);flex:none;background:var(--the-noi);color:var(--chu-mo);}
.ic.ssh{background:var(--nhan-mo);color:var(--nhan);} .ic.telnet{background:var(--vang-mo);color:var(--vang);}
.ic.serial{background:var(--xanh-mo);color:var(--xanh);} .ic.local{background:var(--the-noi);color:var(--chu);}
.ph-muc .chu{flex:1;min-width:0;} .ph-muc .chu b{display:block;font-size:14px;font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ph-muc .chu small{color:var(--chu-mo);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;}
.ph-muc .sua{opacity:0;border:none;background:none;color:var(--chu-mo);cursor:pointer;padding:4px;min-height:0;}
.ph-muc:hover .sua{opacity:1;}
.ph-phai{flex:1;min-width:0;display:flex;flex-direction:column;}
.ph-tabs{display:flex;gap:2px;padding:8px 8px 0;border-bottom:1px solid var(--vien);overflow-x:auto;}
.ph-tab{display:flex;align-items:center;gap:8px;padding:7px 10px;border-radius:8px 8px 0 0;
  cursor:pointer;white-space:nowrap;font-size:13.5px;color:var(--chu-mo);border:1px solid transparent;border-bottom:none;}
.ph-tab:hover{color:var(--chu);}
.ph-tab.on{background:var(--the-noi);border-color:var(--vien);color:var(--chu);font-weight:600;}
.ph-tab .x{border:none;background:none;color:var(--chu-mo);cursor:pointer;font-size:16px;line-height:1;padding:0 4px;min-height:0;min-width:0;}
.ph-cong{display:flex;gap:6px;flex-wrap:wrap;padding:8px 10px;border-bottom:1px solid var(--vien);align-items:center;}
.ph-cong button{padding:6px 9px;font-size:13px;min-height:36px;white-space:nowrap;gap:6px;}
.ph-cong button svg.i,.ph-cong button svg.ph{width:17px;height:17px;}
#nut-mau.on{background:var(--nhan-mo);color:var(--nhan);border-color:var(--nhan);}
#nut-tv.on{background:var(--nhan-mo);color:var(--nhan);border-color:var(--nhan);}
.ph-giua{flex:1;display:flex;min-height:0;}
.ph-than{flex:1;position:relative;background:var(--pre-nen);min-width:0;}
.ph-than iframe{position:absolute;inset:0;width:100%;height:100%;border:0;display:none;}
.ph-than iframe.on{display:block;}
.ph-trong{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;
  color:var(--chu-mo);text-align:center;padding:24px;gap:6px;}
.ph-trong h3{margin:10px 0 2px;font-size:20px;color:var(--chu);letter-spacing:-.02em;}
.ph-trong p{max-width:460px;margin:0;}
.ph-trong .bd{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;margin-top:14px;}
.ph-trong svg.to{width:44px;height:44px;color:var(--chu-mo2);}
.ph-nhanh{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center;}
.ph-nhanh input{flex:1;min-width:240px;max-width:none;margin:0;font-family:var(--mono);}
.ph-nhanh .tieude{font-weight:650;font-size:18px;letter-spacing:-.02em;margin-right:6px;white-space:nowrap;}

/* ---- Ngan thu vien lenh (truot ra ben phai khung terminal) ---- */
.ph-tv{width:340px;flex:0 0 340px;border-left:1px solid var(--vien);background:var(--the);display:flex;flex-direction:column;min-height:0;}
.ph-tv .tvd{display:flex;align-items:center;gap:8px;padding:12px 14px 6px;}
.ph-tv .tvd b{font-size:16px;font-weight:650;letter-spacing:-.01em;flex:1;}
.ph-tv .tvd a,.ph-tv .tvd button{font-size:13px;min-height:32px;padding:4px 10px;}
.ph-tv .tvt{padding:4px 14px 8px;}
.ph-tv .tvt input{max-width:none;margin:0;}
.ph-chip{display:flex;gap:6px;flex-wrap:wrap;padding:0 14px 8px;}
.ph-chip button{min-height:30px;padding:3px 11px;font-size:12.5px;border-radius:999px;background:transparent;
  color:var(--chu-mo);border:1px solid var(--vien-ro);font-weight:500;}
.ph-chip button.on{background:var(--nhan-mo);color:var(--nhan);border-color:var(--nhan);}
.ph-tvds{flex:1;overflow:auto;padding:0 8px 8px;min-height:90px;}
.ph-the{display:block;width:100%;text-align:left;background:transparent;color:var(--chu);border:1px solid transparent;
  border-radius:10px;padding:10px 12px;margin-bottom:2px;min-height:0;font-weight:400;}
.ph-the:hover{background:var(--the-noi);}
.ph-the.chon{background:var(--nhan-mo);border-color:var(--nhan);}
.ph-the b{display:block;font-size:14px;font-weight:600;}
.ph-the span{display:block;font-size:12.5px;color:var(--chu-mo);margin-top:2px;line-height:1.4;}
.ph-the small{display:block;font:11.5px var(--mono);color:var(--chu-mo2);margin-top:5px;}
.ph-sua{border-top:1px solid var(--vien);padding:12px 14px 14px;background:var(--nen-noi);max-height:58%;overflow:auto;}
.ph-sua h4{margin:0 0 8px;font-size:14px;}
.ph-sua label{margin:8px 0 4px;font-size:12.5px;}
.ph-sua input{max-width:none;min-height:36px;padding:6px 10px;font-size:14px;margin:0;}
.ph-sua textarea{width:100%;max-width:none;min-height:120px;font-size:13px;line-height:1.5;}
.ph-sua .nut{display:flex;gap:8px;margin-top:10px;align-items:center;flex-wrap:wrap;}
.ph-sua .nut button{white-space:nowrap;}
.ph-sua .kq{font-size:12.5px;color:var(--xanh);flex:1 1 100%;order:3;}
.ph-sua .kq.loi{color:var(--do);}
.ph-sua .hd{font-size:12px;color:var(--chu-mo2);margin:8px 0 0;line-height:1.45;}
.ph-modal{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:flex-start;justify-content:center;
  z-index:50;overflow:auto;padding:16px 0 300px;}
.ph-modal.on{display:flex;}
.ph-modal .hop{background:var(--the);border:1px solid var(--vien-ro);border-radius:var(--bo);padding:20px;width:min(520px,94vw);
  max-height:90vh;overflow:auto;}
.ph-modal label{display:block;font-size:13px;color:var(--chu-mo);margin:8px 0 3px;}
.ph-modal .hai{display:flex;gap:10px;} .ph-modal .hai>div{flex:1;}
.ph-loai{display:flex;gap:6px;} .ph-loai button{flex:1;}
.ph-loai button.chon{background:var(--nhan);color:var(--chu-tren-nhan);border-color:var(--nhan);font-weight:700;}
@media (max-width:900px){.ph-khung{flex-direction:column;height:auto;}.ph-trai{width:auto;flex:none;max-height:260px;}
  .ph-phai{height:80vh;}
  .ph-giua{position:relative;} .ph-tv{position:absolute;inset:0;width:auto;flex:none;z-index:5;border-left:0;}}
@media (prefers-reduced-motion:no-preference){
  .ph-tv.vao{animation:tv-vao .3s var(--muot) both;}
  @keyframes tv-vao{from{opacity:0;transform:translateX(24px);}to{opacity:1;transform:none;}}
}
</style>

<div class="ph-nhanh">
  <span class="tieude">Phiên kết nối</span>
  <input type="text" id="o-nhanh" placeholder="Kết nối nhanh: ssh admin@192.168.1.1" autocomplete="off">
  <button id="nut-nhanh" type="button">[[i:go]] Kết nối</button>
  <button id="nut-moi" type="button" class="gray">[[i:plus]] Phiên mới</button>
</div>

<div class="ph-khung">
  <div class="ph-trai">
    <div class="dau"><input id="o-loc" type="search" placeholder="Tìm phiên..." autocomplete="off"></div>
    <div class="ph-ds" id="ds"></div>
  </div>
  <div class="ph-phai">
    <div class="ph-tabs" id="tabs"></div>
    <div class="ph-cong" id="congcu" hidden>
      <button type="button" id="nut-tv" data-lam="tv" title="Mở thư viện lệnh làm sẵn, chọn rồi gửi vào phiên này">[[i:book]] Thư viện lệnh</button>
      <button type="button" id="nut-mau" data-lam="mau" class="gray" title="Tô màu chữ trên màn hình: dòng lỗi (đỏ), cảnh báo (vàng), trạng thái tốt (xanh), địa chỉ IP, MAC, tên cổng">[[p:paint-brush]] Tô màu</button>
      <button type="button" data-lam="mk" class="gray" title="Gõ mật khẩu giúp khi thiết bị hỏi">[[i:key]] Gõ mật khẩu</button>
      <button type="button" data-lam="log" class="gray" title="Tải toàn bộ nội dung màn hình về máy">[[i:save]] Lưu log</button>
      <button type="button" data-lam="full" class="gray">[[i:search]] Toàn màn hình</button>
      <button type="button" data-lam="ngat" class="gray" title="Kết thúc hẳn phiên (không chỉ đóng tab)">[[i:x]] Ngắt phiên</button>
      <span id="tt-tab" class="hint" style="margin-left:auto;flex:1 1 0;min-width:0;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"></span>
    </div>
    <div class="ph-giua">
      <div class="ph-than" id="than">
        <div class="ph-trong" id="trong">
          [[i:term:to]]
          <h3>Chưa mở phiên nào</h3>
          <p>Chọn một phiên ở danh sách bên trái, hoặc bắt đầu nhanh:</p>
          <div class="bd">
            <button type="button" id="bd-local">[[i:term]] Terminal máy này</button>
            <button type="button" id="bd-ssh" class="gray">[[i:key]] SSH / Telnet mới</button>
          </div>
          <p class="hint" style="margin-top:12px;">Hoặc gõ vào ô <b>Kết nối nhanh</b> phía trên, ví dụ <code>ssh admin@192.168.1.1</code>.</p>
        </div>
      </div>
      <aside class="ph-tv" id="tv" hidden aria-label="Thư viện lệnh">
        <div class="tvd"><b>Thư viện lệnh</b>
          <a class="btn gray small" href="/commands" target="_blank" rel="noopener" title="Thêm, sửa, xoá lệnh trong thư viện">Quản lý</a>
          <button type="button" class="gray small" id="tv-dong" aria-label="Đóng thư viện">[[i:x]]</button></div>
        <div class="tvt"><input type="search" id="tv-tim" placeholder="Tìm lệnh: vlan, cổng, ip..." autocomplete="off"></div>
        <div class="ph-chip" id="tv-chip"></div>
        <div class="ph-tvds" id="tv-ds"></div>
        <div class="ph-sua" id="tv-sua" hidden>
          <h4 id="tv-ten"></h4>
          <div id="tv-truong"></div>
          <label for="tv-nd">Lệnh sẽ gửi (sửa được trước khi gửi)</label>
          <textarea id="tv-nd" spellcheck="false"></textarea>
          <div class="nut"><button type="button" id="tv-gui">[[i:go]] Gửi vào phiên</button><span class="kq" id="tv-kq"></span></div>
          <p class="hd">Gửi từng dòng, đợi thiết bị in xong mới gửi dòng tiếp. Dòng cuối không tự bấm Enter để bạn kiểm tra lại.</p>
        </div>
      </aside>
    </div>
  </div>
</div>

<!-- Hop sua phien -->
<div class="ph-modal" id="md-phien"><div class="hop">
  <h3 style="margin:0 0 6px;" id="md-tieude">Phiên mới</h3>
  <input type="hidden" id="f-ma">
  <label>Loại kết nối</label>
  <div class="ph-loai" id="f-loai">
    <button type="button" data-v="ssh">SSH</button><button type="button" data-v="telnet">Telnet</button>
    <button type="button" data-v="serial">Serial (console)</button>
  </div>
  <div class="hai"><div><label>Tên gợi nhớ</label><input type="text" id="f-ten" placeholder="VD: Core switch tầng 3"></div>
    <div><label>Nhóm</label><input type="text" id="f-nhom" placeholder="VD: Chi nhánh HN" list="ds-nhom"></div></div>
  <datalist id="ds-nhom"></datalist>
  <div id="f-mang">
    <div class="hai"><div style="flex:3"><label>Địa chỉ IP / tên máy</label><input type="text" id="f-host" placeholder="192.168.1.1"></div>
      <div><label>Cổng</label><input type="text" id="f-port" placeholder="22"></div></div>
    <div id="f-ssh">
      <label>Tên đăng nhập</label><input type="text" id="f-user" placeholder="admin" autocapitalize="off">
      <label>Mật khẩu (tùy chọn)</label><input id="f-mk" type="password" placeholder="Để trống = hỏi khi kết nối" autocomplete="new-password">
      <label style="display:flex;gap:8px;align-items:center;"><input type="checkbox" id="f-luu-mk" style="width:auto;margin:0;">
        Lưu mật khẩu để tự gõ khi kết nối <span class="hint">(lưu trên máy này, chỉ quản trị đọc được)</span></label>
      <label style="display:flex;gap:8px;align-items:center;" id="f-xoa-mk-dong" hidden><input type="checkbox" id="f-xoa-mk" style="width:auto;margin:0;">
        Xoá mật khẩu đã lưu</label>
    </div>
  </div>
  <div id="f-serial" hidden>
    <div class="hai"><div><label>Cổng console</label><select id="f-cong"></select></div>
      <div><label>Tốc độ (baud)</label><select id="f-baud"></select></div></div>
    <p class="hint">Cisco, Juniper, HPE, Aruba thường là <b>9600</b>. Một số thiết bị mới dùng <b>115200</b>.</p>
  </div>
  <label>Ghi chú</label><input type="text" id="f-ghichu" placeholder="VD: vị trí tủ rack, người phụ trách...">
  <div id="f-loi" class="msg err" hidden style="margin-top:10px;"></div>
  <div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap;">
    <button type="button" id="f-luu-mo">Lưu & kết nối</button>
    <button type="button" id="f-luu" class="gray">Lưu</button>
    <button type="button" id="f-huy" class="gray">Huỷ</button>
    <button type="button" id="f-xoa" class="red" style="margin-left:auto;" hidden>Xoá phiên</button>
  </div>
</div></div>
"""


JS = r"""
<script>
(function(){
  var DS = [], MO = [], DANG = null, THU_VIEN = [];
  var $ = function(i){ return document.getElementById(i); };
  function esc(s){ var d=document.createElement('div'); d.textContent=s==null?'':String(s); return d.innerHTML; }
  function api(u, du){
    var o = du ? {method:'POST', headers:{'Content-Type':'application/json','X-Console-Pi':'fetch'},
                  body:JSON.stringify(du)} : {};
    return fetch(u, o).then(function(r){ return r.json(); });
  }
  function tenTmux(ma){ return ma==='local' ? 'consolepi-local' :
    (ma.indexOf('serial-')===0 ? 'console-'+ma.slice(7) : 'phien-'+ma); }
  var NHAN = {ssh:'SSH', telnet:'TEL', serial:'COM', local:'&gt;_'};
  function moTa(p){
    if (p.loai==='serial') return p.cong + (p.baud ? ' · '+p.baud : '');
    if (p.loai==='local') return 'Dòng lệnh của máy này';
    return (p.user ? p.user+'@' : '') + p.host + (p.port && String(p.port)!==(p.loai==='ssh'?'22':'23') ? ':'+p.port : '');
  }
  function veDs(){
    var q = ($('o-loc').value||'').toLowerCase(), h = '';
    var nhom = {};
    DS.forEach(function(p){ var g = p.nhom_hien || 'Đã lưu'; (nhom[g]=nhom[g]||[]).push(p); });
    Object.keys(nhom).forEach(function(g){
      var cac = nhom[g].filter(function(p){ return !q || (p.ten+' '+moTa(p)+' '+(p.nhom||'')+' '+(p.ghi_chu||'')).toLowerCase().indexOf(q)>=0; });
      if (!cac.length) return;
      h += '<div class="ph-nhom">'+esc(g)+'</div>';
      cac.forEach(function(p){
        var mo = MO.some(function(t){ return t.ma===p.ma; });
        h += '<div class="ph-muc'+(mo?' mo':'')+'" data-ma="'+esc(p.ma)+'" title="'+esc(p.ghi_chu||'')+'">'
          + '<span class="ic '+p.loai+'">'+NHAN[p.loai]+'</span><span class="chu"><b>'+esc(p.ten)+'</b><small>'
          + esc(moTa(p)) + (p.co_mat_khau?', đã lưu mật khẩu':'') + '</small></span>'
          + (p.sua ? '<button class="sua" data-sua="'+esc(p.ma)+'" title="Sửa">✎</button>' : '') + '</div>';
      });
    });
    $('ds').innerHTML = h || '<p class="hint" style="padding:12px;">Chưa có phiên nào.</p>';
  }
  function taiDs(){
    return api('/phien/api/ds').then(function(d){ DS = d.phien; veDs();
      $('ds-nhom').innerHTML = (d.nhom||[]).map(function(g){ return '<option value="'+esc(g)+'">'; }).join('');
    });
  }
  function luuTab(){ try{ localStorage.setItem('phien-tab', JSON.stringify({mo:MO, dang:DANG})); }catch(e){} }
  function veTabs(){
    $('tabs').innerHTML = MO.map(function(t){
      return '<div class="ph-tab'+(t.ma===DANG?' on':'')+'" data-tab="'+esc(t.ma)+'"><span class="ic '+t.loai+
        '" style="width:auto;height:auto;padding:1px 5px;border-radius:4px;font-size:10px;">'+NHAN[t.loai]+'</span>'
        + esc(t.ten) + '<button class="x" data-dong="'+esc(t.ma)+'" title="Đóng tab và tắt phiên">×</button></div>';
    }).join('');
    document.querySelectorAll('#than iframe').forEach(function(f){ f.classList.toggle('on', f.dataset.ma===DANG); });
    $('trong').hidden = MO.length > 0; $('congcu').hidden = !DANG;
    var t = MO.filter(function(x){ return x.ma===DANG; })[0];
    $('tt-tab').textContent = t ? moTa(t) : '';
    if (DANG) document.body.setAttribute('data-tmux-session', tenTmux(DANG));
    veDs(); luuTab();
  }
  function moTab(p, tuGoMk){
    if (p.mo_ma) {   // phien serial da luu -> mo phien cua cong, dat dung baud truoc
      var goc = p;
      api('/phien/api/'+encodeURIComponent(p.ma)+'/baud', {}).then(function(){
        moTab({ma:goc.mo_ma, ten:goc.ten, loai:'serial', cong:goc.cong, baud:goc.baud}, false); });
      return;
    }
    if (!MO.some(function(t){ return t.ma===p.ma; })) {
      MO.push({ma:p.ma, ten:p.ten, loai:p.loai, host:p.host, user:p.user, port:p.port, cong:p.cong, baud:p.baud});
      var f = document.createElement('iframe'); f.dataset.ma = p.ma;
      f.addEventListener('load', function(){ ganChuot(f); });
      f.src = '/term-phien/?arg=' + encodeURIComponent(p.ma); $('than').appendChild(f);
      if (tuGoMk && p.co_mat_khau) api('/phien/api/'+encodeURIComponent(p.ma)+'/mk', {});
    }
    DANG = p.ma; veTabs();
    var f2 = document.querySelector('#than iframe[data-ma="'+p.ma+'"]'); if (f2) setTimeout(function(){ try{f2.focus();}catch(e){} }, 300);
  }
  /* CHUOT TRONG TERMINAL (19/10/2026, anh Thoai: "boi den buong chuot la mat, chuot phai ra 2 bang,
     copy paste kho"). Nguyen nhan: terminal chay trong tmux voi `mouse on` (de banh xe cuon lich su)
     nen xterm.js nhuong het chuot cho tmux: keo chuot = tmux chon roi XOA ngay khi nha, chuot phai =
     menu cua tmux chong len menu cua trinh duyet. KHONG tat `mouse on` (se hong banh xe - xem
     ui/soanlenh.py). Thay vao do, tu khung cha (cung goc nen truy cap duoc iframe):
       - chuot trai keo = xterm.js tu boi den (nhu giu Shift): vet boi con nguyen, TU CHEP khi nha chuot
       - chuot phai   = chi con menu cua trinh duyet (Copy / Paste), khong gui cho tmux
       - banh xe, click thuong, phim bam van nhu cu */
  function chepChon(w, d){
    var t = ''; try{ t = w.term && w.term.getSelection(); }catch(e){}
    if (!t) return;
    /* Du phong (trang mo bang http thuong, trinh duyet khong cho navigator.clipboard): dung su kien "copy"
       de dat noi dung, KHONG tao o nhap tam - o nhap tam bi boi den se bat thanh cong cu cua trinh
       duyet (hinh cai keo "Cat" nhay len man hinh - anh Thoai bao 19/10/2026). */
    function du(){
      var xong = false;
      function dat(ev){ try{ ev.clipboardData.setData('text/plain', t); ev.preventDefault(); xong = true; }catch(e){} }
      try{ d.addEventListener('copy', dat, true); d.execCommand('copy'); }catch(e){}
      d.removeEventListener('copy', dat, true);
      if (!xong){   /* trinh duyet khong cho: o nhap CHI DOC (khong co nut Cat), chen vao roi go ngay */
        try{
          var ta = d.createElement('textarea'); ta.value = t; ta.readOnly = true;
          ta.style.cssText = 'position:fixed;opacity:0;left:-999px;top:0;width:1px;height:1px';
          d.body.appendChild(ta); ta.select(); d.execCommand('copy'); d.body.removeChild(ta);
        }catch(e){}
      }
      try{ if (w.term) w.term.focus(); }catch(e){}   /* tra lai tieu diem cho terminal de go tiep duoc */
    }
    try{ navigator.clipboard.writeText(t).catch(du); }catch(e){ du(); }
  }
  /* TO MAU CHU TRONG TERMINAL (19/10/2026, anh Thoai: "to mau dong loi, IP... nhu MobaXterm").
     Lam o PHIA TRINH DUYET bang "decoration" cua xterm.js (to mau len o chu co san, khong sua du lieu
     di qua): khong lam tre viec go phim, khong chen ma mau vao luong du lieu nen khong hong man hinh
     cua vim/less/htop. Chi to o chu dang mau mac dinh (thiet bi da tu to mau thi giu nguyen mau cua no). */
  var MAU_BAT = true; try{ MAU_BAT = localStorage.getItem('phien-mau') !== '0'; }catch(e){}
  var LUAT_MAU = [
    [/% (?:Invalid input|Incomplete command|Ambiguous command|Unknown command)|\b(?:errors?|err-disabled|failed|failure|fail|fatal|critical|denied|refused|invalid|unreachable|timed out|timeout|down|not found|no route|disconnected|rejected|violation|panic|exception|traceback)\b/gi, '#ff6b6b'],
    [/\b(?:warn(?:ing)?s?|notice|administratively down|deprecated|flapping|collisions?|duplex mismatch)\b/gi, '#ffd166'],
    [/\b(?:up|connected|established|success(?:ful(?:ly)?)?|forwarding|reachable|authenticated)\b/gi, '#7ddc7d'],
    [/\b(?:[0-9a-f]{4}\.){2}[0-9a-f]{4}\b|\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b/gi, '#d99bff'],
    [/\b(?:\d{1,3}\.){3}\d{1,3}(?:\/\d{1,2})?\b|\b(?:[0-9a-f]{1,4}:){3,7}[0-9a-f]{0,4}\b/gi, '#68d5d5'],
    [/\b(?:(?:Ten|Hundred|Forty|Twenty|)Gigabit[A-Za-z]*|FastEthernet|Ethernet|Serial|Loopback|Port-channel|Vlan|Tunnel|mgmt|Gi|Fa|Te|Eth|Po|Vl|Lo|Tw|Hu)\d+(?:\/\d+){0,3}(?:\.\d+)?\b/g, '#6cb6ff'],
    [/\b\d{1,2}:\d{2}:\d{2}(?:\.\d+)?\b/g, '#8a94a6']
  ];
  function ganMau(f){
    var w; try{ w = f.contentWindow; }catch(e){ return; }
    if (!w || w.__csMau) return;
    var lan = 0, doi = setInterval(function(){
      if (w.term && w.term.registerDecoration){ clearInterval(doi); khoiMau(w); }
      else if (++lan > 60) clearInterval(doi);
    }, 250);
  }
  function khoiMau(w){
    var T = w.term, muc = [], cho = null, st = {dem:0};
    w.__csMau = st;
    function xoaHet(){ muc.forEach(function(m){ m.ds.forEach(function(x){ try{ x.dispose(); }catch(e){} }); try{ m.mk.dispose(); }catch(e){} }); muc = []; }
    function chiaDong(dong, cols){      /* chuoi + bang anh xa vi tri ky tu -> cot; bo qua o co mau san */
      var s = '', cot = [], co = [], cell = null;
      for (var x = 0; x < cols; x++){
        cell = dong.getCell(x, cell); if (!cell) break;
        var rong = cell.getWidth(); if (rong === 0) continue;
        var ch = cell.getChars() || ' ';
        for (var k = 0; k < ch.length; k++){ cot.push(x); co.push(cell.getFgColorMode() !== 0); }
        s += ch;
      }
      return {s:s, cot:cot, co:co};
    }
    function ve(){
      cho = null;
      if (!MAU_BAT){ xoaHet(); return; }
      var b = T.buffer.active, cols = T.cols;
      var theoDong = {};
      muc = muc.filter(function(m){ if (m.mk.isDisposed){ return false; } theoDong[m.mk.line] = m; return true; });
      for (var r = 0; r < T.rows; r++){
        var abs = b.viewportY + r, dong = b.getLine(abs); if (!dong) continue;
        var ct = chiaDong(dong, cols), cu = theoDong[abs];
        if (cu && cu.sig === ct.s) continue;                       /* dong khong doi: giu nguyen */
        if (cu){ cu.ds.forEach(function(x){ try{ x.dispose(); }catch(e){} }); try{ cu.mk.dispose(); }catch(e){}
                 muc.splice(muc.indexOf(cu), 1); }
        if (!ct.s.trim()) continue;
        var mk = T.registerMarker(abs - (b.baseY + b.cursorY)); if (!mk) continue;
        var ds = [], da = {};
        LUAT_MAU.forEach(function(lt){
          lt[0].lastIndex = 0; var m;
          while ((m = lt[0].exec(ct.s))){
            if (!m[0]) { lt[0].lastIndex++; continue; }
            var a = m.index, z = m.index + m[0].length, tr = false;
            for (var i = a; i < z; i++){ if (da[i] || ct.co[i]) { tr = true; break; } }   /* trung luat truoc / da co mau */
            if (tr) continue;
            for (var i2 = a; i2 < z; i2++) da[i2] = 1;
            var x0 = ct.cot[a], x1 = ct.cot[z - 1] + 1;
            try{ var d = T.registerDecoration({marker:mk, x:x0, width:x1 - x0, foregroundColor:lt[1]}); if (d){ ds.push(d); st.dem++; } }catch(e){}
          }
        });
        muc.push({mk:mk, sig:ct.s, ds:ds});
      }
    }
    function hen(){ if (!cho) cho = setTimeout(ve, 90); }
    st.ve = hen;
    T.onWriteParsed(hen); T.onScroll(hen); T.onResize(hen);
    hen();
  }
  function datMau(bat){
    MAU_BAT = !!bat; try{ localStorage.setItem('phien-mau', bat ? '1' : '0'); }catch(e){}
    var n = $('nut-mau'); if (n) n.classList.toggle('on', MAU_BAT);
    document.querySelectorAll('#than iframe').forEach(function(f){ try{ if (f.contentWindow.__csMau) f.contentWindow.__csMau.ve(); }catch(e){} });
  }
  function ganChuot(f){
    ganMau(f);
    var d, w; try{ d = f.contentDocument; w = f.contentWindow; }catch(e){ return; }
    if (!d || d.__csChuot) return; d.__csChuot = true;
    /* HINH CAI KEO tren Edge (anh Thoai 19/10/2026): xterm.js, khi co vung chon, dat NOI DUNG DA CHON vao o
       nhap an (textarea.xterm-helper-textarea) roi select() no - Edge thay co vung chon trong o NHAP LIEU nen
       bat thanh cong cu nho "Cat / Chep" (cai keo = Cat) ngay canh vet boi. Vet boi nhin thay do xterm tu ve
       nen KHONG can chon that trong o nhap: vo hieu hoa select()/setSelectionRange() cua DUNG o nay. Go phim,
       dan, IME tieng Viet khong dung toi hai ham do. Chep da lo bang chepChon() (su kien copy), khong can no. */
    function voHieuChon(){
      var ta = d.querySelector('.xterm-helper-textarea');
      if (!ta || ta.__csKhongChon) return !!ta;
      ta.__csKhongChon = true; ta.select = function(){}; ta.setSelectionRange = function(){};
      return true;
    }
    if (!voHieuChon()){ var lan = 0, h = setInterval(function(){ if (voHieuChon() || ++lan > 40) clearInterval(h); }, 250); }
    d.addEventListener('mousedown', function(e){
      if (e.__cs) return;
      if (e.button === 2){ e.stopImmediatePropagation(); return; }          /* chuot phai: khong gui cho tmux */
      if (e.button === 0 && !e.shiftKey){
        e.stopImmediatePropagation();
        var n = new MouseEvent('mousedown', {bubbles:true, cancelable:true, composed:true, view:w,
          clientX:e.clientX, clientY:e.clientY, screenX:e.screenX, screenY:e.screenY, button:0, buttons:e.buttons,
          detail:e.detail, shiftKey:true, ctrlKey:e.ctrlKey, altKey:e.altKey, metaKey:e.metaKey});
        n.__cs = true; e.target.dispatchEvent(n);                           /* giong giu Shift: xterm.js tu boi den */
        /* Su kien that bi chan nen xterm.js khong tu focus o nhap; su kien gia khong lam doi tieu diem cua
           trinh duyet -> phai tu tra tieu diem cho terminal, neu khong bam vao terminal ma khong go duoc
           (anh Thoai 19/10/2026: dau nhay khong sang, phai bam dung vao dau nhay moi go duoc). */
        try{ w.term.focus(); }catch(er){}
        setTimeout(function(){ try{ w.term.focus(); }catch(er){} }, 0);
      }
    }, true);
    d.addEventListener('mouseup', function(e){
      if (e.button === 2){ e.stopImmediatePropagation(); return; }
      if (e.button === 0) setTimeout(function(){ chepChon(w, d); try{ w.term.focus(); }catch(er){} }, 40);
    }, true);
  }
  /* Bam x tren tab = TAT HAN phien (19/10/2026, anh Thoai: "tat phien roi mo lai van quay ve phien do va nhung
     thu no tung show"). Truoc day x chi dong tab, phien tmux chay ngam nen mo lai thay dung man hinh cu.
     Tai lai trang / dong trinh duyet KHONG goi ham nay nen phien van duoc giu khi chi lo tay mat trang. */
  function tatPhien(ma){
    api('/phien/api/'+encodeURIComponent(ma)+'/ngat', {}).catch(function(){});
    dongTab(ma);
  }
  function dongTab(ma){
    MO = MO.filter(function(t){ return t.ma!==ma; });
    var f = document.querySelector('#than iframe[data-ma="'+ma+'"]'); if (f) f.remove();
    if (DANG===ma) DANG = MO.length ? MO[MO.length-1].ma : null; veTabs();
  }
  $('ds').addEventListener('click', function(e){
    var s = e.target.closest('[data-sua]'); if (s){ e.stopPropagation(); moForm(DS.filter(function(p){return p.ma===s.dataset.sua;})[0]); return; }
    var m = e.target.closest('[data-ma]'); if (!m) return;
    var p = DS.filter(function(x){ return x.ma===m.dataset.ma; })[0]; if (p) moTab(p, true);
  });
  $('tabs').addEventListener('click', function(e){
    var x = e.target.closest('[data-dong]'); if (x){ e.stopPropagation(); tatPhien(x.dataset.dong); return; }
    var t = e.target.closest('[data-tab]'); if (t){ DANG = t.dataset.tab; veTabs(); }
  });
  $('o-loc').addEventListener('input', veDs);
  function ketNoiNhanh(){
    var v = $('o-nhanh').value.trim(); if (!v) return;
    api('/phien/api/nhanh', {chuoi:v}).then(function(d){
      if (!d.ok) { alert(d.loi); return; }
      taiDs().then(function(){ var p = DS.filter(function(x){return x.ma===d.ma;})[0] ||
        {ma:d.ma, ten:v, loai:d.loai||'ssh'}; moTab(p, false); $('o-nhanh').value=''; });
    });
  }
  $('nut-nhanh').onclick = ketNoiNhanh;
  $('o-nhanh').addEventListener('keydown', function(e){ if (e.key==='Enter') ketNoiNhanh(); });
  // ---- form phien
  var LOAI = 'ssh';
  function datLoai(l){ LOAI = l;
    document.querySelectorAll('#f-loai button').forEach(function(b){
      b.classList.toggle('chon', b.dataset.v===l); b.classList.toggle('gray', b.dataset.v!==l); });
    $('f-mang').hidden = l==='serial'; $('f-serial').hidden = l!=='serial'; $('f-ssh').hidden = l!=='ssh';
    $('f-port').placeholder = l==='telnet' ? '23' : '22';
  }
  document.querySelectorAll('#f-loai button').forEach(function(b){ b.onclick = function(){ datLoai(b.dataset.v); }; });
  function moForm(p){
    p = p || {}; $('md-tieude').textContent = p.ma ? 'Sửa phiên' : 'Phiên mới';
    $('f-ma').value = p.ma||''; $('f-ten').value = p.ten||''; $('f-nhom').value = p.nhom||'';
    $('f-host').value = p.host||''; $('f-port').value = p.port||''; $('f-user').value = p.user||'';
    $('f-mk').value=''; $('f-luu-mk').checked = false; $('f-xoa-mk').checked=false; $('f-ghichu').value = p.ghi_chu||'';
    $('f-xoa-mk-dong').hidden = !p.co_mat_khau; $('f-xoa').hidden = !p.ma; $('f-loi').hidden = true;
    var cong = DS.filter(function(x){ return x.loai==='serial' && !x.sua; });
    $('f-cong').innerHTML = cong.map(function(c){ return '<option value="'+esc(c.cong)+'">'+esc(c.cong+' - '+c.ten)+'</option>'; }).join('')
      || '<option value="">(chưa cắm cáp console)</option>';
    if (p.cong) $('f-cong').value = p.cong;
    $('f-baud').innerHTML = [1200,2400,4800,9600,19200,38400,57600,115200].map(function(b){
      return '<option'+(b===(+p.baud||9600)?' selected':'')+'>'+b+'</option>'; }).join('');
    datLoai(p.loai||'ssh'); $('md-phien').classList.add('on'); setTimeout(function(){ $('f-ten').focus(); }, 50);
  }
  $('nut-moi').onclick = function(){ moForm(null); };
  $('f-huy').onclick = function(){ $('md-phien').classList.remove('on'); };
  function luuForm(moLuon){
    var du = {ma:$('f-ma').value, loai:LOAI, ten:$('f-ten').value, nhom:$('f-nhom').value, host:$('f-host').value,
      port:$('f-port').value, user:$('f-user').value, mat_khau:$('f-mk').value, luu_mat_khau:$('f-luu-mk').checked?1:'',
      xoa_mat_khau:$('f-xoa-mk').checked?1:'', cong:$('f-cong').value, baud:$('f-baud').value, ghi_chu:$('f-ghichu').value};
    var mkNgay = $('f-mk').value;
    api('/phien/api/luu', du).then(function(d){
      if (!d.ok){ $('f-loi').textContent = d.loi; $('f-loi').hidden = false; return; }
      $('md-phien').classList.remove('on');
      taiDs().then(function(){
        if (!moLuon) return;
        var p = DS.filter(function(x){ return x.ma===d.ma; })[0]; if (!p) return;
        moTab(p, !mkNgay);
        if (mkNgay && !du.luu_mat_khau) api('/phien/api/'+encodeURIComponent(p.ma)+'/mk', {mat_khau:mkNgay});
      });
    });
  }
  $('f-luu').onclick = function(){ luuForm(false); };
  $('f-luu-mo').onclick = function(){ luuForm(true); };
  $('f-xoa').onclick = function(){
    var ma = $('f-ma').value; if (!ma || !confirm('Xoá phiên này?')) return;
    api('/phien/api/xoa', {ma:ma}).then(function(){ $('md-phien').classList.remove('on'); dongTab(ma); taiDs(); });
  };
  // ---- cong cu tab
  $('congcu').addEventListener('click', function(e){
    var b = e.target.closest('[data-lam]'); if (!b || !DANG) return;
    var u = '/phien/api/'+encodeURIComponent(DANG)+'/';
    var lam = b.dataset.lam;
    if (lam==='mk'){
      var t = MO.filter(function(x){return x.ma===DANG;})[0], p = DS.filter(function(x){return x.ma===DANG;})[0]||{};
      var mk = p.co_mat_khau ? null : prompt('Mật khẩu (sẽ được gõ khi thiết bị hỏi, không lưu):');
      if (mk === '' ) return;
      b.disabled = true;
      api(u+'mk', mk===null ? {} : {mat_khau:mk}).then(function(d){ b.disabled=false; if (!d.ok) alert(d.loi); });
    } else if (lam==='log'){ location.href = u+'log';
    } else if (lam==='full'){ var f = document.querySelector('#than iframe.on'); if (f && f.requestFullscreen) f.requestFullscreen();
    } else if (lam==='ngat'){ if (!confirm('Ngắt hẳn phiên này? (Kết nối tới thiết bị sẽ đóng)')) return;
      api(u+'ngat', {}).then(function(){ dongTab(DANG); });
    } else if (lam==='tv'){ moTv(!TV_MO);
    } else if (lam==='mau'){ datMau(!MAU_BAT); }
  });
  // ---- NGAN THU VIEN LENH: chon lenh lam san -> dien cho trong -> gui vao phien dang mo
  var TV_MO = false, TV_LOC = '', TV_THE = '', TV_CHON = -1, TV_MAU = '';
  function taiThuVien(){
    if (THU_VIEN.length) return Promise.resolve();
    return api('/phien/api/thu-vien').then(function(d){ THU_VIEN = d.tap || []; });
  }
  function veChip(){
    var cac = {}; THU_VIEN.forEach(function(t){ (t.the||[]).forEach(function(g){ cac[g]=(cac[g]||0)+1; }); });
    var ten = Object.keys(cac).sort(function(a,b){ return cac[b]-cac[a]; }).slice(0,8);
    $('tv-chip').innerHTML = ten.length ? ['Tất cả'].concat(ten).map(function(g,i){
      var v = i ? g : ''; return '<button type="button" data-the="'+esc(v)+'" class="'+(TV_THE===v?'on':'')+'">'+esc(g)+'</button>'; }).join('') : '';
  }
  function veThuVien(){
    var q = TV_LOC.toLowerCase(), h = '';
    THU_VIEN.forEach(function(t, i){
      if (TV_THE && (t.the||[]).indexOf(TV_THE) < 0) return;
      if (q && (t.ten+' '+t.mo_ta+' '+(t.the||[]).join(' ')+' '+t.lenh).toLowerCase().indexOf(q) < 0) return;
      var n = t.lenh.split('\n').filter(function(x){ return x.trim(); }).length;
      h += '<button type="button" class="ph-the'+(i===TV_CHON?' chon':'')+'" data-tv="'+i+'"><b>'+esc(t.ten)+'</b>'
        + (t.mo_ta ? '<span>'+esc(t.mo_ta)+'</span>' : '') + '<small>'+n+' dòng'+((t.the||[]).length?', '+esc(t.the.join(', ')):'')+'</small></button>';
    });
    if (!THU_VIEN.length) h = '<p class="hint" style="padding:12px;">Thư viện chưa có lệnh nào. Bấm <b>Quản lý</b> để thêm lệnh dùng thường xuyên.</p>';
    else if (!h) h = '<p class="hint" style="padding:12px;">Không có lệnh nào khớp.</p>';
    $('tv-ds').innerHTML = h;
  }
  // Cho trong dang {{ten}} trong lenh -> hien o nhap, dien den dau thay vao dong lenh den do
  function cacTruong(mau){ var r = [], m, re = /\{\{\s*([^{}]+?)\s*\}\}/g;
    while ((m = re.exec(mau))) if (r.indexOf(m[1]) < 0) r.push(m[1]); return r; }
  function ghepLenh(){
    var gt = {}; document.querySelectorAll('#tv-truong input').forEach(function(i){ gt[i.dataset.k] = i.value; });
    $('tv-nd').value = TV_MAU.replace(/\{\{\s*([^{}]+?)\s*\}\}/g, function(m, k){ return gt[k] ? gt[k] : m; });
  }
  function chonLenh(i){
    var t = THU_VIEN[i]; if (!t) return; TV_CHON = i; TV_MAU = t.lenh;
    $('tv-ten').textContent = t.ten; $('tv-kq').textContent = ''; $('tv-sua').hidden = false;
    var tr = cacTruong(TV_MAU);
    $('tv-truong').innerHTML = tr.map(function(k){
      return '<label>'+esc(k)+'</label><input type="text" data-k="'+esc(k)+'" autocomplete="off" autocapitalize="off">'; }).join('');
    $('tv-nd').value = TV_MAU; veThuVien();
    var o = $('tv-truong').querySelector('input'); if (o) setTimeout(function(){ o.focus(); }, 40);
  }
  function moTv(mo, i){
    TV_MO = mo; $('tv').hidden = !mo; $('nut-tv').classList.toggle('on', mo);
    try{ localStorage.setItem('phien-tv', mo ? '1' : '0'); }catch(e){}
    if (!mo) return;
    $('tv').classList.remove('vao'); void $('tv').offsetWidth; $('tv').classList.add('vao');
    taiThuVien().then(function(){ veChip(); veThuVien(); if (i != null && i >= 0) chonLenh(i); });
  }
  $('tv-chip').addEventListener('click', function(e){ var b = e.target.closest('[data-the]'); if (!b) return;
    TV_THE = b.dataset.the; veChip(); veThuVien(); });
  $('tv-ds').addEventListener('click', function(e){ var b = e.target.closest('[data-tv]'); if (b) chonLenh(+b.dataset.tv); });
  $('tv-tim').addEventListener('input', function(){ TV_LOC = this.value; veThuVien(); });
  $('tv-truong').addEventListener('input', ghepLenh);
  $('tv-dong').onclick = function(){ moTv(false); };
  $('tv-gui').onclick = function(){
    var nd = $('tv-nd').value, kq = $('tv-kq'); if (!nd.trim() || !DANG) return;
    kq.className = 'kq';
    if (/\{\{[^{}]+\}\}/.test(nd) && !confirm('Còn chỗ trống chưa điền ({{...}}). Vẫn gửi?')) return;
    var nut = this; nut.disabled = true; kq.textContent = 'Đang gửi...';
    api('/phien/api/'+encodeURIComponent(DANG)+'/dan', {noi_dung:nd}).then(function(d){
      nut.disabled = false;
      if (!d.ok) { kq.className = 'kq loi'; kq.textContent = d.msg || d.loi || 'Không gửi được'; return; }
      kq.textContent = 'Đã gửi vào ' + ((MO.filter(function(x){return x.ma===DANG;})[0]||{}).ten || 'phiên');
    });
  };
  $('bd-local').onclick = function(){ var p = DS.filter(function(x){return x.ma==='local';})[0]; if (p) moTab(p, false); };
  $('bd-ssh').onclick = function(){ moForm(null); };
  datMau(MAU_BAT);
  // ---- khoi dong
  taiDs().then(function(){
    var cu = {}; try{ cu = JSON.parse(localStorage.getItem('phien-tab')||'{}'); }catch(e){}
    var qs = new URLSearchParams(location.search), mo = qs.get('mo');
    var vlenh = qs.get('lenh'), vtv = qs.get('thuvien');
    // Chi mo lai tab cua phien CON TON TAI (phien da xoa / cap console da rut thi bo)
    (cu.mo||[]).forEach(function(t){ var p = DS.filter(function(x){return x.ma===t.ma;})[0];
      if (p) moTab(p, false); });
    if (mo){ var p = DS.filter(function(x){return x.ma===mo;})[0]; if (p) moTab(p, true); }
    else if (cu.dang && MO.some(function(t){return t.ma===cu.dang;})) { DANG = cu.dang; veTabs(); }
  });
  (function(){ var qs = new URLSearchParams(location.search), l = qs.get('lenh'), m = qs.get('thuvien'), nho = '0';
    try{ nho = localStorage.getItem('phien-tv') || '0'; }catch(e){}
    if (l !== null || m !== null || nho === '1') setTimeout(function(){ if (DANG || l !== null) moTv(true, l !== null ? +l : -1); }, 450);
  })();
  if (location.hash === '#moi') setTimeout(function(){ moForm(null); }, 300);
  setInterval(taiDs, 15000);   // cam/rut cap console -> danh sach tu cap nhat
})();
</script>
"""


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
    from .layout import svg_icon
    from .ph_icons import ph_icon
    html = re.sub(r"\[\[p:([a-z-]+)\]\]", lambda m: ph_icon(m.group(1)), html)
    return re.sub(r"\[\[i:([a-z]+)(?::([a-z]+))?\]\]",
                  lambda m: svg_icon(m.group(1), m.group(2) or "i"), html)


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
        nhom = sorted({p.get("nhom") for p in luu_ds if p.get("nhom")})
        return jsonify({"phien": ds, "nhom": nhom})

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
        from .commands import load_library
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
        from .commands import dan_thong_minh
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
