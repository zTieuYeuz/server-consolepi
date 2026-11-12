# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Console Pi - Tab SSH

Chi con 1 che do duy nhat: SSH TUONG TAC bang terminal that (ttyd + tmux),
go duoc moi thu nhu PuTTY. Kem ngay duoi khung terminal 1 O SOAN TAP LENH:
chon tap lenh co san tu Thu vien -> sua lai IP/ten cho dung -> Copy hoac dan
thang vao terminal.

DA BO "chay hang loat" (Netmiko) o tab nay theo yeu cau: no trung vai tro voi
cong cu "Netmiko Config" ben Network Tools, va trong thuc te lam viec thi
duong nao cung phai nhin man hinh thiet bi that de biet lenh an vao chua.

TU DIEN MAT KHAU - vi sao KHONG dung sshpass:
  - sshpass -p '<mk>' dat mat khau THANG TREN DONG LENH: ai chay `ps` cung
    doc duoc, va no con nam lai trong lich su cuon cua terminal.
  - Cach dung o day: go lenh ssh vao terminal, roi DOI cho toi khi dong cuoi
    cua man hinh dung la dau nhac mat khau, moi go mat khau vao. Dau nhac
    mat khau khong hien lai ky tu nen mat khau khong bao gio hien tren man
    hinh, khong vao `ps`, khong vao lich su lenh. Da kiem chung that bang
    tmux capture-pane truoc khi viet ham nay.
  - Neu qua 12 giay khong thay dau nhac (thiet bi cham, dung khoa, khong ket
    noi duoc...) thi BAO THAT la khong thay, khong im lang coi nhu xong.
