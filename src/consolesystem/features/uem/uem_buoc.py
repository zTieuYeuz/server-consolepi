# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - CAC LOAI TAC VU (task) cua Profile, mo phong cac task Windows cua OpenUEM
(openuem-console/internal/models/tasks.go: winget install/delete, registry add/remove key + value + default value,
local user add/remove, local group add/remove + them/bo user, msi install/uninstall, powershell script).

Moi tac vu = MOT kich ban PowerShell chay qua WinRM, theo nguyen tac "kiem tra truoc, chi lam khi chua dung trang thai"
(nhu cach WinGet Configuration/DSC ma OpenUEM dung): in dong `ST=DA_DAT` (da dung san, khong lam gi) / `ST=DA_LAM` (vua
thuc hien) / `ST=LOI ...`. Nho vay profile chay lai moi 30 phut khong cai/ghi lai khong can thiet.

Mat khau trong task (tao user) luu MA HOA (tk_dulieu.ma_hoa), chi giai ma luc chay, khong hien lai tren giao dien.
"""
import sys as _sys
_sys.modules["ui.uem_buoc"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import re
import uuid

from ui import tk_dongco as DC
from ui import tk_dulieu as DL
from consolesystem.core import duongdan as _DD

# ----------------------------------------------------------------- dinh nghia loai tac vu (cho giao dien tao task)
# truong: (ten, nhan, kieu, bat_buoc, mac_dinh, goi_y)   kieu: text | password | checkbox | select:a|b | textarea | number
REG_KIEU = ["String", "DWord", "QWord", "MultiString", "ExpandString", "Binary"]
CAC_LOAI = {
    "winget_cai": ("WinGet: cài đặt phần mềm", "winget", [
        ("goi_id", "Mã gói WinGet (tìm trong danh mục, ví dụ Google.Chrome)", "text", True, "", ""),
        ("phien_ban", "Phiên bản cụ thể (bỏ trống = mới nhất)", "text", False, "", ""),
        ("moi_nhat", "Luôn giữ bản mới nhất (tự nâng cấp khi có bản mới)", "checkbox", False, "", "")]),
    "winget_go": ("WinGet: gỡ phần mềm", "winget", [
        ("goi_id", "Mã gói WinGet", "text", True, "", "")]),
    "reg_them_khoa": ("Registry: tạo khóa", "registry", [
        ("khoa", "Khóa (HKEY_LOCAL_MACHINE\\SOFTWARE\\...)", "text", True, "", "")]),
    "reg_xoa_khoa": ("Registry: xóa khóa", "registry", [
        ("khoa", "Khóa", "text", True, "", "")]),
    "reg_mac_dinh": ("Registry: đặt giá trị mặc định của khóa", "registry", [
        ("khoa", "Khóa", "text", True, "", ""), ("du_lieu", "Dữ liệu (chuỗi)", "text", False, "", "")]),
    "reg_dat_gia_tri": ("Registry: đặt giá trị", "registry", [
        ("khoa", "Khóa", "text", True, "", ""), ("ten", "Tên giá trị", "text", True, "", ""),
        ("loai", "Kiểu dữ liệu", "select:" + "|".join(REG_KIEU), True, "String", ""),
        ("du_lieu", "Dữ liệu (MultiString: mỗi dòng một chuỗi; Binary: chuỗi hex)", "textarea", False, "", ""),
        ("hex", "Dữ liệu DWord/QWord viết dạng hex", "checkbox", False, "", "")]),
    "reg_xoa_gia_tri": ("Registry: xóa giá trị", "registry", [
        ("khoa", "Khóa", "text", True, "", ""), ("ten", "Tên giá trị", "text", True, "", "")]),
    "user_them": ("Người dùng cục bộ: tạo / cập nhật", "nguoidung", [
        ("ten", "Tên đăng nhập", "text", True, "", ""), ("ho_ten", "Họ tên đầy đủ", "text", False, "", ""),
        ("mo_ta", "Mô tả", "text", False, "", ""), ("mat_khau", "Mật khẩu (chỉ đặt khi tạo mới; để trống = không mật khẩu)", "password", False, "", ""),
        ("tat", "Vô hiệu hóa tài khoản", "checkbox", False, "", ""),
        ("khong_doi_mk", "Người dùng không được đổi mật khẩu", "checkbox", False, "", ""),
        ("phai_doi_mk", "Bắt đổi mật khẩu ở lần đăng nhập đầu", "checkbox", False, "", ""),
        ("mk_khong_het_han", "Mật khẩu không bao giờ hết hạn", "checkbox", False, "", "")]),
    "user_xoa": ("Người dùng cục bộ: xóa", "nguoidung", [
        ("ten", "Tên đăng nhập", "text", True, "", "")]),
    "nhom_them": ("Nhóm cục bộ: tạo / bổ sung thành viên", "nhom", [
        ("ten", "Tên nhóm", "text", True, "", ""), ("mo_ta", "Mô tả", "text", False, "", ""),
        ("thanh_vien", "Thành viên (mỗi dòng một tên; chỉ thêm, không gỡ người khác)", "textarea", False, "", "")]),
    "nhom_xoa": ("Nhóm cục bộ: xóa", "nhom", [
        ("ten", "Tên nhóm", "text", True, "", "")]),
    "nhom_them_user": ("Nhóm cục bộ: thêm người dùng vào nhóm", "nhom", [
        ("ten", "Tên nhóm", "text", True, "", ""), ("thanh_vien", "Người dùng cần thêm (mỗi dòng một tên)", "textarea", True, "", "")]),
    "nhom_bo_user": ("Nhóm cục bộ: gỡ người dùng khỏi nhóm", "nhom", [
        ("ten", "Tên nhóm", "text", True, "", ""), ("thanh_vien", "Người dùng cần gỡ (mỗi dòng một tên)", "textarea", True, "", "")]),
    "msi_cai": ("MSI: cài đặt", "msi", [
        ("product_id", "Mã sản phẩm (ProductCode, dạng {GUID})", "text", True, "", ""),
        ("duong_dan", "Đường dẫn file .msi (URL, hoặc đường dẫn trên máy đích, hoặc tên file .msi trong Tài nguyên máy → Phần mềm)", "text", True, "", ""),
        ("tham_so", "Tham số thêm cho msiexec (mặc định /qn /norestart)", "text", False, "", ""),
        ("log", "File log (trên máy đích)", "text", False, "", ""),
        ("hash_alg", "Kiểm tra toàn vẹn: thuật toán", "select:|MD5|SHA1|SHA256|SHA384|SHA512", False, "", ""),
        ("hash", "Giá trị băm", "text", False, "", "")]),
    "msi_go": ("MSI: gỡ cài đặt", "msi", [
        ("product_id", "Mã sản phẩm (ProductCode, dạng {GUID})", "text", True, "", ""),
        ("tham_so", "Tham số thêm cho msiexec", "text", False, "", "")]),
    "fw_trang_thai": ("Tường lửa: bật / tắt", "tuonglua", [
        ("ho_so", "Áp dụng cho hồ sơ mạng", "select:tat_ca=Tất cả (Domain, Private, Public)|Domain=Domain (mạng công ty có domain)|Private=Private (mạng riêng)|Public=Public (mạng công cộng)", True, "tat_ca", ""),
        ("bat", "Tường lửa", "select:bat=Bật tường lửa|tat=Tắt tường lửa", True, "bat", ""),
        ("vao", "Kết nối VÀO máy không khớp quy tắc nào", "select:giu=Giữ nguyên|Block=Chặn (khuyên dùng)|Allow=Cho phép", True, "giu", "")]),
    "fw_quy_tac": ("Tường lửa: tạo / sửa quy tắc", "tuonglua", [
        ("ten", "Tên quy tắc (dùng để nhận ra quy tắc, đổi tên = quy tắc mới)", "text", True, "", ""),
        ("chieu", "Chiều", "select:Inbound=Vào máy (Inbound)|Outbound=Ra ngoài (Outbound)", True, "Inbound", ""),
        ("hanh_dong", "Hành động", "select:Allow=Cho phép|Block=Chặn", True, "Allow", ""),
        ("giao_thuc", "Giao thức", "select:TCP=TCP|UDP=UDP|Any=Mọi giao thức|ICMPv4=ICMPv4 (ping)", True, "TCP", ""),
        ("cong", "Cổng (ví dụ 3389 hoặc 80,443 hoặc 8000-8100; trống = mọi cổng)", "text", False, "", "Vào máy: cổng trên máy này. Ra ngoài: cổng của máy đích."),
        ("dia_chi", "Chỉ áp dụng cho địa chỉ (ví dụ 192.168.1.10, 10.0.0.0/24, LocalSubnet; trống = mọi địa chỉ)", "text", False, "", ""),
        ("chuong_trinh", "Chỉ áp dụng cho chương trình (đường dẫn .exe trên máy; trống = mọi chương trình)", "text", False, "", ""),
        ("ho_so", "Hồ sơ mạng", "select:Any=Tất cả|Domain=Domain|Private=Private|Public=Public", True, "Any", ""),
        ("tat", "Tạo nhưng để tắt (chưa có hiệu lực)", "checkbox", False, "", "")]),
    "fw_xoa_quy_tac": ("Tường lửa: xóa quy tắc", "tuonglua", [
        ("ten", "Tên quy tắc cần xóa", "text", True, "", "")]),
    "fw_nhom": ("Tường lửa: bật / tắt nhóm quy tắc có sẵn của Windows", "tuonglua", [
        ("nhom", "Nhóm quy tắc", "select:rdp=Remote Desktop (cổng 3389)|chia_se=Chia sẻ file và máy in (kèm ping)|kham_pha=Network Discovery (thấy máy trong mạng)|winrm=Windows Remote Management (WinRM)|ho_tro=Remote Assistance", True, "rdp", ""),
        ("trang_thai", "Trạng thái", "select:bat=Bật (cho phép)|tat=Tắt (chặn)", True, "bat", "")]),
    "dv_cau_hinh": ("Dịch vụ Windows: kiểu khởi động / chạy / dừng", "dichvu", [
        ("ten", "Tên dịch vụ (Name, ví dụ Spooler, wuauserv, RemoteRegistry)", "text", True, "", "Xem tên ở tab Dịch vụ của từng máy."),
        ("khoi_dong", "Kiểu khởi động", "select:giu=Giữ nguyên|Automatic=Tự động|Manual=Thủ công|Disabled=Vô hiệu hóa", True, "giu", ""),
        ("trang_thai", "Trạng thái", "select:giu=Giữ nguyên|Running=Đang chạy|Stopped=Dừng", True, "giu", "")]),
    "powershell": ("Script PowerShell", "powershell", [
        ("script", "Nội dung script", "textarea", True, "", ""),
        ("chay", "Chạy", "select:mot_lan|luon", True, "mot_lan", "mot_lan = chạy một lần thành công rồi thôi; luon = chạy lại mỗi chu kỳ")]),
}
NHOM_LOAI = {"winget": "WinGet", "tuonglua": "Tường lửa", "dichvu": "Dịch vụ Windows", "registry": "Registry", "nguoidung": "Người dùng cục bộ",
             "nhom": "Nhóm cục bộ", "msi": "MSI", "powershell": "PowerShell"}
NHOM_MO_TA = {"winget": "Cài, gỡ, giữ phần mềm luôn mới", "tuonglua": "Bật tường lửa, mở / chặn cổng, quy tắc theo chương trình",
              "dichvu": "Bật, tắt, đổi kiểu khởi động dịch vụ", "registry": "Tạo, sửa, xóa khóa và giá trị",
              "nguoidung": "Tạo, sửa, xóa tài khoản trên máy", "nhom": "Nhóm Administrators, Remote Desktop Users...",
              "msi": "Cài / gỡ gói .msi theo mã sản phẩm", "powershell": "Việc khác: tự viết script"}
NHOM_ICON = {"winget": "📦", "tuonglua": "🛡️", "dichvu": "⚙️", "registry": "🗝️", "nguoidung": "👤", "nhom": "👥", "msi": "💿", "powershell": "⌨️"}
# Mau nhanh (dien san form): (nhan, loai, tham_so)
MAU = {
    "fw_bat": ("Bật tường lửa mọi hồ sơ, chặn kết nối vào lạ", "fw_trang_thai", {"ho_so": "tat_ca", "bat": "bat", "vao": "Block"}),
    "fw_rdp": ("Mở Remote Desktop", "fw_nhom", {"nhom": "rdp", "trang_thai": "bat"}),
    "fw_ping": ("Cho phép ping vào máy", "fw_quy_tac", {"ten": "Cho phép ping (ICMPv4)", "chieu": "Inbound", "hanh_dong": "Allow", "giao_thuc": "ICMPv4", "ho_so": "Any"}),
    "fw_chia_se": ("Bật chia sẻ file và máy in", "fw_nhom", {"nhom": "chia_se", "trang_thai": "bat"}),
    "fw_web": ("Mở cổng web 80, 443 vào máy", "fw_quy_tac", {"ten": "Web 80-443", "chieu": "Inbound", "hanh_dong": "Allow", "giao_thuc": "TCP", "cong": "80,443", "ho_so": "Any"}),
    "fw_chan_smb": ("Chặn SMB (445) từ ngoài mạng nội bộ", "fw_quy_tac", {"ten": "Chặn SMB ngoài LAN", "chieu": "Inbound", "hanh_dong": "Block", "giao_thuc": "TCP", "cong": "445", "dia_chi": "Internet", "ho_so": "Any"}),
    "dv_spooler": ("Tắt dịch vụ in (máy không dùng máy in)", "dv_cau_hinh", {"ten": "Spooler", "khoi_dong": "Disabled", "trang_thai": "Stopped"}),
    "dv_remreg": ("Tắt Remote Registry", "dv_cau_hinh", {"ten": "RemoteRegistry", "khoi_dong": "Disabled", "trang_thai": "Stopped"}),
}
_FW_NHOM = {"rdp": "@FirewallAPI.dll,-28752", "chia_se": "@FirewallAPI.dll,-28502", "kham_pha": "@FirewallAPI.dll,-32752",
            "winrm": "@FirewallAPI.dll,-30267", "ho_tro": "@FirewallAPI.dll,-33002"}


def gia_tri_chon(kieu):
    """'select:a=Nhan A|b' -> [('a', 'Nhan A'), ('b', 'b')]"""
    return [tuple(x.split("=", 1)) if "=" in x else (x, x) for x in kieu[7:].split("|")]

_RE_GUID = re.compile(r"^\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}$")
_RE_GOI = re.compile(r"^[A-Za-z0-9._+-]{2,100}$")
_RE_TEN = re.compile(r"^[^\\/\[\]:;|=,+*?<>\"@\x00-\x1f]{1,64}$")          # ten user/nhom Windows (khong chua cac ky tu cam)
_RE_KHOA = re.compile(r"^(HKEY_LOCAL_MACHINE|HKLM|HKEY_CLASSES_ROOT|HKCR|HKEY_USERS|HKU|HKEY_CURRENT_CONFIG|HKCC)(\\[^\x00-\x1f]+)*$", re.I)
_HIVE = {"HKLM": "HKEY_LOCAL_MACHINE", "HKCR": "HKEY_CLASSES_ROOT", "HKU": "HKEY_USERS", "HKCC": "HKEY_CURRENT_CONFIG"}


def _q(x):
    return DC._q(x)


def chuan_khoa(k):
    k = (k or "").strip().strip("\\")
    if not _RE_KHOA.match(k):
        return None
    dau, _, con = k.partition("\\")
    dau = _HIVE.get(dau.upper(), dau.upper())
    return "Registry::" + dau + ("\\" + con if con else "")


def _dong(v):
    return [x.strip() for x in re.split(r"[\r\n]+", v or "") if x.strip()]


def kiem_tra(loai, f):
    """(tham_so_sach, loi). f = dict giá tri form (chuỗi). Mat khau duoc MA HOA ngay tai day."""
    if loai not in CAC_LOAI:
        return None, "Loại tác vụ không hợp lệ."
    ts = {}
    for ten, nhan, kieu, bat_buoc, mac_dinh, _g in CAC_LOAI[loai][2]:
        v = f.get(ten, "")
        if isinstance(v, list):
            v = v[0] if v else ""
        v = (v or "").strip() if kieu != "textarea" else (v or "").replace("\r", "").strip("\n")
        if kieu == "checkbox":
            ts[ten] = str(v).lower() in ("1", "on", "true", "co")
            continue
        if kieu.startswith("select:"):
            ok = [g for g, _n in gia_tri_chon(kieu)]
            if v not in ok:
                v = mac_dinh if mac_dinh in ok else ok[0]
        if bat_buoc and not v:
            return None, f"Thiếu: {nhan.split('(')[0].strip()}."
        ts[ten] = v[:20000] if kieu == "textarea" else v[:500]
    if loai in ("winget_cai", "winget_go"):
        if not _RE_GOI.match(ts["goi_id"]):
            return None, "Mã WinGet không hợp lệ (chỉ chữ, số và . _ + -)."
        if loai == "winget_cai" and ts.get("phien_ban") and not re.fullmatch(r"[A-Za-z0-9._+-]{1,60}", ts["phien_ban"]):
            return None, "Phiên bản không hợp lệ."
    elif loai.startswith("reg_"):
        if not chuan_khoa(ts["khoa"]):
            return None, "Khóa registry không hợp lệ. Bắt đầu bằng HKEY_LOCAL_MACHINE, HKEY_CLASSES_ROOT, HKEY_USERS hoặc HKEY_CURRENT_CONFIG (hoặc viết tắt HKLM, HKCR, HKU, HKCC). HKEY_CURRENT_USER không dùng được vì tác vụ chạy dưới tài khoản quản trị, hãy dùng HKEY_USERS\\<SID>."
        if len(ts["khoa"].split("\\")) < 2 and loai in ("reg_xoa_khoa",):
            return None, "Không được xóa cả nhánh gốc registry."
        if loai == "reg_dat_gia_tri":
            if ts["loai"] in ("DWord", "QWord"):
                try:
                    int(ts["du_lieu"] or "0", 16 if ts.get("hex") else 10)
                except ValueError:
                    return None, "Dữ liệu DWord/QWord phải là số" + (" hex." if ts.get("hex") else " nguyên.")
            if ts["loai"] == "Binary" and not re.fullmatch(r"([0-9A-Fa-f]{2})*", ts["du_lieu"].replace(" ", "").replace(",", "")):
                return None, "Dữ liệu Binary phải là chuỗi hex (ví dụ 0A1B2C)."
    elif loai in ("user_them", "user_xoa", "nhom_them", "nhom_xoa", "nhom_them_user", "nhom_bo_user"):
        if not _RE_TEN.match(ts["ten"]):
            return None, "Tên không hợp lệ (không chứa \\ / [ ] : ; | = , + * ? < > \" @)."
        for tv in _dong(ts.get("thanh_vien", "")):
            if not re.match(r"^[^\[\]:;|=,+*?<>\"@\x00-\x1f/]{1,128}$", tv):
                return None, f'Tên thành viên "{tv[:40]}" không hợp lệ.'
        if loai == "user_them":
            if ts.get("mat_khau"):
                ts["mat_khau"] = DL.ma_hoa(ts["mat_khau"])
            ts["phai_doi_mk"] = ts.get("phai_doi_mk") and not ts.get("khong_doi_mk")
    elif loai in ("fw_quy_tac", "fw_xoa_quy_tac"):
        if not re.fullmatch(r"[^\x00-\x1f\"'`$|<>]{1,100}", ts["ten"]):
            return None, "Tên quy tắc không hợp lệ (không chứa dấu nháy, $, |, < >)."
        if loai == "fw_quy_tac":
            if ts.get("cong"):
                ts["cong"] = re.sub(r"\s+", "", ts["cong"])
                if ts["giao_thuc"] not in ("TCP", "UDP"):
                    return None, "Chỉ điền cổng khi giao thức là TCP hoặc UDP."
                if not re.fullmatch(r"\d{1,5}(-\d{1,5})?(,\d{1,5}(-\d{1,5})?)*", ts["cong"]) or any(int(x) > 65535 for x in re.findall(r"\d+", ts["cong"])):
                    return None, "Cổng không hợp lệ (ví dụ 3389, 80,443 hoặc 8000-8100)."
            if ts.get("dia_chi"):
                ts["dia_chi"] = re.sub(r"\s+", "", ts["dia_chi"])
                for d in ts["dia_chi"].split(","):
                    if not (d in ("LocalSubnet", "Internet", "Intranet", "DNS", "DHCP", "DefaultGateway")
                            or re.fullmatch(r"[0-9A-Fa-f:.]+(/\d{1,3})?(-[0-9A-Fa-f:.]+)?", d)):
                        return None, f'Địa chỉ "{d[:40]}" không hợp lệ (IP, IP/mặt nạ, dải IP-IP hoặc LocalSubnet, Internet).'
            if ts.get("chuong_trinh") and not re.fullmatch(r"[A-Za-z]:\\[^\x00-\x1f\"'`$|<>*?]+|%[A-Za-z]+%\\[^\x00-\x1f\"'`$|<>*?]+", ts["chuong_trinh"]):
                return None, "Đường dẫn chương trình phải dạng C:\\...\\ten.exe hoặc %ProgramFiles%\\...\\ten.exe."
    elif loai == "dv_cau_hinh":
        if not re.fullmatch(r"[A-Za-z0-9_.$@ -]{1,80}", ts["ten"]):
            return None, "Tên dịch vụ không hợp lệ (dùng tên Name, ví dụ Spooler)."
        if ts["khoi_dong"] == "giu" and ts["trang_thai"] == "giu":
            return None, "Chọn ít nhất kiểu khởi động hoặc trạng thái cần đặt."
        if ts["khoi_dong"] == "Disabled" and ts["trang_thai"] == "Running":
            return None, "Dịch vụ bị vô hiệu hóa thì không thể để ở trạng thái Đang chạy."
    elif loai in ("msi_cai", "msi_go"):
        if not _RE_GUID.match(ts["product_id"]):
            return None, "Mã sản phẩm MSI phải dạng {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}."
        if loai == "msi_cai" and bool(ts.get("hash_alg")) != bool(ts.get("hash")):
            return None, "Muốn kiểm tra toàn vẹn thì điền cả thuật toán và giá trị băm."
        if ts.get("hash") and not re.fullmatch(r"[0-9A-Fa-f]{16,128}", ts["hash"]):
            return None, "Giá trị băm không hợp lệ."
    return ts, ""


def mo_ta(loai, ts):
    """Dong tom tat tac vu (khong lo mat khau)."""
    ten = CAC_LOAI.get(loai, ("?",))[0]
    if loai in ("winget_cai", "winget_go"):
        return f'{ten}: {ts.get("goi_id")}' + (f' {ts["phien_ban"]}' if ts.get("phien_ban") else "") + (" (giữ bản mới nhất)" if ts.get("moi_nhat") else "")
    if loai.startswith("reg_"):
        return f'{ten}: {ts.get("khoa")}' + (f' \\ {ts.get("ten")}' if ts.get("ten") else "")
    if loai.startswith("user_") or loai.startswith("nhom_"):
        return f'{ten}: {ts.get("ten")}'
    if loai.startswith("msi_"):
        return f'{ten}: {ts.get("product_id")}'
    if loai == "fw_trang_thai":
        nhan = dict(gia_tri_chon(CAC_LOAI[loai][2][0][2]))
        return (f'{"Bật" if ts.get("bat") == "bat" else "Tắt"} tường lửa: {nhan.get(ts.get("ho_so"), ts.get("ho_so"))}'
                + {"Block": ", chặn kết nối vào lạ", "Allow": ", cho phép kết nối vào lạ"}.get(ts.get("vao"), ""))
    if loai == "fw_quy_tac":
        return (f'Quy tắc tường lửa "{ts.get("ten")}": {"Cho phép" if ts.get("hanh_dong") == "Allow" else "Chặn"} '
                f'{"vào" if ts.get("chieu") == "Inbound" else "ra"} {ts.get("giao_thuc")}' + (f' cổng {ts["cong"]}' if ts.get("cong") else "")
                + (f' từ/tới {ts["dia_chi"]}' if ts.get("dia_chi") else "") + (f' chương trình {ts["chuong_trinh"]}' if ts.get("chuong_trinh") else "")
                + (" (đang tắt)" if ts.get("tat") else ""))
    if loai == "fw_xoa_quy_tac":
        return f'Xóa quy tắc tường lửa "{ts.get("ten")}"'
    if loai == "fw_nhom":
        nhan = dict(gia_tri_chon(CAC_LOAI[loai][2][0][2]))
        return f'{"Bật" if ts.get("trang_thai") == "bat" else "Tắt"} nhóm tường lửa: {nhan.get(ts.get("nhom"), ts.get("nhom"))}'
    if loai == "dv_cau_hinh":
        kd = {"Automatic": "tự động", "Manual": "thủ công", "Disabled": "vô hiệu hóa"}.get(ts.get("khoi_dong"))
        tt = {"Running": "đang chạy", "Stopped": "dừng"}.get(ts.get("trang_thai"))
        return f'Dịch vụ {ts.get("ten")}: ' + ", ".join(x for x in (f"khởi động {kd}" if kd else "", tt or "") if x)
    if loai == "powershell":
        return f'{ten} ({"chạy một lần" if ts.get("chay") != "luon" else "chạy mỗi chu kỳ"}): ' + (ts.get("script", "").strip().splitlines() or [""])[0][:60]
    return ten


# ----------------------------------------------------------------- tao kich ban PowerShell cho tung loai
_TIM_WINGET = ("$w = Get-ChildItem \"$env:ProgramFiles\\WindowsApps\\Microsoft.DesktopAppInstaller_*__8wekyb3d8bbwe\\winget.exe\" -ErrorAction SilentlyContinue "
               "| Sort-Object LastWriteTime | Select-Object -Last 1 -ExpandProperty FullName; "
               "if (-not $w) { $g = Get-Command winget -ErrorAction SilentlyContinue; if ($g) { $w = $g.Source } }; "
               "if (-not $w) { 'ST=LOI May nay chua co WinGet (App Installer)'; return }; ")
_WG_CHUNG = "--accept-source-agreements --disable-interactivity"


def _ps_winget(loai, ts):
    id_ = ts["goi_id"]
    if loai == "winget_go":
        return (_TIM_WINGET + "$ProgressPreference='SilentlyContinue'; "
                f"& $w list --id {id_} -e {_WG_CHUNG} | Out-Null; if ($LASTEXITCODE -ne 0) {{ 'ST=DA_DAT Chua cai san'; return }}; "
                f"$o = & $w uninstall --id {id_} -e --silent {_WG_CHUNG} 2>&1 | Out-String; "
                "if ($LASTEXITCODE -eq 0) { 'ST=DA_LAM Da go' } else { 'ST=LOI winget ma ' + $LASTEXITCODE + ' ' + $o.Substring([Math]::Max(0,$o.Length-300)) }")
    ver = f" --version {ts['phien_ban']}" if ts.get("phien_ban") else ""
    nang = ""
    if ts.get("moi_nhat") and not ts.get("phien_ban"):
        nang = (f"$o2 = & $w upgrade --id {id_} -e --scope machine --silent --accept-package-agreements {_WG_CHUNG} 2>&1 | Out-String; "
                "if ($LASTEXITCODE -eq 0) { 'ST=DA_LAM Da nang cap len ban moi nhat'; return }; ")
    return (_TIM_WINGET + "$ProgressPreference='SilentlyContinue'; "
            f"& $w list --id {id_} -e {_WG_CHUNG} | Out-Null; if ($LASTEXITCODE -eq 0) {{ " + (nang if nang else "") + "'ST=DA_DAT Da co san'; return }; "
            f"$o = & $w install --id {id_} -e --scope machine --silent --accept-package-agreements {_WG_CHUNG}{ver} 2>&1 | Out-String; "
            "if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq -1978335135) { 'ST=DA_LAM Da cai' } else { 'ST=LOI winget ma ' + $LASTEXITCODE + ' ' + $o.Substring([Math]::Max(0,$o.Length-300)) }")


def _ps_registry(loai, ts):
    p = chuan_khoa(ts["khoa"])
    if loai == "reg_them_khoa":
        return f"$p={_q(p)}; if (Test-Path -LiteralPath $p) {{ 'ST=DA_DAT Khoa da co' }} else {{ New-Item -Path $p -Force | Out-Null; 'ST=DA_LAM Da tao khoa' }}"
    if loai == "reg_xoa_khoa":
        return (f"$p={_q(p)}; if (-not (Test-Path -LiteralPath $p)) {{ 'ST=DA_DAT Khoa khong ton tai' }} "
                "else { Remove-Item -LiteralPath $p -Recurse -Force; 'ST=DA_LAM Da xoa khoa' }")
    if loai == "reg_xoa_gia_tri":
        return (f"$p={_q(p)}; $n={_q(ts['ten'])}; $k=Get-Item -LiteralPath $p -ErrorAction SilentlyContinue; "
                "if (-not $k -or ($k.GetValueNames() -notcontains $n)) { 'ST=DA_DAT Gia tri khong ton tai' } "
                "else { Remove-ItemProperty -LiteralPath $p -Name $n -Force; 'ST=DA_LAM Da xoa gia tri' }")
    if loai == "reg_mac_dinh":
        return (f"$p={_q(p)}; $v={_q(ts.get('du_lieu', ''))}; if (-not (Test-Path -LiteralPath $p)) {{ New-Item -Path $p -Force | Out-Null }}; "
                "$cur=(Get-Item -LiteralPath $p).GetValue(''); if ($cur -eq $v) { 'ST=DA_DAT Gia tri mac dinh da dung' } "
                "else { Set-ItemProperty -LiteralPath $p -Name '(default)' -Value $v; 'ST=DA_LAM Da dat gia tri mac dinh' }")
    # reg_dat_gia_tri
    t = ts["loai"]
    d = ts.get("du_lieu", "")
    if t in ("DWord", "QWord"):
        n = int(d or "0", 16 if ts.get("hex") else 10)
        if t == "DWord":
            if n > 0xFFFFFFFF or n < -2147483648:
                n = n & 0xFFFFFFFF
            val = f"[int]{n - 4294967296 if n > 2147483647 else n}"
        else:
            if n > 0xFFFFFFFFFFFFFFFF or n < -9223372036854775808:
                n = n & 0xFFFFFFFFFFFFFFFF
            val = f"[long]{n - 18446744073709551616 if n > 9223372036854775807 else n}"
        so_sanh = "[string]$cur -eq [string]$v"
    elif t == "MultiString":
        val = "[string[]](" + ",".join(_q(x) for x in _dong(d)) + ")" if _dong(d) else "[string[]]@()"
        so_sanh = "(@($cur) -join \"`n\") -eq (@($v) -join \"`n\")"
    elif t == "Binary":
        hx = d.replace(" ", "").replace(",", "")
        val = "[byte[]]@(" + ",".join(f"0x{hx[i:i + 2]}" for i in range(0, len(hx), 2)) + ")" if hx else "[byte[]]@()"
        so_sanh = "(($cur | ForEach-Object { '{0:x2}' -f $_ }) -join '') -eq (($v | ForEach-Object { '{0:x2}' -f $_ }) -join '')"
    else:                                              # String, ExpandString
        val = _q(d)
        so_sanh = "[string]$cur -eq [string]$v"
    if t == "String" or t == "ExpandString":
        so_sanh = "[string]$cur -eq [string]$v"
    return (f"$p={_q(p)}; $n={_q(ts['ten'])}; $t={_q(t)}; $v={val}; if (-not (Test-Path -LiteralPath $p)) {{ New-Item -Path $p -Force | Out-Null }}; "
            "$k=Get-Item -LiteralPath $p; $has=($k.GetValueNames() -contains $n); $cur=$null; $kind=$null; "
            "if ($has) { $cur=$k.GetValue($n, $null, 'DoNotExpandEnvironmentNames'); $kind=[string]$k.GetValueKind($n) }; "
            f"if ($has -and $kind -eq $t -and ({so_sanh})) {{ 'ST=DA_DAT Gia tri da dung' }} "
            "else { New-ItemProperty -LiteralPath $p -Name $n -Value $v -PropertyType $t -Force | Out-Null; 'ST=DA_LAM Da dat gia tri' }")


def _ps_user(loai, ts, giai_ma=True):
    n = ts["ten"]
    if loai == "user_xoa":
        return (f"$n={_q(n)}; if (-not (Get-LocalUser -Name $n -ErrorAction SilentlyContinue)) {{ 'ST=DA_DAT Nguoi dung khong ton tai' }} "
                "else { Remove-LocalUser -Name $n; 'ST=DA_LAM Da xoa nguoi dung' }")
    mk = DL.giai_ma(ts.get("mat_khau", "")) if (ts.get("mat_khau") and giai_ma) else ""
    cu = []
    cu.append(f"$exp = {'$true' if ts.get('tat') else '$false'}")
    ps = (f"$n={_q(n)}; $f={_q(ts.get('ho_ten', ''))}; $d={_q(ts.get('mo_ta', ''))}; $dis={'$true' if ts.get('tat') else '$false'}; "
          f"$nex={'$true' if ts.get('mk_khong_het_han') else '$false'}; $nch={'$true' if ts.get('khong_doi_mk') else '$false'}; "
          f"$must={'$true' if ts.get('phai_doi_mk') else '$false'}; $pw={_q(mk)}; "
          "$u=Get-LocalUser -Name $n -ErrorAction SilentlyContinue; "
          "if (-not $u) { $a=@{Name=$n; Description=$d}; if ($f) { $a.FullName=$f }; "
          "  if ($pw) { $a.Password=(ConvertTo-SecureString $pw -AsPlainText -Force) } else { $a.NoPassword=$true }; "
          "  if ($dis) { $a.Disabled=$true }; if ($nex) { $a.PasswordNeverExpires=$true }; if ($nch) { $a.UserMayNotChangePassword=$true }; "
          "  New-LocalUser @a | Out-Null; if ($must) { net user $n /logonpasswordchg:yes | Out-Null }; 'ST=DA_LAM Da tao nguoi dung' } "
          "else { $chg=@(); "
          "  if ($u.Enabled -eq $dis) { $chg += 'trang thai' }; "
          "  if ([bool]($u.PasswordExpires -eq $null) -ne $nex) { $chg += 'han mat khau' }; "
          "  if ([bool](-not $u.UserMayChangePassword) -ne $nch) { $chg += 'quyen doi mat khau' }; "
          "  if ($f -and $u.FullName -ne $f) { $chg += 'ho ten' }; if ($d -and $u.Description -ne $d) { $chg += 'mo ta' }; "
          "  if ($chg.Count -eq 0) { 'ST=DA_DAT Nguoi dung da dung cau hinh' } else { "
          "    $s=@{Name=$n}; if ($f) { $s.FullName=$f }; if ($d) { $s.Description=$d }; $s.PasswordNeverExpires=$nex; $s.UserMayChangePassword=(-not $nch); Set-LocalUser @s; "
          "    if ($dis) { Disable-LocalUser -Name $n } else { Enable-LocalUser -Name $n }; 'ST=DA_LAM Da cap nhat: ' + ($chg -join ', ') } }")
    return ps


def _ps_nhom(loai, ts):
    n = ts["ten"]
    tv = _dong(ts.get("thanh_vien", ""))
    arr = "@(" + ",".join(_q(x) for x in tv) + ")" if tv else "@()"
    if loai == "nhom_xoa":
        return (f"$n={_q(n)}; if (-not (Get-LocalGroup -Name $n -ErrorAction SilentlyContinue)) {{ 'ST=DA_DAT Nhom khong ton tai' }} "
                "else { Remove-LocalGroup -Name $n; 'ST=DA_LAM Da xoa nhom' }")
    if loai == "nhom_bo_user":
        return (f"$n={_q(n)}; $m={arr}; if (-not (Get-LocalGroup -Name $n -ErrorAction SilentlyContinue)) {{ 'ST=DA_DAT Nhom khong ton tai'; return }}; "
                "$cur=@(Get-LocalGroupMember -Group $n -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }); $lam=@(); "
                "foreach ($x in $m) { $hit=$cur | Where-Object { $_ -eq $x -or $_.EndsWith('\\' + $x) } | Select-Object -First 1; "
                "  if ($hit) { Remove-LocalGroupMember -Group $n -Member $hit; $lam += $x } }; "
                "if ($lam.Count -eq 0) { 'ST=DA_DAT Khong co ai can go' } else { 'ST=DA_LAM Da go: ' + ($lam -join ', ') }")
    tao = (f"$d={_q(ts.get('mo_ta', ''))}; " if loai == "nhom_them" else "$d=''; ")
    bat_buoc_ton_tai = loai == "nhom_them_user"
    return (f"$n={_q(n)}; {tao}$m={arr}; $lam=@(); "
            "if (-not (Get-LocalGroup -Name $n -ErrorAction SilentlyContinue)) { "
            + ("'ST=LOI Nhom khong ton tai'; return " if bat_buoc_ton_tai else "New-LocalGroup -Name $n -Description $d | Out-Null; $lam += 'tao nhom'") + " }; "
            "$cur=@(Get-LocalGroupMember -Group $n -ErrorAction SilentlyContinue | ForEach-Object { $_.Name }); "
            "foreach ($x in $m) { $co=$cur | Where-Object { $_ -eq $x -or $_.EndsWith('\\' + $x) } | Select-Object -First 1; "
            "  if (-not $co) { try { Add-LocalGroupMember -Group $n -Member $x -ErrorAction Stop; $lam += ('them ' + $x) } catch { 'ST=LOI Khong them duoc ' + $x + ': ' + $_.Exception.Message; return } } }; "
            "if ($lam.Count -eq 0) { 'ST=DA_DAT Nhom da dung cau hinh' } else { 'ST=DA_LAM ' + ($lam -join ', ') }")


def _ps_msi(loai, ts, url_tai=""):
    pid = ts["product_id"]
    ds = ("$ma=$null; foreach ($k in 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall','HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall') "
          f"{{ if (Test-Path -LiteralPath (Join-Path $k {_q(pid)})) {{ $ma=$true }} }}; ")
    if loai == "msi_go":
        return (ds + "if (-not $ma) { 'ST=DA_DAT Chua cai san'; return }; "
                f"$p=Start-Process msiexec.exe -ArgumentList {_q('/x ' + pid + ' /qn /norestart ' + ts.get('tham_so', ''))} -Wait -PassThru -WindowStyle Hidden; "
                "if ($p.ExitCode -in 0,3010,1641) { 'ST=DA_LAM Da go (ma ' + $p.ExitCode + ')' } else { 'ST=LOI msiexec ma ' + $p.ExitCode }")
    duong = ts["duong_dan"]
    lay = (f"$src={_q(url_tai or duong)}; $tmp=Join-Path $env:TEMP ('cs-msi-' + [guid]::NewGuid().ToString('N') + '.msi'); "
           "if ($src -match '^https?://') { $ProgressPreference='SilentlyContinue'; Invoke-WebRequest -UseBasicParsing -Uri $src -OutFile $tmp } "
           "elseif (Test-Path -LiteralPath $src) { Copy-Item -LiteralPath $src -Destination $tmp } else { 'ST=LOI Khong thay file MSI: ' + $src; return }; ")
    ha = ""
    if ts.get("hash_alg"):
        ha = (f"$h=(Get-FileHash -LiteralPath $tmp -Algorithm {ts['hash_alg']}).Hash; "
              f"if ($h -ne {_q(ts['hash'].upper())}) {{ Remove-Item -LiteralPath $tmp -Force; 'ST=LOI Gia tri bam khong khop (' + $h + ')'; return }}; ")
    lg = (" /L*v \"" + ts["log"] + "\"") if ts.get("log") else ""
    return (ds + "if ($ma) { 'ST=DA_DAT Da cai san'; return }; " + lay + ha +
            f"$ar='/i \"' + $tmp + '\" ' + {_q((ts.get('tham_so') or '/qn /norestart') + lg)}; "
            "$p=Start-Process msiexec.exe -ArgumentList $ar -Wait -PassThru -WindowStyle Hidden; Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue; "
            "if ($p.ExitCode -in 0,3010,1641) { 'ST=DA_LAM Da cai (ma ' + $p.ExitCode + ')' } else { 'ST=LOI msiexec ma ' + $p.ExitCode }")


def _ps_tuong_lua(loai, ts):
    if loai == "fw_trang_thai":
        ho = "'Domain','Private','Public'" if ts["ho_so"] == "tat_ca" else _q(ts["ho_so"])
        bat = "True" if ts["bat"] == "bat" else "False"
        vao = "" if ts.get("vao", "giu") == "giu" else (
            f"if ([string]$p.DefaultInboundAction -ne {_q(ts['vao'])}) {{ Set-NetFirewallProfile -Name $n -DefaultInboundAction {ts['vao']}; $doi += ($n + ' (ket noi vao: {ts['vao']})') }}; ")
        return ("$doi = @(); foreach ($n in @(" + ho + ")) { $p = Get-NetFirewallProfile -Name $n; "
                f"if ([string]$p.Enabled -ne '{bat}') {{ Set-NetFirewallProfile -Name $n -Enabled {bat}; $doi += $n }}; " + vao + "}; "
                "if ($doi) { 'ST=DA_LAM Da doi: ' + ($doi -join ', ') } else { 'ST=DA_DAT Da dung san' }")
    if loai == "fw_xoa_quy_tac":
        return (f"$r = @(Get-NetFirewallRule -DisplayName {_q(ts['ten'])} -ErrorAction SilentlyContinue); "
                "if (-not $r) { 'ST=DA_DAT Khong co quy tac nay'; return }; $r | Remove-NetFirewallRule; 'ST=DA_LAM Da xoa ' + $r.Count + ' quy tac'")
    if loai == "fw_nhom":
        bat = ts["trang_thai"] == "bat"
        return (f"$rs = @(Get-NetFirewallRule -Group {_q(_FW_NHOM[ts['nhom']])} -ErrorAction SilentlyContinue); "
                "if (-not $rs) { 'ST=LOI Windows khong co nhom quy tac nay'; return }; "
                f"$can = @($rs | Where-Object {{ [string]$_.Enabled -ne '{'True' if bat else 'False'}' }}); "
                "if (-not $can) { 'ST=DA_DAT Da dung san (' + $rs.Count + ' quy tac)'; return }; "
                f"$can | {'Enable' if bat else 'Disable'}-NetFirewallRule; 'ST=DA_LAM Da {'bat' if bat else 'tat'} ' + $can.Count + ' quy tac'")
    # fw_quy_tac: tao moi neu chua co; co roi ma khac cau hinh thi tao lai (so sanh chu ky)
    cong = [x for x in (ts.get("cong") or "").split(",") if x]
    dc = [x for x in (ts.get("dia_chi") or "").split(",") if x]
    vao = ts["chieu"] == "Inbound"
    th = [f"DisplayName = {_q(ts['ten'])}", f"Direction = '{ts['chieu']}'", f"Action = '{ts['hanh_dong']}'", f"Protocol = '{ts['giao_thuc']}'",
          f"Profile = '{ts['ho_so']}'", f"Enabled = '{'False' if ts.get('tat') else 'True'}'", "Group = 'Console System'"]
    if cong:
        th.append(f"{'LocalPort' if vao else 'RemotePort'} = @({','.join(_q(x) for x in cong)})")
    if dc:
        th.append(f"RemoteAddress = @({','.join(_q(x) for x in dc)})")
    if ts.get("chuong_trinh"):
        th.append(f"Program = {_q(ts['chuong_trinh'])}")
    ky = "|".join([ts["chieu"], ts["hanh_dong"], ts["giao_thuc"], ts["ho_so"], "False" if ts.get("tat") else "True", ",".join(cong) or "Any",
                   ",".join(dc) or "Any", ts.get("chuong_trinh") or "Any"])
    return ("$a = @{ " + "; ".join(th) + " }; "
            f"$r = @(Get-NetFirewallRule -DisplayName {_q(ts['ten'])} -ErrorAction SilentlyContinue); "
            "if ($r.Count -eq 1) { $x = $r[0]; $pf = $x | Get-NetFirewallPortFilter; $af = $x | Get-NetFirewallAddressFilter; $ap = $x | Get-NetFirewallApplicationFilter; "
            f"$c = @(if ({'$true' if vao else '$false'}) {{ $pf.LocalPort }} else {{ $pf.RemotePort }}) -join ','; "
            r"$ky = @([string]$x.Direction, [string]$x.Action, [string]$pf.Protocol, [string]$x.Profile, [string]$x.Enabled, $c, ((@($af.RemoteAddress) | ForEach-Object { if ($_ -match '^(.+)/(\d+\.\d+\.\d+\.\d+)$') { $n = 0; foreach ($y in ([Net.IPAddress]$matches[2]).GetAddressBytes()) { $n += ([Convert]::ToString($y, 2) -replace '0', '').Length }; $matches[1] + '/' + $n } else { $_ } }) -join ','), [string]$ap.Program) -join '|'; "
            f"if ($ky -eq {_q(ky)}) {{ 'ST=DA_DAT Quy tac da dung'; return }} }}; "
            "$moi = -not $r; if ($r) { $r | Remove-NetFirewallRule }; New-NetFirewallRule @a | Out-Null; "
            "if ($moi) { 'ST=DA_LAM Da tao quy tac' } else { 'ST=DA_LAM Da cap nhat quy tac' }")


def _ps_dich_vu(ts):
    kd = "" if ts["khoi_dong"] == "giu" else (
        f"if ([string]$s.StartType -ne '{ts['khoi_dong']}') {{ Set-Service -Name $s.Name -StartupType {ts['khoi_dong']}; $doi += 'khoi dong {ts['khoi_dong']}' }}; ")
    tt = "" if ts["trang_thai"] == "giu" else (
        f"$s.Refresh(); if ([string]$s.Status -ne '{ts['trang_thai']}') {{ "
        + ("Start-Service -Name $s.Name -ErrorAction Stop" if ts["trang_thai"] == "Running" else "Stop-Service -Name $s.Name -Force -ErrorAction Stop")
        + f"; $doi += '{'chay' if ts['trang_thai'] == 'Running' else 'dung'}' }}; ")
    return (f"$s = Get-Service -Name {_q(ts['ten'])} -ErrorAction SilentlyContinue; if (-not $s) {{ 'ST=LOI May khong co dich vu nay'; return }}; $doi = @(); "
            "try { " + kd + tt + "} catch { 'ST=LOI ' + $_.Exception.Message; return }; "
            "if ($doi) { 'ST=DA_LAM Da doi: ' + ($doi -join ', ') } else { 'ST=DA_DAT Da dung san' }")


def tao_kich_ban(loai, ts, ip=""):
    """Chuoi PowerShell thuc hien tac vu (da kiem tra dau vao o kiem_tra())."""
    if loai.startswith("fw_"):
        return _ps_tuong_lua(loai, ts)
    if loai == "dv_cau_hinh":
        return _ps_dich_vu(ts)
    if loai.startswith("winget_"):
        return _ps_winget(loai, ts)
    if loai.startswith("reg_"):
        return _ps_registry(loai, ts)
    if loai.startswith("user_"):
        return _ps_user(loai, ts)
    if loai.startswith("nhom_"):
        return _ps_nhom(loai, ts)
    if loai.startswith("msi_"):
        url = ""
        d = ts.get("duong_dan", "")
        if loai == "msi_cai" and d.lower().endswith(".msi") and not re.match(r"^(https?://|[A-Za-z]:\\|\\\\)", d):
            import os
            duong = os.path.join(_DD.APPS_DIR, os.path.basename(d))
            if os.path.isfile(duong):
                url = DC.url_tai(ip, duong)
        return _ps_msi(loai, ts, url)
    if loai == "powershell":
        return ts["script"]
    return ""


def chay(c, ip, loai, ts):
    """Chay 1 tac vu tren may da ket noi. Tra ve (trang_thai, thong_diep): trang_thai = 'da_dat' | 'da_lam' | 'loi'."""
    kb = tao_kich_ban(loai, ts, ip)
    out, err = DC._chay_ps(c, kb)
    if loai == "powershell":
        if err:
            return "loi", f"Script báo lỗi: {err}"
        return "da_lam", ("Chạy xong. " + out.strip()[:300]).strip()
    m = re.search(r"ST=(DA_DAT|DA_LAM|LOI)\s*(.*)", out)
    if not m:
        return "loi", ("Không nhận được kết quả từ máy đích. " + (err or out.strip())[:300]).strip()
    tt = {"DA_DAT": "da_dat", "DA_LAM": "da_lam", "LOI": "loi"}[m.group(1)]
    return tt, (m.group(2).strip() or ("Đã đúng sẵn" if tt == "da_dat" else "Xong"))[:400]


def moi_id():
    return uuid.uuid4().hex[:10]
