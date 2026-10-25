# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Cau noi tuong thich (B2): `ui.remote` da chuyen sang `consolesystem.features.network.remote`. Hai ten tro toi CUNG MOT module (sys.modules), nen
patch/trang thai/`from ui import remote` van nhu truoc. Se go cau noi khi moi noi goi da dung ten moi."""
import importlib as _il
import sys as _sys

_sys.modules[__name__] = _il.import_module("consolesystem.features.network.remote")
