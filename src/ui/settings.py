"""
Console Pi - Tab Cai dat (yeu cau so 3: nut xoay man hinh)

Xoay man hinh dung wlr-randr noi vao compositor cage dang chay. Luu lua chon
vao config de kiosk-start.sh tu ap dung lai moi lan khoi dong.
"""
import json
import os
import subprocess

from flask import request

from .layout import render_page
from .terminal import load_config, save_config, get_term_credential

ROTATIONS = [
    ("normal", "0° - Binh thuong"),
    ("90", "90° - Xoay phai"),
    ("180", "180° - Lat nguoc"),
    ("270", "270° - Xoay trai"),
]

WAYLAND_ENV = {
    "WAYLAND_DISPLAY": "wayland-0",
    "XDG_RUNTIME_DIR": "/run/user/1000",
}


def _wlr(args, timeout=10):
    """Chay wlr-randr duoi quyen user dang giu phien Wayland (administrator)."""
    # Flask chay quyen root, nhung phien Wayland thuoc user administrator,
    # nen phai ha quyen va dat dung WAYLAND_DISPLAY/XDG_RUNTIME_DIR.
    full = ["sudo", "-n", "-u", "administrator",
            "env", f"WAYLAND_DISPLAY={WAYLAND_ENV['WAYLAND_DISPLAY']}",
            f"XDG_RUNTIME_DIR={WAYLAND_ENV['XDG_RUNTIME_DIR']}",
            "wlr-randr"] + args
    try:
        r = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, (r.stdout + r.stderr)
    except FileNotFoundError:
        return False, "Chưa cài wlr-randr."
    except Exception as e:
        return False, str(e)


def get_display_info():
    """Tra ve (co_man_hinh, ten_output, transform_hien_tai, raw)."""
    ok, out = _wlr([])
    if not ok or not out.strip():
        return False, "", "", out
    name = ""
    transform = "normal"
    for line in out.splitlines():
        if line and not line.startswith((" ", "\t")):
            name = line.split()[0]
        s = line.strip()
        if s.lower().startswith("transform:"):
            transform = s.split(":", 1)[1].strip()
    return bool(name), name, transform, out


def set_rotation(value):
    ok_info, name, _, _ = get_display_info()
    if not ok_info:
        return False, ("Không tìm thấy màn hình đang hoạt động. "
                       "Thiết bị này có thể không gắn màn hình, hoặc kiosk chưa chạy.")
    ok, out = _wlr(["--output", name, "--transform", value])
    if not ok:
        return False, f"Xoay thất bại: {out.strip()[:200]}"

    cfg = load_config()
    cfg["screen_rotation"] = value
    save_config(cfg)

    # Ghi them ra file rieng cho kiosk-start.sh doc duoc.
    # config.json chmod 600 thuoc root (giau mat khau terminal), ma kiosk
    # chay duoi quyen user -> khong doc noi. Huong man hinh khong phai bi
    # mat nen tach ra file 644 rieng.
    try:
        with open(ROTATION_FILE, "w") as f:
            f.write(value + "\n")
        os.chmod(ROTATION_FILE, 0o644)
    except Exception:
        pass

    # Xoay toa do cam ung cho khop - bat buoc, neu khong se cham khong trung
    touch_ok = sync_touch_matrix(value)
    extra = (" Toa do cam ung da xoay theo, kiosk dang khoi dong lai."
             if touch_ok else
             " CANH BAO: khong cap nhat duoc toa do cam ung, cham se khong trung.")
    return True, f"Đã xoay màn hình sang {value}.{extra}"



# Ma tran hieu chinh toa do cam ung cho tung goc xoay.
#
# DA KIEM CHUNG THUC TE tren may nay: cage/wlroots KHONG tu xoay toa do cam
# ung theo huong man hinh. Xoay man ma khong doi ma tran thi cham khong trung
# nut va vuot nguoc chieu. Hai thu nay phai LUON di cung nhau.
TOUCH_MATRIX = {
    "normal": "1 0 0 0 1 0",
    "90":     "0 -1 1 1 0 0",
    "180":    "-1 0 1 0 -1 1",
    "270":    "0 1 0 -1 0 1",
}

UDEV_RULE_FILE = "/etc/udev/rules.d/99-consolepi-touch.rules"
ROTATION_FILE = "/opt/console-pi/screen-rotation"


