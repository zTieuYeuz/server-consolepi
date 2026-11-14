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


# ------------------------------------------------------------------------------- B2: ap_dung doc manifest
def _ban(tmp_path, mf=None, units=("console-system-term-ssh.service", "console-system-nang-cap-phuc-hoi.service", "console-system-term-phien.service",
                                   "console-system-tftp.service")):
    ban = tmp_path / "ban"
    (ban / "system" / "systemd").mkdir(parents=True)
    (ban / "system" / "config").mkdir(parents=True)
    for u in units:
        (ban / "system" / "systemd" / u).write_text("[Unit]\nDescription=%s\n" % u)
    if mf is not None:
        (ban / "system" / "config" / "hethong.json").write_text(json.dumps(mf))
    return str(ban)


class Gia:
    def __init__(self, rc=None):
        self.goi, self.rc = [], rc or {}

    def __call__(self, cmd, timeout=60):
        self.goi.append(list(cmd))
        return self.rc.get(tuple(cmd[:3]), 0), ""


def _etc(tmp_path, co=()):
    e = tmp_path / "etc"
    (e / "etc/systemd/system").mkdir(parents=True)
    for u in co:
        (e / "etc/systemd/system" / u).write_text("cu")
    return str(e)


def _bc():
    return {"them": [], "go": [], "canh_bao": []}


def test_B2_them_don_vi_thieu_va_enable(tmp_path):
    from consolesystem.core import phathanh as P
    mf = {"don_vi": {"bat": ["console-system-nang-cap-phuc-hoi", "nginx", "console-system-term-phien"], "go": []}}
    ban, e, gia, bc = _ban(tmp_path, mf), _etc(tmp_path, co=["console-system-term-phien.service"]), Gia(), _bc()
    P.ap_dung_don_vi(ban, str(tmp_path / "bk"), e, gia, False, bc)
    assert bc["them"] == ["console-system-nang-cap-phuc-hoi.service"]                                 # nginx khong co tep trong ban -> bo qua; term-phien da co -> khong dong
    assert open(os.path.join(e, "etc/systemd/system/console-system-nang-cap-phuc-hoi.service")).read().startswith("[Unit]")
    assert ["systemctl", "daemon-reload"] in gia.goi and ["systemctl", "enable", "console-system-nang-cap-phuc-hoi"] in gia.goi
    assert open(os.path.join(e, "etc/systemd/system/console-system-term-phien.service")).read() == "cu"      # don vi co san KHONG bi ghi de o buoc nay
    bc2 = _bc()
    P.ap_dung_don_vi(ban, str(tmp_path / "bk"), e, Gia(), True, bc2)                                  # che do thu: khong ghi
    assert bc2["them"] == [] and not bc["canh_bao"]


def test_B2_go_don_vi_sao_luu_truoc_va_lui_ban_them_lai(tmp_path):
    from consolesystem.core import phathanh as P
    mf_moi = {"don_vi": {"bat": [], "go": ["console-system-term-ssh"]}}
    ban_moi, e, gia, bc = _ban(tmp_path, mf_moi), _etc(tmp_path, co=["console-system-term-ssh.service"]), Gia(), _bc()
    P.ap_dung_don_vi(ban_moi, str(tmp_path / "bk"), e, gia, False, bc)
    assert bc["go"] == ["console-system-term-ssh.service"] and not os.path.exists(os.path.join(e, "etc/systemd/system/console-system-term-ssh.service"))
    assert ["systemctl", "disable", "--now", "console-system-term-ssh"] in gia.goi
    bk = str(tmp_path / "bk" / "etc/systemd/system/console-system-term-ssh.service")
    assert open(bk).read() == "cu"                                                                     # sao luu day du truoc khi go
    # LUI BAN: ban cu (2.0.7) khong co manifest -> mac dinh bat term-ssh -> don vi duoc them lai tu chinh ban cu
    tmp2 = tmp_path / "cu"
    tmp2.mkdir()
    ban_cu = _ban(tmp2, None)
    bc2, gia2 = _bc(), Gia()
    P.ap_dung_don_vi(ban_cu, str(tmp_path / "bk2"), e, gia2, False, bc2)
    assert "console-system-term-ssh.service" in bc2["them"] and ["systemctl", "enable", "console-system-term-ssh"] in gia2.goi


def test_B2_loi_mot_don_vi_chi_canh_bao(tmp_path):
    from consolesystem.core import phathanh as P
    mf = {"don_vi": {"bat": ["console-system-nang-cap-phuc-hoi"], "go": []}}
    ban, e = _ban(tmp_path, mf), _etc(tmp_path)
    gia = Gia(rc={("systemctl", "enable", "console-system-nang-cap-phuc-hoi"): 1})
    bc = _bc()
    P.ap_dung_don_vi(ban, str(tmp_path / "bk"), e, gia, False, bc)                                     # khong nem ngoai le
    assert bc["canh_bao"] and "enable" in bc["canh_bao"][0]


