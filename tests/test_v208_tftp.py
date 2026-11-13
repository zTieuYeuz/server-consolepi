"""2.0.8 V5-2: TFTP chi nghe cong da chon (mac dinh tru cong ra Internet), tu tat khi nhan roi, gioi han dung luong, gia han; --create giu nguyen."""
import importlib.util
import json
import os
import runpy
import stat
import subprocess
import sys
import tempfile
import threading
import time

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(GOC, "src")
sys.path.insert(0, SRC)


def _chay():
    sp = importlib.util.spec_from_file_location("tftp_chay", os.path.join(SRC, "scripts", "tftp-chay.py"))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def test_lenh_va_dia_chi():
    C = _chay()
    assert C.dia_chi_hop_le(["192.168.1.5", "0.0.0.0", "300.1.1.1", "a;b", "10.0.0.1", None]) == ["192.168.1.5", "10.0.0.1"]
    a = C.lenh_tftpd("10.0.0.1", "/d")
    assert "--create" in a and "--secure" in a and "10.0.0.1:69" in a and "0.0.0.0" not in " ".join(a)       # --create giu, khong 0.0.0.0


def test_quyet_dinh_tu_tat():
    C = _chay()
    t = 10000.0
    assert C.quyet_dinh(t, t - 100, 1000, 10 ** 10) is None
    assert "Nhàn rỗi" in C.quyet_dinh(t, t - 3601, 1000, 10 ** 10)
    assert C.quyet_dinh(t, t - 3599, 1000, 10 ** 10) is None                         # chua du 60 phut
    assert "vượt giới hạn" in C.quyet_dinh(t, t, C.TOI_DA_BYTE + 1, 10 ** 10)
    assert "gần đầy" in C.quyet_dinh(t, t, 1, 1000)


def test_dang_chep_nhan_ra_giao_dich():
    C = _chay()
    chi_nghe = 'udp UNCONN 0 0 10.0.0.1:69 0.0.0.0:* users:(("in.tftpd",pid=1,fd=3))\n'
    dang = chi_nghe + 'udp ESTAB 0 0 10.0.0.1:41234 10.0.0.9:2001 users:(("in.tftpd",pid=2,fd=4))\n'
    assert not C.dang_chep(chi_nghe) and C.dang_chep(dang)
    assert not C.dang_chep('udp UNCONN 0 0 0.0.0.0:68 0.0.0.0:* users:(("dhclient",pid=3,fd=6))\n')


def test_tien_trinh_that_tu_tat_khi_nhan_roi(tmp_path):
    """Chay tftp-chay.py that voi in.tftpd gia: moi dia chi 1 tien trinh, --create duoc truyen, nhan roi 2s thi thoat 0 va don tien trinh."""
    goc = tmp_path / "tftp"
    goc.mkdir()
    ghi = tmp_path / "args.txt"
    gia = tmp_path / "in.tftpd"
    gia.write_text('#!/bin/sh\necho "$@" >> %s\nexec sleep 60\n' % ghi)
    gia.chmod(gia.stat().st_mode | stat.S_IXUSR)
    ch = tmp_path / "ch.json"
    ch.write_text(json.dumps({"dia_chi": ["127.0.0.2", "127.0.0.3"], "goc": str(goc)}))
    env = dict(os.environ, CS_TFTP_CAU_HINH=str(ch), CS_TFTP_TRANG_THAI=str(tmp_path / "tt.json"), CS_TFTP_GIA_HAN=str(tmp_path / "gh"),
               CS_TFTP_NHAN_ROI="2", CS_TFTP_NHIP="0.3", CS_TFTPD=str(gia))
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(SRC, "scripts", "tftp-chay.py")], env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    assert time.time() - t0 < 20
    dong = ghi.read_text().splitlines()
    assert len(dong) == 2 and all("--create" in x for x in dong) and {x.split("--address ")[1].split(" ")[0] for x in dong} == {"127.0.0.2:69", "127.0.0.3:69"}
    tt = json.loads((tmp_path / "tt.json").read_text())
    assert tt["nghe"] == [] and "Nhàn rỗi" in tt["ly_do_tat"]
    assert subprocess.run(["pgrep", "-f", str(gia)], capture_output=True).returncode != 0                 # khong con tien trinh mo coi


def test_gia_han_keo_dai_va_doi_file_tinh_la_hoat_dong(tmp_path):
    goc = tmp_path / "tftp"
    goc.mkdir()
    gia = tmp_path / "in.tftpd"
    gia.write_text("#!/bin/sh\nexec sleep 60\n")
    gia.chmod(0o755)
    ch = tmp_path / "ch.json"
    ch.write_text(json.dumps({"dia_chi": ["127.0.0.2"], "goc": str(goc)}))
    env = dict(os.environ, CS_TFTP_CAU_HINH=str(ch), CS_TFTP_TRANG_THAI=str(tmp_path / "tt.json"), CS_TFTP_GIA_HAN=str(tmp_path / "gh"),
               CS_TFTP_NHAN_ROI="3", CS_TFTP_NHIP="0.3", CS_TFTPD=str(gia))
    p = subprocess.Popen([sys.executable, os.path.join(SRC, "scripts", "tftp-chay.py")], env=env)
    try:
        t0 = time.time()
        while time.time() - t0 < 5:                                   # co file moi/gia han moi 1s trong 5s -> khong duoc tat som
            (goc / "x.cfg").write_text(str(time.time()))
            time.sleep(1)
            assert p.poll() is None, "tu tat khi dang co hoat dong"
        assert p.wait(timeout=20) == 0                                 # het hoat dong -> tu tat binh thuong
    finally:
        if p.poll() is None:
            p.kill()


