"""2.0.8 V1-1 (B1): manifest he thong config/hethong.json la nguon chung. install.sh doc tu do va ra DANH SACH Y HET nhu truoc; du phong khi manifest hong."""
import sys
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "src"))
import json
import os
import re
import subprocess

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MF = os.path.join(GOC, "config", "hethong.json")
INSTALL = open(os.path.join(GOC, "install.sh"), encoding="utf-8").read()

# Danh sach cua install.sh o 2.0.7 (1ceb346) - bat bien: cai moi 2.0.8 phai bat DUNG tung ay don vi
BAT_2_0_7 = ["console-system-dashboard", "console-system-term-local", "console-system-term-ssh", "console-system-term-phien", "bt-pan0", "dnsmasq-bt",
             "bt-agent", "bt-nap", "wifi-fallback.timer", "lldpd", "bluetooth", "avahi-daemon", "nginx", "wpa_supplicant@wlan0", "console-system-selftest",
             "console-system-nang-cap-phuc-hoi"]
KIOSK_2_0_7 = ["console-system-kiosk", "console-system-kiosk-helper"]


def _mang(ten):
    m = re.search(r"^%s=\(\s*(.*?)\)" % ten, INSTALL, re.M | re.S)
    return m.group(1).split()


def _khoi_bat():
    i = INSTALL.index("ENABLE_LIST=(")
    j = INSTALL.index("for s in \"${ENABLE_LIST[@]}\"")
    return INSTALL[i:j]


def _chay_khoi(mf_duong, man_hinh, nhat_ky=None):
    kb = ("set -u\nwarn(){ echo \"WARN $*\" >&2; }\nsystemctl(){ echo \"SYSTEMCTL $*\" >> \"$LOGF\"; }\nrm(){ echo \"RM $*\" >> \"$LOGF\"; }\n"
          "SRC_DIR='%s'\nWANT_SCREEN=%s\n%s\n"
          'printf "%%s\\n" "${ENABLE_LIST[@]}"\n') % (GOC, man_hinh, _khoi_bat().replace('"$SRC_DIR/config/hethong.json"', '"%s"' % mf_duong))
    return subprocess.run(["bash", "-c", kb], capture_output=True, text=True, timeout=30, env=dict(os.environ, LOGF=nhat_ky or os.devnull))


def test_manifest_dung_2_0_7():
    d = json.load(open(MF, encoding="utf-8"))
    assert d["don_vi"]["bat"] == BAT_2_0_7 and d["don_vi"]["bat_khi_co_man_hinh"] == KIOSK_2_0_7
    assert d["don_vi"]["go"] == []


def test_goi_apt_manifest_trung_install_sh():
    d = json.load(open(MF, encoding="utf-8"))["goi_apt"]
    assert d["core"] == _mang("PKGS_CORE") and d["man_hinh"] == _mang("PKGS_SCREEN") and d["trien_khai"] == _mang("PKGS_DEPLOY")


def test_install_sh_doc_manifest_ra_dung_danh_sach_cu():
    r = _chay_khoi(MF, "no")
    assert r.returncode == 0 and r.stdout.split() == BAT_2_0_7, r.stderr
    r = _chay_khoi(MF, "yes")
    assert r.stdout.split() == BAT_2_0_7 + KIOSK_2_0_7                              # co man hinh: them kiosk, dung thu tu cu


def test_du_phong_va_go_don_vi(tmp_path):
    r = _chay_khoi(str(tmp_path / "khong-co.json"), "yes")                          # manifest mat -> danh sach du phong trong install.sh, canh bao
    assert r.stdout.split() == BAT_2_0_7 + KIOSK_2_0_7 and "WARN" in r.stderr
    mf = tmp_path / "m.json"
    d = json.load(open(MF, encoding="utf-8"))
    d["don_vi"]["go"] = ["console-system-cu"]
    mf.write_text(json.dumps(d))
    nk = tmp_path / "nk.txt"
    r = _chay_khoi(str(mf), "no", str(nk))
    log = nk.read_text()
    assert "SYSTEMCTL disable --now console-system-cu" in log and "RM -f /etc/systemd/system/console-system-cu.service" in log
    assert r.stdout.split()[-1] == "console-system-nang-cap-phuc-hoi"


def test_manifest_di_theo_goi_ota():
    from consolesystem.core import phathanh as P
    import tempfile
    src = tempfile.mkdtemp()
    os.makedirs(os.path.join(src, "src"))
    open(os.path.join(src, "VERSION"), "w").write("9.9.9\n")
    import shutil
    shutil.copytree(os.path.join(GOC, "config"), os.path.join(src, "config"))
    os.makedirs(os.path.join(src, "systemd"))
    dich = os.path.join(tempfile.mkdtemp(), "ban")
    P.dung_cay(src, dich)
    assert os.path.exists(os.path.join(dich, "system", "config", "hethong.json"))
