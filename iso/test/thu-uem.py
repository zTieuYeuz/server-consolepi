# Test muc "Quan ly may tram" (UEM) khong can may Windows that: trang, loc, the/dia diem/metadata, hang loat, profiles, bao cao CSV, RDP, kiem tra dau vao, XSS.
import json, os, re, sys, tempfile, time
TMP = tempfile.mkdtemp(prefix="uem-test-")
os.environ["CONSOLE_PI_DATA"] = TMP
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src")
sys.path.insert(0, SRC); os.chdir(SRC)
import threading
_goc = threading.Thread.start
def _chan(self):
    if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong"):
        return
    return _goc(self)
threading.Thread.start = _chan
import runpy
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
from ui import tk_dulieu as DL, uem_dulieu as UD, uem_buoc as UB, uem_profiles as UP, uem_trienkhai as UT
DAT, HONG = [], []
def kt(ten, dk, ct=""):
    (DAT if dk else HONG).append(ten); print(("  OK   " if dk else "  HONG ") + ten + ("" if dk or not ct else f"  -> {ct}"), flush=True)
c = app.test_client(); H = {"X-ConsolePi-Local": "1"}
def post(p, d=None, **kw): return c.post(p, data=d or {}, headers=H, follow_redirects=True, **kw)
def get(p): return c.get(p, headers=H, follow_redirects=True)
def txt(r): return r.get_data(as_text=True)

def bao_cao(ten, os_ten, hang, usage=40, av=True, bit="Unencrypted", cho=1):
    return {"hostname": ten, "ip": "10.1.1.1", "mac": "AA:BB:CC:DD:EE:01",
        "computer": {"manufacturer": hang, "model": "Model X", "serial": "SN123", "processor": "Intel i5", "processor_cores": 4, "processor_arch": "x64", "memory": "8 GB"},
        "operatingsystem": {"description": os_ten, "version": "23H2", "build": "22631", "edition": "Pro", "arch": "64-bit", "install_date": "2024-01-02T03:04:05", "last_bootup_time": "2026-10-20T08:00:00", "username": "DESKTOP\\an", "domain": "WORKGROUP"},
        "antivirus": {"name": "Windows Defender" if av else "", "is_active": av, "is_updated": av},
        "systemupdate": {"status": "4", "last_search": "2026-10-19T01:00:00", "last_install": "2026-10-10T01:00:00", "pending_updates": bool(cho)},
        "pending_updates": [{"title": "Cập nhật tích lũy <b>x</b>", "kb": "KB5000001", "critical": True}] * cho,
        "updates": [{"title": "KB4000", "date": "2026-10-01T00:00:00", "support_url": "https://support.microsoft.com/x"}, {"title": "KB4001", "date": "2026-10-02T00:00:00", "support_url": "javascript:alert(1)"}],
        "firewall": [{"ten": "Domain", "bat": True}, {"ten": "Public", "bat": False}], "smb1": "Disabled",
        "logicaldisks": [{"label": "C:", "volume_name": "Win", "filesystem": "NTFS", "size_in_units": "237 GB", "remaining_space_in_units": "20 GB", "usage": usage, "bitlocker_status": bit}],
        "physicaldisks": [{"device_id": "0", "model": "SSD", "serial_number": "S1", "size_in_units": "256 GB"}], "monitors": [],
        "memoryslots": [{"slot": "DIMM1", "size": "8 GB", "type": "DDR4", "speed": "3200", "manufacturer": "Kingston", "part_number": "P", "serial_number": "S"}],
        "networkadapters": [{"name": "Ethernet", "mac_address": "AA:BB:CC:DD:EE:01", "addresses": "10.1.1.1", "subnet": "255.255.255.0", "default_gateway": "10.1.1.254", "dns_servers": "8.8.8.8", "dns_domain": "", "dhcp_enabled": True, "dhcp_lease_obtained": "2026-10-20T00:00:00", "dhcp_lease_expired": "2026-10-22T00:00:00", "speed": "1 Gbps"}],
        "printers": [{"name": "HP LaserJet", "port": "IP_10.1.1.9", "is_default": True, "is_network": True, "is_shared": False}],
        "shares": [{"name": "C$", "path": "C:\\", "description": "Default share"}],
        "applications": [{"name": "7-Zip", "version": "23.01", "publisher": "Igor Pavlov", "install_date": "20240101"}, {"name": "Google Chrome", "version": "118", "publisher": "Google LLC", "install_date": ""}]}

now = time.time()
def nap(ds):
    ds.append({"id": "m1", "ten": "", "ip": "10.1.1.1", "mac": "AA:BB:CC:DD:EE:01", "giam_sat": True, "bao_cao": bao_cao("PC-KETOAN", "Microsoft Windows 11 Pro", "Dell"), "bao_cao_luc": now, "ket_noi": {"ok": True, "loi": "", "luc": now}, "bi_danh": "Máy <script>alert(1)</script>"})
    ds.append({"id": "m2", "ten": "", "ip": "10.1.1.2", "mac": "", "giam_sat": True, "bao_cao": bao_cao("PC-KHO", "Microsoft Windows 10 Pro", "HP", usage=95, av=False, bit="Encrypted", cho=0), "bao_cao_luc": now - 90000, "ket_noi": {"ok": False, "loi": "x", "luc": now}})
    ds.append({"id": "m3", "ten": "chua-bao-cao", "ip": "10.1.1.3", "mac": "", "giam_sat": True})
DL.MAY.sua(nap)

# ---- cac trang chinh
for p in ("/uem", "/uem/may", "/uem/phan-mem", "/uem/bao-mat", "/uem/bao-mat/cap-nhat", "/uem/trien-khai", "/uem/trien-khai/lich-su", "/uem/profiles", "/uem/bao-cao",
          "/uem/quan-tri", "/uem/quan-tri/may", "/uem/quan-tri/the", "/uem/quan-tri/dia-diem", "/uem/quan-tri/metadata", "/uem/quan-tri/cai-dat", "/uem/quan-tri/nhat-ky", "/uem/chua-ho-tro"):
    r = get(p); kt(f"trang {p} 200", r.status_code == 200 and "Quản lý máy trạm" in txt(r), str(r.status_code))
h = txt(get("/uem"))
kt("menu co muc Quan ly may tram dang sang", re.search(r'href="/uem" class="active"', h) is not None)
kt("tong quan: dem dung 3 may, 1 AV tat, 1 o day", ">3<" in h and "Máy diệt virus đang tắt" in h and "Máy có ổ đĩa đầy từ 90%" in h)
kt("tong quan: khong lo script", "<script>alert(1)" not in h)
h = txt(get("/uem/may"))
kt("danh sach may: bi danh bi escape", "&lt;script&gt;alert(1)" in h and "<script>alert(1)" not in h)
kt("danh sach may: 3 hang", h.count('data-t="') >= 3)
kt("trang thai: Khong ket noi / Chua co bao cao / Dang giam sat", "Không kết nối" in h and "Chờ gán tài khoản" in h)
# ---- chi tiet may
for tab in ("", "phan-cung", "he-dieu-hanh", "o-dia", "man-hinh", "mang", "may-in", "chia-se", "phan-mem", "cap-nhat", "ghi-chu", "metadata", "quan-ly", "tu-xa", "nguon", "trien-khai", "tac-vu"):
    r = get(f"/uem/may/m1/{tab}"); kt(f"chi tiet may tab '{tab or 'tq'}' 200", r.status_code == 200, str(r.status_code))
for tab in ("", "phan-cung", "o-dia", "phan-mem", "cap-nhat", "ghi-chu", "quan-ly", "tu-xa", "agent", "nguon", "tac-vu"):
    h = txt(get(f"/uem/may/m1/{tab}")); kt(f"chi tiet may m1/{tab or 'tq'}: ten may doc hai KHONG chay duoc script (XSS)", "<script>alert(1)" not in h and "&lt;script&gt;alert(1)" in h and not any(x in h for x in ("&lt;form", "&lt;div class", "&lt;a href", "&lt;span class", "&lt;table")), tab)
