# Test Trien khai phan mem (khong can may Windows that): lich, ma hoa mat khau, trang, kiem tra dau vao, token tai file, dong co voi may khong ton tai.
import json, os, re, sys, tempfile, time
from datetime import datetime
TMP = tempfile.mkdtemp(prefix="tk-test-")
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
from ui import tk_dulieu as DL, tk_dongco as DC
DAT, HONG = [], []
def kt(ten, dk, ct=""):
    (DAT if dk else HONG).append(ten); print(("  OK   " if dk else "  HONG ") + ten + ("" if dk or not ct else f"  -> {ct}"), flush=True)
c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
def post(p, d): return c.post(p, data=d, headers=H, follow_redirects=True)
def get(p): return c.get(p, headers=H, follow_redirects=True)
# ---- lich
lt = {"kieu": "hang_tuan", "gio": "02:00", "thu": [5]}                      # thu 7
t = DL.lan_hen_gan_nhat(lt, datetime(2026, 10, 21, 12, 0))                     # thu 4 21/10/2026 -> thu 7 gan nhat = 17/10
kt("lich hang tuan thu 7: lan gan nhat 17/10 02:00", t == datetime(2026, 10, 17, 2, 0), str(t))
kt("lich hang tuan: lan ke tiep 24/10", DL.lan_hen_ke_tiep(lt, datetime(2026, 10, 21, 12, 0)) == datetime(2026, 10, 24, 2, 0))
kt("hang ngay: hom nay chua toi gio thi lay hom qua", DL.lan_hen_gan_nhat({"kieu": "hang_ngay", "gio": "23:00"}, datetime(2026, 10, 21, 12, 0)) == datetime(2026, 10, 20, 23, 0))
kt("hang thang ngay 31: thang 2 chay ngay cuoi thang", DL.lan_hen_gan_nhat({"kieu": "hang_thang", "gio": "01:00", "ngay_thang": 31}, datetime(2027, 3, 5, 0, 0)) == datetime(2027, 2, 28, 1, 0))
kt("hang nam 15/3", DL.lan_hen_gan_nhat({"kieu": "hang_nam", "gio": "08:00", "thang": 3, "ngay_thang": 15}, datetime(2026, 10, 21, 0, 0)) == datetime(2026, 3, 15, 8, 0))
kt("mot lan: chua toi thi khong co lan gan nhat", DL.lan_hen_gan_nhat({"kieu": "mot_lan", "gio": "09:00", "ngay": "2030-01-01"}, datetime(2026, 10, 21, 0, 0)) is None)
kt("gioi han den_ngay: qua han thi khong chay nua", DL.lan_hen_gan_nhat({"kieu": "hang_ngay", "gio": "01:00", "den_ngay": "2026-10-10"}, datetime(2026, 10, 21, 0, 0)) == datetime(2026, 10, 10, 1, 0))
l, loi = DL.chuan_lich({"kieu": "hang_tuan", "gio": "25:99"}); kt("gio sai bi tu choi", l is None and loi)
l, loi = DL.chuan_lich({"kieu": "hang_tuan", "gio": "02:00", "thu": []}); kt("hang tuan khong chon thu bi tu choi", l is None and loi)
kt("mo ta lich tieng Viet", "Thứ 7" in DL.mo_ta_lich(lt) and "02:00" in DL.mo_ta_lich(lt))
# ---- ma hoa
s = DL.ma_hoa("MatKhau@2023"); kt("ma hoa khong de lo ban ro", "MatKhau" not in s and DL.giai_ma(s) == "MatKhau@2023")
kt("khoa 0600", oct(os.stat(os.path.join(DL.DIR, ".khoa")).st_mode)[-3:] == "600")
# ---- trang
for p in ("", "/kichban", "/lich", "/may", "/may/nhom", "/may/quet", "/may/taikhoan", "/nhom-tn", "/khac"):
    r = get("/deployos/trienkhai" + p); kt(f"trang {p or '/'} 200", r.status_code == 200 and "Triển khai" in r.get_data(as_text=True))
