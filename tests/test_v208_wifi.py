"""2.0.8 V5-4: doi WiFi - PSK khong ra /tmp 0644, thong tin kiem tra ky tu, that bai thi hoan tac DUNG che do truoc (client -> noi lai, AP -> AP)."""
import os
import stat
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


@pytest.fixture
def NW(monkeypatch):
    from consolesystem.features.network import network as NW
    monkeypatch.setattr(NW.time, "sleep", lambda s: None)
    return NW


class KQ:
    def __init__(self, out="", rc=0):
        self.stdout, self.returncode, self.stderr = out, rc, ""


def test_kiem_tra_ky_tu(NW):
    ok = NW.thong_tin_wifi_hop_le
    assert ok("Cong ty 5G", "matkhau-12345") is None and ok("a", "p\\ss word 12") is None            # ky tu hop le (ke ca gach cheo nguoc, dau cach)
    for ssid, pw in (('a"b', "12345678"), ("ab", 'x"y12345'), ("a\nb", "12345678"), ("ab", "1234567\n8"), ("", "12345678"), ("a" * 33, "12345678"),
                     ("ab", "1234567"), ("ab", "x" * 64), (None, "12345678"), ("ab", None), ("a\x00b", "12345678")):
        assert ok(ssid, pw), (ssid, pw)


def test_psk_khong_o_tmp_ten_co_dinh_va_quyen_0600_va_bi_xoa(NW, monkeypatch):
    thay = {}
    monkeypatch.setattr(NW, "cong_wifi", lambda: "wlan0")

    def lenh(cmd, timeout=15, **kw):
        if cmd[0] == "wpa_supplicant":
            p = cmd[cmd.index("-c") + 1]
            thay["path"] = p
            thay["mode"] = stat.S_IMODE(os.stat(p).st_mode)
            thay["nd"] = open(p).read()
        if cmd[:2] == ["wpa_cli", "-i"]:
            return KQ("wpa_state=COMPLETED")
        return KQ()
    monkeypatch.setattr(NW, "_lenh", lenh)
    assert NW.test_wifi_connection("MangA", "matkhau-12345") is True
    assert thay["path"] != "/tmp/wpa_test.conf" and not thay["path"].startswith("/tmp/wpa_test")
    assert thay["mode"] == 0o600 and 'psk="matkhau-12345"' in thay["nd"]
    assert not os.path.exists(thay["path"])                                                         # xoa ngay sau khi wpa_supplicant da doc


def test_that_bai_khi_truoc_do_la_client_thi_noi_lai_mang_cu_khong_bat_ap(NW, monkeypatch):
    monkeypatch.setattr(NW, "cong_wifi", lambda: "wlan0")
    goi = []

    def lenh(cmd, timeout=15, **kw):
        goi.append(list(cmd))
        if cmd[:3] == ["iw", "dev", "wlan0"]:
            return KQ("Interface wlan0\n\ttype managed\n\tssid MangCu\n")
        if cmd[:2] == ["wpa_cli", "-i"]:
            # lan thu mang MOI (wpa_supplicant -B -c) khong len; sau khi restart unit he thong thi noi lai duoc
            return KQ("wpa_state=COMPLETED" if ["systemctl", "restart", "wpa_supplicant@wlan0"] in goi else "wpa_state=SCANNING")
        return KQ()
    monkeypatch.setattr(NW, "_lenh", lenh)
    monkeypatch.setattr(NW, "get_net_status", lambda: ("", "", "10.1.1.9"))
    NW._switch_worker("MangMoi", "matkhau-12345", False)
    assert NW.WIFI_STATUS["state"] == "failed" and "MangCu" in NW.WIFI_STATUS["msg"] and NW.WIFI_STATUS["ip"] == "10.1.1.9"
    assert ["systemctl", "start", "hostapd"] not in goi                                             # KHONG bat AP khi da noi lai duoc mang cu


def test_that_bai_khi_truoc_do_la_ap_thi_ve_ap(NW, monkeypatch):
    monkeypatch.setattr(NW, "cong_wifi", lambda: "wlan0")
    goi = []

    def lenh(cmd, timeout=15, **kw):
        goi.append(list(cmd))
        if cmd[:3] == ["iw", "dev", "wlan0"]:
            return KQ("Interface wlan0\n\ttype AP\n\tssid ConsolePi\n")
        if cmd[:2] == ["ip", "-4"]:
            return KQ("inet %s/24" % NW.AP_IP)
        return KQ("wpa_state=SCANNING")
    monkeypatch.setattr(NW, "_lenh", lenh)
    NW._switch_worker("MangMoi", "matkhau-12345", False)
    assert NW.WIFI_STATUS["state"] == "failed" and "AP ConsolePi" in NW.WIFI_STATUS["msg"] and ["systemctl", "start", "hostapd"] in goi


def test_thong_tin_xau_khong_dung_vao_mang(NW, monkeypatch):
    goi = []
    monkeypatch.setattr(NW, "_lenh", lambda cmd, timeout=15, **kw: (goi.append(cmd) or KQ()))
    NW._switch_worker('x"\nnetwork={', "matkhau-12345", False)
    assert NW.WIFI_STATUS["state"] == "failed" and goi == []                                       # khong ha AP, khong chay lenh nao
