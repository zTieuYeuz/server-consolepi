"""Gom du lieu ve MOT thu muc (/var/lib/console-system): deploy/storage lien ket sang bo cuc cu, WiFi da luu, token o /etc."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from consolesystem.core import gomdulieu as G  # noqa: E402


def _viet(p, s="x"):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(s)


def test_gom_doi_cho_lien_ket_wifi_va_token(tmp_path):
    cu, goc, etc = tmp_path / "console-pi", tmp_path / "console-system", tmp_path / "etc"
    _viet(str(cu / "deploy" / "os" / "win11.wim"), "anh windows")
    _viet(str(cu / "storage" / "a.txt"))
    os.makedirs(goc / "secrets")
    os.symlink(cu / "deploy", goc / "deploy")
    os.symlink(cu / "storage", goc / "storage")
    _viet(str(etc / "wpa_supplicant" / "wpa_supplicant-wlan0.conf"), "network={ssid=\"Cty\"}")
    _viet(str(etc / "cloudflared" / "console-pi-token"), "T" * 60)
    _viet(str(etc / "tailscale-console-pi-authkey"), "tskey")
    ra = G.gom(str(goc), etc=str(etc))
    assert len(ra) == 5, ra
    # deploy/storage la thu muc THAT trong thu muc du lieu; cho cu thanh lien ket nguoc
    assert not os.path.islink(goc / "deploy") and open(goc / "deploy" / "os" / "win11.wim").read() == "anh windows"
    assert os.path.islink(cu / "deploy") and os.path.realpath(cu / "deploy") == str(goc / "deploy")
    # wifi: ban that trong secrets, /etc la lien ket (wpa_supplicant van doc duoc dung duong cu)
    w = etc / "wpa_supplicant" / "wpa_supplicant-wlan0.conf"
    assert os.path.islink(w) and open(w).read() == 'network={ssid="Cty"}'
    assert os.path.isfile(goc / "secrets" / "he-thong" / "wifi" / "wpa_supplicant-wlan0.conf")
    # token: chuyen han vao secrets (chuong trinh doc thang o day), khong de lai o /etc
    assert open(goc / "secrets" / "cloudflared-token").read() == "T" * 60 and not os.path.exists(etc / "cloudflared" / "console-pi-token")
    assert oct(os.stat(goc / "secrets" / "tailscale-authkey").st_mode)[-3:] == "600"
    assert G.gom(str(goc), etc=str(etc)) == []                       # chay lai: khong lam gi


def test_may_moi_khoi_phuc_sao_luu_tao_lai_lien_ket_wifi(tmp_path):
    goc, etc = tmp_path / "console-system", tmp_path / "etc"
    _viet(str(goc / "secrets" / "he-thong" / "wifi" / "wpa_supplicant-wlan0.conf"), "da luu")
    os.makedirs(goc / "deploy")
    G.gom(str(goc), etc=str(etc))
    assert open(etc / "wpa_supplicant" / "wpa_supplicant-wlan0.conf").read() == "da luu"
    assert not os.path.islink(goc / "deploy")
