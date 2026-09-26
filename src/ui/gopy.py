"""
Console Pi - tab GOP Y (26/09/2026, anh Thoai: "them 1 tab gop y ben trai,
sau khi ho gui thong tin va gop y no se sync len kho, toi se len do xem; gop
y co the gui hinh va tai lieu. Dung de ai biet thong tin gi ket noi den kho,
anh muon giu trang web do cho rieng minh").

CACH LAM:
  - Nguoi dung dien form -> luu NGAY xuong the nho (hop thu di), roi 1 luong
    nen gui len kho. Khong co mang / kho tam loi thi gop y KHONG mat: luong
    nen tu gui lai moi 5 phut. Moi gop y co ma_gui rieng -> kho bo qua ban
    trung neu Pi gui lai sau khi mat ket noi giua chung.
  - Gui toi CONG CHI GHI cua kho (/api/gop-y): nhan vao, khong tra ve gi.
    May cua khach KHONG can ket noi kho, khong co token, khong xem duoc gi.

BAO MAT (theo yeu cau anh Thoai):
  - Dia chi kho va khoa gui KHONG hien o bat ky dau tren giao dien, trang
    tai lieu, thong bao loi hay log - nguoi dung chi thay "gui toi nha phat
    trien". Trong ma nguon chung duoc che (XOR + base64) de khong lo khi
    tim chuoi (grep, strings). NOI THAT: che khong phai ma hoa - nguoi co
    ma nguon va quyet tam van giai duoc; lop bao ve that la kho chi nhan
    gop y, moi thu khac can dang nhap/token (xem gopy.py ben kho).
  - Thong tin may gui kem CHI khi nguoi dung de tick: ten may, phien ban,
    loai thiet bi - KHONG gui IP noi bo, MAC, mat khau, cau hinh.
"""

import base64
import json
import os
import platform
import re
import socket
import threading
import time
import uuid

from .duongdan import THU_MUC_DU_LIEU

THU_MUC = os.path.join(THU_MUC_DU_LIEU, "gopy")

_K = b"ConsoleSystem-gopy"
_DICH = "KxsaAxxWSnwSGxtIDkIJHB8VJkEGHAIJSCAcAQIAHwMOC14PLUAPAwZDAjwJXg0="
_KHOA = "LlorQV02EBY7KRUECBQUJQISBwEZHzY1DxxJOkwPNHI3GhM+GRspLAoYNA=="

LOAI = [("gopy", "Góp ý"), ("loi", "Báo lỗi"), ("tinhnang", "Đề xuất tính năng"),
        ("khac", "Khác")]
DUOI_HOP_LE = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".pdf", ".doc",
               ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".log", ".csv",
               ".zip", ".7z", ".rar", ".json", ".xml"}
TOI_DA_TEP = 10
TOI_DA_1_TEP = 20 * 1024 * 1024
TOI_DA_TONG = 60 * 1024 * 1024
TOI_DA_CHU = 5000
CHU_KY_GUI_LAI = 300           # giay

_khoa_gui = threading.Lock()
_su_kien = threading.Event()


def _mo(s):
    b = base64.b64decode(s)
    return bytes(c ^ _K[i % len(_K)] for i, c in enumerate(b)).decode()


def _dich():
    """Dia chi nhan gop y. Cho phep doi (vd kho chuyen may) bang file cau
    hinh rieng tren may - khong hien tren giao dien."""
    try:
        with open(os.path.join(THU_MUC_DU_LIEU, "gopy-dich.json"), encoding="utf-8") as f:
            d = json.load(f)
            if d.get("url") and d.get("khoa"):
                return d["url"], d["khoa"]
    except (OSError, ValueError):
        pass
    return _mo(_DICH), _mo(_KHOA)


def thong_tin_may():
    """Chi nhung gi giup nha phat trien hieu loi - khong IP, MAC, mat khau."""
    thiet_bi = ""
    for p in ("/proc/device-tree/model", "/sys/class/dmi/id/product_name"):
        try:
            with open(p) as f:
                thiet_bi = f.read().strip("\x00 \n")
                if thiet_bi:
                    break
        except OSError:
            pass
    phien_ban = ""
    for p in ("/opt/console-pi/VERSION",
              os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                  os.path.abspath(__file__)))), "VERSION")):
        try:
            with open(p) as f:
                phien_ban = f.read().strip()
                break
        except OSError:
            pass
    he_dieu_hanh = ""
    try:
        with open("/etc/os-release") as f:
            m = re.search(r'^PRETTY_NAME="?([^"\n]*)', f.read(), re.M)
            he_dieu_hanh = m.group(1) if m else ""
    except OSError:
        pass
    return {"ten_may": socket.gethostname(), "phien_ban": phien_ban,
            "thiet_bi": thiet_bi, "he_dieu_hanh": he_dieu_hanh,
            "kien_truc": platform.machine()}


