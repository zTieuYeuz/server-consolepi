# Console System - (c) 2026 zTieuYeuz. All rights reserved.
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
from consolesystem.core import taisan as _taisan
import base64
import json
import re

from flask import request, render_template_string

from . import nettools_bp
from .lldp import get_lldp_neighbors
from ui import duongdan as _DD

RULES_FILE = _DD.FILE_IFTHEN


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
        return False, "Sai passphrase hoặc file không hợp lệ."
    try:
        rules = json.loads(data)
    except json.JSONDecodeError:
        return False, "Nội dung sau giải mã không phải JSON hợp lệ."
    save_rules(rules)
    return True, f"Đã nhập {len(rules)} rule."


IFTHEN_TEMPLATE = _taisan.doc("nettools/ifthen.IFTHEN_TEMPLATE.html")


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
        return _render(msg=f"Lỗi LLDP: {result['error']}", ok=False, suggestions=None)
    return _render(suggestions=result["suggestions"])


@nettools_bp.route("/nettools/ifthen/add", methods=["POST"])
def ifthen_add_route():
    f = request.form
    commands = [c for c in (f.get("commands") or "").splitlines() if c.strip()]
    if not f.get("name") or not f.get("pattern") or not commands:
        return _render(msg="Thiếu tên/pattern/lệnh.", ok=False)
    try:
        re.compile(f.get("pattern"))
    except re.error as e:
        return _render(msg=f"Regex không hợp lệ: {e}", ok=False)

    add_rule(f.get("name"), f.get("field", "remote_name"), f.get("pattern"),
              f.get("device_type", "cisco_ios"), commands)
    return _render(msg=f"Đã thêm rule '{f.get('name')}'.", ok=True)


@nettools_bp.route("/nettools/ifthen/delete", methods=["POST"])
def ifthen_delete_route():
    idx = int(request.form.get("index", -1))
    if delete_rule(idx):
        return _render(msg="Đã xóa rule.", ok=True)
    return _render(msg="Không tìm thấy rule.", ok=False)


@nettools_bp.route("/nettools/ifthen/export", methods=["POST"])
def ifthen_export_route():
    passphrase = request.form.get("passphrase", "")
    if not passphrase:
        return _render(msg="Cần nhập passphrase.", ok=False)
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
        return _render(msg="Cần chọn file và nhập passphrase.", ok=False)
    ok, msg = import_rules_encrypted(passphrase, file.read())
    return _render(msg=msg, ok=ok)


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(evaluate_rules(), indent=2, ensure_ascii=False))
