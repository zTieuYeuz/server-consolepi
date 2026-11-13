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
import re
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
    "terminal-may": ("Terminal tại chỗ (shell root của Pi)", ["/terminal", "/api/send-keys"]),
    "nguon": ("Nguồn điện: tắt / khởi động lại Pi", ["/power"]),
    "cai-windows": ("Cài Windows qua mạng (PXE)", ["/deployos", "/gopy", "/api/tiendo/data"]),
    "phan-mem": ("Triển khai / kho phần mềm", ["/deployos/trienkhai", "/deployos/kho", "/deployos/ungdung", "/deployos/font", "/deployos/drivers", "/kho-trung-tam", "/tk"]),
    "may-tram": ("Quản lý máy trạm", ["/uem"]),
    "remote": ("Remote: SSH, terminal, RDP, VNC, đường hầm", ["/ssh", "/terminal", "/phien", "/remote", "/remote-desktop", "/console", "/commands", "/term-local", "/term-ssh", "/term-phien", "/term-console", "/uem-vnc-ws"]),
    "rustdesk": ("RustDesk", ["/rustdesk"]),
    "mang": ("Mạng, WiFi, Bluetooth", ["/nettools", "/wifi", "/wifi-", "/connect-wifi", "/release-ap", "/force-ap", "/bluetooth", "/bt-", "/direct", "/rename"]),
    "luu-tru": ("Lưu trữ / tài nguyên", ["/storage", "/tai-nguyen"]),
    "nhat-ky": ("Nhật ký", ["/logs"]),
    "chung": ("Trang chung và cài đặt", ["/", "/settings", "/giaodien", "/ngon-ngu", "/docs", "/giaitri", "/api/status", "/api/suckhoe", "/logout"]),
}
# Cong vao do nginx chuyen thang toi ttyd/cau noi VNC (khong qua route Flask), chi kiem bang auth_request /_auth: nhap phim/dieu khien = muc "ghi" ke ca khi la GET/WebSocket
CONG_VAO = ("/term-local", "/term-ssh", "/term-phien", "/term-console", "/uem-vnc-ws")
# Thao tac "huy diet" (khong GET) KHAI TUONG MINH theo mau route Flask (<x> = mot doan): Van hanh/Chi xem KHONG duoc dung. Tat/khoi dong lai Pi, doi mang loi,
# bat/tat dich vu mang, xoa du lieu/may/kich ban/phien, khoi phuc. Route moi co ten giong the ma chua khai o day (hoac o MIEN_PHA_HUY) thi test CI do.
PHA_HUY = (
    "/power/<what>", "/rename", "/force-ap", "/release-ap", "/direct/bat", "/direct/tat", "/deployos/pxe/bat", "/deployos/pxe/tat", "/deployos/pxe/cong", "/nettools/tftp/bat", "/nettools/tftp/tat",
    "/remote/bat", "/remote/tat", "/remote/ts/bat", "/remote/ts/tat", "/settings/kiosk/bat", "/settings/kiosk/tat", "/wifi-delete",
    "/terminal/paste", "/api/send-keys", "/commands/add", "/commands/send", "/commands/delete",
    # cai goi / dich vu tren chinh Pi, khoa mang, bi mat dich vu, bat goi tin
    "/remote/cai", "/remote/token", "/remote/ts/cai", "/remote/ts/authkey", "/remote/ts/quen", "/remote-desktop/cai", "/rustdesk/api/cai", "/rustdesk/api/cai-dat",
    "/rustdesk/api/hanh-dong", "/settings/api/xem-mat-khau-terminal", "/wifi/api/xem-mat-khau-ap", "/nettools/pcap/start", "/nettools/pcap/stop", "/nettools/pcap/convert", "/deployos/caidat/wol/xoa", "/deployos/console/apps/xoa", "/deployos/console/file/xoa", "/deployos/console/scripts/xoa",
    "/deployos/drivers/<driver_id>/xoa-file", "/deployos/drivers/xoa", "/deployos/font/<bo_id>/xoa-font", "/deployos/font/xoa", "/deployos/kho/huy",
    "/deployos/kho/xoa-cauhinh", "/deployos/kho/xoa-xong", "/deployos/kichban/xoa", "/deployos/lichsu/xoa", "/deployos/o-dia/xoa", "/deployos/o-dia/xoa-het",
    "/deployos/os/xoa", "/deployos/tiendo/xoa", "/deployos/trienkhai/kichban/xoa", "/deployos/trienkhai/lich/xoa", "/deployos/trienkhai/may/nhom/xoa",
    "/deployos/trienkhai/may/taikhoan/xoa", "/deployos/trienkhai/may/xoa", "/deployos/trienkhai/nhom-tn/xoa", "/deployos/trienkhai/tt/<kb_id>/xoa",
    "/deployos/ungdung/<ung_id>/xoa-muc", "/deployos/ungdung/xoa", "/nettools/console-backup/xoa", "/nettools/ifthen/delete", "/nettools/tftp/xoa",
    "/phien/api/nhom/doi-ten", "/phien/api/nhom/xoa", "/phien/api/xoa", "/remote/xoa-token", "/rustdesk/api/ghi-hinh/xoa", "/rustdesk/api/xoa-id",
    "/settings/khoi-phuc", "/settings/nap-sao-luu", "/storage/xoa", "/uem/may/<mid>/duyet-file/xoa", "/uem/may/<mid>/may-in/xoa", "/uem/may/<mid>/xoa",
    "/uem/profiles/<pid>/xoa", "/uem/quan-tri/<muc>/xoa", "/uem/quan-tri/agent/goi/<gid>/xoa", "/uem/trien-khai/dot/<dot>/huy", "/uem/trien-khai/kich-ban/<kb_id>/xoa",
)
# Route co ten giong thao tac huy diet nhung CO Y cho Van hanh (khai ro de test khong bao): bat/tat tinh nang thuong ngay, khong mat du lieu
MIEN_PHA_HUY = {"/nguoi-dung/xoa": "da la quan_tri qua dich vu nguoi-dung", "/bt-reset": "reset adapter Bluetooth", "/uem/profiles/<pid>/bat-tat": "bat/tat ap dung profile (khoi phuc duoc)",
                "/wifi-mac-bat": "loc MAC wifi", "/wifi-mac-tat": "loc MAC wifi", "/cap-nhat/bat-dau": "da la quan_tri qua dich vu cap-nhat",
                "/cap-nhat/huy": "da la quan_tri qua dich vu cap-nhat"}