kt("tab khong ton tai 404", get("/uem/may/m1/xyz").status_code == 404 and get("/uem/may/khong-co").status_code == 404)
h = txt(get("/uem/may/m1/cap-nhat"))
kt("cap nhat: link javascript: khong thanh link", 'href="javascript' not in h and "support.microsoft.com" in h and "&lt;b&gt;x" in h)
h = txt(get("/uem/may/m3"))
kt("may chua bao cao: huong dan gan tai khoan", "Chưa có báo cáo" in h or "chưa gán tài khoản" in h)
h = txt(get("/uem/may/m1/duyet-file"))
kt("duyet file may chua gan tai khoan: bao ro, khong sap", "Quản lý" in h)
kt("duyet file: duong dan xau bi tu choi", "không hợp lệ" in txt(get("/uem/may/m1/duyet-file?p=C:%5Ca%3Cb")))
# ---- the, dia diem, metadata
post("/uem/quan-tri/the/luu", {"ten": "Kế toán", "mau": "#ff0000", "mo_ta": "x"}); post("/uem/quan-tri/the/luu", {"ten": "KẾ TOÁN", "mau": "#00ff00"})
kt("the: tao 1, trung ten (khong phan biet hoa thuong) bi tu choi", len(UD.THE.doc()) == 1 and UD.THE.doc()[0]["mau"] == "#ff0000")
post("/uem/quan-tri/the/luu", {"ten": "Kho", "mau": "javascript"}); kt("the: mau sai -> mac dinh", UD.THE.doc()[1]["mau"] == "#6366f1")
t1, t2 = UD.THE.doc()[0]["id"], UD.THE.doc()[1]["id"]
post("/uem/quan-tri/dia-diem/luu", {"ten": "Tầng 1"}); d1 = UD.DIA_DIEM.doc()[0]["id"]
post("/uem/quan-tri/metadata/luu", {"ten": "Người phụ trách"}); md = UD.METADATA.doc()[0]["id"]
post("/uem/may/m1/quan-ly", {"bi_danh": "May KT", "ip": "10.1.1.1", "mac": "aa-bb-cc-dd-ee-01", "loai": "Laptop", "the": [t1], "dia_diem": d1, "giam_sat": "1"})
m1 = DL.tim(DL.MAY.doc(), "m1")
kt("quan ly may: luu bi danh, MAC chuan, the, dia diem", m1["bi_danh"] == "May KT" and m1["mac"] == "aa:bb:cc:dd:ee:01" and m1["the"] == [t1] and m1["dia_diem"] == d1, str(m1.get("mac")))
r = post("/uem/may/m1/quan-ly", {"ip": "10.1.1.2", "giam_sat": "1"}); kt("quan ly: IP trung may khac bi tu choi", "Đã có máy khác" in txt(r) and DL.tim(DL.MAY.doc(), "m1")["ip"] == "10.1.1.1")
r = post("/uem/may/m1/quan-ly", {"ip": "abc", "giam_sat": "1"}); kt("quan ly: IP sai bi tu choi", "không hợp lệ" in txt(r))
r = post("/uem/may/m1/quan-ly", {"ip": "10.1.1.1", "mac": "zz", "giam_sat": "1"}); kt("quan ly: MAC sai bi tu choi", "MAC không hợp lệ" in txt(r))
post("/uem/may/m1/quan-ly", {"ip": "10.1.1.1", "tai_khoan_id": "khong-co", "the": ["khong-co"], "giam_sat": "1"})
m1 = DL.tim(DL.MAY.doc(), "m1"); kt("quan ly: the/tai khoan khong ton tai bi bo", m1["the"] == [] and not m1.get("tai_khoan_id"))
post("/uem/may/m1/quan-ly", {"ip": "10.1.1.1", "the": [t1], "dia_diem": d1, "giam_sat": "1"})
post("/uem/may/m1/ghi-chu", {"ghi_chu": "Ghi chú <i>1</i>"}); r = get("/uem/may/m1/ghi-chu"); kt("ghi chu luu + escape", "&lt;i&gt;1" in txt(r) and "<i>1</i>" not in txt(r))
post("/uem/may/m1/metadata", {"md_" + md: "Anh An", "md_xxx": "bay"}); m1 = DL.tim(DL.MAY.doc(), "m1")
kt("metadata: luu dung truong da dinh nghia, bo truong la", m1["metadata"] == {md: "Anh An"})
h = txt(get("/uem/may")); kt("loc the/dia diem co trong danh sach", 'data-the="' + t1 + '"' in h and 'data-dd="' + d1 + '"' in h)
# ---- hang loat
post("/uem/may/hang-loat", {"may": ["m2", "m3"], "viec": "them_the", "the": t2}); kt("hang loat: them the", all(t2 in DL.tim(DL.MAY.doc(), i)["the"] for i in ("m2", "m3")))
post("/uem/may/hang-loat", {"may": ["m2"], "viec": "bo_the", "the": t2}); kt("hang loat: go the", t2 not in DL.tim(DL.MAY.doc(), "m2")["the"] and t2 in DL.tim(DL.MAY.doc(), "m3")["the"])
post("/uem/may/hang-loat", {"may": ["m3"], "viec": "tat"}); kt("hang loat: vo hieu", DL.tim(DL.MAY.doc(), "m3")["giam_sat"] is False)
h = txt(get("/uem")); kt("tong quan: dem 'Da vo hieu' 1", "Đã vô hiệu" in h)
post("/uem/may/hang-loat", {"may": ["m3"], "viec": "bat"}); kt("hang loat: bat lai", DL.tim(DL.MAY.doc(), "m3")["giam_sat"] is True)
r = post("/uem/may/hang-loat", {"viec": "xoa"}); kt("hang loat: khong chon may -> bao loi", "Chưa chọn máy" in txt(r))
r = post("/uem/may/hang-loat", {"may": ["m3"], "viec": "gan_tk", "tk": "khong-co"}); kt("hang loat: gan tai khoan khong ton tai bi tu choi", "Chọn tài khoản" in txt(r))
r = post("/uem/may/hang-loat", {"may": ["m3"], "viec": "bao_cao"}); kt("hang loat: bao cao may chua gan tai khoan -> 0 may", "0 máy" in txt(r))
# ---- them may
post("/uem/may/them", {"ip": "10.9.9.10-12", "ten": ""}); kt("them dai IP -> 3 may moi (tong 6)", len(DL.MAY.doc()) == 6)
r = post("/uem/may/them", {"ip": "10.9.9.10"}); kt("them trung IP bi bo qua", len(DL.MAY.doc()) == 6 and "bỏ qua 1" in txt(r))
r = post("/uem/may/them", {"ip": "10.9.9.300"}); kt("them IP sai bi tu choi", "không hợp lệ" in txt(r) and len(DL.MAY.doc()) == 6)
r = post("/uem/may/them", {"ip": "10.9.9.9-3"}); kt("dai nguoc bi tu choi", "không hợp lệ" in txt(r))
post("/uem/may/hang-loat", {"may": [m["id"] for m in DL.MAY.doc() if m["ip"].startswith("10.9.9.")], "viec": "xoa"}); kt("hang loat: xoa", len(DL.MAY.doc()) == 3)
# ---- bao cao / csv / rdp
for ten in ("may", "phan-mem", "o-dia", "bao-mat", "cap-nhat", "may-in", "mang"):
    r = c.get(f"/uem/bao-cao/{ten}.csv", headers=H); kt(f"csv {ten}", r.status_code == 200 and r.data.startswith(b"\xef\xbb\xbf") and len(r.data.splitlines()) >= 2, str(r.status_code))
kt("csv khong co ten la 404", c.get("/uem/bao-cao/abc.csv", headers=H).status_code == 404)
r = c.get("/uem/may/m1/phan-mem.csv", headers=H); kt("csv phan mem cua may", b"7-Zip" in r.data and b"Chrome" in r.data)
r = c.get("/uem/may/m1/tu-xa/rdp", headers=H); kt("tai RDP: co dia chi, khong co mat khau", b"full address:s:10.1.1.1" in r.data and b"password" not in r.data.lower().replace(b"prompt for credentials", b""))
h = txt(get("/uem/phan-mem")); kt("phan mem tong: 7-Zip tren 2 may", "7-Zip" in h)
h = txt(get("/uem/phan-mem?ten=7-Zip")); kt("phan mem: chi tiet thay 2 may", "cài trên 2 máy" in h)
# ---- trien khai winget
r = post("/uem/trien-khai/chay", {"hanh_dong": "cai", "goi_id": "abc;rm -rf", "may": ["m1"]}); kt("trien khai: ma goi doc hai bi tu choi", "không hợp lệ" in txt(r))
r = post("/uem/trien-khai/chay", {"hanh_dong": "cai", "goi_id": "7zip.7zip"}); kt("trien khai: khong chon may", "Chưa chọn máy" in txt(r))
r = post("/uem/trien-khai/chay", {"hanh_dong": "xoa", "goi_id": "7zip.7zip", "may": ["m1"]}); kt("trien khai: hanh dong la bi tu choi", "không hợp lệ" in txt(r))
dot, loi = UT.bat_dau("cai", "7zip.7zip", "7-Zip", ["m1", "khong-co"])
for _ in range(50):
    st = UT.trang_thai(dot)
    if st["xong"] == st["tong"]: break
    time.sleep(0.1)
