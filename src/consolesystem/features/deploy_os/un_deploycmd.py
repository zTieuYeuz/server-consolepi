# Console System - (c) 2026 zTieuYeuz. All rights reserved.
"""Unattend - deploy.cmd (kieu MDT) va cac lenh WinPE: chep app/script, dat ten, bao lich su.

(B4: tach nguyen van tu unattend.py; ten ham/hang giu nguyen, nguon van re-export.)"""
from ui import deployos as _d
from ui import datten as _tm
from consolesystem.features.deploy_os.un_baocao import (_lenh_khong_thay_o, _lenh_kiem_tra_card_mang)  # noqa: F401
from consolesystem.features.deploy_os.un_chonodia import (_ham_chon_o, _lenh_chon_o, o_chon)  # noqa: F401
from consolesystem.features.deploy_os.un_goapp_font import (TEN_PS_CAI_FONT, _bo_font_cai_duoc, _lenh_cai_ungdung, _lenh_chep_go_app, _lenh_net35_offline, _lenh_tiem_driver_offline)  # noqa: F401
from consolesystem.features.deploy_os.un_hangso import (TEN_NHUNG_DRIVER, TEN_TAI_KHOAN_SAMBA, THU_MUC_NHUNG, _doc_mat_khau_samba)  # noqa: F401
from consolesystem.features.deploy_os.un_offline import (BUILD_TOI_THIEU_HEADLESS)  # noqa: F401


def _lenh_chep_app_script(d):
    """
    Cac dong batch chep phan mem + script tu kho tren Pi (o mang Z: dang
    map trong WinPE) sang thang o dia may dich, vao C:\\ConsolePi\\.

    Chep TUNG FILE DA CHON chu khong chep ca thu muc - kho phan mem tren
    Pi co the rat nang, kich ban nay chi can vai file.
    """
    apps = _d.chuan_hoa_apps(d.get("apps"))
    scripts = d.get("scripts") or []
    ungdung = [u for u in _d.chuan_hoa_ungdung(d.get("ungdung"))
               if _lenh_cai_ungdung(u)]  # bo qua ung dung chua dat lenh cai
    fonts = _bo_font_cai_duoc(d)[0]
    if not apps and not scripts and not ungdung and not fonts:
        return []

    dong = ["echo     ... chep them phan mem va script sang may dich..."]
    if apps:
        dong.append("if not exist W:\\ConsolePi\\apps mkdir W:\\ConsolePi\\apps")
        for a in apps:
            dong.append(
                f'copy /y "Z:\\apps\\{a["ten"]}" W:\\ConsolePi\\apps\\ '
                ">> %LOG% 2>&1")
            dong.append("if errorlevel 1 goto loi_chep_app")
    if scripts:
        dong.append("if not exist W:\\ConsolePi\\scripts mkdir W:\\ConsolePi\\scripts")
        for ten in scripts:
            dong.append(
                f'copy /y "Z:\\scripts\\{ten}" W:\\ConsolePi\\scripts\\ '
                ">> %LOG% 2>&1")
            dong.append("if errorlevel 1 goto loi_chep_app")
    if ungdung:
        # Ung dung kieu thu muc (mo hinh MDT) - CA THU MUC, khong phai 1
        # file, nen dung `robocopy /E` (chep het thu muc con) thay vi
        # `copy`. LUU Y THAT VE MA LOI ROBOCOPY (khac han cac lenh khac):
        # robocopy tra ve 0-7 la THANH CONG (1 = "co file duoc chep" - VAN
        # la thanh cong, khong phai loi!), CHI >=8 moi la that bai that su.
        # Neu dung `if errorlevel 1` nhu cac lenh copy khac o tren se BAO
        # LOI SAI ngay ca khi chep thanh cong.
        for u in ungdung:
            # LUU Y: dang o giai doan WinPE, o dich la W: (chua boot vao
            # Windows that su) - KHONG dung THU_MUC_UNGDUNG_TREN_MAY (C:,
            # chi dung cho lenh chay SAU khi da boot vao Windows).
            dich = f"W:\\ConsolePi\\ungdung\\{u['id']}"
            # Bao tien trinh RO RANG truoc moi ung dung: ung dung kieu thu
            # muc co the nang vai GB (Office 365 ~3.5GB), robocopy day het
            # dau ra vao %LOG% nen man hinh dung im nhieu phut. Khong co
            # dong nay thi nguoi dung tuong may treo (da xay ra that).
            dong.append(
                f'echo     ... dang chep ung dung "{u["id"]}" - co the mat '
                "vai phut, xin doi...")
            # /XF _thongtin.json: day la file cau hinh NOI BO cua Console Pi
            # (ten hien thi + dong lenh cai), khong phai file cua ung dung -
            # khong duoc chep sang may khach.
            dong.append(
                f'robocopy "Z:\\ungdung\\{u["id"]}" "{dich}" /E /R:2 /W:2 '
                "/XF _thongtin.json >> %LOG% 2>&1")
            dong.append("if errorlevel 8 goto loi_chep_app")
    if fonts:
        # Bo font chu: chep CA THU MUC (nhieu file) bang robocopy - nho ma thoat 0-7 la
        # thanh cong. cai-font.ps1 lay tu X:\ (da nhung trong boot.wim), khong qua Samba.
        dong.append("if not exist W:\\ConsolePi mkdir W:\\ConsolePi")
        dong.append(f"copy /y %NHUNG%\\{TEN_PS_CAI_FONT} W:\\ConsolePi\\{TEN_PS_CAI_FONT} >> %LOG% 2>&1")
        dong.append("if errorlevel 1 goto loi_chep_app")
        for b in fonts:
            dong.append(f'echo     ... dang chep bo font "{b["id"]}" ({b["so_font"]} font)...')
            dong.append(
                f'robocopy "Z:\\fonts\\{b["id"]}" "W:\\ConsolePi\\fonts\\{b["id"]}" '
                "/E /R:2 /W:2 /XF _thongtin.json >> %LOG% 2>&1")
            dong.append("if errorlevel 8 goto loi_chep_app")
    dong.append("")
    return dong

