# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Danh muc goi WinGet de TIM PHAN MEM (giong OpenUEM: openuem-console .../software_package.go DownloadWingetDB + UpdateWingetApps):
  - tai https://cdn.winget.microsoft.com/cache/source2.msix  (that ra la file ZIP, ~4 MB)
  - lay Public/index.db (SQLite, ~9 MB), bang `packages(id, name, moniker, latest_version, ...)`
  - tim bang SELECT DISTINCT id, name ... WHERE name/id LIKE
Chi giu index.db tren dia (xoa file .msix), lam moi moi 24 gio khi co Internet. Khong co Internet thi dung ban cu / bao ro chua co.
"""
from consolesystem.core.nhatky import bo_qua as _bo_qua
import sys as _sys
_sys.modules["ui.uem_winget"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import os
import re
import sqlite3
import threading
import time
import urllib.request
import zipfile

from ui import tk_dulieu as DL

URL = "https://cdn.winget.microsoft.com/cache/source2.msix"
THU_MUC = os.path.join(DL.DIR, "winget")
DB = os.path.join(THU_MUC, "index.db")
_KHOA = threading.Lock()
_LOI = {"loi": "", "luc": 0}
_BAT_DAU = False


def tuoi_gio():
    try:
        return (time.time() - os.path.getmtime(DB)) / 3600
    except OSError:
        return None


def cap_nhat(force=False):
    """Tai + giai nen index.db. Tra ve (ok, thong_diep)."""
    with _KHOA:
        t = tuoi_gio()
        if not force and t is not None and t < 24:
            return True, "Danh mục còn mới."
        os.makedirs(THU_MUC, exist_ok=True)
        tam = os.path.join(THU_MUC, "source2.msix.tmp")
        try:
            rq = urllib.request.Request(URL, headers={"User-Agent": "ConsoleSystem-UEM"})
            with urllib.request.urlopen(rq, timeout=90) as r, open(tam, "wb") as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            with zipfile.ZipFile(tam) as z:
                with z.open("Public/index.db") as src, open(DB + ".tmp", "wb") as dst:
                    dst.write(src.read())
            c = sqlite3.connect(DB + ".tmp")
            n = c.execute("SELECT COUNT(DISTINCT id) FROM packages").fetchone()[0]
            c.close()
            if n < 1000:
                raise ValueError("danh mục tải về bất thường")
            os.replace(DB + ".tmp", DB)
            _LOI.update(loi="", luc=time.time())
            return True, f"Đã cập nhật danh mục WinGet: {n} gói."
        except Exception as e:
            _LOI.update(loi=str(e)[:200], luc=time.time())
            return False, f"Không cập nhật được danh mục WinGet: {str(e)[:160]}"
        finally:
            for p in (tam, DB + ".tmp"):
                try:
                    os.remove(p)
                except OSError:
                    pass


def co_danh_muc():
    return os.path.isfile(DB)


def so_goi():
    try:
        c = sqlite3.connect(DB)
        n = c.execute("SELECT COUNT(DISTINCT id) FROM packages").fetchone()[0]
        c.close()
        return n
    except Exception:
        return 0


def _thoat_like(s):
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def tim(q, gioi_han=40):
    """[{id, ten, ban}] khop ten hoac id (khong phan biet hoa thuong). Rong neu chua co danh muc."""
    q = (q or "").strip()[:80]
    if len(q) < 2 or not co_danh_muc():
        return []
    try:
        c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        k = f"%{_thoat_like(q)}%"
        ql = q.lower()
        ds = c.execute("SELECT id, name, MAX(latest_version) FROM packages WHERE name LIKE ? ESCAPE '\\' OR id LIKE ? ESCAPE '\\' "
                       "GROUP BY id, name ORDER BY (CASE WHEN LOWER(id)=? THEN 0 WHEN LOWER(SUBSTR(id, INSTR(id,'.')+1))=? THEN 1 "
                       "WHEN LOWER(name)=? THEN 1 WHEN LOWER(name) LIKE ? ESCAPE '\\' THEN 2 ELSE 3 END), LENGTH(name), name LIMIT ?",
                       (k, k, ql, ql, ql, _thoat_like(ql) + "%", gioi_han)).fetchall()
        c.close()
        return [{"id": a, "ten": b, "ban": c_ or ""} for a, b, c_ in ds]
    except Exception:
        return []


def lay(goi_id):
    if not re.fullmatch(r"[A-Za-z0-9._+-]{2,100}", goi_id or "") or not co_danh_muc():
        return None
    try:
        c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        r = c.execute("SELECT id, name, MAX(latest_version) FROM packages WHERE id = ? GROUP BY id, name", (goi_id,)).fetchone()
        c.close()
        return {"id": r[0], "ten": r[1], "ban": r[2] or ""} if r else None
    except Exception:
        return None


def khoi_dong_bo_lap():
    global _BAT_DAU
    with _KHOA:
        if _BAT_DAU:
            return
        _BAT_DAU = True

    def vong():
        time.sleep(45)
        while True:
            try:
                cap_nhat()
            except Exception as _loi:
                _bo_qua(_loi)
            time.sleep(3600)
    threading.Thread(target=vong, daemon=True, name="uem-winget-db").start()
