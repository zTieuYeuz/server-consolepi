"""Loi that 24/10/2026: server.pem cap lai (IP doi) nhung server-chain.pem cu -> nginx -t hong khi khoi dong lai."""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def _pub(duong):
    return subprocess.run(["openssl", "x509", "-in", duong, "-noout", "-pubkey"], capture_output=True, text=True).stdout


def test_chain_khop_sau_khi_cap_lai_chung_chi(tmp_path, monkeypatch):
    from ui import uem_pki as P
    monkeypatch.setattr(P.DL, "DIR", str(tmp_path))
    monkeypatch.setattr(P, "ips_pi", lambda: ["192.168.1.10"])
    P.ca()
    P.may_chu()
    P.ghi_chain()
    monkeypatch.setattr(P, "ips_pi", lambda: ["192.168.1.10", "10.0.0.5"])   # IP doi -> cap lai
    assert P.may_chu() is True
    d = P._dir()
    assert _pub(os.path.join(d, "server-chain.pem")).strip() == _pub(os.path.join(d, "server.pem")).strip()
    khoa = subprocess.run(["openssl", "pkey", "-in", os.path.join(d, "server.key"), "-pubout"], capture_output=True, text=True).stdout
    assert khoa.strip() == _pub(os.path.join(d, "server-chain.pem")).strip()