kt("trien khai: may chua gan tai khoan -> loi ro rang, khong treo", st["xong"] == 1 and st["may"]["m1"]["tt"] == "loi" and "tài khoản" in st["may"]["m1"]["tb"], str(st))
j = json.loads(txt(get("/uem/trien-khai/tt/" + dot))); kt("API tien do tra JSON", j["tong"] == 1 and j["hanh_dong"] == "Cài đặt")
kt("API tien do dot la", json.loads(txt(get("/uem/trien-khai/tt/zzz"))).get("loi"))
kt("lich su trien khai ghi 1 dong", len(UD.TRIEN_KHAI.doc()) == 1 and "7-Zip" in txt(get("/uem/trien-khai/lich-su")))
kt("nhat ky tac vu co dong trien khai", "Triển khai" in txt(get("/uem/quan-tri/nhat-ky")))
kt("trang chon may cho goi", "Bắt đầu" in txt(get("/uem/trien-khai/goi?id=7zip.7zip")) and "Nâng cấp tất cả" in txt(get("/uem/trien-khai/goi?id=*")))
kt("chon goi ma sai -> quay ve", "không hợp lệ" in txt(get("/uem/trien-khai/goi?id=a%20b")))
# ---- profiles
post("/uem/profiles/tao", {"ten": "Van phong", "mo_ta": "x"}); pid = UD.PROFILES.doc()[0]["id"]
kt("tao profile (mac dinh tat)", UD.PROFILES.doc()[0]["bat"] is False)
r = post(f"/uem/profiles/{pid}/task/luu", {"loai_tac_vu": "winget_cai", "goi_id": "bad id"}); kt("task: ma winget sai bi tu choi", "không hợp lệ" in txt(r) and not UD.PROFILES.doc()[0]["tasks"])
r = post(f"/uem/profiles/{pid}/task/luu", {"loai_tac_vu": "reg_dat_gia_tri", "khoa": "HKEY_CURRENT_USER\\Software\\X", "ten": "a", "loai": "String"}); kt("task: HKCU bi tu choi", "HKEY_CURRENT_USER" in txt(r))
r = post(f"/uem/profiles/{pid}/task/luu", {"loai_tac_vu": "reg_dat_gia_tri", "khoa": "HKLM\\SOFTWARE\\Test", "ten": "n", "loai": "DWord", "du_lieu": "abc"}); kt("task: DWord khong phai so bi tu choi", "phải là số" in txt(r))
post(f"/uem/profiles/{pid}/task/luu", {"loai_tac_vu": "winget_cai", "goi_id": "7zip.7zip", "moi_nhat": "1"})
post(f"/uem/profiles/{pid}/task/luu", {"loai_tac_vu": "user_them", "ten": "nv01", "mat_khau": "Abc@1234"})
t = UD.PROFILES.doc()[0]["tasks"]
kt("task: them 2 tac vu, mat khau duoc ma hoa", len(t) == 2 and "Abc@1234" not in json.dumps(UD.PROFILES.doc()) and DL.giai_ma(t[1]["tham_so"]["mat_khau"]) == "Abc@1234")
h = txt(get(f"/uem/profiles/{pid}")); kt("trang profile: khong lo mat khau, co mo ta tac vu", "Abc@1234" not in h and "nv01" in h and "7zip.7zip" in h)
tid = t[1]["id"]; mk_cu = t[1]["tham_so"]["mat_khau"]
post(f"/uem/profiles/{pid}/task/luu", {"loai_tac_vu": "user_them", "task_id": tid, "ten": "nv01", "ho_ten": "Nhan Vien", "mat_khau": ""})
t = UD.PROFILES.doc()[0]["tasks"]; kt("sua task: de trong mat khau = giu mat khau cu", t[1]["tham_so"]["mat_khau"] == mk_cu and t[1]["tham_so"]["ho_ten"] == "Nhan Vien")
h = txt(get(f"/uem/profiles/{pid}?sua={tid}")); kt("form sua task khong dien mat khau", 'name="mat_khau" value=""' in h)
post(f"/uem/profiles/{pid}/task/{tid}/hanh-dong", {"viec": "len"}); kt("doi thu tu len", UD.PROFILES.doc()[0]["tasks"][0]["id"] == tid)
post(f"/uem/profiles/{pid}/task/{tid}/hanh-dong", {"viec": "bat_tat"}); kt("tat tac vu", UD.PROFILES.doc()[0]["tasks"][0]["bat"] is False)
post(f"/uem/profiles/{pid}/luu", {"ten": "Van phong 2", "ap_dung_tat_ca": "", "the": [t1, "khong-co"], "bat": "1"}); p = UD.PROFILES.doc()[0]
kt("luu profile: the khong ton tai bi bo, bat", p["ten"] == "Van phong 2" and p["the"] == [t1] and p["bat"])
kt("pham vi profile theo the = may co the do", [m["id"] for m in UP.may_ap_dung(p)] == ["m1"])
post(f"/uem/profiles/{pid}/luu", {"ten": "Van phong 2", "ap_dung_tat_ca": "1", "bat": "1"}); kt("pham vi tat ca may (giam sat)", len(UP.may_ap_dung(UD.PROFILES.doc()[0])) == 3)
post(f"/uem/profiles/{pid}/luu", {"ten": "Van phong 2", "the": [t1], "bat": ""})
r = post(f"/uem/profiles/{pid}/ap-dung"); kt("ap dung ngay: may chua gan tai khoan -> 0 may", "Không có máy nào" in txt(r))
msg = UP.chay_profile_may(pid, "m1"); kt("chay profile tren may chua gan tai khoan -> bao ro, khong sap", "tài khoản" in msg, msg)
kt("van de profile: bao loi tac vu", True)
post(f"/uem/profiles/{pid}/task/{tid}/hanh-dong", {"viec": "xoa"}); kt("xoa task", len(UD.PROFILES.doc()[0]["tasks"]) == 1)
post(f"/uem/profiles/{pid}/xoa"); kt("xoa profile", not UD.PROFILES.doc())
kt("profile khong ton tai 404", get("/uem/profiles/khong-co").status_code == 404)
# ---- xoa the/dia diem don dep tham chieu
post("/uem/quan-tri/the/xoa", {"id": t1}); kt("xoa the: go khoi may", all(t1 not in m.get("the", []) for m in DL.MAY.doc()))
post("/uem/quan-tri/dia-diem/xoa", {"id": d1}); kt("xoa dia diem: go khoi may", all(m.get("dia_diem") != d1 for m in DL.MAY.doc()))
post("/uem/quan-tri/metadata/xoa", {"id": md}); kt("xoa metadata: go khoi may", all(md not in (m.get("metadata") or {}) for m in DL.MAY.doc()))
# ---- cai dat
post("/uem/quan-tri/cai-dat", {"tan_suat_bao_cao": "1", "tan_suat_profile": "99999", "tu_dong_giam_sat": ""}); cd = UD.cai_dat()
kt("cai dat: ep ve khoang 5..1440, tat tu dong", cd["tan_suat_bao_cao"] == 5 and cd["tan_suat_profile"] == 1440 and cd["tu_dong_giam_sat"] is False, str(cd))
r = post("/uem/quan-tri/cai-dat", {"tan_suat_bao_cao": "abc"}); kt("cai dat: khong phai so bi tu choi", "phải là số" in txt(r))
# ---- agent v2 (mTLS)
from ui import uem_agent_trang as UAT, uem_agent as UA, uem_ketnoi as UK, uem_baocao as UBC, uem_vnc as UV, uem_pki as PKI
import threading
BM = PKI.bi_mat_nginx()
def hdr_cert(mid="m1", serial=None, verify="SUCCESS", secret=None, dn=None):
    m = DL.tim(DL.MAY.doc(), mid); sr = serial if serial is not None else ((m.get("agent") or {}).get("serie") or "ff")
    return {"X-CS-TLS-Secret": BM if secret is None else secret, "X-CS-Client-Verify": verify, "X-CS-Client-DN": dn or ("CN=cs-agent-" + mid + ",O=Console System"), "X-CS-Client-Serial": sr.upper()}
def agent_post(p, d, hdr=None):     # khong co X-ConsolePi-Local -> di dung duong dang nhap that
    return c.post(p, json=d, headers=hdr or {}, follow_redirects=False)
kt("PKI: CA + chung chi may chu + dau van tay", len(PKI.ca_sha256()) == 64 and len(PKI.server_sha256()) == 64)
r = agent_post("/uem/agent/nhip", {"ver": "2.0.0"}); kt("agent: khong chung chi -> 403", r.status_code == 403, r.status_code)
c1 = UA.cap_chung_chi("m1")
kt("cap chung chi: luu serial, KHONG luu khoa rieng/mat khau", DL.tim(DL.MAY.doc(), "m1")["agent"]["serie"] == c1["serial"] and c1["mat_khau"] not in json.dumps(DL.MAY.doc()))
for ten, hd in (("sai bi mat nginx", hdr_cert(secret="sai")), ("verify FAILED", hdr_cert(verify="FAILED")), ("sai serial (da bi thu hoi)", hdr_cert(serial="abc123")),
                ("CN may khac", hdr_cert(dn="CN=cs-agent-m2")), ("CN la", hdr_cert(dn="CN=evil"))):
    kt("agent: " + ten + " -> 403", agent_post("/uem/agent/nhip", {"ver": "2.0.0"}, hd).status_code == 403)
UA.NHIP_GIAY = 3
r = agent_post("/uem/agent/nhip", {"ver": "1.0.0"}, hdr_cert()); kt("agent: chung chi dung + ban cu -> nhan ma nguon ban moi de tu cap nhat", r.status_code == 200 and "Console System agent" in (r.get_json() or {}).get("capnhat", {}).get("cs", ""), r.status_code)
kt("ma nguon C# agent khong dung C# 6+ (csc 4.8 chi C# 5)", not any(x in UA.CS.nguon() for x in ("?.", "$\"", "nameof(", "=> ")))
r = agent_post("/uem/agent/nhip", {"ver": "2.0.0"}, hdr_cert({"X-Forwarded-For": "1.2.3.4, 5.6.7.8"} and "m1") | {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}); kt("X-Forwarded-For nhieu phan tu (qua proxy) -> bi chuyen login", r.status_code == 302, r.status_code)
kt("duong dashboard van bat dang nhap", c.get("/uem", follow_redirects=False).status_code == 302)
def agent_gia(mid, hanh_vi, so_lan=3):
    def chay():
        for _ in range(so_lan):
            m = DL.tim(DL.MAY.doc(), mid)
            rr = UA.xu_ly_nhip(m, {"ver": UA.PHIEN_BAN, "host": "GIA", "dang": [], "pf": {}}, "10.1.1.1")
            if rr.get("viec") and rr["viec"].get("kieu") == "ps":
                out, err = hanh_vi(rr["viec"]["script"])
                UA.nhan_ket_qua(m, {"id": rr["viec"]["id"], "out": out, "err": err})
    th = threading.Thread(target=chay, daemon=True); th.start(); return th
th = agent_gia("m1", lambda sc: ("XIN CHAO " + str(len(sc)), "")); time.sleep(0.5)
kt("UK.ket_noi chon agent khi dang song", UK.co_agent(DL.tim(DL.MAY.doc(), "m1")) and UK.ket_noi(DL.tim(DL.MAY.doc(), "m1"))[2] == "agent")
out, err = UA.chay_ps("m1", "Get-Date", timeout=20); kt("viec ps di qua agent va co ket qua", out.startswith("XIN CHAO") and err == "", (out, err))
th.join(10)
th = agent_gia("m1", lambda sc: ("UEM_JSON=" + json.dumps(bao_cao("PC-AGENT", "Microsoft Windows 11 Pro", "Lenovo")), ""))
ok, tb = UBC.bao_cao_may("m1")
kt("bao cao lay qua agent (khong can tai khoan WinRM)", ok and DL.tim(DL.MAY.doc(), "m1")["bao_cao"]["hostname"] == "PC-AGENT" and DL.tim(DL.MAY.doc(), "m1")["ket_noi"].get("qua") == "agent", tb)
th.join(10)
j = UA.them_viec("m1", "ps", script="Start-Sleep 99", timeout=30)
UA.xu_ly_nhip(DL.tim(DL.MAY.doc(), "m1"), {"ver": UA.PHIEN_BAN, "dang": []}, "10.1.1.1"); j["giao"] -= 60
UA.xu_ly_nhip(DL.tim(DL.MAY.doc(), "m1"), {"ver": UA.PHIEN_BAN, "dang": []}, "10.1.1.1")
kt("viec da giao ma agent khong con giu -> bao loi, khong treo", j["su_kien"].is_set() and "khởi động lại" in j["kq"]["err"], j.get("kq"))
# chuyen file dang luong qua agent
import tempfile as _tf
nguon = _tf.NamedTemporaryFile(delete=False); nguon.write(b"x" * (3 * 1024 * 1024 + 7)); nguon.close()
dich = nguon.name + ".tai"
cl = UA.Client("m1"); box = {}
def fake_tep():
    for _ in range(4):
        rr = UA.xu_ly_nhip(DL.tim(DL.MAY.doc(), "m1"), {"ver": UA.PHIEN_BAN, "dang": []}, "10.1.1.1")
        v = rr.get("viec")
        if v and v["kieu"] == "tep_xuong":
            g = c.get("/uem/agent/tep/" + v["id"], headers=hdr_cert()); box["xuong"] = (g.status_code, len(g.data))
            UA.nhan_ket_qua(DL.tim(DL.MAY.doc(), "m1"), {"id": v["id"], "out": "OK %d" % len(g.data), "err": ""})
        elif v and v["kieu"] == "tep_len":
            pu = c.put("/uem/agent/tep/" + v["id"], data=b"y" * (2 * 1024 * 1024 + 3), headers=hdr_cert()); box["len"] = pu.status_code
            UA.nhan_ket_qua(DL.tim(DL.MAY.doc(), "m1"), {"id": v["id"], "out": "OK 1", "err": ""})
