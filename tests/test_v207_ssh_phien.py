"""2.0.7 cum 2: SSH nhieu nguoi - phien rieng, khoa theo may dich, chi xem / xin dieu khien, ma ngau nhien."""
import os
import subprocess
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, SRC)


def _sp(tmp_path, monkeypatch):
    from consolesystem.features.terminal import ssh_phien as SP
    monkeypatch.setattr(SP, "FILE", str(tmp_path / "ssh-phien.json"))
    return SP


def test_moi_nguoi_mot_phien_rieng_ma_ngau_nhien(tmp_path, monkeypatch):
    SP = _sp(tmp_path, monkeypatch)
    ma_a, tm_a = SP.phien_cua("an")
    ma_b, tm_b = SP.phien_cua("binh")
    assert tm_a != tm_b and ma_a != ma_b and ma_a.startswith("ssh-") and len(ma_a) == 20
    assert SP.phien_cua("an") == (ma_a, tm_a)                                   # cung nguoi: cung phien
    xem = SP.ma_xem("an", "binh")
    assert xem.startswith("xem-") and xem != ma_a and SP.ma_xem("khongco", "binh") is None
    xem2 = SP.ma_xem("an", "binh")                                              # NV8-04: moi lan xin cap ma MOI, thu hoi ma cu cua cung cap (chu, nguoi xem)
    assert xem2 != xem and xem not in SP._doc()["phien"] and SP.ma_xem("an", "binh") != xem2
    assert (tmp_path / "ssh-phien.json").stat().st_mode & 0o777 == 0o600


def test_gioi_han_so_nguoi(tmp_path, monkeypatch):
    SP = _sp(tmp_path, monkeypatch)
    for i in range(SP.TOI_DA_PHIEN):
        SP.phien_cua("u%d" % i)
    try:
        SP.phien_cua("them")
        assert False
    except ValueError as e:
        assert "tối đa" in str(e)
    assert SP.phien_cua("them", dang_chay=lambda t: False) is not None          # phien cu da chet thi khong tinh


def test_khoa_theo_may_chi_xem_xin_nhuong_het_han(tmp_path, monkeypatch):
    SP = _sp(tmp_path, monkeypatch)
    t = [1000.0]
    g = lambda: t[0]  # noqa: E731
    assert SP.lay_khoa("10.0.0.1:22", "an", g) == ("dieu_khien", "an")
    assert SP.lay_khoa("10.0.0.1:22", "binh", g) == ("chi_xem", "an")           # nguoi sau chi xem
    assert SP.lay_khoa("10.0.0.2:22", "binh", g) == ("dieu_khien", "binh")      # may khac thi tu do
    ok, _ = SP.xin("10.0.0.1:22", "binh", g)
    assert ok is False
    tt = SP.trang_thai("an", g)
    assert [k for k in tt if k["may"] == "10.0.0.1:22"][0]["xin"] == "binh"
    assert SP.nhuong("10.0.0.1:22", "binh", g)[0] is False                      # chi chu moi nhuong duoc
    assert SP.nhuong("10.0.0.1:22", "an", g)[0] is True
    assert SP.lay_khoa("10.0.0.1:22", "an", g) == ("chi_xem", "binh")
    t[0] += SP.HAN_KHOA + 1                                                      # chu bo di: khoa tu het han
    assert SP.lay_khoa("10.0.0.1:22", "an", g) == ("dieu_khien", "an")
    assert SP.tha("10.0.0.1:22", "an") and not SP.tha("10.0.0.1:22", "binh")


def test_script_tra_ma_chi_nhan_ma_dung(tmp_path, monkeypatch):
    SP = _sp(tmp_path, monkeypatch)
    ma, tm = SP.phien_cua("an")
    xem = SP.ma_xem("an", "binh")
    env = dict(os.environ, CS_SSH_PHIEN=str(tmp_path / "ssh-phien.json"))
    sc = os.path.join(SRC, "scripts", "ssh-phien-tra.py")
    run = lambda m: subprocess.run([sys.executable, sc, m], capture_output=True, text=True, env=env)  # noqa: E731
    assert run(ma).stdout.split() == ["rw", tm] and run(xem).stdout.split() == ["ro", tm]
    assert run("ssh-0123456789abcdef").returncode == 1 and run("ssh-an").returncode == 1 and run("../x").returncode == 1
    # phien-mo.sh phai co nhanh ssh-*|xem-* va doc ma qua script, khong lay ten tmux tu URL
    sh = open(os.path.join(SRC, "scripts", "phien-mo.sh"), encoding="utf-8").read()
    assert "ssh-*|xem-*)" in sh and "ssh-phien-tra.py" in sh and "attach-session -r" in sh


def test_ma_xem_ngan_han_gan_nguoi_xem_va_chu_phai_dang_chay(tmp_path, monkeypatch):
    """NV8-04: ma xem het han sau HAN_MA_XEM, ghi ten nguoi xem, chu khong co phien dang chay thi khong cap, script tra tu choi ma het han."""
    SP = _sp(tmp_path, monkeypatch)
    ma, tm = SP.phien_cua("an")
    assert SP.ma_xem("an", "binh", dang_chay=lambda t: False) is None             # chu khong con phien tmux song
    t0 = 1_000_000.0
    xem = SP.ma_xem("an", "binh", gio=lambda: t0)
    p = SP._doc()["phien"][xem]
    assert p["cho"] == "binh" and p["het"] == t0 + SP.HAN_MA_XEM and p["chi_xem"] is True
    env = dict(os.environ, CS_SSH_PHIEN=str(tmp_path / "ssh-phien.json"))
    sc = os.path.join(SRC, "scripts", "ssh-phien-tra.py")
    # ma moi cap co 'het' trong tuong lai thuc -> doi sang het han bang cach sua file
    d = SP._doc()
    d["phien"][xem]["het"] = 1.0
    SP._ghi(d)
    assert subprocess.run([sys.executable, sc, xem], capture_output=True, text=True, env=env).returncode == 1
    SP.ma_xem("an", "cuong", gio=lambda: t0 + 5000)                               # cap ma khac don ma het han
    assert xem not in SP._doc()["phien"]
