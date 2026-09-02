"""
Console Pi - Thu vien lenh (yeu cau so 6)

Luu cac tap lenh hay dung, them/sua/xoa duoc qua web. Tu day co the:
  - Gui thang vao Terminal dang mo (qua tmux send-keys)
  - Copy sang tab SSH de sua (doi IP/ten) roi chay hang loat

File luu: /opt/console-pi/command-library.json  (giu nguyen khi cai dat lai)
"""
import json
import os
import subprocess

from flask import request, redirect

from .layout import render_page

LIB_FILE = "/opt/console-pi/command-library.json"

# 5 tap lenh co ban hay dung nhat khi lam viec voi switch Cisco
DEFAULT_LIBRARY = [
    {
        "name": "Xem thong tin co ban switch",
        "desc": "Kiem tra model, IOS version, uptime, so serial",
        "tags": "cisco, xem",
        "commands": "show version\nshow inventory\nshow env all",
    },
    {
        "name": "Xem trang thai tat ca cong",
        "desc": "Cong nao up/down, toc do, duplex, VLAN dang gan",
        "tags": "cisco, xem, port",
        "commands": "show ip interface brief\nshow interfaces status\nshow interfaces description",
    },
    {
        "name": "Xem VLAN va bang MAC",
        "desc": "Danh sach VLAN, cong nao thuoc VLAN nao, MAC dang hoc duoc",
        "tags": "cisco, xem, vlan",
        "commands": "show vlan brief\nshow mac address-table\nshow interfaces trunk",
    },
    {
        "name": "Gan VLAN cho 1 cong (access)",
        "desc": "SUA lai ten cong va so VLAN truoc khi chay",
        "tags": "cisco, cau hinh, vlan",
        "commands": ("interface GigabitEthernet0/1\n"
                     " description Cau hinh boi Console Pi\n"
                     " switchport mode access\n"
                     " switchport access vlan 10\n"
                     " no shutdown"),
    },
    {
        "name": "Cau hinh IP quan ly + SSH",
        "desc": "SUA lai IP/subnet/gateway/domain truoc khi chay",
        "tags": "cisco, cau hinh, quan ly",
        "commands": ("interface Vlan1\n"
                     " ip address 192.168.1.10 255.255.255.0\n"
                     " no shutdown\n"
                     "exit\n"
                     "ip default-gateway 192.168.1.1\n"
                     "ip domain-name local.lan\n"
                     "crypto key generate rsa modulus 2048\n"
                     "ip ssh version 2\n"
                     "line vty 0 4\n"
                     " transport input ssh\n"
                     " login local"),
    },
]


