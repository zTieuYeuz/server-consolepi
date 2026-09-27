"""
Console System - nhan dien thuong hieu zTieuYeuz + phan "Gioi thieu".

- /thuong-hieu/<file> : logo, favicon (CONG KHAI - trang dang nhap can hien
  logo truoc khi co phien dang nhap). Chi phuc vu dung cac file trong danh
  sach cho phep, khong nhan duong dan tuy y.
- khoi_gioi_thieu()   : the "Gioi thieu" dung chung cho trang Cai dat va
  trang Tai lieu (tac gia, phien ban, ban quyen, lien ket trang huong dan).

(c) 2026 zTieuYeuz - Console System. Moi quyen duoc bao luu.
"""
import os

from flask import abort, send_file

THU_MUC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "branding")
TAC_GIA = "zTieuYeuz"
TRANG_TAI_LIEU = "https://console-docs.home-server.id.vn"
FILE_CONG_KHAI = {
    "logo-mark.svg": "image/svg+xml",
    "logo-full.svg": "image/svg+xml",
    "logo-full-nen-sang.svg": "image/svg+xml",
    "logo-mark-256.png": "image/png",
    "logo-mark-64.png": "image/png",
    "logo-mark-32.png": "image/png",
    "favicon.ico": "image/x-icon",
}
DUONG_CONG_KHAI = {f"/thuong-hieu/{f}" for f in FILE_CONG_KHAI} | {"/favicon.ico"}


# ---------------------------------------------------------------- dau an an
# Dau an ban quyen AN (yeu cau 27/09/2026: "danh dau an trong ma"):
#  - dau_an_an(): chuoi KY TU KHONG RONG (U+200B/U+200C) ma hoa tung bit cua
#    "zTieuYeuz", chen vao chu "(c) 2026" o chan trang, trang dang nhap...
#    Nhin khong thay, nhung chep/dan giao dien sang noi khac van mang theo ->
#    doc lai bang tools/kiem-dau-an.py de chung minh nguon goc.
#  - MA_NHAN_DIEN: hex cua "zTieuYeuz|ConsoleSystem" - xuat hien trong CSS moi
#    trang (bien --zt) va trong header phan hoi; tim chuoi nay tren mang la
#    ra ban sao chep.
_KY_0, _KY_1 = "\u200b", "\u200c"
MA_NHAN_DIEN = "7a546965755965757a7c436f6e736f6c6553797374656d"


def dau_an_an(chu="zTieuYeuz"):
    bit = "".join(f"{b:08b}" for b in chu.encode())
    return "\u2060" + "".join(_KY_1 if c == "1" else _KY_0 for c in bit) + "\u2060"


def _phien_ban():
    for p in ("/opt/console-pi/VERSION",
              os.path.join(os.path.dirname(THU_MUC), "..", "VERSION")):
        try:
            return open(p).read().strip()
        except OSError:
            continue
    return "?"


def khoi_gioi_thieu():
    """The Gioi thieu: logo, san pham, tac gia, ban quyen, nut mo tai lieu."""
    return f"""
    <div class="card gt-the">
      <img src="/thuong-hieu/logo-full.svg" alt="zTieuYeuz - Console System" class="gt-logo">
      <p class="gt-mo">Bộ công cụ cho kỹ sư mạng: cấu hình thiết bị qua cổng console, SSH/Telnet,
        công cụ chẩn đoán mạng và cài Windows hàng loạt qua mạng (PXE) - tất cả trong một
        thiết bị nhỏ gọn, dùng ngay trên trình duyệt.</p>
      <table class="gt-bang">
        <tr><th>Sản phẩm</th><td>Console System</td></tr>
        <tr><th>Phiên bản</th><td><code>{_phien_ban()}</code></td></tr>
        <tr><th>Phát triển bởi</th><td><b class="gt-ten"><span>z</span>TieuYeu<span>z</span></b></td></tr>
        <tr><th>Bản quyền</th><td>&copy; 2026 {TAC_GIA}. Mọi quyền được bảo lưu.</td></tr>
      </table>
      <div class="row" style="margin-top:14px;">
        <a class="btn" href="{TRANG_TAI_LIEU}" target="_blank" rel="noopener">📖 Mở trang hướng dẫn sử dụng</a>
      </div>
      <p class="hint" style="margin-top:10px;">Trang hướng dẫn: <code>{TRANG_TAI_LIEU.split("//", 1)[1]}</code>
        - cần có Internet. Máy không có mạng thì mở địa chỉ này trên điện thoại.</p>
    </div>"""


CSS_GIOI_THIEU = """
.gt-the .gt-logo{height:64px;width:auto;display:block;margin:2px 0 12px;}
.gt-the .gt-mo{color:var(--chu-mo);font-size:13.5px;max-width:640px;margin:0 0 12px;line-height:1.55;}
.gt-bang{max-width:520px;} .gt-bang th{width:150px;}
.gt-ten{font-size:15px;letter-spacing:.2px;} .gt-ten span{color:#22D3EE;}
"""


def register_gioithieu(app):
    @app.route("/thuong-hieu/<ten>")
    def thuong_hieu(ten):
        if ten not in FILE_CONG_KHAI:
            abort(404)
        r = send_file(os.path.join(THU_MUC, ten), mimetype=FILE_CONG_KHAI[ten], max_age=86400)
        r.headers["X-Content-Type-Options"] = "nosniff"
        return r

    @app.after_request
    def _gan_ma_nhan_dien(resp):
        resp.headers.setdefault("X-CS-ID", MA_NHAN_DIEN)
        return resp

    @app.route("/favicon.ico")
    def favicon():
        return send_file(os.path.join(THU_MUC, "favicon.ico"), mimetype="image/x-icon", max_age=86400)

    return app
