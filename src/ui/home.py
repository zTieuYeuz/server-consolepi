# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Trang Tong quan (yeu cau so 2 va 4)

Bo cuc uu tien nhung gi dan network can nhin dau tien:
  1. Cac cong console dang cam (viec chinh cua thiet bi nay)
  2. Trang thai mang chi tiet tung card
  3. Tinh trang cac dich vu
"""
import glob
import os
import re
import subprocess

from flask import request

from .layout import render_page, get_status_chips, gan_phien_tmux
from . import health
from . import duongdan as _DD
from consolesystem.core.esc import esc as _esc

BASE_TTYD_PORT = 8001
NAMES_FILE = _DD.FILE_TEN_CONG

SERVICES = [
    ("console-pi-dashboard", "Dashboard web"),
    ("console-pi-term-local", "Terminal tại chỗ"),
    ("console-pi-term-ssh", "Terminal SSH"),
    ("lldpd", "LLDP/CDP discovery"),
    ("bluetooth", "Bluetooth"),
    ("bt-nap", "Bluetooth PAN"),
    ("wifi-fallback.timer", "Tự chuyển WiFi/AP"),
    ("console-pi-kiosk", "Màn hình cảm ứng"),
]




def power_msg_html(h):
    """Dung chung giua Tong quan va tab Nguon dien (dung 1 nguon logic)."""
    th = h["throttle"]
    if th is None:
        return ('<span style="color:#8b93a1;">Không áp dụng &mdash; máy này '
                'không phải Raspberry Pi (không có cảm biến nguồn)</span>')
    if th["now"]:
        return ('<span style="color:#ff6b6b;">⛔ ' +
                _esc(", ".join(th["now"])) +
                ' - ĐANG xảy ra. Đổi nguồn/cáp sạc tốt hơn ngay.</span>')
    if th["past"]:
        return ('<span style="color:#ffb74d;">⚠️ ' +
                _esc(", ".join(th["past"])) +
                ' - đã từng xảy ra kể từ lúc bật máy. Nguồn đang ở ranh giới.</span>')
    return '<span style="color:#6ee7a0;">🟢 Nguồn ổn định, không sụt áp</span>'


def load_names():
    import json
    try:
        with open(NAMES_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def console_port_for(devname):
    """
    Cong web cho 1 thiet bi serial. Hai ho thiet bi dung dai cong rieng de
    khong dam nhau:
        ttyUSB0..3 -> 8001..8004   (cap FTDI / Prolific / CH340 thong thuong)
        ttyACM0..3 -> 8005..8008   (cap Cisco USB Console, thiet bi CDC-ACM)

    Cong thuc nay phai KHOP voi scripts/ttyd-one.sh va bang map trong
    config/nginx-console-pi.conf - lech mot cho la console khong mo duoc.
    """
    m = re.search(r"(\d+)$", devname)
    idx = int(m.group(1)) if m else 0
    base = 8005 if devname.startswith("ttyACM") else BASE_TTYD_PORT
    return base + idx


def chip_of(devname):
    """
    Ten chip/hang cua cap console, doc tu /dev/serial/by-id.
    Giup phan biet khi cam nhieu cap cung luc (vd 'Cisco' vs 'FTDI').
    """
    try:
        for link in glob.glob("/dev/serial/by-id/*"):
            if os.path.basename(os.path.realpath(link)) == devname:
                name = os.path.basename(link)
                # usb-FTDI_FT232R_USB_UART_A9WUI6D2-if00-port0 -> FTDI FT232R
                name = name.replace("usb-", "").split("-if")[0]
                parts = name.split("_")
                return " ".join(parts[:3])[:34]
    except Exception:
        pass
    return ""


def get_ports():
    """
    Tim moi cong console dang cam.

    Quet CA HAI ho thiet bi:
      /dev/ttyUSB*  - cap dung chip chuyen doi (FTDI, Prolific, CH340...)
      /dev/ttyACM*  - thiet bi CDC-ACM, vi du cap console micro-USB cua Cisco
                      (thiet bi tu trinh dien la USB device)

    Truoc day chi quet ttyUSB* nen cap Cisco micro-USB cam vao khong hien -
    kernel co nhan (tao /dev/ttyACM0) nhung dashboard bo sot.
    """
    names = load_names()
    out = []
    for dev in sorted(glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")):
        devname = os.path.basename(dev)
        out.append({
            "devname": devname,
            "name": names.get(devname, ""),
            "port": console_port_for(devname),
            "chip": chip_of(devname),
        })
    return out


def service_states(names):
    """
    Hoi trang thai NHIEU dich vu bang MOT lenh.
    Truoc day goi rieng tung cai (8 lan spawn tien trinh moi lan tai trang) -
    tren Pi doi thap rat cham. systemctl is-active nhan nhieu ten cung luc.
    """
    try:
        r = subprocess.run(["systemctl", "is-active"] + list(names),
                           capture_output=True, text=True, timeout=6)
        lines = r.stdout.split()
        if len(lines) == len(names):
            return dict(zip(names, lines))
    except Exception:
        pass
    return {n: "unknown" for n in names}


def iface_detail(name):
    """Thong tin chi tiet 1 interface cho bang trang chu."""
    info = {"name": name, "ip": "", "mac": "", "state": "?", "speed": "", "extra": ""}
    try:
        with open(f"/sys/class/net/{name}/operstate") as f:
            info["state"] = f.read().strip()
    except Exception:
        return None      # interface khong ton tai
    try:
        with open(f"/sys/class/net/{name}/address") as f:
            info["mac"] = f.read().strip()
    except Exception:
        pass
    # Doc IP tu /proc/net/route + lenh ip chi khi can.
    # Uu tien /sys va /proc vi khong phai spawn tien trinh - nhanh hon nhieu
    # tren Pi doi thap (Pi 3 / Zero).
    try:
        out = subprocess.run(["ip", "-4", "-o", "addr", "show", name],
                             capture_output=True, text=True, timeout=4).stdout
        for tok in out.split():
            if "/" in tok and tok.count(".") == 3:
                info["ip"] = tok
                break
    except Exception:
        pass
    try:
        with open(f"/sys/class/net/{name}/speed") as f:
            s = f.read().strip()
            if s and s != "-1":
                info["speed"] = f"{s} Mbps"
    except Exception:
        pass
    return info


def _hang_so(nhan, gia_tri, phu="", phan_tram=None, muc="ok", co_dem=None, ghi_chu=False, chu_thich=""):
    """
    1 dong cua khoi "Suc khoe thiet bi": nhan ben trai, so ben phai, thanh ben duoi.
    Thanh CO NEN (track): phan nen xam la 100% nen nhin vao biet ngay da dung bao nhieu tren tong - truoc day
    thanh chi dai ra theo % khong co nen nen khong thay thang do (anh Thoai 22/10/2026: dung 17 GB ma nhin nhu 10 GB).
    Mau thanh theo muc: ok (xanh) / warn (vang) / bad (do). chu_thich: dong chu nho duoi thanh (da dung / con trong).
    co_dem: (so, so_le) de JS dem tu 0 len luc moi vao trang.
    """
    if co_dem is not None and not ghi_chu:
        so, le = co_dem
        gia_tri = gia_tri.replace(str(so), f'<span data-n="{so}" data-d="{le}">{so}</span>', 1)
    thanh = ""
    if phan_tram is not None:
        rong = max(1, min(100, int(phan_tram)))
        thanh = ('<span class="track" role="img" aria-label="' + str(rong) + '%"><span class="bar ' + muc
                 + '" style="width:' + str(rong) + '%"></span></span>')
        if chu_thich:
            thanh += '<span class="cap">' + chu_thich + '</span>'
    lop = ' class="none"' if ghi_chu else ""
    nho = ("<small>" + phu + "</small>") if phu else ""
    return ("<div" + lop + "><dt>" + nhan + "</dt><dd>" + gia_tri + nho + "</dd>" + thanh + "</div>")


def _so_gb(x):
    """17.1 -> '17,1' (dau phay kieu Viet)."""
    return f"{x:.1f}".replace(".", ",")


def _muc(p, vang, do):
    return "ok" if p < vang else ("warn" if p < do else "bad")


def _bang_suc_khoe(h, power_msg):
    """
    Khoi "Suc khoe thiet bi" - dung RIENG mot ham vi duoc dung o HAI cho: luc
    dung trang lan dau, va moi 10 giay khi /api/suckhoe tra ve de cap nhat
    tai cho. Viet 2 ban se lech nhau.

    Giao dien moi (18/10/2026): danh sach dong (nhan - so - thanh mong) thay
    cho luoi the; so lieu y nhu cu, cho nao khong do duoc thi ghi ro, khong
    bia so.
    """
    temp = h.get("temp")
    mem_u, mem_t, mem_p = h.get("mem", (0, 0, 0))
    dk_u, dk_t, dk_p = h.get("disk", (0, 0, 0))
    cpu = h.get("cpu")

    if cpu is None:
        # Lan do dau tien chua co moc so sanh - xem cpu_percent() trong
        # ui/health.py. Sau 10 giay se co so that.
        r_cpu = _hang_so("CPU", "đang đo…", ghi_chu=True)
    else:
        r_cpu = _hang_so("CPU", f"{cpu}%", "", cpu, _muc(cpu, 75, 90), (cpu, 0))

    r_ram = _hang_so("Bộ nhớ", f"{mem_p}%", f"{mem_u} / {mem_t} MB", mem_p,
                     _muc(mem_p, 75, 90), (mem_p, 0),
                     chu_thich=f"Đã dùng <b>{mem_u} MB</b> · còn trống <b>{max(mem_t - mem_u, 0)} MB</b>")

    if temp is None:
        r_temp = _hang_so("Nhiệt độ CPU", "máy này không có cảm biến", ghi_chu=True)
    else:
        r_temp = _hang_so("Nhiệt độ CPU", f"{temp} &deg;C", "", min(100, temp),
                          _muc(temp, 65, 80))

    # LOI THAT (26/09/2026, test ban ISO 32-bit chay LIVE tu USB): o dia hien
    # "0 / 0 GB 0%" - so bia. May live khong co o cai dat: "/" la overlay nam
    # tren RAM. Nguyen tac du an: khong bia so - ghi ro la khong ap dung.
    if os.path.isdir("/run/live/medium"):
        r_dia = _hang_so("Ổ đĩa", "không áp dụng (đang chạy từ USB)", ghi_chu=True)
    elif dk_t:
        r_dia = _hang_so("Ổ đĩa", f"{dk_p}%", f"{_so_gb(dk_u)} / {_so_gb(dk_t)} GB", dk_p,
                         _muc(dk_p, 80, 92), (dk_p, 0),
                         chu_thich=f"Đã dùng <b>{_so_gb(dk_u)} GB</b> · còn trống <b>{_so_gb(max(dk_t - dk_u, 0))} GB</b>"
                                   f" · tổng {_so_gb(dk_t)} GB")
    else:
        r_dia = _hang_so("Ổ đĩa", "không đọc được", ghi_chu=True)

    r_tai = (f'<div class="tai"><dt>Tải hệ thống</dt><dd>{h.get("load", "?")}'
             f'<small>trung bình 1 / 5 / 15 phút</small></dd></div>')

    return f"""
        <dl class="dl">{r_cpu}{r_ram}{r_dia}{r_temp}{r_tai}</dl>
        <p class="so-nguon"><b>Nguồn điện:</b> {power_msg}</p>"""


# ---------------------------------------------------------------- tong quan
# Thu muc du lieu -> (ten de hieu, trang quan ly). Dung cho the "Can chu y"
# khi dia sap day: chi ra CAI GI dang chiem cho va bam vao dung trang do de
# nguoi dung TU chon xoa. Khong bao gio tu xoa.
_THU_MUC_LON = [
    ("deploy/os", "Bộ cài Windows", "/deployos/os"),
    ("deploy/winpe-apps", "Ứng dụng WinPE cứu hộ", "/deployos/console"),
    ("deploy/boot", "File WinPE / boot", "/deployos/console"),
    ("deploy/apps", "Phần mềm cài kèm", "/deployos/console/apps"),
    ("deploy/ungdung", "Ứng dụng nhiều file", "/deployos/ungdung"),
    ("deploy/drivers", "Driver", "/deployos/drivers"),
    ("deploy/fonts", "Font chữ", "/deployos/font"),
    ("storage", "Kho file", "/storage"),
]
_DL_CACHE = {"t": 0, "ds": []}


def _kich_thuoc(duong):
    tong = 0
    for goc, _ds, cac_file in os.walk(duong):
        for f in cac_file:
            try:
                tong += os.lstat(os.path.join(goc, f)).st_size
            except OSError:
                pass
    return tong


def dung_luong_lon():
    """[(ten, trang, so_byte)] cac thu muc du lieu lon, giam dan. Nho 10 phut."""
    import time as _t
    if _t.time() - _DL_CACHE["t"] < 600:
        return _DL_CACHE["ds"]
    from .duongdan import _duong
    ds = []
    for tuong_doi, ten, trang in _THU_MUC_LON:
        d = _duong(tuong_doi)
        if os.path.isdir(d):
            n = _kich_thuoc(d)
            if n >= 50 * 1024 * 1024:
                ds.append((ten, trang, n))
    ds.sort(key=lambda x: -x[2])
    _DL_CACHE.update(t=_t.time(), ds=ds)
    return ds


def _gb(n):
    return f"{n / 1024 ** 3:.1f}".replace(".", ",") + " GB" if n >= 1024 ** 3 else f"{n // 1024 ** 2} MB"


def can_chu_y(h, ports, states):
    """
    Cac the "Can chu y" o dau trang Tong quan - CHI sinh tu so lieu that
    cua may, khong co gi la minh hoa. Tra ve [(muc, icon, tieu_de, mo_ta, nut)]
    muc: "do" (loi) / "vang" (canh bao) / "nhan" (thong tin).
    """
    ra = []
    th = h.get("throttle")
    if th and th.get("now"):
        ra.append(("do", "bolt", "Nguồn điện đang yếu",
                   _esc(", ".join(th["now"])) + ". Đổi nguồn / cáp sạc tốt hơn.",
                   ("Xem nguồn điện", "/power")))
    temp = h.get("temp")
    if temp is not None and temp >= 70:
        ra.append(("do" if temp >= 80 else "vang", "temp", f"Nhiệt độ CPU {temp} °C",
                   "Máy đang nóng. Để chỗ thoáng, kiểm tra quạt / tản nhiệt.", None))
    hong = [nhan for svc, nhan in SERVICES if states.get(svc) == "failed"]
    if hong:
        ra.append(("do", "warn", "Dịch vụ bị lỗi: " + _esc(", ".join(hong)),
                   "Dịch vụ này đã dừng vì lỗi. Xem nhật ký để biết lý do.",
                   ("Xem nhật ký", "/logs")))
    dk_u, dk_t, dk_p = h.get("disk", (0, 0, 0))
    if dk_t and dk_p >= 80 and not os.path.isdir("/run/live/medium"):
        lon = dung_luong_lon()[:3]
        mo_ta = f"Đã dùng {_so_gb(dk_u)} / {_so_gb(dk_t)} GB. "
        if lon:
            mo_ta += "Chiếm nhiều nhất: " + ", ".join(
                f'<a href="{t}">{_esc(n)} {_gb(b)}</a>' for n, t, b in lon) + "."
        ra.append(("do" if dk_p >= 92 else "vang", "save",
                   f"Bộ nhớ lưu trữ đã đầy {dk_p}%", mo_ta,
                   ("Xem " + lon[0][0], lon[0][1]) if lon else None))
    chua_ten = [p["devname"] for p in ports if not p.get("name")]
    if chua_ten:
        ra.append(("nhan", "usb", "Cáp console chưa đặt tên",
                   "Cổng " + ", ".join(f"<code>{_esc(d)}</code>" for d in chua_ten) +
                   ". Đặt tên để dễ nhận ra thiết bị.", ("Đặt tên", "#cong-console")))
    try:
        from . import pxe as _pxe
        if _pxe.dang_bat():
            ra.append(("nhan", "disk", "PXE đang bật",
                       "Máy trong mạng chọn boot qua mạng sẽ thấy menu cài Windows. "
                       "Tắt khi xong việc.", ("Bật / Tắt PXE", "/deployos/caidat")))
    except Exception:
        pass
    n_cai = _so_may_dang_cai()
    if n_cai:
        ra.append(("nhan", "win", f"Đang cài Windows cho {n_cai} máy",
                   "Theo dõi tiến độ từng máy.", ("Xem tiến trình", "/deployos/tiendo")))
    return ra


def _so_may_dang_cai():
    """So may dang o giua chung (WinPE / Windows), cap nhat trong 3 gio qua."""
    import time as _t
    try:
        from . import lichsu as _ls
        moc = _t.time() - 3 * 3600
        return sum(1 for b in _ls.danh_sach()
                   if b.get("trang_thai") in ("winpe", "windows")
                   and (b.get("cap_nhat") or b.get("bat_dau") or 0) >= moc)
    except Exception:
        return 0


def _dem_kich_ban():
    try:
        from .deployos import KICHBAN_DIR
        return sum(1 for f in os.listdir(KICHBAN_DIR) if f.endswith(".json"))
    except Exception:
        return 0


def _dem_may_wol():
    try:
        from . import wol as _w
        return len(_w.tat_ca_may())
    except Exception:
        return 0


def _cai_gan_day(n=5):
    try:
        from . import lichsu as _ls
        return _ls.danh_sach()[:n], _ls
    except Exception:
        return [], None


CSS_TONG_QUAN = """
/* ---- Phan mo dau ---- */
.hero { display:grid; grid-template-columns:minmax(0,1.5fr) minmax(0,1fr); gap:clamp(24px,5vw,72px);
        align-items:end; padding:20px 0 12px; }
