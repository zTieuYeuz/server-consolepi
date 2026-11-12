"""2.0.7 cum 3: khung mat khau dung chung - cac trang remote dung o password + nut Hien/An, khong con 'o_mat_khau(' ro ra, khong co o mat khau dang chu."""
import json
import os
import runpy
import sys
import threading

os.environ.setdefault("CONSOLE_PI_LOG", __import__("tempfile").mkdtemp(prefix="cs-test-log-"))
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)
os.chdir(SRC)
_goc = threading.Thread.start
threading.Thread.start = lambda self: None if getattr(getattr(self, "_target", None), "__name__", "") in ("tu_dang_ky_nen", "_driver_nen", "vong", "vong_kiem_tra_nen") else _goc(self)
app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
c = app.test_client()
H = {"X-ConsolePi-Local": "1"}
kq = {}
for ten, duong, ten_o in (("ssh", "/ssh", "password"), ("rdp", "/remote-desktop", "mk"), ("rustdesk", "/rustdesk", "rd-mk")):
    h = c.get(duong, headers=H).get_data(as_text=True)
    kq[ten + "_khong_ro_ham"] = "o_mat_khau(" not in h and "@@MK@@" not in h
    kq[ten + "_o_password"] = ('name="%s"' % ten_o in h or 'id="%s"' % ten_o in h) and 'type="text" id="rd-mk"' not in h
    if ten != "rustdesk":
        kq[ten + "_nut_hien"] = ">Hiện</button>" in h and "mk-khung" in h
h = c.get("/remote", headers=H).get_data(as_text=True)
kq["remote_khong_ro_ham"] = "o_mat_khau(" not in h
print("KETQUA " + json.dumps(kq, ensure_ascii=False))
