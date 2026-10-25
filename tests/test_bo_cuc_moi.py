"""A3: chuyen sang bo cuc /var/lib/console-system. Chi dung thu muc tam; mau that cua .30 (neu co) dung de thu them."""
import hashlib
import json
import os
import subprocess
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))
from consolesystem.core import dichuyen as M  # noqa: E402

MAU_30 = "/root/ban-sao-30"
MAU_30_OPT = "/root/ban-sao-30-opt"


def bam_cay(p):
    ra = {}
    for d, _ds, fs in os.walk(p):
        for f in fs:
            fp = os.path.join(d, f)
            ra[os.path.relpath(fp, p)] = hashlib.sha256(open(fp, "rb").read()).hexdigest()
    return ra


@pytest.fixture
def cay(tmp_path):
    cu, opt = tmp_path / "cu", tmp_path / "opt"
    (cu / "trienkhai" / "pki").mkdir(parents=True)
    (cu / "trienkhai" / "pki" / "ca.pem").write_text("CA")
    (cu / "trienkhai" / "pki" / "ca.key").write_text("CAKEY")
    (cu / "trienkhai" / ".khoa").write_text("KHOA")
    (cu / "trienkhai" / "may.json").write_text("[1]")
    (cu / "trienkhai" / "trong").mkdir()
    (cu / "kho-trungtam.json").write_text("{}")
    (cu / "samba-deploy.key").write_text("SMB")
    (cu / "lich-su-cai.json").write_text("[]")
    (cu / "deploy").mkdir()
    (cu / "deploy" / "anh.wim").write_text("NANG")
    opt.mkdir()
    (opt / "config.json").write_text('{"a":1}')
    (opt / "flask-secret.key").write_text("FLASK")
    os.chmod(opt / "flask-secret.key", 0o600)
    return str(cu), str(opt), str(tmp_path / "moi")


def test_anh_xa_dung_cho_va_ban_cu_nguyen_ven(cay):
    cu, opt, moi = cay
    truoc = (bam_cay(cu), bam_cay(opt))
    n = M.dua_ve_bo_cuc_moi(cu, opt, moi)
    assert n >= 9 and M.kiem_bo_cuc_moi(moi) == []
    doc = lambda *p: open(os.path.join(moi, *p)).read()  # noqa: E731
    assert doc("config", "config.json") == '{"a":1}' and doc("secrets", "flask-secret.key") == "FLASK"
    assert doc("secrets", "trienkhai.khoa") == "KHOA" and doc("pki", "ca.key") == "CAKEY"
    assert doc("secrets", "samba-deploy.key") == "SMB" and doc("data", "trienkhai", "may.json") == "[1]"
    assert doc("data", "lich-su-cai.json") == "[]" and os.path.isdir(os.path.join(moi, "data", "trienkhai", "trong"))
    assert (bam_cay(cu), bam_cay(opt)) == truoc            # ban cu KHONG bi dong toi
    assert os.path.islink(os.path.join(moi, "deploy")) and os.path.exists(os.path.join(moi, "deploy", "anh.wim"))
    assert os.stat(os.path.join(moi, "secrets")).st_mode & 0o777 == 0o700
    assert os.stat(os.path.join(moi, "secrets", "flask-secret.key")).st_mode & 0o777 == 0o600


def test_khong_ghi_de_va_khong_chuyen_hai_lan(cay):
    cu, opt, moi = cay
    M.dua_ve_bo_cuc_moi(cu, opt, moi)
    with pytest.raises(M.LoiDichuyen, match="da la bo cuc moi"):
        M.dua_ve_bo_cuc_moi(cu, opt, moi)


def test_loi_giua_chung_khong_de_lai_gi(cay, monkeypatch):
    cu, opt, moi = cay
    truoc = bam_cay(cu)
    goc, dem = M._chep_va_kiem, []

    def hong(n, d, lan=3):
        dem.append(1)
        if len(dem) == 4:
            raise OSError("het cho gia")
        return goc(n, d, lan)
    monkeypatch.setattr(M, "_chep_va_kiem", hong)
    with pytest.raises(OSError):
        M.dua_ve_bo_cuc_moi(cu, opt, moi)
    assert not os.path.exists(moi) and not os.path.exists(moi + ".dang-chuyen") and bam_cay(cu) == truoc


def test_phat_hien_file_bi_sua_sau_khi_chep(cay):
    cu, opt, moi = cay
    M.dua_ve_bo_cuc_moi(cu, opt, moi)
    open(os.path.join(moi, "pki", "ca.pem"), "w").write("BI-SUA")
    assert M.kiem_bo_cuc_moi(moi) == ["pki/ca.pem"]


def test_hoan_tac_giu_lai_ban_moi(cay):
    cu, opt, moi = cay
    M.dua_ve_bo_cuc_moi(cu, opt, moi)
    dich = M.hoan_tac_bo_cuc(moi)
    assert not os.path.exists(moi) and os.path.isdir(dich) and os.path.exists(os.path.join(dich, M.DAU_BO_CUC_MOI))


def _vi_tri(env_goc):
    code = ("import sys;sys.path.insert(0,'src');from ui import duongdan as D;"
            "print(json.dumps([D.BO_CUC_MOI,D.THU_MUC_DU_LIEU,D.FILE_CONFIG,D.FILE_KHOA_SAMBA,D.DIR_PKI,D.FILE_TK_KHOA,D.DEPLOY_DIR]))")
    r = subprocess.run(["python3", "-c", "import json;" + code], cwd=GOC, capture_output=True, text=True,
                       env=dict(os.environ, CONSOLE_PI_DATA=env_goc))
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_chuong_trinh_doi_duong_theo_dau_bo_cuc(cay):
    cu, opt, moi = cay
    assert _vi_tri(cu) == [False, cu, "/opt/console-pi/config.json", cu + "/samba-deploy.key",
                           cu + "/trienkhai/pki", cu + "/trienkhai/.khoa", cu + "/deploy"]
    M.dua_ve_bo_cuc_moi(cu, opt, moi)
    assert _vi_tri(moi) == [True, moi + "/data", moi + "/config/config.json", moi + "/secrets/samba-deploy.key",
                            moi + "/pki", moi + "/secrets/trienkhai.khoa", moi + "/deploy"]


@pytest.mark.skipif(not os.path.isdir(MAU_30), reason="khong co ban sao du lieu .30")
def test_mau_that_30_pki_va_khoa_giong_het(tmp_path):
    import shutil
    cu = str(tmp_path / "cu")
    shutil.copytree(MAU_30, cu, symlinks=True)          # chay tren BAN SAO (mo CA co the cap lai chung chi may chu)
    moi = str(tmp_path / "moi")
    M.dua_ve_bo_cuc_moi(cu, MAU_30_OPT, moi)
    assert M.kiem_bo_cuc_moi(moi) == []
    code = ("import sys,runpy,threading;sys.path.insert(0,'src');"
            "from ui import uem_pki as P, tk_dulieu as DL;"
            "print(P.ca_sha256(), DL.giai_ma(DL.ma_hoa('xin chao')))")
    kq = []
    for goc in (cu, moi):
        r = subprocess.run(["python3", "-c", code], cwd=GOC, capture_output=True, text=True,
                           env=dict(os.environ, CONSOLE_PI_DATA=goc))
        assert r.returncode == 0, r.stderr[-400:]
        kq.append(r.stdout.split())
    assert kq[0] == kq[1] and kq[0][1:] == ["xin", "chao"]
