"""Dung chung cho test cap nhat: dung 'the gioi' gia (kho, may, khoa, goi) de thu bo nang cap ma KHONG dong vao he thong that."""
import hashlib
import json
import os
import sys
import time

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: E402

from consolesystem.core import phathanh as PH  # noqa: E402
from consolesystem.core.capnhat import danhmuc as DM  # noqa: E402
from consolesystem.core.capnhat import goi as G  # noqa: E402
from consolesystem.core.capnhat import khoa as K  # noqa: E402
from consolesystem.core.capnhat import may as M  # noqa: E402
from consolesystem.core.capnhat import nangcap as N  # noqa: E402

N_SCRYPT = 2 ** 14


class SupDo(BaseException):
    """Mo phong MAT DIEN: ket thuc tien trinh ngay lap tuc (BaseException nen khong bi `except Exception` nuot)."""


def viet(p, nd):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(nd if isinstance(nd, bytes) else nd.encode())


class KhoGia:
    def __init__(self, he):
        self.he = he
        self.bao_cao_ds = []
        self.tai_hong = False
        self.loi_danh_muc = None
        self.dung_giua_chung = None            # so byte: ghi dung chung roi SupDo

    def danh_muc(self, kenh):
        if self.loi_danh_muc:
            raise self.loi_danh_muc
        return {"danh_muc": self.he.danh_muc_pb, "tin_cay": self.he.tin_cay, "co_khoa_may": True, "gio_kho": int(self.he.gio())}

    def tai_goi(self, pb, kt, kenh, dich_part, bao_tien_do=None, dung=None):
        raw = open(self.he.goi[pb], "rb").read()
        if self.tai_hong:
            raw = raw[:-10] + b"\0" * 10
        have = os.path.getsize(dich_part) if os.path.exists(dich_part) else 0
        with open(dich_part, "ab") as f:
            if self.dung_giua_chung and have < self.dung_giua_chung:
                f.write(raw[have:self.dung_giua_chung])
                f.flush()
                raise SupDo("mat dien luc dang tai")
            f.write(raw[have:])

    def khoa_goi(self, pb, kt, kenh):
        import base64
        nonce = os.urandom(12)
        aad = ("cspkg-khoa-goi|%s|%s|%s|%s" % (pb, kt, kenh, hashlib.sha256(self.he.token.encode()).hexdigest()[:16])).encode()
        return {"nonce": base64.b64encode(nonce).decode(), "ct": base64.b64encode(AESGCM(self.he.khoa_may).encrypt(nonce, self.he.dek[pb], aad)).decode()}

    def bao_cao(self, hanh_dong, tu="", den="", ket_qua=""):
        self.bao_cao_ds.append((hanh_dong, tu, den, ket_qua))


