# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Dang nhap bang tai khoan Linux cua chinh may (qua PAM)

Vi sao can: tab Terminal va SSH cho quyen root day du qua web. Neu khong
co dang nhap, bat ky ai vao duoc mang (hoac bat duoc song AP "ConsolePi")
deu chiem duoc may.

Dung PAM nen KHONG luu mat khau o dau ca - moi lan dang nhap deu hoi lai
he dieu hanh. Tai khoan chinh la tai khoan Linux (vd: administrator).
"""
import os
import secrets

from flask import request, redirect, session, render_template_string

# Duong dan cac trang khong can dang nhap
from .gioithieu import DUONG_CONG_KHAI as _LOGO
# Logo/favicon cong khai: trang dang nhap phai hien duoc logo truoc khi dang nhap
PUBLIC_PATHS = {"/login", "/vkeyboard.js", "/dashboard.js", "/healthz", "/_auth"} | _LOGO

SECRET_FILE = "/opt/console-pi/flask-secret.key"


def get_or_create_secret():
    """Khoa ky session - giu nguyen qua cac lan restart de khong bi dang xuat."""
    try:
        with open(SECRET_FILE, "rb") as f:
            data = f.read().strip()
            if len(data) >= 32:
                return data
    except Exception:
        pass

    key = secrets.token_bytes(48)
    try:
        old = os.umask(0o077)          # chi root doc duoc
        with open(SECRET_FILE, "wb") as f:
            f.write(key)
        os.umask(old)
    except Exception:
        pass
    return key


def check_login(username, password):
    """
    Xac thuc voi PAM (tai khoan Linux cua chinh may). Tra ve (ok, thong_bao).

    Ho tro 2 thu vien vi ten module khac nhau tuy ban phan phoi:
      - "PAM" (chu hoa): goi Debian python3-pam - dung API conversation kieu cu
      - "pam"  (chu thuong): goi python-pam tren PyPI - API gon hon
    Uu tien cai nao co san, khong bat nguoi dung phai cai them.
    """
    if not username or not password:
        return False, "Chưa nhập đầy đủ."

    # --- Cach 1: goi Debian python3-pam (module ten PAM) ---
    try:
        import PAM as _PAM

        def _conv(auth, query_list, user_data=None):
            # Tra loi moi cau hoi cua PAM bang mat khau nguoi dung nhap
            resp = []
            for query, qtype in query_list:
                if qtype in (_PAM.PAM_PROMPT_ECHO_OFF, _PAM.PAM_PROMPT_ECHO_ON):
                    resp.append((password, 0))
                else:
                    resp.append(("", 0))
            return resp

        auth = _PAM.pam()
        auth.start("login")
        auth.set_item(_PAM.PAM_USER, username)
        auth.set_item(_PAM.PAM_CONV, _conv)
        try:
            auth.authenticate()
            auth.acct_mgmt()
            return True, ""
        except _PAM.error:
            return False, "Sai tài khoản hoặc mật khẩu."
        except Exception as e:
            return False, f"Lỗi xác thực: {e}"
    except ImportError:
        pass

    # --- Cach 2: goi python-pam tren PyPI (module ten pam) ---
    try:
        import pam as _pam
        p = _pam.pam()
        if p.authenticate(username, password, service="login"):
            return True, ""
        return False, "Sai tài khoản hoặc mật khẩu."
    except ImportError:
        pass
    except Exception as e:
        return False, f"Lỗi xác thực: {e}"

    return False, ("Máy thiếu thư viện PAM cho Python. Cài bằng: "
                   "sudo apt install python3-pam")

def local_bypass_enabled():
    """
    Co cho phep man hinh gan tren Pi vao thang khong can dang nhap?
    Doi thanh false trong /opt/console-pi/config.json neu muon that chat.
    """
    try:
        import json
        with open("/opt/console-pi/config.json") as f:
            return bool(json.load(f).get("local_screen_no_login", True))
    except Exception:
        return True


def _is_local_screen():
    """
    Man hinh cam ung gan tren Pi duoc vao thang khong can dang nhap - go mat
    khau tren man hinh cam ung rat bat tien.

    Danh doi ve bao mat chap nhan duoc: ai cham duoc vao man hinh nay thi da
    dung TRUOC MAT thiet bi, luc do ho rut duoc ca the nho ra doc, tuc la da
    toan quyen roi. Truy cap TU MANG van phai dang nhap binh thuong.

    ---------------------------------------------------------------------
    LO HONG DA SUA (nghiem trong)
    ---------------------------------------------------------------------
    Truoc day dieu kien la `request.remote_addr in ("127.0.0.1", "::1")`.

    Sai o cho: cloudflared chay NGAY TREN Pi va cung goi vao 127.0.0.1:80.
    Nen MOI NGUOI di qua duong ham Cloudflare deu duoc cham nham la man hinh
    tai cho, va vao thang dashboard + terminal quyen root KHONG CAN MAT KHAU.
    Da kiem chung that: goi tu 127.0.0.1 kem X-Forwarded-For tra ve 200 thay
    vi 302. Bat ky ai biet ten mien deu chiem duoc thiet bi.

    Cach vas: khong tin dia chi IP nua, vi tren cung mot may thi trinh duyet
    kiosk va cloudflared khong the phan biet bang IP. Thay vao do dua vao
    CONG ma request di vao:
      - cong 80   : duong cong cong (LAN / WiFi / Cloudflare) -> phai dang nhap
      - cong 8880 : chi lang nghe loopback, danh rieng cho trinh duyet kiosk
    nginx dat header X-ConsolePi-Local=1 CHI o cong 8880, va GHI DE header do
    (thanh rong) o cong 80 - nen nguoi ngoai co tu gui cung vo tac dung.
    """
    if not local_bypass_enabled():
        return False
    return request.headers.get("X-ConsolePi-Local") == "1"


def _pxe_boot_cong_khai():
    """
    Duong /deployos/pxeboot/<file> phai KHONG can dang nhap - may dang boot
    qua mang (PC hong dang duoc cai lai) chua co gi de dang nhap ca luc do.

    An toan: CHI mo khi tinh nang PXE dang that su duoc bat (kiem tra qua
    ui.pxe.dang_bat() - doc file co/khong /run/console-pi-pxe.flag), va
    route pxe.py tu no cung kiem tra lai lan nua + gioi han duoi file +
    chi phuc vu dung BOOT_DIR - hai lop kiem tra doc lap. Giong het mo hinh
    rui ro cua TFTP/AP dnsmasq da co san (mac dinh tat, chi bat khi nguoi
    dung chu dong yeu cau, khong xac thuc vi thiet bi dau xa chua dang nhap
    duoc), khong phai mo rong dien rui ro moi.
    """
    if not request.path.startswith("/deployos/pxeboot/"):
        return False
    try:
        from . import pxe as _pxe
        return _pxe.dang_bat()
    except Exception:
        return False


def _bao_tien_trinh_cong_khai():
    """
    /api/tiendo/* phai KHONG can dang nhap: may vua duoc cai xong tu bao
    tien trinh ve (xem ui/tiendo.py) - no la may Windows moi tinh, khong
    co tai khoan nao cua dashboard de dang nhap.

    Vi sao chap nhan duoc:
      - CHI cho POST ghi tien trinh, KHONG doc duoc bat ky du lieu nao cua
        Pi qua duong nay (cac route deu tra ve {"ok": true}).
      - CHI mo khi PXE dang bat, tuc la dang trong mot dot trien khai that
        su - het dot thi tat PXE la duong nay dong lai.
      - Du lieu ghi vao bi cat ngan (ten may 64 ky tu, toi da 60 buoc) nen
        khong the nhoi cho day dia.
    Rieng /api/tiendo/data (doc, de trang tu lam moi) KHONG nam trong day -
    van phai dang nhap nhu moi trang khac.
    """
    if not request.path.startswith("/api/tiendo/"):
        return False
    if request.path == "/api/tiendo/data":
        return False
    try:
        from . import pxe as _pxe
        return _pxe.dang_bat()
    except Exception:
        return False


LOGIN_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Đăng nhập - Console System</title>
<link rel="icon" href="/favicon.ico">
<style>
* { box-sizing:border-box; }
body { margin:0; min-height:100vh; display:flex; flex-direction:column; align-items:center; justify-content:center;
       background:radial-gradient(1200px 600px at 20% -10%, rgba(34,211,238,.14), transparent 60%),
                  radial-gradient(900px 500px at 110% 110%, rgba(37,99,235,.16), transparent 60%), #0B0E14;
       color:#E3E8EF; font-family:system-ui, -apple-system, "Segoe UI", Arial, sans-serif; padding:16px; }
.box { background:#141A23; border:1px solid #1F2733; border-radius:14px;
       padding:28px 30px; width:100%; max-width:400px; box-shadow:0 10px 40px rgba(0,0,0,.45); }
.logo { display:block; height:58px; width:auto; margin:0 0 18px; }
p.s { margin:0 0 18px; color:#8A94A6; font-size:13.5px; }
label { display:block; margin:13px 0 5px; font-size:13px; color:#A8B0BD; }
input { width:100%; padding:13px; background:#0F141C; color:#E3E8EF;
        border:1px solid #2B3746; border-radius:8px; font-size:16px; }
input:focus { outline:none; border-color:#22D3EE; box-shadow:0 0 0 3px rgba(34,211,238,.15); }
button { width:100%; margin-top:20px; padding:14px; background:linear-gradient(135deg,#22D3EE,#2563EB);
         color:#fff; font-weight:700; border:none; border-radius:8px; font-size:16px; cursor:pointer; min-height:48px; }
button:active { transform:scale(.98); }
.err { background:rgba(248,113,113,.12); border-left:4px solid #F87171; padding:11px 14px;
       border-radius:6px; margin-top:15px; font-size:14px; }
.hint { margin-top:18px; color:#5D6879; font-size:12px; line-height:1.6; }
.ban-quyen { margin-top:18px; color:#5D6879; font-size:12px; text-align:center; }
.ban-quyen b span { color:#22D3EE; }
</style>
</head>
<body>
<div class="box">
  <img class="logo" src="/thuong-hieu/logo-full.svg" alt="zTieuYeuz - Console System">
  <p class="s">Đăng nhập bằng tài khoản của thiết bị</p>
  <form method="POST">
    <label>Tài khoản</label>
    <input type="text" name="username" value="{{ username or '' }}" autofocus autocapitalize="off" autocomplete="username">
    <label>Mật khẩu</label>
    <input type="password" name="password" autocomplete="current-password">
    <button type="submit">Đăng nhập</button>
  </form>
  {% if error %}<div class="err">{{ error }}</div>{% endif %}
  <div class="hint">Dùng chính tài khoản đăng nhập của máy (ví dụ <code>administrator</code>).
  Giao diện không có tài khoản riêng và không lưu mật khẩu.</div>
</div>
<div class="ban-quyen">Console System{{ dau_an }} &middot; phát triển bởi <b><span>z</span>TieuYeu<span>z</span></b> &middot; &copy; 2026</div>
<script src="/vkeyboard.js"></script>
</body>
</html>"""


def register_auth(app):
    """Gan co che dang nhap vao app Flask."""
    app.secret_key = get_or_create_secret()
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.permanent_session_lifetime = __import__("datetime").timedelta(days=7)

    @app.before_request
    def _require_login():
        if request.path in PUBLIC_PATHS:
            return None
        if session.get("user"):
            return None
        if _is_local_screen():
            return None          # man hinh gan trren Pi - xem muc dich o duoi
        if _pxe_boot_cong_khai():
            return None          # may dang boot qua PXE - xem muc dich o duoi
        if _bao_tien_trinh_cong_khai():
            return None          # may vua cai xong bao tien trinh - xem duoi

        return redirect("/login")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = ""
        username = ""
        if request.method == "POST":
            username = (request.form.get("username") or "").strip()
            password = request.form.get("password") or ""
            ok, msg = check_login(username, password)
            if ok:
                session.permanent = True
                session["user"] = username
                return redirect("/")
            error = msg
        from .gioithieu import dau_an_an
        return render_template_string(LOGIN_TEMPLATE, error=error, username=username, dau_an=dau_an_an())

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    @app.route("/healthz")
    def healthz():
        """
        LOI THAT DA GAP khi lam man hinh cho cua kiosk
        (scripts/kiosk-loading.html): trang do dung fetch() che do "no-cors"
        de kiem tra dashboard san sang - nhung che do nay KHONG DOC DUOC ma
        trang thai that su (response "opaque"), nen khi nginx da chay
        nhung Flask (backend that su) CHUA XONG (nginx tra ve 502), fetch()
        van resolve() BINH THUONG y het luc thanh cong that - trang cho
        tuong nham la da xong va chuyen trang som, van thay trang loi y het
        truoc khi sua.

        Sua: route nay tra CORS header rieng (chi minh no) de trang
        kiosk-loading.html doc duoc bang fetch() CHE DO THUONG (khong phai
        no-cors) va kiem tra dung response.ok - phan biet duoc 200 that su
        (Flask da song) voi 502/503 (nginx song nhung Flask chua xong).
        An toan de mo CORS o day vi noi dung tra ve khong co gi nhay cam
        (chi {"ok": true}), va route nay von da mien dang nhap
        (PUBLIC_PATHS) tu truoc.
        """
        from flask import jsonify
        resp = jsonify({"ok": True})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    @app.route("/_auth")
    def nginx_auth_check():
        """
        nginx goi vao day truoc khi cho vao cac duong dan terminal.
        Tra 200 = duoc phep, 401 = chua dang nhap (nginx se chuyen ve /login).

        Nho vay terminal dung CHUNG phien dang nhap cua dashboard, khong can
        mat khau rieng nua.
        """
        if session.get("user") or _is_local_screen():
            return "", 200
        return "", 401

    return app
