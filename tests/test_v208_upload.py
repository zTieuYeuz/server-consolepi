"""2.0.8 V1-4 + V6-6: nginx mac dinh body nho; MOI route tai len (doc request.files) phai duoc nang dung muc o nginx; khong route khac bi nang 8g."""
import os
import re
import subprocess
import sys

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NG = open(os.path.join(GOC, "config", "nginx-console-pi.conf"), encoding="utf-8").read()
SO_MB = {"m": 1, "g": 1024}

# Gioi han toi thieu moi route tai len can (MB): route nao khong liet ke thi can >= 16 (mac dinh) ... nhung la anh OS/ISO/phan mem thi 8 GB
CAN_MB = {"/settings/nap-sao-luu": 64, "/uem/may/<mid>/duyet-file/tai-len": 200, "/gopy": 64, "/nettools/ifthen/import": 1,
          "/deployos/wizard/<ma>/<int:buoc>": 4}
ANH_LON = ("/storage/len", "/deployos/console/", "/deployos/os/", "/deployos/drivers/", "/deployos/ungdung/", "/deployos/font/")


def _mb(v):
    m = re.match(r"(\d+)([mg])$", v)
    return int(m.group(1)) * SO_MB[m.group(2)]


def _locations():
    """[(kieu, mau, gioi_han_mb hoac None)] theo thu tu trong tep (chi location ~ regex va = exact, du cho mo hinh khop)."""
    ra = []
    for m in re.finditer(r"^    location (~ |= )?(\S+) \{(.*?)\n    \}", NG, re.S | re.M):
        kieu, mau, than = (m.group(1) or "").strip(), m.group(2), m.group(3)
        g = re.search(r"client_max_body_size\s+(\d+[mg]);", than)
        ra.append((kieu or "prefix", mau, _mb(g.group(1)) if g else None))
    return ra


def gioi_han_cua(duong):
    mac_dinh = _mb(re.search(r"^    client_max_body_size\s+(\d+[mg]);", NG, re.M).group(1))
    locs = _locations()
    for kieu, mau, gh in locs:
        if kieu == "=" and mau == duong:
            return gh or mac_dinh
    for kieu, mau, gh in locs:
        if kieu == "~" and re.search(mau.replace("(?<", "(?P<"), duong):
            return gh or mac_dinh
    return mac_dinh


def _tai_len():
    return [x for x in open(os.path.join(GOC, "tests", "hop-dong", "route-tai-len.txt"), encoding="utf-8").read().split("\n") if x]


def _vi_du(route):
    return re.sub(r"<(?:int:)?[^>]+>", "x1", route)


def test_danh_sach_route_tai_len_khop_ma_hien_tai(tmp_path):
    ra = tmp_path / "up.txt"
    r = subprocess.run([sys.executable, os.path.join(GOC, "tools", "xuat-route-upload.py"), str(ra)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr[-400:]
    assert ra.read_text(encoding="utf-8") == open(os.path.join(GOC, "tests", "hop-dong", "route-tai-len.txt"), encoding="utf-8").read(), \
        "route tai len doi: cap nhat tests/hop-dong/route-tai-len.txt VA nginx (khoi tai len)"


def test_mac_dinh_nho_va_moi_route_tai_len_du_cho():
    assert gioi_han_cua("/login") <= 16 and gioi_han_cua("/api/tiendo/ketthuc") <= 16 and gioi_han_cua("/uem/agent/bao-cao") <= 16
    for route in _tai_len():
        gh = gioi_han_cua(_vi_du(route))
        if route.startswith(ANH_LON):
            assert gh >= 8 * 1024, (route, gh)                       # anh OS/ISO/phan mem: 8 GB
        else:
            assert gh >= CAN_MB[route], (route, gh)                  # khong co trong CAN_MB => them vao bang va khoi nginx tuong ung
            assert gh <= 1024, route                                # route trung binh khong duoc mo 8 GB


def test_khong_route_nao_ngoai_danh_sach_bi_nang_len_8g():
    """Moi location nginx nang >256 MB chi duoc khop cac route TAI LEN that (danh sach hop dong)."""
    tai_len = _tai_len()
    for kieu, mau, gh in _locations():
        if gh and gh > 256 and kieu == "~":
            for ung_vien in ("/login", "/api/tiendo/ketthuc", "/uem/agent/bao-cao", "/settings", "/nettools/tftp/bat", "/deployos/os", "/deployos/os/a/xoa",
                             "/storage", "/deployos/font/a/xoa", "/deployos/ungdung/a/xoa"):
                assert not re.search(mau.replace("(?<", "(?P<"), ung_vien), (mau, ung_vien)
            for ung_vien in tai_len:
                if gioi_han_cua(_vi_du(ung_vien)) >= 8 * 1024:
                    assert any(re.search(m2.replace("(?<", "(?P<"), _vi_du(ung_vien)) for k2, m2, g2 in _locations() if k2 == "~" and g2 and g2 >= 8192)
    assert re.search(r"^    client_max_body_size\s+16m;", NG, re.M) and not re.search(r"^    client_max_body_size\s+8g;", NG, re.M)


def test_flask_tu_choi_file_qua_lon_truoc_khi_doc(monkeypatch):
    s = open(os.path.join(GOC, "src", "consolesystem", "features", "uem", "uem_trang_b.py"), encoding="utf-8").read()
    i = s.index("def uem_tai_len")
    j = s.index("request.files.get", i)
    assert s.index("request.content_length", i) < s.index('request.form.get("cha")', i) < j        # kiem Content-Length TRUOC khi parse form/files