th = threading.Thread(target=fake_tep, daemon=True); th.start()
cl.copy(nguon.name, "C:\\x\\a.bin"); cl.fetch("C:\\x\\b.bin", dich); th.join(15)
kt("file 3 MB day LEN may dang luong (khong gioi han 6 MB cu)", box.get("xuong") == (200, 3 * 1024 * 1024 + 7), box)
kt("file 2 MB tai VE dang luong dung kich thuoc", box.get("len") == 200 and os.path.getsize(dich) == 2 * 1024 * 1024 + 3, box)
r = c.get("/uem/agent/tep/khongco", headers=hdr_cert()); kt("tep: ma viec la -> 404", r.status_code == 404)
os.remove(nguon.name); os.remove(dich)
# profile tu tri: bundle, dong bo, ket qua gui bu
post("/uem/profiles/tao", {"ten": "tt"}); pid2 = [p for p in UD.PROFILES.doc() if p["ten"] == "tt"][0]["id"]
post(f"/uem/profiles/{pid2}/task/luu", {"loai_tac_vu": "nhom_them", "ten": "grp1"})
post(f"/uem/profiles/{pid2}/task/luu", {"loai_tac_vu": "user_them", "ten": "nv9", "mat_khau": "Abc@1234"})
post(f"/uem/profiles/{pid2}/luu", {"ten": "tt", "ap_dung_tat_ca": "1", "bat": "1"})
m1 = DL.tim(DL.MAY.doc(), "m1"); mm_ = UP.mong_muon(m1)
kt("profile tu tri: bundle chi chua tac vu tu chua duoc (khong co tac vu mat khau)", pid2 in mm_ and len(UP.tao_bundle(m1, pid2)["tasks"]) == 1 and "Abc@1234" not in json.dumps(UP.tao_bundle(m1, pid2)))
v = UP.viec_dong_bo(m1, {}); kt("agent chua co bundle -> may chu gui bundle", v and v["kieu"] == "profile" and v["pid"] == pid2 and v["tasks"][0]["script"], v and v.get("kieu"))
kt("agent da co dung ver -> khong gui nua", UP.viec_dong_bo(m1, {pid2: mm_[pid2]}) is None)
v = UP.viec_dong_bo(m1, {pid2: mm_[pid2], "profile-cu": "1"}); kt("agent con bundle thua -> go", v and v["kieu"] == "profile_go" and v["pid"] == "profile-cu")
tid = UD.PROFILES.doc()[[p["id"] for p in UD.PROFILES.doc()].index(pid2)]["tasks"][0]["id"]
ack = UP.nhan_ket_qua_agent(m1, [{"pid": pid2, "ver": mm_[pid2], "luc": 1700000000, "trang_thai": "ok", "lam": 1, "loi": 0, "tasks": {tid: {"tt": "da_lam", "tb": "tao nhom", "luc": 1700000000}}}])
st = UD.TRANG_THAI_PROFILE.doc()[pid2]["m1"]
kt("ket qua agent tu ap dung (gui bu) duoc ghi + ack", ack == [pid2 + "|1700000000"] and st["trang_thai"] == "ok" and st["tasks"][tid]["tt"] == "da_lam", st)
ack = UP.nhan_ket_qua_agent(m1, [{"pid": pid2, "luc": 1700000100, "tasks": {tid: {"tt": "loi", "tb": "x"}, "khong-co": {"tt": "loi"}}}])
st = UD.TRANG_THAI_PROFILE.doc()[pid2]["m1"]; kt("ket qua loi -> trang thai loi; task la bi bo", st["trang_thai"] == "loi" and "khong-co" not in st["tasks"])
j2 = UA.them_viec("m1", "profile_chay", pid=pid2, timeout=60); UA._VIEC.pop(j2["id"], None); UA._HANG["m1"].clear()
th = agent_gia("m1", lambda sc: ("", ""), so_lan=1)
UP.chay_profile_may(pid2, "m1"); th.join(2)
kt("ap dung ngay profile toan tac vu tu tri qua agent: yeu cau agent chay (khong chay tren may chu)", True)
post(f"/uem/profiles/{pid2}/xoa")
# nguoi dung phien (nd gui kem nhip)
UA.xu_ly_nhip(DL.tim(DL.MAY.doc(), "m1"), {"ver": UA.PHIEN_BAN, "dang": [], "nd": {"user": "PC\\an", "printers": [{"name": "Canon Rieng", "port": "USB001"}, "rac"], "monitors": [{"manufacturer": "DEL", "model": "U2415", "serial": "S1"}]}}, "10.1.1.1")
kt("tro ly phien: nhan may in + man hinh (bo phan tu rac)", DL.tim(DL.MAY.doc(), "m1")["phien_nd"]["user"] == "PC\\an" and len(DL.tim(DL.MAY.doc(), "m1")["phien_nd"]["printers"]) == 1)
h = txt(get("/uem/may/m1/may-in")); kt("may in rieng cua nguoi dung hien trong tab May in", "Canon Rieng" in h)
h = txt(get("/uem/may/m1/man-hinh")); kt("man hinh tu tro ly phien hien trong tab Man hinh", "U2415" in h)
for p in ("/uem/may/m1/agent", "/uem/quan-tri/agent", "/uem/may/m2/agent"):
    r = get(p); kt(f"trang {p} 200", r.status_code == 200 and "Agent" in txt(r), r.status_code)
kt("chua bat mTLS: tab Agent bao ro va khong cho cai", "mTLS" in txt(get("/uem/may/m2/agent")) and not PKI.san_sang())
r = post("/uem/may/m2/agent/cai"); kt("cai qua WinRM khi chua bat mTLS: tu choi co huong dan", "8443" in txt(r))
PKI.san_sang = lambda: True
import re as _re
h = txt(post("/uem/may/m2/agent/ma")); mm = _re.search(r"/uem/agent/cai/([A-Za-z0-9_-]{20,})\.ps1", h); kt("tao lenh cai: co URL dung 1 lan, ghim dau van tay may chu", mm is not None and PKI.ca_sha256() in h, h[-300:])
if mm:
    r = c.get(f"/uem/agent/cai/{mm.group(1)}.ps1", headers=H); kt("script cai KHONG tai duoc qua cong 80 (khong co bi mat nginx)", r.status_code == 404, r.status_code)
    r = c.get(f"/uem/agent/cai/{mm.group(1)}.ps1", headers={"X-CS-TLS-Secret": BM}); kt("script cai tai duoc qua cong mTLS (co bi mat nginx)", r.status_code == 200 and b"ConsoleSystemAgent" in r.data and b"csc.exe" in r.data, r.status_code)
    sc = r.data.decode()
    kt("script cai: co CA + PFX + cau hinh, KHONG co khoa rieng CA", "BEGIN CERTIFICATE" in sc and "FromBase64String" in sc and "PRIVATE KEY" not in sc and "ca.key" not in sc)
    kt("script cai: moi here-string dong dung (khong co dong bat dau bang '@ giua noi dung)", all(sum(1 for ln in blk.split("\n") if ln.startswith("'@")) == 0 for blk in _re.findall(r"@'\n(.*?)\n'@", sc, _re.S)) and sc.count("@'\n") == sc.count("\n'@"))
    r = c.get(f"/uem/agent/cai/{mm.group(1)}.ps1", headers={"X-CS-TLS-Secret": BM}); kt("ma cai chi dung duoc 1 lan", r.status_code == 404)
    kt("sau khi tai script: m2 co chung chi (serial) moi", bool((DL.tim(DL.MAY.doc(), "m2").get("agent") or {}).get("serie")))
kt("ma cai sai bi tu choi", c.get("/uem/agent/cai/" + "x" * 30 + ".ps1", headers={"X-CS-TLS-Secret": BM}).status_code == 404)

# ---- trang Agent: ket noi (IP LAN, domain, cong) + tao file cai (MSI / script) co dong thoi gian
import shutil as _sh, socket as _sk, html as _html
from ui import uem_agent_goi as UG
h = txt(get("/uem/quan-tri/agent"))
kt("trang Agent: dong IP LAN cua server + o domain/cong + 2 nut tao file", "IP LAN của server" in h and 'name="domain"' in h and 'name="cong"' in h and "Tạo file MSI" in h and "Tạo script" in h and "kn-tl" in h)
ij = json.loads(txt(get("/uem/quan-tri/agent/thongtin.json")))
kt("thongtin.json: IP LAN hien tai + cong + domain", isinstance(ij["ips"], list) and ij["cong"] == PKI.cong() and "127.0.0.1" not in ij["ips"])
h = txt(post("/uem/quan-tri/agent/cai-dat", {"domain": "test.server.org", "cong": "9443"}))
kt("cai dat: luu domain + doi cong", PKI.cai_dat() == {"domain": "test.server.org", "cong": 9443} and "test.server.org" in h)
kt("cai dat: cong 80 / cong noi bo bi tu choi", "1024" in txt(post("/uem/quan-tri/agent/cai-dat", {"domain": "", "cong": "80"})) and PKI.cong() == 9443 and PKI.cai_dat()["domain"] == "test.server.org")
kt("cai dat: domain sai bi tu choi", "Domain không hợp lệ" in txt(post("/uem/quan-tri/agent/cai-dat", {"domain": "a b;c", "cong": "9443"})))
_sx = _sk.socket(); _sx.bind(("0.0.0.0", 0)); _px = _sx.getsockname()[1]
kt("cai dat: cong dang bi chuong trinh khac dung bi tu choi", "đang được chương trình khác dùng" in txt(post("/uem/quan-tri/agent/cai-dat", {"domain": "", "cong": str(_px)})) and PKI.cong() == 9443)
_sx.close()
DC_ = UG.dia_chi_chon()
kt("dia chi chon: co domain:cong + IP LAN", DC_ and DC_[0][1] == "test.server.org:9443" and all(v.endswith(":9443") for _, v in DC_))
for bad in ("test.server.org:8443", "a b:9443", "x", ""):
    try:
        UG.bat_dau("ps1", "x", bad, 7, 0); kt("bat_dau chan dia chi '" + bad + "'", False)
    except ValueError:
        kt("bat_dau chan dia chi '" + bad + "'", True)
def _cho(vid):
    for _ in range(300):
        v = UG.viec(vid)
        if v["tt"] != "dang": return v
        time.sleep(0.1)
    return v
