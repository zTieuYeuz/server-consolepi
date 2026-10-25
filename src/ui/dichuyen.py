# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Cau noi tuong thich (B2): `ui.dichuyen` da chuyen sang `consolesystem.core.dichuyen`. Hai ten tro toi CUNG MOT module (sys.modules), nen
patch/trang thai/`from ui import dichuyen` van nhu truoc. Se go cau noi khi moi noi goi da dung ten moi."""
import importlib as _il
import sys as _sys

_sys.modules[__name__] = _il.import_module("consolesystem.core.dichuyen")
