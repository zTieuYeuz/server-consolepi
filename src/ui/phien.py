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
    if ma == "local":
        return
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
.ph-modal [hidden],.ph-cong[hidden],.ph-trong[hidden]{display:none !important;}
.ph-khung{display:flex;gap:10px;height:calc(100vh - 72px);min-height:420px;}
.ph-trai{width:270px;flex:0 0 270px;display:flex;flex-direction:column;background:var(--card,#131a24);
  border:1px solid var(--border,#1f2733);border-radius:10px;overflow:hidden;}
.ph-trai .dau{padding:6px;border-bottom:1px solid var(--border,#1f2733);display:flex;gap:6px;}
.ph-trai input{margin:0;padding:7px 10px;min-height:0;}
.ph-ds{overflow:auto;flex:1;padding:6px 0;}
.ph-nhom{font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:#8A94A6;
  padding:10px 12px 4px;}
.ph-muc{display:flex;align-items:center;gap:8px;padding:7px 12px;cursor:pointer;border-left:3px solid transparent;}
.ph-muc:hover{background:#18212d;}
.ph-muc.mo{border-left-color:#38BDF8;background:#132132;}
.ph-muc .ic{width:26px;height:26px;border-radius:6px;display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;flex:none;}
.ic.ssh{background:#12324a;color:#7cc8ff;} .ic.telnet{background:#3a2a12;color:#ffcf7a;}
.ic.serial{background:#123a22;color:#7ddc9a;} .ic.local{background:#2a2140;color:#c8a8ff;}
.ph-muc .chu{flex:1;min-width:0;} .ph-muc .chu b{display:block;font-size:13.5px;font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.ph-muc .chu small{color:#8A94A6;font-size:11.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;display:block;}
.ph-muc .sua{opacity:.0;border:none;background:none;color:#8A94A6;cursor:pointer;font-size:14px;padding:2px 4px;}
.ph-muc:hover .sua{opacity:1;}
.ph-phai{flex:1;min-width:0;display:flex;flex-direction:column;background:var(--card,#131a24);
  border:1px solid var(--border,#1f2733);border-radius:10px;overflow:hidden;}
.ph-tabs{display:flex;gap:2px;padding:6px 6px 0;border-bottom:1px solid var(--border,#1f2733);overflow-x:auto;}
.ph-tab{display:flex;align-items:center;gap:8px;padding:5px 10px;border-radius:8px 8px 0 0;background:#0f151d;
  cursor:pointer;white-space:nowrap;font-size:13px;border:1px solid transparent;border-bottom:none;}
.ph-tab.on{background:#18212d;border-color:#2a3647;color:#fff;}
.ph-tab .x{border:none;background:none;color:#8A94A6;cursor:pointer;font-size:15px;line-height:1;padding:0 4px;min-height:0;min-width:0;}
.ph-cong{display:flex;gap:6px;flex-wrap:nowrap;overflow:hidden;padding:4px 8px;border-bottom:1px solid var(--border,#1f2733);align-items:center;}
.ph-cong button{padding:4px 10px;font-size:12.5px;min-height:0;}
.ph-than{flex:1;position:relative;background:#0f1114;}
.ph-than iframe{position:absolute;inset:0;width:100%;height:100%;border:0;display:none;}
.ph-than iframe.on{display:block;}
.ph-trong{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;flex-direction:column;
  color:#8A94A6;text-align:center;padding:20px;}
.ph-nhanh{display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;align-items:center;}
.ph-nhanh input{flex:1;min-width:240px;margin:0;font-family:ui-monospace,monospace;padding:8px 12px;min-height:0;}
.ph-nhanh button{padding:8px 14px;min-height:0;}
.ph-nhanh .tieude{font-weight:700;font-size:15px;margin-right:4px;white-space:nowrap;}
.ph-modal{position:fixed;inset:0;background:rgba(0,0,0,.6);display:none;align-items:flex-start;justify-content:center;
  z-index:50;overflow:auto;padding:16px 0 300px;}
.ph-modal.on{display:flex;}
.ph-modal .hop{background:#131a24;border:1px solid #2a3647;border-radius:12px;padding:18px;width:min(520px,94vw);
  max-height:90vh;overflow:auto;}
.ph-modal label{display:block;font-size:13px;color:#aeb7c5;margin:8px 0 3px;}
.ph-modal .hai{display:flex;gap:10px;} .ph-modal .hai>div{flex:1;}
.ph-loai{display:flex;gap:6px;} .ph-loai button{flex:1;}
.ph-loai button.chon{background:#38BDF8;color:#0b1220;border-color:#38BDF8;font-weight:700;}
@media (max-width:900px){.ph-khung{flex-direction:column;height:auto;}.ph-trai{width:auto;flex:none;max-height:260px;}
  .ph-phai{height:70vh;}}
</style>

<div class="ph-nhanh">
  <span class="tieude">🗂️ Phiên kết nối</span>
  <input type="text" id="o-nhanh" placeholder="Kết nối nhanh:  ssh admin@192.168.1.1   ·   telnet 10.0.0.1   ·   ttyUSB0" autocomplete="off">
  <button id="nut-nhanh" type="button">⚡ Kết nối</button>
  <button id="nut-moi" type="button" class="gray">+ Phiên mới</button>
</div>

<div class="ph-khung">
  <div class="ph-trai">
    <div class="dau"><input id="o-loc" type="search" placeholder="Tìm phiên..." autocomplete="off"></div>
    <div class="ph-ds" id="ds"></div>
  </div>
  <div class="ph-phai">
    <div class="ph-tabs" id="tabs"></div>
    <div class="ph-cong" id="congcu" hidden>
      <button type="button" data-lam="lenh" title="Chọn tập lệnh trong thư viện, sửa rồi dán vào phiên">📋 Gửi tập lệnh</button>
      <button type="button" data-lam="mk" title="Gõ mật khẩu giúp khi thiết bị hỏi">🔑 Gõ mật khẩu</button>
      <button type="button" data-lam="log" class="gray" title="Tải toàn bộ nội dung màn hình về máy">💾 Lưu log</button>
      <button type="button" data-lam="full" class="gray">🔍 Toàn màn hình</button>
      <button type="button" data-lam="ngat" class="gray" title="Kết thúc hẳn phiên (không chỉ đóng tab)">✖ Ngắt phiên</button>
      <span id="tt-tab" class="hint" style="margin-left:auto;flex:1 1 0;min-width:0;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"></span>
    </div>
    <div class="ph-than" id="than">
      <div class="ph-trong" id="trong">
        <div style="font-size:40px;">🖥️</div>
        <h3 style="margin:8px 0;">Chưa mở phiên nào</h3>
        <p style="max-width:460px;">Bấm một phiên ở danh sách bên trái, gõ vào ô <b>Kết nối nhanh</b>
          (ví dụ <code>ssh admin@192.168.1.1</code>), hoặc bấm <b>+ Phiên mới</b> để lưu thiết bị dùng lại.</p>
      </div>
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

<!-- Hop gui tap lenh -->
<div class="ph-modal" id="md-lenh"><div class="hop" style="width:min(680px,95vw);">
  <h3 style="margin:0 0 8px;">Gửi tập lệnh vào phiên</h3>
  <label>Chọn từ thư viện lệnh</label><select id="l-chon"></select>
  <label>Nội dung (sửa lại IP / tên cổng trước khi gửi)</label>
  <textarea id="l-noidung" rows="10" style="width:100%;font-family:ui-monospace,monospace;"></textarea>
  <p class="hint">Vào thiết bị mạng: gửi <b>từng dòng</b>, đợi thiết bị in xong mới gửi dòng tiếp; dòng cuối không tự Enter để anh/chị kiểm tra.</p>
  <div style="display:flex;gap:8px;margin-top:10px;"><button type="button" id="l-gui">Dán vào phiên</button>
    <button type="button" id="l-huy" class="gray">Đóng</button></div>
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
          + esc(moTa(p)) + (p.co_mat_khau?' · 🔑':'') + '</small></span>'
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
        + esc(t.ten) + '<button class="x" data-dong="'+esc(t.ma)+'" title="Đóng tab (phiên vẫn chạy)">×</button></div>';
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
      f.src = '/term-phien/?arg=' + encodeURIComponent(p.ma); $('than').appendChild(f);
      if (tuGoMk && p.co_mat_khau) api('/phien/api/'+encodeURIComponent(p.ma)+'/mk', {});
    }
    DANG = p.ma; veTabs();
    var f2 = document.querySelector('#than iframe[data-ma="'+p.ma+'"]'); if (f2) setTimeout(function(){ try{f2.focus();}catch(e){} }, 300);
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
    var x = e.target.closest('[data-dong]'); if (x){ e.stopPropagation(); dongTab(x.dataset.dong); return; }
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
    $('f-cong').innerHTML = cong.map(function(c){ return '<option value="'+esc(c.cong)+'">'+esc(c.cong+' — '+c.ten)+'</option>'; }).join('')
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
    } else if (lam==='lenh'){ moLenh(); }
  });
  function moLenh(){
    var napLai = THU_VIEN.length ? Promise.resolve() : api('/phien/api/thu-vien').then(function(d){ THU_VIEN = d.tap; });
    napLai.then(function(){
      $('l-chon').innerHTML = '<option value="">— Chọn tập lệnh —</option>' + THU_VIEN.map(function(t,i){
        return '<option value="'+i+'">'+esc(t.ten)+(t.mo_ta?' — '+esc(t.mo_ta):'')+'</option>'; }).join('');
      $('md-lenh').classList.add('on');
    });
  }
  $('l-chon').onchange = function(){ var t = THU_VIEN[this.value]; if (t) $('l-noidung').value = t.lenh; };
  $('l-huy').onclick = function(){ $('md-lenh').classList.remove('on'); };
  $('l-gui').onclick = function(){
    var nd = $('l-noidung').value; if (!nd.trim() || !DANG) return;
    this.disabled = true; var nut = this;
    api('/phien/api/'+encodeURIComponent(DANG)+'/dan', {noi_dung:nd}).then(function(d){
      nut.disabled = false; if (!d.ok) { alert(d.msg||d.loi); return; } $('md-lenh').classList.remove('on'); });
  };
  // ---- khoi dong
  taiDs().then(function(){
    var cu = {}; try{ cu = JSON.parse(localStorage.getItem('phien-tab')||'{}'); }catch(e){}
    var mo = new URLSearchParams(location.search).get('mo');
    // Chi mo lai tab cua phien CON TON TAI (phien da xoa / cap console da rut thi bo)
    (cu.mo||[]).forEach(function(t){ var p = DS.filter(function(x){return x.ma===t.ma;})[0];
      if (p) moTab(p, false); });
    if (mo){ var p = DS.filter(function(x){return x.ma===mo;})[0]; if (p) moTab(p, true); }
    else if (cu.dang && MO.some(function(t){return t.ma===cu.dang;})) { DANG = cu.dang; veTabs(); }
  });
  if (location.hash === '#moi') setTimeout(function(){ moForm(null); }, 300);
  setInterval(taiDs, 15000);   // cam/rut cap console -> danh sach tu cap nhat
})();
</script>
"""


CSS_GON = """
.main>.status{display:none;}
.content{padding:10px 12px 10px;max-width:none;}
.content>h1,.content>.sub{display:none;}
"""


def register_phien(app):
    @app.route("/phien")
    def phien_trang():
        # Trang terminal: bo thanh trang thai + tieu de lon cua khung chung de
        # khung terminal duoc cao toi da (yeu cau 27/09/2026 - phan tren chiem
        # gan 1/3 man hinh cam ung). Tieu de thu nho nam cung hang Ket noi nhanh.
        return render_page(TRANG + JS, active="/phien", title="Phiên kết nối", extra_css=CSS_GON)

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
            tap.append({"ten": t.get("name", ""), "mo_ta": t.get("desc", ""), "lenh": lenh})
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