"""
from consolesystem.core import taisan as _taisan
import sys as _sys
_sys.modules["ui.ssh"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import json
import os
import re
import subprocess
import time

from flask import request

from ui.layout import render_page, gan_phien_tmux
from ui.commands import load_library, dan_thong_minh
from ui.soanlenh import khoi_soan_lenh, khoi_copy_terminal
from ui.terminal import SSH_SESSION, tmux_session_exists, service_active  # noqa: F401
from consolesystem.features.terminal import ssh_phien as SP
from consolesystem.web.khung_mk import o_mat_khau
from consolesystem.core.esc import esc as _esc

# Dau nhac mat khau cua ssh ("...'s password:", "Enter passphrase for key ...:")
_DAU_NHAC_MK = re.compile(r"(?:password|passphrase).*:\s*$", re.I)




def _chup_man_hinh(session):
    """Doc noi dung dang hien tren man hinh cua phien tmux."""
    try:
        r = subprocess.run(["tmux", "capture-pane", "-p", "-t", session],
                           capture_output=True, text=True, timeout=5)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def _dong_cuoi(text):
    dong = [l.rstrip() for l in (text or "").splitlines() if l.strip()]
    return dong[-1] if dong else ""


def _la_dau_nhac_mat_khau(dong):
    return bool(dong) and bool(_DAU_NHAC_MK.search(dong))


def _cho_dau_nhac_mat_khau(session, truoc, giay_toi_da=12):
    """
    Doi cho toi khi man hinh terminal hien dau nhac mat khau.

    Bat buoc man hinh phai KHAC luc truoc khi go lenh: neu khong so sanh, mot
    dau nhac mat khau con sot lai cua phien cu se bi cham nham la dau nhac
    cua phien vua mo, va mat khau se bi go nham cho.
    """
    het_han = time.time() + giay_toi_da
    while time.time() < het_han:
        time.sleep(0.3)
        hien = _chup_man_hinh(session)
        if hien and hien != truoc and _la_dau_nhac_mat_khau(_dong_cuoi(hien)):
            return True
    return False


DIR_YC = os.environ.get("CS_SSH_YC") or "/var/lib/console-ssh/yeu-cau"


def lenh_hien_tai(ten):
    """Ten lenh dang chay o tien canh cua phien tmux (vd 'ssh', 'python3')."""
    try:
        r = subprocess.run(["tmux", "display-message", "-p", "-t", ten, "#{pane_current_command}"], capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def ghi_yeu_cau(ten, host, user, cong):
    """Yeu cau ket noi cho launcher: file JSON nho trong thu muc yeu cau (chi chua dich, KHONG co mat khau)."""
    os.makedirs(DIR_YC, exist_ok=True)
    f = os.path.join(DIR_YC, ten + ".json")
    tam = f + ".tmp"
    with open(os.open(tam, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o660), "w", encoding="utf-8") as h:
        json.dump({"host": host, "user": user, "port": int(cong)}, h)
    try:
        import grp
        os.chown(tam, -1, grp.getgrnam("console-ssh").gr_gid)
    except (KeyError, OSError, ImportError):
        pass                              # chua co user console-ssh (may chua mo phien lan nao): launcher chay root doc duoc
    os.replace(tam, f)


def start_ssh_in_tmux(host, user, port=22, password="", nguoi=""):
    """Chay lenh ssh trong phien tmux RIENG cua `nguoi`; tu dien mat khau neu duoc nhap san. Moi may dich chi mot nguoi dieu khien (ssh_phien.lay_khoa)."""
    host = (host or "").strip()
    user = (user or "").strip()
    if not host or not user:
        return False, "Thiếu địa chỉ hoặc tài khoản."

    # Loc dau vao: host/user duoc ghep thanh 1 DONG LENH chay trong shell cua
    # terminal, khong loc thi mot gia tri kieu "1.1.1.1; rm -rf /" se chay
    # that su tren Pi.
    #
    # LO HONG RIENG DA VA (ra soat lai code): ca 2 mau tren DEU cho phep dau
    # "-" o VI TRI DAU chuoi. Voi lenh `ssh`, mot host/user bat dau bang "-"
    # la ky thuat CHEN CO LENH THAT SU va nguy hiem - vi du host =
    # "-oProxyCommand=<lenh tuy y>" khien ssh chay LENH TUY Y ngay khi ket
    # noi, du cac ky tu nguy hiem nhu ";  $ ` & |" da bi chan tu truoc. Nay
    # bat buoc KY TU DAU TIEN phai la chu/so, khong duoc la dau "-" (hay bat
    # ky ky tu dac biet nao khac).
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:\-]{0,254}", host):
        return False, ("Địa chỉ không hợp lệ (phải bắt đầu bằng chữ/số, sau đó cho "
                       "thêm các dấu . - _ :).")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._\-\\]{0,63}", user):
        return False, ("Tài khoản không hợp lệ (phải bắt đầu bằng chữ/số, sau đó cho "
                       "thêm các dấu . - _ \\).")
    try:
        cong = int(port or 22)
    except (TypeError, ValueError):
        return False, "Cổng không hợp lệ."
    if not 1 <= cong <= 65535:
        return False, "Cổng phải trong khoảng 1-65535."

    may = "%s:%s" % (host.lower(), cong)
    che, chu = SP.lay_khoa(may, nguoi or "khach")
    if che != "dieu_khien":
        return False, ("Máy %s đang do %s điều khiển. Bạn chỉ xem được; bấm \"Xin điều khiển\" để nhờ %s nhường." % (may, chu, chu))
    try:
        _ma, PHIEN_TMUX = SP.phien_cua(nguoi or "khach", dang_chay=tmux_session_exists)
    except ValueError as e:
        return False, str(e)
    if not tmux_session_exists(PHIEN_TMUX):
        return False, ("Chưa có phiên terminal SSH. Mở khung terminal bên dưới "
                       "de tao phien truoc roi bam lai.")

    truoc = _chup_man_hinh(PHIEN_TMUX)
    # Terminal dang dung o 1 dau nhac mat khau cu: go lenh vao day thi ca dong
    # lenh se bi hieu la mat khau. Dung lai va noi ro, thay vi lam roi them.
    if _la_dau_nhac_mat_khau(_dong_cuoi(truoc)):
        return False, ("Khung terminal đang dừng ở dấu nhắc mật khẩu của lần trước. "
                       "Vào khung terminal xử lý xong (nhập mật khẩu hoặc bấm Ctrl+C) "
                       "rồi bấm Kết nối lại.")

    if lenh_hien_tai(PHIEN_TMUX) == "ssh":
        return False, "Đang có một kết nối SSH trong terminal. Thoát kết nối đó (gõ exit) rồi bấm Kết nối lại."
    # KHONG go lenh vao shell (phien SSH khong con shell - LOI-013): ghi yeu cau cho launcher phien-ssh.py, no tu chay ssh bang danh sach doi so.
    try:
        ghi_yeu_cau(PHIEN_TMUX, host, user, cong)
    except OSError as e:
        return False, f"Lỗi: {e}"

    if not password:
        return True, (f"Đã gửi lệnh kết nối tới {host}. "
                      f"Nhập mật khẩu trong khung terminal bên dưới.")

    if not _cho_dau_nhac_mat_khau(PHIEN_TMUX, truoc, 12):
        return True, (f"Đã gửi lệnh kết nối tới {host} nhưng sau 12 giây không thấy dấu "
                      f"nhắc mật khẩu - có thể thiết bị phản hồi chậm, đang dùng khóa (key), "
                      f"hoặc không kết nối được. Xem khung terminal bên dưới, nhập tay nếu cần.")

    try:
        # -l = gui NGUYEN VAN. Thieu -l thi tmux dich cac chuoi trung ten phim
        # (vi du mat khau chua "Enter", "Space") thanh phim bam thay vi ky tu.
        subprocess.run(["tmux", "send-keys", "-l", "-t", PHIEN_TMUX, password],
                       capture_output=True, timeout=5)
        subprocess.run(["tmux", "send-keys", "-t", PHIEN_TMUX, "Enter"],
                       capture_output=True, timeout=5)
    except Exception as e:
        return False, f"Lỗi khi gửi mật khẩu: {e}"

    return True, (f"Đã kết nối tới {host} và tự điền mật khẩu. "
                  f"Xem kết quả trong khung terminal bên dưới.")


# ---------------------------------------------------------------------------
# JS cua trang. De rieng ngoai f-string vi co rat nhieu dau ngoac nhon, nhet
# vao f-string phai nhan doi het - rat de sai va kho doc.
# ---------------------------------------------------------------------------
SSH_JS = _taisan.doc("features/terminal/ssh.SSH_JS.html")


def _nguoi():
    from flask import session
    return session.get("user") or "khach"


def _khoi_trang_thai_html(nguoi):
    """Danh sach may dang co nguoi dieu khien + nut Xin dieu khien / Nhuong / Thoi (cap nhat moi 5 giay bang JS)."""
    ds = SP.trang_thai(nguoi)
    if not ds:
        return '<p class="tk-ghi" style="margin:0;">Chưa có máy nào đang được điều khiển qua SSH.</p>'
    ra = ""
    for k in ds:
        may = _esc(k["may"])
        if k["cua_toi"]:
            nut = ('<form method="POST" action="/ssh/tha" style="display:inline"><input type="hidden" name="may" value="%s"><button class="gray small">Thôi điều khiển</button></form>' % may)
            if k["xin"]:
                nut += (' <b>%s xin điều khiển</b> <form method="POST" action="/ssh/nhuong" style="display:inline"><input type="hidden" name="may" value="%s">'
                        '<button class="small">Nhường</button></form>' % (_esc(k["xin"]), may))
            ra += '<div>%s: <b>bạn đang điều khiển</b> %s</div>' % (may, nut)
        else:
            ra += ('<div>%s: <b>%s</b> đang điều khiển (bạn chỉ xem) <form method="POST" action="/ssh/xin" style="display:inline"><input type="hidden" name="may" value="%s">'
                   '<button class="small">Xin điều khiển</button></form> <a class="tk-nut" href="/ssh?xem=%s">Xem</a></div>' % (may, _esc(k["chu"]), may, _esc(k["chu"])))
    return ra


def _render(msg="", ok=True, prefill="", xem=""):
    nguoi = _nguoi()
    try:
        if xem and xem != nguoi:
            ma = SP.ma_xem(xem)
        else:
            ma = SP.phien_cua(nguoi, dang_chay=tmux_session_exists)[0]
    except ValueError as e:
        msg, ok, ma = str(e), False, None
    term_running = service_active("console-system-term-phien.service")
    msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""
    term_status = ("" if term_running else
                   '<div class="msg err">Dich vu terminal SSH chua chay: '
                   '<code>sudo systemctl start console-system-term-phien</code></div>')

    # Bo trong: chi 1 hang nhap gon, khong tieu de/doan giai thich dai - de
    # danh cang nhieu chieu cao cang tot cho khung terminal.
    body = f"""
    {msg_html}
    {term_status}
    <div id="bao_server" class="msg ok" style="display:none;"></div>
    {('<div class="msg ok">Bạn đang <b>xem</b> terminal của %s (chỉ đọc). <a href="/ssh">Về terminal của tôi</a></div>' % _esc(xem)) if (xem and xem != nguoi) else ''}
    <div id="ssh-ai-dieu-khien" class="card" style="padding:8px 12px;margin-bottom:8px;">{_khoi_trang_thai_html(nguoi)}</div>
    <script>setInterval(function(){{if(document.hidden)return;fetch('/ssh/trang-thai-html',{{cache:'no-store'}}).then(function(r){{return r.text();}}).then(function(h){{document.getElementById('ssh-ai-dieu-khien').innerHTML=h;}}).catch(function(){{}});}},5000);</script>

    <form method="POST" action="/ssh/connect" id="form_ket_noi" class="row"
          style="align-items:flex-end;margin-bottom:10px;">
      <div><label style="margin-top:0;">Địa chỉ</label>
        <input type="text" name="host" placeholder="192.168.1.1" style="max-width:180px;" required></div>
      <div><label style="margin-top:0;">Tài khoản</label>
        <input type="text" name="user" placeholder="admin" style="max-width:140px;" required></div>
      <div style="flex:1 1 240px;max-width:340px;">{o_mat_khau("password", "Mật khẩu", "để trống = tự nhập")}</div>
      <div><label style="margin-top:0;">Cổng</label>
        <input type="number" name="port" value="22" style="max-width:85px;"></div>
      <div><button type="submit" id="nut_ket_noi">🔑 Kết nối</button></div>
    </form>

    <div class="card" style="padding:0;overflow:hidden;margin-bottom:12px;">
      <iframe src="{('/term-phien/?arg=' + ma) if ma else 'about:blank'}" title="SSH terminal"
              style="width:100%;height:calc(100vh - 330px);min-height:360px;border:0;display:block;background:#000;"></iframe>
    </div>

    {khoi_copy_terminal()}
    {khoi_soan_lenh("/ssh/paste", "consolepi-ssh-o-lenh", prefill)}
    {SSH_JS}"""

    html = render_page(body, active="/ssh", title="SSH", subtitle="")
    return gan_phien_tmux(html, SP.phien_cua(nguoi, dang_chay=tmux_session_exists)[1] if ma else SSH_SESSION)


def register_ssh(app):
    @app.route("/ssh")
    def ssh_page():
        lib_idx = request.args.get("lib")
        prefill = ""
        if (lib_idx or "").isdigit():
            lib = load_library()
            i = int(lib_idx)
            if 0 <= i < len(lib):
                prefill = lib[i].get("commands", "")
        return _render(prefill=prefill, xem=request.args.get("xem", ""))

    def _tra_ve(ok, msg, prefill=""):
        """
        Goi tu fetch (JS) thi tra JSON de trang KHONG phai tai lai - vua muot
        hon, vua khong lam khung terminal nap lai tu dau, vua khong dinh hop
        thoai "Leave site?" cua ttyd. Goi kieu form thuong (JS loi/bi tat) thi
        van dung nhu cu - khong bao gio mat duong lui.
        """
        if request.headers.get("X-Console-Pi") == "fetch":
            from flask import jsonify
            return jsonify({"ok": ok, "msg": msg})
        return _render(msg=msg, ok=ok, prefill=prefill)

    @app.route("/ssh/connect", methods=["POST"])
    def ssh_connect():
        f = request.form
        ok, msg = start_ssh_in_tmux(f.get("host", "").strip(),
                                    f.get("user", "").strip(),
                                    f.get("port", 22) or 22,
                                    f.get("password", ""), nguoi=_nguoi())
        # Khong bao gio tra mat khau nguoc lai trang.
        return _tra_ve(ok, msg)

    @app.route("/ssh/paste", methods=["POST"])
    def ssh_paste():
        noi_dung = request.form.get("noi_dung", "")
        if not noi_dung.strip():
            return _tra_ve(False, "Ô lệnh đang trống - chưa có gì để dán.", noi_dung)
        # Tu chon cach dan cho dung voi thu dang chay trong terminal (dang
        # SSH vao thiet bi thi gui tung dong; con dang o shell thi dan ca
        # khoi, khong dong nao chay). Xem dan_thong_minh().
        try:
            ten = SP.phien_cua(_nguoi(), dang_chay=tmux_session_exists)[1]
        except ValueError as e:
            return _tra_ve(False, str(e), noi_dung)
        if lenh_hien_tai(ten) != "ssh":
            return _tra_ve(False, "Chưa có kết nối SSH đang chạy: chỉ dán được vào thiết bị đã kết nối (terminal này không có shell của Pi).", noi_dung)
        ok, msg = dan_thong_minh(ten, noi_dung)
        return _tra_ve(ok, msg, noi_dung)

    def _may_hop_le(may):
        return bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:\-]{0,260}", may or ""))

    @app.route("/ssh/xin", methods=["POST"])
    def ssh_xin():
        may = request.form.get("may", "")
        ok, msg = SP.xin(may, _nguoi()) if _may_hop_le(may) else (False, "Máy không hợp lệ.")
        return _tra_ve(ok, msg)

    @app.route("/ssh/nhuong", methods=["POST"])
    def ssh_nhuong():
        may = request.form.get("may", "")
        ok, msg = SP.nhuong(may, _nguoi()) if _may_hop_le(may) else (False, "Máy không hợp lệ.")
        return _tra_ve(ok, msg)

    @app.route("/ssh/tha", methods=["POST"])
    def ssh_tha():
        may = request.form.get("may", "")
        ok = _may_hop_le(may) and SP.tha(may, _nguoi())
        return _tra_ve(ok, "Đã thôi điều khiển." if ok else "Bạn không đang điều khiển máy này.")

    @app.route("/ssh/trang-thai-html")
    def ssh_trang_thai_html():
        return _khoi_trang_thai_html(_nguoi())

    return app
