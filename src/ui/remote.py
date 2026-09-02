"""
Console Pi - Truy cap tu xa qua Cloudflare Tunnel.

Kich ban: dua Pi cho nguoi khac mang toi diem xa, ho chi can cam console va
cam mang internet (ke ca 4G). Nguoi quan tri ngoi nha van vao cau hinh duoc.

Vi sao chon Cloudflare Tunnel:
  - KHONG can mo port tren router, khong can IP tinh, chay sau moi lop NAT
  - Duong ham do cloudflared TU MO RA, nen mang o dau khong quan trong

Bao mat:
  - Duong ham chi tro vao 127.0.0.1:80, ma cong 80 da co lop dang nhap PAM
  - Token duoc luu voi quyen 600, chi root doc duoc
  - Nen bat them Cloudflare Access de chan ngay tu bien Cloudflare
"""
import os
import re
import shutil
import subprocess

CONF_DIR = "/etc/cloudflared"
TOKEN_FILE = os.path.join(CONF_DIR, "console-pi-token")
SERVICE = "console-pi-tunnel"
DEB_URL = ("https://github.com/cloudflare/cloudflared/releases/latest/"
           "download/cloudflared-linux-{arch}.deb")


def da_cai():
    return shutil.which("cloudflared") is not None


def kien_truc():
    m = subprocess.run(["dpkg", "--print-architecture"],
                       capture_output=True, text=True).stdout.strip()
    return m or "arm64"