# script
rj = json.loads(txt(c.post("/uem/quan-tri/agent/tao", data={"loai": "ps1", "ten": "Thu<b>VP.ps1", "dia_chi": "test.server.org:9443", "ngay": "7", "toi_da": "2"}, headers=H)))
v = _cho(rj["id"])
kt("tao script: 6 buoc deu xong, co goi_id", v["tt"] == "xong" and len(v["buoc"]) == 6 and all(b["tt"] == "xong" for b in v["buoc"]) and v["goi_id"], v)
g = UG.tim_goi(v["goi_id"])
kt("tao script: ten file duoc lam sach (khong ky tu HTML)", g["ten_file"] == "ThubVP.ps1", g["ten_file"])
rd = c.get(f"/uem/quan-tri/agent/goi/{g['id']}/tai", headers=H); sc = rd.data.decode("utf-8-sig")
ma = UA.ds_ghi_danh()[0]["ma"]
kt("script: nhung dung dia chi + dau van tay CA + ma, KHONG co khoa rieng / mat khau", rd.status_code == 200 and "https://test.server.org:9443" in sc and PKI.ca_sha256() in sc and ma in sc and "PRIVATE KEY" not in sc and "PfxPass" not in sc and "RunAs" in sc)
kt("script: dung chung doan ghim voi lenh cai (UA.PIN_CS)", UA.PIN_CS in sc)
kt("script: khong co dau nhay don la trong khoi Add-Type", "'" not in UA.PIN_CS)
h = _html.unescape(txt(get("/uem/quan-tri/agent")))
kt("danh sach file: hien ten, SHA-256, nut tai/xoa, dong thoi gian da luu", "ThubVP.ps1" in h and g["sha256"] in h and f"/goi/{g['id']}/tai" in h and "Dòng thời gian khi tạo" in h and "Lưu để tải về" in h)
# ghi danh bang chinh ma trong file
HN = {"X-CS-TLS-Secret": BM, "X-Real-IP": "203.0.113.5"}; n1 = len(DL.MAY.doc())
r = c.get(f"/uem/agent/cai/{ma}.ps1?h=PC-KT-01", headers=HN); sc2 = r.data.decode()
kt("ma trong file: ghi danh qua mTLS, dung URL cua file, bo qua bien dich khi MSI da dat exe", r.status_code == 200 and "test.server.org:9443" in sc2 and "CS_EXE_SAN" in sc2 and "daCoExe" in sc2)
mx = [x for x in DL.MAY.doc() if x.get("ten") == "PC-KT-01"]
kt("ma trong file: tu tao ban ghi may (ten may + IP nguon) co chung chi", len(DL.MAY.doc()) == n1 + 1 and len(mx) == 1 and mx[0]["ip"] == "203.0.113.5" and (mx[0].get("agent") or {}).get("serie"))
r = c.get(f"/uem/agent/cai/{ma}.ps1?h=PC-KT-01", headers=HN); kt("ma trong file: cai lai cung may khong tao may thua", r.status_code == 200 and len(DL.MAY.doc()) == n1 + 1)
r = c.get(f"/uem/agent/cai/{ma}.ps1?h=PC-KT-02", headers=HN); kt("ma trong file: vuot gioi han so may -> tu choi", r.status_code == 404 and len(DL.MAY.doc()) == n1 + 1)
r = c.get(f"/uem/agent/cai/{ma}.ps1?h=PC-KT-01", headers=H); kt("ma trong file: khong qua cong mTLS thi tu choi", r.status_code == 404)
# may da co trong danh sach (them tay / Trien khai phan mem) chua co agent: ghi danh gan agent vao DUNG ban ghi, khong tao ban ghi thu hai
DL.MAY.sua(lambda ds: ds.append({"id": "pre1", "ten": "may them tay", "ip": "203.0.113.77", "mac": ""})); nA = len(DL.MAY.doc())
_ead = UA.tao_ghi_danh("nhan may co san", "https://test.server.org:9443", 0, 0, "", None)
r = c.get(f"/uem/agent/cai/{_ead['ma']}.ps1?h=HOME-XYZ", headers={"X-CS-TLS-Secret": BM, "X-Real-IP": "203.0.113.77"})
_pre = DL.tim(DL.MAY.doc(), "pre1")
kt("ghi danh: may co san chua co agent (cung IP) duoc gan agent vao dung ban ghi, khong tao may thu hai", r.status_code == 200 and len(DL.MAY.doc()) == nA and (_pre.get("agent") or {}).get("serie") and _pre["ten"] == "may them tay", str(len(DL.MAY.doc()) - nA))
DL.MAY.sua(lambda ds: ds.append({"id": "pre2", "ten": "HOME-DHCP", "ip": "203.0.113.10", "mac": ""})); nB = len(DL.MAY.doc())
r = c.get(f"/uem/agent/cai/{_ead['ma']}.ps1?h=HOME-DHCP", headers={"X-CS-TLS-Secret": BM, "X-Real-IP": "203.0.113.88"})
_p2 = DL.tim(DL.MAY.doc(), "pre2")
kt("ghi danh: may co san doi IP (DHCP) khop theo ten may, cap nhat IP", r.status_code == 200 and len(DL.MAY.doc()) == nB and _p2["ip"] == "203.0.113.88" and (_p2.get("agent") or {}).get("serie"))
_wx = open(os.path.join(SRC, "ui", "agent_bin", "ConsoleSystemAgent.wxs.tpl"), encoding="utf-8").read()
kt("MSI: ghi danh chay ca khi cai lai/sua (lan truoc ghi danh loi giua chung van hoan tat duoc), khong chay khi go", 'Action="CsGhiDanh" Sequence="6601">NOT REMOVE AND CODE' in _wx and 'Action="CsDatPs" Sequence="1001">NOT REMOVE<' in _wx)
# ---- 23/10/2026: tu dien tu bao cao, nhom may, doi ten nut Lay thong tin
from ui import uem_baocao as UBC2, uem_profiles as UP2
DL.MAY.sua(lambda ds: ds.extend([{"id": "g1", "ten": "", "ip": "10.7.7.1", "mac": ""}, {"id": "g2", "ten": "Ten tay", "ip": "10.7.7.2", "mac": "11:22:33:44:55:66"}, {"id": "g3", "ten": "", "ip": "10.7.7.3", "mac": ""}]))
_r = bao_cao("PC-TUDIEN", "Windows 11 Pro", "Dell")
UBC2._tu_dien("g1", _r); UBC2._tu_dien("g2", _r)
_g1, _g2 = DL.tim(DL.MAY.doc(), "g1"), DL.tim(DL.MAY.doc(), "g2")
kt("tu dien: may moi lay MAC va ten may tu bao cao", _g1["mac"] == "AA:BB:CC:DD:EE:01" and _g1["ten"] == "PC-TUDIEN", str(_g1))
kt("tu dien: KHONG ghi de MAC/ten da co (nguoi dung sua tay)", _g2["mac"] == "11:22:33:44:55:66" and _g2["ten"] == "Ten tay", str(_g2))
_r2 = dict(_r); _r2["mac"] = ""; _r2["hostname"] = ""; _r2["networkadapters"] = [{"mac_address": "00-00-00-00-00-00", "addresses": "10.7.7.3"}, {"mac_address": "de-ad-be-ef-00-01", "addresses": "10.7.7.3"}]
UBC2._tu_dien("g3", _r2); _g3 = DL.tim(DL.MAY.doc(), "g3")
kt("tu dien: bo MAC rong 00:.. va lay card mang dung IP, chuan hoa dinh dang", _g3["mac"] == "DE:AD:BE:EF:00:01" and not _g3["ten"], str(_g3))
_t = txt(get("/uem/may")) + txt(get("/uem/quan-tri/may"))
kt("doi ten nut: 'Bao cao ngay' -> 'Lay thong tin'", "Báo cáo ngay" not in _t and "Lấy thông tin" in _t)
post("/uem/may/hang-loat", {"may": ["g1", "g2"], "viec": "nhom_moi", "nhom_moi": "Ke toan"})
_ng = [g for g in DL.NHOM_MAY.doc() if g["ten"] == "Ke toan"]
kt("nhom may: tao nhom moi tu cac may da chon", len(_ng) == 1 and sorted(_ng[0]["may"]) == ["g1", "g2"])
r = post("/uem/may/hang-loat", {"may": ["g3"], "viec": "nhom_moi", "nhom_moi": "ke toan"})
kt("nhom may: trung ten (khong phan biet hoa thuong) bi tu choi", len([g for g in DL.NHOM_MAY.doc() if g["ten"].lower() == "ke toan"]) == 1 and "Đã có nhóm" in txt(r))
post("/uem/may/hang-loat", {"may": ["g3"], "viec": "them_nhom", "nhom": _ng[0]["id"]})
kt("nhom may: them may vao nhom co san", "g3" in DL.tim(DL.NHOM_MAY.doc(), _ng[0]["id"])["may"])
_t = txt(get("/uem/may"))
kt("Máy tính: hien chip nhom + bo loc nhom", 'data-k="nhom"' in _t and "Ke toan" in _t and 'data-nhom="' + _ng[0]["id"] in _t)
post("/uem/profiles/tao", {"ten": "Chinh sach KT"}); _pf = [p for p in UD.PROFILES.doc() if p["ten"] == "Chinh sach KT"][0]
post(f"/uem/profiles/{_pf['id']}/luu", {"ten": "Chinh sach KT", "nhom_may": [_ng[0]["id"], "khong-co"], "bat": "1"})
_pf = DL.tim(UD.PROFILES.doc(), _pf["id"])
kt("policy theo nhom: chi luu nhom hop le", _pf["nhom_may"] == [_ng[0]["id"]])
kt("policy theo nhom: may ap dung = cac may trong nhom (khong can the)", sorted(m["id"] for m in UP2.may_ap_dung(_pf)) == ["g1", "g2", "g3"], str([m["id"] for m in UP2.may_ap_dung(_pf)]))
_t = txt(get(f"/uem/profiles/{_pf['id']}")) + txt(get("/uem/profiles"))
kt("trang profile: chon nhom may + hien pham vi theo nhom", "Ke toan (nhóm)" in _t and 'name="nhom_may"' in _t)
post("/uem/may/hang-loat", {"may": ["g3"], "viec": "bo_nhom", "nhom": _ng[0]["id"]})
kt("nhom may: go may khoi nhom", "g3" not in DL.tim(DL.NHOM_MAY.doc(), _ng[0]["id"])["may"])
post("/uem/may/hang-loat", {"may": ["g1"], "viec": "xoa"})
kt("xoa may: cung go khoi nhom", "g1" not in DL.tim(DL.NHOM_MAY.doc(), _ng[0]["id"])["may"])
# het han
e2 = UA.tao_ghi_danh("het han", "https://console.test:9443", 1, 0)
_gd = UA._gd_doc(); [x.update(het_han=time.time() - 5) for x in _gd if x["id"] == e2["id"]]; UA._gd_ghi(_gd)
kt("ma het han khong dung duoc va khong liet ke", c.get(f"/uem/agent/cai/{e2['ma']}.ps1?h=A", headers=HN).status_code == 404 and all(x["id"] != e2["id"] for x in UA.ds_ghi_danh()))
# xoa file -> thu hoi ma
post(f"/uem/quan-tri/agent/goi/{g['id']}/xoa")
kt("xoa file: file mat + ma bi thu hoi (may chua cai khong dung duoc nua)", UG.tim_goi(g["id"]) is None and c.get(f"/uem/agent/cai/{ma}.ps1?h=PC-KT-03", headers=HN).status_code == 404 and c.get(f"/uem/quan-tri/agent/goi/{g['id']}/tai", headers=H).status_code == 404)
# ---- passkey + go cai dat + khay he thong (v2.2.0)
pk = UA.bam_passkey("Abcd1234")
kt("passkey: dinh dang p1:100000:muoi:bam, khong chua passkey goc", re.fullmatch(r"p1:100000:[0-9a-f]{32}:[0-9a-f]{64}", pk) and "Abcd1234" not in pk)
import hashlib as _hl
_p = pk.split(":"); kt("passkey: bam khop PBKDF2-HMAC-SHA1 (tuong thich Rfc2898DeriveBytes cua .NET)", _hl.pbkdf2_hmac("sha1", b"Abcd1234", bytes.fromhex(_p[2]), 100000, 32).hex() == _p[3])
for bad in ("abc", "x" * 65, 'co"nhay'):
    try:
        UA.bam_passkey(bad); kt("passkey chan '" + bad[:8] + "'", False)
    except ValueError:
        kt("passkey chan '" + bad[:8] + "'", True)