r = get("/deployos/kho"); h = r.get_data(as_text=True); open("/tmp/kho-test.html","w").write(h)
kt("Kho trung tam (ngu canh tk): khong co nut loc He dieu hanh / WinPE", 'data-loai="os"' not in h and 'data-loai="winpe"' not in h and 'data-loai="phanmem"' in h)
r = get("/deployos/console/apps"); kt("Tai nguyen Phan mem (tk): thanh tab Trien khai", "Máy - nhóm máy" in r.get_data(as_text=True))
r = get("/deployos/kichban"); kt("Vao Deployment OS tro lai thanh tab OS", "Tiến trình" in r.get_data(as_text=True) and "Máy - nhóm máy" not in r.get_data(as_text=True))
# ---- may / nhom / tai khoan
post("/deployos/trienkhai/may/them", {"ip": "10.255.255.1-3", "ten": "May thu"})
kt("them dai IP -> 3 may", len(DL.MAY.doc()) == 3)
r = post("/deployos/trienkhai/may/them", {"ip": "999.1.1.1"}); kt("IP sai bi tu choi", "không phải địa chỉ IP" in r.get_data(as_text=True))
post("/deployos/trienkhai/may/them", {"ip": "10.255.255.1"}); kt("them trung IP khong nhan doi", len(DL.MAY.doc()) == 3)
ids = [m["id"] for m in DL.MAY.doc()]
post("/deployos/trienkhai/may/nhom/luu", {"ten": "Nhom thu", "may": ids[:2]}); kt("tao nhom may", len(DL.NHOM_MAY.doc()) == 1 and len(DL.NHOM_MAY.doc()[0]["may"]) == 2)
post("/deployos/trienkhai/may/taikhoan/them", {"ten": "Tk thu", "user": "administrator", "mk": "BiMat-xyz-123"})
tk = DL.TAI_KHOAN.doc()
kt("tai khoan luu da ma hoa", len(tk) == 1 and "BiMat" not in json.dumps(tk))
tat_ca = "".join(get("/deployos/trienkhai" + p).get_data(as_text=True) for p in ("/may/taikhoan", "/kichban", "/khac", "/may"))
kt("mat khau KHONG hien o bat ky trang nao", "BiMat-xyz-123" not in tat_ca and tk[0]["mk"] not in tat_ca)
# ---- nhom tai nguyen + kich ban
r = post("/deployos/trienkhai/nhom-tn/luu", {"ten": "Nhom tn", "muc": ["script|khong-co.bat"]}); kt("nhom tai nguyen voi tai nguyen khong ton tai bi tu choi", "ít nhất một tài nguyên" in r.get_data(as_text=True))
buoc = [{"loai": "winget", "ref": "7zip.7zip"}, {"loai": "baomat", "ref": ""}, {"loai": "kiemke", "ref": ""}, {"loai": "nguon", "ref": "khoi_dong_lai"},
        {"loai": "winget", "ref": "bad id; rm -rf"}, {"loai": "phanmem", "ref": "khong-co.msi"}, {"loai": "la", "ref": "x"}]
post("/deployos/trienkhai/kichban/luu", {"ten": "KB thu", "buoc_json": json.dumps(buoc), "nhom_may": [DL.NHOM_MAY.doc()[0]["id"]], "may": [ids[2]], "tai_khoan_id": tk[0]["id"]})
kb = DL.KICH_BAN.doc()
kt("kich ban luu, loc buoc khong hop le (con 4)", len(kb) == 1 and len(kb[0]["buoc"]) == 4, str(kb and [b["loai"] for b in kb[0]["buoc"]]))
kt("may cua kich ban = nhom + le, khong trung (3)", len(DC.may_cua_kich_ban(kb[0])) == 3)
r = post("/deployos/trienkhai/kichban/luu", {"ten": "", "buoc_json": "[]"}); kt("kich ban rong bi tu choi", len(DL.KICH_BAN.doc()) == 1)
# ---- kich hoat + dong co (may khong ton tai -> offline, thu lai, khong sap)
r = post("/deployos/trienkhai/chay", {"id": kb[0]["id"]})
kt("bam Chay -> kich hoat", DL.TRANG_THAI.doc()[kb[0]["id"]]["bat"] is True)
DC.tick()
for _ in range(40):
    time.sleep(0.5)
    st = DL.TRANG_THAI.doc()[kb[0]["id"]]
    if st.get("may") and all(m["tt"] == "offline" for m in st["may"].values()): break