class He:
    """Mot may gia: opt/ + goc du lieu/ + khoa + 2 goi (2.0.1, 2.0.2) san sang trong kho gia."""

    def __init__(self, tmp, kien_truc="amd64"):
        self.tmp = tmp
        self.opt, self.goc = str(tmp / "opt"), str(tmp / "du-lieu")
        os.makedirs(self.goc)
        self.t = [1_800_000_000.0]
        self.token = "tok" + "a" * 61
        self.khoa_may = os.urandom(32)
        # khoa
        kd = str(tmp / "khoa")
        for vt in K.VAI_TRO:
            K.luu_cap_khoa(kd, vt, "mat-khau-test-12345", n=N_SCRYPT)
        goc_priv = K.doc_khoa_rieng(kd + "/goc.khoa-rieng.json", "mat-khau-test-12345")
        self.goc_pub, _ = K.doc_khoa_cong_khai(kd + "/goc.khoa-cong-khai.json")
        self.ph_priv = K.doc_khoa_rieng(kd + "/phat-hanh.khoa-rieng.json", "mat-khau-test-12345")
        ph_pub, _ = K.doc_khoa_cong_khai(kd + "/phat-hanh.khoa-cong-khai.json")
        self.ph_id = K.dau_van_tay(ph_pub)
        self.tin_cay = K.tao_tai_lieu_tin_cay([{"vai_tro": "phat-hanh", "khoa_cong_khai": K.b64(ph_pub), "den": int(self.t[0]) + 10 ** 8}], 1, int(self.t[0]) + 10 ** 7,
                                              goc_priv, K.dau_van_tay(self.goc_pub), tu=int(self.t[0]) - 100)
        # ban dang chay: 2.0.0
        self.nguon = {}
        self._cay("2.0.0", 1)
        PH.tao_ban(self.nguon["2.0.0"], self.opt)
        PH.chuyen_ban(self.opt, "2.0.0")
        os.symlink(os.path.join(self.opt, "current"), str(tmp / "opt-console-pi"))
        # goi 2.0.1, 2.0.2
        self.goi, self.dek, self.ban = {}, {}, []
        for pb, so, truoc in (("2.0.1", 2, "2.0.0"), ("2.0.2", 3, "2.0.1")):
            self._cay(pb, so)
            PH.tao_ban(self.nguon[pb], str(tmp / "build-opt"))              # cay phat hanh THAT (RELEASE.json co tep + so_phat_hanh)
            rd = str(tmp / "build-opt" / "releases" / pb)
            p = str(tmp / ("g-%s.cspkg" % pb))
            m, dek = G.dong_goi(rd, {"phien_ban": pb, "so_phat_hanh": so, "kien_truc": kien_truc, "kenh": "on-dinh", "ban_truoc_bat_buoc": truoc,
                                     "ban_toi_thieu_ha_cap": "2.0.0", "ghi_chu": "ban " + pb}, self.ph_priv, self.ph_id, p)
            self.goi[pb], self.dek[pb] = p, dek
            self.ban.append({"phien_ban": pb, "so_phat_hanh": so, "kien_truc": kien_truc, "kich_thuoc": os.path.getsize(p),
                             "sha256_goi": hashlib.sha256(open(p, "rb").read()).hexdigest(), "ban_truoc_bat_buoc": truoc})
        self.kien_truc = kien_truc
        self.kho = KhoGia(self)
        self.ghi_danh_muc()
        self.nhat_ky = []
        self.khoi_phuc_goi = []
        self.hong = {}                       # ten hook -> so lan goi dau tien se nem loi
        self.suc_khoe_ok = True
        os.makedirs(os.path.join(self.goc, "secrets"))
        M.luu_khoa_may(os.path.join(self.goc, "secrets", "khoa-may.key"), K.b64(self.khoa_may))

    def gio(self):
        return self.t[0]

    def _cay(self, pb, so):
        d = self.tmp / ("nguon-" + pb)
        viet(str(d / "VERSION"), pb + "\n")
        viet(str(d / "SO_PHAT_HANH"), str(so) + "\n")
        viet(str(d / "src/app.py"), "print('%s')\n" % pb * 50)
        viet(str(d / "src/ui/a.py"), os.urandom(5000))
        viet(str(d / "src/scripts/x.sh"), "#!/bin/sh\n")
        self.nguon[pb] = str(d)

    def ghi_danh_muc(self, so_hieu=1, **kw):
        self.danh_muc_pb = DM.tao_danh_muc("on-dinh", so_hieu, self.ban, self.ph_priv, self.ph_id, bay_gio=int(self.t[0]), **kw)

    def moi(self, **ghi_de):
        nhat_ky = self.nhat_ky

        def hook(ten, ham=None):
            def f(*a, **k):
                nhat_ky.append(ten)
                if self.hong.get(ten):
                    self.hong[ten] -= 1
                    raise N.LoiNangCap("loi gia lap o %s" % ten)
                return ham(*a, **k) if ham else None
            return f

        def sao_luu(duong):
            viet(duong, b"SAO-LUU-GIA")

        def ap_dung(ban_dir):
            pass

        def suc_khoe(ten):
            if not self.suc_khoe_ok:
                return False, "gia lap khong khoe"
            return (PH.hien_tai(self.opt) == ten), "current=%s" % PH.hien_tai(self.opt)

        kw = dict(goc=self.goc, opt=self.opt, kho=self.kho, gio=self.gio, khoa_goc=self.goc_pub, kien_truc=self.kien_truc,
                  khoa_may_duong=os.path.join(self.goc, "secrets", "khoa-may.key"),
                  sao_luu_fn=hook("sao_luu", sao_luu), khoi_phuc_fn=hook("khoi_phuc", lambda d: self.khoi_phuc_goi.append(d)),
                  suc_khoe_fn=hook("suc_khoe", suc_khoe), khoi_dong_lai_fn=hook("khoi_dong_lai"), ap_dung_fn=hook("ap_dung", ap_dung),
                  migration_fn=hook("migration"), schema_fn=lambda d: 1, token_fn=lambda: self.token, ngu=lambda s: self.t.__setitem__(0, self.t[0] + s),
                  dung_luong_trong_fn=lambda d: 10 ** 12)
        kw.update(ghi_de)
        m = N.MoiNangCap(**kw)
        m.cho_suc_khoe = 10
        return m


def kiem_nhat_quan(he, moi):
    """BAT BIEN sau moi tinh huong: current tro ban ton tai + nguyen ven, khong con thu muc cai do dang, job o trang thai ket thuc."""
    cur = PH.hien_tai(he.opt)
    assert cur and os.path.isdir(os.path.join(he.opt, "releases", cur)), "current khong tro vao ban hop le"
    assert PH.kiem_ban(he.opt, cur) == [], "ban dang chay khong nguyen ven"
    thu = os.path.join(he.opt, "releases")
    assert not [x for x in os.listdir(thu) if x.startswith(".")], "con thu muc tam: %s" % os.listdir(thu)
    return cur
