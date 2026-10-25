# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Cau noi tuong thich (B2): `ui.tk_dongco` da chuyen sang `consolesystem.features.software_deploy.tk_dongco`. Hai ten tro toi CUNG MOT module (sys.modules), nen
patch/trang thai/`from ui import tk_dongco` van nhu truoc. Se go cau noi khi moi noi goi da dung ten moi."""
import importlib as _il
import sys as _sys

_sys.modules[__name__] = _il.import_module("consolesystem.features.software_deploy.tk_dongco")