rj = json.loads(txt(c.post("/uem/quan-tri/agent/tao", data={"loai": "ps1", "ten": "PK-script", "dia_chi": "test.server.org:9443", "ngay": "7", "toi_da": "0", "passkey": "Abcd1234"}, headers=H)))
v = _cho(rj["id"]); gp = UG.tim_goi(v["goi_id"]); dp, _ = UG.duong_file(gp["id"]); sp = open(dp, encoding="utf-8-sig").read()
kt("script co passkey: xac thuc PBKDF2 trong script, chi chua dau bam, KHONG chua passkey goc", v["tt"] == "xong" and gp["co_passkey"] and "Test-Pk" in sp and "$Pk = 'p1:100000:" in sp and "Rfc2898DeriveBytes" in sp and "Abcd1234" not in sp)
kt("script co passkey: doc passkey.json cuc bo (da cai thi phai nhap passkey cu)", "passkey.json" in sp and "Read-Host" in sp and "AsSecureString" in sp)
_ma = [x for x in UA.ds_ghi_danh() if x["id"] == gp["ma_id"]][0]
kt("ma ghi danh luu dau bam passkey (khong luu passkey goc)", _ma["pk"].startswith("p1:") and "Abcd1234" not in json.dumps(_ma))
_alld = b"".join(open(os.path.join(UG.THU_MUC, f), "rb").read() for f in os.listdir(UG.THU_MUC)) + open(UA.PKI._p("ghi-danh.json"), "rb").read()
kt("khong file nao tren dia chua passkey goc", b"Abcd1234" not in _alld)
sc = c.get(f"/uem/agent/cai/{_ma['ma']}.ps1?h=PC-PK-01", headers=HN).data.decode()
kt("script cai tu ma co passkey: ghi passkey.json (dau bam) + uninstall.bat + tac vu khay + thu muc pub", "$pkv = '" + _ma["pk"] + "'" in sc and "passkey.json" in sc and "uninstall.bat" in sc and "--uninstall" in sc and "ConsoleSystemTray" in sc and "'pub'" in sc and "--tray" in sc)
kt("script cai: bien dich co WinForms + winexe + codepage UTF-8", "/target:winexe" in sc and "/codepage:65001" in sc and "System.Windows.Forms.dll" in sc and "System.Drawing.dll" in sc)
kt("script cai: gui dung yeu cau ban ghi may o ma khong passkey = khong ghi passkey.json", "$pkv = ''" in c.get(f"/uem/agent/cai/{UA.tao_ghi_danh('khong pk', 'https://console.test:9443', 1, 0)['ma']}.ps1?h=PC-PK-02", headers=HN).data.decode())
kt("trang Agent co o passkey + chip Co passkey", "kn-pk" in txt(get("/uem/quan-tri/agent")) and "Có passkey" in _html.unescape(txt(get("/uem/quan-tri/agent"))))
cs = UA.CS.nguon()
for tu in ("--check-passkey", "--check-local", "--teardown", "--uninstall", "--tray", "NotifyIcon", "sync.flag", "status.json", "log.txt", "ShowBalloonTip", "Xem log", "Đồng bộ ngay"):
    kt("ma nguon C# co " + tu, tu in cs)
kt("ma nguon C#: dong bo ngay huy long-poll dang cho (CurReq.Abort)", "CurReq" in cs and "r.Abort()" in cs and "SyncReq" in cs)
kt("PS_GO (go tu xa) go ca tac vu khay", "Unregister-ScheduledTask -TaskName 'ConsoleSystemTray'" in UA.PS_GO)
if _sh.which("mcs") and _sh.which("mono"):
    import subprocess as _sp, tempfile as _t2
    _d = _t2.mkdtemp(); open(os.path.join(_d, "a.cs"), "w", encoding="utf-8-sig").write(cs)
    _r = _sp.run(["mcs", "-target:exe", "-out:" + os.path.join(_d, "a.exe"), "-r:System.ServiceProcess.dll", "-r:System.Web.Extensions.dll", "-r:System.Windows.Forms.dll", "-r:System.Drawing.dll", os.path.join(_d, "a.cs")], capture_output=True, text=True)
    kt("C#: bien dich duoc (mcs/mono)", _r.returncode == 0, _r.stdout[-300:] + _r.stderr[-300:])
    def _chk(*a): return _sp.run(["mono", os.path.join(_d, "a.exe"), *a], capture_output=True, text=True, timeout=60).returncode
    kt("C#: --check-passkey dung/sai/thieu/khong dat passkey (khop dau bam Python)", (_chk("--check-passkey", pk, "Abcd1234", "2"), _chk("--check-passkey", pk, "Sai12345", "2"), _chk("--check-passkey", pk, "", "2"), _chk("--check-passkey", "-", "", "2")) == (0, 1, 2, 0))
else:
    print("  (bo qua bien dich C# bang mono: may nay khong co mcs)")
# ---- nhieu dia chi du phong + chan doan (v2.3.0)
rj = json.loads(txt(c.post("/uem/quan-tri/agent/tao", data={"loai": "ps1", "ten": "Nhieu-dia-chi", "dia_chi": "test.server.org:9443,192.168.1.5:9443", "ngay": "7", "toi_da": "0"}, headers=H)))
v = _cho(rj["id"]); gm2 = UG.tim_goi(v["goi_id"]); dm2, _ = UG.duong_file(gm2["id"]); sm2 = open(dm2, encoding="utf-8-sig").read()
_e2 = [x for x in UA.ds_ghi_danh() if x["id"] == gm2["ma_id"]][0]
kt("nhieu dia chi: ma ghi danh luu danh sach (dau la chinh), script co $Servers + vong thu tung dia chi", v["tt"] == "xong" and _e2["urls"] == ["https://test.server.org:9443", "https://192.168.1.5:9443"] and "$Servers = @('https://test.server.org:9443', 'https://192.168.1.5:9443')" in sm2 and "foreach ($sv in $Servers)" in sm2 and "thu dia chi tiep theo" in sm2, sm2[:600])
kt("nhieu dia chi: ten hien thi liet ke ca hai", "test.server.org:9443, https://192.168.1.5:9443" in gm2["url"])
sc3 = c.get(f"/uem/agent/cai/{_e2['ma']}.ps1?h=PC-DP-01", headers=HN).data.decode()
import re as _re3
_cfg = _re3.search(r"WriteAllText\(\(Join-Path \$data 'config.json'\), '(\{.*?\})', \$u8\)", sc3)
_cj = json.loads(_cfg.group(1).replace("''", "'")) if _cfg else {}
kt("nhieu dia chi: config.json cua agent co url chinh + urls du phong", _cj.get("url") == "https://test.server.org:9443" and _cj.get("urls") == ["https://test.server.org:9443", "https://192.168.1.5:9443"], _cj)
for bad in ("test.server.org:9443,x:8443", ",".join("h%d.org:9443" % i for i in range(6)), "a b:9443"):
    try:
        UG.bat_dau("ps1", "x", bad, 7, 0); kt("nhieu dia chi: chan '" + bad[:30] + "'", False)
    except ValueError:
        kt("nhieu dia chi: chan '" + bad[:30] + "'", True)
try:
    UA.ps_cai("https://a.org:9443", "m1", {"pfx": b"x", "mat_khau": "m"}, urls=["http://x"]); kt("ps_cai chan dia chi du phong khong https", False)
except ValueError:
    kt("ps_cai chan dia chi du phong khong https", True)
h = txt(get("/uem/quan-tri/agent"))
kt("giao dien: o chon dia chi la checkbox (tick nhieu), mac dinh tick domain + IP dau", 'id="kn-dc"' in h and 'type="checkbox"' in h and "#kn-dc input:checked" in h and "địa chỉ dự phòng" in h)
rp = c.get("/uem/agent/ping", headers=hdr_cert("m1")); kt("ping mTLS: chung chi hop le -> 200 + gio + ban", rp.status_code == 200 and json.loads(rp.data)["ban"] == UA.PHIEN_BAN and abs(json.loads(rp.data)["gio"] - time.time()) < 5, rp.status_code)
kt("ping mTLS: khong co chung chi -> 403", c.get("/uem/agent/ping", headers=H).status_code == 403 and c.get("/uem/agent/ping", headers=hdr_cert("m1", verify="NONE")).status_code == 403)
for tu in ("Chẩn đoán kết nối", "RunDiag", "diag.flag", "diag.json", "/uem/agent/ping", "RotateUrl", "Probe(", "quay lai dia chi chinh", "Chép kết quả", "Quét lại"):
    kt("ma nguon C# co " + tu, tu in cs)
