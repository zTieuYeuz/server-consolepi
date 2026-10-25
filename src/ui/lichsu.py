# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console System - LICH SU CAI DAT tung may (bien ban ban giao).

VI SAO (anh Thoai 14/10/2026, muc 6 "lich su + bao cao tung may"): di cai hang loat cho
cong ty thi can biet may nao (MAC, serial, hang, model) da cai luc nao, bang kich ban
nao, thanh cong hay loi o buoc nao - va xuat ra CSV gui khach lam bien ban. Trang Tien
trinh (ui/tiendo.py) chi giu 20 may gan nhat va chi bat dau tu luc Windows dang nhap
lan dau; nay ghi tu LUC MAY CHON KICH BAN.

DU LIEU DEN TU 3 CHO (khong phai doan, moi cho la 1 diem chac chan co):
  1. iPXE - luc may chon kich ban trong menu, iPXE tai them 1 file nho "cs-may.cmd" voi
     URL chua MAC + hang + model + serial doc tu SMBIOS (bien ${manufacturer}...).
     Pi tao ban ghi, tra ve `set CS_LS=<ma>` (+ danh sach goi driver hop model - xem
     ui/drivermodel.py). iPXE la noi DUY NHAT doc SMBIOS ma khong can driver/WMI gi.
     Gia tri ma hoa hexraw trong DUONG DAN (khong dung query string): ten file wimboot
     lay theo cuoi URL, va hex chi co [0-9a-f] - khong bao gio vo URL.
  2. WinPE (deploy.cmd) - ghi 1 file .txt vao share Samba [cs-lich-su] khi bung xong
     (XONG) hoac khi loi (LOI=<buoc>). Giong share [cs-o-dia]: chi nhan .txt nho.
  3. Windows (tien-trinh.ps1) - goi /api/tiendo/* kem ma "ls" (deploy.cmd chep ma vao
     C:\\ConsolePi\\ls-id.txt) -> cap nhat ten may, so buoc xong/loi, luc xong.
"""
import csv
import io
import json
import os
import re
import secrets
import threading
import time

from .duongdan import THU_MUC_DU_LIEU
from consolesystem.core.esc import esc_html_rong as _esc

FILE_LUU = os.path.join(THU_MUC_DU_LIEU, "lich-su-cai.json")
THU_MUC_BAO = os.path.join(THU_MUC_DU_LIEU, "lich-su-bao")   # share [cs-lich-su]
TEN_SHARE = "cs-lich-su"
GIU_TOI_DA = 2000          # ban ghi - vai trieu byte, du cho ca nam cai may
MAX_BYTE_BAO = 64 * 1024

_khoa = threading.Lock()

TRANG_THAI = {
    "winpe": ("Đang cài (WinPE)", "#f59e0b"),
    "loi_winpe": ("Lỗi khi cài", "#ff6b6b"),
    "windows": ("Đang cấu hình Windows", "#38bdf8"),
    "xong": ("Xong", "#4CAF50"),
    "xong_co_loi": ("Xong, có bước lỗi", "#f59e0b"),
}

_RE_MA = re.compile(r"^[a-z0-9]{8,16}$")
_RE_MAC = re.compile(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$")


# ------------------------------------------------------------------ luu tru
def _doc():
    try:
        with open(FILE_LUU, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _ghi(ds):
    try:
        os.makedirs(THU_MUC_DU_LIEU, exist_ok=True)
        tam = FILE_LUU + ".tmp"
        with open(tam, "w", encoding="utf-8") as f:
            json.dump(ds[-GIU_TOI_DA:], f, ensure_ascii=False)
        os.replace(tam, FILE_LUU)
    except OSError:
        pass


def giai_hex(s, dai=80):
    """Gia tri iPXE `:hexraw` -> chuoi. iPXE cho rong neu may khong khai SMBIOS do. Bo ky
    tu dieu khien; hang dien rac kieu "To Be Filled By O.E.M." / "Default string" -> rong."""
    s = (s or "").strip().lower()
    if s.startswith("x"):
        s = s[1:]
    if not s or len(s) % 2 or not re.fullmatch(r"[0-9a-f]*", s):
        return ""
    try:
        t = bytes.fromhex(s[:dai * 2]).decode("utf-8", "replace")
    except ValueError:
        return ""
    t = re.sub(r"[\x00-\x1f\x7f]", "", t).strip()
    if t.lower() in ("to be filled by o.e.m.", "default string", "system product name",
                     "system manufacturer", "not specified", "none", "0", "123456789"):
        return ""
    return t[:dai]


def chuan_mac(s):
    """MAC tu iPXE (`${mac:hexraw}` = 12 hex) hoac nguoi dung go -> aa:bb:cc:dd:ee:ff."""
    h = re.sub(r"[^0-9a-f]", "", (s or "").lower())
    if len(h) != 12:
        return ""
    return ":".join(h[i:i + 2] for i in range(0, 12, 2))


def bat_dau(ip, mac, hang, model, phien_ban, serial, nen_tang, kichban, os_id="",
            driver=None):
    """Tao ban ghi khi iPXE tai cs-may.cmd. Tra ve ma ban ghi."""
    ma = secrets.token_hex(5)
    bg = {
        "id": ma, "bat_dau": time.time(), "cap_nhat": time.time(),
        "ip": str(ip or "")[:45], "mac": chuan_mac(mac),
        "hang": hang, "model": model, "phien_ban": phien_ban, "serial": serial,
        "nen_tang": "UEFI" if nen_tang == "efi" else ("BIOS" if nen_tang == "pcbios" else ""),
        "kichban": str(kichban or "")[:120], "os": str(os_id or "")[:80],
        "driver": list(driver or [])[:20],
        "trang_thai": "winpe", "loi": "", "ten_may": "",
        "so_xong": 0, "so_loi": 0, "tong": 0, "xong_luc": None,
    }
    with _khoa:
        ds = _doc()
        ds.append(bg)
        _ghi(ds)
    return ma


def _sua(ma, ham):
    with _khoa:
        ds = _doc()
        for bg in reversed(ds):
            if bg.get("id") == ma:
                ham(bg)
                bg["cap_nhat"] = time.time()
                _ghi(ds)
                return True
    return False


def tu_tiendo(ma, ten_may="", so_xong=None, so_loi=None, tong=None, xong=False):
    """Windows bao tien trinh (ui/tiendo.py) kem ma ban ghi."""
    if not _RE_MA.match(ma or ""):
        return False

    def ham(bg):
        if ten_may:
            bg["ten_may"] = str(ten_may)[:64]
        for k, v in (("so_xong", so_xong), ("so_loi", so_loi), ("tong", tong)):
            if v is not None:
                bg[k] = int(v)
        if bg.get("trang_thai") in ("winpe", "windows"):
            bg["trang_thai"] = "windows"
        if xong:
            bg["xong_luc"] = time.time()
            bg["trang_thai"] = "xong_co_loi" if bg.get("so_loi") else "xong"
    return _sua(ma, ham)


def nap_bao_winpe():
    """Doc cac file deploy.cmd ghi vao share [cs-lich-su] roi xoa. Goi moi lan xem trang
    (vai file nho - khong can tien trinh nen). Ten file = <ma>.txt."""
    try:
        cac = os.listdir(THU_MUC_BAO)
    except OSError:
        return 0
    n = 0
    for f in cac:
        p = os.path.join(THU_MUC_BAO, f)
        ma = f[:-4].lower() if f.lower().endswith(".txt") else ""
        try:
            if not _RE_MA.match(ma) or os.path.getsize(p) > MAX_BYTE_BAO:
                os.remove(p)
                continue
            with open(p, encoding="utf-8", errors="replace") as fh:
                nd = fh.read()
            luc = os.path.getmtime(p)
        except OSError:
            continue
        dong = [x.strip() for x in nd.replace("\r", "").split("\n") if x.strip()]
        loi = next((x[4:].strip() for x in dong if x.upper().startswith("LOI=")), "")
        xong = any(x.upper() == "XONG" for x in dong)
        # deploy.cmd them nguyen dong `reg query ... SystemProductName` (khong qua bien cmd
        # - ten model co the chua & ) ...): "    SystemProductName    REG_SZ    <model>"
        model_pe = next((m.group(1).strip() for m in (
            re.search(r"SystemProductName\s+REG_SZ\s+(.+)", x) for x in dong) if m), "")

        def ham(bg, loi=loi, xong=xong, model_pe=model_pe, luc=luc):
            if loi:
                bg["trang_thai"] = "loi_winpe"
                bg["loi"] = loi[:200]
            elif xong and bg.get("trang_thai") == "winpe":
                bg["trang_thai"] = "windows"
            bg["winpe_xong_luc"] = luc
            if model_pe and not bg.get("model"):
                bg["model"] = model_pe[:80]
        _sua(ma, ham)          # ma khong con (da xoa khoi lich su) -> van bo file
        try:
            os.remove(p)
        except OSError:
            pass
        n += 1
    return n


def danh_sach(tim=""):
    nap_bao_winpe()
    with _khoa:
        ds = _doc()
    ds.reverse()
    tim = (tim or "").strip().lower()
    if tim:
        ds = [b for b in ds if tim in " ".join(str(b.get(k) or "") for k in (
            "mac", "hang", "model", "phien_ban", "serial", "kichban", "ten_may", "ip",
            "loi")).lower()]
    return ds


def xoa(cac_ma):
    cac_ma = set(cac_ma or [])
    with _khoa:
        ds = _doc()
        moi = [b for b in ds if b.get("id") not in cac_ma]
        _ghi(moi)
    return len(ds) - len(moi)


def xoa_het():
    with _khoa:
        n = len(_doc())
        _ghi([])
    return n


def may_da_biet():
    """MAC -> ban ghi moi nhat (cho trang Bat may tu xa)."""
    ra = {}
    for b in danh_sach():
        if b.get("mac") and b["mac"] not in ra:
            ra[b["mac"]] = b
    return ra


def gio(t):
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(t)) if t else ""


def thoi_luong(b):
    het = b.get("xong_luc") or b.get("winpe_xong_luc")
    if not het:
        return ""
    phut = int((het - b.get("bat_dau", het)) // 60)
    return f"{phut // 60} giờ {phut % 60} phút" if phut >= 60 else f"{phut} phút"


def xuat_csv(ds):
    """CSV mo duoc bang Excel (UTF-8 co BOM, dau phay)."""
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Bắt đầu", "Xong lúc", "Thời gian", "Trạng thái", "Lỗi", "Tên máy",
                "Hãng", "Model", "Dòng máy", "Serial", "MAC", "IP lúc cài", "Firmware",
                "Kịch bản", "Hệ điều hành", "Bước xong", "Bước lỗi", "Tổng bước",
                "Gói driver theo model"])
    for b in ds:
        w.writerow([gio(b.get("bat_dau")), gio(b.get("xong_luc")), thoi_luong(b),
                    TRANG_THAI.get(b.get("trang_thai"), ("?",))[0], b.get("loi", ""),
                    b.get("ten_may", ""), b.get("hang", ""), b.get("model", ""),
                    b.get("phien_ban", ""), b.get("serial", ""), b.get("mac", ""),
                    b.get("ip", ""), b.get("nen_tang", ""), b.get("kichban", ""),
                    b.get("os", ""), b.get("so_xong", 0), b.get("so_loi", 0),
                    b.get("tong", 0), " ".join(b.get("driver") or [])])
    return "\ufeff" + out.getvalue()


# ------------------------------------------------------------- noi dung cho WinPE
def sinh_cs_may_cmd(ma, cac_driver, ten_may=None):
    """File chen vao WinPE qua wimboot (X:\\Windows\\System32\\cs-may.cmd) - deploy.cmd
    `call` no. Chi chua ma ban ghi + ten thu muc driver (da loc ky tu an toan) + (1.9.4) ten may
    da tinh san cho che do serial/CSV/ngau nhien (chi nhan [A-Za-z0-9-], toi da 15 ky tu)."""
    an_toan = [d for d in (cac_driver or []) if re.fullmatch(r"[A-Za-z0-9._-]{1,120}", d)]
    ra = ("@echo off\r\n"
          f"set CS_LS={ma}\r\n"
          f"set CS_DRV={' '.join(an_toan)}\r\n")
    if ten_may and re.fullmatch(r"[A-Za-z0-9-]{1,15}", ten_may):
        ra += f"set CS_TENMAY={ten_may}\r\n"
    return ra


def dat_ten(ma, ten_may):
    """Ghi ten may da tinh san vao dong lich su (hien ngay o trang Lich su, truoc khi Windows bao ve)."""
    if not _RE_MA.match(ma or "") or not ten_may:
        return False

    def ham(bg):
        bg["ten_may"] = str(ten_may)[:64]
    return _sua(ma, ham)


def ten_dang_dung():
    """Cac ten may da co trong lich su (de ten ngau nhien khong trung may khac)."""
    return [str(b.get("ten_may") or "") for b in _doc() if b.get("ten_may")]


# ---------------------------------------------------------------- giao dien
def register_lichsu(app):
    from flask import Response, redirect, request
    from .layout import render_page
    from . import deployos as _d
    import html as _h


    @app.route("/deployos/lichsu")
    def deployos_lichsu():
        tim = request.args.get("tim", "")
        ds = danh_sach(tim)
        hang = ""
        for b in ds:
            nhan, mau = TRANG_THAI.get(b.get("trang_thai"), ("?", "#8b93a1"))
            ten = " ".join(x for x in (b.get("hang"), b.get("model")) if x) or "—"
            may = _esc(ten)
            if b.get("phien_ban") and b["phien_ban"] not in ten:
                may += f' <small style="color:#8b93a1;">({_esc(b["phien_ban"])})</small>'
            buoc = (f'{b.get("so_xong", 0)}/{b.get("tong", 0)}'
                    + (f' <span style="color:#ff6b6b;">({b["so_loi"]} lỗi)</span>'
                       if b.get("so_loi") else "")) if b.get("tong") else ""
            loi = (f'<br><small style="color:#ff6b6b;">{_esc(b["loi"])}</small>'
                   if b.get("loi") else "")
            drv = (f'<br><small style="color:#8b93a1;">Driver: {_esc(", ".join(b["driver"]))}</small>'
                   if b.get("driver") else "")
            hang += f"""<tr>
              <td><input type="checkbox" name="ma" value="{_esc(b['id'])}" form="ls-xoa"></td>
              <td>{_esc(gio(b.get('bat_dau')))}<br><small style="color:#8b93a1;">{_esc(thoi_luong(b))}</small></td>
              <td><strong>{_esc(b.get('ten_may') or '—')}</strong><br>
                  <small style="color:#8b93a1;">{_esc(b.get('mac'))} · {_esc(b.get('nen_tang'))}</small></td>
              <td>{may}<br><small style="color:#8b93a1;">S/N: {_esc(b.get('serial') or '—')}</small>{drv}</td>
              <td>{_esc(b.get('kichban'))}</td>
              <td><span style="color:{mau};">{_esc(nhan)}</span> {buoc}{loi}</td>
            </tr>"""
        if ds:
            bang = f"""
            <div class="tbl-scroll"><table data-pt="25">
              <tr><th style="width:28px;"><input type="checkbox" id="ls-tat-ca" title="Chọn cả trang"></th>
                  <th>Bắt đầu</th><th>Máy</th><th>Hãng / model</th><th>Kịch bản</th><th>Kết quả</th></tr>
              {hang}
            </table></div>
            <form id="ls-xoa" method="POST" action="/deployos/lichsu/xoa"
                  onsubmit="return confirm('Xóa các dòng đã chọn khỏi lịch sử?');" style="margin-top:10px;">
              <button type="submit" class="red small">Xóa các dòng đã chọn</button>
            </form>
            <script>
            (function() {{
              var t = document.getElementById('ls-tat-ca');
              if (t) t.addEventListener('change', function() {{
                document.querySelectorAll('input[name=ma][form=ls-xoa]').forEach(function(c) {{
                  if (!c.closest('tr').classList.contains('pt-an')) c.checked = t.checked; }});
              }});
            }})();
            </script>"""
        else:
            bang = ('<p style="color:#8b93a1;">Chưa có máy nào' +
                    (' khớp từ khóa tìm.' if tim else
                     ' &mdash; máy chọn kịch bản trong menu PXE sẽ tự hiện ở đây.') + '</p>')
        csv_url = "/deployos/lichsu/csv" + (f"?tim={_esc(tim)}" if tim else "")
        body = _d.tabs_deployos("tiendo", "lichsu") + f"""
        <div class="card">
          <p style="color:#8b93a1;font-size:13.5px;margin:0 0 10px;">
            Mỗi máy chọn kịch bản trong menu PXE được ghi lại: MAC, hãng, model, serial
            (đọc từ BIOS máy), kịch bản, lúc bắt đầu/xong và kết quả. Dùng làm biên bản
            bàn giao: tìm theo tên máy/serial/model rồi bấm <strong>Xuất CSV</strong>
            (mở bằng Excel).</p>
          <form method="GET" action="/deployos/lichsu" class="row" style="gap:8px;flex-wrap:wrap;">
            <input type="text" name="tim" value="{_esc(tim)}" placeholder="Tìm MAC, serial, model, tên máy, kịch bản...">
            <button type="submit">Tìm</button>
            <a class="btn gray" href="{csv_url}">Xuất CSV ({len(ds)} dòng)</a>
          </form>
        </div>
        <h2>Máy đã cài ({len(ds)})</h2>
        {bang}"""
        if "data-pt=" in body:
            body += _d.JS_PHAN_TRANG_CHUNG
        return render_page(body, active="/deployos", title="Lịch sử cài đặt",
                           subtitle="Biên bản từng máy đã cài qua PXE", extra_css=_d.CSS_CHUNG)

    @app.route("/deployos/lichsu/csv")
    def deployos_lichsu_csv():
        ds = danh_sach(request.args.get("tim", ""))
        ten = time.strftime("lich-su-cai-dat-%Y%m%d-%H%M.csv")
        return Response(xuat_csv(ds), mimetype="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{ten}"'})

    @app.route("/deployos/lichsu/xoa", methods=["POST"])
    def deployos_lichsu_xoa():
        xoa(request.form.getlist("ma"))
        return redirect("/deployos/lichsu")