def _lenh_chon_unattend():
    r"""
    Dong deploy.cmd: doc so build cua Windows VUA BUNG (hive SOFTWARE offline, chi reg.exe + find -
    WinPE khong co findstr/powershell) roi chon unattend.xml (conhost --headless, khong console) hay
    unattend-cu.xml (cmd /c powershell) cho Windows < 1809. Doc khong duoc -> CSBUILD=0 -> kieu cu
    (chac chan chay duoc, chi la co cua so console).
    """
    return [
        "set CSBUILD=0",
        "reg load HKLM\\CSOFF W:\\Windows\\System32\\config\\SOFTWARE >> %LOG% 2>&1",
        'for /f "tokens=3" %%a in (\'reg query "HKLM\\CSOFF\\Microsoft\\Windows NT\\CurrentVersion" '
        '/v CurrentBuildNumber 2^>nul ^| find "CurrentBuildNumber"\') do set CSBUILD=%%a',
        "reg unload HKLM\\CSOFF >> %LOG% 2>&1",
        "set CSUNA=unattend.xml",
        f"if %CSBUILD% LSS {BUILD_TOI_THIEU_HEADLESS} set CSUNA=unattend-cu.xml",
        "echo Windows build %CSBUILD% - dung %CSUNA% >> %LOG%",
    ]

def _lenh_bao_lich_su(dia_chi_pi, dong_dau, nhan):
    r"""
    Bao ket qua giai doan WinPE ve trang Lich su (ui/lichsu.py): ghi X:\ls.txt roi chep
    vao share [cs-lich-su] (chi nhan .txt nho - xem config/smb.conf), dung phien SMB cua
    Z: (cung may chu, cung tai khoan). Khong co ma lich su / chep loi -> bo qua, KHONG
    bao gio lam hong viec cai. Dung nhan + goto, khong dung khoi ( ) (BUOC co dau ngoac).
    """
    from ui import lichsu as _ls
    return [
        f"if not defined CS_LS goto {nhan}",
        f"echo {dong_dau}> X:\\ls.txt",
        'reg query "HKLM\\HARDWARE\\DESCRIPTION\\System\\BIOS" /v SystemProductName >> X:\\ls.txt 2>nul',
        f"copy /y X:\\ls.txt \\\\{dia_chi_pi}\\{_ls.TEN_SHARE}\\%CS_LS%.txt >> %LOG% 2>&1",
        f":{nhan}",
    ]

