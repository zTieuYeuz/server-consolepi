# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - chon o cai Windows (tu dong/tay), diskpart.

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
import re



def tuychon_tu_dong(d):
    """Tuy chon cua che do "Phan chia tu dong" (1.9.0): dict(c_gb, d_tao, c_nhan, d_nhan).
    Mac dinh (c_gb = 0): 1 o C dung het o, y nhu cac ban truoc. c_gb > 0: o C co dinh GB va (neu d_tao)
    phan con lai thanh o du lieu."""
    def ten(x, mac_dinh):
        x = re.sub(r"[^A-Za-z0-9 _-]", "", str(x or "")).strip()[:24]
        return x or mac_dinh
    c = str(d.get("tu_dong_c_gb") or "").strip()
    c = int(c) if c.isdigit() and int(c) > 0 else 0
    return {"c_gb": c, "d_tao": bool(d.get("tu_dong_d")) and c > 0,
            "c_nhan": ten(d.get("tu_dong_c_nhan"), "Windows"), "d_nhan": ten(d.get("tu_dong_d_nhan"), "DuLieu")}

def mo_ta_tu_dong(d):
    """Cau mo ta tuy chon phan chia tu dong, dung o trang tong ket."""
    t = tuychon_tu_dong(d)
    if not t["c_gb"]:
        return "1 ổ C dùng hết ổ"
    if t["d_tao"]:
        return f"ổ C {t['c_gb']} GB + ổ dữ liệu “{t['d_nhan']}” (phần còn lại)"
    return f"ổ C {t['c_gb']} GB (phần còn lại để trống)"

# ---------------------------------------------------------------------------
# Chon O DICH theo dac diem (1.9.0). Cung 1 kich ban dung cho nhieu may khi
# may nay danh so o khac may kia (o Windows luc la Disk 0, luc la Disk 1):
# chon theo dung luong / model / "o dang chua Windows" thay vi so co dinh.
# AN TOAN: chi cho phep DUNG 1 o khop; 0 hoac nhieu o -> DUNG, bao loi, KHONG
# xoa gi. O USB / the nho khong bao gio duoc chon.
# ---------------------------------------------------------------------------
CACH_CHON_O = ("so", "co_windows", "dung_luong", "model", "nho_nhat", "lon_nhat")

def o_chon(d):
    """Chuan hoa cach chon o dich cua kich ban: dict(chon, gb, dungsai, model)."""
    chon = d.get("o_dia_chon") or "so"
    if chon not in CACH_CHON_O:
        chon = "so"
    gb = str(d.get("o_dia_gb") or "").strip()
    gb = int(gb) if gb.isdigit() and int(gb) > 0 else 0
    ds = str(d.get("o_dia_dungsai") or "").strip()
    ds = min(max(int(ds), 1), 40) if ds.isdigit() else 10
    model = re.sub(r"[^A-Za-z0-9 ._-]", "", str(d.get("o_dia_model") or "")).strip()[:40]
    if chon == "dung_luong" and not gb:
        chon = "so"
    if chon == "model" and not model:
        chon = "so"
    return {"chon": chon, "gb": gb, "dungsai": ds, "model": model}

def mo_ta_chon_o(d):
    """Cau mo ta (tieng Viet) cach chon o, dung o trang tong ket / bang kich ban."""
    c = o_chon(d)
    return {
        "so": f"ổ đĩa số {d.get('o_dia_so', '0')}",
        "co_windows": "ổ đang chứa Windows (phải có đúng 1 ổ)",
        "dung_luong": f"ổ có dung lượng khoảng {c['gb']} GB (±{c['dungsai']}%, phải có đúng 1 ổ)",
        "model": f"ổ có tên/model chứa “{c['model']}” (phải có đúng 1 ổ)",
        "nho_nhat": "ổ nhỏ nhất của máy (không tính USB)",
        "lon_nhat": "ổ lớn nhất của máy (không tính USB)",
    }[c["chon"]]