.hero h1 { font-size:clamp(34px,4.2vw,54px); line-height:1.04; letter-spacing:-.035em; margin:0; }
.hero h1 em { font-style:normal; color:var(--xanh); }
.hero h1 em.canh { color:var(--vang); }
.hero p { margin:14px 0 0; max-width:52ch; color:var(--chu-mo); font-size:16px; line-height:1.55; }
.hero .acts { display:flex; flex-wrap:wrap; gap:10px; margin-top:24px; }
.net { margin:0; border-left:1px solid var(--vien); padding-left:clamp(20px,3vw,40px); display:grid; gap:20px; }
.net dt { font-size:13px; color:var(--chu-mo2); }
.net dd { margin:3px 0 0; font:550 clamp(20px,2.2vw,28px)/1.15 var(--mono); letter-spacing:-.03em; word-break:break-all; }
.net dd small { display:block; font:400 13px var(--chu-font); letter-spacing:0; color:var(--chu-mo); margin-top:5px; }
.net dd.off { font:500 17px var(--chu-font); color:var(--chu-mo); letter-spacing:0; }
@media (max-width:1100px) { .hero { grid-template-columns:1fr; }
  .net { border-left:0; padding-left:0; border-top:1px solid var(--vien); padding-top:20px; grid-template-columns:1fr 1fr; } }