def _lenh_dat_ten(d):
    r"""
    Dong deploy.cmd xac dinh CS_TENMAY (chi khi ten may DONG - xem ui/datten.py):
      - serial / csv / ngau_nhien: server da ghi `set CS_TENMAY=...` vao cs-may.cmd (call o tren).
        Khong co (iPXE tai cs-may.cmd loi) -> du phong PC-<so ngau nhien cua cmd>, KHONG bao gio de trong.
      - hoi: hien cua so cmd hoi ten, kiem tra bang `for /f delims=` (WinPE khong co findstr/powershell),
        sai thi hoi lai; go xong bam Enter moi chay tiep toan bo qua trinh.
    Co dinh -> khong them dong nao (hanh vi cu giu nguyen).
    """
    c = _tm.che_do_cua(d)
    if c == "co_dinh":
        return []
    if c != "hoi":
        tt = _tm.tien_to_sach(d.get("ten_may_tiento_ngau" if c == "ngau_nhien" else "ten_may_tiento")) or "PC"
        return [
            "rem === Ten may dong (" + c + "): server ghi CS_TENMAY vao cs-may.cmd; thieu thi du phong ===",
            f"if not defined CS_TENMAY set CS_TENMAY={tt}-%RANDOM%",
            "echo === ten may: %CS_TENMAY% === >> %LOG%",
            "echo  Ten may se la: %CS_TENMAY%",
            "echo.",
            "",
        ]
    chu = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    return [
        "rem === Ten may: hoi nguoi dung (che do 'hoi') ===",
        ":nhap_ten",
        "set CS_TENMAY=",
        "set CS_BAD=",
        "set CS_CO_CHU=",
        "echo.",
        "echo  NHAP TEN MAY roi bam Enter (chu khong dau, so, dau -, toi da 15 ky tu).",
        "echo  Bam Enter xong, may se TU CAI TOAN BO - khong can bam gi them.",
        "echo.",
        "set /p CS_TENMAY=  Ten may: ",
        "if not defined CS_TENMAY goto ten_sai",
        'if not "%CS_TENMAY:~15,1%"=="" set CS_BAD=dai',
        'if "%CS_TENMAY:~0,1%"=="-" set CS_BAD=gach',
        'if "%CS_TENMAY:~-1%"=="-" set CS_BAD=gach',
        # eol mac dinh cua `for /f` la ";" (dong bat dau bang ";" bi bo qua -> "ab;c" lot qua kiem tra): quet 2 lan, eol khac nhau.
        f'for /f "eol=; delims={chu}0123456789-" %%a in ("%CS_TENMAY%") do set CS_BAD=kytu',
        f'for /f "eol=, delims={chu}0123456789-" %%a in ("%CS_TENMAY%") do set CS_BAD=kytu',
        f'for /f "delims=0123456789" %%a in ("%CS_TENMAY%") do set CS_CO_CHU=1',
        "if not defined CS_CO_CHU set CS_BAD=toanso",
        "if defined CS_BAD goto ten_sai",
        "goto ten_xong",
        ":ten_sai",
        "echo.",
        "echo  Ten may khong hop le. Chi dung chu KHONG DAU, so, dau gach ngang; toi da 15 ky tu; khong chi toan so.",
        "goto nhap_ten",
        ":ten_xong",
        "echo === ten may (nguoi dung nhap): %CS_TENMAY% === >> %LOG%",
        "echo.",
        "echo  OK, ten may: %CS_TENMAY%. Bat dau cai dat...",
        "echo.",
        "",
    ]

def _lenh_chep_unattend(d):
    r"""Chep unattend vao Panther. Ten may dong: ghep nua-truoc + ten + nua-sau (copy /b, khong can powershell)."""
    if not _tm.la_dong(d):
        return ["copy /y %NHUNG%\\%CSUNA% W:\\Windows\\Panther\\unattend.xml >> %LOG% 2>&1"]
    return [
        "set CSPA=una-a.xml",
        "set CSPB=una-b.xml",
        'if "%CSUNA%"=="unattend-cu.xml" set CSPA=una-cu-a.xml',
        'if "%CSUNA%"=="unattend-cu.xml" set CSPB=una-cu-b.xml',
        '<nul set /p "=%CS_TENMAY%">X:\\csten.txt',
        "echo Ten may %CS_TENMAY% - ghep %CSPA% + ten + %CSPB% >> %LOG%",
        "copy /b /y %NHUNG%\\%CSPA%+X:\\csten.txt+%NHUNG%\\%CSPB% W:\\Windows\\Panther\\unattend.xml >> %LOG% 2>&1",
    ]

