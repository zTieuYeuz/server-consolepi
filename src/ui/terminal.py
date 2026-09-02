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


def _terminal_body(kind, base_path, session_name, service_name, intro_html):
    running = service_active(service_name)
    has_session = tmux_session_exists(session_name)

    status = (f'<div class="msg ok">Terminal dang chay &middot; phien tmux '
              f'<code>{session_name}</code> {"dang mo" if has_session else "se tu tao khi mo"}</div>'
              if running else
              f'<div class="msg err">Dich vu <code>{service_name}</code> chua chay. '
              f'Chay: <code>sudo systemctl start {service_name}</code></div>')

    return f"""
    {intro_html}
    {status}
    <div class="card" style="padding:0;overflow:hidden;">
      <iframe src="{base_path}/" title="{kind}"
              style="width:100%;height:560px;border:0;display:block;background:#000;"></iframe>
    </div>
    <div class="row">
      <a class="btn" href="{base_path}/">↗ Mo terminal toan man hinh</a>
      <a class="btn gray" href="/commands">📚 Lay lenh tu thu vien</a>
    </div>"""


def register_terminal(app):
    @app.route("/terminal")
    def terminal_page():
        intro = """
        <div class="msg warn">
          <strong>Luu y:</strong> Day la terminal cua chinh Pi voi <strong>quyen root</strong>.
          Dung de sua chua khi can (xem log, sua file cau hinh, khoi dong lai dich vu).
          Go lenh can than.
        </div>"""
        body = _terminal_body("Terminal local", "/term-local", LOCAL_SESSION,
                              "console-pi-term-local.service", intro)
        html = render_page(body, active="/terminal", title="Terminal",
                           subtitle="Dong lenh truc tiep tren Pi (phien tmux giu nguyen khi dong trinh duyet)")
        # Bao cho ban phim ao biet go phim vao phien tmux nao
        return html.replace("<body>", f'<body data-tmux-session="{LOCAL_SESSION}">', 1)

    @app.route("/api/send-keys", methods=["POST"])
    def api_send_keys():
        from flask import request as _rq, jsonify
        data = _rq.get_json(silent=True) or {}
        ok, msg = send_keys(data.get("session", ""), data.get("keys", ""))
        return jsonify({"ok": ok, "error": msg}), (200 if ok else 400)

    return app