def sync_touch_matrix(rotation):
    """Cap nhat ma tran cam ung cho khop huong man hinh vua chon."""
    matrix = TOUCH_MATRIX.get(rotation, TOUCH_MATRIX["normal"])
    rule = (
        "# Console Pi - tu sinh khi doi huong man hinh trong tab Cai dat.\n"
        "# cage/wlroots khong tu xoay toa do cam ung nen phai chinh o day.\n"
        f"# Hướng hiện tại: {rotation}\n"
        f'ENV{{ID_INPUT_TOUCHSCREEN}}=="1", ENV{{LIBINPUT_CALIBRATION_MATRIX}}="{matrix}"\n'
    )
    try:
        with open(UDEV_RULE_FILE, "w") as f:
            f.write(rule)
        subprocess.run(["udevadm", "control", "--reload-rules"],
                       capture_output=True, timeout=10)
        subprocess.run(["udevadm", "trigger", "--subsystem-match=input",
                        "--action=change"], capture_output=True, timeout=10)
        # cage chi doc cau hinh thiet bi luc MO thiet bi -> phai restart kiosk
        subprocess.run(["systemctl", "restart", "console-pi-kiosk"],
                       capture_output=True, timeout=30)
        return True
    except Exception:
        return False


def register_settings(app):
    @app.route("/settings")
    def settings_page():
        return _render_settings()

    @app.route("/settings/rotate", methods=["POST"])
    def settings_rotate():
        val = request.form.get("rotation", "normal")
        if val not in [r[0] for r in ROTATIONS]:
            return _render_settings(msg="Giá trị xoay không hợp lệ.", ok=False)
        ok, msg = set_rotation(val)
        return _render_settings(msg=msg, ok=ok)

    @app.route("/settings/kiosk/bat", methods=["POST"])
    def settings_kiosk_bat():
        import subprocess
        try:
            r = subprocess.run(
                ["systemctl", "enable", "--now",
                 "console-pi-kiosk", "console-pi-kiosk-helper"],
                capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return _render_settings(
                    msg="Đã bật giao diện màn hình. Nhìn vào màn hình của máy "
                        "này sẽ thấy dashboard sau vài giây.", ok=True)
            return _render_settings(
                msg=f"Không bật được: {(r.stderr or r.stdout)[:200]}", ok=False)
        except Exception as e:
            return _render_settings(msg=f"Không bật được: {e}", ok=False)

    @app.route("/settings/kiosk/tat", methods=["POST"])
    def settings_kiosk_tat():
        import subprocess
        try:
            r = subprocess.run(
                ["systemctl", "disable", "--now",
                 "console-pi-kiosk", "console-pi-kiosk-helper"],
                capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                return _render_settings(
                    msg="Đã tắt giao diện màn hình, lấy lại RAM cho máy.", ok=True)
            return _render_settings(
                msg=f"Không tắt được: {(r.stderr or r.stdout)[:200]}", ok=False)
        except Exception as e:
            return _render_settings(msg=f"Không tắt được: {e}", ok=False)

    @app.route("/settings/don-rac", methods=["POST"])
    def settings_don_rac():
        from . import baotri as bt
        ok, msg = bt.don_rac(request.form.get("ma", ""))
        return _render_settings(msg=msg, ok=ok)

    @app.route("/settings/sao-luu")
    def settings_sao_luu():
        from flask import Response
        from . import baotri as bt
        du, ten = bt.tao_ban_sao_luu()
        return Response(du, mimetype="application/gzip", headers={
            "Content-Disposition": f'attachment; filename="{ten}"'})

    @app.route("/settings/nap-sao-luu", methods=["POST"])
    def settings_nap_sao_luu():
        from . import baotri as bt
        f = request.files.get("file")
        if not f or not getattr(f, "filename", ""):
            return _render_settings(msg="Chưa chọn file sao lưu.", ok=False)
        ok, msg = bt.nap_ban_sao_luu(f.read())
        return _render_settings(msg=msg, ok=ok)

    @app.route("/settings/regen-term-pass", methods=["POST"])
    def regen_term_pass():
        import secrets
        cfg = load_config()
        cfg["terminal_auth"] = "console:" + secrets.token_urlsafe(12)
        save_config(cfg)
        for svc in ("console-pi-term-local", "console-pi-term-ssh"):
            subprocess.run(["systemctl", "restart", svc], capture_output=True, timeout=20)
        return _render_settings(msg="Đã đổi mật khẩu terminal và khởi động lại dịch vụ.", ok=True)

    return app


def _render_settings(msg="", ok=True):
    has_screen, name, transform, raw = get_display_info()
    cfg = load_config()
    saved = cfg.get("screen_rotation", "normal")
    user, pw = get_term_credential()

    msg_html = f'<div class="msg {"ok" if ok else "err"}">{msg}</div>' if msg else ""

    if has_screen:
        buttons = "".join(f"""
          <form method="POST" action="/settings/rotate" style="display:inline;">
            <input type="hidden" name="rotation" value="{val}">
            <button type="submit" class="{'blue' if transform == val else 'gray'}" data-busy="Dang xoay...">{label}</button>
          </form>""" for val, label in ROTATIONS)
        screen_card = f"""
        <div class="card">
          <h3>Xoay man hinh</h3>
          <table style="max-width:430px;margin-bottom:12px;">
            <tr><th style="width:150px;">Man hinh</th><td><code>{name}</code></td></tr>
            <tr><th>Hướng hiện tại</th><td><code>{transform}</code></td></tr>
            <tr><th>Đã lưu cho lần sau</th><td><code>{saved}</code></td></tr>
          </table>
          <div class="row">{buttons}</div>
          <p style="color:#8b93a1;font-size:13px;margin-top:11px;">
            Áp dụng ngay lập tức, không cần khởi động lại. Lựa chọn được ghi nhớ
            và tự áp dụng lại mỗi lần Pi khởi động.
          </p>
        </div>"""
    else:
        screen_card = """
        <div class="card">
          <h3>Xoay man hinh</h3>
          <div class="msg info" style="margin:0;">
            Thiet bi nay khong gan man hinh (hoac che do kiosk chua chay),
            nen khong co gi de xoay. Day la binh thuong voi Pi dung tu xa.
          </div>
        </div>"""

    body = f"""
    {msg_html}
    {screen_card}

    <div class="card">
      <h3>Mat khau terminal</h3>
      <table style="max-width:430px;margin-bottom:12px;">
        <tr><th style="width:150px;">Tai khoan</th><td><code>{user}</code></td></tr>
        <tr><th>Mat khau</th><td><code id="term-mk" data-mk="{pw}">••••••••••</code>
          <button type="button" class="small gray" style="margin-left:8px;"
            onclick="var c=document.getElementById('term-mk');var h=c.textContent.indexOf('•')<0;
                     c.textContent=h?'••••••••••':c.dataset.mk;this.textContent=h?'Hiện':'Ẩn';">Hiện</button>
          <!-- Che mac dinh (26/09/2026): truoc day hien thang chu ro - ai liec man
               hinh / chup anh la lo. Bam Hien moi thay. --></td></tr>
      </table>
      <form method="POST" action="/settings/regen-term-pass"
            onsubmit="return confirm('Doi mat khau terminal? Trinh duyet se hoi dang nhap lai.');">
        <button type="submit" class="gray">🔄 Đổi mật khẩu mới</button>
      </form>
      <p style="color:#8b93a1;font-size:13px;margin-top:11px;">
        Dùng cho 2 khung terminal (Terminal tại chỗ và SSH). Lưu tại
        <code>/opt/console-pi/config.json</code>.
      </p>
    </div>

    {_khoi_man_hinh()}

    {_khoi_baotri()}

    <div class="card">
      <h3>Thông tin hệ thống</h3>
      <table>
        <tr><th style="width:180px;">Phien ban toolkit</th><td><code>{_version()}</code></td></tr>
        <tr><th>Thư mục cài đặt</th><td><code>/opt/console-pi</code></td></tr>
        <tr><th>File cau hinh</th><td><code>/opt/console-pi/config.json</code></td></tr>
        <tr><th>Thu vien lenh</th><td><code>/opt/console-pi/command-library.json</code></td></tr>
      </table>
    </div>"""

    return render_page(body, active="/settings", title="Cai dat",
                       subtitle="Màn hình, mật khẩu terminal, thông tin hệ thống")


def _trang_thai_kiosk():
    """
    Tra (da_cai, dang_bat, dang_chay, co_man_hinh) cua giao dien kiosk.

    Dung `systemctl is-enabled/is-active` thay vi doan theo file: day la
    nguon su that duy nhat ve trang thai dich vu.
    """
    import subprocess, glob

    def _ht(*lenh):
        try:
            r = subprocess.run(lenh, capture_output=True, text=True, timeout=5)
            return r.stdout.strip()
        except Exception:
            return ""

    da_cai = bool(_ht("systemctl", "list-unit-files", "console-pi-kiosk.service"))
    dang_bat = _ht("systemctl", "is-enabled", "console-pi-kiosk") == "enabled"
    dang_chay = _ht("systemctl", "is-active", "console-pi-kiosk") == "active"

    # Man hinh THAT dang cam: doc /sys/class/drm/*/status - cach nay dung
    # cho ca man hinh that lan man hinh ao cua may ao (VMware/QEMU deu bao
    # "connected" khi cua so console dang mo).
    co_man_hinh = False
    for f in glob.glob("/sys/class/drm/*/status"):
        try:
            with open(f) as fh:
                if fh.read().strip() == "connected":
                    co_man_hinh = True
                    break
        except OSError:
            continue
    return da_cai, dang_bat, dang_chay, co_man_hinh


def _khoi_man_hinh():
    """
    Bat/tat giao dien hien thang tren man hinh cua chinh may nay (kiosk).

    VI SAO CAN NUT NAY (anh Thoai 20/09/2026): ban cai x86 tu nhan man hinh
    luc khoi dong lan dau, nhung "tu nhan" khong bao gio dung 100%: may ao
    luon bao co man hinh du khong ai nhin, con may chu cam trong rack thi
    co the co cong VGA nhung khong ai cam day. Chromium ton ~300MB RAM -
    dang ke tren may 2GB - nen phai cho nguoi dung tu quyet.
    """
    da_cai, dang_bat, dang_chay, co_man_hinh = _trang_thai_kiosk()

    if not da_cai:
        return '''
    <div class="card">
      <h3>Giao diện trên màn hình máy này</h3>
      <p style="color:#8A94A6;font-size:13.5px;margin:0;">
        Máy này chưa cài sẵn phần giao diện màn hình (cage + Chromium).
        Tính năng này có sẵn trong bản cài Console System OS.</p>
    </div>'''

    if dang_chay:
        trang_thai = ('<div class="msg ok" style="margin-top:0;">Đang <strong>BẬT</strong> '
                      '&mdash; màn hình của máy này đang hiện dashboard.</div>')
        nut = ('<form method="POST" action="/settings/kiosk/tat">'
               '<button type="submit" class="red" data-busy="Đang tắt...">'
               'Tắt giao diện màn hình</button></form>')
    else:
        canh = ("" if co_man_hinh else
                '<div class="msg warn">Không phát hiện màn hình nào đang cắm. '
                'Bật lên vẫn được nhưng sẽ không thấy gì.</div>')
        trang_thai = ('<div class="msg warn" style="margin-top:0;">Đang <strong>TẮT</strong> '
                      '&mdash; máy chỉ phục vụ qua trình duyệt từ máy khác.</div>' + canh)
        nut = ('<form method="POST" action="/settings/kiosk/bat">'
               '<button type="submit" data-busy="Đang bật...">'
               'Bật giao diện màn hình</button></form>')

    return f'''
    <div class="card">
      <h3>Giao diện trên màn hình máy này</h3>
      <p style="color:#8A94A6;font-size:13.5px;margin:0 0 12px;">
        Bật lên thì màn hình gắn vào máy này sẽ hiện thẳng dashboard toàn
        màn hình (như màn cảm ứng của Raspberry Pi), không cần máy khác.
        Tắt đi thì máy chỉ phục vụ qua mạng.
        <br>Tốn khoảng <strong>300 MB RAM</strong> cho trình duyệt &mdash;
        đáng cân nhắc trên máy ít RAM nếu không ai nhìn màn hình.
      </p>
      {trang_thai}
      {nut}
    </div>'''


def _khoi_baotri():
    """
    Hai cong cu bao tri (xem ui/baotri.py cho phan xu ly). De o trang Cai
    dat vi day la viec "cham vao may" chu khong phai viec mang.
    """
    from . import baotri as bt
    from .home import _esc

    dia, muc = bt.tinh_dung_luong()
    mau = "#F87171" if dia["phan_tram"] >= 90 else (
          "#FBBF24" if dia["phan_tram"] >= 80 else "#4ADE80")
    hang_muc = "".join(
        f'''<tr><td><a href="{m["lien_ket"]}">{_esc(m["nhan"])}</a></td>
             <td style="text-align:right;font-family:ui-monospace,monospace;">
             {bt.co_kich_thuoc(m["byte"])}</td></tr>'''
        for m in muc)

    rac = bt.tim_rac()
    tong_rac = sum(r[2] for r in rac)
    hang_rac = "".join(
        f'''<tr>
             <td>{_esc(nhan)}<br><small style="color:#8A94A6;">{_esc(gt)}</small></td>
             <td style="text-align:right;font-family:ui-monospace,monospace;">
               {bt.co_kich_thuoc(byte)}</td>
             <td style="width:110px;">
               <form method="POST" action="/settings/don-rac">
                 <input type="hidden" name="ma" value="{ma}">
                 <button type="submit" class="gray small"{" disabled" if byte <= 0 else ""}
                         data-busy="Đang dọn...">Dọn</button>
               </form></td>
           </tr>'''
        for ma, nhan, byte, gt in rac)

    return f'''
    <div class="card">
      <h3>Dung lượng thẻ nhớ</h3>
      <div style="background:#0B0E14;border:1px solid #1F2733;border-radius:8px;
                  height:16px;overflow:hidden;margin-bottom:8px;">
        <div style="height:100%;width:{dia["phan_tram"]}%;background:{mau};"></div>
      </div>
      <p style="margin:0 0 14px;color:#8A94A6;font-size:13.5px;">
        Đã dùng <strong style="color:#E3E8EF;">{bt.co_kich_thuoc(dia["dung"])}</strong>
        / {bt.co_kich_thuoc(dia["tong"])} ({dia["phan_tram"]}%) &mdash;
        còn trống <strong style="color:{mau};">{bt.co_kich_thuoc(dia["trong"])}</strong>.
      </p>
      <div class="tbl-scroll"><table>
        <thead><tr><th>Dữ liệu của anh</th><th style="text-align:right;width:120px;">Chiếm</th></tr></thead>
        <tbody>{hang_muc}</tbody>
      </table></div>
      <h3 style="margin-top:18px;">Dọn rác an toàn ({bt.co_kich_thuoc(tong_rac)})</h3>
      <p class="hint" style="margin:0 0 10px;">Ba mục dưới đây xoá đi KHÔNG mất
        dữ liệu nào của anh - hệ thống tự tạo lại khi cần.</p>
      <div class="tbl-scroll"><table><tbody>{hang_rac}</tbody></table></div>
    </div>

    <div class="card">
      <h3>Sao lưu cấu hình</h3>
      <p style="color:#8A94A6;font-size:13.5px;margin:0 0 12px;">
        Toàn bộ công sức cấu hình (kịch bản cài đặt, bảng tra tham số, thư
        viện lệnh, kết nối kho trung tâm) chỉ nằm trên <strong>một thẻ nhớ</strong>
        - mà thẻ nhớ là thứ hỏng vặt nhất trên Pi. Tải file này về cất ở máy
        khác, mất thẻ thì nạp lại là xong.
        <br>Ảnh Windows và bộ cài phần mềm <strong>không</strong> nằm trong đây
        (tải lại được từ nguồn gốc, mà nhét vào thì file to không ai tải nổi).
      </p>
      <div class="msg warn" style="margin-top:0;">
        File sao lưu có chứa <strong>mật khẩu</strong> trong kịch bản cài đặt
        và token kho trung tâm - cất nơi kín đáo, đừng gửi lung tung.
      </div>
      <div class="row">
        <a class="btn" href="/settings/sao-luu">Tải file sao lưu về</a>
      </div>
      <form method="POST" action="/settings/nap-sao-luu" enctype="multipart/form-data"
            style="margin-top:16px;"
            onsubmit="return confirm('Nạp lại cấu hình sẽ GHI ĐÈ kịch bản và bảng tham số hiện tại. Tiếp tục?');">
        <label>Nạp lại từ file sao lưu (.tar.gz)</label>
        <input type="file" name="file" accept=".gz,.tar.gz" required>
        <button type="submit" class="gray" style="margin-top:10px;"
                data-busy="Đang nạp...">Nạp lại cấu hình</button>
      </form>
    </div>'''


def _version():
    for p in ("/opt/console-pi/VERSION", "/opt/console-pi/version.txt"):
        try:
            with open(p) as f:
                return f.read().strip()
        except Exception:
            continue
    return "khong ro"