@media (max-width:640px) { .net { grid-template-columns:1fr; } .hero .acts .btn { flex:1 1 100%; } }
section.rvg { margin-top:44px; }
.hero.rvg { margin-top:0; }

/* ---- Viec hay lam (Che do PC): luoi bat doi xung, du 5 o ---- */
.bento { display:grid; grid-template-columns:repeat(6,1fr); grid-auto-rows:minmax(104px,auto); gap:12px; }
.bt { position:relative; display:flex; flex-direction:column; justify-content:flex-end; gap:2px; padding:20px;
      border:1px solid var(--vien); border-radius:var(--bo); background:var(--the); color:var(--chu); overflow:hidden; }
.bt:hover { border-color:var(--vien-ro); color:var(--chu); }
.bt:active { transform:scale(.99); }
.bt svg.i { width:26px; height:26px; color:var(--nhan); margin-bottom:auto; }
.bt svg.go { position:absolute; top:18px; right:18px; width:18px; height:18px; color:var(--chu-mo2); margin:0; }
.bt:hover svg.go { color:var(--chu); transform:translateX(3px); }
.bt b { font-size:16px; font-weight:600; letter-spacing:-.01em; }
.bt span { font-size:13.5px; color:var(--chu-mo); }
.bt.a { grid-column:span 4; grid-row:span 2; padding:28px;
        background:radial-gradient(120% 90% at 100% 0%, var(--nhan-mo), transparent 60%), var(--the);
        border-color:color-mix(in srgb, var(--nhan) 32%, var(--vien)); }
