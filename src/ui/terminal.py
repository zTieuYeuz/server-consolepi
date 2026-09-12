"""
Console Pi - Terminal local (yeu cau so 5) va SSH tuong tac (mot phan yeu cau 7)

Kien truc:
  ttyd (co xac thuc co ban) chay dinh vao 1 phien tmux co dinh:
      Terminal local : tmux session "consolepi-local"  -> cong 8010
      SSH            : tmux session "consolepi-ssh"    -> cong 8011

Dung tmux vi 2 ly do:
  1. Phien khong mat khi dong trinh duyet / mat mang giua chung
  2. Cho phep "dan lenh tu thu vien" bang `tmux send-keys` tu phia server
     (yeu cau so 7: copy tap lenh, sua, xac nhan roi dan vao chay)

BAO MAT: 2 cong nay cho quyen root day du nen ttyd chay kem xac thuc co ban
(-c user:pass). Mat khau sinh ngau nhien luc cai dat, luu tai
/opt/console-pi/config.json (chmod 600) va chi hien cho nguoi da dang nhap
dashboard.
"""
import json
import os
import secrets
import subprocess

from flask import request


from .layout import render_page

CONFIG_FILE = "/opt/console-pi/config.json"

LOCAL_SESSION = "consolepi-local"
SSH_SESSION = "consolepi-ssh"
LOCAL_PORT = 8010
SSH_PORT = 8011


def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    old = os.umask(0o077)
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    finally:
        os.umask(old)


def get_term_credential():
    """Lay (user, pass) cho ttyd. Tu sinh lan dau neu chua co."""
    cfg = load_config()
    cred = cfg.get("terminal_auth")
    if not cred or ":" not in cred:
        cred = "console:" + secrets.token_urlsafe(12)
        cfg["terminal_auth"] = cred
        save_config(cfg)
    user, _, pw = cred.partition(":")
    return user, pw


def tmux_session_exists(name):
    try:
        r = subprocess.run(["tmux", "has-session", "-t", name],
                           capture_output=True, timeout=5)
        return r.returncode == 0
    except Exception:
        return False


