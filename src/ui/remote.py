"""
Console Pi - Truy cap tu xa qua Cloudflare Tunnel (mac dinh) hoac Tailscale
(lua chon phu).

Kich ban: dua Pi cho nguoi khac mang toi diem xa, ho chi can cam console va
cam mang internet (ke ca 4G). Nguoi quan tri ngoi nha van vao cau hinh duoc.

Vi sao Cloudflare Tunnel la MAC DINH:
  - Vao duoc tu BAT KY trinh duyet nao, khong can cai gi tren may dang xem -
    hop voi kich ban "dua Pi cho nguoi khac, minh xem tu xa" o tren
  - KHONG can mo port tren router, khong can IP tinh, chay sau moi lop NAT

Vi sao them Tailscale la LUA CHON PHU (khong thay the Cloudflare):
  - Tailscale tao mang rieng ao (VPN mesh) GIUA CAC THIET BI CUA CHINH
    NGUOI DUNG - may nao muon vao cung phai CAI APP TAILSCALE va dang nhap
    CUNG TAI KHOAN truoc, khong vao duoc tu trinh duyet/may la nhu
    Cloudflare. Doi lai: vao duoc ca SSH/dich vu khac cua Pi qua dia chi IP
    rieng trong mang do, khong chi trang web qua nginx cong 80.
  - Hop khi CHINH nguoi dung (khong phai nguoi thu ba) muon truy cap day du
    hon tu cac thiet bi ca nhan da cai san Tailscale.

Bao mat (ca hai):
  - Cloudflare: duong ham chi tro vao 127.0.0.1:80, mà cổng đó đã có lớp
    dang nhap PAM. Token luu quyen 600, chi root doc duoc. Nen bat them
    Cloudflare Access de chan ngay tu bien Cloudflare.
  - Tailscale: authkey luu quyen 600. Ban than Tailscale da ma hoa
    (WireGuard) toan bo duong truyen giua cac thiet bi trong tailnet -
    khong can lop dang nhap PAM rieng vi chi thiet bi DA DUOC XAC THUC vao
    dung tailnet do moi ket noi toi duoc Pi.
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

TS_AUTHKEY_FILE = "/etc/tailscale-console-pi-authkey"
TS_HOSTNAME = "console-pi"


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
            return False, ("Không tải được cloudflared. Kiểm tra Pi có vào được "
                           f"internet khong. Chi tiet: {r.stderr.strip()[:150]}")
        r = subprocess.run(["dpkg", "-i", deb], capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            return False, f"Cài thất bại: {(r.stderr or r.stdout).strip()[:200]}"
    except Exception as e:
        return False, f"Lỗi khi cài: {e}"
    finally:
        try:
            os.remove(deb)
        except OSError:
            pass
    return True, "Đã cài cloudflared."


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
        return False, f"Không lưu được token: {e}"
    return True, "Đã lưu token."


def co_token():
    return os.path.exists(TOKEN_FILE) and os.path.getsize(TOKEN_FILE) > 40


def xoa_token():
    subprocess.run(["systemctl", "disable", "--now", SERVICE],
                   capture_output=True, timeout=25)
    try:
        os.remove(TOKEN_FILE)
    except OSError:
        pass
    return True, "Đã xóa token và tắt đường hầm."


def dang_chay():
    r = subprocess.run(["systemctl", "is-active", SERVICE],
                       capture_output=True, text=True, timeout=8)
    return r.stdout.strip() == "active"


def bat_tunnel():
    if not da_cai():
        return False, "Chưa cài cloudflared."
    if not co_token():
        return False, "Chưa có token."
    r = subprocess.run(["systemctl", "enable", "--now", SERVICE],
                       capture_output=True, text=True, timeout=40)
    if r.returncode != 0:
        return False, f"Không bật được: {(r.stderr or r.stdout).strip()[:200]}"
    return True, "Đã bật đường hầm. Xem nhật ký bên dưới để biết tên miền truy cập."


def tat_tunnel():
    subprocess.run(["systemctl", "disable", "--now", SERVICE],
                   capture_output=True, timeout=30)
    return True, "Đã tắt đường hầm."


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


# =========================================================== Tailscale (phu)
def ts_da_cai():
    return shutil.which("tailscale") is not None


def ts_cai_dat():
    """
    Cai bang script chinh thuc cua Tailscale - KHAC voi cach lam voi
    cloudflared (tai thang file .deb roi dpkg -i). Ly do: Tailscale KHONG
    co 1 duong dan .deb "ban moi nhat" don gian nhu Cloudflare - phai biet
    dung ten ban Debian (vd "trixie") de lay dung goi, va tu ho da lam san
    script chinh thuc de tu nhan dien dieu do dang tin cay hon minh tu doan.
    Day la cach duoc chinh Tailscale khuyen dung cho cai dat khong tuong
    tac (headless), khong phai chon curl|sh cho tien.
    """
    if ts_da_cai():
        return True, "tailscale da co san."
    try:
        r = subprocess.run(
            "curl -fsSL https://tailscale.com/install.sh | sh",
            shell=True, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            return False, ("Cai that bai. Kiem tra Pi co vao duoc internet khong. "
                           f"Chi tiet: {(r.stderr or r.stdout).strip()[-300:]}")
    except Exception as e:
        return False, f"Lỗi khi cài: {e}"
    if not ts_da_cai():
        return False, "Script chay xong nhung khong thay lenh tailscale - cai that bai."
    return True, "Da cai Tailscale."


def ts_luu_authkey(authkey):
    authkey = (authkey or "").strip()
    if len(authkey) < 20:
        return False, "Authkey khong dung dinh dang. Sao chep lai tu trang Tailscale admin."
    try:
        fd = os.open(TS_AUTHKEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(authkey + "\n")
    except OSError as e:
        return False, f"Khong luu duoc authkey: {e}"
    return True, "Da luu authkey."


def ts_co_authkey():
    return os.path.exists(TS_AUTHKEY_FILE) and os.path.getsize(TS_AUTHKEY_FILE) > 20


def ts_trang_thai():
    """
    Doc trang thai qua `tailscale status --json`. Tra ve dict voi cac khoa:
      dang_ket_noi (bool), ip (str, rong neu chua co),
      ten_mien (str, ten MagicDNS rong neu chua co), can_dang_nhap (bool)
    Khong doan gia tri nao khi lenh loi hoac JSON thieu truong - tra ve
    trang thai "khong ro" trung thuc thay vi bia.

    Ten mien lay tu `Self.DNSName` - da kiem chung that tren chinh may
    (khong doan): Tailscale luon co san 1 ten MagicDNS dang
    "<hostname>.<ten-tailnet>.ts.net." (co dau cham cuoi) ngay ca khi
    chi dung dia chi IP de vao - khong can bat/cau hinh gi them.
    """
    import json as _json
    RONG = {"dang_ket_noi": False, "ip": "", "ten_mien": "",
            "can_dang_nhap": False, "ro": False}
    if not ts_da_cai():
        return RONG
    try:
        r = subprocess.run(["tailscale", "status", "--json"],
                           capture_output=True, text=True, timeout=10)
        d = _json.loads(r.stdout)
    except Exception:
        return RONG

    trang_thai = d.get("BackendState", "")
    ban_than = d.get("Self") or {}
    ip_list = ban_than.get("TailscaleIPs") or []
    ip = ip_list[0] if ip_list else ""
    ten_mien = (ban_than.get("DNSName") or "").rstrip(".")
    return {
        "dang_ket_noi": trang_thai == "Running" and bool(ip),
        "ip": ip,
        "ten_mien": ten_mien,
        "can_dang_nhap": trang_thai == "NeedsLogin",
        "ro": True,
    }


def ts_bat():
    """Dang nhap + bat ket noi bang authkey da luu."""
    if not ts_da_cai():
        return False, "Chua cai Tailscale."
    if not ts_co_authkey():
        return False, "Chua co authkey."
    try:
        with open(TS_AUTHKEY_FILE) as f:
            authkey = f.read().strip()
    except OSError as e:
        return False, f"Khong doc duoc authkey da luu: {e}"

    subprocess.run(["systemctl", "enable", "--now", "tailscaled"],
                   capture_output=True, timeout=20)
    r = subprocess.run(["tailscale", "up", f"--authkey={authkey}",
                        f"--hostname={TS_HOSTNAME}", "--accept-dns=false"],
                       capture_output=True, text=True, timeout=40)
    if r.returncode != 0:
        return False, f"Khong ket noi duoc: {(r.stderr or r.stdout).strip()[:250]}"
    return True, "Da ket noi Tailscale."


def ts_tat():
    """Ngat ket noi nhung GIU LAI dang ky thiet bi trong tailnet - bat lai
    nhanh, khong can authkey moi (khac voi 'quen thiet bi' o duoi)."""
    r = subprocess.run(["tailscale", "down"], capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return False, f"Khong tat duoc: {(r.stderr or r.stdout).strip()[:200]}"
    return True, "Da ngat ket noi Tailscale."


def ts_quen_thiet_bi():
    """Dang xuat han + xoa authkey - thiet bi bien mat khoi tailnet, phai
    dan authkey moi neu muon bat lai."""
    subprocess.run(["tailscale", "logout"], capture_output=True, timeout=20)
    try:
        os.remove(TS_AUTHKEY_FILE)
    except OSError:
        pass
    return True, "Da dang xuat va xoa authkey khoi Pi."


# =============================================================== giao dien web
def _goc_ngoai():
    """
    Dia chi ma nguoi NGOAI dung de vao. Qua Cloudflare thi la ten mien that,
    con vao truc tiep trong mang thi la IP/hostname - lay tu chinh request nen
    luon dung voi duong ma nguoi dung dang di.
    """
    from flask import request as _rq
    proto = _rq.headers.get("X-Forwarded-Proto", "http")
    return f"{proto}://{_rq.host}"


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
            trang_thai = ('<span style="color:#6ee7a0;">🟢 Đường hầm đang chạy</span>'
                          if chay else '<span style="color:#8b93a1;">⚪ Duong ham dang tat</span>')
            mien_html = (f'<p style="margin:9px 0 0;">Truy cap tai: '
                         f'<a href="https://{_esc(mien)}" target="_blank" rel="noopener">'
                         f'<code>https://{_esc(mien)}</code></a></p>' if mien else
                         '<p style="color:#8b93a1;font-size:13px;margin:9px 0 0;">'
                         'Tên miền do anh đặt trong Cloudflare - xem trong trang Tunnels.</p>')
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

        # --- Tailscale (lua chon phu, KHONG thay the Cloudflare o tren) ---
        ts_cai = ts_da_cai()
        ts_key = ts_co_authkey() if ts_cai else False
        ts_tt = ts_trang_thai() if ts_cai else {"dang_ket_noi": False, "ip": "",
                                                "ten_mien": "", "can_dang_nhap": False,
                                                "ro": False}

        if not ts_cai:
            ts_khoi = """
            <div class="msg warn">Chua cai <code>tailscale</code>. Pi phai vao duoc
            internet de tai goi cai chinh chu tu Tailscale.</div>
            <form method="POST" action="/remote/ts/cai" style="margin-top:12px;">
              <button type="submit" class="gray" data-busy="Dang tai va cai, toi 2 phut...">
                ⬇ Cai Tailscale</button>
            </form>"""
        elif not ts_key:
            ts_khoi = """
            <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
              Vao <strong>Tailscale admin console &rarr; Settings &rarr; Keys</strong>,
              tao mot <em>Auth key</em> (nen chon <em>Reusable</em> neu muon dung lai
              nhieu lan, hoac dat han su dung phu hop).</p>
            <form method="POST" action="/remote/ts/authkey">
              <label>Auth key</label>
              <input type="password" name="authkey" required autocomplete="off"
                     placeholder="tskey-auth-...">
              <div class="row" style="margin-top:13px;">
                <button type="submit" class="gray" data-busy="Dang luu va ket noi...">
                  Luu va ket noi</button>
              </div>
            </form>"""
        else:
            if not ts_tt["ro"]:
                ts_trang = ('<span style="color:#8b93a1;">⚪ Khong doc duoc trang thai '
                           '(chay <code>tailscale status</code> tren Terminal de xem chi tiet)</span>')
            elif ts_tt["dang_ket_noi"]:
                mien_html = (f'<p style="margin:9px 0 0;">Truy cap tai: '
                            f'<a href="http://{_esc(ts_tt["ten_mien"])}" target="_blank" rel="noopener">'
                            f'<code>http://{_esc(ts_tt["ten_mien"])}</code></a> '
                            f'<span style="color:#8b93a1;">(hoac IP '
                            f'<code>{_esc(ts_tt["ip"])}</code>)</span></p>'
                            if ts_tt["ten_mien"] else
                            f'<p style="margin:9px 0 0;">Dia chi trong tailnet: '
                            f'<code>{_esc(ts_tt["ip"])}</code></p>')
                ts_trang = (f'<span style="color:#6ee7a0;">🟢 Dang ket noi</span>'
                           f'{mien_html}')
            elif ts_tt["can_dang_nhap"]:
                ts_trang = ('<span style="color:#ffb74d;">⚠️ Authkey da luu nhung chua '
                           'dang nhap duoc - co the authkey het han/da dung het luot. '
                           'Xoa va dan authkey moi.</span>')
            else:
                ts_trang = '<span style="color:#8b93a1;">⚪ Dang tat</span>'

            ts_nut = ('<form method="POST" action="/remote/ts/tat" style="display:inline;">'
                     '<button type="submit" class="red" data-busy="Dang tat...">⏹ Tat</button></form>'
                     if ts_tt["dang_ket_noi"] else
                     '<form method="POST" action="/remote/ts/bat" style="display:inline;">'
                     '<button type="submit" class="gray" data-busy="Dang ket noi...">▶ Bat</button></form>')
            ts_khoi = f"""
            <p style="margin:0;">{ts_trang}</p>
            <div class="row" style="gap:10px;margin-top:13px;flex-wrap:wrap;">
              {ts_nut}
              <form method="POST" action="/remote/ts/quen" style="display:inline;"
                    onsubmit="return confirm('Dang xuat va xoa authkey? Thiet bi se bien mat khoi tailnet, phai dan authkey moi neu muon dung lai.');">
                <button type="submit" class="gray">Quên thiết bị</button>
              </form>
            </div>
            <details style="margin-top:13px;">
              <summary style="cursor:pointer;color:#8b93a1;font-size:13px;">
                Authkey het han / muon doi sang key khac?</summary>
              <p style="color:#8b93a1;font-size:13px;margin:9px 0 11px;">
                Tao Auth key moi trong <strong>Tailscale admin console &rarr; Settings
                &rarr; Keys</strong>, dan vao day - KHONG can bam "Quên thiết bị" truoc,
                thiết bị vẫn giữ nguyên tên/địa chỉ cũ.</p>
              <form method="POST" action="/remote/ts/authkey">
                <input type="password" name="authkey" required autocomplete="off"
                       placeholder="tskey-auth-...">
                <div class="row" style="margin-top:11px;">
                  <button type="submit" class="gray" data-busy="Dang doi key...">
                    Doi sang key nay</button>
                </div>
              </form>
            </details>"""

        ts_card = f"""
        <div class="card" style="border-left:4px solid #5a6672;">
          <h3>Tailscale <span style="color:#8b93a1;font-size:12px;font-weight:400;">
              (lựa chọn phụ - vào được SSH/dịch vụ khác của Pi, không chỉ trang web)</span></h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Tạo mạng riêng ảo giữa các thiết bị CỦA CHÍNH ANH - máy nào muốn vào cũng
            phải cài app Tailscale và đăng nhập cùng tài khoản trước. Khác với Cloudflare
            ở trên (ai có link cũng vào được qua trình duyệt), Tailscale chỉ hợp khi
            chính anh muốn truy cập đầy đủ hơn từ thiết bị cá nhân đã cài sẵn.</p>
          {ts_khoi}
        </div>"""

        # --- Duong vao danh cho may / AI ---
        from . import api as capi
        ai = capi.api_info()
        token_moi = request.args.get("_token_moi", "")

        if token_moi:
            # Hien DUY NHAT mot lan ngay sau khi tao. Trong may chi luu ban bam
            # SHA256 nen khong the hien lai - dong nen chep ngay
            ai_khoi = f"""
            <div class="msg ok" style="margin:0 0 13px;">Da tao token. <strong>Chep ngay
              bay gio</strong> - roi khoi trang nay la khong xem lai duoc nua.</div>
            <label>Token (chi hien mot lan)</label>
            <textarea readonly rows="2" onclick="this.select();"
                      style="width:100%;font-family:monospace;font-size:13px;">{_esc(token_moi)}</textarea>
            <p style="margin:13px 0 5px;">Dua nguyen doan nay cho AI ben kia:</p>
            <textarea readonly rows="4" onclick="this.select();"
                      style="width:100%;font-family:monospace;font-size:13px;">Toi co mot thiet bi Console Pi o xa. Hay doc tai lieu huong dan tai:
{_esc(_goc_ngoai())}/ai
Dung header: Authorization: Bearer {_esc(token_moi)}
Doc tai lieu do truoc, roi giup toi lam viec voi thiet bi mang dang cam vao no.</textarea>"""
        elif ai["has_token"]:
            ai_khoi = f"""
            <table style="max-width:470px;margin-bottom:12px;">
              <tr><th style="width:150px;">Trang thai</th>
                  <td><span style="color:#6ee7a0;">🟢 Dang bat</span></td></tr>
              <tr><th>Quyen</th><td><code>{_esc(ai['scope'])}</code>
                  {'&mdash; chỉ đọc' if ai['scope'] == 'read'
                    else '&mdash; doc va go duoc lenh vao thiet bi mang'}</td></tr>
              <tr><th>Tao luc</th><td>{_esc(ai['created'])}</td></tr>
              <tr><th>Dung lan cuoi</th>
                  <td>{_esc(ai['last_used']) or '<span style="color:#8b93a1;">chua dung</span>'}</td></tr>
            </table>
            <p style="color:#8b93a1;font-size:13px;margin:0 0 12px;">
              Token thật không hiện lại được (trong máy chỉ lưu bản băm SHA256).
              Mất thì tạo cái mới - cái cũ tự hết hiệu lực.</p>
            <div class="row" style="gap:10px;flex-wrap:wrap;">
              <form method="POST" action="/remote/api-token">
                <input type="hidden" name="scope" value="read">
                <button type="submit" class="gray" data-busy="Dang tao...">Tạo token mới (chỉ đọc)</button>
              </form>
              <form method="POST" action="/remote/api-token">
                <input type="hidden" name="scope" value="full">
                <button type="submit" class="gray" data-busy="Dang tao...">Tạo token mới (đầy đủ)</button>
              </form>
              <form method="POST" action="/remote/api-thu-hoi"
                    onsubmit="return confirm('Thu hoi token? AI ben kia se mat quyen truy cap ngay lap tuc.');">
                <button type="submit" class="red">Thu hoi</button>
              </form>
            </div>"""
        else:
            ai_khoi = """
            <p style="color:#8b93a1;font-size:13px;margin:0 0 12px;">
              Dang <strong>tat</strong>. Tao token de mot AI (hoac phan mem khac) doc
              duoc trang thai thiet bi va lam viec voi switch/router dang cam.
              AI chi can mot duong dan <code>/ai</code> la tu biet phai goi gi.</p>
            <div class="row" style="gap:10px;flex-wrap:wrap;">
              <form method="POST" action="/remote/api-token">
                <input type="hidden" name="scope" value="read">
                <button type="submit" class="blue" data-busy="Dang tao...">
                  🔍 Tao token CHI DOC</button>
              </form>
              <form method="POST" action="/remote/api-token"
                    onsubmit="return confirm('Token quyen day du cho phep GO LENH vao switch/router dang cam.\\n\\nChi tao khi that su can, va thu hoi ngay khi xong viec.');">
                <input type="hidden" name="scope" value="full">
                <button type="submit" data-busy="Dang tao...">
                  ⌨️ Tao token DAY DU (go duoc lenh)</button>
              </form>
            </div>
            <p style="color:#8b93a1;font-size:13px;margin-top:11px;">
              Nên bắt đầu bằng <strong>chỉ đọc</strong>. Chỉ nâng lên đầy đủ khi thật
              su can go lenh, va thu hoi ngay khi xong.</p>"""

        ai_card = f"""
        <div class="card">
          <h3>Cho AI / may khac truy cap</h3>
          {ai_khoi}
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
            Đưa Pi tới điểm xa, cắm console và cắm mạng internet là vào cấu hình được
            từ bất kỳ đâu. Không cần mở port trên router, không cần IP tĩnh, chạy
            duoc ca sau 4G.</p>
          {khoi}
        </div>

        {ts_card}

        {ai_card}

        <div class="card" style="border-left:4px solid #ffb74d;">
          <h3 style="color:#ffb74d;">Lưu ý bảo mật</h3>
          <ul style="margin:0;padding-left:19px;line-height:1.75;color:#c9cfda;">
            <li>Đường hầm chỉ trỏ vào <code>127.0.0.1:80</code>, mà cổng đó đã có lớp
                đăng nhập bằng tài khoản Linux của máy</li>
            <li>Nên bật thêm <strong>Cloudflare Access</strong> để chặn ngay từ biên
                Cloudflare, truoc khi cham toi Pi</li>
            <li>Token được lưu quyền 600, chỉ root đọc được. Bất kỳ ai có token đều
                dùng lại được đường hầm - đừng gửi qua chat/email</li>
            <li>Xong viec thi <strong>tat duong ham</strong>, dùng để mở thường xuyên</li>
            <li>Token cho AI mac dinh <strong>tat</strong>. Token quyền đầy đủ gõ được
                lệnh vào switch/router - chỉ tạo khi cần, thu hồi ngay khi xong.
                Mỗi lần máy gọi vào đều ghi <code>/var/log/console-pi-api.log</code></li>
          </ul>
        </div>

        {log_html}"""

        return render_page(body, active="/remote", title="Truy cap tu xa",
                           subtitle="Cloudflare Tunnel - vào được Pi từ bất kỳ đâu")

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

    @app.route("/remote/api-token", methods=["POST"])
    def remote_api_token():
        from . import api as capi
        from flask import redirect as _rd
        scope = request.form.get("scope", "read")
        token = capi.tao_token(scope)
        # Chuyen huong kem token tren URL de sau khi bam F5 no khong tao lai
        # token moi. Token chi song trong thanh dia chi cua chinh may nay -
        # da qua nginx tren localhost, khong di dau ca.
        from urllib.parse import quote
        return _rd(f"/remote?_token_moi={quote(token)}")

    @app.route("/remote/api-thu-hoi", methods=["POST"])
    def remote_api_revoke():
        from . import api as capi
        capi.thu_hoi_token()
        return page(msg="Da thu hoi token. May/AI ben kia mat quyen truy cap ngay.",
                    ok=True)

    @app.route("/remote/xoa-token", methods=["POST"])
    def remote_clear():
        ok_x, msg = xoa_token()
        return page(msg=msg, ok=ok_x)

    # --------------------------------------------------------- Tailscale
    @app.route("/remote/ts/cai", methods=["POST"])
    def remote_ts_cai():
        ok_i, msg = ts_cai_dat()
        return page(msg=msg, ok=ok_i)

    @app.route("/remote/ts/authkey", methods=["POST"])
    def remote_ts_authkey():
        ok_k, msg = ts_luu_authkey(request.form.get("authkey", ""))
        if ok_k:
            ok_b, msg2 = ts_bat()
            return page(msg=f"{msg} {msg2}", ok=ok_b)
        return page(msg=msg, ok=False)

    @app.route("/remote/ts/bat", methods=["POST"])
    def remote_ts_on():
        ok_b, msg = ts_bat()
        return page(msg=msg, ok=ok_b)

    @app.route("/remote/ts/tat", methods=["POST"])
    def remote_ts_off():
        ok_o, msg = ts_tat()
        return page(msg=msg, ok=ok_o)

    @app.route("/remote/ts/quen", methods=["POST"])
    def remote_ts_forget():
        ok_f, msg = ts_quen_thiet_bi()
        return page(msg=msg, ok=ok_f)