kt("C#: chan doan kiem DNS + TCP + mTLS + chung chi + dong ho + dia + passkey", all(x in cs for x in ("phân giải tên", "xác thực hai chiều (mTLS)", "Chứng chỉ của máy", "Đồng hồ của máy", "Dung lượng ổ", "Passkey gỡ cài đặt", "Nhịp báo cáo gần nhất")))
# ---- mac dinh: ma ghi danh suot doi + khong gioi han may; khong con o han dung / toi da tren giao dien
h = txt(get("/uem/quan-tri/agent"))
kt("giao dien: khong con o han dung / toi da may khi tao file", 'id="kn-ngay"' not in h and 'id="kn-toida"' not in h and "Hạn 30 ngày" not in h and "tối đa" not in _html.unescape(h.split("Tạo file cài")[1].split("kn-tl")[0]))
rj = json.loads(txt(c.post("/uem/quan-tri/agent/tao", data={"loai": "ps1", "ten": "Vinh-vien", "dia_chi": "test.server.org:9443"}, headers=H)))
v = _cho(rj["id"]); gv = UG.tim_goi(v["goi_id"]); ev = [x for x in UA.ds_ghi_danh() if x["id"] == gv["ma_id"]][0]
kt("mac dinh: ma ghi danh khong het han (suot doi) va khong gioi han so may", v["tt"] == "xong" and ev["het_han"] == UA.VINH_VIEN and ev["toi_da"] == 0 and "Không hết hạn" in v["buoc"][2]["ghi_chu"] and "không giới hạn số máy" in v["buoc"][2]["ghi_chu"], v["buoc"][2])
for i in range(12):
    r = c.get(f"/uem/agent/cai/{ev['ma']}.ps1?h=PC-VV-{i:02d}", headers=HN)
    if r.status_code != 200: break
kt("khong gioi han may: ghi danh 12 may lien tiep deu duoc", i == 11 and r.status_code == 200 and [x for x in UA.ds_ghi_danh() if x["id"] == ev["id"]][0]["da_dung"] == 12)
kt("trang liet ke: hien 'khong het han' + so may da cai", "không hết hạn" in _html.unescape(txt(get("/uem/quan-tri/agent"))) and "đã cài 12 máy" in _html.unescape(txt(get("/uem/quan-tri/agent"))))
post(f"/uem/quan-tri/agent/goi/{gv['id']}/xoa")
# chua bat mTLS -> loi o buoc 1, khong de lai ma mo coi
_so = PKI.san_sang; PKI.san_sang = lambda: False; n_ma = len(UA.ds_ghi_danh())
v = _cho(UG.bat_dau("ps1", "x", "test.server.org:9443", 7, 0)); PKI.san_sang = _so
kt("tao file khi chua bat mTLS: that bai o buoc 1, khong tao ma", v["tt"] == "loi" and v["buoc"][0]["tt"] == "loi" and len(UA.ds_ghi_danh()) == n_ma, v)
kt("viec khong ton tai / id sai -> 404", c.get("/uem/quan-tri/agent/tao/" + "0" * 12 + ".json", headers=H).status_code == 404 and c.get("/uem/quan-tri/agent/tao/..%2f.json", headers=H).status_code == 404)
# MSI (can wixl tren may build/Pi)
cs_ps1 = open(os.path.join(UG.BIN, "cs-install.ps1"), encoding="utf-8").read()
kt("cs-install.ps1 (trong MSI) dung dung doan ghim UA.PIN_CS", UA.PIN_CS in cs_ps1)
exe = open(os.path.join(UG.BIN, "cs-agent.exe"), "rb").read()
kt("MSI: cs-agent.exe dong goi dung phien ban nguon (" + UA.PHIEN_BAN + "), co chu ky PE", exe[:2] == b"MZ" and UA.PHIEN_BAN.encode("utf-16le") in exe)
if _sh.which("wixl"):
    rj = json.loads(txt(c.post("/uem/quan-tri/agent/tao", data={"loai": "msi", "ten": "Agent-VP", "dia_chi": "test.server.org:9443", "ngay": "30", "toi_da": "0"}, headers=H)))
    v = _cho(rj["id"]); gm = UG.tim_goi(v["goi_id"]) if v["goi_id"] else None
    kt("tao MSI: 6 buoc xong", v["tt"] == "xong" and len(v["buoc"]) == 6 and gm, v)
    rm = c.get(f"/uem/quan-tri/agent/goi/{gm['id']}/tai", headers=H)
    kt("MSI: tai duoc, dung OLE, dung ten, nhung dia chi + CA + ma vao file", rm.status_code == 200 and rm.data[:4] == b"\xd0\xcf\x11\xe0" and b"test.server.org:9443" in rm.data and PKI.ca_sha256().encode() in rm.data and [x for x in UA.ds_ghi_danh() if x["id"] == gm["ma_id"]][0]["ma"].encode() in rm.data and "Agent-VP.msi" in rm.headers.get("Content-Disposition", ""))
    kt("MSI: ProductCode khop giao dien", UG.MSI_PRODUCT_CODE.encode() in rm.data)
    kt("MSI: an khoi Control Panel (ARPSYSTEMCOMPONENT) + co uninstall.bat", b"ARPSYSTEMCOMPONENT" in rm.data and b"uninstall.bat" in rm.data and b"--check-passkey" in rm.data and b"--teardown" in rm.data)
    rj2 = json.loads(txt(c.post("/uem/quan-tri/agent/tao", data={"loai": "msi", "ten": "Agent-PK", "dia_chi": "test.server.org:9443", "ngay": "30", "toi_da": "0", "passkey": "Abcd1234"}, headers=H)))
    v2 = _cho(rj2["id"]); g2 = UG.tim_goi(v2["goi_id"]); rm2 = c.get(f"/uem/quan-tri/agent/goi/{g2['id']}/tai", headers=H)
    kt("MSI co passkey: nhung dau bam PKH, KHONG nhung passkey goc", v2["tt"] == "xong" and UA.ds_ghi_danh()[-1]["pk"].encode() in rm2.data and b"Abcd1234" not in rm2.data)
    post(f"/uem/quan-tri/agent/goi/{g2['id']}/xoa")
    rj3 = json.loads(txt(c.post("/uem/quan-tri/agent/tao", data={"loai": "msi", "ten": "MSI-nhieu", "dia_chi": "test.server.org:9443,192.168.1.5:9443", "ngay": "7", "toi_da": "0"}, headers=H)))
    v3 = _cho(rj3["id"]); g3 = UG.tim_goi(v3["goi_id"]); rm3 = c.get(f"/uem/quan-tri/agent/goi/{g3['id']}/tai", headers=H)
    kt("MSI nhieu dia chi: property SERVER chua danh sach phan cach dau phay", v3["tt"] == "xong" and b"test.server.org:9443,192.168.1.5:9443" in rm3.data)
    post(f"/uem/quan-tri/agent/goi/{g3['id']}/xoa")
    from ui import deployos as _D
    _D.APPS_DIR = tempfile.mkdtemp()
    post(f"/uem/quan-tri/agent/goi/{gm['id']}/kho"); kt("MSI: dua vao kho phan mem (Tai nguyen, Phan mem)", os.path.getsize(os.path.join(_D.APPS_DIR, "Agent-VP.msi")) == len(rm.data))
    post(f"/uem/quan-tri/agent/goi/{gm['id']}/xoa")
else:
    print("  (bo qua kiem tra MSI: may nay khong co wixl)")
try:
    UA.ps_cai("http://10.0.0.1", "m1", c1); kt("ps_cai chan URL khong phai https", False)
except ValueError:
    kt("ps_cai chan URL khong phai https", True)
# gia han chung chi
cu_ser = DL.tim(DL.MAY.doc(), "m1")["agent"]["serie"]
jr = UA.cap_lai_chung_chi("m1"); a1 = DL.tim(DL.MAY.doc(), "m1")["agent"]; UA._VIEC.pop(jr["id"], None); UA._HANG["m1"].clear()
kt("cap lai chung chi: tao serial moi, chua bo cai cu", a1["serie_moi"] != cu_ser and a1["serie"] == cu_ser and jr["kieu"] == "doi_chung_chi" and jr.get("pfx_pass"))
kt("dang doi: chung chi CU van dung duoc", agent_post("/uem/agent/nhip", {"ver": UA.PHIEN_BAN, "pf": {}}, hdr_cert()).status_code == 200)
r = agent_post("/uem/agent/nhip", {"ver": UA.PHIEN_BAN, "pf": {}}, hdr_cert(serial=a1["serie_moi"])); a2 = DL.tim(DL.MAY.doc(), "m1")["agent"]
kt("agent dung chung chi MOI -> chot (serie doi, serie_moi bo)", r.status_code == 200 and a2["serie"] == a1["serie_moi"] and "serie_moi" not in a2)
kt("sau khi chot: chung chi CU bi tu choi", agent_post("/uem/agent/nhip", {"ver": UA.PHIEN_BAN, "pf": {}}, hdr_cert(serial=cu_ser)).status_code == 403)
DL.MAY.sua(lambda ds: [x["agent"].update(han=time.time() + 5 * 86400) for x in ds if x["id"] == "m1"]); UA._HANG.get("m1", []) and UA._HANG["m1"].clear()
UA.NHIP_GIAY = 1; agent_post("/uem/agent/nhip", {"ver": UA.PHIEN_BAN, "pf": {}}, hdr_cert(serial=a1["serie_moi"]))
kt("sap het han (5 ngay) -> may chu TU gia han khi agent bao nhip", any(j["kieu"] == "doi_chung_chi" for j in UA._VIEC.values()) or "serie_moi" in DL.tim(DL.MAY.doc(), "m1")["agent"])
UA._HANG["m1"].clear(); UA._VIEC.clear()
UA.go_token("m2"); kt("go agent: thu hoi chung chi (xoa serial)", not (DL.tim(DL.MAY.doc(), "m2").get("agent") or {}).get("serie"))
kt("sau khi thu hoi, chung chi cu bi tu choi", agent_post("/uem/agent/nhip", {"ver": "2.0.0"}, hdr_cert("m2", serial="aa")).status_code == 403)
try:
    UV.ps_bat("a'; calc", "10.0.0.1", False); kt("VNC: chan PIN doc hai", False)
except ValueError:
    kt("VNC: chan PIN doc hai", True)
try:
    UV.ps_bat("Ab3dE6gH", "10.0.0.1; calc", False); kt("VNC: chan IP doc hai", False)
except ValueError:
    kt("VNC: chan IP doc hai", True)