def _lenh_chon_o(d):
    r"""
    Cac dong batch chon o dich theo dac diem, chay SAU `list disk` (X:\ds_out.txt)
    va TRUOC khi diskpart xoa/chia. Ket qua: bien DISK = so o. Khong co/nhieu
    hon 1 o khop -> `goto loi_chon_o` (bao ro ly do, KHONG xoa gi). Chi dung
    cmd + diskpart (WinPE khong co findstr/powershell). Moi `if` chi 1 lenh
    (cu phap `if .. cmd & cmd` tren WinPE da gay loi that).
    """
    c = o_chon(d)
    ra = [
        "set DISK=", "set NOK=0", "set NKHOP=0", "set DANH_SACH=",
        "set MINKG=999999", "set MAXKG=-1", "set MINDN=", "set MAXDN=", "set MINTRUNG=0", "set MAXTRUNG=0",
        "set CMODEL=", "set CKG=",
        f"set CHON={c['chon']}",
        f"set MODELTIM={c['model']}",
    ]
    if c["chon"] == "dung_luong":
        ra += [f"set /a LO={c['gb']}*(100-{c['dungsai']})/100", f"set /a HI={c['gb']}*(100+{c['dungsai']})/100"]
    ra += [
        "echo === chon o dich theo: %CHON% === >> %LOG%",
        "echo.",
        "echo  Cac o dia cua may nay:",
    ]
    if c["chon"] == "co_windows":
        ra += [
            # Quet cac chu o co thu muc Windows (X: = WinPE, Z: = kho trien khai: bo qua)
            "for %%L in (C D E F G H I J K L M N O P Q R S T U V W Y) do call :cs_tim_windows %%L",
            'for /f "tokens=2" %%n in (\'type X:\\ds_out.txt ^| find "Disk "\') do call :cs_xet_o %%n',
        ]
    else:
        ra += ['for /f "tokens=2" %%n in (\'type X:\\ds_out.txt ^| find "Disk "\') do call :cs_xet_o %%n']
    ra += ["echo."]
    # Ket luan
    if c["chon"] in ("nho_nhat", "lon_nhat"):
        t = "MIN" if c["chon"] == "nho_nhat" else "MAX"
        ra += [
            f"if %{t}TRUNG% EQU 1 goto loi_chon_trung",
            f"if not defined {t}DN goto loi_chon_khong",
            f"set DISK=%{t}DN%",
            f"set /a NKHOP=1",
        ]
    elif c["chon"] == "co_windows":
        ra += ["if %NKHOP% EQU 0 goto loi_chon_khong", "if %NKHOP% GTR 1 goto loi_chon_trung"]
    else:
        ra += ["if %NKHOP% EQU 0 goto loi_chon_khong", "if %NKHOP% GTR 1 goto loi_chon_trung"]
    ra += [
        'echo === DA CHON o so %DISK% === >> %LOG%',
        # LUU Y: KHONG viet "=>" trong echo - dau > bi hieu la chuyen huong ra file (loi that luc thu)
        "echo  Da chon o dia so %DISK% de cai Windows. Cac o khac KHONG bi dung toi.",
        "echo.",
        "echo.",
        # diskpart cua kich ban khong co dong `select disk` - them o day
        "(echo select disk %DISK%& type %DPT%)> X:\\dp.txt",
    ]
    return ra

