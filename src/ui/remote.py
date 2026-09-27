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
                       capture_output=True, text=True, timeout=15).stdout.strip()
    return m or "arm64"


def cai_cloudflared():
    """Tai goi .deb chinh chu tu Cloudflare va cai. Can internet."""
    if da_cai():
        return True, "cloudflared đã có sẵn."
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
        return False, "Token không đúng định dạng. Sao chép lại từ trang Cloudflare Zero Trust."
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
        return True, "Tailscale đã có sẵn."
    try:
        r = subprocess.run(
            "curl -fsSL https://tailscale.com/install.sh | sh",
            shell=True, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            return False, ("Cài thất bại. Kiểm tra máy có vào được Internet không. "
                           f"Chi tiet: {(r.stderr or r.stdout).strip()[-300:]}")
    except Exception as e:
        return False, f"Lỗi khi cài: {e}"
    if not ts_da_cai():
        return False, "Script chạy xong nhưng không thấy lệnh tailscale - cài thất bại."
    return True, "Đã cài Tailscale."


def ts_luu_authkey(authkey):
    authkey = (authkey or "").strip()
    if len(authkey) < 20:
        return False, "Authkey không đúng định dạng. Sao chép lại từ trang Tailscale admin."
    try:
        fd = os.open(TS_AUTHKEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(authkey + "\n")
    except OSError as e:
        return False, f"Không lưu được authkey: {e}"
    return True, "Đã lưu authkey."


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
        return False, "Chưa cài Tailscale."
    if not ts_co_authkey():
        return False, "Chưa có authkey."
    try:
        with open(TS_AUTHKEY_FILE) as f:
            authkey = f.read().strip()
    except OSError as e:
        return False, f"Không đọc được authkey đã lưu: {e}"

    subprocess.run(["systemctl", "enable", "--now", "tailscaled"],
                   capture_output=True, timeout=20)
    r = subprocess.run(["tailscale", "up", f"--authkey={authkey}",
                        f"--hostname={TS_HOSTNAME}", "--accept-dns=false"],
                       capture_output=True, text=True, timeout=40)
    if r.returncode != 0:
        return False, f"Không kết nối được: {(r.stderr or r.stdout).strip()[:250]}"
    return True, "Đã kết nối Tailscale."


def ts_tat():
    """Ngat ket noi nhung GIU LAI dang ky thiet bi trong tailnet - bat lai
    nhanh, khong can authkey moi (khac voi 'quen thiet bi' o duoi)."""
    r = subprocess.run(["tailscale", "down"], capture_output=True, text=True, timeout=20)
    if r.returncode != 0:
        return False, f"Không tắt được: {(r.stderr or r.stdout).strip()[:200]}"
    return True, "Đã ngắt kết nối Tailscale."


def ts_quen_thiet_bi():
    """Dang xuat han + xoa authkey - thiet bi bien mat khoi tailnet, phai
    dan authkey moi neu muon bat lai."""
    subprocess.run(["tailscale", "logout"], capture_output=True, timeout=20)
    try:
        os.remove(TS_AUTHKEY_FILE)
    except OSError:
        pass
    return True, "Đã đăng xuất và xóa authkey khỏi máy."


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
            <div class="msg warn">Chưa cài <code>cloudflared</code>. Máy phải vào được
            Internet để tải gói cài chính chủ từ Cloudflare.</div>
            <form method="POST" action="/remote/cai" style="margin-top:12px;">
              <button type="submit" data-busy="Đang tải và cài, tới 2 phút...">
                ⬇ Cài cloudflared</button>
            </form>"""
        elif not tok:
            khoi = """
            <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
              Vào <strong>Cloudflare Zero Trust &rarr; Networks &rarr; Tunnels</strong>,
              tạo một tunnel mới, chọn <em>Debian / arm64</em> (máy tính: amd64), rồi sao chép phần token
              trong dòng lệnh cài đặt (chuỗi dài sau <code>--token</code>).
              Trỏ tunnel đó vào <code>http://127.0.0.1:80</code>.</p>
            <form method="POST" action="/remote/token">
              <label>Tunnel token</label>
              <input type="password" name="token" required autocomplete="off"
                     placeholder="eyJhIjoiN...">
              <div class="row" style="margin-top:13px;">
                <button type="submit" data-busy="Đang lưu...">Lưu và bật đường hầm</button>
              </div>
            </form>"""
        else:
            trang_thai = ('<span style="color:#6ee7a0;">🟢 Đường hầm đang chạy</span>'
                          if chay else '<span style="color:#8b93a1;">⚪ Đường hầm đang tắt</span>')
            mien_html = (f'<p style="margin:9px 0 0;">Truy cập tại: '
                         f'<a href="https://{_esc(mien)}" target="_blank" rel="noopener">'
                         f'<code>https://{_esc(mien)}</code></a></p>' if mien else
                         '<p style="color:#8b93a1;font-size:13px;margin:9px 0 0;">'
                         'Tên miền do bạn đặt trong Cloudflare - xem trong trang Tunnels.</p>')
            nut = ('<form method="POST" action="/remote/tat" style="display:inline;">'
                   '<button type="submit" class="red" data-busy="Đang tắt...">⏹ Tắt đường hầm</button></form>'
                   if chay else
                   '<form method="POST" action="/remote/bat" style="display:inline;">'
                   '<button type="submit" data-busy="Đang bật...">▶ Bật đường hầm</button></form>')
            khoi = f"""
            <p style="margin:0;">{trang_thai}</p>
            {mien_html}
            <div class="row" style="gap:10px;margin-top:13px;flex-wrap:wrap;">
              {nut}
              <button type="button" class="red" data-mo-hop="hop-xoa-token">
                Xoá token</button>
            </div>

            <!-- Hop thoai xac nhan.
                 VI SAO KHONG DUNG confirm() cua trinh duyet nua (anh Thoai
                 yeu cau 19/09/2026 "phai hoi xac nhan de dam bao chac an"):
                 tren man hinh cam ung, hop confirm() hien ra voi nut OK
                 nam ngay duoi ngon tay dang bam - rat de cham trung lan
                 hai ma khong kip doc. Ma day la thao tac CO THE TU KHOA
                 CHINH MINH RA NGOAI: neu dang vao dashboard QUA duong ham
                 Cloudflare, xoa token la mat ket noi NGAY LAP TUC, khong
                 con duong nao vao lai tu xa - phai co mat tai cho.
                 Hop thoai nay bat tich vao o dong y truoc, va nut xac nhan
                 nam XA nut mo, nen khong the bam nham. -->
            <dialog id="hop-xoa-token" style="border:1px solid #2B3746;border-radius:12px;
                    background:#141A23;color:#E3E8EF;padding:0;max-width:560px;width:94vw;">
              <div style="padding:18px 20px;border-bottom:1px solid #1F2733;">
                <strong style="font-size:16px;color:#F87171;">Xoá token Cloudflare?</strong>
              </div>
              <div style="padding:18px 20px;">
                <p style="margin:0 0 12px;">Sau khi xoá:</p>
                <ul style="margin:0 0 14px;padding-left:20px;line-height:1.7;">
                  <li>Đường hầm <strong>tắt ngay</strong>, tên miền hiện tại không vào được nữa.</li>
                  <li>Muốn dùng lại phải <strong>tạo token mới</strong> trên trang Cloudflare
                      Zero Trust rồi dán vào đây.</li>
                </ul>
                <div class="msg err" style="margin:0 0 14px;">
                  <strong>Cẩn thận:</strong> nếu bạn đang mở trang này
                  <em>qua chính đường hầm Cloudflare</em> thì xoá xong là
                  <strong>mất kết nối ngay lập tức</strong> — phải có mặt tại chỗ
                  (hoặc vào bằng WiFi/LAN nội bộ) mới làm tiếp được.
                </div>
                <label style="display:flex;gap:10px;align-items:flex-start;margin:0;">
                  <input type="checkbox" id="dong-y-xoa-token"
                         style="width:20px;height:20px;min-height:20px;margin-top:2px;flex:none;">
                  <span>Tôi hiểu và vẫn muốn xoá token.</span>
                </label>
              </div>
              <div class="row" style="padding:0 20px 18px;justify-content:flex-end;">
                <button type="button" class="gray" data-dong-hop>Huỷ</button>
                <form method="POST" action="/remote/xoa-token" style="display:inline;">
                  <button type="submit" class="red" id="nut-xoa-token" disabled
                          data-busy="Đang xoá...">Xoá token</button>
                </form>
              </div>
            </dialog>
            <script>
            (function() {{
              var o = document.getElementById('dong-y-xoa-token');
              var n = document.getElementById('nut-xoa-token');
              if (o && n) o.addEventListener('change', function() {{ n.disabled = !o.checked; }});
            }})();
            </script>"""

        # --- Tailscale (lua chon phu, KHONG thay the Cloudflare o tren) ---
        ts_cai = ts_da_cai()
        ts_key = ts_co_authkey() if ts_cai else False
        ts_tt = ts_trang_thai() if ts_cai else {"dang_ket_noi": False, "ip": "",
                                                "ten_mien": "", "can_dang_nhap": False,
                                                "ro": False}

        if not ts_cai:
            ts_khoi = """
            <div class="msg warn">Chưa cài <code>tailscale</code>. Máy phải vào được
            Internet để tải gói cài chính chủ từ Tailscale.</div>
            <form method="POST" action="/remote/ts/cai" style="margin-top:12px;">
              <button type="submit" class="gray" data-busy="Đang tải và cài, tới 2 phút...">
                ⬇ Cài Tailscale</button>
            </form>"""
        elif not ts_key:
            ts_khoi = """
            <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
              Vào <strong>Tailscale admin console &rarr; Settings &rarr; Keys</strong>,
              tạo một <em>Auth key</em> (nên chọn <em>Reusable</em> nếu muốn dùng lại
              nhiều lần, hoặc đặt hạn sử dụng phù hợp).</p>
            <form method="POST" action="/remote/ts/authkey">
              <label>Auth key</label>
              <input type="password" name="authkey" required autocomplete="off"
                     placeholder="tskey-auth-...">
              <div class="row" style="margin-top:13px;">
                <button type="submit" class="gray" data-busy="Đang lưu và kết nối...">
                  Lưu và kết nối</button>
              </div>
            </form>"""
        else:
            if not ts_tt["ro"]:
                ts_trang = ('<span style="color:#8b93a1;">⚪ Không đọc được trạng thái '
                           '(chạy <code>tailscale status</code> trên Terminal để xem chi tiết)</span>')
            elif ts_tt["dang_ket_noi"]:
                mien_html = (f'<p style="margin:9px 0 0;">Truy cập tại: '
                            f'<a href="http://{_esc(ts_tt["ten_mien"])}" target="_blank" rel="noopener">'
                            f'<code>http://{_esc(ts_tt["ten_mien"])}</code></a> '
                            f'<span style="color:#8b93a1;">(hoặc IP '
                            f'<code>{_esc(ts_tt["ip"])}</code>)</span></p>'
                            if ts_tt["ten_mien"] else
                            f'<p style="margin:9px 0 0;">Địa chỉ trong tailnet: '
                            f'<code>{_esc(ts_tt["ip"])}</code></p>')
                ts_trang = (f'<span style="color:#6ee7a0;">🟢 Đang kết nối</span>'
                           f'{mien_html}')
            elif ts_tt["can_dang_nhap"]:
                ts_trang = ('<span style="color:#ffb74d;">⚠️ Authkey đã lưu nhưng chưa '
                           'đăng nhập được - có thể authkey hết hạn/đã dùng hết lượt. '
                           'Xóa và dán authkey mới.</span>')
            else:
                ts_trang = '<span style="color:#8b93a1;">⚪ Đang tắt</span>'

            ts_nut = ('<form method="POST" action="/remote/ts/tat" style="display:inline;">'
                     '<button type="submit" class="red" data-busy="Đang tắt...">⏹ Tắt</button></form>'
                     if ts_tt["dang_ket_noi"] else
                     '<form method="POST" action="/remote/ts/bat" style="display:inline;">'
                     '<button type="submit" class="gray" data-busy="Đang kết nối...">▶ Bật</button></form>')
            ts_khoi = f"""
            <p style="margin:0;">{ts_trang}</p>
            <div class="row" style="gap:10px;margin-top:13px;flex-wrap:wrap;">
              {ts_nut}
              <button type="button" class="red" data-mo-hop="hop-quen-ts">
                Quên thiết bị</button>
            </div>

            <!-- Xac nhan giong het ly do o hop xoa token Cloudflare: day
                 cung la thao tac tu cat duong vao tu xa cua chinh minh. -->
            <dialog id="hop-quen-ts" style="border:1px solid #2B3746;border-radius:12px;
                    background:#141A23;color:#E3E8EF;padding:0;max-width:560px;width:94vw;">
              <div style="padding:18px 20px;border-bottom:1px solid #1F2733;">
                <strong style="font-size:16px;color:#F87171;">Quên thiết bị Tailscale?</strong>
              </div>
              <div style="padding:18px 20px;">
                <p style="margin:0 0 12px;">Sau khi quên:</p>
                <ul style="margin:0 0 14px;padding-left:20px;line-height:1.7;">
                  <li>Pi <strong>đăng xuất khỏi tailnet</strong> và biến mất khỏi
                      danh sách máy.</li>
                  <li>Authkey đang lưu bị <strong>xoá khỏi máy</strong>.</li>
                  <li>Muốn dùng lại phải lấy <strong>authkey mới</strong> từ trang
                      Tailscale rồi dán vào đây.</li>
                </ul>
                <div class="msg err" style="margin:0 0 14px;">
                  <strong>Cẩn thận:</strong> nếu bạn đang vào máy
                  <em>qua chính Tailscale</em> thì quên xong là mất kết nối ngay.
                </div>
                <label style="display:flex;gap:10px;align-items:flex-start;margin:0;">
                  <input type="checkbox" id="dong-y-quen-ts"
                         style="width:20px;height:20px;min-height:20px;margin-top:2px;flex:none;">
                  <span>Tôi hiểu và vẫn muốn quên thiết bị này.</span>
                </label>
              </div>
              <div class="row" style="padding:0 20px 18px;justify-content:flex-end;">
                <button type="button" class="gray" data-dong-hop>Huỷ</button>
                <form method="POST" action="/remote/ts/quen" style="display:inline;">
                  <button type="submit" class="red" id="nut-quen-ts" disabled
                          data-busy="Đang quên...">Quên thiết bị</button>
                </form>
              </div>
            </dialog>
            <script>
            (function() {{
              var o = document.getElementById('dong-y-quen-ts');
              var n = document.getElementById('nut-quen-ts');
              if (o && n) o.addEventListener('change', function() {{ n.disabled = !o.checked; }});
            }})();
            </script>
            <details style="margin-top:13px;">
              <summary style="cursor:pointer;color:#8b93a1;font-size:13px;">
                Authkey hết hạn / muốn đổi sang key khác?</summary>
              <p style="color:#8b93a1;font-size:13px;margin:9px 0 11px;">
                Tạo Auth key mới trong <strong>Tailscale admin console &rarr; Settings
                &rarr; Keys</strong>, dán vào đây - KHÔNG cần bấm "Quên thiết bị" trước,
                thiết bị vẫn giữ nguyên tên/địa chỉ cũ.</p>
              <form method="POST" action="/remote/ts/authkey">
                <input type="password" name="authkey" required autocomplete="off"
                       placeholder="tskey-auth-...">
                <div class="row" style="margin-top:11px;">
                  <button type="submit" class="gray" data-busy="Đang đổi key...">
                    Đổi sang key này</button>
                </div>
              </form>
            </details>"""

        ts_card = f"""
        <div class="card" style="border-left:4px solid #5a6672;">
          <h3>Tailscale <span style="color:#8b93a1;font-size:12px;font-weight:400;">
              (lựa chọn phụ - vào được SSH/dịch vụ khác của Pi, không chỉ trang web)</span></h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Tạo mạng riêng ảo giữa các thiết bị CỦA CHÍNH BẠN - máy nào muốn vào cũng
            phải cài app Tailscale và đăng nhập cùng tài khoản trước. Khác với Cloudflare
            ở trên (ai có link cũng vào được qua trình duyệt), Tailscale chỉ hợp khi
            chính bạn muốn truy cập đầy đủ hơn từ thiết bị cá nhân đã cài sẵn.</p>
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
            <div class="msg ok" style="margin:0 0 13px;">Đã tạo token. <strong>Chép ngay
              bây giờ</strong> - rời khỏi trang này là không xem lại được nữa.</div>
            <label>Token (chỉ hiện một lần)</label>
            <textarea readonly rows="2" onclick="this.select();"
                      style="width:100%;font-family:monospace;font-size:13px;">{_esc(token_moi)}</textarea>
            <p style="margin:13px 0 5px;">Đưa nguyên đoạn này cho AI bên kia:</p>
            <textarea readonly rows="4" onclick="this.select();"
                      style="width:100%;font-family:monospace;font-size:13px;">Tôi có một thiết bị Console System ở xa. Hãy đọc tài liệu hướng dẫn tại:
{_esc(_goc_ngoai())}/ai
Dùng header: Authorization: Bearer {_esc(token_moi)}
Đọc tài liệu đó trước, rồi giúp tôi làm việc với thiết bị mạng đang cắm vào nó.</textarea>"""
        elif ai["has_token"]:
            ai_khoi = f"""
            <table style="max-width:470px;margin-bottom:12px;">
              <tr><th style="width:150px;">Trạng thái</th>
                  <td><span style="color:#6ee7a0;">🟢 Đang bật</span></td></tr>
              <tr><th>Quyền</th><td><code>{_esc(ai['scope'])}</code>
                  {'&mdash; chỉ đọc' if ai['scope'] == 'read'
                    else '&mdash; đọc và gõ được lệnh vào thiết bị mạng'}</td></tr>
              <tr><th>Tạo lúc</th><td>{_esc(ai['created'])}</td></tr>
              <tr><th>Dùng lần cuối</th>
                  <td>{_esc(ai['last_used']) or '<span style="color:#8b93a1;">chưa dùng</span>'}</td></tr>
            </table>
            <p style="color:#8b93a1;font-size:13px;margin:0 0 12px;">
              Token thật không hiện lại được (trong máy chỉ lưu bản băm SHA256).
              Mất thì tạo cái mới - cái cũ tự hết hiệu lực.</p>
            <div class="row" style="gap:10px;flex-wrap:wrap;">
              <form method="POST" action="/remote/api-token">
                <input type="hidden" name="scope" value="read">
                <button type="submit" class="gray" data-busy="Đang tạo...">Tạo token mới (chỉ đọc)</button>
              </form>
              <form method="POST" action="/remote/api-token">
                <input type="hidden" name="scope" value="full">
                <button type="submit" class="gray" data-busy="Đang tạo...">Tạo token mới (đầy đủ)</button>
              </form>
              <form method="POST" action="/remote/api-thu-hoi"
                    onsubmit="return confirm('Thu hồi token? AI bên kia sẽ mất quyền truy cập ngay lập tức.');">
                <button type="submit" class="red">Thu hồi</button>
              </form>
            </div>"""
        else:
            ai_khoi = """
            <p style="color:#8b93a1;font-size:13px;margin:0 0 12px;">
              Đang <strong>tắt</strong>. Tạo token để một AI (hoặc phần mềm khác) đọc
              được trạng thái thiết bị và làm việc với switch/router đang cắm.
              AI chỉ cần một đường dẫn <code>/ai</code> là tự biết phải gọi gì.</p>
            <div class="row" style="gap:10px;flex-wrap:wrap;">
              <form method="POST" action="/remote/api-token">
                <input type="hidden" name="scope" value="read">
                <button type="submit" class="blue" data-busy="Đang tạo...">
                  🔍 Tạo token CHỈ ĐỌC</button>
              </form>
              <form method="POST" action="/remote/api-token"
                    onsubmit="return confirm('Token quyền đầy đủ cho phép GÕ LỆNH vào switch/router đang cắm.\\n\\nChỉ tạo khi thật sự cần, và thu hồi ngay khi xong việc.');">
                <input type="hidden" name="scope" value="full">
                <button type="submit" data-busy="Đang tạo...">
                  ⌨️ Tạo token ĐẦY ĐỦ (gõ được lệnh)</button>
              </form>
            </div>
            <p style="color:#8b93a1;font-size:13px;margin-top:11px;">
              Nên bắt đầu bằng <strong>chỉ đọc</strong>. Chỉ nâng lên đầy đủ khi thật
              sự cần gõ lệnh, và thu hồi ngay khi xong.</p>"""

        ai_card = f"""
        <div class="card">
          <h3>Cho AI / máy khác truy cập</h3>
          {ai_khoi}
        </div>"""

        log_html = ""
        if cai and tok:
            log_html = f"""
            <h2>Nhật ký đường hầm</h2>
            <pre style="background:#12151b;padding:13px;border-radius:6px;overflow:auto;
                        max-height:290px;font-size:12px;">{_esc(nhat_ky(30))}</pre>"""

        body = f"""
        {msg_html}
        <div class="card">
          <h3>Truy cập từ xa qua Cloudflare</h3>
          <p style="color:#8b93a1;font-size:13px;margin:0 0 11px;">
            Đưa Pi tới điểm xa, cắm console và cắm mạng internet là vào cấu hình được
            từ bất kỳ đâu. Không cần mở port trên router, không cần IP tĩnh, chạy
            được cả sau 4G.</p>
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
                Cloudflare, trước khi chạm tới máy</li>
            <li>Token được lưu quyền 600, chỉ root đọc được. Bất kỳ ai có token đều
                dùng lại được đường hầm - đừng gửi qua chat/email</li>
            <li>Xong việc thì <strong>tắt đường hầm</strong>, đừng để mở thường xuyên</li>
            <li>Token cho AI mặc định <strong>tắt</strong>. Token quyền đầy đủ gõ được
                lệnh vào switch/router - chỉ tạo khi cần, thu hồi ngay khi xong.
                Mỗi lần máy gọi vào đều được ghi nhật ký (xem ở menu Nhật ký).</li>
          </ul>
        </div>

        {log_html}"""

        return render_page(body, active="/remote", title="Truy cập từ xa",
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
        return page(msg="Đã thu hồi token. Máy/AI bên kia mất quyền truy cập ngay.",
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
