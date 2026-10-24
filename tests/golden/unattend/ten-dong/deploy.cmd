@echo off
title Console System - Trien khai he dieu hanh
set LOG=X:\deploy_log.txt
set NHUNG=X:\Windows\System32
echo === Console System - bat dau trien khai === > %LOG%
set CS_LS=
set CS_DRV=
if exist %NHUNG%\cs-may.cmd call %NHUNG%\cs-may.cmd
echo === lich su: %CS_LS%  driver theo dong may: %CS_DRV% === >> %LOG%
reg query "HKLM\HARDWARE\DESCRIPTION\System\BIOS" >> %LOG% 2>&1

echo.
echo  ================================================
echo    CONSOLE SYSTEM - TRIEN KHAI HE DIEU HANH TU DONG
echo  ================================================
echo.

rem === Ten may dong (serial): server ghi CS_TENMAY vao cs-may.cmd; thieu thi du phong ===
if not defined CS_TENMAY set CS_TENMAY=PC-%RANDOM%
echo === ten may: %CS_TENMAY% === >> %LOG%
echo  Ten may se la: %CS_TENMAY%
echo.

echo  [1/6] Nap driver card mang (neu co)...
echo === nap driver cho WinPE === >> %LOG%
if exist %NHUNG%\cpi-drivers.bin copy /y %NHUNG%\cpi-drivers.bin X:\cpi-drivers.wim >> %LOG% 2>&1
if exist X:\cpi-drivers.wim mkdir X:\ConsolePiDrivers >nul 2>&1
if exist X:\cpi-drivers.wim dism /apply-image /imagefile:X:\cpi-drivers.wim /index:1 /applydir:X:\ConsolePiDrivers >> %LOG% 2>&1
if exist X:\ConsolePiDrivers (for /r X:\ConsolePiDrivers %%i in (*.inf) do drvload "%%i" >> %LOG% 2>&1)

wpeutil UpdateBootInfo >nul 2>&1
set FW=UEFI
for /f "tokens=3" %%a in ('reg query HKLM\System\CurrentControlSet\Control /v PEFirmwareType 2^>nul ^| find "PEFirmwareType"') do if "%%a"=="0x1" set FW=BIOS
echo === may khoi dong kieu %FW% === >> %LOG%
set DPT=%NHUNG%\diskpart.txt
if "%FW%"=="BIOS" set DPT=%NHUNG%\diskpart-mbr.txt

echo  [1/6] Khoi tao mang va doi mang san sang...
echo === khoi tao mang === >> %LOG%
ping -n 1 -w 1000 192.168.98.1 >nul 2>&1
if not errorlevel 1 goto mang_thong
reg query HKLM\SYSTEM\CurrentControlSet\Enum\PCI /k /f "VEN_8086&DEV_100F&SUBSYS_075015AD" 2>nul | find /i "DEV_100F" >nul
if errorlevel 1 goto khong_e1000_vmware
echo === CANH BAO: card VMware E1000 (82545EM) === >> %LOG%
echo.
echo  CANH BAO: may ao VMware nay dung card mang E1000 (Intel 82545EM, doi 2001).
echo  Neu may ao khai Guest OS la Linux/Other, WinPE se TREO o buoc mang.
echo  CACH SUA (1 lan cho may ao): tat may ao - Edit Settings - Options -
echo    General - Guest OS = Microsoft Windows, Version = Windows 10/11 x64.
echo  (Hoac doi Network Adapter sang E1000E / VMXNET3.) May that khong bi.
echo  Van thu tiep - neu dung qua 3 phut o duoi thi lam theo cach tren.
echo.
:khong_e1000_vmware
start "khoi tao mang" /min cmd /c "wpeinit >> X:\wpeinit_log.txt 2>&1 & wpeutil InitializeNetwork >> X:\wpeinit_log.txt 2>&1"
set CHO=0

