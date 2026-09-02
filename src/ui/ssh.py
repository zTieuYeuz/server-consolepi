"""
Console Pi - Tab SSH (yeu cau so 7)

Anh chon "Ca hai" nen co 2 che do:

  1. SSH TUONG TAC  - terminal that (ttyd + tmux), go duoc moi thu nhu PuTTY.
     Bam "Ket noi" se chay lenh ssh trong phien tmux.

  2. CHAY HANG LOAT - chon tap lenh tu Thu vien, SUA lai (doi IP/ten...),
     XEM TRUOC roi moi xac nhan chay. Dung Netmiko nen ho tro nhieu hang
     thiet bi va thay duoc ket qua tung lenh.

Diem chung: luon cho SUA va XEM TRUOC truoc khi thuc thi - vi day la thao
tac ghi len thiet bi that.
"""
import subprocess

from flask import request

from .layout import render_page
from .commands import load_library
from .terminal import (SSH_SESSION, SSH_PORT, get_term_credential,
                       tmux_session_exists, service_active)

AUDIT_LOG = "/var/log/console-pi-netmiko.log"

DEVICE_TYPES = [
    "cisco_ios", "cisco_xe", "cisco_nxos", "arista_eos",
    "hp_comware", "hp_procurve", "juniper_junos",
    "mikrotik_routeros", "ubiquiti_edge", "linux",
]



# ---------------------------------------------------------------------------
# To mau output thiet bi mang hien tren web
#
# Khac voi terminal (output tu thiet bi gui ve, khong the sua real-time),
# o day la HTML do minh sinh ra nen to mau duoc triet de.
# Mau chon theo thoi quen doc cua dan mang:
#   do = van de, xanh la = tot, vang = canh bao,
#   xanh nhat = dia chi IP, tim = ten cong
# ---------------------------------------------------------------------------
import html as _html
import re as _re

