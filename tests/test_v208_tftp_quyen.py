"""2.0.8 V5-2 (phan an toan): don vi TFTP khong con chmod 777; thu muc giao cho user tftp + 0775 (nhat quan voi bat_tftp)."""
import os

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def test_don_vi_tftp_khong_chmod_777():
    s = open(os.path.join(GOC, "systemd", "console-system-tftp.service"), encoding="utf-8").read()
    lenh = [x for x in s.splitlines() if x.startswith("ExecStartPre=")]
    assert not any("777" in x for x in lenh), lenh
    assert any("chown tftp:tftp" in x for x in lenh) and any("chmod 0775" in x for x in lenh)
    assert "--secure --create" in s                                  # chuc nang nhan file tu switch (copy running-config tftp://) giu nguyen
