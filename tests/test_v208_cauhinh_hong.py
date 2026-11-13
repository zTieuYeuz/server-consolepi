"""2.0.8 V6-3: config.json hong -> doc-sua-ghi KHONG ghi de thanh file chi con mot khoa; doc binh thuong/ghi binh thuong khong doi."""
import json
import os
import sys

import pytest

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(GOC, "src"))


@pytest.fixture
def CH(tmp_path, monkeypatch):
    from consolesystem.core import cauhinh as CH
    from consolesystem.core import duongdan as DD
    monkeypatch.setattr(DD, "FILE_CONFIG", str(tmp_path / "config.json"))
    CH._cac.clear()
    yield CH
    CH._cac.clear()


def test_binh_thuong_sinh_va_giu_mat_khau(CH, tmp_path):
    u, p = CH.get_term_credential()
    assert u == "console" and p
    assert CH.get_term_credential() == (u, p)                                  # on dinh, khong sinh lai
    cfg = CH.load_config()
    cfg["screen_rotation"] = "90"
    CH.save_config(cfg)
    assert CH.load_config()["screen_rotation"] == "90" and CH.get_term_credential() == (u, p)


def test_loi_doc_o_cung_khong_bi_ghi_de(CH, tmp_path, monkeypatch):
    """Loi DOC that (EIO tren the SD, mat quyen) -> LoiDuLieu. Truoc day load_config tra {} roi get_term_credential ghi config.json chi con 1 khoa."""
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"terminal_auth": "console:giu-me", "screen_rotation": "90", "khac": 1}))
    goc = f.read_text()
    kho = CH.kho(str(f))

    def hong(_duong):
        raise OSError(5, "Input/output error")
    monkeypatch.setattr(kho, "_doc_file", hong)
    from consolesystem.core.store import LoiDuLieu
    with pytest.raises(LoiDuLieu):
        CH.load_config_de_ghi()
    assert CH.load_config() == {}                                              # doc thuan van tra {} nhu cu (khong lam hong trang)
    u, p = CH.get_term_credential()                                            # khong ghi de
    assert u == "console" and p
    assert f.read_text() == goc, "config.json bi ghi de khi loi doc"


def test_json_hong_duoc_store_giu_lai_va_bao(CH, tmp_path):
    f = tmp_path / "config.json"
    f.write_text('{"a": 1} RAC{{{')
    assert CH.load_config() == {}
    assert [x for x in os.listdir(tmp_path) if ".hong-" in x]                  # file hong con nguyen o .hong-*