.bt.a svg.i { width:34px; height:34px; }
.bt.a b { font-size:clamp(22px,2.2vw,28px); letter-spacing:-.025em; font-weight:630; }
.bt.a span { font-size:15px; max-width:40ch; }
.bt.b, .bt.c { grid-column:span 2; }
.bt.d, .bt.e { grid-column:span 3; min-height:96px; }
.bt::after { content:""; position:absolute; inset:0; border-radius:inherit; pointer-events:none; opacity:0;
             transition:opacity .25s;
             background:radial-gradient(240px circle at var(--mx,50%) var(--my,50%), color-mix(in srgb, var(--nhan) 16%, transparent), transparent 70%); }
.bt:hover::after { opacity:1; }
@media (hover:none) { .bt::after { display:none; } }
@media (max-width:640px) { .bento { grid-template-columns:1fr 1fr; }
  .bt.a { grid-column:span 2; grid-row:auto; min-height:190px; }
  .bt.b, .bt.c, .bt.d, .bt.e { grid-column:span 1; min-height:132px; } }

/* ---- Suc khoe: dong nhan - so - thanh mong ---- */
.dl { margin:0; display:grid; }
.dl > div { display:grid; grid-template-columns:1fr auto; align-items:baseline; gap:4px 16px;
            padding:14px 0; border-bottom:1px solid var(--vien); }
.dl > div:first-child { padding-top:0; }
.dl dt { color:var(--chu-mo); font-size:14.5px; white-space:nowrap; }
.dl .tai dd { font-size:15px; }
.dl dd { margin:0; font:550 20px var(--mono); letter-spacing:-.03em; text-align:right; }
.dl dd small { font:400 13px var(--chu-font); color:var(--chu-mo2); letter-spacing:0; margin-left:8px; }
.dl .track { grid-column:1 / -1; display:block; height:8px; border-radius:5px; background:var(--vien-ro);
             overflow:hidden; margin-top:6px; }
.dl .bar { display:block; height:100%; border-radius:5px; background:var(--nhan); transform-origin:left; }
.dl .cap { grid-column:1 / -1; font-size:12.5px; color:var(--chu-mo2); margin-top:2px; }
.dl .cap b { color:var(--chu-mo); font-weight:600; }
.dl .bar.ok { background:var(--xanh); } .dl .bar.warn { background:var(--vang); } .dl .bar.bad { background:var(--do); }
.dl .none dd { font:400 14.5px var(--chu-font); color:var(--chu-mo2); letter-spacing:0; }
.so-nguon { margin:14px 0 0; font-size:14px; color:var(--chu-mo); }
.vazio { border:1px dashed var(--vien-ro); border-radius:var(--bo); padding:24px; display:grid; gap:12px; justify-items:start; }
.vazio h3 { margin:0; font-size:16px; font-weight:600; }
.vazio p { margin:0; color:var(--chu-mo); max-width:46ch; font-size:14.5px; }
.col { display:grid; gap:30px; align-content:start; }
.tq-hai { display:grid; grid-template-columns:minmax(0,5fr) minmax(0,7fr); gap:clamp(24px,5vw,72px); align-items:start; }
@media (max-width:1100px) { .tq-hai { grid-template-columns:1fr; } }

