"""A4: install.sh/script dung bo cuc moi. Chay trong thu muc tam (CS_GOC_CU/CS_GOC_MOI/CS_OPT ghi de), khong dung may that."""
import os
import subprocess

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAG = "v1.9.5-truoc-dai-tu"


def bash(code, env):
    e = dict(os.environ, CS_KHONG_DUNG_DICH_VU="1")
    e.pop("CONSOLE_PI_DATA", None)
    e.update(env)
    return subprocess.run(["bash", "-c", code], cwd=GOC, capture_output=True, text=True, env=e)


@pytest.fixture
def mt(tmp_path):
    cu, moi, opt = tmp_path / "cu", tmp_path / "moi", tmp_path / "opt"
    opt.mkdir()
    return {"CS_GOC_CU": str(cu), "CS_GOC_MOI": str(moi), "CS_OPT": str(opt)}, cu, moi, opt


IN = '. src/scripts/duong-dan.sh; echo "$CS_BO_CUC|$CS_DATA|$CS_FILE_CONFIG|$CS_FILE_XOAY|$CS_KHOA_SAMBA|$CS_DEPLOY"'


def test_duong_dan_bo_cuc_cu(mt):
    env, cu, moi, opt = mt
    r = bash(IN, env)
    assert r.stdout.strip() == f"cu|{cu}|{opt}/config.json|{opt}/screen-rotation|{cu}/samba-deploy.key|{cu}/deploy"


def test_duong_dan_bo_cuc_moi(mt):
    env, cu, moi, opt = mt
    moi.mkdir()
    (moi / ".bo-cuc-moi").write_text("2")
    r = bash(IN, env)
    assert r.stdout.strip() == f"moi|{moi}/data|{moi}/config/config.json|{moi}/config/screen-rotation|{moi}/secrets/samba-deploy.key|{moi}/deploy"


def test_may_moi_hoan_toan_tao_thang_bo_cuc_moi(mt):
    env, cu, moi, opt = mt
    r = bash('. src/scripts/chon-bo-cuc.sh; chon_bo_cuc "$PWD"; echo "$CS_BO_CUC"', env)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == "moi" and (moi / ".bo-cuc-moi").exists()
    assert not cu.exists() and (moi / "secrets").stat().st_mode & 0o777 == 0o700


def test_may_cu_duoc_chuyen_va_ban_cu_giu_nguyen(mt):
    env, cu, moi, opt = mt
    (cu / "trienkhai" / "pki").mkdir(parents=True)
    (cu / "trienkhai" / "pki" / "ca.pem").write_text("CA")
    (cu / "samba-deploy.key").write_text("SMB")
    (opt / "config.json").write_text('{"x": 1}')
    r = bash('. src/scripts/chon-bo-cuc.sh; chon_bo_cuc "$PWD"; echo "$CS_BO_CUC|$CS_FILE_CONFIG"', env)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip().splitlines()[-1] == f"moi|{moi}/config/config.json"
    assert (moi / "config" / "config.json").read_text() == '{"x": 1}' and (moi / "pki" / "ca.pem").read_text() == "CA"
    assert (cu / "samba-deploy.key").read_text() == "SMB" and (opt / "config.json").exists()


def test_chuyen_loi_thi_giu_bo_cuc_cu_va_van_tiep_tuc(mt):
    env, cu, moi, opt = mt
    cu.mkdir()
    (cu / "x.json").write_text("{}")
    moi.mkdir()
    (moi / "vat-can.txt").write_text("dang co noi dung")          # dich khong rong -> dua_ve_bo_cuc_moi tu choi
    r = bash('. src/scripts/chon-bo-cuc.sh; warn(){ echo "CANH-BAO $*"; }; chon_bo_cuc "$PWD"; echo "$CS_BO_CUC"', env)
    assert r.returncode == 0
    assert r.stdout.strip().splitlines()[-1] == "cu" and "CANH-BAO" in r.stdout and not (moi / ".bo-cuc-moi").exists()


def test_ep_giu_bo_cuc_cu(mt):
    env, cu, moi, opt = mt
    cu.mkdir()
    r = bash('. src/scripts/chon-bo-cuc.sh; chon_bo_cuc "$PWD"; echo "$CS_BO_CUC"', dict(env, CS_KHONG_DOI_BO_CUC="1"))
    assert r.stdout.strip().splitlines()[-1] == "cu" and not moi.exists()


def _mau_cu(ten):
    return subprocess.run(["git", "show", f"{TAG}:config/{ten}"], cwd=GOC, capture_output=True, text=True).stdout


def test_mau_cau_hinh_o_bo_cuc_cu_giong_het_ban_1_9_5(mt):
    """Mau smb.conf/nginx viet theo bo cuc moi; sed cua install.sh o bo cuc cu phai ra DUNG noi dung 1.9.5 (tru dong ghi chu)."""
    env, cu, moi, opt = mt
    env = dict(env, CS_GOC_CU="/var/lib/console-pi", CS_OPT="/opt/console-pi", CS_GOC_MOI="/nonexistent-moi")
    r = bash(". src/scripts/duong-dan.sh; DATA_DIR=$CS_DATA; "
             'sed -e "s#/var/lib/console-system/deploy#$CS_DEPLOY#g" -e "s#/var/lib/console-system/data/o-dia#$DATA_DIR/o-dia#g" '
             '-e "s#/var/lib/console-system/data/lich-su-bao#$DATA_DIR/lich-su-bao#g" '
             '-e "s#/var/lib/console-system/secrets/samba-deploy.key#$CS_KHOA_SAMBA#g" config/smb.conf', env)
    ra = [x for x in r.stdout.splitlines() if "samba-deploy.key" not in x]
    cu_ = [x for x in _mau_cu("smb.conf").splitlines() if "samba-deploy.key" not in x]
    assert ra == cu_
    r2 = bash('. src/scripts/duong-dan.sh; sed "s#/var/lib/console-system/deploy#$CS_DEPLOY#g" config/nginx-console-pi.conf', env)
    assert r2.stdout.splitlines() == _mau_cu("nginx-console-pi.conf").splitlines()


def test_phien_chay_chon_dung_thu_muc(tmp_path):
    code = "import runpy,sys;print(runpy.run_path('src/scripts/phien-chay.py', run_name='x')['DU_LIEU'])"
    cu, moi = tmp_path / "cu", tmp_path / "moi"
    cu.mkdir()
    r = subprocess.run(["python3", "-c", code], cwd=GOC, capture_output=True, text=True, env=dict(os.environ, CONSOLE_PI_DATA=str(cu)))
    assert r.stdout.strip() == str(cu), r.stderr[-300:]
    moi.mkdir()
    (moi / ".bo-cuc-moi").write_text("2")
    r = subprocess.run(["python3", "-c", code], cwd=GOC, capture_output=True, text=True, env=dict(os.environ, CONSOLE_PI_DATA=str(moi)))
    assert r.stdout.strip() == str(moi / "data"), r.stderr[-300:]