def _ham_chon_o(d):
    """Cac ham con (nhan batch) cho _lenh_chon_o - dat cuoi deploy.cmd, sau cac nhan loi."""
    c = o_chon(d)
    ra = [
        ":cs_xet_o",
        'if "%~1"=="###" exit /b 0',
        "set DN=%~1",
        "(echo select disk %DN%& echo detail disk)> X:\\dd.txt",
        "diskpart /s X:\\dd.txt > X:\\dd_out.txt 2>&1",
        "type X:\\dd_out.txt >> %LOG%",
        "set BUS=NA",
        'for /f "tokens=2 delims=:" %%t in (\'type X:\\dd_out.txt ^| find "Type   :"\') do set BUS=%%t',
        "set BUS=%BUS: =%",
        "set MODEL=",
        "set GOT=0",
        'for /f "delims=" %%l in (\'type X:\\dd_out.txt\') do call :cs_doc_model "%%l"',
        "set KG=0",
        'for /f "tokens=3-9" %%a in (\'type X:\\ds_out.txt ^| find "Disk %DN% "\') do call :cs_tinh_gb %%a %%b %%c %%d %%e %%f %%g',
        'echo === o %DN%: "%MODEL%" bus=%BUS% %KG% GB === >> %LOG%',
        'echo     Disk %DN%:  %MODEL%   [%BUS%]   %KG% GB',
        'if /i "%BUS%"=="USB" exit /b 0',
        'if /i "%BUS%"=="SD" exit /b 0',
        'if /i "%BUS%"=="MMC" exit /b 0',
        "if %KG% EQU 0 exit /b 0",
        "set /a NOK+=1",
    ]
    ch = c["chon"]
    if ch == "dung_luong":
        ra += ["if %KG% LSS %LO% exit /b 0", "if %KG% GTR %HI% exit /b 0", "goto cs_khop"]
    elif ch == "model":
        ra += ['echo "%MODEL%"| find /i "%MODELTIM%" >nul', "if errorlevel 1 exit /b 0", "goto cs_khop"]
    elif ch == "nho_nhat":
        ra += [
            "if %KG% EQU %MINKG% set MINTRUNG=1",
            "if %KG% LSS %MINKG% set MINTRUNG=0",
            "if %KG% LSS %MINKG% set MINDN=%DN%",
            "if %KG% LSS %MINKG% set CMODEL=%MODEL%",
            "if %KG% LSS %MINKG% set CKG=%KG%",
            "if %KG% LSS %MINKG% set MINKG=%KG%",
            "exit /b 0",
        ]
    elif ch == "lon_nhat":
        ra += [
            "if %KG% EQU %MAXKG% set MAXTRUNG=1",
            "if %KG% GTR %MAXKG% set MAXTRUNG=0",
            "if %KG% GTR %MAXKG% set MAXDN=%DN%",
            "if %KG% GTR %MAXKG% set CMODEL=%MODEL%",
            "if %KG% GTR %MAXKG% set CKG=%KG%",
            "if %KG% GTR %MAXKG% set MAXKG=%KG%",
            "exit /b 0",
        ]
    elif ch == "co_windows":
        # Chi nhan o co chua Windows (danh dau o :tim_windows -> bien WIN_<so>=1)
        ra += ["if not defined WIN_%DN% exit /b 0", "goto cs_khop"]
    else:
        ra += ["exit /b 0"]
    ra += [
        "",
        ":cs_khop",
        "set /a NKHOP+=1",
        "set DISK=%DN%",
        "set CMODEL=%MODEL%",
        "set CKG=%KG%",
        "exit /b 0",
        "",
        ":cs_doc_model",
        'if "%GOT%"=="1" goto dm_lay',
        'echo "%~1"| find "is now the selected disk" >nul',
        "if errorlevel 1 exit /b 0",
        "set GOT=1",
        "exit /b 0",
        ":dm_lay",
        "set MODEL=%~1",
        "set GOT=2",
        "exit /b 0",
        "",
        ":cs_tinh_gb",
        "set KG=0",
        "set PV=",
        ":tg1",
        'if "%~1"=="" exit /b 0',
        'if /i "%~1"=="GB" goto tg_gb',
        'if /i "%~1"=="TB" goto tg_tb',
        'if /i "%~1"=="MB" goto tg_mb',
        'if /i "%~1"=="KB" exit /b 0',
        'if /i "%~1"=="B" exit /b 0',
        "set PV=%~1",
        "shift",
        "goto tg1",
        ":tg_gb",
        "set /a KG=%PV%",
        "exit /b 0",
        ":tg_tb",
        "set /a KG=%PV%*1024",
        "exit /b 0",
        ":tg_mb",
        "set /a KG=%PV%/1024",
        "exit /b 0",
        "",
        ":cs_tim_windows",
        "if not exist %~1:\\Windows\\System32\\config\\SYSTEM exit /b 0",
        "(echo select volume %~1& echo detail volume)> X:\\dv.txt",
        "diskpart /s X:\\dv.txt > X:\\dv_out.txt 2>&1",
        "type X:\\dv_out.txt >> %LOG%",
        'for /f "tokens=1-3" %%a in (\'type X:\\dv_out.txt ^| find "Disk " ^| find /v "###"\') do call :cs_win_o %%a %%b %%c',
        "exit /b 0",
        ":cs_win_o",
        'if "%~1"=="*" set WIN_%~3=1',
        'if not "%~1"=="*" set WIN_%~2=1',
        "exit /b 0",
        "",
        ":loi_chon_khong",
        "echo.",
        "echo  KHONG co o dia nao khop cach chon cua kich ban (xem danh sach tren).",
        "echo  KHONG xoa/chia gi ca. Sua kich ban (buoc Chia o dia) hoac kiem tra o dia cua may.",
        "set BUOC=Khong co o dia nao khop cach chon cua kich ban - KHONG xoa gi. Xem danh sach o tren man hinh",
        "goto bao_loi",
        "",
        ":loi_chon_trung",
        "echo.",
        "echo  CO NHIEU HON 1 O khop cach chon cua kich ban (xem danh sach tren).",
        "echo  De an toan KHONG doan - KHONG xoa/chia gi ca. Chon cach khac (model, so o...).",
        "set BUOC=Co nhieu hon 1 o dia khop cach chon cua kich ban - KHONG xoa gi. Dung cach chon chinh xac hon",
        "goto bao_loi",
        "",
    ]
    return ra