st = DL.TRANG_THAI.doc()[kb[0]["id"]]
kt("tick tao luot chay voi 3 may", len(st.get("may", {})) == 3, str(st.get("slot")))
kt("may khong ton tai -> offline + hen thu lai ~5 phut", all(m["tt"] == "offline" and m["tiep"] > time.time() + 200 for m in st["may"].values()), str({k: v["tt"] for k, v in st["may"].items()}))
kt("popup JSON co nhat ky va buoc", bool(json.loads(get("/deployos/trienkhai/tt/" + kb[0]["id"]).data)["nhat_ky"]))
post("/deployos/trienkhai/dung", {"id": kb[0]["id"]}); kt("bam Dung -> tat", DL.TRANG_THAI.doc()[kb[0]["id"]]["bat"] is False)
# ---- hen gio chi tinh sau luc bam Chay
kbx = {"id": "x", "lich_id": "lx"}
DL.LICH.sua(lambda ds: ds.append({"id": "lx", "ten": "x", "kieu": "hang_ngay", "gio": "00:01"}))
now = datetime.now()
sl = DC._slot_hien_tai(kbx, {"kich_hoat": time.time(), "slot": ""}, now.replace(hour=12, minute=0)) if now.hour >= 12 or True else ""
kt("bam Chay SAU gio hen thi khong chay ngay luon", sl == "", sl)
sl2 = DC._slot_hien_tai(kbx, {"kich_hoat": time.time() - 90000, "slot": ""}, datetime.now().replace(hour=0, minute=30))
kt("da kich hoat tu truoc, lo gio hen <6h thi chay bu", sl2 != "", sl2)
# ---- chay nhanh
kid, loi = DC.chay_nhanh("Thu nhanh", [{"loai": "baomat", "ref": ""}], ids[:1], tk[0]["id"]); kt("chay nhanh tao kich ban tam", bool(kid))
kt("kich ban tam khong hien o danh sach Trien khai", "Thu nhanh" not in get("/deployos/trienkhai").get_data(as_text=True))
# ---- token tai file
f = os.path.join(TMP, "x.bat"); open(f, "w").write("echo 1")
tok = DC.tao_token(f)
r = c.get(f"/tk/tai/{tok}/x.bat", environ_overrides={"REMOTE_ADDR": "192.168.1.50"}); kt("token dung -> tai duoc", r.status_code == 200 and b"echo 1" in r.data)
r = c.get(f"/tk/tai/{tok}/khac.bat", environ_overrides={"REMOTE_ADDR": "192.168.1.50"}); kt("sai ten file -> khong tai duoc", r.status_code != 200)
r = c.get("/tk/tai/00000000000000000000000000000000/x.bat", environ_overrides={"REMOTE_ADDR": "192.168.1.50"}); kt("token gia -> khong tai duoc", r.status_code != 200)
r = c.get(f"/tk/tai/{tok}/x.bat", environ_overrides={"REMOTE_ADDR": "8.8.8.8"}); kt("IP cong cong -> khong tai duoc", r.status_code != 200)
DC._TOKEN[tok]["het"] = time.time() - 1
r = c.get(f"/tk/tai/{tok}/x.bat", environ_overrides={"REMOTE_ADDR": "192.168.1.50"}); kt("token het han -> khong tai duoc", r.status_code != 200)
# ---- 23/10/2026: thu lai 3 lan cach 5 phut roi "Khong thanh cong", 4 nhom trang thai, lam moi, doi ten tab
kt("TOI_DA_THU = 3, thu lai moi 5 phut", DC.TOI_DA_THU == 3 and DC.THU_LAI_LOI_BUOC == 300 and DC.THU_LAI_MAY_TAT == 300)
post("/deployos/trienkhai/chay", {"id": kb[0]["id"]})
kid = kb[0]["id"]
def cho_thu(n):
    for _ in range(80):
        time.sleep(0.5)
        st_ = DL.TRANG_THAI.doc()[kid]
        if st_.get("may") and all(m["thu"] >= n and m["tt"] in ("offline", "loi") for m in st_["may"].values()): return st_
    return DL.TRANG_THAI.doc()[kid]
