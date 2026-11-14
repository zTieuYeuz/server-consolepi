"""2.0.8 V5-3: pcap - ten cong + bo loc BPF duoc kiem, khong chen duoc tuy chon tcpdump; gioi han kich thuoc; chuan hoa ten tep."""
import os
import sys
import time

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


class FakeProc:
    pid = 4242

    def __init__(self):
        self._rc = None

    def poll(self):
        return self._rc

    def send_signal(self, s):
        self._rc = 0

    def wait(self, timeout=None):
        return 0

    def kill(self):
        self._rc = -9


@pytest.fixture
def PC(tmp_path, monkeypatch):
    from nettools import pcap as PC
    monkeypatch.setattr(PC, "get_capture_dir", lambda: str(tmp_path))
    monkeypatch.setattr(PC, "free_space_mb", lambda d: 10 ** 6)
    PC.CAPTURE_STATE.update(proc=None, pid=None, file=None, started=None)
    goi = []
    monkeypatch.setattr(PC.subprocess, "Popen", lambda cmd, **kw: (goi.append(cmd) or FakeProc()))
    PC._goi = goi
    return PC


def test_chay_binh_thuong_loc_la_mot_doi_so_sau_dau_gach_gach(PC):
    r = PC.start_capture("eth0", "host 192.168.1.5 and tcp port 80", 30)
    assert r["ok"], r
    cmd = PC._goi[-1]
    if cmd[0] == "prlimit":
        assert cmd[1] == "--fsize=%d" % (PC.MAX_FILE_MB * 1024 * 1024)       # P1: gioi han kich thuoc tep o nhan, khong dung -C/-W (doi ten tep)
        cmd = cmd[2:]
    assert "-W" not in cmd and "-C" not in cmd
    assert cmd[:3] == ["tcpdump", "-i", "eth0"] and cmd[-2:] == ["--", "host 192.168.1.5 and tcp port 80"] and cmd.count("-w") == 1
    PC.stop_capture()
    r = PC.start_capture("eth0.100", "tcp[13] & 2 != 0", 30)                               # cu phap BPF thong dung van duoc
    assert r["ok"], r


@pytest.mark.parametrize("loc", ["-z /bin/sh -G 1", "port 80 -w /etc/cron.d/x", "host x; rm -rf /", "$(id)", "a`id`", "x" * 201, "port 80\nhost 1.1.1.1"])
def test_loc_xau_bi_tu_choi_khong_chay_tcpdump(PC, loc):
    r = PC.start_capture("eth0", loc, 30)
    assert not r["ok"] and not PC._goi


@pytest.mark.parametrize("iface", ["-w/etc/passwd", "eth0 -z x", "../x", "", "a" * 16, "eth0;id"])
def test_ten_cong_xau_bi_tu_choi(PC, iface):
    r = PC.start_capture(iface, "", 30)
    assert not r["ok"] and not PC._goi


def test_thoi_luong_sai_khong_gay_500(PC):
    assert not PC.start_capture("eth0", "", "abc")["ok"]


def test_tu_dung_khi_vuot_gioi_han_kich_thuoc(PC, tmp_path, monkeypatch):
    monkeypatch.setattr(PC, "MAX_FILE_MB", 0)                       # moi tep co noi dung deu vuot
    r = PC.start_capture("eth0", "", 600)
    assert r["ok"]
    open(r["file"], "wb").write(b"x" * 10)
    het = time.time() + 6
    while time.time() < het and PC.CAPTURE_STATE.get("pid"):
        time.sleep(0.2)
    assert PC.CAPTURE_STATE.get("pid") is None                       # tu dung khi vuot gioi han, khong cho het 600 giay


def test_convert_khong_theo_duong_dan(PC, tmp_path):
    (tmp_path / "ok.pcap").write_bytes(b"x")
    for xau in ("../ok.pcap", "/etc/passwd.pcap", "a/../ok.pcap"):
        r = PC.convert_to_text(xau)
        assert not r["ok"], xau


def test_N2_xuong_dong_cuoi_khong_lot_qua(PC):
    assert not PC.start_capture("eth0\n", "", 30)["ok"] and not PC._goi


def test_P1_co_prlimit_thi_boc_va_khong_co_thi_van_chay(PC, monkeypatch):
    monkeypatch.setattr(PC.shutil, "which", lambda n: "/usr/bin/prlimit")
    assert PC.start_capture("eth0", "", 30)["ok"] and PC._goi[-1][0] == "prlimit"
    PC.stop_capture()
    monkeypatch.setattr(PC.shutil, "which", lambda n: None)
    assert PC.start_capture("eth0", "", 30)["ok"] and PC._goi[-1][0] == "tcpdump"
    PC.stop_capture()


def test_P2_convert_gioi_han_so_goi(PC, tmp_path, monkeypatch):
    (tmp_path / "ok.pcap").write_bytes(b"x")
    goi = []
    monkeypatch.setattr(PC.subprocess, "run", lambda cmd, **kw: goi.append(cmd))
    assert PC.convert_to_text("ok.pcap")["ok"]
    assert goi[-1][goi[-1].index("-c") + 1] == str(PC.MAX_GOI_TEXT)