/* ---- Dich vu: 2 cot, chu trang thai (khong chi dua vao mau) ---- */
.svc { list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:0 clamp(24px,5vw,72px); }
.svc li { display:flex; justify-content:space-between; align-items:center; gap:16px; padding:13px 0; border-top:1px solid var(--vien); }
.sv-t b { display:block; font-weight:550; font-size:14.5px; }
.sv-t code { background:none; padding:0; font-size:12px; color:var(--chu-mo2); }
.tt { font-size:13px; font-weight:600; display:inline-flex; align-items:center; gap:7px; white-space:nowrap; }
.tt.bat { color:var(--xanh); } .tt.bat::before { content:""; width:7px; height:7px; border-radius:50%; background:var(--xanh); }
.tt.tat { color:var(--chu-mo2); font-weight:500; }
.tt.hong { color:var(--do); }
@media (max-width:640px) { .svc { grid-template-columns:1fr; } }

/* ---- The "can chu y" ---- */
.ccy { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:12px; }
.ccy-the { display:flex; gap:12px; align-items:flex-start; padding:16px 18px; border-radius:var(--bo);
           border:1px solid var(--vien); background:var(--the); }
.ccy-the .bi { width:40px; height:40px; border-radius:10px; display:grid; place-items:center; flex:none; }
.ccy-the.vang { border-color:rgba(232,176,74,.45); background:var(--vang-mo); }
.ccy-the.vang .bi { color:var(--vang); background:var(--vang-mo); }
.ccy-the.do { border-color:rgba(239,107,107,.45); background:var(--do-mo); }
.ccy-the.do .bi { color:var(--do); background:var(--do-mo); }
.ccy-the.nhan .bi { color:var(--nhan); background:var(--nhan-mo); }
.ccy-the .nd { flex:1; min-width:0; }
.ccy-the .nd b { display:block; font-size:14.5px; color:var(--chu); margin-bottom:2px; }
.ccy-the .nd span { font-size:13px; color:var(--chu-mo); line-height:1.5; }
.ccy-the .nut { margin-top:10px; }

/* ---- Che do cam ung: giu o to nhu cu ---- */
.viec { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; }
body.cd-cu .viec { grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:16px; }
body.cd-cu .viec .o-to { min-height:150px; padding:20px; border-radius:22px; }
body.cd-cu .viec .o-to b { font-size:18.5px; margin-top:auto; }
body.cd-cu .viec .o-to .bi { width:56px; height:56px; border-radius:16px; }
body.cd-cu .hero { padding-top:6px; }
body.cd-cu .hero p { font-size:17px; }
.o-to .nhan-so { position:absolute; top:14px; right:14px; font-size:12px; font-weight:700;
                 padding:4px 10px; border-radius:999px; background:var(--nhan-mo); color:var(--nhan); }
.o-to .nhan-so.xanh { background:var(--xanh-mo); color:var(--xanh); }
.gan-day { display:flex; flex-direction:column; }
.gan-day a { display:flex; gap:12px; align-items:center; padding:12px 4px; border-top:1px solid var(--vien);
             color:var(--chu); font-size:14px; }
.gan-day a:first-child { border-top:0; }
.gan-day a .t { flex:1; min-width:0; }
.gan-day a small { display:block; color:var(--chu-mo); font-size:12.5px; }
.gan-day .tt { font-size:12px; padding:3px 10px; border-radius:999px; background:var(--the-noi); }