DC.tick(); st = cho_thu(1)
kt("lan thu 1 that bai: cho thu lai (thu=1, offline)", all(m["thu"] == 1 and m["tt"] == "offline" for m in st["may"].values()), str({k: (v["tt"], v["thu"]) for k, v in st["may"].items()}))
for n in (2, 3):
    def ep(tt):
        for m in tt[kid]["may"].values(): m["tiep"] = 0
    DL.TRANG_THAI.sua(ep); DC.tick(); st = cho_thu(n)
kt("sau 3 lan thu may bi danh dau 'loi' (Khong thanh cong), het hen thu lai", all(m["tt"] == "loi" and m["thu"] == 3 and m["tiep"] == 0 for m in st["may"].values()), str({k: (v["tt"], v["thu"]) for k, v in st["may"].items()}))
kt("nhat ky ghi 'Khong thanh cong' o lan 3/3", any("3/3" in x and "Không thành công" in x for x in st["nhat_ky"]))
DC.tick()
kt("may da Khong thanh cong thi tick khong chay lai", all(m["tt"] == "loi" for m in DL.TRANG_THAI.doc()[kid]["may"].values()))
trang = get("/deployos/trienkhai").get_data(as_text=True)
kt("trang Trien khai co nut Lam moi", 'id="tk-lam-moi"' in trang and "Làm mới" in trang)
kt("hien chip 'Khong thanh cong 3' (nhom may that bai)", "Không thành công 3" in trang, re.sub(r"<[^>]+>", " ", trang)[:300])
kt("noi ro 3 lan, cach nhau 5 phut", "tối đa 3 lần, cách nhau 5 phút" in trang)
st_mix = {"bat": True, "slot": "x", "may": {"a": {"tt": "xong"}, "b": {"tt": "loi"}, "c": {"tt": "dang"}, "d": {"tt": "offline"}}}
from ui import tk_trang as TKT
d_ = TKT._dem_may(st_mix); h_ = TKT._chip_dem(d_)
kt("kich ban co ca may thanh cong va that bai: hien ca 'Thanh cong' + 'Khong thanh cong' (+ Dang chay, Cho thu lai)",
   d_ == {"xong": 1, "dang": 1, "cho": 1, "loi": 1} and all(x in h_ for x in ("Thành công 1", "Không thành công 1", "Đang chạy 1", "Chờ thử lại 1")), h_)
kt("trang trien khai khong con nhan 'Chuc nang khac'", "Chức năng khác" not in trang and "Kiểm tra bảo mật" in trang)
khac = get("/deployos/trienkhai/khac").get_data(as_text=True)
kt("da bo muc 'Tinh nang lay cam hung tu OpenUEM'", "lấy cảm hứng từ OpenUEM" not in khac and "Đang triển khai" not in khac)
kt("trang Kiem tra bao mat van co bang va chay nhanh", "Trạng thái bảo mật các máy" in khac and "Chạy nhanh" in khac)
kbp = get("/deployos/trienkhai/kichban").get_data(as_text=True)
kt("kich ban: o tim phan mem/script trong danh sach chon buoc", 'id="b-tim"' in kbp and "ve_ref" in kbp)
post("/deployos/trienkhai/dung", {"id": kid})
# ---- Kho trung tam: tich nhieu muc roi tai 1 lan
from ui import khotrungtam as KT, deployos as DOS
DS_KHO = [{"id": f"m{i}", "loai": "phanmem", "ten": f"Phan mem {i}", "ten_file": f"pm{i}.msi", "kich_thuoc": 1000, "mo_ta": "", "cap_nhat_luc": 1} for i in range(1, 4)] + \
         [{"id": "s1", "loai": "script", "ten": "Script 1", "ten_file": "s1.ps1", "kich_thuoc": 100, "mo_ta": "", "cap_nhat_luc": 1},
          {"id": "x1", "loai": "phanmem", "ten": "Khong ho tro", "ten_file": "x.dat", "kich_thuoc": 100, "mo_ta": "", "cap_nhat_luc": 1}]
