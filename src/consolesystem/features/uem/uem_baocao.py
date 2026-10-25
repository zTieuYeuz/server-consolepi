# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - THU THAP BAO CAO may (tuong duong "agent report" cua OpenUEM, nhung khong can agent).

Nguon du lieu bam theo ma nguon OpenUEM (openuem-agent/internal/commands/report/*_windows.go):
  may tinh      Win32_ComputerSystem (hang, model, RAM) + Win32_BIOS (serial; "System Serial Number" = Unknown) +
                Win32_Processor (ten, kien truc 0=x86 5=ARM 9=x64 12=ARM64..., so nhan)
  he dieu hanh  Win32_OperatingSystem (Version, Caption, InstallDate, LastBootUpTime), EditionID (registry), Domain, UserName
  o dia logic   Win32_LogicalDisk (chi o co Size) + BitLocker qua Win32_EncryptableVolume (ProtectionStatus 0/1)
  o dia vat ly  Win32_DiskDrive          man hinh   WmiMonitorID (root\\wmi, mang ma ASCII)    khe RAM  Win32_PhysicalMemory
  card mang     Win32_NetworkAdapter (NetConnectionStatus=2) + Win32_NetworkAdapterConfiguration
  may in        Win32_Printer          thu muc chia se  Win32_Share
  diet virus    root\\SecurityCenter2 AntiVirusProduct, productState: (state & 0xF000)==0x1000 la dang bat,
                (state & 0xF0)==0 la CSDL moi (dung y isAntivirusActive / isSignatureDBUpdated cua OpenUEM)
  cap nhat      Microsoft.Update.AutoUpdate (NotificationLevel, ngay tim/cai gan nhat) + Search "IsAssigned=1 and IsHidden=0 and IsInstalled=0
                and Type='Software'" (cap nhat dang cho) + QueryHistory (lich su)
  phan mem      Uninstall registry HKLM 64/32-bit + hive cac user dang nap; CAN co DisplayName va DisplayVersion; trung ten lay ban dau
GIOI HAN SO VOI AGENT THAT (ghi ro tren giao dien): WinRM chay duoi phien quan tri KHONG phai phien nguoi dung dang ngoi may,
nen may in cai rieng cho tung user va ung dung Microsoft Store khong thay duoc.
"""
from consolesystem.core import taisan as _taisan
from consolesystem.core.nhatky import bo_qua as _bo_qua
import sys as _sys
_sys.modules["ui.uem_baocao"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from ui import tk_dongco as DC
from ui import uem_ketnoi as UK
from ui import tk_dulieu as DL
from ui import uem_dulieu as UD

SCRIPT = _taisan.doc("features/uem/uem_baocao.SCRIPT.ps1")

_MA_UPDATE = {"0": "Chưa cấu hình", "1": "Tắt", "2": "Thông báo trước khi tải", "3": "Thông báo trước khi cài", "4": "Tự động tải và cài theo lịch"}
_EX = ThreadPoolExecutor(max_workers=4)
_DANG = set()
_KHOA = threading.Lock()
_BAT_DAU = False


def ten_cap_nhat_tu_dong(s):
    return _MA_UPDATE.get(str(s), str(s) or "Không rõ")


def _doc(c, mk):
    out, err = DC._chay_ps(c, SCRIPT)
    m = re.search(r"UEM_JSON=(\{.*\})", out, re.S)
    if not m:
        return None, f"Không đọc được báo cáo. {err}"[:300]
    d = json.loads(m.group(1))
    d["luc"] = time.time()
    return d, ""


def thu_thap(ip, user, mat_khau):
    """Lay bao cao qua WinRM voi thong tin truc tiep (dung cho thu nghiem). Tra ve (dict hoac None, loi)."""
    try:
        if not DC.cong_mo(ip, 5985, 3.0):
            return None, "Máy tắt, mất mạng hoặc chưa bật WinRM (cổng 5985 đóng)."
        return _doc(DC._ket_noi(ip, user, mat_khau), mat_khau)
    except DC.LoiKetNoi as e:
        return None, str(e)
    except Exception as e:
        return None, DC._loi_dep(e, mat_khau)


def thu_thap_may(m):
    """Lay bao cao cua 1 may qua agent (neu dang song) hoac WinRM. Tra ve (dict hoac None, loi, cach)."""
    try:
        c, mk, loai = UK.ket_noi(m)
        d, loi = _doc(c, mk)
        return d, loi, loai
    except UK.LoiMay as e:
        return None, str(e), ""
    except Exception as e:
        return None, DC._loi_dep(e), ""


def _chuan_mac(x):
    h = re.sub(r"[^0-9A-Fa-f]", "", x or "")
    return ":".join(h[i:i + 2] for i in range(0, 12, 2)).upper() if len(h) == 12 and h != "0" * 12 else ""


def _tu_dien(may_id, d):
    """Sau khi co thong tin may: tu dien cac o con trong cua ban ghi may (MAC cho Wake-on-LAN, ten may). KHONG ghi de o da co,
    nen nguoi dung sua tay sau do se duoc giu nguyen. IP khong doi (la khoa de ket noi)."""
    m = DL.tim(DL.MAY.doc(), may_id) or {}
    the_nic = [n for n in (d.get("networkadapters") or []) if _chuan_mac(n.get("mac_address"))]
    nic = next((n for n in the_nic if m.get("ip") and m["ip"] in (n.get("addresses") or "")), None) or (the_nic[0] if the_nic else None)
    mac = _chuan_mac(d.get("mac")) or (_chuan_mac(nic.get("mac_address")) if nic else "")
    host = re.sub(r"[^A-Za-z0-9._-]", "", d.get("hostname") or "")[:63]
    kw = {}
    if mac and not m.get("mac"):
        kw["mac"] = mac
    if host and (not m.get("ten") or m.get("ten") == m.get("ip")):
        kw["ten"] = host
    if kw:
        UD.sua_may(may_id, **kw)


def bao_cao_may(may_id):
    """Lay + luu bao cao cua 1 may (agent neu co, khong thi WinRM voi tai khoan da gan). Tra ve (ok, thong_diep)."""
    m = DL.tim(DL.MAY.doc(), may_id)
    if not m:
        return False, "Không tìm thấy máy."
    d, loi, cach = thu_thap_may(m)
    if d is None:
        UD.sua_may(may_id, ket_noi={"ok": False, "loi": loi, "luc": time.time()})
        return False, loi
    UD.sua_may(may_id, bao_cao=d, bao_cao_luc=time.time(), ket_noi={"ok": True, "loi": "", "luc": time.time(), "qua": cach})
    _tu_dien(may_id, d)
    return True, f"{d['computer'].get('manufacturer', '')} {d['computer'].get('model', '')}, {len(d.get('applications', []))} phần mềm."


def _viec(may_id):
    try:
        bao_cao_may(may_id)
    finally:
        with _KHOA:
            _DANG.discard(may_id)


def dang_chay(may_id):
    with _KHOA:
        return may_id in _DANG


def chay_nen(may_id):
    """Bao cao o nen (khong chan giao dien). False neu may dang duoc lay bao cao."""
    with _KHOA:
        if may_id in _DANG:
            return False
        _DANG.add(may_id)
    _EX.submit(_viec, may_id)
    return True


def _tick():
    cd = UD.cai_dat()
    if not cd.get("tu_dong_giam_sat", True):
        return
    chu_ky = max(5, int(cd.get("tan_suat_bao_cao", 60))) * 60
    now = time.time()
    for m in DL.MAY.doc():
        if not m.get("giam_sat", True) or not UK.co_the_ket_noi(m):
            continue
        lan_cuoi = max(m.get("bao_cao_luc", 0), (m.get("ket_noi") or {}).get("luc", 0))
        loi = not (m.get("ket_noi") or {"ok": True}).get("ok", True)
        cho = 300 if loi else chu_ky          # may loi/tat: thu lai moi 5 phut
        if now - lan_cuoi >= cho:
            chay_nen(m["id"])


def khoi_dong_bo_lap():
    global _BAT_DAU
    with _KHOA:
        if _BAT_DAU:
            return
        _BAT_DAU = True

    def vong():
        time.sleep(20)
        while True:
            try:
                _tick()
            except Exception as _loi:
                _bo_qua(_loi)
            time.sleep(30)
    threading.Thread(target=vong, daemon=True, name="uem-bao-cao").start()
