"""
Console Pi Network Tools - IF/THEN Automation (netool.io Phan 7)

Rule dang JSON: neu hostname/mgmt-ip phat hien qua LLDP khop 1 pattern,
GOI Y (khong tu dong chay) mot bo lenh Netmiko tuong ung. Nguoi dung van
phai bam xac nhan qua man hinh preview/run cua netmiko_tool.py - AN TOAN
HON de xuat trong tai lieu goc (tai lieu goc de xuat tu dong chay hoan
toan, o day co tinh giam bot vi day van la thao tac ghi thiet bi that).

Export/import rule duoc ma hoa bang Fernet (AES-128-CBC + HMAC, tuong
duong yeu cau AES-128 cua tai lieu goc) voi passphrase nguoi dung tu chon.
"""
import base64
import json
import re

from flask import request, render_template_string

from . import nettools_bp
from .lldp import get_lldp_neighbors

RULES_FILE = "/opt/console-pi/nettools/ifthen-rules.json"


def load_rules():
    try:
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_rules(rules):
    with open(RULES_FILE, "w") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)


def add_rule(name, field, pattern, device_type, commands):
    rules = load_rules()
    rules.append({
        "name": name, "field": field, "pattern": pattern,
        "device_type": device_type, "commands": commands,
    })
    save_rules(rules)


def delete_rule(index):
    rules = load_rules()
    if 0 <= index < len(rules):
        rules.pop(index)
        save_rules(rules)
        return True
    return False


def evaluate_rules():
    """
    Chay LLDP discovery, doi chieu voi rule da luu. Tra ve danh sach goi y
    (KHONG tu chay gi): [{"rule": {...}, "neighbor": {...}}]
    """
    lldp_result = get_lldp_neighbors()
    rules = load_rules()
    suggestions = []

    if not lldp_result.get("ok"):
        return {"ok": False, "error": lldp_result.get("error"), "suggestions": []}

    for neighbor in lldp_result.get("neighbors", []):
        for rule in rules:
            field_val = str(neighbor.get(rule["field"], ""))
            try:
                if re.search(rule["pattern"], field_val, re.IGNORECASE):
                    suggestions.append({"rule": rule, "neighbor": neighbor})
            except re.error:
                continue

    return {"ok": True, "error": None, "suggestions": suggestions}


def _derive_key(passphrase):
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    # Salt co dinh, chap nhan duoc vi day la ma hoa file backup ca nhan
    # (khong phai luu tru mat khau nguoi dung), muc tieu la tranh file
    # export bi doc duoc neu ai do vo tinh thay duoc, khong phai chong
    # tan cong brute-force chuyen nghiep.
    salt = b"console-pi-ifthen-salt-v1"
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=390000)
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def export_rules_encrypted(passphrase):
    from cryptography.fernet import Fernet
    key = _derive_key(passphrase)
    data = json.dumps(load_rules(), ensure_ascii=False).encode()
    return Fernet(key).encrypt(data)


def import_rules_encrypted(passphrase, blob):
    from cryptography.fernet import Fernet, InvalidToken
    key = _derive_key(passphrase)
    try:
        data = Fernet(key).decrypt(blob)
    except InvalidToken:
        return False, "Sai passphrase hoac file khong hop le."
    try:
        rules = json.loads(data)
    except json.JSONDecodeError:
        return False, "Noi dung sau giai ma khong phai JSON hop le."
    save_rules(rules)
    return True, f"Da nhap {len(rules)} rule."