def sinh_deploy_cmd(d, dia_chi_pi="192.168.98.1"):
    r"""
    Sinh script trien khai chay NGAY TRONG WinPE - mo phong dung cach
    MDT (LiteTouch) lam viec.

    LY DO THAT SU PHAI LAM NHU VAY (ca 1 chuoi kiem chung that, khong
    doan - xem lich su chi tiet trong sinh_autounattend_xml va
    dung_dia_gpt_tu_dong):

      Moi huong "nho Windows Setup tu lay install.wim qua mang" DEU that
      bai, ly do cuoi cung tim ra tu CHINH setupact.log cua Windows Setup:
        "Failed to access network share '\\<pi>\deploy' with credentials
         \consolepi-deploy (status 0x80070035)" (ERROR_BAD_NETPATH)
      - va Samba tren Pi KHONG HE ghi nhan bat ky ket noi nao trong TAT
      CA cac lan thu, trong khi `net use` GO TAY voi CUNG dia chi + CUNG
      tai khoan, trong CUNG phien WinPE do, lai THANH CONG ngay lap tuc
      (anh Thoai da kiem chung truc tiep). Nghia la co che tu ket noi SMB
      cua rieng Windows Setup (InstallFrom/Credentials) khong lam viec
      duoc voi Samba o day - va no nam trong ruot setup.exe, khong sua
      duoc tu ben ngoai.

    CACH MDT LAM (va gio Console Pi lam theo): KHONG CHAY setup.exe CHUT
    NAO. Thay vao do WinPE tu lam tung buoc bang cong cu co san (da kiem
    tra that: dism.exe, diskpart.exe, bcdboot.exe, wpeutil.exe deu CO SAN
    trong boot.wim, ke ca bo provider DISM day du):
        1. wpeinit               -> len mang
        2. net use               -> map kho trien khai (lenh DA CHUNG MINH
                                    chay duoc bang tay)
        3. diskpart /s           -> chia o dia
        4. dism /apply-image     -> bung install.wim ra o W:
        5. copy unattend.xml     -> W:\Windows\Panther (pass specialize +
                                    oobeSystem se chay luc boot lan dau)
        6. bcdboot               -> tao boot loader UEFI tren o S:
        7. wpeutil reboot        -> khoi dong vao Windows vua bung

    Neu bat ky buoc nao loi: KHONG tu khoi dong lai (tranh vong lap vo
    han), ma hien loi ro rang roi mo Command Prompt de xem log that.
    """
    os_id = d.get("os_id", "")
    duong_wim = f"Z:\\os\\{os_id}\\install.wim"
    # Luon cai phien ban Pro (ISO nhieu phien ban: chi so 1 thuong la Home).
    chi_so_anh = _d.chi_so_anh_pro(os_id)

    return "\r\n".join([
        "@echo off",
        "title Console System - Trien khai he dieu hanh",
        "set LOG=X:\\deploy_log.txt",
        # File nhung (deploy.cmd, diskpart*.txt, unattend.xml, *.ps1) do
        # wimboot chen vao luc boot - wimboot LUON dat chung o System32
        # (tai lieu wimboot), khong phai goc X:\\ nhu thoi anh dia GPT.
        f"set NHUNG={THU_MUC_NHUNG}",
        "echo === Console System - bat dau trien khai === > %LOG%",
        # Lich su + driver theo dong may (ui/lichsu.py, 14/10/2026): iPXE tai cs-may.cmd
        # tu Pi luc may chon kich ban - chua CS_LS (ma dong lich su) va CS_DRV (goi driver
        # hop hang/model trong BIOS). Khong co file (iPXE tai loi) -> cai binh thuong.
        "set CS_LS=",
        "set CS_DRV=",
        "if exist %NHUNG%\\cs-may.cmd call %NHUNG%\\cs-may.cmd",
        "echo === lich su: %CS_LS%  driver theo dong may: %CS_DRV% === >> %LOG%",
        'reg query "HKLM\\HARDWARE\\DESCRIPTION\\System\\BIOS" >> %LOG% 2>&1',
        "",
        "echo.",
        "echo  ================================================",
        "echo    CONSOLE SYSTEM - TRIEN KHAI HE DIEU HANH TU DONG",
        "echo  ================================================",
        "echo.",
        "",
    ] + _lenh_dat_ten(d) + [
        # ================================================================
        # KHOI TAO MANG - phan mong manh nhat, da phai sua nhieu vong.
        #
        # DU LIEU THAT thu duoc tu chinh X:\deploy_log.txt qua cac lan
        # chay (khong doan):
        #   - Lan A: ngay tu dau `ipconfig` DA co IP hop le -> mang san
        #     sang truoc khi script chay.
        #   - Lan B: `ipconfig` bao "Unable to contact IP driver. General
        #     failure", `ping` bao "The network is not present or not
        #     started" (loi 1222), `net use` bao loi 2138 (Workstation
        #     service chua chay) -> mang CHUA duoc khoi tao gi ca.
        # => setup.exe khoi tao mang BAT DONG BO; script nay (chay qua
        #    RunSynchronousCommand ben trong setup.exe) co the roi vao
        #    BAT KY thoi diem nao trong qua trinh do. Day chinh la ly do
        #    "luc duoc luc khong" - khong phai loi ngau nhien.
        #
        # CACH LAM DUNG (giong LiteTouch cua MDT): khoi tao mang MOT LAN
        # ngay tu dau, roi DOI cho toi khi mang THAT SU thong (ping duoc
        # Pi) - lay ping lam moc kiem chung khach quan, khong tin vao
        # viec "lenh da chay xong". Chi khi L3 da thong moi dung toi SMB.
        # NAP DRIVER CARD MANG TRUOC KHI KHOI TAO MANG.
        # LY DO THAT (kiem chung bang cach trich .inf trong chinh
        # boot.wim ra doc ma phan cung): anh WinPE nay CHI co driver
        # Intel I219 doi 2016-2019; TU doi 2020 tro di (Comet Lake,
        # Tiger Lake, Alder Lake, Raptor Lake, Meteor Lake) va toan bo
        # Intel I225/I226 2.5G thi KHONG CO. May HP/Dell/Lenovo doi moi
        # dung LAN Intel se khong co mang trong WinPE -> khong tai duoc
        # install.wim -> dung hinh (dung hien tuong anh Thoai gap voi
        # MDT). `drvload` la cong cu chinh chu cua WinPE de nap driver
        # luc dang chay - da kiem tra CO SAN trong boot.wim nay.
        # Neu khong danh dau goi driver nao "cho anh boot" thi thu muc
        # nay khong ton tai va vong lap chay qua, khong anh huong gi.
        "echo  [1/6] Nap driver card mang (neu co)...",
        "echo === nap driver cho WinPE === >> %LOG%",
        # wimboot chi chen duoc FILE PHANG (khong thu muc) -> cac goi
        # driver "cho anh boot" dong chung 1 file drivers.wim, bung ra
        # X:\\ConsolePiDrivers bang dism (co san trong boot.wim).
        # dism can thu muc dich co san + file duoi .wim.
        f"if exist %NHUNG%\\{TEN_NHUNG_DRIVER} copy /y %NHUNG%\\{TEN_NHUNG_DRIVER} "
        "X:\\cpi-drivers.wim >> %LOG% 2>&1",
        "if exist X:\\cpi-drivers.wim mkdir X:\\ConsolePiDrivers >nul 2>&1",
        "if exist X:\\cpi-drivers.wim dism /apply-image "
        "/imagefile:X:\\cpi-drivers.wim /index:1 "
        "/applydir:X:\\ConsolePiDrivers >> %LOG% 2>&1",
        'if exist X:\\ConsolePiDrivers (for /r X:\\ConsolePiDrivers %%i in '
        '(*.inf) do drvload "%%i" >> %LOG% 2>&1)',
        "",
        # BIOS hay UEFI? - quyet dinh kieu chia o (MBR/GPT) va kieu boot
        # loader. PEFirmwareType: 1 = BIOS, 2 = UEFI (tai lieu WinPE cua
        # Microsoft; kiem chung that trong lab: may BIOS doc ra 0x1).
        "wpeutil UpdateBootInfo >nul 2>&1",
        "set FW=UEFI",
        'for /f "tokens=3" %%a in (\'reg query '
        'HKLM\\System\\CurrentControlSet\\Control /v PEFirmwareType '
        '2^>nul ^| find "PEFirmwareType"\') do if "%%a"=="0x1" set FW=BIOS',
        "echo === may khoi dong kieu %FW% === >> %LOG%",
        "set DPT=%NHUNG%\\diskpart.txt",
        'if "%FW%"=="BIOS" set DPT=%NHUNG%\\diskpart-mbr.txt',
        "",
        "echo  [1/6] Khoi tao mang va doi mang san sang...",
        "echo === khoi tao mang === >> %LOG%",
        # Setup thuong da tu khoi tao mang truoc khi goi script nay - thong
        # roi thi thoi, khong goi lai wpeinit.
        f"ping -n 1 -w 1000 {dia_chi_pi} >nul 2>&1",
        "if not errorlevel 1 goto mang_thong",
        # LOI THAT (VMware BIOS, card E1000, 26/09/2026): man hinh dung mai o
        # dong tren, vong cho ben duoi KHONG in dong nao -> ket ngay trong
        # `wpeinit` goi dong bo. Nay chay wpeinit/InitializeNetwork O NEN
        # (start) - script van dem, van ping, van bao loi dung luc.
        # Card E1000 GIA LAP cua VMware (PCI 8086:100F, SUBSYS ..15AD): WinPE
        # Windows 10/11 treo luc cai driver cho no (loi that may ao anh Thoai
        # 26/09/2026 - dung ca he thong o vong 19-20; dung loi Michael Niehaus
        # da ghi: oofhours.com 2020/12/30). Chip 2001, may that khong con - bao
        # ngay cach sua thay vi de nguoi dung ngoi doi.
        'reg query HKLM\\SYSTEM\\CurrentControlSet\\Enum\\PCI /k /f "VEN_8086&DEV_100F&SUBSYS_075015AD" 2>nul | find /i "DEV_100F" >nul',
        "if errorlevel 1 goto khong_e1000_vmware",
        "echo === CANH BAO: card VMware E1000 (82545EM) === >> %LOG%",
        "echo.",
        "echo  CANH BAO: may ao VMware nay dung card mang E1000 (Intel 82545EM, doi 2001).",
        # Nguyen nhan goc (26/09/2026): may ao khai Guest OS la LINUX (vd
        # "debian13-64") -> VMware dua phan cung/ACPI kieu Linux, driver E1000
        # cua WinPE treo ca ngan xep mang. Doi Guest OS sang Windows la het
        # (schmidi2itblog 2013: ESXi, doi Guest OS tu Linux sang Windows).
        "echo  Neu may ao khai Guest OS la Linux/Other, WinPE se TREO o buoc mang.",
        "echo  CACH SUA (1 lan cho may ao): tat may ao - Edit Settings - Options -",
        "echo    General - Guest OS = Microsoft Windows, Version = Windows 10/11 x64.",
        "echo  (Hoac doi Network Adapter sang E1000E / VMXNET3.) May that khong bi.",
        "echo  Van thu tiep - neu dung qua 3 phut o duoi thi lam theo cach tren.",
        "echo.",
        ":khong_e1000_vmware",
        'start "khoi tao mang" /min cmd /c "wpeinit >> X:\\wpeinit_log.txt 2>&1 '
        '& wpeutil InitializeNetwork >> X:\\wpeinit_log.txt 2>&1"',
        "set CHO=0",
        "",
        ":cho_mang",
        "set /a CHO+=1",
        f"ping -n 1 -w 1000 {dia_chi_pi} >nul 2>&1",
        "if not errorlevel 1 goto mang_thong",
        # ~5 phut (75 x ~4 giay). LOI THAT (lab 26/09/2026, card 82545EM - dung
        # loai E1000 cua VMware): WinPE nap driver cho card nay MAT HON 30 GIAY
        # - kiem tra som thi tuong "thieu driver" trong khi mot lat sau card
        # co IP. Vi vay: giay ~30 chi GHI canh bao, het gio moi ket luan.
        "if %CHO% GEQ 75 goto het_gio_mang",
        "if %CHO% EQU 8 goto kiem_tra_card",
        ":sau_kiem_tra_card",
        # Cu 10 lan doi khong duoc thi khoi tao lai 1 lan (o nen).
        "set /a NHAC=%CHO% %% 10",
        "if %NHAC% NEQ 0 goto cho_tiep",
        "echo === khoi tao lai mang lan %CHO% === >> %LOG%",
        'start "khoi tao mang" /min cmd /c "wpeutil InitializeNetwork >> X:\\wpeinit_log.txt 2>&1"',
        "",
        ":cho_tiep",
        "echo     dang doi mang san sang... (%CHO%)",
        "ping -n 3 127.0.0.1 >nul",
        "goto cho_mang",
        "",
    ] + _lenh_kiem_tra_card_mang() + [
        "",
        ":mang_thong",
        "echo === mang da thong === >> %LOG%",
        "if exist X:\\wpeinit_log.txt type X:\\wpeinit_log.txt >> %LOG% 2>&1",
        "ipconfig >> %LOG% 2>&1",
        "",
        "echo  [2/6] Ket noi kho trien khai tren Console System...",
        # TUYET DOI KHONG `net stop workstation` o day.
        #
        # LOI THAT DA GAP khi tung lam vay (log: "=== khoi dong lai dich vu
        # SMB client ===" -> "The Workstation service was stopped/started
        # successfully" -> `net use` bao "System error 1312 - A specified
        # logon session does not exist"): dung dich vu Workstation huy toan
        # bo logon session ma SMB redirector dang giu. Tien trinh cmd dang
        # chay deploy.cmd van giu token cua session DA BI HUY do, nen moi
        # `net use ... /user:...` sau do deu that bai 1312 - du mang va
        # Samba deu hoan toan binh thuong. Day chinh la hien tuong "luc
        # duoc luc khong".
        #
        # Gia thuyet cu (dich vu bind truoc khi co IP nen phai restart) la
        # SAI: nguyen nhan that cua loi 53 truoc day la ket noi SMB cu con
        # ESTABLISHED tren Pi, da duoc xu ly o phia Pi bang
        # `smbcontrol smbd kill-client-ip` luc nap menu.ipxe.
        # O day chi CAN dam bao dich vu dang chay - start khong bao gio
        # huy session, stop thi co.
        "echo === bao dam dich vu SMB client dang chay === >> %LOG%",
        "net start workstation >> %LOG% 2>&1",
        "net config workstation >> %LOG% 2>&1",
        "set THU=0",
        "",
        ":thu_ket_noi",
        "set /a THU+=1",
        "echo --- ket noi lan thu %THU% --- >> %LOG%",
        # Xoa phien cu (neu co) truoc moi lan thu - phien hong nua chung
        # se lam lan thu sau bao loi y het du van de goc da het.
        "net use Z: /delete /y >nul 2>&1",
        f"net use Z: \\\\{dia_chi_pi}\\deploy /user:{TEN_TAI_KHOAN_SAMBA} "
        f"{_doc_mat_khau_samba()} >> %LOG% 2>&1",
        "if not errorlevel 1 goto ket_noi_xong",
        "if %THU% GEQ 10 goto loi_mang",
        # KHONG dung `sc` o day - WinPE nay KHONG co sc.exe (da kiem chung
        # that: log bao "'sc' is not recognized as an internal or external
        # command"). Dung `net` (luon co san) de chan doan.
        "net start workstation >> %LOG% 2>&1",
        "net view \\\\" + dia_chi_pi + " >> %LOG% 2>&1",
        "echo     chua ket noi duoc, thu lai lan %THU% ...",
        "ping -n 4 127.0.0.1 >nul",
        "goto thu_ket_noi",
        "",
        ":ket_noi_xong",
        "echo  [2/6] Da ket noi kho trien khai.",
        # LUU Y CU PHAP BATCH (loi that da tranh duoc): KHONG duoc viet
        # `if errorlevel 1 set X=...& goto nhan` - cmd.exe tach thanh
        # `(if errorlevel 1 set X=...) & (goto nhan)`, tuc la LUON LUON
        # nhay bat ke dieu kien. Cung KHONG dung block `( )` vi thong bao
        # co the chua dau ngoac lam vo parse. Dung nhan rieng cho tung loi
        # la cach chac chan dung nhat.
        f"if not exist {duong_wim} goto loi_thieu_wim",
        "",
        "echo  [3/6] Chia lai o dia - toan bo du lieu cu se mat...",
        # WinPE CO THAY o dia can cai khong? LOI THAT (VMware Workstation cua
        # anh Thoai, 26/09/2026): bo dieu khien "LSI Logic Parallel" - WinPE
        # Win10/11 KHONG co driver -> diskpart "The disk you specified is not
        # valid", script van chay tiep va bao "Error: 3" o buoc bung anh, rat
        # kho hieu. Nay kiem truoc, khong thay thi bao ro bo dieu khien nao.
        "echo list disk> X:\\ds.txt",
        "diskpart /s X:\\ds.txt > X:\\ds_out.txt 2>&1",
        "type X:\\ds_out.txt >> %LOG%",
    ] + ([
        f'find /i "Disk {d.get("o_dia_so", "0")} " X:\\ds_out.txt >nul',
        "if errorlevel 1 goto khong_thay_o",
        "diskpart /s %DPT% >> %LOG% 2>&1",
    ] if o_chon(d)["chon"] == "so" else _lenh_chon_o(d) + [
        "diskpart /s X:\\dp.txt >> %LOG% 2>&1",
    ]) + [
        "if errorlevel 1 goto loi_dia",
        # diskpart KHONG luon tra ma loi khi 1 lenh trong script hong - kiem
        # bang ket qua that: phai co o W: vua tao.
        "if not exist W:\\ goto loi_dia",
        "",
        "echo  [4/6] Bung anh he dieu hanh - buoc nay lau nhat, xin doi...",
        "echo.",
        f"dism /apply-image /imagefile:{duong_wim} /index:{chi_so_anh} /applydir:W:\\ "
        "/logpath:X:\\dism_log.txt",
        "if errorlevel 1 goto loi_bung",
        "",
        "echo.",
        "echo  Da bung xong anh he dieu hanh. Dang chuan bi buoc tiep theo"
        " (nap driver, phan mem, cau hinh tu dong) - xin doi...",
        "echo.",
    ] + _lenh_tiem_driver_offline(d) + _lenh_net35_offline(d) + _lenh_chep_go_app(d) + [
        "echo  [5/6] Chep cau hinh tu dong - ten may, tai khoan, mui gio...",
        "if not exist W:\\Windows\\Panther mkdir W:\\Windows\\Panther",
    ] + _lenh_chon_unattend() + [
    ] + _lenh_chep_unattend(d) + [
        "if errorlevel 1 goto loi_chep",
        "",
        # Chep phan mem + script sang THANG o dia may dich NGAY BAY GIO,
        # trong khi con o WinPE va o mang Z: dang chac chan hoat dong.
        # LY DO: luc Windows chay lan dau va cai cac phan mem nay, no se
        # doc file tu o C: cua chinh no - KHONG can mang, khong can tai
        # khoan Samba. Dung cai cho da gay ra rat nhieu rac roi truoc day
        # (loi 53, phien SMB ket...) nen khong lap lai o giai doan do.
    ] + _lenh_chep_app_script(d) + [
        # BAO CAO TONG KET - chep LUON LUON, khong phu thuoc lua chon nao.
        # Lay tu X:\ (da nhung san trong boot.wim) chu KHONG qua Samba:
        # bao cao la thu cuoi cung con lai de biet ca ca lan cai co dung
        # y hay khong, khong duoc phep phu thuoc vao mang con song hay
        # kho Samba con ket noi duoc hay khong.
        "if not exist W:\\ConsolePi mkdir W:\\ConsolePi",
        "copy /y %NHUNG%\\bao-cao.ps1 W:\\ConsolePi\\bao-cao.ps1 >> %LOG% 2>&1",
        "copy /y %NHUNG%\\tien-trinh.ps1 W:\\ConsolePi\\tien-trinh.ps1 >> %LOG% 2>&1",
        # Ma lich su cho tien-trinh.ps1 gui kem moi lan bao Pi (noi dong lich su voi
        # ten may + ket qua cac buoc sau dang nhap).
        "if defined CS_LS echo %CS_LS%> W:\\ConsolePi\\ls-id.txt",
        "",
        "echo  [6/6] Tao boot loader (%FW%)...",
        "bcdboot W:\\Windows /s S: /f %FW% >> %LOG% 2>&1",
        "if errorlevel 1 goto loi_boot",
        "",
        "echo XONG >> %LOG%",
    ] + _lenh_bao_lich_su(dia_chi_pi, "XONG", "ls_xong") + [
        "echo.",
        "echo  ================================================",
        "echo    HOAN TAT - khoi dong lai sau 10 giay",
        "echo  ================================================",
        "ping -n 11 127.0.0.1 >nul",
        "wpeutil reboot",
        "exit",
        "",
":loi_thieu_driver",
        "set BUOC=Card mang cua may nay CHUA CO DRIVER trong WinPE - xem dong [THIEU DRIVER] o tren",
        "goto bao_loi",
        "",
        ":loi_mang_khong_thong",
        f"set BUOC=Mang khong thong toi Console System ({dia_chi_pi}) - kiem tra "
        "day mang da cam dung chua",
        "goto bao_loi",
        "",
        ":loi_mang",
        "set BUOC=Mang thong nhung khong ket noi duoc kho trien khai - kiem "
        "tra dich vu Samba tren Pi",
        "goto bao_loi",
        "",
        ":loi_thieu_wim",
        f"set BUOC=Khong tim thay {duong_wim}",
        "goto bao_loi",
        "",
        ":loi_dia",
        "set BUOC=Chia o dia that bai (khong tao duoc o W:) - xem dong diskpart trong log",
        "goto bao_loi",
        "",
    ] + _lenh_khong_thay_o(d) + (_ham_chon_o(d) if o_chon(d)["chon"] != "so" else []) + [
        "",
        ":loi_bung",
        "set BUOC=Bung anh he dieu hanh that bai - xem X:\\dism_log.txt",
        "goto bao_loi",
        "",
        ":loi_chep",
        "set BUOC=Chep unattend.xml that bai",
        "goto bao_loi",
        "",
        ":loi_chep_app",
        "set BUOC=Chep phan mem/script sang may dich that bai",
        "goto bao_loi",
        "",
        ":loi_boot",
        "set BUOC=Tao boot loader that bai",
        "goto bao_loi",
        "",
        ":bao_loi",
        "echo LOI: %BUOC% >> %LOG%",
    ] + _lenh_bao_lich_su(dia_chi_pi, "LOI=%BUOC%", "ls_loi") + [
        "echo.",
        "echo  ================================================",
        "echo    LOI: %BUOC%",
        "echo.",
        "echo    Xem chi tiet:  type %LOG%",
        "echo  ================================================",
        "echo.",
        # Script co the chay AN (khong hien cua so) khi duoc goi tu
        # RunSynchronousCommand cua Windows Setup - nen mo Notepad hien
        # log ra man hinh de nguoi dung doc duoc ngay, khong phai tu di
        # tim file. Notepad co san trong WinPE (da kiem chung that).
        "start notepad %LOG%",
        "cmd",
        "",
    ]) + "\r\n"