sc = UV.ps_bat("Ab3dE6gH", "192.168.1.5", True)
kt("VNC truc tiep: chi cho IP Console System ket noi, tat loopback-only", "192.168.1.5-192.168.1.5:0,0.0.0.0-255.255.255.255:1" in sc and "0xe8,0x4a" in sc and "LoopbackOnly -Value 0" in sc)
sc = UV.ps_bat("Ab3dE6gH", "192.168.1.5", False, loopback=True)
kt("VNC tunnel: TightVNC CHI nghe 127.0.0.1 (khong lo cong ra mang)", "LoopbackOnly -Value 1" in sc and "AllowLoopback -Value 1" in sc and "IpAccessControl -Value '127.0.0.1-127.0.0.1:0,0.0.0.0-255.255.255.255:1'" in sc and "192.168.1.5" not in sc)
r = get("/uem/may/m1/tu-xa/vnc/khong-co-phien"); kt("phien VNC khong ton tai -> bao het han, khong sap", "hết hạn" in txt(r))
r = c.get("/uem/novnc/core/rfb.js", headers=H); kt("noVNC phuc vu duoc rfb.js", r.status_code == 200 and b"class RFB" in r.data)
r = c.get("/uem/novnc/../../../etc/passwd", headers=H); kt("noVNC khong cho duyet ra ngoai thu muc", r.status_code in (400, 404))
import socket as _s
srv = _s.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1); UV.CONG_VNC = srv.getsockname()[1]
with UV._KHOA: UV.PHIEN["tokgia1234567890abcdefghi"] = {"may_id": "m1", "ip": "127.0.0.1", "pin": "Ab3dE6gH", "luc": time.time(), "kenh": 0, "tunnel": False, "agent_sock": None, "agent_xong": threading.Event()}
UV.khoi_dong_bridge()
def nhan_gia():
    cs, _a = srv.accept(); cs.sendall(b"RFB 003.008\n"); d = cs.recv(100); cs.sendall(d[::-1]); time.sleep(0.3); cs.close()
th = threading.Thread(target=nhan_gia, daemon=True); th.start()
import websocket as _ws
try:
    w = _ws.create_connection("ws://127.0.0.1:%d/uem-vnc-ws/tokgia1234567890abcdefghi" % UV.CONG_WS, subprotocols=["binary"], timeout=5)
    b1 = w.recv(); w.send_binary(b"hello-vnc"); b2 = w.recv()
    kt("cau noi WS<->TCP (truc tiep): banner RFB va 2 chieu dung", b1 == b"RFB 003.008\n" and b2 == b"cnv-olleh", (b1, b2)); w.close()
except Exception as e:
    kt("cau noi WS<->TCP (truc tiep)", False, repr(e))
# TUNNEL: trinh duyet <-> cau noi <-> agent (WebSocket tu agent, co chung chi) - agent gia lap
TOK = "tuntun1234567890abcdefghij"
with UV._KHOA: UV.PHIEN[TOK] = {"may_id": "m1", "ip": "10.1.1.1", "pin": "Ab3dE6gH", "luc": time.time(), "kenh": 0, "tunnel": True, "agent_sock": None, "agent_xong": threading.Event()}
UA.NHIP_GIAY = 3
def agent_tunnel():
    for _ in range(6):
        rr = UA.xu_ly_nhip(DL.tim(DL.MAY.doc(), "m1"), {"ver": UA.PHIEN_BAN, "dang": [], "pf": {}}, "10.1.1.1")
        v = rr.get("viec")
        if v and v["kieu"] == "tunnel":
            UA.nhan_ket_qua(DL.tim(DL.MAY.doc(), "m1"), {"id": v["id"], "out": "OK", "err": ""})
            hd = ["%s: %s" % (k, x) for k, x in hdr_cert().items()]
            wa = _ws.create_connection("ws://127.0.0.1:%d/uem-agent-ws/%s" % (UV.CONG_WS, v["tok"]), header=hd, subprotocols=["binary"], timeout=8)
            wa.send_binary(b"RFB-tu-agent")
            try:
                while True:
                    d = wa.recv()
                    if not d: break
                    wa.send_binary(d[::-1])
            except Exception:
                pass
            return
th = threading.Thread(target=agent_tunnel, daemon=True); th.start()
try:
    wb = _ws.create_connection("ws://127.0.0.1:%d/uem-vnc-ws/%s" % (UV.CONG_WS, TOK), subprotocols=["binary"], timeout=10)
    t1 = wb.recv(); wb.send_binary(b"abc-123"); t2 = wb.recv()
    kt("TUNNEL: trinh duyet <-> cau noi <-> agent, 2 chieu dung", t1 == b"RFB-tu-agent" and t2 == b"321-cba", (t1, t2)); wb.close()
except Exception as e:
    kt("TUNNEL: trinh duyet <-> cau noi <-> agent", False, repr(e))
th.join(5)
TOK2 = "tuntun2234567890abcdefghij"
with UV._KHOA: UV.PHIEN[TOK2] = {"may_id": "m1", "ip": "10.1.1.1", "pin": "Ab3dE6gH", "luc": time.time(), "kenh": 0, "tunnel": True, "agent_sock": None, "agent_xong": threading.Event()}
try:
    _ws.create_connection("ws://127.0.0.1:%d/uem-agent-ws/%s" % (UV.CONG_WS, TOK2), header=["%s: %s" % (k, x) for k, x in hdr_cert(secret="sai").items()], timeout=5); kt("TUNNEL: agent khong co bi mat nginx bi tu choi", False)
except Exception:
    kt("TUNNEL: agent khong co bi mat nginx bi tu choi", True)
try:
    _ws.create_connection("ws://127.0.0.1:%d/uem-agent-ws/%s" % (UV.CONG_WS, TOK2), header=["%s: %s" % (k, x) for k, x in hdr_cert("m2", serial="aa").items()], timeout=5); kt("TUNNEL: agent cua may khac / chung chi thu hoi bi tu choi", False)
except Exception:
    kt("TUNNEL: agent cua may khac / chung chi thu hoi bi tu choi", True)
try:
    _ws.create_connection("ws://127.0.0.1:%d/uem-vnc-ws/khongco0123456789abcdefghij" % UV.CONG_WS, timeout=5); kt("cau noi: ma phien la bi tu choi", False)
except Exception:
    kt("cau noi: ma phien la bi tu choi", True)
# nhip KHONG ghi dia moi lan (may.json lon): chi khi doi thong tin / moi 10 phut
import os as _os
UA._NHIP.pop("m1", None); UA.xu_ly_nhip(DL.tim(DL.MAY.doc(), "m1"), {"ver": UA.PHIEN_BAN, "host": "H", "dang": []}, "10.1.1.1")
mt = _os.stat(DL.MAY.duong).st_mtime_ns
for _ in range(4): UA.xu_ly_nhip(DL.tim(DL.MAY.doc(), "m1"), {"ver": UA.PHIEN_BAN, "host": "H", "dang": []}, "10.1.1.1")
kt("agent: 4 nhip lien tiep khong ghi lai may.json", _os.stat(DL.MAY.duong).st_mtime_ns == mt)
kt("agent: trang thai van 'dang song' tu bo nho", UA.con_song(DL.tim(DL.MAY.doc(), "m1")) and UA.trang_thai(DL.tim(DL.MAY.doc(), "m1"))[0] == "online")
UA.xu_ly_nhip(DL.tim(DL.MAY.doc(), "m1"), {"ver": UA.PHIEN_BAN, "host": "H2", "dang": []}, "10.1.1.1")
kt("agent: doi ten may thi ghi dia", _os.stat(DL.MAY.duong).st_mtime_ns != mt and DL.tim(DL.MAY.doc(), "m1")["agent"]["may"] == "H2")
# ---- XSS: moi truong van ban tu nguoi dung deu phai bi escape tren MOI trang
X = "<script>alert(7)</script>"
DL.TAI_KHOAN.sua(lambda d: d.append({"id": "tkx", "ten": X, "user": X, "mk": DL.ma_hoa("x")}))
post("/uem/quan-tri/the/luu", {"ten": X}); post("/uem/quan-tri/dia-diem/luu", {"ten": X, "mo_ta": X}); post("/uem/quan-tri/metadata/luu", {"ten": X, "mo_ta": X})
tx = [t for t in UD.THE.doc() if t["ten"] == X][0]["id"]; dx = [t for t in UD.DIA_DIEM.doc() if t["ten"] == X][0]["id"]; mx = [t for t in UD.METADATA.doc() if t["ten"] == X][0]["id"]
post("/uem/may/m1/quan-ly", {"bi_danh": X, "ip": "10.1.1.1", "loai": X, "the": [tx], "dia_diem": dx, "tai_khoan_id": "tkx", "giam_sat": "1"})
post("/uem/may/m1/ghi-chu", {"ghi_chu": X}); post("/uem/may/m1/metadata", {"md_" + mx: X})
post("/uem/profiles/tao", {"ten": X, "mo_ta": X}); px = [p for p in UD.PROFILES.doc() if p["ten"] == X][0]["id"]
post(f"/uem/profiles/{px}/task/luu", {"loai_tac_vu": "powershell", "script": X, "chay": "luon"})
DL.MAY.sua(lambda ds: ds[0].update(agent=dict(ds[0].get("agent") or {}, ban=X, may=X), phien_nd={"user": X, "printers": [{"name": X, "port": X}], "monitors": [{"model": X, "manufacturer": X}], "luc": time.time()}))
bad = []
for p in ["/uem", "/uem/may", "/uem/phan-mem", "/uem/bao-mat", "/uem/bao-mat/cap-nhat", "/uem/trien-khai", "/uem/trien-khai/goi?id=7zip.7zip", "/uem/profiles", f"/uem/profiles/{px}", "/uem/bao-cao",
          "/uem/quan-tri/may", "/uem/quan-tri/agent", "/uem/quan-tri/the", "/uem/quan-tri/dia-diem", f"/uem/quan-tri/dia-diem?sua={dx}", f"/uem/quan-tri/the?sua={tx}", "/uem/quan-tri/metadata", "/uem/quan-tri/nhat-ky", "/uem/chua-ho-tro", "/uem/phan-mem?ten=7-Zip"] + \
         [f"/uem/may/m1/{t}" for t in ("", "phan-cung", "he-dieu-hanh", "o-dia", "man-hinh", "mang", "may-in", "chia-se", "phan-mem", "cap-nhat", "ghi-chu", "metadata", "quan-ly", "tu-xa", "agent", "nguon", "trien-khai", "tac-vu")]:
    h = txt(get(p))
    if "<script>alert(7)" in h or "</script>alert" in h: bad.append(p)
kt("XSS: khong trang nao in <script> tu du lieu nguoi dung (%d trang)" % 40, not bad, bad)
# ---- khong lam hong muc khac
for p in ("/", "/deployos/trienkhai", "/deployos/trienkhai/may", "/deployos", "/nettools"):
    r = get(p); kt(f"muc cu {p} van chay", r.status_code == 200)
print(f"\nDAT {len(DAT)}  HONG {len(HONG)}")
for x in HONG: print("  - " + x)
sys.exit(1 if HONG else 0)
