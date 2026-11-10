"""Cach ly bo test khoi du lieu THAT cua may chay test: nhat ky loi / thao tac ghi vao thu muc tam, khong ghi /var/log.
(LOI-004 NV4: test tung ghi dong vao /var/log/console-pi-audit.log cua may build.) Cac tien trinh con ke thua bien moi truong nay."""
import os
import tempfile

_TAM = tempfile.mkdtemp(prefix="cs-test-log-")
os.environ.setdefault("CONSOLE_PI_LOG", _TAM)
