"""Chay tren Console: sinh script tung loai tac vu Profile (uem_buoc) roi chay 2 lan tren may thu qua agent (cli/chay)."""
import json, sys, urllib.request
sys.path.insert(0, "/opt/console-system/current")
from consolesystem.features.uem import uem_buoc as B
MID = sys.argv[1]
CA = [
 ("winget_cai", {"goi_id": "7zip.7zip"}),
 ("reg_them_khoa", {"khoa": r"HKLM\SOFTWARE\CS-Thu"}),
 ("reg_dat_gia_tri", {"khoa": r"HKLM\SOFTWARE\CS-Thu", "ten": "A", "loai": "DWord", "du_lieu": "5"}),
 ("reg_dat_gia_tri", {"khoa": r"HKLM\SOFTWARE\CS-Thu", "ten": "S", "loai": "String", "du_lieu": "xin chào"}),
 ("reg_dat_gia_tri", {"khoa": r"HKLM\SOFTWARE\CS-Thu", "ten": "M", "loai": "MultiString", "du_lieu": "a\nb"}),
 ("reg_mac_dinh", {"khoa": r"HKLM\SOFTWARE\CS-Thu", "du_lieu": "mac dinh"}),
 ("reg_xoa_gia_tri", {"khoa": r"HKLM\SOFTWARE\CS-Thu", "ten": "A"}),
 ("reg_xoa_khoa", {"khoa": r"HKLM\SOFTWARE\CS-Thu"}),
 ("user_them", {"ten": "csthu", "ho_ten": "CS Thu", "mat_khau": "MatKhau#Thu12345"}),
 ("nhom_them", {"ten": "CS-Nhom-Thu", "mo_ta": "thu", "thanh_vien": ""}),
 ("nhom_them_user", {"ten": "CS-Nhom-Thu", "thanh_vien": "csthu"}),
 ("nhom_bo_user", {"ten": "CS-Nhom-Thu", "thanh_vien": "csthu"}),
 ("nhom_xoa", {"ten": "CS-Nhom-Thu"}),
 ("user_xoa", {"ten": "csthu"}),
 ("powershell", {"script": "'ok ' + $env:COMPUTERNAME", "chay": "mot_lan"}),
 ("fw_trang_thai", {"ho_so": "tat_ca", "bat": "bat", "vao": "giu"}),
 ("fw_nhom", {"nhom": "rdp", "trang_thai": "bat"}),
 ("dv_cau_hinh", {"ten": "RemoteRegistry", "khoi_dong": "Disabled", "trang_thai": "Stopped"}),
]
def chay(s):
    r = urllib.request.Request("http://127.0.0.1:5000/uem/may/%s/cli/chay" % MID, data=json.dumps({"loai": "ps", "lenh": s}).encode(),
                               headers={"X-ConsolePi-Local": "1", "Content-Type": "application/json"})
    j = json.load(urllib.request.urlopen(r, timeout=600))
    return (j.get("out") or j.get("loi") or "").strip().replace("\r\n", " ")[:110]
for loai, f in CA:
    ts, loi = B.kiem_tra(loai, f)
    if loi:
        print(loai, "KIEM TRA LOI", loi); continue
    if loai == "user_them":
        sc = B._ps_user(loai, ts, giai_ma=True)
    else:
        sc = B.tao_kich_ban(loai, ts)
    print("%-16s | %s || %s" % (loai, chay(sc), chay(sc)), flush=True)
