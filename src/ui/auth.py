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
PUBLIC_PATHS = {"/login", "/vkeyboard.js", "/dashboard.js", "/healthz", "/_auth"}

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
        return False, "Chua nhap day du."

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
            return False, "Sai tai khoan hoac mat khau."
        except Exception as e:
            return False, f"Loi xac thuc: {e}"
    except ImportError:
        pass

    # --- Cach 2: goi python-pam tren PyPI (module ten pam) ---
    try:
        import pam as _pam
        p = _pam.pam()
        if p.authenticate(username, password, service="login"):
            return True, ""
        return False, "Sai tai khoan hoac mat khau."
    except ImportError:
        pass
    except Exception as e:
        return False, f"Loi xac thuc: {e}"

    return False, ("May thieu thu vien PAM cho Python. Cai bang: "
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


LOGIN_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dang nhap - Console Pi</title>
<style>
* { box-sizing:border-box; }
body { margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
       background:#15171a; color:#e6e6e6; font-family:system-ui, Arial, sans-serif; }
.box { background:#1b1e22; border:1px solid #2c3036; border-radius:11px;
       padding:30px 32px; width:100%; max-width:390px; }
h1 { margin:0 0 4px; font-size:21px; color:#4CAF50; }
p.s { margin:0 0 20px; color:#8b93a1; font-size:13px; }
label { display:block; margin:13px 0 5px; font-size:13px; color:#a8b0bd; }
input { width:100%; padding:13px; background:#22262b; color:#e6e6e6;
        border:1px solid #363b42; border-radius:6px; font-size:16px; }
button { width:100%; margin-top:20px; padding:14px; background:#4CAF50; color:#fff;
         border:none; border-radius:6px; font-size:16px; cursor:pointer; min-height:48px; }
.err { background:#3a1a1a; border-left:4px solid #ef4444; padding:11px 14px;
       border-radius:6px; margin-top:15px; font-size:14px; }
.hint { margin-top:18px; color:#6b7280; font-size:12px; line-height:1.6; }
</style>
</head>
<body>
<div class="box">
  <h1>🖥️ Console Pi</h1>
  <p class="s">Dang nhap bang tai khoan Linux cua thiet bi</p>
  <form method="POST">
    <label>Tai khoan</label>
    <input type="text" name="username" value="{{ username or '' }}" autofocus autocapitalize="off" autocomplete="username">
    <label>Mat khau</label>
    <input type="password" name="password" autocomplete="current-password">
    <button type="submit">Dang nhap</button>
  </form>
  {% if error %}<div class="err">{{ error }}</div>{% endif %}
  <div class="hint">Dung chinh tai khoan SSH cua Pi (vi du <code>administrator</code>).
  Khong co tai khoan rieng, khong luu mat khau tren dashboard.</div>
</div>
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

        # Duong vao thu ba: token API, danh cho may (vi du mot AI o dau xa
        # dieu khien giup). Phai kiem tra o day chu khong o rieng cac route
        # /api, vi before_request nay chay TRUOC moi thu - neu khong thi
        # request cua may bi day ve /login truoc khi kip toi noi.
        #
        # Mac dinh API TAT. Chi khi chu thiet bi tu bat va tu tao token trong
        # dashboard thi nhanh nay moi cho ai di qua.
        from .api import kiem_tra_truy_cap
        kq = kiem_tra_truy_cap()
        if kq == "ok":
            return None
        if kq is not None:
            return kq            # co gui token nhung bi tu choi (401 / 403)

        # Chua co token: tra ve huong dan lay token, KHONG lo bat ky thong
        # tin nao ve he thong
        if request.path == "/ai":
            from flask import Response
            from .api import TAI_LIEU_CHUA_CO_TOKEN
            return Response(TAI_LIEU_CHUA_CO_TOKEN,
                            mimetype="text/markdown", status=401)
        if request.path.startswith("/api/"):
            from flask import jsonify
            return jsonify({"error": "Can token. Xem huong dan tai /ai"}), 401

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
        return render_template_string(LOGIN_TEMPLATE, error=error, username=username)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/login")

    @app.route("/healthz")
    def healthz():
        return {"ok": True}

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
        # Token API cung duoc di qua, de may goi duoc ca cac duong terminal
        # va console ma nginx dang canh
        from .api import quyen_cua_request
        if quyen_cua_request():
            return "", 200
        return "", 401

    return app
