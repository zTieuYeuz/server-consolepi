"""2.0.8 X1: ho XSS sua THEO NGU CANH. (a) chuoi JS trong thuoc tinh su kien -> data-hoi; (b) JSON trong <script> thoat < > &; (c) esc() cua phien.JS.html thoat ca " va ';
(d) chip SSID + tieu de Console thoat HTML; V4-1 option.textContent khong di vao innerHTML. Co test hanh vi (Flask that / node that), khong chi grep."""
import os
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import threading

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(GOC, "src")
sys.path.insert(0, SRC)
HAI = "x');alert(1);x"                          # ten file / SSID doc hai


def _doc(rel):
    return open(os.path.join(SRC, "consolesystem", rel), encoding="utf-8").read()


def test_khong_con_confirm_noi_chuoi_du_lieu_trong_thuoc_tinh():
    """Moi onsubmit/onclick="...confirm('...{bien}...')" (noi chuoi du lieu vao JS trong thuoc tinh) deu bi cam; dung data-hoi + this.dataset.hoi."""
    mau = re.compile(r"""on(?:submit|click|change)=\\?"[^"]*confirm\(\\?'[^'"]*(?:\{[^}]*\}|\{\{)""")
    cho_phep = ("len(ds)", "PI_IP", "HOI_XOA_FW", "so_font", "'Gỡ khóa AP?'", "commands|length")        # hang so / so nguyen / mau da duyet (khong phai du lieu ngoai)
    xau = []
    for d, _ds, fs in os.walk(os.path.join(SRC)):
        for f in fs:
            if f.endswith((".py", ".html")):
                for dong in open(os.path.join(d, f), encoding="utf-8").read().splitlines():
                    if mau.search(dong) and not any(c in dong for c in cho_phep):
                        xau.append("%s: %s" % (f, dong.strip()[:90]))
    assert not xau, xau


@pytest.fixture(scope="module")
def app():
    os.environ.setdefault("CONSOLE_PI_LOG", tempfile.mkdtemp(prefix="cs-test-log-"))
    cu = os.getcwd()
    os.chdir(SRC)
    goc = threading.Thread.start
    threading.Thread.start = lambda self: None
    try:
        return runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
    finally:
        threading.Thread.start = goc
        os.chdir(cu)


def test_trang_storage_ten_file_doc_hai_khong_thoat_duoc_khoi_chuoi(app, monkeypatch, tmp_path):
    from consolesystem.features.files import storage
    (tmp_path / HAI).write_text("x")
    monkeypatch.setattr(storage, "LOCAL_DIR", str(tmp_path))
    c = app.test_client()
    with c.session_transaction() as s:
        s["user"] = "root"
    r = c.get("/storage", environ_overrides={"REMOTE_ADDR": "192.168.1.50"})
    h = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "confirm('Xóa x" not in h and "confirm(this.dataset.hoi)" in h                      # khong con noi chuoi vao JS
    assert 'data-hoi="Xóa x\');alert(1);x?"' in h                                         # du lieu nam trong thuoc tinh data-hoi dang van ban thuan (dau " da thoat)
    assert "x');alert(1);//?')" not in h


@pytest.mark.skipif(not shutil.which("node"), reason="khong co node")
def test_esc_cua_phien_thoat_ca_nhay_kep_va_nhay_don(tmp_path):
    h = _doc("assets/features/terminal/phien.JS.html")
    m = re.search(r"function esc\(s\)\{.*?\}   /\*", h)
    assert m, "khong thay esc()"
    # chay ham THAT voi mot DOM gia toi thieu (textContent -> innerHTML thoat & < > nhu trinh duyet)
    mk = ("var document={createElement:function(){var d={set textContent(v){this._t=v;},get innerHTML(){return String(this._t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}};return d;}};\n"
          + m.group(0)[:-3] + "\nconsole.log(esc('a\"b\\'c<d>'));")
    f = tmp_path / "t.js"
    f.write_text(mk)
    r = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=20)
    assert r.stdout.strip() == "a&quot;b&#39;c&lt;d&gt;", (r.stdout, r.stderr)


def test_json_trong_script_khong_cat_duoc_the_script():
    s = _doc("features/deploy_os/dosui_kho.py")
    assert '.replace("<", "\\\\u003c").replace(">", "\\\\u003e").replace("&", "\\\\u0026")' in s
    import json
    j = json.dumps([{"tim": "</script><img src=x onerror=alert(1)>"}], ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    assert "<" not in j and ">" not in j and json.loads(j)[0]["tim"].startswith("</script>")        # van doc lai dung gia tri goc


def test_chip_ssid_va_tieu_de_console_duoc_thoat():
    assert '_esc_chip(ssid)' in _doc("web/layout.py") and '_esc_chip(ssid or "ConsolePi")' in _doc("web/layout.py")
    assert 'title=f"Console: {_esc(label)}"' in _doc("web/home.py")


def test_loc_uem_khong_dung_innerhtml_voi_van_ban_option():
    s = _doc("features/uem/uem_trang.py")
    assert "b.innerHTML = w.querySelector" not in s and "tx.textContent" in s
