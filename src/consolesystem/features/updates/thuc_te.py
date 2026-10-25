# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Noi bo nang cap voi HE THONG THAT: kho trung tam, systemd, nginx, sao luu/khoi phuc, kiem suc khoe. Moi ham la mot HOOK cua MoiNangCap
(test dung gia lap, xem tests/capnhat_gia.py)."""
import json
import os
import re
import subprocess
import sys
import time

import requests

from consolesystem.core import duongdan as DD
from consolesystem.core import phathanh as PH
from consolesystem.core.capnhat import nangcap as N
from consolesystem.core.lenh import chay as chay_lenh
from consolesystem.integrations.kho_capnhat import KhoCapNhat

DICH_VU_CHINH = "console-pi-dashboard"
DICH_VU_KHAC = ("console-pi-tftp",)
CONG_NOI_BO = 5000


def _kt():
    from consolesystem.features.deploy_os import khotrungtam as KT
    return KT


def kho_thuc():
    """Kho dung de cap nhat: mac dinh kho trung tam (cung token/Cloudflare Access); co the chi dinh KHO RIENG trong updates/cau-hinh.json
    (kho_url + kho_token) - dung cho kenh thu nghiem qua LAN va cho thu nghiem."""
    KT = _kt()
    from consolesystem.core.capnhat import may as M
    try:
        cfg = M.cau_hinh(M.Moi())
    except Exception:
        cfg = {}
    if cfg.get("kho_url") and cfg.get("kho_token"):
        return KhoCapNhat(lambda: {"url": KT.chuan_hoa_url(cfg["kho_url"]), "token": cfg["kho_token"]}, lambda: {}, KT._phien_ban)
    return KhoCapNhat(KT.doc_cauhinh, KT.cf_access_headers, KT._phien_ban)


def _py(duong_script, *args, timeout=900):
    r = chay_lenh(["python3", duong_script, *args], timeout=timeout)
    if not r.ok:
        raise N.LoiNangCap("%s that bai (rc=%s): %s" % (os.path.basename(duong_script), r.rc, (r.err or r.out)[-300:]))
    return r.out


def sao_luu(duong):
    from consolesystem.features.backup import saoluu as SL
    SL.tao_goi(DD.GOC, "cauhinh", duong)
    SL.kiem_goi(duong)                                        # sao luu phai doc lai duoc moi coi la co


def khoi_phuc(duong):
    from consolesystem.features.backup import saoluu as SL
    for s in (DICH_VU_CHINH,) + DICH_VU_KHAC:
        chay_lenh(["systemctl", "stop", s], timeout=60)
    SL.khoi_phuc(duong, DD.GOC)
    SL.hau_khoi_phuc(DD.GOC)


def ap_dung(ban_dir):
    _py(os.path.join(ban_dir, "scripts", "console-system-apply.py"), "--ban", os.path.basename(ban_dir.rstrip("/")))


def migration(ban_dir):
    _py(os.path.join(ban_dir, "scripts", "dichuyen.py"), "chay", "--thu-muc", DD.GOC)


def schema(ban_dir):
    m = re.search(r"ma biet toi: (\d+)", _py(os.path.join(ban_dir, "scripts", "dichuyen.py"), "trangthai", "--thu-muc", DD.GOC))
    return int(m.group(1)) if m else 0


def khoi_dong_lai():
    chay_lenh(["systemctl", "daemon-reload"], timeout=60)
    for s in DICH_VU_KHAC:
        chay_lenh(["systemctl", "try-restart", s], timeout=60)
    r = chay_lenh(["systemctl", "restart", DICH_VU_CHINH], timeout=120)
    if not r.ok:
        raise N.LoiNangCap("khong khoi dong lai duoc dashboard: %s" % (r.err or r.out)[-200:], hoan_tac=True)
    chay_lenh(["systemctl", "reload", "nginx"], timeout=60)


def suc_khoe(ten_ban):
    """(ok, ly do): dashboard tra loi 200 tu chinh may, dung PHIEN BAN cua ban `ten_ban`, nginx hop le."""
    try:
        mong = open(os.path.join(PH.GOC_OPT, "releases", ten_ban, "VERSION"), encoding="utf-8").read().strip()
        r = requests.get("http://127.0.0.1:%d/healthz" % CONG_NOI_BO, timeout=5)
        if r.status_code != 200:
            return False, "healthz tra %s" % r.status_code
        dang = r.json().get("phien_ban")
        if dang != mong:
            return False, "dashboard dang chay ban %s, mong %s" % (dang, mong)
    except (requests.RequestException, OSError, ValueError) as e:
        return False, "%s: %s" % (type(e).__name__, e)
    if not chay_lenh(["nginx", "-t"], timeout=20).ok:
        return False, "nginx -t loi"
    return True, "ok"


def token():
    from consolesystem.core.capnhat import may as M
    cfg = M.cau_hinh(M.Moi())
    if cfg.get("kho_url") and cfg.get("kho_token"):
        return cfg["kho_token"]
    c = _kt().doc_cauhinh()
    if not c:
        raise N.LoiNangCap("chua ket noi kho")
    return c["token"]


def moi_thuc():
    return N.MoiNangCap(kho=kho_thuc(), sao_luu_fn=sao_luu, khoi_phuc_fn=khoi_phuc, pxe_dang_bat_fn=DD.pxe_dang_bat, suc_khoe_fn=suc_khoe,
                        khoi_dong_lai_fn=khoi_dong_lai, ap_dung_fn=ap_dung, migration_fn=migration, schema_fn=schema, token_fn=token)


def khoi_chay_bo_nang_cap():
    """Chay bo nang cap o MOT DON VI systemd RIENG (song sot khi dashboard khoi dong lai). Dev khong co systemd-run -> tien trinh tach roi."""
    script = os.path.join(PH.GOC_OPT, "current", "scripts", "console-system-nang-cap.py")
    if not os.path.exists(script):
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "scripts", "console-system-nang-cap.py")
    ten = "console-system-nang-cap-%d" % int(time.time())
    r = chay_lenh(["systemd-run", "--unit=" + ten, "--collect", "--description=Console System: nang cap", sys.executable, script, "chay"], timeout=30)
    if not r.ok:
        subprocess.Popen([sys.executable, script, "chay"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return ten


def mo_ta_job(job):
    """Phan cua job an toan de gui ra giao dien (khong khoa, khong duong dan nhay cam)."""
    if not job:
        return None
    return {k: job.get(k) for k in ("id", "loai", "tu", "den", "buoc", "trang_thai", "ly_do", "bat_dau", "ket_thuc", "canh_bao", "nhat_ky")}