def _ten_tep_an_toan(ten):
    goc, duoi = os.path.splitext(os.path.basename(ten or "tep"))
    goc = re.sub(r"[^A-Za-z0-9._-]", "_", goc)[:60] or "tep"
    return goc + duoi.lower()


def luu(form, files):
    """Luu 1 gop y vao hop thu di. Tra (ok, thong_bao)."""
    noi_dung = (form.get("noi_dung") or "").strip()
    if not noi_dung:
        return False, "Chưa viết nội dung góp ý."
    if len(noi_dung) > TOI_DA_CHU:
        return False, f"Nội dung dài quá {TOI_DA_CHU} ký tự."
    tep = [f for f in files if f and f.filename]
    if len(tep) > TOI_DA_TEP:
        return False, f"Tối đa {TOI_DA_TEP} tệp đính kèm."
    for f in tep:
        if os.path.splitext(f.filename)[1].lower() not in DUOI_HOP_LE:
            return False, (f'Không gửi được tệp "{f.filename}" - chỉ nhận ảnh '
                           f'(jpg, png...) và tài liệu (pdf, word, excel, txt, zip...).')
    ma = str(uuid.uuid4())
    thu_muc = os.path.join(THU_MUC, ma)
    os.makedirs(thu_muc, mode=0o700)
    ds, tong = [], 0
    try:
        for i, f in enumerate(tep):
            ten = f"{i + 1:02d}_{_ten_tep_an_toan(f.filename)}"
            kt = 0
            with open(os.path.join(thu_muc, ten), "wb") as o:
                while True:
                    k = f.stream.read(1024 * 1024)
                    if not k:
                        break
                    kt += len(k)
                    tong += len(k)
                    if kt > TOI_DA_1_TEP or tong > TOI_DA_TONG:
                        raise ValueError("Tệp quá lớn - tối đa 20 MB mỗi tệp, 60 MB tất cả.")
                    o.write(k)
            ds.append({"ten": ten, "ten_goc": os.path.basename(f.filename)[:120],
                       "kich_thuoc": kt})
    except ValueError as e:
        import shutil
        shutil.rmtree(thu_muc, ignore_errors=True)
        return False, str(e)
    loai = form.get("loai") if form.get("loai") in dict(LOAI) else "gopy"
    d = {"ma_gui": ma, "tao_luc": time.time(), "loai": loai,
         "ho_ten": (form.get("ho_ten") or "").strip()[:100],
         "lien_he": (form.get("lien_he") or "").strip()[:150],
         "noi_dung": noi_dung, "tep": ds,
         "thong_tin_may": thong_tin_may() if form.get("kem_thong_tin") else {},
         "trang_thai": "cho", "lan_thu": 0, "gui_luc": 0}
    _ghi(ma, d)
    _su_kien.set()          # danh thuc luong gui ngay
    return True, ma


def _ghi(ma, d):
    p = os.path.join(THU_MUC, ma, "gopy.json")
    tam = p + ".tmp"
    with open(tam, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tam, p)


def danh_sach(gioi_han=30):
    ra = []
    try:
        cac = os.listdir(THU_MUC)
    except OSError:
        return ra
    for ma in cac:
        try:
            with open(os.path.join(THU_MUC, ma, "gopy.json"), encoding="utf-8") as f:
                ra.append(json.load(f))
        except (OSError, ValueError):
            pass
    ra.sort(key=lambda d: -d.get("tao_luc", 0))
    return ra[:gioi_han]