IFTHEN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>IF/THEN Automation - Console Pi</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; background: #1e1e1e; color: #eee; padding: 20px; }
        h1 { color: #4CAF50; }
        h3 { color: #4CAF50; margin-top: 24px; }
        a { color: #4CAF50; }
        label { display: block; margin-top: 10px; }
        input[type=text], select, textarea, input[type=file], input[type=password] {
            padding: 8px; width: 100%; max-width: 420px; background: #333; color: #eee;
            border: 1px solid #555; box-sizing: border-box; font-family: monospace;
        }
        textarea { height: 80px; }
        table { width: 100%; border-collapse: collapse; margin-top: 12px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #444; }
        th { background: #2d2d2d; }
        button { padding: 9px 16px; background: #4CAF50; color: white; border: none;
            border-radius: 4px; cursor: pointer; margin-top: 10px; }
        button.del { background: #f44336; }
        .msg { padding: 12px 16px; border-radius: 4px; margin-top: 14px; }
        .ok { background: #2d4a2d; border-left: 4px solid #4CAF50; }
        .err { background: #4a2d2d; border-left: 4px solid #f44336; }
        .suggest { background: #2d3d4a; border-left: 4px solid #2196F3; padding: 12px 16px;
            border-radius: 4px; margin-top: 12px; }
        .hint { color: #999; font-size: 13px; }
    </style>
</head>
<body>
    <h1>🧩 IF/THEN Automation</h1>
    <p><a href="/nettools">← Network Tools</a></p>
    <p class="hint">Rule chi TAO GOI Y sau khi quet LLDP - khong tu dong chay lenh len thiet bi.
    Ban van phai xac nhan qua man hinh xem-truoc cua Netmiko.</p>

    {% if msg %}<div class="msg {{ 'ok' if ok else 'err' }}">{{ msg }}</div>{% endif %}

    <h3>▶ Quet va doi chieu rule</h3>
    <form method="POST" action="/nettools/ifthen/evaluate">
        <button type="submit">Quet LLDP va kiem tra rule khop</button>
    </form>

    {% if suggestions is not none %}
        {% if suggestions %}
        {% for s in suggestions %}
        <div class="suggest">
            <p>Rule "<strong>{{ s.rule.name }}</strong>" KHOP voi thiet bi
            <strong>{{ s.neighbor.remote_name }}</strong> ({{ s.neighbor.iface }}):</p>
            <pre>{{ s.rule.commands | join('\\n') }}</pre>
            <form method="GET" action="/nettools/netmiko" style="display:inline;">
                <button type="submit">Mo Netmiko de xac nhan chay lenh nay</button>
            </form>
        </div>
        {% endfor %}
        {% else %}<p>Khong co rule nao khop voi thiet bi da phat hien.</p>{% endif %}
    {% endif %}

    <h3>📋 Danh sach rule da luu</h3>
    <table>
        <tr><th>Ten</th><th>Dieu kien</th><th>Device type</th><th></th></tr>
        {% for i, r in rules %}
        <tr>
            <td>{{ r.name }}</td>
            <td><code>{{ r.field }}</code> ~ <code>{{ r.pattern }}</code></td>
            <td>{{ r.device_type }}</td>
            <td>
                <form method="POST" action="/nettools/ifthen/delete"
                      onsubmit="return confirm('Xoa rule {{ r.name }}?');">
                    <input type="hidden" name="index" value="{{ i }}">
                    <button type="submit" class="del">Xoa</button>
                </form>
            </td>
        </tr>
        {% endfor %}
    </table>
    {% if not rules %}<p>Chua co rule nao.</p>{% endif %}

    <h3>➕ Them rule moi</h3>
    <form method="POST" action="/nettools/ifthen/add">
        <label>Ten rule:</label>
        <input type="text" name="name" required placeholder="vd Switch tang 3">
        <label>Truong LLDP can khop:</label>
        <select name="field">
            <option value="remote_name">remote_name (hostname switch)</option>
            <option value="mgmt_ip">mgmt_ip</option>
            <option value="port_descr">port_descr</option>
        </select>
        <label>Pattern (regex):</label>
        <input type="text" name="pattern" required placeholder="vd SW-TANG3.*">
        <label>Device type (Netmiko):</label>
        <select name="device_type">
            <option value="cisco_ios">cisco_ios</option>
            <option value="cisco_xe">cisco_xe</option>
            <option value="arista_eos">arista_eos</option>
            <option value="hp_comware">hp_comware</option>
            <option value="juniper_junos">juniper_junos</option>
            <option value="mikrotik_routeros">mikrotik_routeros</option>
        </select>
        <label>Danh sach lenh (moi dong 1 lenh):</label>
        <textarea name="commands" placeholder="interface GigabitEthernet0/1&#10;switchport access vlan 10"></textarea>
        <button type="submit">Luu rule</button>
    </form>

    <h3>🔒 Export / Import (ma hoa)</h3>
    <form method="POST" action="/nettools/ifthen/export">
        <label>Passphrase de ma hoa:</label>
        <input type="password" name="passphrase" required>
        <button type="submit">Tai ve file rule da ma hoa</button>
    </form>
    <form method="POST" action="/nettools/ifthen/import" enctype="multipart/form-data" style="margin-top:16px;">
        <label>File rule da ma hoa:</label>
        <input type="file" name="file" required>
        <label>Passphrase de giai ma:</label>
        <input type="password" name="passphrase" required>
        <button type="submit">Nhap rule</button>
    </form>
</body>
</html>
"""


def _render(msg="", ok=True, suggestions=None):
    rules = load_rules()
    return render_template_string(
        IFTHEN_TEMPLATE, rules=list(enumerate(rules)), msg=msg, ok=ok, suggestions=suggestions
    )


@nettools_bp.route("/nettools/ifthen")
def ifthen_route():
    return _render()


@nettools_bp.route("/nettools/ifthen/evaluate", methods=["POST"])
def ifthen_evaluate_route():
    result = evaluate_rules()
    if not result["ok"]:
        return _render(msg=f"Loi LLDP: {result['error']}", ok=False, suggestions=None)
    return _render(suggestions=result["suggestions"])


@nettools_bp.route("/nettools/ifthen/add", methods=["POST"])
def ifthen_add_route():
    f = request.form
    commands = [c for c in (f.get("commands") or "").splitlines() if c.strip()]
    if not f.get("name") or not f.get("pattern") or not commands:
        return _render(msg="Thieu ten/pattern/lenh.", ok=False)
    try:
        re.compile(f.get("pattern"))
    except re.error as e:
        return _render(msg=f"Regex khong hop le: {e}", ok=False)

    add_rule(f.get("name"), f.get("field", "remote_name"), f.get("pattern"),
              f.get("device_type", "cisco_ios"), commands)
    return _render(msg=f"Da them rule '{f.get('name')}'.", ok=True)


@nettools_bp.route("/nettools/ifthen/delete", methods=["POST"])
def ifthen_delete_route():
    idx = int(request.form.get("index", -1))
    if delete_rule(idx):
        return _render(msg="Da xoa rule.", ok=True)
    return _render(msg="Khong tim thay rule.", ok=False)


@nettools_bp.route("/nettools/ifthen/export", methods=["POST"])
def ifthen_export_route():
    passphrase = request.form.get("passphrase", "")
    if not passphrase:
        return _render(msg="Can nhap passphrase.", ok=False)
    from flask import Response
    blob = export_rules_encrypted(passphrase)
    return Response(
        blob, mimetype="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=console-pi-rules.enc"},
    )


@nettools_bp.route("/nettools/ifthen/import", methods=["POST"])
def ifthen_import_route():
    passphrase = request.form.get("passphrase", "")
    file = request.files.get("file")
    if not passphrase or not file:
        return _render(msg="Can chon file va nhap passphrase.", ok=False)
    ok, msg = import_rules_encrypted(passphrase, file.read())
    return _render(msg=msg, ok=ok)


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(evaluate_rules(), indent=2, ensure_ascii=False))