:cho_mang
set /a CHO+=1
ping -n 1 -w 1000 192.168.98.1 >nul 2>&1
if not errorlevel 1 goto mang_thong
if %CHO% GEQ 75 goto het_gio_mang
if %CHO% EQU 8 goto kiem_tra_card
:sau_kiem_tra_card
set /a NHAC=%CHO% %% 10
if %NHAC% NEQ 0 goto cho_tiep
echo === khoi tao lai mang lan %CHO% === >> %LOG%
start "khoi tao mang" /min cmd /c "wpeutil InitializeNetwork >> X:\wpeinit_log.txt 2>&1"

:cho_tiep
echo     dang doi mang san sang... (%CHO%)
ping -n 3 127.0.0.1 >nul
goto cho_mang

:kiem_tra_card_cuoi
ipconfig >> %LOG% 2>&1
:kiem_tra_card
echo === kiem tra card mang co driver (lan %CHO%) === >> %LOG%
set NICCO=0
set NICTHIEU=0
for /f "delims=" %%D in ('reg query HKLM\SYSTEM\CurrentControlSet\Enum\PCI /s /f "PCI\CC_02" /d 2^>nul ^| find /i "HKEY_"') do call :xet_card "%%D"
echo     card mang PCI: %NICCO%, thieu driver: %NICTHIEU% >> %LOG%
if %CHO% GEQ 75 if %NICCO%==0 goto loi_mang_khong_thong
if %CHO% GEQ 75 if not %NICCO%==%NICTHIEU% goto loi_mang_khong_thong
if %NICCO%==0 goto sau_kiem_tra_card
if %NICCO%==%NICTHIEU% goto canh_bao_driver
goto sau_kiem_tra_card

:canh_bao_driver
if %CHO% GEQ 75 goto thieu_driver
echo     (card mang dang nap driver - co may mat 1-2 phut, van dang cho...)
goto sau_kiem_tra_card

:het_gio_mang
goto kiem_tra_card_cuoi

:xet_card
set /a NICCO+=1
reg query "%~1" /v Driver >nul 2>&1
if not errorlevel 1 goto :eof
set /a NICTHIEU+=1
if %CHO% GEQ 75 echo     [THIEU DRIVER] "%~1"
echo [THIEU DRIVER] "%~1" >> %LOG%
goto :eof

:thieu_driver
echo.
echo  LOI: card mang cua may nay CHUA CO DRIVER trong WinPE (dong [THIEU DRIVER] o tren).
echo    VEN_15AD^&DEV_07B0 = VMware VMXNET3: tat may ao, doi Adapter Type sang E1000E,
echo        hoac tai goi vmxnet3 (Microsoft Update Catalog) vao muc Driver cho anh boot.
echo    VEN_8086^&DEV_125x / 15F2 / 15F3 / 3100 = Intel I225/I226 2.5G;
echo    VEN_1AF4 = virtio (may ao KVM/Proxmox) - nap driver vao muc Driver cho anh boot.
goto loi_thieu_driver

:mang_thong
echo === mang da thong === >> %LOG%
if exist X:\wpeinit_log.txt type X:\wpeinit_log.txt >> %LOG% 2>&1
ipconfig >> %LOG% 2>&1

echo  [2/6] Ket noi kho trien khai tren Console System...
echo === bao dam dich vu SMB client dang chay === >> %LOG%
net start workstation >> %LOG% 2>&1
net config workstation >> %LOG% 2>&1
set THU=0

:thu_ket_noi
set /a THU+=1
echo --- ket noi lan thu %THU% --- >> %LOG%
net use Z: /delete /y >nul 2>&1
net use Z: \\192.168.98.1\deploy /user:consolepi-deploy  >> %LOG% 2>&1
if not errorlevel 1 goto ket_noi_xong
if %THU% GEQ 10 goto loi_mang
net start workstation >> %LOG% 2>&1
net view \\192.168.98.1 >> %LOG% 2>&1
echo     chua ket noi duoc, thu lai lan %THU% ...
ping -n 4 127.0.0.1 >nul
goto thu_ket_noi