def sinh_diskpart_txt(d, mbr=False):
    """
    Script cho `diskpart /s` - chia o dia theo dung lua chon wizard.

    Kieu MDT: TU chia o dia trong WinPE (thay vi giao cho Windows Setup
    qua DiskConfiguration cua autounattend.xml) - xem ly do that trong
    docstring cua sinh_deploy_cmd().

    Quy uoc chu o (giong het MDT):
      S: = phan vung he thong (EFI khi UEFI, phan vung "active" khi BIOS)
      W: = phan vung se chua Windows (luc boot that no se thanh C:)
    Khong dung C: trong WinPE vi chu o do co the da bi chiem san.

    mbr=True: ban cho may BIOS/Legacy (deploy.cmd tu chon theo
    PEFirmwareType). Wizard ve bo cuc theo GPT (EFI + MSR + ...) nen doi:
    EFI -> phan vung he thong NTFS "active" (bcdboot /f BIOS ghi bootmgr vao
    do), MSR -> bo (MBR khong co), MBR toi da 4 phan vung chinh -> tu phan
    vung thu 4 tro di nam trong 1 phan vung mo rong (logical).
    """
    o_dia_so = d.get("o_dia_so", "0")
    # Chon o theo dac diem: deploy.cmd tu them dong `select disk N` o dau (xem _lenh_chon_o)
    dau = [] if o_chon(d)["chon"] != "so" else [f"select disk {o_dia_so}"]
    dong = dau + ["clean",
                  "convert mbr" if mbr else "convert gpt"]
    so_chinh = 0

    def tao(kich_thuoc=None):
        nonlocal so_chinh
        cd = f" size={kich_thuoc}" if kich_thuoc else ""
        if not mbr:
            return [f"create partition primary{cd}"]
        so_chinh += 1
        if so_chinh < 4:
            return [f"create partition primary{cd}"]
        ra = ["create partition extended"] if so_chinh == 4 else []
        return ra + [f"create partition logical{cd}"]

    def he_thong(kich_thuoc, nhan):
        if not mbr:
            return [f"create partition efi size={kich_thuoc}",
                    f'format quick fs=fat32 label="{nhan}"', "assign letter=S"]
        # 500 MB: du cho bootmgr + WinRE nhu Windows tu chia tren may BIOS.
        return tao(max(500, int(kich_thuoc) if str(kich_thuoc).isdigit() else 500)) + [
            f'format quick fs=ntfs label="{nhan}"', "active", "assign letter=S"]

    if d.get("o_dia_che_do") != "chia_tay":
        dong += he_thong(260, "System")
        if not mbr:
            dong.append("create partition msr size=16")
        tt = tuychon_tu_dong(d)
        if not tt["c_gb"]:
            dong += tao() + ['format quick fs=ntfs label="Windows"', "assign letter=W"]
        else:
            dong += tao(tt["c_gb"] * 1024) + [f'format quick fs=ntfs label="{tt["c_nhan"]}"', "assign letter=W"]
            if tt["d_tao"]:
                # Khong gan chu cai cu the o WinPE (chu D co the dang bi o CD/o du lieu khac chiem -> diskpart loi);
                # Windows tu gan chu cai o lan khoi dong dau.
                dong += tao() + [f'format quick fs=ntfs label="{tt["d_nhan"]}"', "assign"]
    else:
        da_gan_windows = False
        for i, p in enumerate(d.get("phan_vung") or [], start=1):
            fs = (p.get("fs") or "ntfs").lower()
            nhan = p.get("nhan") or ""
            if fs == "msr":
                if not mbr:
                    dong.append(f"create partition msr size={p.get('cd', '16')}")
                continue
            if fs == "fat32" and i == 1:
                dong += he_thong(p.get("cd", "260"), nhan or "System")
                continue
            dong += tao(None if p.get("cd") == "con_lai" else p.get("cd", "1024"))
            dinh_dang = "fat32" if fs == "fat32" else "ntfs"
            dong.append(f'format quick fs={dinh_dang} label="{nhan}"')
            # Phan vung dau tien khong phai EFI/MSR chinh la o he dieu hanh
            if not da_gan_windows:
                dong.append("assign letter=W")
                da_gan_windows = True
            else:
                # Chu cai o WinPE KHONG duoc luu vao Windows vua bung (Windows tu gan lai o lan boot dau), con ep
                # `assign letter=X` se LOI neu X dang bi chiem (vd o du lieu cua may nhieu o hien la D: trong WinPE) -
                # nen chi gan tu dong. Cot "gan" chi la ghi chu y dinh.
                dong.append("assign")

    dong.append("exit")
    return "\r\n".join(dong) + "\r\n"
