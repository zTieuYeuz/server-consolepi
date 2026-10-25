# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Chu "Pi" trong cau chu hien cho nguoi dung.

Giao dien viet tu thoi con Raspberry Pi nen nhieu cau noi "Pi tu cap IP", "cam Pi vao mang"...
Tren may x86 (ISO) chu "Pi" do sai/lam kho hieu (lỗi thật gặp khi quay video 16/10/2026).
Thay vi sua tay ~150 cau (de sot, de hong khi sua tiep), loc 1 cho: khi may KHONG phai
Raspberry Pi, doi tu "Pi" doc lap thanh "Console System" trong HTML/JSON tra ve trinh duyet.

Khong dung toi: "Raspberry Pi", "Console Pi", "ConsolePi", "X-Console-Pi", "$Pi", "Pi 4", "Pi OS",
duong dan/ten bien (cac ky tu lien ke \\w - / . $).
"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import sys as _sys
_sys.modules["ui.tenmay"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import re

from ui.phancung import la_raspberry_pi

TEN_THAY = "Console System"
_RE_PI = re.compile(r"(?<![\w/\-.$])(?<!Raspberry )(?<!Console )Pi(?![\w\-/$])(?!\.\w)(?!\s*\d)(?!\s+OS)")
_LA_PI = None


def doi_chu_pi(chu):
    """Doi tu 'Pi' doc lap -> 'Console System' (dung cho test)."""
    return _RE_PI.sub(TEN_THAY, chu)


def register_tenmay(app):
    @app.after_request
    def _doi_ten_pi(resp):
        global _LA_PI
        try:
            if _LA_PI is None:
                _LA_PI = la_raspberry_pi()
            if _LA_PI or resp.direct_passthrough or resp.status_code == 304:
                return resp
            kieu = (resp.mimetype or "")
            if kieu not in ("text/html", "application/json"):
                return resp
            goc = resp.get_data(as_text=True)
            if "Pi" not in goc:
                return resp
            moi = doi_chu_pi(goc)
            if moi != goc:
                resp.set_data(moi)
        except Exception as _loi:      # khong bao gio lam hong trang vi viec doi chu
            _bo_qua(_loi)
        return resp

    return app