MAU_NGHI_HUY = re.compile(r"(^|[/_-])(xoa|delete|remove|reset|wipe|format|restore|shutdown|reboot|poweroff|power|doi-ten|rename|tat|bat|huy|khoi-phuc|nap)([/_-]|$)")


def _mau_ra_regex(mau):
    return re.compile("^" + "".join((".+" if x.startswith("<path:") else "[^/]+") if x.startswith("<") else re.escape(x) for x in re.split(r"(<[^>]+>)", mau)) + "$")


# Phien serial / terminal may nay trong trang Phien (ma = local | serial-*): shell root + cong serial cua Pi
PHA_HUY_RE_PHU = (re.compile(r"^/phien/api/(local|serial-[^/]+)/"),)
_PHA_HUY_RE = [_mau_ra_regex(m) for m in PHA_HUY] + list(PHA_HUY_RE_PHU)


# GET KHONG dong nghia an toan: doc noi dung terminal/serial/log phien, ban chup goi tin, ban sao luu cau hinh thiet bi, goi agent, tai khoan trien khai... (LOI NV8-02)
GET_QUAN_TRI = (
    "/phien/api/<ma>/log", "/nettools/pcap", "/nettools/pcap/download/<path:filename>", "/nettools/console-backup", "/nettools/console-backup/tai/<path:ten>",
    "/nettools/tftp/tai/<path:ten>", "/logs/tai", "/uem/quan-tri/agent/goi/<gid>/tai", "/deployos/trienkhai/may/taikhoan",
)
# GET chi cho Van hanh tro len (Chi xem khong): ban ghi man hinh, tai tep tu may tram
GET_GHI = ("/uem/may/<mid>/tu-xa/vnc/<tok>", "/rustdesk/ghi-hinh/<mid>/<ten>", "/uem/may/<mid>/duyet-file/tai", "/rustdesk/api/lich-su")
_GET_QT_RE = [_mau_ra_regex(m) for m in GET_QUAN_TRI]
_GET_GHI_RE = [_mau_ra_regex(m) for m in GET_GHI]


def la_pha_huy(path):
    return any(r.match(path) for r in _PHA_HUY_RE)


# Cong vao nginx chi danh cho Quan tri (LOI-011-F, CEO chot 12/11): shell root cua chinh Pi (terminal tai cho) va cong console/serial. Cong phien SSH (?arg=<ma>) van
# cho Van hanh, TRU phien dac biet "local" (terminal may nay) va "serial-*" (cong serial).
CONG_VAO_QUAN_TRI = ("/term-local", "/term-ssh", "/term-console")   # /term-ssh = ttyd SSH dung chung kieu cu (root, con chay, khong con trang dan toi): chi Quan tri (LOI-013)