def cai_cloudflared():
    """Tai goi .deb chinh chu tu Cloudflare va cai. Can internet."""
    if da_cai():
        return True, "cloudflared da co san."
    url = DEB_URL.format(arch=kien_truc())
    deb = "/tmp/cloudflared.deb"
    try:
        r = subprocess.run(["curl", "-fsSL", "-o", deb, url],
                           capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            return False, ("Khong tai duoc cloudflared. Kiem tra Pi co vao duoc "
                           f"internet khong. Chi tiet: {r.stderr.strip()[:150]}")
        r = subprocess.run(["dpkg", "-i", deb], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return False, f"Cai that bai: {(r.stderr or r.stdout).strip()[:200]}"
    except Exception as e:
        return False, f"Loi khi cai: {e}"
    finally:
        try:
            os.remove(deb)
        except OSError:
            pass
    return True, "Da cai cloudflared."


def luu_token(token):
    """
    Token cua Cloudflare Tunnel la chuoi base64 dai. Chi kiem tra hinh dang
    co ban - Cloudflare se tu bao neu token sai.
    """
    token = (token or "").strip()
    if len(token) < 40 or not re.fullmatch(r"[A-Za-z0-9+/=_.\-]+", token):
        return False, "Token khong dung dinh dang. Sao chep lai tu trang Cloudflare Zero Trust."
    try:
        os.makedirs(CONF_DIR, exist_ok=True)
        # Ghi voi quyen 600 NGAY TU DAU, khong ghi roi moi chmod - giua hai
        # buoc do file nam ho o quyen mac dinh.
        fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(token + "\n")
    except OSError as e:
        return False, f"Khong luu duoc token: {e}"
    return True, "Da luu token."


def co_token():
    return os.path.exists(TOKEN_FILE) and os.path.getsize(TOKEN_FILE) > 40


def xoa_token():
    subprocess.run(["systemctl", "disable", "--now", SERVICE],
                   capture_output=True, timeout=25)
    try:
        os.remove(TOKEN_FILE)
    except OSError:
        pass
    return True, "Da xoa token va tat duong ham."


def dang_chay():
    r = subprocess.run(["systemctl", "is-active", SERVICE],
                       capture_output=True, text=True, timeout=8)
    return r.stdout.strip() == "active"


def bat_tunnel():
    if not da_cai():
        return False, "Chua cai cloudflared."
    if not co_token():
        return False, "Chua co token."
    r = subprocess.run(["systemctl", "enable", "--now", SERVICE],
                       capture_output=True, text=True, timeout=40)
    if r.returncode != 0:
        return False, f"Khong bat duoc: {(r.stderr or r.stdout).strip()[:200]}"
    return True, "Da bat duong ham. Xem nhat ky ben duoi de biet ten mien truy cap."


def tat_tunnel():
    subprocess.run(["systemctl", "disable", "--now", SERVICE],
                   capture_output=True, timeout=30)
    return True, "Da tat duong ham."


def nhat_ky(n=25):
    r = subprocess.run(["journalctl", "-u", SERVICE, "-n", str(n),
                        "--no-pager", "-o", "cat"],
                       capture_output=True, text=True, timeout=15)
    return r.stdout.strip() or "(chua co nhat ky)"


def ten_mien():
    """Doc ten mien tu nhat ky - cloudflared in ra khi ket noi xong."""
    log = nhat_ky(200)
    m = re.findall(r"https://([a-z0-9.-]+\.(?:trycloudflare\.com|[a-z0-9-]+\.[a-z]{2,}))", log)
    return m[-1] if m else ""


# =============================================================== giao dien web
def register_remote(app):
    from flask import request
    from .layout import render_page
    from .home import _esc

    def page(msg="", ok=True):
        cai = da_cai()
        tok = co_token()
        chay = dang_chay() if cai else False
        mien = ten_mien() if chay else ""

        msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""

        if not cai:
            khoi = """
            <div class="msg warn">Chua cai <code>cloudflared</code>. Pi phai vao duoc
            internet de tai goi cai chinh chu tu Cloudflare.</div>
            <form method="POST" action="/remote/cai" style="margin-top:12px;">
              <button type="submit" data-busy="Dang tai va cai, toi 2 phut...">
                ⬇ Cai cloudflared</button>
            </form>"""
        elif not tok:
            khoi = """
            <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
              Vao <strong>Cloudflare Zero Trust &rarr; Networks &rarr; Tunnels</strong>,
              tao mot tunnel moi, chon <em>Debian / arm64</em>, roi sao chep phan token
              trong dong lenh cai dat (chuoi dai sau <code>--token</code>).
              Tro tunnel do vao <code>http://127.0.0.1:80</code>.</p>
            <form method="POST" action="/remote/token">
              <label>Tunnel token</label>
              <input type="password" name="token" required autocomplete="off"
                     placeholder="eyJhIjoiN...">
              <div class="row" style="margin-top:13px;">
                <button type="submit" data-busy="Dang luu...">Luu va bat duong ham</button>
              </div>
            </form>"""
        else:
            trang_thai = ('<span style="color:#6ee7a0;">🟢 Duong ham dang chay</span>'
                          if chay else '<span style="color:#8b93a1;">⚪ Duong ham dang tat</span>')
            mien_html = (f'<p style="margin:9px 0 0;">Truy cap tai: '
                         f'<a href="https://{_esc(mien)}" target="_blank" rel="noopener">'
                         f'<code>https://{_esc(mien)}</code></a></p>' if mien else
                         '<p style="color:#8b93a1;font-size:13px;margin:9px 0 0;">'
                         'Ten mien do ban dat trong Cloudflare - xem trong trang Tunnels.</p>')
            nut = ('<form method="POST" action="/remote/tat" style="display:inline;">'
                   '<button type="submit" class="red" data-busy="Dang tat...">⏹ Tat duong ham</button></form>'
                   if chay else
                   '<form method="POST" action="/remote/bat" style="display:inline;">'
                   '<button type="submit" data-busy="Dang bat...">▶ Bat duong ham</button></form>')
            khoi = f"""
            <p style="margin:0;">{trang_thai}</p>
            {mien_html}
            <div class="row" style="gap:10px;margin-top:13px;flex-wrap:wrap;">
              {nut}
              <form method="POST" action="/remote/xoa-token" style="display:inline;"
                    onsubmit="return confirm('Xoa token va tat duong ham?');">
                <button type="submit" class="gray">Xoa token</button>
              </form>
            </div>"""

        log_html = ""
        if cai and tok:
            log_html = f"""
            <h2>Nhat ky duong ham</h2>
            <pre style="background:#12151b;padding:13px;border-radius:6px;overflow:auto;
                        max-height:290px;font-size:12px;">{_esc(nhat_ky(30))}</pre>"""

        body = f"""
        {msg_html}
        <div class="card">
          <h3>Truy cap tu xa qua Cloudflare</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Dua Pi toi diem xa, cam console va cam mang internet la vao cau hinh duoc
            tu bat ky dau. Khong can mo port tren router, khong can IP tinh, chay
            duoc ca sau 4G.</p>
          {khoi}
        </div>

        <div class="card" style="border-left:4px solid #ffb74d;">
          <h3 style="color:#ffb74d;">Luu y bao mat</h3>
          <ul style="margin:0;padding-left:19px;line-height:1.75;color:#c9cfda;">
            <li>Duong ham chi tro vao <code>127.0.0.1:80</code>, ma cong do da co lop
                dang nhap bang tai khoan Linux cua may</li>
            <li>Nen bat them <strong>Cloudflare Access</strong> de chan ngay tu bien
                Cloudflare, truoc khi cham toi Pi</li>
            <li>Token duoc luu quyen 600, chi root doc duoc. Bat ky ai co token deu
                dung lai duoc duong ham - dung gui qua chat/email</li>
            <li>Xong viec thi <strong>tat duong ham</strong>, dung de mo thuong xuyen</li>
          </ul>
        </div>

        {log_html}"""

        return render_page(body, active="/remote", title="Truy cap tu xa",
                           subtitle="Cloudflare Tunnel - vao duoc Pi tu bat ky dau")

    @app.route("/remote")
    def remote_page():
        return page()

    @app.route("/remote/cai", methods=["POST"])
    def remote_install():
        ok_i, msg = cai_cloudflared()
        return page(msg=msg, ok=ok_i)

    @app.route("/remote/token", methods=["POST"])
    def remote_token():
        ok_t, msg = luu_token(request.form.get("token", ""))
        if ok_t:
            ok_b, msg2 = bat_tunnel()
            return page(msg=f"{msg} {msg2}", ok=ok_b)
        return page(msg=msg, ok=False)

    @app.route("/remote/bat", methods=["POST"])
    def remote_on():
        ok_b, msg = bat_tunnel()
        return page(msg=msg, ok=ok_b)

    @app.route("/remote/tat", methods=["POST"])
    def remote_off():
        ok_o, msg = tat_tunnel()
        return page(msg=msg, ok=ok_o)

    @app.route("/remote/xoa-token", methods=["POST"])
    def remote_clear():
        ok_x, msg = xoa_token()
        return page(msg=msg, ok=ok_x)