def load_library():
    """Doc thu vien. Lan dau chua co file thi tao san 5 tap lenh mau."""
    try:
        with open(LIB_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except FileNotFoundError:
        save_library(DEFAULT_LIBRARY)
        return list(DEFAULT_LIBRARY)
    except Exception:
        pass
    return []


def save_library(items):
    try:
        with open(LIB_FILE, "w") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def add_item(name, desc, tags, commands):
    items = load_library()
    items.append({"name": name, "desc": desc, "tags": tags, "commands": commands})
    return save_library(items)


def update_item(index, name, desc, tags, commands):
    items = load_library()
    if 0 <= index < len(items):
        items[index] = {"name": name, "desc": desc, "tags": tags, "commands": commands}
        return save_library(items)
    return False


def delete_item(index):
    items = load_library()
    if 0 <= index < len(items):
        items.pop(index)
        return save_library(items)
    return False


def send_to_tmux(session_name, text, press_enter=False):
    """
    Dan tap lenh vao phien tmux dang chay (terminal tren web).

    Dung "bracketed paste" cua tmux (paste-buffer -p) thay vi send-keys:
      - send-keys se lam cac dong DINH LIEN nhau thanh 1 dong vo nghia
      - bracketed paste giu nguyen xuong dong, va shell (bash >= 4.4) hieu
        day la van ban dan vao nen KHONG tu chay - nguoi dung xem lai roi
        moi tu bam Enter. Dung y do "sua xong xac nhan moi chay".
    """
    import tempfile

    try:
        has = subprocess.run(["tmux", "has-session", "-t", session_name],
                             capture_output=True, timeout=5)
        if has.returncode != 0:
            return False, (f"Chua co phien terminal '{session_name}'. "
                           f"Mo tab Terminal truoc roi bam lai.")

        buf_name = "consolepi-lib"
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write(text.rstrip("\n"))
            tmp = f.name
        try:
            subprocess.run(["tmux", "load-buffer", "-b", buf_name, tmp],
                           capture_output=True, timeout=5)
            subprocess.run(["tmux", "paste-buffer", "-p", "-b", buf_name,
                            "-t", session_name],
                           capture_output=True, timeout=5)
            if press_enter:
                subprocess.run(["tmux", "send-keys", "-t", session_name, "Enter"],
                               capture_output=True, timeout=5)
        finally:
            os.unlink(tmp)

        n = len([l for l in text.splitlines() if l.strip()])
        if press_enter:
            return True, f"Da dan va chay {n} lenh trong terminal."
        return True, (f"Da dan {n} lenh vao terminal (chua chay). "
                      f"Mo tab Terminal xem lai, sua neu can, roi bam Enter de chay.")
    except FileNotFoundError:
        return False, "Chua cai tmux tren may."
    except Exception as e:
        return False, f"Loi: {e}"


def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_library_page(msg="", ok=True, edit_index=None):
    items = load_library()

    rows = ""
    for i, it in enumerate(items):
        cmds = _esc(it.get("commands", ""))
        n_lines = len([l for l in it.get("commands", "").splitlines() if l.strip()])
        rows += f"""
        <div class="card">
          <div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:flex-start;">
            <div style="flex:1;min-width:220px;">
              <h3 style="margin-bottom:3px;">{_esc(it.get('name'))}</h3>
              <div style="color:#8b93a1;font-size:13px;">{_esc(it.get('desc'))}</div>
              <div style="color:#6b7280;font-size:12px;margin-top:4px;">
                {n_lines} lenh &middot; {_esc(it.get('tags'))}
              </div>
            </div>
          </div>
          <pre style="margin-top:10px;">{cmds}</pre>
          <div class="row" style="margin-top:10px;">
            <form method="POST" action="/commands/send" style="display:inline;">
              <input type="hidden" name="index" value="{i}">
              <button type="submit" class="blue small">⌨️ Gui vao Terminal</button>
            </form>
            <a class="btn small" href="/ssh?lib={i}">🔑 Dung o tab SSH</a>
            <a class="btn gray small" href="/commands?edit={i}">✏️ Sua</a>
            <form method="POST" action="/commands/delete" style="display:inline;"
                  onsubmit="return confirm('Xoa tap lenh &quot;{_esc(it.get('name'))}&quot;?');">
              <input type="hidden" name="index" value="{i}">
              <button type="submit" class="red small">🗑 Xoa</button>
            </form>
          </div>
        </div>"""

    if not items:
        rows = '<div class="msg info">Thu vien dang trong. Them tap lenh dau tien ben duoi.</div>'

    # Form them moi hoac sua
    editing = edit_index is not None and 0 <= edit_index < len(items)
    cur = items[edit_index] if editing else {"name": "", "desc": "", "tags": "", "commands": ""}
    form_title = f"✏️ Sua: {_esc(cur.get('name'))}" if editing else "➕ Them tap lenh moi"
    action = "/commands/update" if editing else "/commands/add"

    form_html = f"""
    <h2>{form_title}</h2>
    <div class="card">
      <form method="POST" action="{action}">
        {f'<input type="hidden" name="index" value="{edit_index}">' if editing else ''}
        <label>Ten tap lenh</label>
        <input type="text" name="name" required value="{_esc(cur.get('name'))}"
               placeholder="Vi du: Gan VLAN cho 1 cong">
        <label>Mo ta ngan</label>
        <input type="text" name="desc" value="{_esc(cur.get('desc'))}"
               placeholder="Nho ghi ro cho nao can sua truoc khi chay">
        <label>The (phan cach bang dau phay)</label>
        <input type="text" name="tags" value="{_esc(cur.get('tags'))}"
               placeholder="cisco, vlan, cau hinh">
        <label>Cac lenh (moi dong 1 lenh)</label>
        <textarea name="commands" required style="max-width:100%;">{_esc(cur.get('commands'))}</textarea>
        <div class="row" style="margin-top:12px;">
          <button type="submit">{'Luu thay doi' if editing else 'Them vao thu vien'}</button>
          {'<a class="btn gray" href="/commands">Huy</a>' if editing else ''}
        </div>
      </form>
    </div>"""

    msg_html = f'<div class="msg {"ok" if ok else "err"}">{_esc(msg)}</div>' if msg else ""

    body = f"""
    {msg_html}
    <div class="msg info">
      <strong>Cach dung:</strong> <em>Gui vao Terminal</em> se dan lenh vao terminal dang mo
      nhung <strong>khong tu bam Enter</strong> - anh xem lai roi tu chay.
      <em>Dung o tab SSH</em> se chep sang tab SSH de sua IP/ten truoc khi chay hang loat.
    </div>
    {form_html}
    <h2>Danh sach ({len(items)} tap lenh)</h2>
    {rows}"""

    return render_page(body, active="/commands", title="Thu vien lenh",
                       subtitle="Luu san cac tap lenh hay dung, sua duoc truoc khi chay")


def register_commands(app, tmux_session="consolepi-local"):
    @app.route("/commands")
    def commands_page():
        edit = request.args.get("edit")
        edit_index = int(edit) if (edit or "").isdigit() else None
        return render_library_page(edit_index=edit_index)

    @app.route("/commands/add", methods=["POST"])
    def commands_add():
        f = request.form
        if not (f.get("name") or "").strip() or not (f.get("commands") or "").strip():
            return render_library_page(msg="Thieu ten hoac noi dung lenh.", ok=False)
        add_item(f.get("name").strip(), f.get("desc", "").strip(),
                 f.get("tags", "").strip(), f.get("commands"))
        return render_library_page(msg=f"Da them '{f.get('name')}'.", ok=True)

    @app.route("/commands/update", methods=["POST"])
    def commands_update():
        f = request.form
        idx = int(f.get("index", -1) or -1)
        if update_item(idx, f.get("name", "").strip(), f.get("desc", "").strip(),
                       f.get("tags", "").strip(), f.get("commands", "")):
            return render_library_page(msg="Da luu thay doi.", ok=True)
        return render_library_page(msg="Khong tim thay tap lenh de sua.", ok=False)

    @app.route("/commands/delete", methods=["POST"])
    def commands_delete():
        idx = int(request.form.get("index", -1) or -1)
        if delete_item(idx):
            return render_library_page(msg="Da xoa tap lenh.", ok=True)
        return render_library_page(msg="Khong tim thay tap lenh.", ok=False)

    @app.route("/commands/send", methods=["POST"])
    def commands_send():
        idx = int(request.form.get("index", -1) or -1)
        items = load_library()
        if not (0 <= idx < len(items)):
            return render_library_page(msg="Khong tim thay tap lenh.", ok=False)
        ok, msg = send_to_tmux(tmux_session, items[idx].get("commands", ""))
        return render_library_page(msg=msg, ok=ok)

    return app
