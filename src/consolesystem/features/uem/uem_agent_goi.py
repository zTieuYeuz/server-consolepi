# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""
Quan ly may tram - AGENT: tao FILE CAI (MSI hoac script PowerShell) co san dia chi Console System + ma ghi danh.

Moi lan bam "Tao file": mot viec chay nen ghi lai tung buoc (dong thoi gian) -> kiem tra dia chi/cong -> tao ma ghi danh -> ghep thong tin
vao file -> dong goi (MSI bang wixl) -> kiem tra lai file -> luu. File luu o <data>/goi-agent/ de tai ve sau; xoa file thi thu hoi luon ma ghi danh cua no.
MSI khong chua mat khau/chung chi: chi chua dia chi, dau van tay CA va ma ghi danh (co han + gioi han so may); moi may nhan chung chi rieng luc cai.
"""
import sys as _sys
_sys.modules["ui.uem_agent_goi"] = _sys.modules[__name__]   # B2: ten cu tro toi chinh module nay ngay tu dau (vong import)
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time

from ui import duongdan as _DD
from ui import tk_dulieu as DL
from ui import uem_agent as UA
from ui import uem_pki as PKI

BIN = os.path.join(_DD.DIR_UI, "agent_bin")      # tai nguyen nam o ui/ (khong chuyen)
THU_MUC = os.path.join(DL.DIR, "goi-agent")
_FILE_DS = os.path.join(THU_MUC, "danh-sach.json")
_KHOA = threading.Lock()
_VIEC = {}                      # id viec -> {id, kieu, ten, buoc[], tt, loi, goi_id}
TOI_DA_GOI = 40
MSI_PRODUCT_CODE = "{6B1F2C9E-4D7A-4E58-9C31-0A5D8E7F4B21}"


def _doc():
    try:
        with open(_FILE_DS, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except (OSError, ValueError):
        return []


def _ghi(ds):
    os.makedirs(THU_MUC, mode=0o700, exist_ok=True)
    tam = _FILE_DS + ".tmp"
    with open(tam, "w", encoding="utf-8") as f:
        json.dump(ds, f, ensure_ascii=False)
    os.replace(tam, _FILE_DS)


def ds_goi():
    with _KHOA:
        return sorted(_doc(), key=lambda x: -x["tao_luc"])


def tim_goi(gid):
    return next((x for x in ds_goi() if x["id"] == gid), None)


def duong_file(gid):
    g = tim_goi(gid)
    if not g:
        return None, None
    p = os.path.join(THU_MUC, g["id"] + "." + g["loai"])
    return (p, g["ten_file"]) if os.path.isfile(p) else (None, None)


def luu_passkey_trien_khai(gid, passkey):
    """Luu (ma hoa) passkey cua 1 goi da tao de 'Trien khai phan mem' tu dien khi cai MSI. Chi nhan khi dung voi dau bam cua goi."""
    with _KHOA:
        ds = _doc()
        g = next((x for x in ds if x["id"] == gid), None)
        if not g or not g.get("co_passkey"):
            return False, "Gói này không đặt passkey."
        if not UA.kiem_passkey(passkey, UA.pk_cua_ma(g.get("ma_id"))):
            return False, "Passkey không đúng với gói này."
        g["pk_ma"] = DL.ma_hoa(passkey)
        _ghi(ds)
    return True, "Đã lưu passkey (mã hóa) để Triển khai phần mềm tự điền khi cài gói này."


def bo_passkey_trien_khai(gid):
    with _KHOA:
        ds = _doc()
        g = next((x for x in ds if x["id"] == gid), None)
        if not g:
            return False
        g["pk_ma"] = ""
        _ghi(ds)
    return True


def tim_theo_file(duong):
    """Goi agent trung khop NOI DUNG voi file MSI nay (so SHA-256; chi xet file nho) hoac None.
    Dung cho Trien khai phan mem: file agent.msi tai ve roi dua vao Tai nguyen van nhan ra duoc."""
    try:
        if os.path.getsize(duong) > 8 * 1024 * 1024:
            return None
        with open(duong, "rb") as f:
            sha = hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None
    return next((x for x in ds_goi() if x.get("sha256") == sha and x["loai"] == "msi"), None)


def passkey_trien_khai(g):
    """Passkey goc (giai ma) cua goi, hoac '' neu chua luu."""
    return DL.giai_ma(g.get("pk_ma", "")) if g and g.get("pk_ma") else ""


def xoa_goi(gid):
    with _KHOA:
        ds = _doc()
        g = next((x for x in ds if x["id"] == gid), None)
        if not g:
            return False
        _ghi([x for x in ds if x["id"] != gid])
    try:
        os.remove(os.path.join(THU_MUC, g["id"] + "." + g["loai"]))
    except OSError:
        pass
    if g.get("ma_id"):
        UA.xoa_ghi_danh(g["ma_id"])             # thu hoi ma: may chua cai khong dung duoc file nay nua
    return True


def dia_chi_chon():
    """Cac dia chi co the nhung vao file: [(nhan, 'host:cong')]. Domain (neu co) dung lai duoc khi IP doi."""
    cd = PKI.cai_dat()
    kq = []
    if cd["domain"]:
        kq.append((f"Domain: {cd['domain']}:{cd['cong']}", f"{cd['domain']}:{cd['cong']}"))
    for ip in PKI.ips_pi():
        if not ip.startswith("127."):
            kq.append((f"IP LAN hiện tại: {ip}:{cd['cong']}", f"{ip}:{cd['cong']}"))
    return kq


def _ten_file(ten, loai):
    t = re.sub(r"\.(msi|ps1|bat)$", "", (ten or "").strip(), flags=re.I)
    t = re.sub(r"[^A-Za-z0-9._ \-]", "", t).strip(" .")[:60] or "ConsoleSystemAgent"
    return t + "." + loai


def _script(url, pin, ma, ten, pk=""):
    kiem = ""
    if pk:
        kiem = (f"$Pk = '{pk}'\r\n"
                "function Test-Pk($h, $pw) { $p = $h.Split(':'); if ($p.Count -ne 4 -or $p[0] -ne 'p1') { return $false }; "
                "$salt = [byte[]]@(for ($i = 0; $i -lt 32; $i += 2) { [Convert]::ToByte($p[2].Substring($i, 2), 16) }); "
                "$d = New-Object Security.Cryptography.Rfc2898DeriveBytes($pw, $salt, [int]$p[1]); "
                "return (((($d.GetBytes(32)) | ForEach-Object { $_.ToString('x2') }) -join '') -eq $p[3]) }\r\n"
                "$need = $Pk; $lp = Join-Path $env:ProgramData 'ConsoleSystem\\passkey.json'\r\n"
                "if (Test-Path -LiteralPath $lp) { try { $need = (Get-Content -LiteralPath $lp -Raw | ConvertFrom-Json).pk } catch {} }\r\n"
                "$ok = $false\r\n"
                "for ($i = 0; $i -lt 3 -and -not $ok; $i++) { $ss = Read-Host 'Nhap passkey de cai agent' -AsSecureString; "
                "$pw = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($ss)); if (Test-Pk $need $pw) { $ok = $true } else { Write-Host 'Passkey sai.' -ForegroundColor Red } }\r\n"
                "if (-not $ok) { Read-Host 'Khong dung passkey, khong cai. Nhan Enter de dong'; exit 1 }\r\n")
    return ("﻿# Console System - script cài agent '" + ten + "' (tạo " + time.strftime("%d/%m/%Y %H:%M") + ").\r\n"
            "# Chạy: chuột phải, Run with PowerShell (tự xin quyền Administrator). Mã ghi danh có hạn dùng; không chứa mật khẩu hay chứng chỉ.\r\n"
            f"$Servers = @({', '.join(chr(39) + u + chr(39) for u in url.split(','))}); $Pin = '{pin}'; $Code = '{ma}'\r\n"
            "$adm = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)\r\n"
            "if (-not $adm) { Start-Process -FilePath powershell.exe -Verb RunAs -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File \"' + $PSCommandPath + '\"'); exit }\r\n"
            + kiem +
            "$ErrorActionPreference = 'Stop'\r\n"
            "try {\r\n"
            "  Add-Type '" + UA.PIN_CS + "'\r\n"
            "  [CsPin]::On($Pin)\r\n"
            "  [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12\r\n"
            "  $s = $null; $lastErr = ''\r\n"
            "  foreach ($sv in $Servers) { try { $s = Invoke-RestMethod -UseBasicParsing -TimeoutSec 25 -Uri ($sv + '/uem/agent/cai/' + $Code + '.ps1?h=' + [uri]::EscapeDataString($env:COMPUTERNAME)); break } catch { $lastErr = $_; Write-Host ('Khong noi duoc ' + $sv + ', thu dia chi tiep theo...') } }\r\n"
            "  if (-not $s) { throw $lastErr }\r\n"
            "  $r = (& ([scriptblock]::Create([string]$s)) | Out-String).Trim()\r\n"
            "  Write-Host $r\r\n"
            "} catch { Write-Host ('LOI: ' + $_) -ForegroundColor Red }\r\n"
            "Read-Host 'Nhan Enter de dong'\r\n")


def _bat(ps1_text):
    """File .bat bam doi la chay: tu xin quyen Administrator, tach script PowerShell nhung o cuoi file ra %TEMP% roi chay voi -ExecutionPolicy Bypass
    (khong bi loi 'running scripts is disabled', khong can chuot phai 'Run with PowerShell')."""
    import base64
    b = base64.b64encode(ps1_text.encode("utf-8")).decode("ascii")
    dong = "\r\n".join("::B64:" + b[i:i + 200] for i in range(0, len(b), 200))
    dau = ("@echo off\r\n"
           "net session >nul 2>&1 || (powershell -NoProfile -Command \"Start-Process -Verb RunAs -FilePath '%~f0'\" & exit /b)\r\n"
           "set \"CSP=%TEMP%\\cs-cai-agent.ps1\"\r\n"
           "powershell -NoProfile -ExecutionPolicy Bypass -Command \"$t=(Get-Content -LiteralPath '%~f0' | Where-Object { $_ -like '::B64:*' } | ForEach-Object { $_.Substring(6) }) -join ''; [IO.File]::WriteAllBytes($env:CSP,[Convert]::FromBase64String($t))\"\r\n"
           "powershell -NoProfile -ExecutionPolicy Bypass -File \"%CSP%\"\r\n"
           "del \"%CSP%\" >nul 2>&1\r\n"
           "exit /b\r\n")
    return dau + dong + "\r\n"


def _msi(thu_muc, server, pin, ma, pk=""):
    wixl = shutil.which("wixl")
    if not wixl:
        raise RuntimeError("Máy chủ chưa có công cụ wixl để đóng gói MSI (cài gói wixl: sudo apt install wixl).")
    with open(os.path.join(BIN, "ConsoleSystemAgent.wxs.tpl"), encoding="utf-8") as f:
        wxs = f.read().replace("__SERVER__", server).replace("__PIN__", pin).replace("__CODE__", ma).replace("__PKH__", pk or "-")
    with open(os.path.join(thu_muc, "ConsoleSystemAgent.wxs"), "w", encoding="utf-8") as f:
        f.write(wxs)
    for ten in ("cs-agent.exe", "cs-install.ps1", "uninstall.bat"):
        shutil.copyfile(os.path.join(BIN, ten), os.path.join(thu_muc, ten))
    r = subprocess.run([wixl, "-a", "x64", "-o", "out.msi", "ConsoleSystemAgent.wxs"], cwd=thu_muc, capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not os.path.isfile(os.path.join(thu_muc, "out.msi")):
        raise RuntimeError("wixl lỗi: " + (r.stderr or r.stdout)[-300:])
    return os.path.join(thu_muc, "out.msi")


def _buoc(j, ten, fn):
    b = {"ten": ten, "tt": "dang", "t0": time.time(), "ghi_chu": ""}
    j["buoc"].append(b)
    try:
        b["ghi_chu"] = fn() or ""
        b["tt"] = "xong"
    except Exception as e:
        b["ghi_chu"] = str(e)
        b["tt"] = "loi"
        raise
    finally:
        b["t1"] = time.time()


def _chay(j, loai, ten, ds_dia_chi, ngay, toi_da, pk, pk_goc=""):
    st = {}
    tmp = tempfile.mkdtemp(prefix="cs-goi-")
    try:
        def b1():
            if not PKI.san_sang():
                raise RuntimeError("Cổng mTLS của agent chưa bật (bấm Bật kết nối an toàn).")
            st["urls"] = ["https://" + d for d in ds_dia_chi]
            st["url"] = st["urls"][0]
            return ("Địa chỉ nối về: " + ", ".join(ds_dia_chi) + (" (địa chỉ đầu là chính, còn lại là dự phòng)" if len(ds_dia_chi) > 1 else "")) + ", cổng mTLS đang nghe."

        def b2():
            st["pin"] = PKI.ca_sha256()
            return "SHA-256 của CA: " + st["pin"][:16] + "…"

        def b3():
            e = UA.tao_ghi_danh(ten, st["url"], ngay, toi_da, pk, st["urls"])
            st["ma"], st["ma_id"] = e["ma"], e["id"]
            return ((f"Hạn {ngay} ngày, " if ngay else "Không hết hạn, ") + (f"tối đa {toi_da} máy" if toi_da else "không giới hạn số máy")) + (", có passkey (chỉ lưu dấu băm PBKDF2)" if pk else ", không đặt passkey")

        def b4():
            if loai in ("ps1", "bat"):
                st["duong"] = os.path.join(tmp, "out." + loai)
                nd = _script(",".join(st["urls"]), st["pin"], st["ma"], ten, pk)
                with open(st["duong"], "w", encoding="utf-8", newline="") as f:
                    f.write(nd if loai == "ps1" else _bat(nd))
                return "Đã ghi địa chỉ, dấu vân tay CA và mã vào " + ("script." if loai == "ps1" else "file .bat (chạy bằng chuột đúp).")
            st["duong"] = _msi(tmp, ",".join(ds_dia_chi), st["pin"], st["ma"], pk)
            return "Đã ghép địa chỉ, dấu vân tay CA và mã vào gói và đóng gói MSI (x64)."

        def b5():
            with open(st["duong"], "rb") as f:
                d = f.read()
            if loai == "msi" and (d[:4] != b"\xd0\xcf\x11\xe0" or len(d) < 10000):
                raise RuntimeError("File MSI tạo ra không hợp lệ.")
            if st["ma"].encode() not in d or st["pin"].encode() not in d:
                raise RuntimeError("Thông tin chưa nằm trong file.")
            st["kich_thuoc"], st["sha256"] = len(d), hashlib.sha256(d).hexdigest()
            return f"{len(d):,} byte, SHA-256 {st['sha256'][:16]}…".replace(",", ".")

        def b6():
            gid = os.urandom(5).hex()
            os.makedirs(THU_MUC, mode=0o700, exist_ok=True)
            shutil.copyfile(st["duong"], os.path.join(THU_MUC, gid + "." + loai))
            with _KHOA:
                ds = _doc()
                if len(ds) >= TOI_DA_GOI:                                  # day: bo file cu nhat
                    cu = min(ds, key=lambda x: x["tao_luc"])
                    ds = [x for x in ds if x["id"] != cu["id"]]
                    try:
                        os.remove(os.path.join(THU_MUC, cu["id"] + "." + cu["loai"]))
                    except OSError:
                        pass
                    if cu.get("ma_id"):
                        UA.xoa_ghi_danh(cu["ma_id"])
                ds.append({"id": gid, "loai": loai, "ten_file": _ten_file(ten, loai), "tao_luc": time.time(), "url": ", ".join(st["urls"]), "ma_id": st["ma_id"],
                           "ngay": ngay, "toi_da": toi_da, "co_passkey": bool(pk), "pk_ma": DL.ma_hoa(pk_goc) if (pk and pk_goc) else "", "kich_thuoc": st["kich_thuoc"], "sha256": st["sha256"], "ban_agent": UA.PHIEN_BAN, "buoc": []})
                _ghi(ds)
            j["goi_id"] = gid
            return "Đã lưu, có thể tải ở danh sách bên dưới."

        for ten_buoc, fn in (("Kiểm tra địa chỉ và cổng mTLS", b1), ("Lấy dấu vân tay CA để ghim", b2), ("Tạo mã ghi danh", b3),
                             ("Ghép thông tin vào " + ("script" if loai == "ps1" else "file .bat" if loai == "bat" else "gói MSI"), b4), ("Kiểm tra lại file", b5), ("Lưu để tải về", b6)):
            _buoc(j, ten_buoc, fn)
        with _KHOA:                                                          # luu dong thoi gian cung file
            ds = _doc()
            for x in ds:
                if x["id"] == j["goi_id"]:
                    x["buoc"] = [{"ten": b["ten"], "tt": b["tt"], "giay": round(b["t1"] - b["t0"], 2), "ghi_chu": b["ghi_chu"]} for b in j["buoc"]]
            _ghi(ds)
        j["tt"] = "xong"
    except Exception as e:
        j["tt"], j["loi"] = "loi", str(e)
        if st.get("ma_id") and not j.get("goi_id"):
            UA.xoa_ghi_danh(st["ma_id"])                                  # loi giua chung: khong de lai ma mo coi
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def bat_dau(loai, ten, dia_chi, ngay=0, toi_da=0, passkey="", cho_trien_khai=False):
    """Kiem tra dau vao roi chay nen. Tra ve id viec; ValueError neu dau vao sai."""
    if loai not in ("msi", "ps1", "bat"):
        raise ValueError("Loại file không hợp lệ.")
    ds_dia_chi = []
    for d in re.split(r"[,\s]+", (dia_chi or "").strip()):
        if not d:
            continue
        m = re.fullmatch(r"([0-9A-Za-z.\-]{1,253}):(\d{1,5})", d)
        if not m or int(m.group(2)) != PKI.cong():
            raise ValueError(f"Địa chỉ nối về phải có dạng tên-máy:{PKI.cong()} (đúng cổng mTLS đang bật).")
        if d not in ds_dia_chi:
            ds_dia_chi.append(d)
    if not ds_dia_chi or len(ds_dia_chi) > 5:
        raise ValueError("Chọn từ 1 đến 5 địa chỉ nối về.")
    ngay = max(0, min(int(ngay or 0), 3650))                    # 0 = suot doi (mac dinh: khong het han, khong gioi han so may)
    toi_da = max(0, min(int(toi_da or 0), 100000))
    ten = re.sub(r"[^A-Za-z0-9._ \-]", "", (ten or "").strip())[:60] or "ConsoleSystemAgent"
    pk = UA.bam_passkey(passkey) if passkey else ""                    # ValueError neu passkey khong hop le; khong luu passkey goc
    j = {"id": os.urandom(6).hex(), "kieu": loai, "ten": _ten_file(ten, loai), "buoc": [], "tt": "dang", "loi": "", "goi_id": "", "bat_dau": time.time()}
    with _KHOA:
        for k in [k for k, v in _VIEC.items() if time.time() - v["bat_dau"] > 3600]:
            _VIEC.pop(k, None)
        _VIEC[j["id"]] = j
    threading.Thread(target=_chay, args=(j, loai, ten, ds_dia_chi, ngay, toi_da, pk, passkey if (pk and cho_trien_khai) else ""), daemon=True).start()
    return j["id"]


def viec(vid):
    j = _VIEC.get(vid)
    if not j:
        return None
    now = time.time()
    return {"id": j["id"], "ten": j["ten"], "tt": j["tt"], "loi": j["loi"], "goi_id": j["goi_id"],
            "buoc": [{"ten": b["ten"], "tt": b["tt"], "giay": round((b.get("t1") or now) - b["t0"], 2), "ghi_chu": b["ghi_chu"]} for b in j["buoc"]]}