def _gui_1(d):
    """Gui 1 gop y. Tra (ok, loi_de_ghi_log). KHONG dua dia chi vao loi."""
    import requests
    url, khoa = _dich()
    thu_muc = os.path.join(THU_MUC, d["ma_gui"])
    mo = []
    try:
        tep = []
        for t in d.get("tep", []):
            fh = open(os.path.join(thu_muc, t["ten"]), "rb")
            mo.append(fh)
            tep.append(("tep", (t["ten_goc"], fh)))
        du_lieu = {k: d.get(k, "") for k in ("ma_gui", "loai", "ho_ten", "lien_he", "noi_dung")}
        du_lieu["thong_tin_may"] = json.dumps(d.get("thong_tin_may") or {}, ensure_ascii=False)
        r = requests.post(url, data=du_lieu, files=tep or None,
                          headers={"X-GopY-Khoa": khoa}, timeout=180)
        if r.status_code == 200 and (r.json() or {}).get("ok"):
            return True, ""
        try:
            loi = (r.json() or {}).get("loi") or f"HTTP {r.status_code}"
        except ValueError:
            loi = f"HTTP {r.status_code}"
        return False, loi
    except Exception as e:          # mang, DNS, het gio... - thu lai sau
        return False, type(e).__name__
    finally:
        for fh in mo:
            fh.close()


def gui_cac_gop_y_cho():
    """Gui tat ca gop y dang cho. Goi tu luong nen."""
    with _khoa_gui:
        for d in danh_sach(gioi_han=1000):
            if d.get("trang_thai") == "da_gui":
                continue
            ok, loi = _gui_1(d)
            d["lan_thu"] = d.get("lan_thu", 0) + 1
            if ok:
                d["trang_thai"] = "da_gui"
                d["gui_luc"] = time.time()
                d["loi"] = ""
                # Da len kho -> xoa tep dinh kem tren the nho cho do chat
                # (giu lai noi dung + ten tep de nguoi dung xem lich su).
                for t in d.get("tep", []):
                    try:
                        os.remove(os.path.join(THU_MUC, d["ma_gui"], t["ten"]))
                    except OSError:
                        pass
            else:
                d["loi"] = loi
            _ghi(d["ma_gui"], d)


def _luong():
    while True:
        try:
            gui_cac_gop_y_cho()
        except Exception:
            pass
        _su_kien.wait(CHU_KY_GUI_LAI)
        _su_kien.clear()


_da_chay = False


def bat_luong_gui():
    global _da_chay
    if _da_chay:
        return
    _da_chay = True
    threading.Thread(target=_luong, daemon=True).start()