/* ---- Hieu ung rieng trang Tong quan ---- */
@media (prefers-reduced-motion: no-preference) {
  .js-tq .rv { opacity:0; transform:translateY(16px); }
  .js-tq .rv.in { opacity:1; transform:none; transition:opacity .7s var(--muot) var(--d,0s), transform .7s var(--muot) var(--d,0s); }
  .js-tq #suc-khoe:not(.lan2) .bar { animation:chay-thanh 1.1s var(--muot) .25s both; }
  @keyframes chay-thanh { from { transform:scaleX(0); } to { transform:none; } }
  .tt.bat::before { animation:nhip 2.4s ease-out infinite; }
  .dl dd.sk { position:relative; color:transparent !important; }
  .dl dd.sk * { color:transparent !important; }
  .dl dd.sk::after { content:""; position:absolute; inset:3px 0 3px auto; width:min(110px,60%); border-radius:5px;
    background:linear-gradient(90deg,var(--vien) 0%,var(--vien-ro) 50%,var(--vien) 100%); background-size:200% 100%;
    animation:quet 1.2s linear infinite; }
  @keyframes quet { to { background-position:-200% 0; } }
}
"""

# Hieu ung trang Tong quan: hien dan theo thu bac, so dem len, o sang theo con tro.
# KHONG dung scroll listener: IntersectionObserver + requestAnimationFrame cho so.
JS_TONG_QUAN = """
<script>
(function() {
  var giam = matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.querySelectorAll('.bt').forEach(function(o) {
    o.addEventListener('pointermove', function(e) {
      var b = o.getBoundingClientRect();
      o.style.setProperty('--mx', (e.clientX - b.left) + 'px');
      o.style.setProperty('--my', (e.clientY - b.top) + 'px');
    });
  });
  if (giam) return;
  function dem(el) {
    var to = parseFloat(el.dataset.n), d = +el.dataset.d || 0, t0 = performance.now();
    (function f(t) { var k = Math.min(1, (t - t0) / 900), e = 1 - Math.pow(1 - k, 3);
      el.textContent = (to * e).toFixed(d); if (k < 1) requestAnimationFrame(f); })(t0);
  }
  document.documentElement.classList.add('js-tq');
  document.querySelectorAll('.rvg').forEach(function(g) {
    var ks = g.classList.contains('hero') ? g.querySelectorAll('h1,p,.acts,.net > div')
      : g.querySelectorAll(':scope > h2, :scope > div > h2, :scope > div > div > h2, .bt, .dl > div, .vazio, .ccy-the, .tbl-scroll, .svc li');
    ks.forEach(function(k, i) { k.classList.add('rv'); k.style.setProperty('--d', (i * 0.07) + 's'); });
  });
  var io = new IntersectionObserver(function(es) { es.forEach(function(e) {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }); }, {threshold: .12});
  document.querySelectorAll('.rv').forEach(function(n) { io.observe(n); });
  /* Khung cho luc doc so lieu, roi so dem len tu 0 (phan hoi: dang cap nhat that) */
  var dds = document.querySelectorAll('#suc-khoe .dl dd'); dds.forEach(function(d) { d.classList.add('sk'); });
  setTimeout(function() {
    dds.forEach(function(d) { d.classList.remove('sk'); });
    document.querySelectorAll('#suc-khoe [data-n]').forEach(dem);
  }, 800);
})();
</script>
"""


def register_home(app):
    @app.route("/")
    def home():
        host = request.host.split(":")[0]
        ports = get_ports()

        # --- Cong console ---
        if ports:
            rows = ""
            for p in ports:
                rows += f"""
                <tr>
                  <td><code>{p['devname']}</code>
                      {f'<br><small style="color:#8b93a1;">{_esc(p["chip"])}</small>' if p.get("chip") else ''}</td>
                  <td>
                    <form method="POST" action="/rename" class="row" style="gap:7px;">
                      <input type="hidden" name="devname" value="{p['devname']}">
                      <input type="text" name="name" value="{_esc(p['name'])}"
                             placeholder="Ví dụ: Switch tầng 3" style="max-width:260px;">
                      <button type="submit" class="gray small">Lưu tên</button>
                    </form>
                  </td>
                  <td><a class="btn" href="/phien?mo=serial-{p['devname']}">Mở Console</a></td>
                </tr>"""
            ports_html = f"""
            <table>
              <tr><th style="width:120px;">Cổng</th><th>Tên gợi nhớ</th><th style="width:150px;">Thao tác</th></tr>
              {rows}
            </table>"""
        else:
            ports_html = ('<div class="vazio"><h3>Chưa cắm cáp console nào</h3>'
                          '<p>Cắm cáp USB-serial (FTDI/Prolific) vào máy này, trang sẽ tự nhận và hiện cổng ở đây.</p></div>')

        # --- Mang chi tiet ---
        net_rows = ""
        # Liet ke CONG THAT cua may, khong viet cung "eth0"/"wlan0": tren may
        # x86 cong ten ens3/enp1s0/wlp2s0 nen bang nay tung trong tron (bat
        # duoc khi thu ban ISO 23/09/2026). pan0 la cong ao cua du an
        # (Bluetooth) nen phancung loc ra - them tay, khong co thi bo qua.
        from .phancung import danh_sach_cong
        cac_cong = [(c["ten"], "Card WiFi" if c["wifi"] else "Card LAN")
                    for c in danh_sach_cong()] + [("pan0", "Bluetooth PAN")]
        for ifname, label in cac_cong:
            d = iface_detail(ifname)
            if not d:
                continue
            up = bool(d["ip"])
            net_rows += f"""
            <tr>
              <td><strong>{label}</strong><br><code style="font-size:12px;">{ifname}</code></td>
              <td>{'<code>' + d['ip'] + '</code>' if d['ip'] else '<span style="color:#8b93a1;">chưa có IP</span>'}</td>
              <td><code style="font-size:12px;">{d['mac']}</code></td>
              <td>{d['state']}{' &middot; ' + d['speed'] if d['speed'] else ''}</td>
              <td>{'<span class="tt bat">Có IP</span>' if up else '<span class="tt tat">Chưa có IP</span>'}</td>
            </tr>"""

        # --- Dich vu ---
        states = service_states([s for s, _ in SERVICES])
        svc_rows = ""
        for svc, label in SERVICES:
            st = states.get(svc, "unknown")
            if st == "active":
                tt = '<span class="tt bat">Đang chạy</span>'
            elif st == "failed":
                tt = '<span class="tt hong">Lỗi</span>'
            else:
                tt = '<span class="tt tat">Tắt</span>'
            svc_rows += (f'<li><span class="sv-t"><b>{label}</b><code>{svc}</code></span>{tt}</li>')


        # --- Suc khoe he thong + nguon ---
        h = health.snapshot()
        power_msg = power_msg_html(h)

        # Khoi suc khoe TU CAP NHAT moi 10 giay (xem /api/suckhoe + doan JS
        # cuoi trang). Chi thay so trong khoi nay, KHONG tai lai ca trang.
        health_html = f"""
        <div id="suc-khoe">{_bang_suc_khoe(h, power_msg)}</div>
        <script>
        (function() {{
          var o = document.getElementById('suc-khoe');
          if (!o) return;
          function lamMoi() {{
            fetch('/api/suckhoe', {{cache: 'no-store'}})
              .then(function(r) {{ return r.json(); }})
              .then(function(d) {{ if (d && d.html) {{ o.innerHTML = d.html; o.classList.add('lan2'); }} }})
              .catch(function() {{}});   /* mat mang thi giu so cu, khong bao loi */
          }}
          setInterval(lamMoi, 10000);
          /* Tab bi an thi KHONG do nua - quay lai thi do ngay. */
          document.addEventListener('visibilitychange', function() {{
            if (!document.hidden) lamMoi();
          }});
        }})();
        </script>"""

        from .layout import svg_icon, che_do_giao_dien
        che_do = che_do_giao_dien()

        # --- Can chu y: CHI tu so lieu that (xem can_chu_y) ---
        canh = can_chu_y(h, ports, states)
        n_van_de = sum(1 for c in canh if c[0] in ("do", "vang"))
        ccy_html = ""
        if canh:
            ccy_html = '<section class="rvg"><h2>' + ("Cần chú ý" if n_van_de else "Đang diễn ra") + '</h2><div class="ccy">' + "".join(
                f'<div class="ccy-the {muc}"><div class="bi">{svg_icon(ic)}</div>'
                f'<div class="nd"><b>{td}</b><span>{mt}</span>'
                + (f'<div class="nut"><a class="btn gray small" href="{nut[1]}">{nut[0]}</a></div>' if nut else "")
                + '</div></div>' for muc, ic, td, mt, nut in canh) + '</div></section>'

        # --- Viec hay lam: nhan so tren moi o deu dem tu du lieu that ---
        from nettools import TOOLS_READONLY, TOOLS_WRITE
        n_cong = len(ports)
        try:
            from . import pxe as _pxe
            pxe_bat = _pxe.dang_bat()
        except Exception:
            pxe_bat = False
        n_kb = _dem_kich_ban()
        n_wol = _dem_may_wol()
        chip_wifi = next((c for c in get_status_chips() if c["key"].startswith("WiFi")), None)
        viec = [
            ("term", "Console",
             (f"/phien?mo=serial-{ports[0]['devname']}" if ports else "/console"),
             (_esc(ports[0]["name"] or ports[0]["devname"]) if ports else "Chưa cắm cáp console"),
             (f"{n_cong} cổng" if n_cong else ""), ""),
            ("win", "Cài Windows qua mạng", "/deployos/kichban",
             f"{n_kb} kịch bản đã lưu" if n_kb else "Chưa có kịch bản",
             ("PXE đang bật" if pxe_bat else ""), "xanh"),
            ("net", "Công cụ mạng", "/nettools",
             f"{len(TOOLS_READONLY) + len(TOOLS_WRITE)} công cụ: ARP, ping, LLDP, DHCP…", "", ""),
            ("bolt", "Bật máy từ xa", "/deployos/caidat/wol", "Wake-on-LAN",
             (f"{n_wol} máy" if n_wol else ""), ""),
            ("list", "Phiên kết nối", "/phien", "SSH, Telnet, Serial, terminal máy này", "", ""),
            ("wifi", "WiFi / AP", "/wifi",
             (_esc(chip_wifi["extra"]) if chip_wifi else "WiFi / điểm phát"), "", ""),
            ("save", "Kho file", "/storage", "Cấu hình, firmware, file tải lên", "", ""),
            ("log", "Nhật ký", "/logs", "Nhật ký hệ thống và lỗi", "", ""),
        ]
        if che_do == "pc":
            # Che do PC: 5 o bat doi xung (o dau noi bat), vua du, khong lap lai
            dv = {v[2]: v for v in viec}
            def _bt(lop, href):
                ic, ten, hr, phu, so, _l = dv[href]
                if so:
                    phu = f"{phu} ({so})" if phu else so
                return (f'<a class="bt {lop}" href="{hr}">{svg_icon(ic)}{svg_icon("go", "i go")}'
                        f'<b>{ten}</b><span>{phu}</span></a>')
            viec_html = ('<div class="bento">'
                         + _bt("a", "/deployos/kichban")
                         + _bt("b", viec[0][2])
                         + _bt("c", "/nettools")
                         + _bt("d", "/deployos/caidat/wol")
                         + _bt("e", "/phien") + '</div>')
        else:
            viec_html = '<div class="viec">' + "".join(
                f'<a class="o-to" href="{href}">'
                + (f'<span class="nhan-so {lop}">{so}</span>' if so else "")
                + f'<span class="bi">{svg_icon(ic)}</span><b>{ten}</b><small>{phu}</small></a>'
                for ic, ten, href, phu, so, lop in viec) + '</div>'

        # --- Cai dat gan day (Lich su cai that) ---
        gan, _ls = _cai_gan_day(5)
        if gan:
            dong = ""
            for bg in gan:
                nhan, _m = _ls.TRANG_THAI.get(bg.get("trang_thai"), ("?", ""))
                may = (bg.get("ten_may") or " ".join(x for x in (bg.get("hang"), bg.get("model")) if x)
                       or bg.get("mac") or "Máy không rõ tên")
                tl = _ls.thoi_luong(bg)
                dong += (f'<a href="/deployos/lichsu"><span class="t"><b>{_esc(may)}</b>'
                         f'<small>{_ls.gio(bg.get("bat_dau"))}{" · " + tl if tl else ""}'
                         f'{" · " + _esc(bg.get("mac")) if bg.get("mac") else ""}</small></span>'
                         f'<span class="tt">{_esc(nhan)}</span></a>')
            gan_html = f'<div class="gan-day">{dong}</div>'
        else:
            gan_html = ('<div class="vazio"><h3>Chưa có lần cài Windows nào</h3>'
                        '<p>Kết quả các lần cài qua mạng sẽ được ghi lại tại đây.</p>'
                        '<a class="btn gray" href="/deployos/kichban">Mở Deployment OS</a></div>')

        # --- Phan mo dau: tra loi ngay "may co on khong" ---
        from .gioithieu import _phien_ban
        chips_mang = get_status_chips()[:2]
        mang_html = "".join(
            f'<div><dt>{_esc(c["key"])}</dt><dd class="{"" if c["up"] else "off"}">{_esc(c["val"])}'
            f'<small>{_esc(c["extra"])}</small></dd></div>' for c in chips_mang)
        link_console = (f"/phien?mo=serial-{ports[0]['devname']}" if ports else "/console")
        if n_van_de:
            h1 = f'Có <em class="canh">{n_van_de} việc</em> cần chú ý.'
            mo_ta = "Xem các mục bên dưới trước khi làm việc khác."
        else:
            h1 = 'Mọi thứ đang <em>ổn.</em>'
            mo_ta = "Nguồn điện, nhiệt độ, dịch vụ và dung lượng đều trong ngưỡng."
        hero_html = f"""
        <div class="hero rvg">
          <div>
            <h1>{h1}</h1>
            <p>{mo_ta} Phiên bản {_esc(_phien_ban())}, đã chạy {h.get('uptime', '?')}.</p>
            <div class="acts">
              <a class="btn" href="/deployos/kichban">{svg_icon("win")} Cài Windows qua mạng</a>
              <a class="btn gray" href="{link_console}">{svg_icon("term")} Mở Console</a>
            </div>
          </div>
          <dl class="net">{mang_html}</dl>
        </div>"""

        body = f"""
        {hero_html}
        {ccy_html}

        <section class="rvg">
          <h2>{"Việc hay làm" if che_do == "pc" else "Chức năng"}</h2>
          {viec_html}
        </section>

        <section class="tq-hai rvg">
          <div>
            <h2>Sức khỏe thiết bị</h2>
            {health_html}
            <p style="margin-top:14px;"><a class="btn gray" href="/power">{svg_icon("pow")} Tắt máy / Khởi động lại</a></p>
          </div>
          <div class="col">
            <div id="cong-console"><h2 style="margin-top:0;">Cổng console đang cắm</h2>{ports_html}</div>
            <div><h2 style="margin-top:0;">Cài đặt gần đây</h2>{gan_html}</div>
          </div>
        </section>

        <section class="rvg">
          <h2>Chi tiết mạng</h2>
          <div class="tbl-scroll"><table>
            <tr><th>Giao diện</th><th>Địa chỉ IP</th><th>MAC</th><th>Trạng thái</th><th style="width:130px;"></th></tr>
            {net_rows}
          </table></div>
        </section>

        <section class="rvg">
          <h2>Dịch vụ hệ thống</h2>
          <ul class="svc">{svc_rows}</ul>
        </section>
        {JS_TONG_QUAN}"""

        return render_page(body, active="/", title="Tổng quan", extra_css=CSS_TONG_QUAN, an_tieu_de=True)


    @app.route("/api/status")
    def api_status():
        """Du lieu cho thanh trang thai tu cap nhat moi 30 giay."""
        from flask import jsonify
        from .layout import get_status_chips
        return jsonify({"chips": get_status_chips()})

    @app.route("/api/suckhoe")
    def api_suc_khoe():
        """Bang suc khoe da render san - trang Tong quan goi moi 10 giay."""
        from flask import jsonify
        h = health.snapshot()
        from .layout import doi_mau_viet_cung
        return jsonify({"html": doi_mau_viet_cung(_bang_suc_khoe(h, power_msg_html(h)))})

    @app.route("/console")
    def console_danh_sach():
        """
        Trang RIENG liet ke cac cong console dang cam.

        VI SAO TACH KHOI "Tong quan": cong console la thu dung NHIEU NHAT
        khi di hien truong (cam cap vao switch/router roi mo console), nhung
        truoc day no nam lot giua trang Tong quan - phai vao Tong quan roi
        cuon qua thanh trang thai, bang dich vu... moi toi. Nay co muc rieng
        trong nhom "Ket noi thiet bi", bam 1 phat la toi.
        """
        ports = get_ports()
        if ports:
            rows = ""
            for p in ports:
                chip = (f'<br><small style="color:#8b93a1;">{_esc(p["chip"])}</small>'
                        if p.get("chip") else "")
                rows += f"""
                <tr>
                  <td><code>{p['devname']}</code>{chip}</td>
                  <td>
                    <form method="POST" action="/rename" class="row" style="gap:7px;">
                      <input type="hidden" name="devname" value="{p['devname']}">
                      <input type="text" name="name" value="{_esc(p['name'])}"
                             placeholder="Ví dụ: Switch tầng 3" style="max-width:260px;">
                      <button type="submit" class="gray small">Lưu tên</button>
                    </form>
                  </td>
                  <td><a class="btn" href="/phien?mo=serial-{p['devname']}">Mở Console</a></td>
                </tr>"""
            noi_dung = f"""
            <div class="card">
              <h3>Cổng console đang cắm</h3>
              <table>
                <tr><th style="width:150px;">Cổng</th><th>Tên gợi nhớ</th>
                    <th style="width:150px;">Thao tác</th></tr>
                {rows}
              </table>
              <p style="color:#8b93a1;font-size:13px;margin:12px 0 0;">
                Đặt tên gợi nhớ để lần sau cắm nhiều cáp cùng lúc còn biết cáp
                nào vào thiết bị nào. Tên được nhớ theo cổng.</p>
            </div>"""
        else:
            noi_dung = """
            <div class="card">
              <h3>Cổng console đang cắm</h3>
              <div class="msg warn">Chưa cắm cáp console nào. Cắm cáp USB-serial
                (FTDI / Prolific / CH340) hoặc cáp console micro-USB của Cisco
                vào máy này &mdash; trang này tự nhận, không cần khởi động lại.</div>
            </div>"""
        return render_page(noi_dung, active="/console", title="Console",
                           subtitle="Cổng serial nối tới switch / router")

    @app.route("/console/<devname>")
    def console_view(devname):
        """
        Hien console serial NGAY TRONG dashboard (giu thanh dieu huong).

        Truoc day nut nay mo thang cong 8001 o tab moi. Tren man hinh cam ung
        chay che do kiosk thi khong co thanh trinh duyet -> bam vao la ket luon,
        khong co duong quay lai. Nhung vao iframe thi thanh trai van con.
        """
        import re as _re
        if not _re.fullmatch(r"tty(USB|ACM)\d+", devname or ""):
            return render_page(
                '<div class="msg err">Tên cổng không hợp lệ.</div>'
                '<p><a class="btn" href="/">← Về trang chủ</a></p>',
                active="/", title="Console")

        if not os.path.exists(f"/dev/{devname}"):
            return render_page(
                f'<div class="msg err">Không thấy cổng <code>{devname}</code>. '
                f'Co the cap da bi rut.</div><p><a class="btn" href="/">← Về trang chủ</a></p>',
                active="/", title="Console")

        from .soanlenh import khoi_copy_terminal

        names = load_names()
        label = names.get(devname, "") or devname
        base = f"/term-console/{devname}"

        body = f"""
        <div class="row" style="margin-bottom:11px;">
          <a class="btn gray" href="/">← Về trang chủ</a>
          <a class="btn" href="{base}/" target="_blank" rel="noopener">↗ Mở toàn màn hình</a>
          <a class="btn blue" href="/nettools/console-backup?dev={devname}">🔌 Sao lưu cấu hình</a>
          <span style="color:#8b93a1;font-size:13px;align-self:center;">
            {devname} &middot; 9600 8N1
          </span>
        </div>
        <div class="card" style="padding:0;overflow:hidden;margin-bottom:12px;">
          <iframe src="{base}/" title="Console {devname}"
                  style="width:100%;height:calc(100vh - 330px);min-height:380px;border:0;display:block;background:#000;"></iframe>
        </div>
        {khoi_copy_terminal()}
        <div class="msg info">
          Cham vao khung den de go lenh. Neu dung man hinh cam ung, ban phim ao
          se hien khi cham vao o nhap lieu o cac trang khac - rieng khung console
          nay can ban phim that (cam USB) hoac dung tab Thu vien lenh de dan lenh.
        </div>"""

        html = render_page(body, active="/", title=f"Console: {label}",
                           subtitle="Cổng serial đang mở trong dashboard")
        # Bao cho ban phim ao biet go vao phien tmux nao (xem vkeyboard.js)
        return gan_phien_tmux(html, f"console-{devname}")

    return app