def chuan_uri(uri):
    """Dua URI cong vao ve dang that: giai ma %xx lap lai (chong %252e), doi \\ thanh /, gon // va ./.. nhu nginx/ttyd. Tra (duong_chuan, query, la_lat_leo).
    la_lat_leo = co '..' hoac ma hoa/ky tu la trong duong dan - nginx chon location theo duong dan chua chuan hoa nen kiem quyen khong duoc tin."""
    import posixpath
    from urllib.parse import unquote
    duong, _, query = (uri or "").partition("?")
    thô = duong
    for _ in range(3):
        giai = unquote(duong)
        if giai == duong:
            break
        duong = giai
    duong = duong.replace("\\", "/")
    lat = (".." in duong.split("/")) or ("." in duong.split("/")[1:-1]) or ("%" in thô and duong != thô) or ("\x00" in duong) or ("//" in duong)
    chuan = posixpath.normpath(duong) if duong else "/"
    if duong.endswith("/") and not chuan.endswith("/"):
        chuan += "/"
    return chuan, query, lat


def muc_cong_vao(uri):
    """'quan_tri' neu URI cong vao (co ca query) cham toi shell root/serial cua Pi, nguoc lai None. URI co dau hieu lach duong dan (.., %2e, //) cung tinh la quan_tri."""
    from urllib.parse import parse_qs
    duong, query, lat = chuan_uri(uri)
    if lat or any(_khop(duong, t) for t in CONG_VAO_QUAN_TRI):
        return "quan_tri"
    if _khop(duong, "/term-phien"):
        for a in parse_qs(query).get("arg", []):
            if a == "local" or a.startswith("serial-"):
                return "quan_tri"
    return None


# dich vu ma van_hanh/chi_xem KHONG duoc dung (ke ca doc): quyet o thiet ke RBAC G1 muc 2 va cau hoi 4
DICH_VU_QUAN_TRI = {"cap-nhat", "sao-luu", "nguoi-dung", "nguon", "terminal-may"}
# Loi vao KHONG qua RBAC (khong co phien Console): moi muc co co che xac thuc rieng trong web/auth.py; liet ke HET de test khong cho them am tham.
CONG_KHAI = {
    "/login": "dang nhap", "/logout": "tu thoat (ca nguoi chua gan vai tro)", "/healthz": "kiem tra song", "/_auth": "nginx auth_request", "/vkeyboard.js": "tai nguyen tinh", "/dashboard.js": "tai nguyen tinh",
    "/favicon.ico": "tai nguyen tinh", "/static": "tai nguyen tinh", "/thuong-hieu": "logo",
    "/deployos/pxeboot": "may boot PXE (chi khi PXE bat, mang noi bo)", "/api/tiendo/batdau": "may vua cai bao tien trinh (chi khi PXE bat)", "/api/tiendo/buoc": "nt", "/api/tiendo/domain": "nt", "/api/tiendo/ketthuc": "nt",
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
    if any(r.match(path) for r in PHA_HUY_RE_PHU):          # terminal may nay / cong serial trong trang Phien: MOI phuong thuc (GET log cung la quan_tri)
        return "quan_tri"
    if dv in DICH_VU_QUAN_TRI:
        return "quan_tri"
    if method.upper() not in ("GET", "HEAD", "OPTIONS") and la_pha_huy(path):
        return "quan_tri"
    if any(_khop(path, t) for t in CONG_VAO):
        return "ghi"
    if method.upper() in ("GET", "HEAD", "OPTIONS"):
        if any(r.match(path) for r in _GET_QT_RE):
            return "quan_tri"
        if any(r.match(path) for r in _GET_GHI_RE):
            return "ghi"
    return "xem" if method.upper() in ("GET", "HEAD", "OPTIONS") else "ghi"


def cho_phep(vai_tro, method, path, nang_muc=None):
    """(ok, ly_do). Route chua khai: tu choi (mac dinh tu choi) - o buoc 1 chi duoc GHI NHAN."""
    if la_cong_khai(path):
        return True, "cong-khai"
    dv = dich_vu_cua(path)
    if dv is None:
        return False, "route-chua-khai"
    if vai_tro == "quan_tri":
        return True, ""
    m = muc_can(method, path)
    if nang_muc == "quan_tri":
        m = "quan_tri"
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
    from consolesystem.core.store import ghi_json
    ghi_json(FILE, d, mode=0o600, ensure_ascii=False)


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


def ghi_nhan(method, path, user, la_quan_tri_fn, gio=time.time, nang_muc=None):
    """Buoc 1: tinh quyet dinh, neu SE bi tu choi thi ghi nhat ky (toi da 1 lan / 10 phut cho moi nguoi+dich vu+ly do) va nho 50 su kien gan nhat.
    KHONG bao gio chan. Tra (ok, ly_do) de test."""
    vt = vai_tro_cua(user, la_quan_tri_fn)
    ok, ly = cho_phep(vt, method, path, nang_muc)
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