# ---- phia dashboard
def test_bat_chi_nghe_cong_da_chon_va_mac_dinh_tru_cong_ra_net(monkeypatch, tmp_path):
    from nettools import tftp_server as T
    ds = [{"iface": "eth0", "ip": "192.168.1.5"}, {"iface": "eth1", "ip": "10.9.9.1"}]
    monkeypatch.setattr(T, "ip_theo_giao_dien", lambda: ds)
    monkeypatch.setattr(T, "cong_ra_internet", lambda: {"eth0"})
    assert T.cong_nghe_mac_dinh() == ["10.9.9.1"]                                    # tru cong ra Internet
    monkeypatch.setattr(T, "cong_ra_internet", lambda: set())
    assert T.cong_nghe_mac_dinh() == []                                              # khong nhan biet duoc -> khong tich san
    monkeypatch.setattr(T, "TFTP_ROOT", str(tmp_path / "root"))
    monkeypatch.setattr(T, "FILE_CAU_HINH", str(tmp_path / "ch.json"))
    monkeypatch.setattr(T, "FILE_GIA_HAN", str(tmp_path / "gh"))
    monkeypatch.setattr(T, "FILE_TRANG_THAI", str(tmp_path / "tt.json"))
    monkeypatch.setattr(T, "STATE_FLAG", str(tmp_path / "flag"))
    monkeypatch.setattr(T, "da_cai_dat", lambda: True)
    goi = []
    monkeypatch.setattr(T, "_sh", lambda c, timeout=15: (goi.append(c) or (True, "")))
    ok, tb = T.bat_tftp([])
    assert not ok and not goi                                                        # khong chon cong -> khong bat
    ok, tb = T.bat_tftp(["8.8.8.8", "10.9.9.1"])                                     # IP khong phai cua may bi loai
    assert ok and json.load(open(tmp_path / "ch.json"))["dia_chi"] == ["10.9.9.1"] and ["systemctl", "start", T.DON_VI_SYSTEMD] in goi
    ok, _ = T.gia_han()
    assert ok and (tmp_path / "gh").exists()
    json.dump({"nghe": ["10.9.9.1"], "het_han": time.time() + 1800, "ly_do_tat": ""}, open(tmp_path / "tt.json", "w"))
    st = T.trang_thai()
    assert st["nghe"] == ["10.9.9.1"] and 28 <= st["con_lai_phut"] <= 30


def test_trang_tftp_hien_cong_nghe_va_nut_gia_han(monkeypatch, tmp_path):
    os.environ.setdefault("CONSOLE_PI_LOG", tempfile.mkdtemp(prefix="cs-test-log-"))
    cu = os.getcwd()
    os.chdir(SRC)
    goc = threading.Thread.start
    threading.Thread.start = lambda self: None
    try:
        app = runpy.run_path(os.path.join(SRC, "app.py"), run_name="dev")["app"]
    finally:
        threading.Thread.start = goc
        os.chdir(cu)
    from nettools import tftp_server as T
    monkeypatch.setattr(T, "ip_theo_giao_dien", lambda: [{"iface": "eth0", "ip": "192.168.1.5"}, {"iface": "eth1", "ip": "10.9.9.1"}])
    monkeypatch.setattr(T, "cong_ra_internet", lambda: {"eth0"})
    monkeypatch.setattr(T, "da_cai_dat", lambda: True)
    monkeypatch.setattr(T, "dang_bat", lambda: False)
    c = app.test_client()
    with c.session_transaction() as s:
        s["user"] = "root"
    h = c.get("/nettools/tftp", environ_overrides={"REMOTE_ADDR": "192.168.1.50"}).get_data(as_text=True)
    assert 'name="cong" value="10.9.9.1" checked' in h and 'name="cong" value="192.168.1.5">' in h        # tru cong ra Internet khong tich san
    monkeypatch.setattr(T, "dang_bat", lambda: True)
    monkeypatch.setattr(T, "trang_thai", lambda: {"nghe": ["10.9.9.1"], "con_lai_phut": 42, "ly_do_tat": ""})
    h = c.get("/nettools/tftp", environ_overrides={"REMOTE_ADDR": "192.168.1.50"}).get_data(as_text=True)
    assert "10.9.9.1" in h and "42 phút" in h and "/nettools/tftp/gia-han" in h


def test_don_vi_dung_wrapper_va_giu_create():
    s = open(os.path.join(GOC, "systemd", "console-system-tftp.service"), encoding="utf-8").read()
    assert "tftp-chay.py" in s and "0.0.0.0" not in [x for x in s.splitlines() if x.startswith("ExecStart=")][0]
    assert "ExecStopPost=" in s and "console-system-tftp.flag" in s


def test_B3_nhip_kiem_dung_luong_5_giay():
    assert _chay().NHIP <= 5.0
