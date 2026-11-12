# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
PHAN QUYEN (RBAC) - 2.0.7: registry + bang nguoi dung + vai tro. Buoc 1 = che do GHI NHAN; buoc 2 = CHAN (mac dinh bat; dat bien moi truong
CONSOLE_RBAC_GHI_NHAN=1 de quay lai chi ghi nhan neu can cuu).

Thuan logic, khong import flask. Moi route thuoc DUNG MOT dich vu trong REGISTRY (khop theo tien to dai nhat) hoac nam trong CONG_KHAI (loi vao
khong qua dang nhap Console, da co co che rieng: PXE, may cai bao ve, tai goi, agent mTLS). Route khong thuoc ai = "chua khai" - test CI bao.
Muc: xem < ghi < quan_tri. Vai tro: quan_tri (moi quyen), van_hanh (xem + ghi cac dich vu van hanh, KHONG dung cac dich vu quan_tri), chi_xem (chi GET).
Tai khoan CUU HO: root va thanh vien nhom sudo luon la quan_tri (khong bi bang vai tro ha xuong) - khong the tu khoa minh ra ngoai;
`scripts/rbac-reset.py` xoa rbac.json ve mac dinh.
"""
import json
import os
import threading
import time

from consolesystem.core import duongdan as DD

FILE = os.path.join(DD.THU_MUC_DU_LIEU, "rbac.json")
VAI_TRO = {"quan_tri": "Quản trị", "van_hanh": "Vận hành", "chi_xem": "Chỉ xem"}
LOCAL_MAC_DINH = "van_hanh"       # man hinh cuc bo tren Pi (khong qua dang nhap): cho anh quyet (cau hoi 2) - tam la Van hanh, KHONG phai Quan tri
_KHOA = threading.Lock()

# dich vu -> (nhan, [tien to route]). Tien to dai nhat thang.
REGISTRY = {
    "cap-nhat": ("Cập nhật Console System", ["/cap-nhat", "/khoa-may", "/commands/update"]),
    "sao-luu": ("Sao lưu / khôi phục / khóa", ["/settings/sao-luu", "/settings/nap-sao-luu", "/settings/khoi-phuc", "/settings/rotate", "/settings/regen-term-pass"]),
    "nguoi-dung": ("Người dùng và vai trò", ["/nguoi-dung"]),
    "cai-windows": ("Cài Windows qua mạng (PXE)", ["/deployos", "/gopy"]),
    "phan-mem": ("Triển khai / kho phần mềm", ["/deployos/trienkhai", "/deployos/kho", "/deployos/ungdung", "/deployos/font", "/deployos/drivers", "/kho-trung-tam", "/tk"]),
    "may-tram": ("Quản lý máy trạm", ["/uem"]),
    "remote": ("Remote: SSH, terminal, RDP, VNC, đường hầm", ["/ssh", "/terminal", "/phien", "/remote", "/remote-desktop", "/console", "/api/send-keys", "/commands"]),
    "rustdesk": ("RustDesk", ["/rustdesk"]),
    "mang": ("Mạng, WiFi, Bluetooth", ["/nettools", "/wifi", "/wifi-", "/connect-wifi", "/release-ap", "/force-ap", "/bluetooth", "/bt-", "/direct", "/rename"]),
    "luu-tru": ("Lưu trữ / tài nguyên", ["/storage", "/tai-nguyen"]),
    "nhat-ky": ("Nhật ký", ["/logs"]),
    "chung": ("Trang chung và cài đặt", ["/", "/settings", "/giaodien", "/ngon-ngu", "/docs", "/giaitri", "/api/status", "/api/suckhoe", "/logout", "/power"]),
}
# dich vu ma van_hanh/chi_xem KHONG duoc dung (ke ca doc): quyet o thiet ke RBAC G1 muc 2 va cau hoi 4
DICH_VU_QUAN_TRI = {"cap-nhat", "sao-luu", "nguoi-dung"}
# Loi vao KHONG qua RBAC (khong co phien Console): moi muc co co che xac thuc rieng trong web/auth.py; liet ke HET de test khong cho them am tham.
CONG_KHAI = {
    "/login": "dang nhap", "/healthz": "kiem tra song", "/_auth": "nginx auth_request", "/vkeyboard.js": "tai nguyen tinh", "/dashboard.js": "tai nguyen tinh",
    "/favicon.ico": "tai nguyen tinh", "/static": "tai nguyen tinh", "/thuong-hieu": "logo",
    "/deployos/pxeboot": "may boot PXE (chi khi PXE bat, mang noi bo)", "/api/tiendo": "may vua cai bao tien trinh (chi khi PXE bat)",
    "/tk/tai": "may dich tai goi cai (Trien khai phan mem)", "/uem/agent": "agent Windows (mTLS / ma ghi danh)", "/uem/novnc": "tai nguyen noVNC tinh",
}


def _khop(path, tien_to):
    if tien_to == "/":
        return path == "/"
    return path == tien_to or path.startswith(tien_to.rstrip("/") + "/") or (tien_to.endswith("-") and path.startswith(tien_to))


def la_cong_khai(path):
    return any(_khop(path, t) for t in CONG_KHAI)


def dich_vu_cua(path):
    """Id dich vu so huu route, hoac None (chua khai). Tien to dai nhat thang; '/' chi khop dung '/'."""
    tot, kq = -1, None
    for dv, (_n, tt) in REGISTRY.items():
        for t in tt:
            if _khop(path, t) and len(t) > tot:
                tot, kq = len(t), dv
    return kq


def muc_can(method, path):
    dv = dich_vu_cua(path)
    if dv in DICH_VU_QUAN_TRI:
        return "quan_tri"
    return "xem" if method.upper() in ("GET", "HEAD", "OPTIONS") else "ghi"


def cho_phep(vai_tro, method, path):
    """(ok, ly_do). Route chua khai: tu choi (mac dinh tu choi) - o buoc 1 chi duoc GHI NHAN."""
    if la_cong_khai(path):
        return True, "cong-khai"
    dv = dich_vu_cua(path)
    if dv is None:
        return False, "route-chua-khai"
    if vai_tro == "quan_tri":
        return True, ""
    m = muc_can(method, path)
    if m == "quan_tri":
        return False, "can-quan-tri"
    if vai_tro == "van_hanh":
        return True, ""
    if vai_tro == "chi_xem":
        return (m == "xem"), ("" if m == "xem" else "chi-xem-khong-ghi")
    return False, "khong-co-vai-tro"


# ----------------------------------------------------------------------------------------------- du lieu
def _doc():
    try:
        with open(FILE, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("nguoi_dung"), dict):
            return d
    except (OSError, ValueError):
        pass
    return {"nguoi_dung": {}}


def _ghi(d):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    tam = FILE + ".tmp"
    fd = os.open(tam, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tam, FILE)


def danh_sach():
    return dict(_doc()["nguoi_dung"])


def dat_vai_tro(ten, vai_tro):
    if vai_tro not in VAI_TRO:
        raise ValueError("Vai trò không hợp lệ.")
    with _KHOA:
        d = _doc()
        d["nguoi_dung"][ten] = {"vai_tro": vai_tro, "luc": int(time.time())}
        _ghi(d)


def xoa(ten):
    with _KHOA:
        d = _doc()
        co = d["nguoi_dung"].pop(ten, None) is not None
        if co:
            _ghi(d)
        return co


def reset():
    """rbac-reset: ve mac dinh (sudo/root = Quan tri, nguoi khac chua co vai tro)."""
    try:
        os.remove(FILE)
        return True
    except FileNotFoundError:
        return False


def vai_tro_cua(user, la_quan_tri_fn):
    """Vai tro hieu luc. root/sudo luon quan_tri (tai khoan cuu ho). user None = man hinh cuc bo tren Pi."""
    if not user:
        return LOCAL_MAC_DINH
    if user == "root" or la_quan_tri_fn(user):
        return "quan_tri"
    return _doc()["nguoi_dung"].get(user, {}).get("vai_tro")


# ----------------------------------------------------------------------------------------------- ghi nhan (buoc 1)
_GHI_NHAN = {"sap_tu_choi": [], "gan_nhat": {}}      # in-memory: khong ghi dia, de xem tren trang Nguoi dung


def dang_chan():
    """Buoc 2: chan that. CONSOLE_RBAC_GHI_NHAN=1 (systemd override) quay lai che do chi ghi nhan."""
    return os.environ.get("CONSOLE_RBAC_GHI_NHAN", "") not in ("1", "true", "yes")


def ghi_nhan(method, path, user, la_quan_tri_fn, gio=time.time):
    """Buoc 1: tinh quyet dinh, neu SE bi tu choi thi ghi nhat ky (toi da 1 lan / 10 phut cho moi nguoi+dich vu+ly do) va nho 50 su kien gan nhat.
    KHONG bao gio chan. Tra (ok, ly_do) de test."""
    vt = vai_tro_cua(user, la_quan_tri_fn)
    ok, ly = cho_phep(vt, method, path)
    if ok:
        return ok, ly
    now = gio()
    khoa = (user or "-", dich_vu_cua(path), ly)
    with _KHOA:
        if now - _GHI_NHAN["gan_nhat"].get(khoa, 0) < 600:
            return ok, ly
        _GHI_NHAN["gan_nhat"][khoa] = now
        _GHI_NHAN["sap_tu_choi"].append({"luc": now, "nguoi": user or "(màn hình cục bộ)", "vai_tro": vt or "(chưa có)", "method": method, "path": path[:120], "ly_do": ly})
        del _GHI_NHAN["sap_tu_choi"][:-50]
    try:
        from consolesystem.core.errlog import ghi_thao_tac
        ghi_thao_tac("RBAC: từ chối %s %s" % (method, path[:80]) if dang_chan() else "RBAC (ghi nhận, chưa chặn): sẽ từ chối %s %s" % (method, path[:80]), "vai trò %s: %s" % (vt or "chưa có", ly), nguoi=user or "-")
    except Exception as e:
        print("[rbac] khong ghi duoc nhat ky: %s" % type(e).__name__, flush=True)
    return ok, ly


def su_kien_gan_day():
    with _KHOA:
        return list(_GHI_NHAN["sap_tu_choi"])
