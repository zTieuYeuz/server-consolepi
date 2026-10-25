# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Ket noi toi kho trung tam cho viec CAP NHAT (C3/C4): hoi danh muc, tai goi (tai tiep bang Range), lay khoa goi, bao ket qua.
`cau_hinh_fn()` tra {"url","token"} hoac None; `headers_fn()` tra header Cloudflare Access (neu co). Khong import tinh nang nao."""
import os

import requests

from consolesystem.core.capnhat.may import LoiKho

TIMEOUT = 20


class KhoCapNhat:
    def __init__(self, cau_hinh_fn, headers_fn=lambda: {}, phien_ban_fn=lambda: ""):
        self._cau_hinh, self._headers_fn, self._pb = cau_hinh_fn, headers_fn, phien_ban_fn

    def _co(self):
        c = self._cau_hinh()
        if not c:
            raise LoiKho("chua ket noi kho trung tam")
        return c

    def _h(self, c):
        import socket
        return {"X-Token": c["token"], "X-Pi-Ten": socket.gethostname(), "X-Pi-Phienban": self._pb(), **self._headers_fn()}

    def _get(self, duong, **kw):
        c = self._co()
        try:
            r = requests.get(c["url"] + duong, headers={**self._h(c), **kw.pop("headers", {})}, timeout=kw.pop("timeout", TIMEOUT), **kw)
        except (requests.ConnectionError, requests.Timeout) as e:
            raise LoiKho("khong toi duoc kho (%s)" % type(e).__name__)
        except requests.RequestException as e:
            raise LoiKho("loi mang: %s" % type(e).__name__)
        return r

    def danh_muc(self, kenh):
        r = self._get("/api/cap-nhat/danh-muc", params={"kenh": kenh})
        if r.status_code != 200:
            try:
                msg = r.json().get("loi", "")
            except ValueError:
                msg = ""
            raise LoiKho("kho tra %s %s" % (r.status_code, msg), r.status_code)
        try:
            return r.json()
        except ValueError:
            raise LoiKho("kho tra noi dung khong phai JSON", r.status_code)

    def khoa_goi(self, pb, kt, kenh):
        r = self._get("/api/cap-nhat/khoa-goi/%s/%s" % (pb, kt), params={"kenh": kenh})
        if r.status_code != 200:
            raise LoiKho("kho khong cap khoa goi (%s)" % r.status_code, r.status_code)
        return r.json()

    def tai_goi(self, pb, kt, kenh, dich_part, bao_tien_do=None, dung=None):
        """Tai ve `dich_part`, TIEP TUC neu da co mot phan (Range). `dung()` -> True de huy giua chung."""
        have = os.path.getsize(dich_part) if os.path.exists(dich_part) else 0
        r = self._get("/api/cap-nhat/goi/%s/%s" % (pb, kt), params={"kenh": kenh}, stream=True, timeout=60,
                      headers={"Range": "bytes=%d-" % have} if have else {})
        if r.status_code == 416:                                   # da du roi
            return
        if r.status_code not in (200, 206):
            raise LoiKho("kho khong cho tai goi (%s)" % r.status_code, r.status_code)
        if r.status_code == 200:
            have = 0
        tong = have + int(r.headers.get("Content-Length") or 0)
        with open(dich_part, "ab" if have else "wb") as f:
            for kh in r.iter_content(1 << 20):
                if dung and dung():
                    raise LoiKho("da huy tai goi")
                f.write(kh)
                have += len(kh)
                if bao_tien_do:
                    bao_tien_do(have, tong)
            f.flush()
            os.fsync(f.fileno())

    def bao_cao(self, hanh_dong, tu="", den="", ket_qua=""):
        try:
            c = self._co()
            requests.post(c["url"] + "/api/cap-nhat/bao-cao", json={"hanh_dong": hanh_dong, "tu": tu, "den": den, "ket_qua": ket_qua},
                          headers=self._h(c), timeout=10)
        except (LoiKho, requests.RequestException):
            pass                                                    # bao cao la phu - khong duoc lam hong viec chinh
