# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Ma nguon C# cua AGENT Console System (dich vu Windows). KHONG co file .exe san: ma nay duoc BIEN DICH NGAY TREN MAY WINDOWS luc cai
bang csc.exe co san trong .NET Framework 4 (C:\\Windows\\Microsoft.NET\\Framework64\\v4.0.30319\\csc.exe) - khong can cai Visual Studio,
Console System khong phai giu/ky file nhi phan nao. C# 5 (csc 4.8): khong dung ?. / $"" / nameof.

Agent lam:
  * Dich vu Windows ConsoleSystemAgent (LocalSystem, tu khoi dong, tu chay lai khi loi).
  * mTLS toi Console System (https://<Pi>:8443): xac thuc may chu bang CA GHIM (ca.pem), xac thuc agent bang chung chi khach (client.pfx).
  * Long-poll "nhip" 25 giay: nhan viec, chay, tra ket qua. Viec: ps (PowerShell), tep_len/tep_xuong (chuyen file dang luong, khong gioi han 25MB),
    tunnel (VNC di NGUOC qua TLS, TightVNC chi nghe 127.0.0.1), hoi_phep (hop thoai xin phep nguoi dang dung may), profile/profile_go/profile_chay.
  * TU TRI: luu cac profile ve dia va TU AP DUNG theo chu ky ke ca khi mat ket noi voi Console System; ket qua gui bu o nhip sau.
  * Tu cap nhat: Console System gui ma nguon moi, agent tu bien dich, thay file va khoi dong lai dich vu.
  * Doc du lieu "tro ly phien nguoi dung" (may in rieng, man hinh, nguoi dang nhap) tu thu muc nd\\ va gui kem nhip.
"""

from consolesystem.core import taisan as _taisan

VER_FILE = "2.3.2"      # TANG so nay moi khi sua ma C# (test_agent_phien_ban ep buoc) -> moi agent cu tu cap nhat khi bao nhip; roi dung tools/dung-agent-exe.py bien dich lai cs-agent.exe

SOURCE = _taisan.doc("features/uem/uem_agent_cs.SOURCE.cs")


def nguon():
    return SOURCE.replace("__VER__", VER_FILE)

from consolesystem.core import taisan as _taisan
import sys as _sys
_sys.modules["ui.uem_agent_cs"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)