def test_B2_khoi_dong_lai_theo_manifest_va_thieu_goi(tmp_path):
    from consolesystem.core import phathanh as P
    mf = {"don_vi": {"bat": [], "go": []}, "khoi_dong_lai_khi_doi": {"console-system-tftp.service": ["console-system-tftp"]},
          "goi_apt": {"core": ["python3", "khong-co-goi-nay"], "man_hinh": ["cage"], "trien_khai": []}}
    ban = _ban(tmp_path, mf)
    assert P.dich_vu_can_khoi_dong_lai(ban, ["console-system-tftp.service", "console-system-dashboard.service"]) == ["console-system-tftp"]
    cu = tmp_path / "cu2"
    cu.mkdir()
    assert P.dich_vu_can_khoi_dong_lai(_ban(cu, None), ["a.service", "console-system-dashboard.service"]) == ["a.service"]                  # khong manifest: hanh vi cu
    chay = lambda cmd, timeout=60: (1 if cmd[-1] == "khong-co-goi-nay" else 0, "")                      # noqa: E731
    e = _etc(tmp_path)
    assert P.thieu_goi_apt(ban, chay, e) == ["khong-co-goi-nay"]                                        # chi KIEM; kiosk khong co -> khong doi hoi goi man hinh
    open(os.path.join(e, "etc/systemd/system/console-system-kiosk.service"), "w").write("x")
    chay2 = lambda cmd, timeout=60: (1 if cmd[-1] in ("khong-co-goi-nay", "cage") else 0, "")           # noqa: E731
    assert P.thieu_goi_apt(ban, chay2, e) == ["khong-co-goi-nay", "cage"]


def test_B2_ota_chay_ap_dung_cua_BAN_MOI_khong_phai_ma_2_0_7(tmp_path):
    """Dieu kien CEO (1): nang cap OTA goi <ban moi>/scripts/console-system-apply.py va script dat <ban moi> dau sys.path -> import ap_dung CUA BAN MOI."""
    s = open(os.path.join(GOC, "src", "consolesystem", "features", "updates", "thuc_te.py"), encoding="utf-8").read()
    assert 'os.path.join(ban_dir, "scripts", "console-system-apply.py")' in s
    n = open(os.path.join(GOC, "src", "consolesystem", "core", "capnhat", "nangcap.py"), encoding="utf-8").read()
    i = n.index("def _b_doi_ban")
    assert n[i:i + 700].index("chuyen_ban") < n[i:i + 700].index('hook("ap_dung_fn")(ban_dir)')       # chuyen current truoc, roi ap_dung(ban moi)
    ap = open(os.path.join(GOC, "src", "scripts", "console-system-apply.py"), encoding="utf-8").read()
    assert 'sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))' in ap
    # Chay that: sao chep script + ui + consolesystem sang "ban moi" co dau vet rieng; "ma cu" nam tren PYTHONPATH; ap_dung phai lay tu ban moi
    import shutil
    ban = tmp_path / "moi"
    for m in ("scripts", "ui", "consolesystem"):
        shutil.copytree(os.path.join(GOC, "src", m), ban / m, ignore=shutil.ignore_patterns("__pycache__", "agent_bin"))
    (ban / "consolesystem" / "core" / "phathanh.py").write_text(
        open(ban / "consolesystem" / "core" / "phathanh.py", encoding="utf-8").read() + "\nDAU_VET_BAN_MOI = True\n")
    cu = tmp_path / "cu"
    for m in ("ui", "consolesystem"):
        shutil.copytree(os.path.join(GOC, "src", m), cu / m, ignore=shutil.ignore_patterns("__pycache__", "agent_bin"))
    code = ("import runpy,sys\nsys.argv=['x','--ban','khong','--opt','/khong-co']\n"
            "try:\n    runpy.run_path(%r, run_name='__main__')\nexcept SystemExit:\n    pass\n"
            "import consolesystem.core.phathanh as P\nprint('MOI' if getattr(P,'DAU_VET_BAN_MOI',False) else 'CU', P.__file__)\n") % str(ban / "scripts" / "console-system-apply.py")
    r = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=60, env=dict(os.environ, PYTHONPATH=str(cu), CONSOLE_PI_LOG=str(tmp_path)))
    assert "MOI" in r.stdout and str(ban) in r.stdout, (r.stdout, r.stderr[-400:])