_goc_dc, _goc_ds, _goc_tn = KT.doc_cauhinh, KT.danh_sach, KT.tai_nen
GOI = []
KT.doc_cauhinh = lambda: {"url": "https://kho.test", "token": "t"}
KT.danh_sach = lambda ch: (True, DS_KHO)
KT.tai_nen = lambda ch, m, dich, sau=None, khi_huy=None, don_dep=None: (GOI.append((m["id"], os.path.basename(dich))) or (True, "ok"))
trang = get("/deployos/kho").get_data(as_text=True)
kt("Kho trung tam: moi muc tai duoc co o tich, muc khong ho tro thi khong", trang.count('class="tich-kho"') == 4, str(trang.count('class="tich-kho"')))
kt("Kho trung tam: o 'chon tat ca' + nut Tai cac muc da tich", 'id="tich-tat-ca"' in trang and 'action="/deployos/kho/tai-nhieu"' in trang and "Tải các mục đã tích" in trang)
r = post("/deployos/kho/tai-nhieu", {"id": ["m1", "m3", "s1", "khong-co"]})
t_ = r.get_data(as_text=True)
kt("tai nhieu: 3 muc hop le duoc bat dau, muc la bi bao", sorted(x[0] for x in GOI) == ["m1", "m3", "s1"] and "Chưa tải được" in t_ and "Đã bắt đầu tải 3/4" in t_, str(GOI) + re.sub(r"<[^>]+>", " ", t_)[:400])
GOI.clear(); r = post("/deployos/kho/tai-nhieu", {})
kt("tai nhieu: khong tich gi thi bao ro", "Chưa tích mục nào" in r.get_data(as_text=True) and not GOI)
GOI.clear(); r = post("/deployos/kho/tai", {"id": "m2"})
kt("nut Tai ve tung muc van chay nhu cu", GOI == [("m2", "pm2.msi")])
KT.doc_cauhinh, KT.danh_sach, KT.tai_nen = _goc_dc, _goc_ds, _goc_tn
# ---- MSI agent co passkey: Trien khai phan mem tu dien PASSKEY
from ui import uem_agent as UA, uem_agent_goi as UG
os.makedirs(DOS.APPS_DIR, exist_ok=True)
msi = b"\xd0\xcf\x11\xe0" + os.urandom(20000)
open(os.path.join(DOS.APPS_DIR, "agent.msi"), "wb").write(msi)
import hashlib
pkh = UA.bam_passkey("Mat-Khau-9")
e = UA.tao_ghi_danh("thu", "https://192.168.9.9:8443", 0, 0, pkh, ["https://192.168.9.9:8443"])
os.makedirs(UG.THU_MUC, exist_ok=True)
UG._ghi([{"id": "abcdef0123", "loai": "msi", "ten_file": "agent.msi", "tao_luc": time.time(), "url": "x", "ma_id": e["id"], "ngay": 0, "toi_da": 0,
          "co_passkey": True, "pk_ma": "", "kich_thuoc": len(msi), "sha256": hashlib.sha256(msi).hexdigest(), "ban_agent": "2.3.2", "buoc": []}])
