"""2.0.7 cum 1: Console tu hoi phuc khi kho tra 401/403 (kho mat token), co gioi han tan suat va dung khi bi chan that."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))


class _R:
    def __init__(self, code, js=None):
        self.status_code, self._js, self.headers = code, js or {}, {}

    def json(self):
        return self._js


def _kho(monkeypatch, hook):
    from consolesystem.integrations import kho_capnhat as K
    cau = {"url": "https://kho.test", "token": "cu"}
    goi = []

    def get(url, headers=None, timeout=0, **kw):
        goi.append(headers["X-Token"])
        return _R(200, {"ok": 1}) if headers["X-Token"] == "moi" else _R(401, {"loi": "Token không hợp lệ"})
    monkeypatch.setattr(K.requests, "get", get)
    return K.KhoCapNhat(lambda: dict(cau), lambda: {}, lambda: "2.0.7", lambda: hook(cau)), goi


def test_401_tu_dang_ky_lai_roi_thu_lai_mot_lan(monkeypatch):
    def hook(cau):
        cau["token"] = "moi"
        return True
    kho, goi = _kho(monkeypatch, hook)
    assert kho.danh_muc("on-dinh") == {"ok": 1} and goi == ["cu", "moi"]


def test_hoi_phuc_that_bai_thi_bao_loi_khong_lap(monkeypatch):
    from consolesystem.core.capnhat.may import LoiKho
    n = []
    kho, goi = _kho(monkeypatch, lambda cau: n.append(1) or False)
    try:
        kho.danh_muc("on-dinh")
        assert False
    except LoiKho as e:
        assert e.ma == 401 if hasattr(e, "ma") else True
    assert len(n) == 1 and goi == ["cu"]


def test_gioi_han_tan_suat_va_dung_khi_bi_chan(monkeypatch):
    from consolesystem.features.deploy_os import khotrungtam as KT
    goi = []
    monkeypatch.setattr(KT, "tu_dang_ky", lambda bo_token=False: goi.append(bo_token) or (False, "Kho bản cũ"))
    HP = KT.HOI_PHUC
    HP.update(luc=0.0, ok=None, msg="", chan=False, lan=[])
    t = [1000.0]
    assert KT.tu_hoi_phuc_token(lambda: t[0]) is False and goi == [True]          # lan 1: dang ky bo token cu
    assert KT.tu_hoi_phuc_token(lambda: t[0] + 60) is False and len(goi) == 1     # <10 phut: khong goi lai
    t[0] += 700
    KT.tu_hoi_phuc_token(lambda: t[0])
    assert len(goi) == 2
    for i in range(10):                                                          # toi da 6 lan / 24 gio
        t[0] += 700
        KT.tu_hoi_phuc_token(lambda: t[0])
    assert len(goi) == KT.HOI_PHUC_TOI_DA_NGAY
    HP.update(luc=0.0, chan=False, lan=[])
    monkeypatch.setattr(KT, "tu_dang_ky", lambda bo_token=False: goi.append("c") or (False, "Máy bị chặn bởi kho"))
    n0 = len(goi)
    KT.tu_hoi_phuc_token(lambda: 5000.0)
    KT.tu_hoi_phuc_token(lambda: 5000.0 + 800)
    assert len(goi) == n0 + 1 and HP["chan"] is True                             # bi chan that: dung han