:ket_noi_xong
echo  [2/6] Da ket noi kho trien khai.
if not exist Z:\os\windows_10_pro\install.wim goto loi_thieu_wim

echo  [3/6] Chia lai o dia - toan bo du lieu cu se mat...
echo list disk> X:\ds.txt
diskpart /s X:\ds.txt > X:\ds_out.txt 2>&1
type X:\ds_out.txt >> %LOG%
find /i "Disk 0 " X:\ds_out.txt >nul
if errorlevel 1 goto khong_thay_o
diskpart /s %DPT% >> %LOG% 2>&1
if errorlevel 1 goto loi_dia
if not exist W:\ goto loi_dia

echo  [4/6] Bung anh he dieu hanh - buoc nay lau nhat, xin doi...
echo.
dism /apply-image /imagefile:Z:\os\windows_10_pro\install.wim /index:1 /applydir:W:\ /logpath:X:\dism_log.txt
if errorlevel 1 goto loi_bung

echo.
echo  Da bung xong anh he dieu hanh. Dang chuan bi buoc tiep theo (nap driver, phan mem, cau hinh tu dong) - xin doi...
echo.
echo === tiem driver vao Windows vua bung === >> %LOG%
if exist X:\ConsolePiDrivers dism /image:W:\ /add-driver /driver:X:\ConsolePiDrivers /recurse >> %LOG% 2>&1
if defined CS_DRV echo  Nap driver rieng cho dong may nay: %CS_DRV%
if defined CS_DRV for %%i in (%CS_DRV%) do if exist "Z:\drivers\%%i" dism /image:W:\ /add-driver /driver:"Z:\drivers\%%i" /recurse >> %LOG% 2>&1
echo  [5/6] Chep cau hinh tu dong - ten may, tai khoan, mui gio...
if not exist W:\Windows\Panther mkdir W:\Windows\Panther
set CSBUILD=0
reg load HKLM\CSOFF W:\Windows\System32\config\SOFTWARE >> %LOG% 2>&1
for /f "tokens=3" %%a in ('reg query "HKLM\CSOFF\Microsoft\Windows NT\CurrentVersion" /v CurrentBuildNumber 2^>nul ^| find "CurrentBuildNumber"') do set CSBUILD=%%a
reg unload HKLM\CSOFF >> %LOG% 2>&1
set CSUNA=unattend.xml
if %CSBUILD% LSS 17763 set CSUNA=unattend-cu.xml
echo Windows build %CSBUILD% - dung %CSUNA% >> %LOG%
set CSPA=una-a.xml
set CSPB=una-b.xml
if "%CSUNA%"=="unattend-cu.xml" set CSPA=una-cu-a.xml
if "%CSUNA%"=="unattend-cu.xml" set CSPB=una-cu-b.xml
<nul set /p "=%CS_TENMAY%">X:\csten.txt
echo Ten may %CS_TENMAY% - ghep %CSPA% + ten + %CSPB% >> %LOG%
copy /b /y %NHUNG%\%CSPA%+X:\csten.txt+%NHUNG%\%CSPB% W:\Windows\Panther\unattend.xml >> %LOG% 2>&1
if errorlevel 1 goto loi_chep

if not exist W:\ConsolePi mkdir W:\ConsolePi
copy /y %NHUNG%\bao-cao.ps1 W:\ConsolePi\bao-cao.ps1 >> %LOG% 2>&1
copy /y %NHUNG%\tien-trinh.ps1 W:\ConsolePi\tien-trinh.ps1 >> %LOG% 2>&1
if defined CS_LS echo %CS_LS%> W:\ConsolePi\ls-id.txt

echo  [6/6] Tao boot loader (%FW%)...
bcdboot W:\Windows /s S: /f %FW% >> %LOG% 2>&1
if errorlevel 1 goto loi_boot