kt("kiem_passkey dung/sai", UA.kiem_passkey("Mat-Khau-9", pkh) and not UA.kiem_passkey("sai", pkh) and not UA.kiem_passkey("x", "rac"))
CHAY = []
_g1, _g2 = DC._tai_ve_may, DC._chay_tien_trinh
DC._tai_ve_may = lambda *a, **k: None
DC._chay_tien_trinh = lambda c, tep, doi_so, don="": (CHAY.append((tep, doi_so)) or (0, ""))
ok, tb = DC._b_phanmem(None, "1.1.1.1", {"loai": "phanmem", "ref": "agent.msi"}, {})
kt("MSI agent co passkey ma chua luu passkey -> bao ro, khong chay msiexec", not ok and "Lưu passkey cho triển khai" in tb and not CHAY, tb)
ok, tb = UG.luu_passkey_trien_khai("abcdef0123", "sai-passkey"); kt("luu passkey sai bi tu choi", not ok and not UG.tim_goi("abcdef0123")["pk_ma"])
ok, tb = UG.luu_passkey_trien_khai("abcdef0123", "Mat-Khau-9"); g_ = UG.tim_goi("abcdef0123")
kt("luu passkey dung: duoc ma hoa, khong luu ban ro", ok and g_["pk_ma"] and "Mat-Khau-9" not in json.dumps(g_) and UG.passkey_trien_khai(g_) == "Mat-Khau-9")
ok, tb = DC._b_phanmem(None, "1.1.1.1", {"loai": "phanmem", "ref": "agent.msi"}, {})
kt("Trien khai MSI agent: tu dien PASSKEY vao msiexec", ok and CHAY and CHAY[0][0] == "msiexec.exe" and 'PASSKEY="Mat-Khau-9"' in CHAY[0][1] and "/qn" in CHAY[0][1], str(CHAY))
CHAY.clear(); open(os.path.join(DOS.APPS_DIR, "khac.msi"), "wb").write(b"\xd0\xcf\x11\xe0" + os.urandom(100))
ok, tb = DC._b_phanmem(None, "1.1.1.1", {"loai": "phanmem", "ref": "khac.msi"}, {})
kt("MSI khac (khong phai goi agent): khong chen PASSKEY", ok and "PASSKEY" not in CHAY[0][1], str(CHAY))
DC._tai_ve_may, DC._chay_tien_trinh = _g1, _g2
tr = get("/uem/quan-tri/agent").get_data(as_text=True)
kt("trang Agent: trang thai passkey cho triển khai + khung Smart App Control", "đã lưu passkey" in tr and "Smart App Control" in tr and "VerifiedAndReputablePolicyState" in tr)
UG.bo_passkey_trien_khai("abcdef0123"); kt("bo passkey da luu", not UG.passkey_trien_khai(UG.tim_goi("abcdef0123")))
# ---- Kho file: thanh tien do khi tai len (XHR) tra JSON; khong XHR van tra trang
import io
sp = get("/storage").get_data(as_text=True)
kt("Kho file: co thanh tien do tai len (phan tram, toc do, con lai)", 'id="thanh-len"' in sp and "xhr.upload.onprogress" in sp and "còn khoảng" in sp and "SHA-256" in sp)
r = c.post("/storage/len", data={"file": (io.BytesIO(b"abc" * 1000), "thu-tien-do.iso")}, headers={**H, "X-Requested-With": "xhr"}, content_type="multipart/form-data")
j = r.get_json(silent=True) or {}
kt("tai len qua XHR tra JSON {ok,msg}", r.status_code == 200 and j.get("ok") is True and "thu-tien-do.iso" in j.get("msg", ""), r.get_data(as_text=True)[:200])
r = c.post("/storage/len", data={"file": (io.BytesIO(b"x"), "bad.sh")}, headers={**H, "X-Requested-With": "xhr"}, content_type="multipart/form-data")
j = r.get_json(silent=True) or {}
kt("XHR: duoi file khong cho phep -> ok=false kem ly do", j.get("ok") is False and "Không nhận đuôi" in j.get("msg", ""))
r = c.post("/storage/len", data={"file": (io.BytesIO(b"abc"), "thu2.iso")}, headers=H, content_type="multipart/form-data", follow_redirects=True)
kt("khong XHR van tra trang binh thuong", "Đã lưu thu2.iso" in r.get_data(as_text=True))
post("/storage/xoa", {"name": "thu-tien-do.iso"}); post("/storage/xoa", {"name": "thu2.iso"})
# ---- xoa
post("/deployos/trienkhai/kichban/xoa", {"id": kb[0]["id"]}); kt("xoa kich ban", not [k for k in DL.KICH_BAN.doc() if not k.get("tam")])
post("/deployos/trienkhai/may/xoa", {"id": ids[0]}); kt("xoa may go khoi nhom", ids[0] not in DL.NHOM_MAY.doc()[0]["may"])
import shutil; shutil.rmtree(TMP, ignore_errors=True)
print(f"TONG: {len(DAT)} dat, {len(HONG)} hong")
sys.exit(1 if HONG else 0)