_RULES = [
    # Trang thai xau
    (_re.compile(r"\b(?:down|err-disabled|errdisable|shutdown|failed|denied|deny|"
                 r"invalid|error|CRC|collision|drops?|unreachable|timeout|inactive|"
                 r"blocking|discarding)\b", _re.I), "c-bad"),
    # Trang thai tot
    (_re.compile(r"\b(?:up|connected|established|active|forwarding|permit|success|"
                 r"enabled|reachable|full-duplex)\b", _re.I), "c-good"),
    # Canh bao
    (_re.compile(r"\b(?:warning|notice|half-duplex|learning|listening|standby|"
                 r"administratively|notconnect|disabled)\b", _re.I), "c-warn"),
    # Ten cong Cisco (day du va viet tat)
    (_re.compile(r"\b(?:GigabitEthernet|TenGigabitEthernet|FastEthernet|Ethernet|"
                 r"Serial|Loopback|Port-channel|Vlan|Tunnel|Management)[\d/\.]*\b"), "c-if"),
    (_re.compile(r"\b(?:Gi|Fa|Te|Et|Se|Lo|Po|Vl|Tu|Mg)\d+(?:/\d+)*(?:\.\d+)?\b"), "c-if"),
    # MAC kieu Cisco va kieu thong thuong
    (_re.compile(r"\b(?:[0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4}\b"), "c-mac"),
    (_re.compile(r"\b(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\b"), "c-mac"),
    # Dia chi IPv4
    (_re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?\b"), "c-ip"),
]

COLOR_CSS = """
.termout { background:#0f1114; border:1px solid #2c3036; padding:13px;
           border-radius:6px; overflow-x:auto; white-space:pre-wrap;
           word-break:break-word; font-size:13px; line-height:1.55;
           font-family:ui-monospace, Menlo, Consolas, monospace; color:#d5dae2; }
.termout .c-bad  { color:#ff6b6b; font-weight:600; }
.termout .c-good { color:#7ddc7d; font-weight:600; }
.termout .c-warn { color:#ffd166; }
.termout .c-ip   { color:#68d5d5; }
.termout .c-mac  { color:#6cb6ff; }
.termout .c-if   { color:#d99bff; }
"""


def colorize_output(text):
    """Chuyen output thiet bi thanh HTML co mau. Luon escape truoc de an toan."""
    if not text:
        return ""
    out = _html.escape(text)

    # Danh dau bang the tam roi doi sang <span> o buoc cuoi, tranh viec
    # quy tac sau to mau trung vao the HTML cua quy tac truoc.
    marks = []

    def _sub(m, cls):
        marks.append((cls, m.group(0)))
        return f"\x00{len(marks) - 1}\x00"

    for rx, cls in _RULES:
        out = rx.sub(lambda m, c=cls: _sub(m, c), out)

    def _restore(m):
        cls, val = marks[int(m.group(1))]
        return f'<span class="{cls}">{val}</span>'

    return _re.sub(r"\x00(\d+)\x00", _restore, out)


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def start_ssh_in_tmux(host, user, port=22):
    """Chay lenh ssh trong phien tmux de terminal web hien ra."""
    if not host or not user:
        return False, "Thieu dia chi hoac tai khoan."
    try:
        if not tmux_session_exists(SSH_SESSION):
            return False, (f"Chua co phien terminal SSH. Mo tab SSH (khung terminal ben duoi) "
                           f"de tao phien truoc roi bam lai.")
        cmd = f"ssh -o StrictHostKeyChecking=accept-new -p {int(port)} {user}@{host}"
        subprocess.run(["tmux", "send-keys", "-t", SSH_SESSION, cmd, "Enter"],
                       capture_output=True, timeout=5)
        return True, f"Da gui lenh ket noi toi {host}. Nhap mat khau trong khung terminal ben duoi."
    except Exception as e:
        return False, f"Loi: {e}"


def run_batch(host, device_type, username, password, commands, save=False, port=22, timeout=15):
    """Chay hang loat lenh qua Netmiko (co the la lenh doc hoac lenh cau hinh)."""
    try:
        from netmiko import ConnectHandler
        from netmiko.exceptions import (NetmikoTimeoutException,
                                        NetmikoAuthenticationException)
    except ImportError as e:
        return {"ok": False, "error": f"Thieu netmiko: {e}", "output": ""}

    device = {"device_type": device_type, "host": host, "username": username,
              "password": password, "port": int(port), "timeout": timeout}

    import time as _t
    def _audit(result):
        try:
            with open(AUDIT_LOG, "a") as f:
                f.write(f"{_t.strftime('%Y-%m-%d %H:%M:%S')} | host={host} | "
                        f"type={device_type} | action=ssh-batch | "
                        f"commands={commands!r} | result={result}\n")
        except Exception:
            pass

    try:
        conn = ConnectHandler(**device)
        output = conn.send_config_set(commands)
        if save:
            output += "\n--- LUU CAU HINH ---\n" + str(conn.save_config())
        conn.disconnect()
    except NetmikoAuthenticationException:
        _audit("AUTH FAILED")
        return {"ok": False, "error": "Sai tai khoan hoac mat khau.", "output": ""}
    except NetmikoTimeoutException:
        _audit("TIMEOUT")
        return {"ok": False, "error": f"Khong ket noi duoc toi {host} (timeout).", "output": ""}
    except Exception as e:
        _audit(f"ERROR: {e}")
        return {"ok": False, "error": str(e), "output": ""}

    _audit("OK" + (" + SAVED" if save else ""))
    return {"ok": True, "error": None, "output": output, "saved": save}


def _render(msg="", ok=True, prefill="", form=None, result=None, preview=None):
    form = form or {}
    lib = load_library()
    user, pw = get_term_credential()
    host_addr = request.host.split(":")[0]
    term_running = service_active("console-pi-term-ssh.service")

    lib_options = "".join(
        f'<option value="{i}">{_esc(it.get("name"))}</option>' for i, it in enumerate(lib)
    )
    lib_data = "".join(
        f'<script type="application/json" id="lib{i}">{_esc(it.get("commands",""))}</script>'
        for i, it in enumerate(lib)
    )

    msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""

    # --- Ket qua chay hang loat ---
    result_html = ""
    if result:
        if result.get("error"):
            result_html = f'<div class="msg err">Loi: {_esc(result["error"])}</div>'
        else:
            result_html = (f'<div class="msg ok">Chay xong'
                           f'{" va da luu cau hinh" if result.get("saved") else ""}.</div>'
                           f'<h2>Ket qua</h2>'
                           f'<div class="termout">{colorize_output(result.get("output"))}</div>')

    # --- Man hinh xem truoc truoc khi chay ---
    if preview:
        cmds = preview.get("commands", "")
        n = len([l for l in cmds.splitlines() if l.strip()])
        body = f"""
        <div class="msg warn">
          <strong>⚠ Xem truoc - CHUA KET NOI GI CA.</strong>
          Doc ky {n} lenh duoi day truoc khi xac nhan. Day la thao tac ghi len thiet bi that.
        </div>
        <div class="card">
          <h3>Se ket noi toi</h3>
          <table style="max-width:460px;">
            <tr><th style="width:130px;">Dia chi</th><td><code>{_esc(preview.get('host'))}:{_esc(preview.get('port'))}</code></td></tr>
            <tr><th>Loai thiet bi</th><td><code>{_esc(preview.get('device_type'))}</code></td></tr>
            <tr><th>Tai khoan</th><td><code>{_esc(preview.get('username'))}</code></td></tr>
          </table>
        </div>
        <div class="card">
          <h3>Cac lenh se chay</h3>
          <pre>{_esc(cmds)}</pre>
        </div>
        <form method="POST" action="/ssh/run"
              onsubmit="return confirm('XAC NHAN chay {n} lenh tren {_esc(preview.get('host'))}?');">
          <input type="hidden" name="host" value="{_esc(preview.get('host'))}">
          <input type="hidden" name="port" value="{_esc(preview.get('port'))}">
          <input type="hidden" name="device_type" value="{_esc(preview.get('device_type'))}">
          <input type="hidden" name="username" value="{_esc(preview.get('username'))}">
          <input type="hidden" name="password" value="{_esc(preview.get('password'))}">
          <input type="hidden" name="commands" value="{_esc(cmds)}">
          <label style="display:flex;align-items:center;gap:9px;">
            <input type="checkbox" name="save" value="1" style="width:20px;height:20px;">
            <span>Luu cau hinh vinh vien (write memory) - KHO HOAN TAC, mac dinh khong tick</span>
          </label>
          <div class="row" style="margin-top:14px;">
            <button type="submit" class="red" data-busy="Dang chay tren thiet bi...">✅ Xac nhan va chay</button>
            <a class="btn gray" href="/ssh">Huy</a>
          </div>
        </form>"""
        return render_page(body, active="/ssh", title="SSH - Xem truoc",
                           subtitle="Buoc cuoi truoc khi ghi len thiet bi that")

    term_status = ("" if term_running else
                   '<div class="msg err">Dich vu terminal SSH chua chay: '
                   '<code>sudo systemctl start console-pi-term-ssh</code></div>')

    body = f"""
    {msg_html}
    {result_html}

    <h2>1. SSH tuong tac (go truc tiep nhu PuTTY)</h2>
    {term_status}
    <div class="card">
      <form method="POST" action="/ssh/connect" class="row">
        <div><label>Dia chi thiet bi</label>
          <input type="text" name="host" placeholder="192.168.1.1" style="max-width:210px;" required></div>
        <div><label>Tai khoan</label>
          <input type="text" name="user" placeholder="admin" style="max-width:160px;" required></div>
        <div><label>Cong</label>
          <input type="number" name="port" value="22" style="max-width:95px;"></div>
        <div><button type="submit" data-busy="Dang gui lenh...">🔑 Ket noi</button></div>
      </form>
      <p style="color:#8b93a1;font-size:13px;margin:10px 0 0;">
        Lenh ssh se duoc go vao khung terminal ben duoi. Nhap mat khau thiet bi truc tiep trong do.
      </p>
    </div>
    <div class="card" style="padding:0;overflow:hidden;">
      <iframe src="/term-ssh/" title="SSH terminal"
              style="width:100%;height:460px;border:0;display:block;background:#000;"></iframe>
    </div>

    <h2>2. Chay hang loat (chon tu thu vien, sua roi xac nhan)</h2>
    <div class="card">
      <form method="POST" action="/ssh/preview">
        <div class="row">
          <div><label>Dia chi thiet bi</label>
            <input type="text" name="host" required placeholder="192.168.1.1" style="max-width:210px;"
                   value="{_esc(form.get('host'))}"></div>
          <div><label>Cong SSH</label>
            <input type="number" name="port" value="{_esc(form.get('port') or 22)}" style="max-width:95px;"></div>
          <div><label>Loai thiet bi</label>
            <select name="device_type" style="max-width:200px;">
              {"".join(f'<option {"selected" if form.get("device_type")==d else ""}>{d}</option>' for d in DEVICE_TYPES)}
            </select></div>
        </div>
        <div class="row">
          <div><label>Tai khoan</label>
            <input type="text" name="username" required style="max-width:200px;"
                   value="{_esc(form.get('username'))}"></div>
          <div><label>Mat khau</label>
            <input type="password" name="password" required style="max-width:200px;"></div>
        </div>

        <label>Lay tap lenh co san tu thu vien</label>
        <div class="row">
          <select id="libSel" style="max-width:340px;">
            <option value="">-- Chon tap lenh --</option>
            {lib_options}
          </select>
          <button type="button" class="gray" onclick="loadLib()">📋 Chep vao o ben duoi</button>
        </div>

        <label>Cac lenh se chay (SUA lai IP/ten cho dung truoc khi tiep tuc)</label>
        <textarea name="commands" required style="max-width:100%;min-height:170px;">{_esc(prefill)}</textarea>

        <div class="row" style="margin-top:13px;">
          <button type="submit" data-busy="Dang chuan bi...">👁 Xem truoc roi chay</button>
        </div>
      </form>
    </div>
    {lib_data}
    <script>
      function loadLib() {{
        var sel = document.getElementById('libSel');
        if (!sel.value) return;
        var el = document.getElementById('lib' + sel.value);
        if (!el) return;
        var ta = document.querySelector('textarea[name=commands]');
        ta.value = el.textContent;
        ta.focus();
      }}
    </script>"""

    html = render_page(body, active="/ssh", title="SSH",
                       subtitle="Ket noi tuong tac hoac chay hang loat lenh len thiet bi mang")
    return html.replace("<body>", f'<body data-tmux-session="{SSH_SESSION}">', 1)


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
        return _render(prefill=prefill)

    @app.route("/ssh/connect", methods=["POST"])
    def ssh_connect():
        f = request.form
        ok, msg = start_ssh_in_tmux(f.get("host", "").strip(),
                                    f.get("user", "").strip(),
                                    f.get("port", 22) or 22)
        return _render(msg=msg, ok=ok)

    @app.route("/ssh/preview", methods=["POST"])
    def ssh_preview():
        f = request.form
        return _render(preview={
            "host": f.get("host", "").strip(), "port": f.get("port", 22) or 22,
            "device_type": f.get("device_type", "cisco_ios"),
            "username": f.get("username", "").strip(),
            "password": f.get("password", ""),
            "commands": f.get("commands", ""),
        })

    @app.route("/ssh/run", methods=["POST"])
    def ssh_run():
        f = request.form
        cmds = [c for c in (f.get("commands") or "").splitlines() if c.strip()]
        res = run_batch(f.get("host", "").strip(), f.get("device_type", "cisco_ios"),
                        f.get("username", "").strip(), f.get("password", ""),
                        cmds, save=(f.get("save") == "1"), port=f.get("port", 22) or 22)
        return _render(result=res, form={
            "host": f.get("host"), "port": f.get("port"),
            "device_type": f.get("device_type"), "username": f.get("username"),
        }, prefill=f.get("commands", ""))

    return app