# ================================================================ giao dien
def register_gopy(app):
    from flask import flash, get_flashed_messages, redirect, request
    from .layout import render_page
    from html import escape as _esc

    bat_luong_gui()

    def _trang(msg="", ok=True):
        tuy_chon = "".join(f'<option value="{k}">{_esc(n)}</option>' for k, n in LOAI)
        ls = danh_sach()
        hang = ""
        for d in ls:
            luc = time.strftime("%d/%m/%Y %H:%M", time.localtime(d.get("tao_luc", 0)))
            if d.get("trang_thai") == "da_gui":
                tt = '<span style="color:#4ADE80;">&#10003; Đã gửi</span>'
            else:
                tt = ('<span style="color:#FBBF24;">Chờ gửi</span><br><small class="hint">'
                      'tự gửi khi có mạng</small>')
            so_tep = len(d.get("tep", []))
            hang += (f"<tr><td style='white-space:nowrap;'>{luc}</td>"
                     f"<td>{_esc(dict(LOAI).get(d.get('loai'), ''))}</td>"
                     f"<td>{_esc(d.get('noi_dung', '')[:140])}"
                     f"{'…' if len(d.get('noi_dung', '')) > 140 else ''}"
                     f"{f'<br><small class=hint>&#128206; {so_tep} tệp</small>' if so_tep else ''}</td>"
                     f"<td>{tt}</td></tr>")
        lich_su = (f"""<div class="card"><h3>Góp ý đã gửi từ máy này</h3>
            <div class="tbl-scroll"><table><thead><tr><th>Lúc</th><th>Loại</th>
            <th>Nội dung</th><th>Trạng thái</th></tr></thead><tbody>{hang}</tbody></table></div>
            </div>""" if ls else "")
        mau = {"ok": "ok", "err": "err"}["ok" if ok else "err"]
        body = (f'<div class="msg {mau}">{_esc(msg)}</div>' if msg else "") + f"""
        <div class="card">
          <h3>Gửi góp ý tới nhà phát triển</h3>
          <p class="hint" style="margin:0 0 12px;">Báo lỗi, đề xuất tính năng, hay bất cứ
            điều gì anh/chị muốn chúng tôi cải thiện. Có thể đính kèm ảnh chụp màn hình và
            tài liệu. Không có mạng lúc này cũng được - góp ý được lưu lại và tự gửi khi có mạng.</p>
          <form method="POST" action="/gopy" enctype="multipart/form-data" id="form-gopy">
            <div class="row" style="gap:12px;flex-wrap:wrap;">
              <div style="flex:1;min-width:200px;">
                <label>Họ tên</label>
                <input type="text" name="ho_ten" maxlength="100" placeholder="Không bắt buộc">
              </div>
              <div style="flex:1;min-width:200px;">
                <label>Số điện thoại / email để liên hệ lại</label>
                <input type="text" name="lien_he" maxlength="150" placeholder="Không bắt buộc">
              </div>
              <div style="min-width:180px;">
                <label>Loại</label>
                <select name="loai">{tuy_chon}</select>
              </div>
            </div>
            <label style="margin-top:10px;display:block;">Nội dung</label>
            <textarea name="noi_dung" rows="6" maxlength="{TOI_DA_CHU}" required
                      placeholder="Mô tả chi tiết: đang làm gì, bấm vào đâu, thấy lỗi gì..."
                      style="width:100%;max-width:100%;box-sizing:border-box;"></textarea>
            <label style="margin-top:10px;display:block;">Ảnh / tài liệu đính kèm
              (tối đa {TOI_DA_TEP} tệp, mỗi tệp 20 MB)</label>
            <input type="file" name="tep" multiple id="o-tep"
                   accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.log,.csv,.zip,.7z,.rar,.json,.xml">
            <div id="ds-tep" class="hint" style="margin-top:6px;"></div>
            <label style="display:flex;gap:8px;align-items:center;margin-top:12px;font-size:13.5px;">
              <input type="checkbox" name="kem_thong_tin" value="1" checked style="width:auto;">
              Gửi kèm thông tin máy (tên máy, phiên bản phần mềm, loại thiết bị) để chúng tôi
              tìm lỗi nhanh hơn - không gồm địa chỉ mạng hay mật khẩu.
            </label>
            <button type="submit" style="margin-top:14px;" data-busy="Đang gửi...">Gửi góp ý</button>
          </form>
        </div>
        {lich_su}
        <script>
        (function() {{
          var o = document.getElementById('o-tep'), ds = document.getElementById('ds-tep');
          function co(n) {{ return n > 1048576 ? (n / 1048576).toFixed(1) + ' MB' : Math.ceil(n / 1024) + ' KB'; }}
          o.addEventListener('change', function() {{
            var h = [], tong = 0, loi = '';
            for (var i = 0; i < o.files.length; i++) {{
              var f = o.files[i]; tong += f.size;
              if (f.size > {TOI_DA_1_TEP}) loi = '"' + f.name + '" lớn hơn 20 MB.';
              h.push(f.name + ' (' + co(f.size) + ')');
            }}
            if (o.files.length > {TOI_DA_TEP}) loi = 'Tối đa {TOI_DA_TEP} tệp.';
            if (tong > {TOI_DA_TONG}) loi = 'Tổng dung lượng quá 60 MB.';
            ds.innerHTML = h.join('<br>') + (loi ? '<div style="color:#F87171;">' + loi + '</div>' : '');
          }});
        }})();
        </script>"""
        return render_page(body, active="/gopy", title="Góp ý",
                           subtitle="Gửi góp ý, báo lỗi, đề xuất tính năng")

    @app.route("/gopy")
    def gopy_trang():
        tb = get_flashed_messages()
        return _trang(tb[0] if tb else "")

    @app.route("/gopy", methods=["POST"])
    def gopy_gui():
        ok, kq = luu(request.form, request.files.getlist("tep"))
        if not ok:
            return _trang(kq, False)
        # Doi toi da ~10 giay xem chinh gop y nay da len kho chua (mang tot
        # thi bao "da gui" ngay; khong thi bao ro la se tu gui sau).
        p = os.path.join(THU_MUC, kq, "gopy.json")
        da_gui = False
        for _ in range(20):
            time.sleep(0.5)
            try:
                with open(p, encoding="utf-8") as f:
                    d = json.load(f)
            except (OSError, ValueError):
                continue
            if d.get("trang_thai") == "da_gui":
                da_gui = True
                break
            if d.get("lan_thu"):
                break           # da thu 1 lan va that bai -> khong doi them
        flash("Cảm ơn anh/chị! Góp ý đã được gửi tới nhà phát triển." if da_gui else
              "Đã lưu góp ý. Máy chưa gửi được lúc này - sẽ tự gửi khi có mạng.")
        return redirect("/gopy")