def service_active(name):
    try:
        r = subprocess.run(["systemctl", "is-active", name],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() == "active"
    except Exception:
        return False


# Ten phim dac biet ma vkeyboard.js gui khi bam phim chuc nang (Enter, Xoa,
# Tab...) - PHAI khop dung chuoi ben JS. tmux hieu day la LENH DIEU KHIEN
# (nhan phim tuong ung), khong phai chu can go.
_PHIM_DAC_BIET = {"Enter", "BSpace", "Tab", "Escape", "Space",
                  "Up", "Down", "Left", "Right", "C-c"}


def send_keys(session_name, keys):
    """
    Gui 1 lan go phim (ky tu thuong hoac phim dac biet) vao phien tmux -
    dung boi ban phim ao (vkeyboard.js) khi trang la Console/Terminal/SSH
    (khung terminal khong phai o nhap <input> nen khong the go thang vao).

    LOI THAT DA GAP (anh Thoai bao "go hoai khong an vao terminal", chup man
    hinh ban phim qua lon che mat man hinh): ham nay duoc GOI o /api/send-keys
    (ui/terminal.py) nhung CHUA TUNG DUOC DINH NGHIA O DAU CA trong toan bo
    ma nguon - moi lan bam phim ao deu goi ham khong ton tai, Flask nem
    NameError (loi 500), va vkeyboard.js lai NUOT LOI ay bang .catch(()=>{})
    nen nguoi dung khong thay bao gi ca, chi thay go khong an. Day la loi co
    san tu truoc, khong phai do thay doi gan day.

    KHONG dung `-l` (literal) cho phim dac biet - can de tmux hieu la LENH
    (vd "Enter" = nhan phim Enter that). Co dung `-l` cho ky tu thuong -
    tranh tmux hieu nham mot so ky tu (vi du ';') thanh cu phap rieng cua
    no thay vi ky tu can go.
    """
    session_name = (session_name or "").strip()
    if not session_name:
        return False, "Thiếu tên phiên tmux."
    if keys is None or keys == "":
        return False, "Thiếu nội dung cần gửi."
    if not tmux_session_exists(session_name):
        return False, f"Chưa có phiên terminal '{session_name}'."

    cmd = ["tmux", "send-keys", "-t", session_name]
    if keys not in _PHIM_DAC_BIET:
        cmd.append("-l")
        # LOI THAT DA GAP: go dau ";" qua ban phim ao thi khong ra gi ca -
        # tmux dung ";" DUNG THAN NO (ke ca sau -l) de TACH NHIEU LENH tmux
        # trong 1 lan goi (vd `tmux new-window \; split-window`), nen mot
        # doi so dung la ";" bi hieu thanh dau tach lenh rong thay vi ky tu
        # can go. Phai thoat thanh "\;" de tmux hieu la ky tu that (da kiem
        # chung: khong thoat thi man hinh khong nhan duoc gi, co thoat thi
        # dung dau ";" hien ra).
        if keys == ";":
            keys = "\\;"
    cmd.append(keys)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            return False, (r.stderr or "Gửi phím thất bại.").strip()
        return True, "ok"
    except Exception as e:
        return False, str(e)


def _terminal_body(kind, base_path, session_name, service_name, warn_html):
    running = service_active(service_name)
    has_session = tmux_session_exists(session_name)

    # 1 dong duy nhat (thay vi 2 banner rieng canh bao + trang thai) - danh
    # cho man hinh nho/cua so trinh duyet thap thi khung terminal van con
    # nhieu khong gian de nhin, khong bi choan het boi phan chu thich.
    if running:
        status = (f'{warn_html} &middot; tmux <code>{session_name}</code> '
                  f'{"dang mo" if has_session else "se tu tao khi mo"}')
        banner = f'<div class="msg warn">{status}</div>'
    else:
        banner = (f'<div class="msg err">{warn_html} &middot; Dich vu '
                 f'<code>{service_name}</code> chua chay. '
                 f'Chay: <code>sudo systemctl start {service_name}</code></div>')

    from .soanlenh import khoi_soan_lenh, khoi_copy_terminal

    return f"""
    {banner}
    <div id="bao_server" class="msg ok" style="display:none;"></div>
    <div class="card" style="padding:0;overflow:hidden;margin-bottom:12px;">
      <iframe src="{base_path}/" title="{kind}"
              style="width:100%;height:calc(100vh - 330px);min-height:360px;border:0;display:block;background:#000;"></iframe>
    </div>
    <div class="row" style="margin-bottom:12px;">
      <a class="btn gray" href="{base_path}/">↗ Mo terminal toan man hinh</a>
    </div>
    {khoi_copy_terminal()}
    {khoi_soan_lenh("/terminal/paste", "consolepi-local-o-lenh")}"""


def register_terminal(app):
    @app.route("/terminal")
    def terminal_page():
        warn = ('<strong>Lưu ý:</strong> Terminal của chính Pi với <strong>quyen root</strong> '
               '- go lenh can than')
        body = _terminal_body("Terminal tại chỗ", "/term-local", LOCAL_SESSION,
                              "console-pi-term-local.service", warn)
        html = render_page(body, active="/terminal", title="Terminal",
                           subtitle="Dòng lệnh trực tiếp trên Pi (phiên tmux giữ nguyên khi đóng trình duyệt)")
        # Bao cho ban phim ao biet go phim vao phien tmux nao
        return html.replace("<body>", f'<body data-tmux-session="{LOCAL_SESSION}">', 1)

    @app.route("/terminal/paste", methods=["POST"])
    def terminal_paste():
        """
        Dan noi dung o soan vao khung Terminal.

        Goi tu fetch thi tra JSON de trang KHONG tai lai - khung terminal giu
        nguyen phien va khong dinh hop thoai "Leave site?" cua ttyd. Goi kieu
        form thuong (JS loi/bi tat) thi van ra trang binh thuong.
        """
        from .commands import dan_thong_minh
        noi_dung = request.form.get("noi_dung", "")
        if not noi_dung.strip():
            ok, msg = False, "Ô lệnh đang trống - chưa có gì để dán."
        else:
            ok, msg = dan_thong_minh(LOCAL_SESSION, noi_dung)

        if request.headers.get("X-Console-Pi") == "fetch":
            from flask import jsonify
            return jsonify({"ok": ok, "msg": msg})

        warn = ('<strong>Lưu ý:</strong> Terminal của chính Pi với <strong>quyen root</strong> '
                '- go lenh can than')
        body = _terminal_body("Terminal tại chỗ", "/term-local", LOCAL_SESSION,
                              "console-pi-term-local.service", warn)
        html = render_page(f'<div class="msg {"ok" if ok else "err"}">{msg}</div>' + body,
                           active="/terminal", title="Terminal", subtitle="")
        return html.replace("<body>", f'<body data-tmux-session="{LOCAL_SESSION}">', 1)

    @app.route("/api/send-keys", methods=["POST"])
    def api_send_keys():
        from flask import request as _rq, jsonify
        data = _rq.get_json(silent=True) or {}
        ok, msg = send_keys(data.get("session", ""), data.get("keys", ""))
        return jsonify({"ok": ok, "error": msg}), (200 if ok else 400)

    return app