echo XONG >> %LOG%
if not defined CS_LS goto ls_xong
echo XONG> X:\ls.txt
reg query "HKLM\HARDWARE\DESCRIPTION\System\BIOS" /v SystemProductName >> X:\ls.txt 2>nul
copy /y X:\ls.txt \\192.168.98.1\cs-lich-su\%CS_LS%.txt >> %LOG% 2>&1
:ls_xong
echo.
echo  ================================================
echo    HOAN TAT - khoi dong lai sau 10 giay
echo  ================================================
ping -n 11 127.0.0.1 >nul
wpeutil reboot
exit

:loi_thieu_driver
set BUOC=Card mang cua may nay CHUA CO DRIVER trong WinPE - xem dong [THIEU DRIVER] o tren
goto bao_loi

:loi_mang_khong_thong
set BUOC=Mang khong thong toi Console System (192.168.98.1) - kiem tra day mang da cam dung chua
goto bao_loi

:loi_mang
set BUOC=Mang thong nhung khong ket noi duoc kho trien khai - kiem tra dich vu Samba tren Pi
goto bao_loi

:loi_thieu_wim
set BUOC=Khong tim thay Z:\os\windows_10_pro\install.wim
goto bao_loi

:loi_dia
set BUOC=Chia o dia that bai (khong tao duoc o W:) - xem dong diskpart trong log
goto bao_loi

:khong_thay_o
echo === KHONG THAY O DIA - kiem tra bo dieu khien o === >> %LOG%
for /f "delims=" %%D in ('reg query HKLM\SYSTEM\CurrentControlSet\Enum\PCI /s /f "PCI\CC_01" /d 2^>nul ^| find /i "HKEY_"') do call :xet_o "%%D"
echo.
echo  LOI: WinPE KHONG THAY o dia so 0 (xem danh sach 'list disk' trong log).
echo    Thuong do bo dieu khien o dia chua co driver trong WinPE:
echo    VEN_1000^&DEV_0030 = VMware LSI Logic Parallel: sua file .vmx
echo        scsi0.virtualDev = "lsisas1068"  (LSI SAS) hoac dung SATA/NVMe.
echo    VEN_15AD^&DEV_07C0 = VMware PVSCSI (Win10 PE khong co driver).
echo    VEN_8086 RAID/VMD (laptop Intel doi moi): BIOS doi RAID/VMD sang AHCI
echo        hoac nap driver Intel RST vao muc Driver cho anh boot.
set BUOC=Khong thay o dia so 0 - bo dieu khien o dia chua co driver (xem tren)
goto bao_loi

:xet_o
reg query "%~1" /v Driver >nul 2>&1
if not errorlevel 1 goto :eof
echo     [O DIA THIEU DRIVER] "%~1"
echo [O DIA THIEU DRIVER] "%~1" >> %LOG%
goto :eof

:loi_bung
set BUOC=Bung anh he dieu hanh that bai - xem X:\dism_log.txt
goto bao_loi

:loi_chep
set BUOC=Chep unattend.xml that bai
goto bao_loi

:loi_chep_app
set BUOC=Chep phan mem/script sang may dich that bai
goto bao_loi

:loi_boot
set BUOC=Tao boot loader that bai
goto bao_loi

:bao_loi
echo LOI: %BUOC% >> %LOG%
if not defined CS_LS goto ls_loi
echo LOI=%BUOC%> X:\ls.txt
reg query "HKLM\HARDWARE\DESCRIPTION\System\BIOS" /v SystemProductName >> X:\ls.txt 2>nul
copy /y X:\ls.txt \\192.168.98.1\cs-lich-su\%CS_LS%.txt >> %LOG% 2>&1
:ls_loi
echo.
echo  ================================================
echo    LOI: %BUOC%
echo.
echo    Xem chi tiet:  type %LOG%
echo  ================================================
echo.
start notepad %LOG%
cmd