def sinh_autounattend_goi_script(ten_script="deploy.cmd",
                                 mo_ta="Console System - trien khai he dieu hanh"):
    r"""
    autounattend.xml TOI GIAN - chi lam DUNG 1 viec: goi script trien khai
    cua Console Pi (X:\deploy.cmd), khong khai bao DiskConfiguration hay
    ImageInstall gi ca (script tu lam het bang diskpart + dism).

    LY DO THAT SU PHAI LAM KIEU NAY (chuoi kiem chung that, khong doan):

      1. Thay setup.exe bang script rieng qua winpeshl.ini: script CHAY
         DUOC (da thay man hinh Console Pi that), nhung `net use` bao
         "System error 53 - network path not found", va tcpdump tren Pi
         cho thay client KHONG GUI BAT KY GOI NAO toi cong 445 - tuc bo
         SMB client phia Windows chua hoat dong, du:
           - ping tu may do sang Pi THONG hoan toan (4/4 reply)
           - `net start workstation/mup/rdbss/mrxsmb/mrxsmb20` deu bao
             "already been started"
           - wpeinit + wpeutil InitializeNetwork da chay xong, da co IP
      2. NHUNG khi de setup.exe chay binh thuong roi bam Shift+F10 mo
         Command Prompt, thi CUNG lenh `net use` do lai THANH CONG ngay
         (anh Thoai da lam that nhieu lan). Khac biet DUY NHAT giua 2
         truong hop la: co setup.exe chay hay khong.
      => Ket luan: chinh setup.exe (moi truong Windows Setup) moi kich
         hoat day du bo SMB client trong anh boot.wim nay. Vay ta KHONG
         thay the setup.exe nua, ma de no chay binh thuong, roi nho no
         goi script cua minh qua RunSynchronousCommand (co che nay DA
         duoc kiem chung la chay that - lan truoc no da ghi duoc file
         netinit_log.txt).

    Script se tu reboot khi xong nen Setup khong bao gio kip hien giao
    dien hoi gi - nguoi dung chi thay man hinh tien trinh cua Console Pi.
    """
    return """<?xml version="1.0" encoding="utf-8"?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
  <settings pass="windowsPE">
    <component name="Microsoft-Windows-International-Core-WinPE"
        processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35"
        language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <SetupUILanguage><UILanguage>en-US</UILanguage></SetupUILanguage>
      <InputLocale>en-US</InputLocale>
      <SystemLocale>en-US</SystemLocale>
      <UILanguage>en-US</UILanguage>
      <UserLocale>en-US</UserLocale>
    </component>
    <component name="Microsoft-Windows-Setup" processorArchitecture="amd64"
        publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS"
        xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State">
      <RunSynchronous>
        <RunSynchronousCommand wcm:action="add">
          <Order>1</Order>
          <Path>cmd /c X:\\Windows\\System32\\""" + ten_script + """</Path>
          <Description>""" + mo_ta + """</Description>
        </RunSynchronousCommand>
      </RunSynchronous>
    </component>
  </settings>
</unattend>
"""
