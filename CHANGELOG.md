# Changelog

## 1.5.0

**Cai Windows qua PXE chay duoc ca BIOS, UEFI va UEFI bat Secure Boot.** Anh
Thoai 25/09/2026: "may do la bios, uefi hoac co secure thi sao, minh phai boot
duoc het chu". Ban 1.4.x chi chay UEFI tat Secure Boot (anh dia GPT+FAT32 +
sanboot; iPXE cua Debian khong ky).

- Kem san iPXE v2.0.0 + wimboot v2.9.0 BAN KY chinh thuc (src/pxe-boot/, co
  README + SHA256SUMS; chu ky kiem bang sbverify). BIOS -> undionly.kpxe;
  UEFI -> snponly-shim.efi (Microsoft UEFI CA 2011) -> ipxe.efi (= snponly ban
  ky, shim xin dung ten nay). Khong con phai tai file boot len.
- Bo anh dia 500 MB/kich ban: wimboot nap boot.wim GOC + file nho cua kich ban
  (X:\Windows\System32). winpeshl.ini goi setup.exe /unattend:<duong dan> ->
  deploy.cmd nhu cu. Bat PXE con vai giay (truoc ~1 phut/kich ban). Anh cu
  _menu-*.img tu xoa (giai phong ~500 MB moi kich ban).
- deploy.cmd tu nhan BIOS/UEFI (PEFirmwareType): BIOS -> chia MBR (phan vung
  he thong NTFS active, >3 phan vung thi dung extended/logical) + bcdboot
  /f BIOS; UEFI -> GPT + bcdboot /f UEFI.
- SUA LOI LON: driver "nap vao anh boot" CHUA BAO GIO toi WinPE qua PXE -
  wimboot bo qua file duoi .wim (BIOS), iPXE UEFI lay ten file theo URL (UEFI).
  Nay chen duoi ten cpi-drivers.bin. Driver con duoc tiem vao Windows vua bung
  (dism /add-driver) - truoc day o PVSCSI/VMD/virtio se man hinh xanh lan
  khoi dong dau, card VMXNET3 mat mang sau cai. Kiem tren Pi that: BIOS
  VMXNET3+PVSCSI 11/11, UEFI VMXNET3+NVMe 42/42, Secure Boot VirtIO 65/65.
- Trang Tien trinh chi bao "da xong" SAU khi bao cao da ghi ra dia (tat may
  ngay luc bao xong truoc day mat bao cao). Bao cao ghi ma phan cung thiet bi
  thieu driver.
- An toan: cong mang da chon khong con (rut USB-LAN, doi ten) -> PXE / cam
  thang TU CHOI bat thay vi am tham phat DHCP tren cong khac.
- GOI DRIVER PHO BIEN (Drivers): WinPE Windows 10/11 thieu driver cho VMware
  VMXNET3/PVSCSI, Intel I225/I226 va I219 doi moi, Intel RST VMD, Realtek
  8125/8126, virtio (KVM/Proxmox) -> may do khong co mang / khong thay o dia
  (may ao VMware cua anh Thoai 26/09/2026). Bam "Tai" -> Pi tu tai goi CHINH
  THUC (Microsoft ky) tu Microsoft Update Catalog, kiem sha256, giai nen, danh
  dau nap vao anh boot + dung cho Windows sau cai. KHONG dong goi san driver
  cua hang (giay phep) - may cua nguoi dung tu tai nhu Windows Update. Danh
  sach: src/ui/goi-driver.json (10 goi x64, da kiem cai duoc tren WinPE 19041
  va 26100). LSI Logic Parallel khong co driver Win10 - trang huong dan doi
  sang LSI Logic SAS.
- Driver "cho anh boot" dong thanh drivers.wim (wimboot chi chen file phang),
  deploy.cmd bung bang dism roi drvload nhu cu.
- Trinh tao kich ban: o "Bang phan vung" GPT/MBR thanh "Tu dong theo may"
  (truoc day chon MBR cung BI BO QUA - luon chia GPT; nay deploy.cmd tu chon).
- Trang Tien trinh: may dich gui ten buoc tieng Viet -> PowerShell 5.1 ma hoa
  -Body chuoi theo ISO-8859-1 -> Pi khong doc duoc goi "batdau" (hien ban ghi
  "?" 0/0, buoc chi con "Buoc 1, Buoc 2..."). Sua: script gui byte UTF-8; Pi
  doc lai goi hong theo cp1252 thay vi bo ca goi. Ban ghi theo "ten may · IP"
  - 2 may cung ten (cung kich ban) khong con de trang thai len nhau.
- May x86 (ban ISO): nhiet do CPU doc them hwmon (coretemp/k10temp) khi
  khong co thermal_zone0; khong co cam bien (may ao) -> ghi ro "may nay khong
  co cam bien nhiet do" thay vi "? do C". Nguon dien: "Khong ap dung - may
  nay khong phai Raspberry Pi" (co dau). "Cam cap ... vao Pi" -> "vao may nay".
- Ban ISO: may co 2 card LAN cai xong KHONG co mang - trinh cai dat de lai 1
  ho so NetworkManager "Wired connection 1" khong gan card, NM cam no vao card
  khong co DHCP va bo trong card co DHCP. Thiet lap lan dau nay xoa ho so DHCP
  khong gan card (giu ho so IP tinh/da gan card) -> NM tu tao ho so cho tung
  card. Thiet lap lan dau xep TRUOC NetworkManager (xoa luc NM dang chay thi
  NM khong tu tao lai ho so - may cai moi van mat mang, lab 26/09/2026).
  Kiem chung may ao 2 card: ens3 nhan IP ngay, ens4 co ho so rieng.
- Ban ISO: kho Samba KHONG dung duoc - thiet lap lan dau tao nham tai khoan
  "deploy" trong khi share va deploy.cmd dung "consolepi-deploy" -> WinPE
  `net use` bao System error 1312, khong lay duoc install.wim (lab may chu cai
  tu ISO, 26/09/2026). Sua ca 2 dau: lan dau tao dung ten; va moi lan bat PXE
  / cap nhat menu, ui/pxe.py tu dam bao tai khoan ton tai + mat khau khop file
  khoa (may DA cai tu ISO loi tu het sau khi cap nhat). Them muc kiem tra vao
  kiem-tra-may-da-cai.sh.
- Kich ban co script .ps1: script KHONG chay ma mo ra Notepad (goi thang
  duong dan file - lien ket mac dinh cua .ps1 la "Edit"), buoc tien trinh dung
  toi qua gio. Nay .ps1 chay qua powershell -ExecutionPolicy Bypass -File.
- Tuy chon gom nhieu lenh hien "(1/2)", "(2/2)" tren bang tien trinh thay vi
  2 dong trung ten (trong nhu chay trung).
- Bao cao: PowerShell 5.1 ConvertFrom-Json tra ca mang thanh 1 doi tuong ->
  dong "Sau dang nhap" khong hien (lab Win11). Sua: gan bien truoc khi duyet.
  Them C:\ConsolePi\bao-cao-day-du.json (ca muc chua dat) cho ky thuat.
- Tuy chon "Tat Widgets": Windows 11 moi chan ghi HKCU TaskbarDa (Ma loi 1 -
  lab Win11 24H2). Nay dung chinh sach may: Dsh\AllowNewsAndInterests=0
  (Win11) + Windows Feeds\EnableFeeds=0 (Win10).
- Go app kem san: truoc chi go o phien nguoi dung dau - Weather/Solitaire VAN
  CON (lenh can quyen quan tri, loi bi nuot, buoc van bao "xong" - lo ra nho
  bao-cao-day-du.json). Nay deploy.cmd go ngay trong WinPE tren anh vua bung
  (dism /Image:W:\ /Remove-ProvisionedAppxPackage, kieu MDT).
- Bao cao: khoa HKU\... (Num Lock) luon "khong tim thay" - PowerShell khong co
  o HKU:/HKCR:. Doi sang Registry::HKEY_USERS\... / HKEY_CLASSES_ROOT\...
- Menu PXE "1. Win PE - cuu ho may" (truoc: "chua co"): moi bo Windows co
  boot.wim 1 muc. Boot boot.wim image 2 + winpeshl.ini mo cmd cuu ho (diskpart,
  notepad de chep file, bcdboot, chkdsk, net use) - co nap driver "cho anh
  boot", KHONG kem mat khau kho. Image 1 cua boot.wim bo cai khong boot rieng
  duoc ("SYSTEMROOT X:\$windows.~bt"). Kiem chung: may UEFI+Secure Boot vao
  WinPE, co mang.
- May dich treo o buoc mang (may ao VMware card E1000 cua anh Thoai): wpeinit
  goi dong bo nen card nap driver cham/treo = ca script dung. Nay wpeinit chay o
  nen, cho mang ~5 phut; ghi canh bao card chua co driver luc giay 30, het gio
  moi ket luan va bao TEN card thieu driver (VMXNET3, I225/I226, virtio...).
  Card VMware E1000 (82545EM) - WinPE Win10/11 treo khi nap driver (loi cua
  VMware, lab QEMU cung chip thi chay, nap cham ~75s) - script nhan ra ngay tu
  dau va huong dan doi sang E1000E.
- Khong thay o dia (may ao VMware Workstation cua anh Thoai: bo dieu khien LSI
  Logic Parallel - WinPE Win10/11 khong co driver): truoc day diskpart hong
  nhung script van chay tiep, bao "Error: 3" o buoc bung anh. Nay kiem 'list
  disk' TRUOC khi chia (khong thay -> liet ke bo dieu khien o dia thieu driver
  + cach sua: LSI SAS/SATA/NVMe, Intel RST/VMD) va kiem o W: SAU khi chia.
- Bo nut "Trich bootmgr" va yeu cau BCD tu ISO (wimboot tu lay trong boot.wim).
- Menu "Khoi dong o cung" tren UEFI dung `exit 1` (truoc la `exit`): may ao
  UEFI cai tu Pi that - moi lan Windows tu khoi dong lai giua luc cai, menu
  het gio -> `exit` -> firmware DUNG o man hinh Setup (OVMF) thay vi vao o
  cung. `exit 1` = "boot mang khong thanh" -> firmware thu muc ke tiep; kiem
  chung lab: vao thang Windows. BIOS giu `exit` (da chay dung).
- Lab tu dong iso/test/wimboot-lab.sh (QEMU/KVM, OVMF khoa Microsoft): BIOS,
  UEFI, UEFI+SB deu vao WinPE, chay script, net use Samba thanh cong.
- Ban 32-bit (Debian 12) - sua loi tester bat duoc 26/09/2026:
  - Kiosk man hinh den: cage 0.1.4 (wlroots 0.15) cua bookworm can
    /usr/bin/Xwayland nhung khong khai phu thuoc; them `xwayland` vao
    iso/i386/danh-sach-goi.txt. Ban 64-bit/Pi (trixie, cage 0.2.0 Depends
    xwayland) da tu co, khong them.
  - Kiosk chet vi SIGHUP ~60 ms sau khi chay roi tra ve dong lenh (ca 32 lan
    64-bit, nhat la khi chay live): ExecStartPost cung bi TTYVHangup tty1 ->
    giet cage. Bo ExecStartPost; canh gac chay bang unit tam (systemd-run,
    BindsTo kiosk) tha tu buoc chuan-bi.
  - QEMU/Proxmox card "std" (bochs-drm): cage bao "PRIME import not
    supported" roi TREO, kiosk van "active", man hinh den mai. Khong bien
    WLR_* nao cuu duoc (da thu). Canh gac nay canh ca duong ve bang CPU: cage
    bao loi (doc nhat ky) hoac 90 giay chua co Chromium -> bat getty@tty1
    (kiosk dung, khong lap lai). Duong GPU loi cung doi sang CPU som hon.
  - Doc ISO Windows hong: bookworm chi co lenh `7zz`. ui/isotach.py dung
    `7z` hoac `7zz` (cai nao co), thieu ca hai thi bao ro cach cai;
    install.sh coi `7zz` la du; iso/test/kiem-tra-may-da-cai.sh kiem 7z/7zz.
  - Ten he thong: os-release, /etc/issue (ca 2 ban) va Calamares lay phien
    ban tu file VERSION thay vi viet cung "1.0"; bo iso/i386/os-release
    (base-files ghi de, vo dung).
  - Dashboard chay live hien Dia "0 / 0 GB 0%" (so cua RAM) - nay ghi
    "không áp dụng (đang chạy từ USB/live...)".
  - Kiem chung: build lai ISO 32-bit (1042 MB; co Xwayland, 7zz, os-release
    "Console System 1.5.0 (32-bit)"); boot live `-vga virtio` -> kiosk hien
    dashboard, 0 lan restart, kiem-tra-may-da-cai.sh 34 dat / 0 loi; `-vga
    std` -> 19 giay sau ve dong lenh co logo + IP, kiosk "failed" khong lap;
    isotach doc muc luc + tach file tu ISO thu bang 7zz (live bookworm) va 7z
    (Pi), md5 khop; py_compile Python 3.13 (Pi) va 3.11 (chroot i386).
    CHUA test: ban 64-bit (khong build lai), cai 32-bit vao o cung, may that.

## 1.4.2

**May khach BIOS/Legacy dung im sau "Booting from SAN device 0x80".** Loi that
tren may VMware cua anh Thoai 25/09/2026 (Firmware = BIOS): chon kich ban, may
doc 3 khoi dau anh dia roi dung mai, khong bao loi. Nguyen nhan: anh cai
Windows la GPT+FAT32 chi co duong boot UEFI (440 byte ma boot MBR toan 0).
Sua: menu iPXE kiem tra `${platform}`; may khong phai UEFI -> hien huong dan
chuyen sang UEFI + tat Secure Boot, bam phim quay lai menu. Them ghi chu vao
tai lieu.

**Bat PXE sau moi lan cap nhat khong con dung lai het anh dia.** Dau van tay anh
dia truoc day tinh theo NGAY GIO file code - cap-nhat-pi.sh chep lai moi file
nen lan bat PXE dau sau moi lan cap nhat deu dung lai tat ca (~1 phut/kich
ban, 3 kich ban = 3 phut). Nay bam theo NOI DUNG unattend.py + deployos.py
(2 file sinh noi dung anh). Lan bat dau tien sau ban 1.4.2 van dung lai 1 lan
vi cach tinh doi.

## 1.4.1

**Sua loi che do "mang co san DHCP": may khach bao "Nothing to boot", khong
thay menu.** Loi that tren may VMware cua anh Thoai 25/09/2026.

Nguyen nhan (tai hien trong phong thi nghiem: router DHCP + Pi proxyDHCP +
may khach QEMU, bat goi tin 2 phia): iPXE hoi Pi qua cong 4011, Pi tra loi CO
ten file menu nhung next-server (siaddr) = 0.0.0.0 -> iPXE loai goi
(src/net/udp/dhcp.c, dhcp_has_pxeopts: proxyDHCP chi hop le khi co ca
next-server lan ten file). Sua: 3 dong dhcp-boot ghi ro dia chi Pi o truong
thu 3 -> dnsmasq dien siaddr.

Kiem chung (phong thi nghiem, file cau hinh sinh boi chinh code, menu that 2
kich ban): BIOS x 3 che do (co DHCP, khong DHCP, cam thang) - deu hien menu,
vao "Install Windows", chon kich ban thu 2 -> tai dung `_menu-B.img`. Truoc
khi sua: tai hien dung loi "Nothing to boot". CHUA kiem chung UEFI trong phong
thi nghiem (OVMF cua Debian khong tu boot mang; may build mat ket noi giua
chung) - phan UEFI dung chung dong dhcp-boot tag ipxe da sua.

## 1.4.0

**Chi con menu PXE: bat PXE -> may khach tu chon kich ban. Bo nut "Dung".**
Anh Thoai 25/09/2026: "co menu va khi nao client chon kich ban thi moi bat
dau boot, con phan 'dung' kia thi thoi".

- Tab Cai dat -> Bat / Tat PXE la noi DUY NHAT bat PXE: chon che do mang
  (truc tiep / mang khong DHCP / mang co san DHCP - mac dinh "co DHCP" vi
  khong bao gio tranh cap IP voi router), so giay cho, bam Bat PXE. Dung 1 anh
  dia cho moi kich ban Windows roi bat menu. Dang bat: "Cap nhat menu" va
  "Tat PXE"; doi che do = tat roi bat lai. Co bang kich ban trong menu
  (co / thieu gi / chua co anh) va xem truoc man hinh may khach.
- Trang nay TUNG khong hien thong bao ket qua (flash bi nuot) - bam Bat PXE
  khong biet thanh cong hay loi. Da sua.
- Bo nut "Dung", route `/deployos/kichban/dung/<ten>`, anh chung
  `windows-autounattend.img` (tu xoa khi bat PXE, ~500 MB) va duong wimboot
  tran. Menu la duong duy nhat.
- Menu chinh het gio -> khoi dong o cung; danh sach kich ban cho nguoi chon,
  khong tu cai. Bo tuy chon "muc mac dinh"/"bat menu".
- Trinh tu tao kich ban: bo buoc "Kieu boot" (con 6 buoc, danh so lai); bo
  dong "Kieu boot" o tong ket va tom tat kich ban.
- Tai lieu: che do mang chon khi bat PXE; loi that "mang khong DHCP" tren
  mang cong ty -> iPXE nhan IP router, "Nothing to boot".

Kiem chung: Flask test client voi du lieu tam, MOI lenh he thong duoc thay
bang lenh gia (khong dung eth0/dnsmasq cua Pi dang chay): bat PXE che do co
DHCP -> dung dung 2 anh (bo kich ban thieu mat khau, bao ro), xoa anh chung
cu, menu.ipxe dung dia chi Pi, khong nmcli/ip; cap nhat menu dung lai anh;
tat PXE; trinh tu buoc 1->2, 8->2, lui tu buoc dau; cac trang 200.

## 1.3.3

**Sua loi "PXE cua Console Pi khong bat duoc" (bat menu PXE tren Pi).**
Loi that tren Pi cua anh Thoai 24/09/2026:

- Bat menu thi "Bat PXE" dung them 1 anh dia cho moi kich ban Windows
  (~1-2 phut/cai tren Pi) -> trang quay lau, bam them lan nua -> 2 lan bat
  CHAY CHONG: lan sau bao thieu cho (file tam cua lan truoc chiem o) va bo
  kich ban khoi menu, ca 2 cung khoi dong lai dnsmasq/ghi de menu.ipxe.
  Sua: khoa (RLock) cho bat_pxe / tat_pxe / cap_nhat_menu - lan bam sau duoc
  bao "dang lam, cho xong, khong can bam lai".
- `sync` 30s / `umount` 15s khong du cho the SD ghi ~500 MB -> umount bi cat
  ngang, anh dia KET mount (gpt-mnt-* treo, loop con gan). Sua: sync 600s,
  umount 300s; umount khong duoc thi bao loi, khong coi anh la xong.
- Truoc moi lan dung anh: don rac cua lan bi ngat (gpt-mnt-* con mount ->
  umount, gpt-src-*, *.dang-dung) va XOA dau van tay cua anh tung bi ket de
  bat buoc dung lai (dau van tay khop du file co the chua ghi du).
- Nut "Bat PXE" / "Dung": chu cho noi ro mat vai phut, KHONG bam lai.

Kiem chung: test khoa bang 2 luong (lan 2 bi tu choi dung thong bao, xong
thi bat lai binh thuong); don rac tren thu muc tam; tim dung file sau
/dev/loop1p1 tren chinh Pi (anh _menu-TEST_TOAN_BO.img dang ket that);
Flask test client luu kich ban -> menu van cap nhat.

## 1.3.2

**Menu PXE 2 tang: "1. Win PE" + "2. Install Windows" -> tat ca kich ban.**
Anh Thoai: "neu nhu la kich ban de lua chon thi co 1 cai a lua chon lam gi" -
ban 1.3.0 bat phai tick tung kich ban vao menu, de ra menu chi co 1 muc.

- Menu chinh: `1. Win PE` (dong chu, chua chon duoc - lam sau), `2. Install
  Windows >`, Khoi dong o cung, Khoi dong lai. Vao muc 2 thay TAT CA kich ban
  Windows du thong tin; Esc quay lai menu chinh; loi nap anh quay lai danh
  sach kich ban.
- Bo nut "Them vao menu" va route `/deployos/menu-pxe/kichban`. Cot "Menu PXE"
  nay chi cho biet: Co trong menu / thieu gi / chi Windows.
- Luu hoac xoa kich ban luc PXE dang bat -> tu dung/xoa anh dia va ghi lai
  menu.ipxe ngay.
- Mac dinh "Kich ban dang Dung": ca 2 tang dem nguoc (phong may van tu cai).
- Xem truoc tren web ve ca 2 man hinh, dung nhu iPXE hien (iPXE gop dau cach).

Kiem chung: iPXE that trong QEMU (menu chinh, vao Install Windows, chon kich
ban thu 2 -> nap dung `_menu-<ten>.img`, loi -> ve danh sach, Esc -> menu
chinh); Flask test client voi du lieu tam + gia lap PXE dang bat (luu kich ban
-> dung anh + vao menu, xoa -> bo khoi menu + xoa anh, PXE tat -> khong dung).

## 1.3.1

**Sua loi install.sh: Pi cai moi thieu cong cu cho Deployment OS.**
install.sh chua bao gio cai cac lenh ma Deployment OS goi (wimlib-imagex,
wiminfo, 7z, parted, mkfs.vfat, mformat/mcopy). Pi dang chay duoc chi vi cac
goi nay da cai tay / co san - Pi cai moi tu ban Lite se bao "No such file or
directory" khi nap ISO hoac bam "Dung" kich ban.

- Them mang `PKGS_DEPLOY` (wimtools 7zip parted dosfstools mtools), luon cai
  (khong phu thuoc man hinh), giong danh sach goi ban ISO x86.
- Pi OS cu khong co goi `7zip`: da co lenh `7z` thi bo qua; chua co thi tu
  doi sang `p7zip-full` de apt-get khong dung ca buoc cai goi.

Kiem chung: `bash -n`; chay rieng doan logic (Pi nay: khong thieu goi nao;
gia lap thieu 7zip + ban cu: doi dung thanh p7zip-full); `apt-cache policy`
tren Pi (Debian 13 trixie arm64) - ca 5 goi deu co.

## 1.3.0

**Menu PXE: may khach tu chon kich ban ngay tai may (kieu MDT) - "Buoc A".**
Truoc day PXE chi phuc vu dung 1 kich ban (cai vua bam "Dung"); cai may khac
bang kich ban khac phai quay lai web doi. Nay bat menu thi may khach boot qua
mang thay danh sach kich ban, chon bang phim mui ten + Enter.

- Tab Kich ban: cot "Menu PXE" (Them vao menu / Co trong menu) + hop cai dat
  menu: bat/tat, so giay cho, muc mac dinh ("Kich ban dang Dung" = tu cai cho
  phong may, hoac "Khoi dong o cung" = an toan). Co xem truoc man hinh may
  khach. Bam Esc tai menu luon la khoi dong o cung.
- Moi kich ban trong menu 1 anh dia rieng, dung bang CHINH ham cua nut "Dung"
  voi cau hinh nap y het (tach ra deployos.cauhinh_tu_kichban) - 2 duong khong
  bao gio lech nhau. Chi dung lai anh nao da doi (dau van tay: kich ban + dia
  chi Pi + boot.wim + ma nguon); bo khoi menu thi anh tu xoa.
- Menu TAT (mac dinh) thi menu.ipxe y het ban cu - khong doi gi voi nguoi
  dang dung.
- **Sua loi cua ban ISO**: thieu `parted` (va `dosfstools` o ban 32-bit) ->
  Deployment OS tren may x86 bam "Dung" bao "No such file or directory:
  'parted'", chua bao gio dung duoc anh dia cai dat. Pi khong bi vi Raspberry
  Pi OS co san.

Kiem chung: menu chay tren iPXE THAT (QEMU): hien dung, dem nguoc, het gio
chay muc mac dinh, mui ten + Enter chon dung anh, Esc -> o cung, thieu anh ->
bao loi quay lai menu, chon muc tro toi anh boot duoc -> boot that. Dung anh
that bang boot.wim Windows 10 tren may Console System x86: anh chinh 46s, anh
menu 19s, lan 2 dung lai 0s; mo anh ra kiem tra moi anh dung ten may cua kich
ban minh. Them/bo kich ban luc PXE dang bat -> tu dung lai (doi dia chi Pi) va
ghi lai menu; tat menu -> menu.ipxe ve dung 1 dong nhu cu. 16 trang Deployment
OS + trinh tu sua kich ban 7 buoc deu 200, khong loi.

## 1.2.4

**Kiosk hien hinh tren MOI loai may, ke ca may ao VMware.** Anh Thoai chay
ban ISO tren VMware: man hinh den. "lo nhu sau nay user chay tren may ao
thi sao ... file nay phai chay duoc nhieu loai may cua nhieu hang khac nhau".

Nguyen nhan THAT (SSH vao chinh may VMware cua anh Thoai, doc nhat ky): may
ao khong co 3D -> cage bao "VMware: No 3D enabled ... Unable to create the
wlroots renderer" roi TREO LUON, bo qua ca lenh dung - co che "loi 5 lan
thi tra dong lenh" khong bao gio chay, man hinh den vinh vien.

- Script moi `console-system-kiosk-ve` chon cach ve moi lan kiosk khoi dong:
  card Intel/AMD (ca card roi lan iGPU tich hop trong CPU) ve bang GPU; may
  ao, card may chu (iDRAC/iLO), nouveau, simpledrm... ve bang CPU (cage
  `WLR_RENDERER=pixman` + Chromium `--disable-gpu`).
- Canh gac: chon GPU ma 90 giay chua co trinh duyet (card that nhung loi
  driver/firmware) -> tu doi sang CPU, ghi nho cho may do. Kiosk thoat loi 2
  lan lien bang GPU cung doi sang CPU.
- May ao nay CUNG tu bat kiosk sau khi cai (truoc day bo qua).
- **Sua loi cua 1.2.3**: khoi dong lai kiosk (vd doi xoay man hinh o tab Cai
  dat) lam mat kiosk, rot ve dong lenh.
- Tat hop thoai "Dich trang Vietnamese/English" cua Chromium tren kiosk.

Kiem chung tren may VMware THAT cua anh Thoai (anh Thoai nhin man hinh xac
nhan hien dashboard): ve bang CPU hien sau 5-15 giay; ep ve bang GPU de
cage treo that -> 90 giay sau tu doi CPU, hien dashboard, khong den man
hinh; restart, Tat/Bat tren web, kiosk crash, khoi dong lai may - deu dung.

## 1.2.3

**Cai xong la vao kiosk luon + tat kiosk khong con den man hinh.** Anh
Thoai cai len mini PC Dell co cam man hinh: cai xong chi co dong lenh, phai
go lenh moi hien giao dien; bam "Tat giao dien man hinh" tren web thi man
hinh den thui, chi con con tro nhap nhay.

- Truoc day kiosk chi bat neu luc khoi dong lan dau "thay man hinh", nhung
  luc do driver card man hinh (Intel) chua nap xong -> ket luan nham. Nay
  may that cai xong la BAT KIOSK LUON (theo yeu cau anh Thoai); kiosk tu cho
  driver man hinh nap xong (toi da 60 giay). May ao van khong tu bat.
- Tat kiosk (nut tren web hoac `systemctl stop/disable`) thi tu bat lai
  dong lenh dang nhap tren man hinh. Kiosk bi loi thi van tu chay lai nhu
  cu, loi 5 lan moi tra ve dong lenh.
- Man hinh chao bo cau "khong co giao dien do hoa".

Kiem chung (may ao gia lap may that, card man hinh std-VGA): lan khoi dong
dau tu vao dashboard; khoi dong lai van vao; bam Tat tren web -> hien
`console-system login:`; bam Bat lai -> vao dashboard; giet cage -> kiosk tu
chay lai; khong unit nao loi.

**May da cai tu ban cu** - sua tat-kiosk-den-man-hinh (khong can cai lai):

```bash
printf '[Service]\nExecStopPost=+/bin/sh -c %s\n' "'[ \"\$\$SERVICE_RESULT\" = success ] && systemctl start --no-block getty@tty1.service; true'" | sudo tee /etc/systemd/system/console-pi-kiosk.service.d/30-tra-tty1.conf
sudo systemctl daemon-reload
```

## 1.2.2

**May cai bang TRINH CAI CHU khong cai them duoc goi nao - da sua.** Sau
khi sua loi `VERSION_CODENAME` (1.2.1), bam "Cai Tailscale" tren may cai
bang trinh cai chu van that bai: *"Depends: iptables but it is not
installable"*. Nguyen nhan: may cai bang trinh cai chu co
`/etc/apt/sources.list` TRONG TRON (chi co dong cdrom da bi comment), nen
`apt install` bat ky goi nao cung hong. May cai bang trinh cai do hoa khong
bi.

- Cuoi qua trinh cai, trinh cai chu tu ghi nguon goi Debian chinh thuc
  (`deb.debian.org` + `security.debian.org`) dung ten ban (trixie/bookworm).
  Chay duoc ca khi cai khong co mang; chi ghi khi chua co nguon nao - khong
  de len mirror rieng nguoi cai da chon.
- Sua dong preseed `popularity-contest` thieu truong nen bi trinh cai bo qua.

Kiem chung: cai tu dong bang trinh cai chu trong may ao, boot len - web bam
"Cai Tailscale" thanh cong (Tailscale 1.102.4, dich vu dang chay).

**May DA CAI tu ban cu** sua tay (chay 1 lan, qua SSH hoac terminal):

```bash
grep -q ^VERSION_CODENAME /etc/os-release || echo "VERSION_CODENAME=$(. /usr/lib/os-release; echo $VERSION_CODENAME)" | sudo tee -a /etc/os-release
grep -v cdrom: /etc/apt/sources.list | grep -q '^deb ' || printf 'deb http://deb.debian.org/debian %s main contrib non-free non-free-firmware\ndeb http://deb.debian.org/debian %s-updates main contrib non-free non-free-firmware\ndeb http://security.debian.org/debian-security %s-security main contrib non-free non-free-firmware\n' $(. /usr/lib/os-release; echo $VERSION_CODENAME $VERSION_CODENAME $VERSION_CODENAME) | sudo tee /etc/apt/sources.list
sudo apt update
```

## 1.2.1

**Cai Tailscale bao "VERSION_CODENAME: parameter not set" du may vao duoc
internet - da sua.** Anh Thoai bam "Cai Tailscale" tren may cai tu ISO:
`ping 8.8.8.8` van duoc nhung trang bao cai that bai. Nguyen nhan: luc doi
ten he thong thanh "Console System", hook viet lai `/etc/os-release` bang
tay va lam mat dong `VERSION_CODENAME` (trixie/bookworm) - script cai chinh
thuc cua Tailscale (va cua nhieu phan mem khac: Docker, Grafana...) doc
dong do de chon dung kho goi.

- Nay lay nguyen file goc cua Debian va chi doi ten hien thi; thieu
  `VERSION_CODENAME` thi ban build tu dung lai bao loi.
- Ban i386 truoc do bi dung nham hook cua ban amd64 (tu nhan "Debian 13"
  trong khi la Debian 12) - da dung lai dung hook, va them buoc xoa file
  tang toc build khoi may i386 da cai.

Kiem chung: chay dung script `curl -fsSL https://tailscale.com/install.sh
| sh` trong chroot cua ban amd64 - cai thanh cong Tailscale 1.102.4.

May DA CAI tu ban 1.2.0 tro ve truoc: xem lenh sua tay o muc 1.2.2.

## 1.2.0

**Trinh cai dat do hoa (Calamares) + ban ISO ra dung duoc cho khach.** Anh
Thoai: "co the lam giong nhu windows ma hinh dep... chu khong dung mac dinh
cua debian nua". Ban ISO 64-bit nay co them muc menu *CAI Console System -
giao dien do hoa (khuyen dung)*: 5 buoc bam Tiep/Quay lai, co so do o dia
truoc/sau, co trang gioi thieu chay trong luc chep file. Trinh cai chu cua
Debian van giu lam duong du phong cho may loi do hoa.

### Trinh cai do hoa
- Giao dien tieng Viet, thuong hieu Console System (logo, mau, anh chao).
- **KHONG chon san o dia, khong chon san cach chia** - dung nguyen tac an
  toan xuyen suot du an. O USB dang cai khong hien trong danh sach.
- Cai xong TU GO trinh cai + thu vien Qt + live-boot khoi may da cai, tu
  sinh khoa SSH rieng cho tung may, bo dong nguon `file:/run/live/medium`
  va cac dong `deb-src` trong `sources.list`.
- Cai GRUB da ky (shim) cho may UEFI, them ca duong du phong
  `/EFI/BOOT/BOOTX64.EFI`; may BIOS thi cai `grub-pc`.
- **Sua 113 chuoi trong ban dich tieng Viet cua Calamares 3.3.14**
  (`iso/calamares/lang/sua-ban-dich-vi.py` - chay lai duoc khi len ban moi).
  Ban goc co loi hien ngay tren man hinh: "Hay cho **Vigo** biet ten day du
  cua ban?", "Tu dang nhat", o "Yeu cau mat khau manh" bi dich NGUOC nghia,
  va ca hop xac nhan truoc khi XOA DIA ("Install Now"/"Go Back") lan phan
  mo ta thao tac phan vung van con nguyen tieng Anh.
- **Tat o "Ma hoa he thong"**: anh dia khong co `cryptsetup`, khach tick vao
  la cai xong khong mo khoa duoc luc boot (bat duoc khi cai thu).
- Ban 32-bit (i386) CO Y khong co trinh cai do hoa: Calamares cua Debian 12
  keo theo QtWebKit + KDE Frameworks (~200MB), qua nang cho may doi cu.

### Sua loi tim duoc khi cai that ra may x86
- **THIEU `microcom` trong ISO - chuc nang CHINH cua san pham (cam cap
  console vao switch/router) hong tren moi may cai tu ISO tu truoc den
  gio.** `scripts/ttyd-one.sh` goi thang lenh `microcom` de mo cong serial,
  nhung goi nay chi co trong danh sach cai cua Pi (`install.sh`), khong co
  trong danh sach goi cua ISO. Hau qua: dich vu console van bao "active",
  trang Console van hien dung cong, nhung bam "Mo Console" thi khong co
  phien nao - API tra "Khong tao duoc phien console". Kiem chung that:
  cam cap USB-serial gia lap switch vao may cai tu ISO, go duoc lenh va
  doc duoc phan hoi sau khi them goi.
- Thieu ca `pipewire`/`pipewire-pulse`/`wireplumber`: tab Giai tri (video)
  chay hinh nhung KHONG CO TIENG, khong bao loi gi.
- **Vua bat may, mo trang web ra "502 Bad Gateway"** muoi may giay (Flask
  chua kip mo cong 5000), cac trang terminal con ra "500". Nay nginx tra
  trang "Console System dang khoi dong..." tu tai lai sau 3 giay. Chi bat
  loi do nginx sinh ra - loi 500 that cua Flask van hien nguyen.
- **Cong mang tren may x86 ten `ens3`/`enp1s0`, khong phai `eth0`**:
  - trang chu KHONG hien card LAN nao (bang mang trong tron),
  - trang TFTP khong hien duoc IP de go vao lenh tren switch,
  - `/api/system` bo sot toan bo phan mang.
- **802.1X**: bam Chay voi o trong thi hien loi tho cua chuong trinh
  (`eapol_test ... Assertion '0' failed`). Nay kiem tra du lieu nhap truoc.
- **Kiem tra DNS bao nham "bi can thiep"**: DNS he thong tra 1 IP, cac DNS
  cong khai tra 4 IP trong do co chinh IP do (binh thuong voi CDN). Nay chi
  canh bao khi co hai server tra ve hai tap IP KHONG TRUNG NHAU IP nao.
- **Trang Bluetooth cho 5 giay moi lan mo** tren may khong co Bluetooth
  (`bluetoothctl` ngoi cho bluetoothd). Nay hoi kernel truoc, khong co thi
  bao ro "May nay khong co bo Bluetooth" va mo ngay (0.06s).
- Nhan TFTP ghi "dang bat tren eth0" trong khi dich vu nghe tren MOI cong
  (`--address 0.0.0.0:69`) - sai ca tren Pi. So do mang ghi "Console Pi"
  tren san pham ten Console System. Mo ta L2 scan ghi cung "eth0".

### Tai lieu
- Muc cai dat: 4 muc menu (ban i386 co 3), mo ta trinh cai do hoa, dung
  luong that.
- `iso/README.md`: them phan Calamares va bang anh xa file.

Kiem chung that tren ca hai ban (amd64 + i386), cai bang CA HAI trinh cai
(do hoa va chu), tren QEMU:
  - amd64, do hoa, UEFI: cai xong khoi dong duoc kem Secure Boot
    (`SecureBoot enabled`), sudo dung, khong dich vu nao that bai,
    dashboard tra 302, cong Console gop cap USB-serial (gia lap switch)
    go duoc `show version` va doc duoc phan hoi
  - amd64, do hoa, BIOS: cai xong khoi dong duoc trong 30s
  - amd64, trinh cai chu (d-i), UEFI: cai tu dong, cung dat het cac muc
    tren, Calamares/Qt khong co trong danh sach goi (khong bi anh huong)
  - i386, trinh cai chu (d-i), BIOS: cai tu dong, dat het cac muc tren
  - Ca hai bang goi da kiem lai co du `microcom` va `pipewire`

## 1.1.5

**Cai len mini PC that: hoi firmware + cai xong khong boot - da sua.** Anh
Thoai ghi USB bang Rufus, cai len mini PC: trinh cai dung lai hoi "Load
missing firmware from removable media? rtl_nic/rtl8168h-2.fw", va cai xong
thi khong boot vao duoc.

- **Firmware Realtek nhung san vao trinh cai** (`dung-iso.sh`, ~140KB):
  mini PC gia re gan nhu luon dung card Realtek. Trinh cai chi tim firmware
  trong `/firmware` cua USB dung mot lan, truot la hoi USB/dia mem. Them
  `hw-detect/load_firmware=false` de khong con hop thoai do.
- **May bat Secure Boot cai xong khong boot.** Nhat ky cai ghi ro
  `Recommended packages: grub-efi-amd64-signed` - trinh cai muon cai GRUB
  da ky nhung chi la goi "khuyen nghi", ma live-build de lai file
  `/etc/apt/apt.conf.d/00recommends` tat han goi khuyen nghi. Ket qua: o
  dia chi co GRUB CHUA KY, khong co `shimx64.efi`. Mini PC ban kem Windows
  bat san Secure Boot nen tu choi. Da xoa file do trong hook (sau khi cai
  goi cho ISO, nen ISO khong phinh them).
- **Mini PC bo qua muc boot trong NVRAM**: preseed
  `grub-installer/force-efi-extra-removable=true`, GRUB co them o
  `/EFI/BOOT/BOOTX64.EFI`.
- Tai lieu: huong dan Rufus chon **DD Image mode**.

Kiem chung that - cai tu dong qua `d-i` len o trang, ISO gan dang USB:
  - UEFI, bat Secure Boot, NVRAM trong: boot duoc, `SecureBoot enabled`,
    o co `shimx64.efi` ca o `EFI/console` lan `EFI/BOOT`
  - UEFI khong Secure Boot, NVRAM trong: boot duoc
  - BIOS: boot duoc, sudo chay, dashboard tra 302
  - Initrd amd64 co 36 file `rtl_nic` o `/usr/lib/firmware`, i386 co 31
    file o `/lib/firmware` (Debian 12 chua gop /usr)
Chua kiem chung duoc: card Realtek that (QEMU khong gia lap duoc r8168).

## 1.1.4

**Cai xong khong dung duoc sudo - da sua.** Anh Thoai cai len VMware, dang
nhap duoc nhung MOI lenh `sudo` deu bao "administrator is not in the
sudoers file. This incident will be reported." - tai khoan tao luc cai
khong duoc them vao nhom `sudo`.

Nguyen nhan: bo cai Debian (`user-setup`) chi tu them tai khoan moi vao
nhom `sudo` NEU goi `sudo` da co san dung luc no hoi tao tai khoan. Goi
`sudo` cua du an lai nam trong danh sach goi rieng, duoc cai o buoc SAU,
nen bi bo sot moi lan.

- `iso/preseed.cfg`: dien san `d-i passwd/user-default-groups` co san
  `sudo`, khong con phu thuoc thoi diem phat hien goi nua.
- `iso/includes/console-system-lan-dau`: them buoc tu kiem tra/tu vao lai
  nhom sudo o lan khoi dong dau (phong ban ISO cu hoac duong cai khac).

Kiem chung THAT (khong chi chay thu): dung QEMU tu dong cai HOAN TOAN qua
`d-i` (phan vung, tao tai khoan, cai GRUB) len o dia trang, sau do boot
dia da cai va SSH vao kiem `id administrator` + chay `sudo whoami` that
su - co nhom `sudo`, lenh chay duoc ngay tu lan dau, dashboard van hoat
dong binh thuong.

## 1.1.3

**Cai xong tren may ao thi man hinh den thui - da sua.** Anh Thoai cai len
VMware Workstation, xong khoi dong lai thi man hinh den hoan toan. Nguyen
nhan: card do hoa ao luon bao man hinh "connected" nen lan khoi dong dau tu
bat kiosk; kiosk chiem tty1, ma VMware chay tren Hyper-V khong co tang toc
3D (vmware.log: "Disabling 3d support") nen Chromium khong ve duoc gi.

- May ao (`systemd-detect-virt --vm`) khong tu bat kiosk nua. May that
  van tu bat nhu cu; may ao can thi bat tay trong Cai dat.
- Kiosk loi 5 lan trong 5 phut thi dung han va bat lai `getty@tty1`
  (OnFailure) - man hinh quay ve dong lenh co logo + IP.
- Bo gioi han khoi dong lai cua `getty@tty1`: lan thu dau, getty bi bat/tat
  qua lai theo kiosk qua nhanh nen bi systemd chan (start-limit-hit),
  kiosk da dung ma tty1 van den.

Kiem chung: boot ca 2 ISO (amd64, i386) trong QEMU - `detect-virt` = qemu,
kiosk disabled/inactive, getty@tty1 active, chup man hinh thay logo va
`http://10.0.2.15`. Rieng co che tra man hinh da thu bang cach co y lam
kiosk hong tren may ao: dung sau 5 lan, man hinh hien lai dong lenh.

## 1.1.2

**Menu boot UEFI gio khop voi menu BIOS.** Menu tieng Viet 3 muc lam o ban
1.1.0 chi ap dung cho may boot kieu BIOS (isolinux); may boot UEFI di duong
GRUB hoan toan khac nen van hien menu mac dinh cua live-build. Da chup man
hinh xac nhan truoc khi sua: 5 muc tieng Anh "Live system (amd64)" /
"Live system (amd64 fail-safe mode)" / "Start installer" /
"Advanced install options ..." / "Utilities...".

Them `config/bootloaders/grub-pc/` (nguon o `iso/bootloader-grub/`):
- 3 muc tieng Viet giong het ban BIOS, bo 2 muc long nhau
- Mau xanh cyan tren nen den cho hop tong Console System

**Loi kem theo da sua - menu UEFI doi mai khong tu chay.** live-build
khong dat timeout cho GRUB. Do that: boot trong may ao, chup man hinh luc
dau va sau 2 phut - trung MD5 tung byte, khong he dem lui. May cam trong
rack khong ban phim se dung im vinh vien. Ban BIOS da sua bang
"timeout 50" tu truoc, ban UEFI thi chua ai sua. Nay dat `set timeout=5`.

**CHO KHONG LAM DUOC - anh nen cho menu UEFI.** Bat anh nen len thi GRUB ve
mot O DEN DAC che kin giua man hinh (do duoc: trai 10%, tren 18%, rong 81%,
cao 73%) - dung vung hien danh sach, nen chi thay anh nen va thanh dem lui
chu KHONG THAY MUC NAO de bam. Da loai tru tung kha nang:
  - bo chu thich tu them vao theme  -> anh chup trung MD5, y nguyen
  - them `insmod gfxmenu`           -> trung MD5, y nguyen
  - chen mot dong chu thu mau do    -> HIEN RA, tuc file theme cua minh
                                       that su duoc dung
  - thu nho cua so terminal         -> o den bien mat, 3 muc hien du,
                                       nhung mat luon anh nen
  - **dung theme GOC cua live-build, khong sua mot chu nao -> VAN BI Y HET**
Thu cuoi la quyet dinh: loi nam trong theme cua live-build / GRUB 2.12.
Sua tan goc phai dung vao ruot GRUB - khong dang danh doi cho mot thu chi
la trang tri, trong khi de nguyen thi nguoi dung khong bam duoc vao dau.
Nen bo anh nen o menu UEFI, chi doi mau. Menu BIOS van co anh nen day du.

Ban i386 khong bi anh huong: no chi dung syslinux, khong co duong UEFI.
## 1.1.1

**Sua loi "Install the GRUB boot loader - Installation step failed"** - anh
Thoai cai ban amd64 len may that (UEFI, khong cam mang, chia o kieu Guided)
thi dung o buoc cuoi. Da TAI HIEN nguyen van trong may ao roi doc log that,
tim ra HAI loi khac nhau chu khong phai mot.

*Gia thuyet dau tien da bo*: khong phai "khong co mang nen khong tai duoc
goi". Dia ISO co chi muc apt day du va apt trong trinh cai dat chay binh
thuong du khong mang - log co "Reading package lists... grub-common is
already the newest version".

**Loi 1 - may UEFI** (dung truong hop anh Thoai gap). Doc ma nguon
`/usr/bin/grub-installer` lay tu chinh dia: dong 912 cho thay
`grub-install` chi bo qua NVRAM khi duoc khai bao truoc, mac dinh la LUON
ghi muc khoi dong vao NVRAM - viec do can `efibootmgr`. Ma `grub-efi-amd64`
khong khai Recommends nao ca nen khong duong nao keo goi do ve.
SUA: cai san `efibootmgr`.

**Loi 2 - may BIOS** (chua ai bao cao, tu tai hien ra khi test).
grub-installer go het goi grub-efi ra truoc khi cai GRUB cho BIOS, nhung he
thong live co san `grub-efi-amd64-signed` - goi "Protected: yes" ma dpkg tu
choi go vinh vien. grub-installer co `set -e` nen dung ngay. Loi nay khong
lien quan gi toi mang.
SUA: bo khai `shim-signed` + `grub-efi-amd64-signed` khoi danh sach goi.
Doc `/usr/lib/live/build/binary` moi biet: binary_rootfs dong squashfs
TRUOC, binary_grub-efi moi TU cai hai goi do de lam file EFI cho dia roi go
ra ngay - tuc khai trong danh sach goi khong giup gi cho Secure Boot cua
dia, chi lam chung dinh vao he thong live.

**Kem theo - `os-prober`** (ca hai kien truc): khong co trong chi muc apt
cua dia va khong goi nao keo theo. Thieu no thi GRUB khong thay Windows
tren cung o ma them vao menu boot - khach hang tuong bi xoa mat Windows.

Ca ba goi deu la Recommends nen bi `--apt-recommends false` loai nham -
cung mot ho loi voi user-setup/sudo/nmcli truoc day.

**Nghiem thu** (cai that trong may ao, deu NGAT MANG):
- May UEFI: qua duoc buoc GRUB; boot lai tu o cung thi may len trong 43
  giay, khong viec treo, dashboard/nginx/ttyd deu active, ba trang web deu
  HTTP 200. Muc khoi dong UEFI co that trong NVRAM:
  `Boot0001* console ... \EFI\console\grubx64.efi`. Ba goi
  efibootmgr/grub-efi-amd64/shim-signed deu "install ok installed" tren may
  vua cai du khong he co mang.
- May BIOS: cai chay het den buoc cuoi va tu khoi dong lai.
- Secure Boot cua dia van nguyen: `bootx64.efi` trung MD5 tung byte voi
  `shimx64.efi.signed` (887305fc4744...) trong khi chroot khong con
  shim-signed.

**Con thieu, chua lam**: menu boot tieng Viet 3 muc chi ap dung cho may boot
kieu BIOS (isolinux). May boot UEFI van thay menu GRUB mac dinh cua Debian
(tieng Anh: "Live system", "Utilities"). Khong gay loi gi nhung khong dong
nhat.
## 1.1.0

Bon viec anh Thoai giao 20/09/2026, roi mot vong tu kiem tra rieng phat hien
them 6 loi lam ban cai x86 khong dung duoc that su - tat ca deu bat duoc
bang cach boot THAT trong QEMU roi goi vao dashboard ben trong, khong chi
nhin "co file ISO hay khong".

**Nut ve trang chu tren MOI trang** (yeu cau: "tat ca cac trang du co mo
trang khac thi cung phai co nut home, nhu 1 cai bong bong nho phia duoi
goc"). Ap dung ca cho 2 trang terminal (Local/SSH) - hai trang nay la ttyd,
nginx chuyen thang toi khong qua Flask nen phai chen bang `sub_filter` cua
nginx, gan vao `<html>` chu khong phai `<body>` (ttyd dung preact quan ly
con cua `<body>`, gan vao do se bi xoa mat).
- *Sua lai vi tri sau khi giao*: dat ban dau o goc trai duoi thi de thang
  len link "Dang xuat" cuoi thanh menu. Doi sang goc phai, xep ngay tren nut
  ban phim ao (`clamp(46px,7vh,58px)` - dung cong thuc chieu cao cua no de
  hai nut luon cach nhau dung 10px). Noi them dem cuoi trang 96px -> 150px.

**Giao dien tren man hinh cho ban ISO x86** (yeu cau: "thieu option cai khi
co man hinh, vi du laptop... giong nhu rasberry hien tai cua anh do co man
hinh"). Tu doc `/sys/class/drm/*/status` luc khoi dong lan dau - thay man
hinh dang cam thi tu bat kiosk (`cage` + Chromium), khong thay thi bo qua.
Them nut bat/tat tay trong tab Cai dat.

**Menu boot con 3 muc** (truoc la 8 muc long nhau kieu "Tuy chon cai dat
nang cao", trong do co "Automated install" chay `auto=true priority=critical`
KHONG HOI GI ke ca khong hoi chon o dia - nguy co xoa nham may co du lieu
khach): Chay thu - Chay thu che do an toan - Cai len o cung.

**Sau khi giao, tu kiem tra lai va bat duoc 6 loi that su, deu da sua**:

1. **May co man hinh treo boot vinh vien**: script thiet lap lan dau goi
   `systemctl enable --now console-pi-kiosk`. `--now` = bat roi CHAY VA DOI
   CHAY XONG, nhung dich vu kiosk lai xep hang SAU multi-user.target - trong
   khi chinh script nay chay TRUOC no. Hai ben doi nhau vinh vien, ca
   dashboard/terminal/kiosk deu ket cung ("waiting" trong
   `systemctl list-jobs` sau 9 phut). Sua: tach `enable` va
   `start --no-block`.
2. **Trang Terminal trong ISO bao 502 Bad Gateway**: `ttyd` khong nam trong
   kho goi Debian (kiem tra that: ca trixie lan bookworm deu
   "Candidate: (none)") nen khong the khai trong danh sach goi nhu binh
   thuong. Danh sach goi thieu han buoc tai no rieng (ban chay tren Pi co
   lam trong install.sh, ban ISO thi quen) -> dich vu terminal chet lap vo
   han voi ma loi 127. Sua: hook tai `ttyd` dung theo kien truc ngay trong
   chroot luc build, that bai la do vo ban build thay vi giao ISO co
   terminal chet.
3. **Ban amd64 thieu sach firmware man hinh Intel (i915)**: Debian 13 da
   tach i915 ra khoi `firmware-misc-nonfree` sang goi rieng
   `firmware-intel-graphics`; danh sach goi cu chi khai goi cu nen mat
   trang firmware cho dung loai GPU pho bien nhat tren laptop. Them
   `firmware-amd-graphics` + `firmware-intel-graphics` (amd64) va
   `firmware-amd-graphics` (i386, vi Debian 12 van de i915 chung trong goi
   cu). Gia ~2% kich thuoc ISO.
4. **Mot dau phan tram trong CHINH chu thich cua muc 3 lam mat 5 goi khoi
   ISO ma khong bao loi**: `lb build` cho file danh sach goi di qua
   `printf`; chuoi "2% k" bi hieu la ma dinh dang, in bo ngang va nuot sach
   moi dong con lai (2 dong firmware vua them, roi `cage`, `chromium`,
   `sudo`, `user-setup`) - may boot len khong ai dang nhap duoc, ma
   `lb build` van bao thanh cong. Dau hieu duy nhat la mot dong lap giua
   4600 dong `build.log`. Sua: bo dau phan tram (viet bang chu), them chan
   dau `dung-iso.sh` - thay dau phan tram trong danh sach goi la dung ngay.
5. **Kich ban tu test bao oan "ISO hong"**: `pkill -x qemu-system-x86_64`
   khong bao gio giet duoc gi - ten tien trinh bi kernel cat con 15 ky tu
   ("qemu-system-x86"), `-x` doi khop chinh xac nen luon that bai trong im
   lang. May ao cu con song giu mat cong chuyen tiep, may ao moi bi QEMU tu
   choi ngay roi chet, vong kiem tra thi cu goi vao may ao CU 600 giay roi
   ket luan sai la ISO khong boot duoc. Sua: giet theo PID, kiem tra cong da
   nha truoc khi test (khong dung `pkill -f` - da giet nham chinh phien SSH
   hai lan truoc day).
6. **Loi doc sai manifest goi (lai mot lan nua)**: dung `grep -c` voi `\b`
   qua SSH bi nuot escape, ket luan sai la thieu ca `chromium`/`cage`/
   `sudo`... trong khi thuc te co du. Sua bang `awk` so dung cot, khong doan
   qua regex.

**Nghiem thu cuoi cung** (boot that ca hai ban tren nen QEMU sach): amd64
1401MB boot 1 phut 37; i386 1030MB boot 3 phut 20. Ca hai: khong con viec
nao treo, 4 dich vu dashboard/nginx/ttyd-local/ttyd-ssh deu active, `/`,
`/nettools`, `/term-local/` deu HTTP 200 voi nut Home dung cho, terminal la
ttyd that (khong con trang loi 502 bi nham la "co nut nen dat"), kiosk
active tren may co man hinh.
## 1.0.0 - Console System OS

Ban cai Linux (.iso) cai duoc len laptop/may ban bat ky, cung mot bo cong
cu voi ban chay tren Raspberry Pi. Doi ten hien thi thanh **Console
System**. Toan bo cau hinh dung ISO nam trong thu muc `iso/`.

**Qua 6 vong dung-thu-sua.** Moi vong deu boot that trong QEMU roi goi
thang vao dashboard ben trong, khong chi kiem tra "co file ISO". Cac loi
bat duoc - deu la loai KHONG THE thay bang cach doc code:

1. **ISO boot len la tu chay DHCP server, phat WiFi, TFTP va Samba.** Debian
   tu bat dich vu khi cai goi. Cam may vao mang cong ty la thanh DHCP lau,
   sap mang khach. Da tat tuong minh (van cai san de bat khi can).
2. **Khong ai dang nhap duoc vao may**: `Authentication failure` ngay luc tu
   dang nhap. Do bat `--apt-recommends false` cho nhe nen loai nham
   `user-setup` va `sudo` (chung la Recommends cua live-config).
3. **Thieu `nmcli`** - cung ly do tren. ui/pxe.py va ui/direct.py dung no de
   chiem va TRA LAI cong mang; thieu thi bat PXE xong may mat mang.
4. **De quy vo han o `cong_wifi()`** - chi lo ra tren may KHONG CO card
   WiFi. Doan thay the hang loat da thay ca chuoi "wlan0" trong chinh ve du
   phong cua ham. Tren Pi khong bao gio lo vi Pi co WiFi.
5. **Thieu `python3-requests`** -> trang Kho trung tam loi 500.
6. **SSH bat nhung khong ai vao duoc** - anh dia chi nhan khoa cong khai,
   trong khi nguoi vua cai may chi co tai khoan/mat khau.
7. **Menu boot cho bam phim mai mai** (`timeout 0` mac dinh) - may khong cam
   man hinh se dung im vinh vien.
8. **Dich vu thiet lap lan dau co file nhung quen bat** -> mat khau kho
   Samba khong duoc sinh, bat PXE thi may can cai khong noi duoc kho.

**Ket qua nghiem thu cuoi** (chay trong ISO that dang boot): 24/24 trang
khong loi; dang nhap web va SSH bang mat khau deu duoc; chi mo dung 2 cong
ra mang (22, 80); cac dich vu nguy hiem deu inactive; ping va kiem tra DNS
chay that; va quan trong nhat - **he thong tu nhan cong mang `ens3`** cua
may ao x86 thay vi `eth0` viet cung.

**Toi uu:** 1492 MB -> **1136 MB**. Bo firmware do hoa (nvidia/amdgpu/i915,
224MB) vi may khong co desktop; GIU NGUYEN 94 thu muc firmware mang de chay
duoc moi laptop. Bo tai lieu goi va ~100 thu tieng khong dung.

**Secure Boot**: `bootx64.efi` tren ISO chinh la `shimx64.efi.signed` (doi
chieu ma bam MD5 trung khit) - laptop bat san Secure Boot khong phai vao
BIOS tat di.

## 0.5.0

Vong lam viec dem 18-19/09/2026 theo danh sach anh Thoai giao.

**Giao dien lam lai toan bo** (anh Thoai chon tone "hien dai ky thuat"):
chuyen tu xanh la sang nen toi + cyan, khai bao mot cho bang bien CSS.
Mau gio CO Y NGHIA thay vi trang tri: cyan = thao tac/dang chon, xanh la
= CHI danh cho trang thai tot, vang = canh bao, do = loi hoac hanh dong
pha huy. Nut chia 3 cap ro rang (chinh: nen dac; phu: vien mo - dung o 57
cho nen day la thay doi lam trang do roi nhat; nguy hiem: vien do). Man
PC tu dong gon lai, man cam ung van giu nut >=44px.
*Chung minh khong vo logic:* tach toan bo phan Python ngoai chuoi CSS o
ban cu va ban moi ra so - giong het 364/364 dong; tai lai 12 trang that
va doi chieu HTML - 10 trang giong tung byte, 2 trang chi lech o so lieu
song (CPU/RAM) va log vua xoay vong.

**Tai thang file ISO Windows len, Pi tu tach** boot.wim/install.wim
(truoc day phai muon mot may Windows de mount ISO chep tay 2 file). Sau
khi tach co BA lop kiem chung truoc khi dam xoa ISO: file khac rong,
kich thuoc khop tung byte voi muc luc ISO, va wimlib doc duoc ruot file.
Truot bat ky lop nao thi giu nguyen ISO va xoa 2 file hong di (de lai se
lam giao dien bao xanh "Da co" trong khi thuc te khong boot duoc).

**bat_pxe() luon di dung kieu boot cua kich ban duoc chon.** Truoc day
doi kieu boot trong khi PXE dang bat thi khong doi gi ca - dung nguyen
nhan lam may can cai treo o "Start PXE over IPv4". Nang hon: anh dia tung
duoc dung TRUOC khi doi che do mang nen nhet nham dia chi Pi cu vao, di
sang che do khac la WinPE khong tim thay kho trien khai.

**Popup thay cho khoi chu dai**: bang tra tham so cai im lang va phan
giai thich "ung dung nhieu file" gio nam trong hop thoai co nut Dong,
khong con chan mat danh sach that. Them o tim phan mem. Trang "Tien
trinh" gio co thanh tab Deployment OS (truoc day vao la cut duong).

**Hai cong cu bao tri moi** o trang Cai dat: xem dung luong the nho theo
tung muc kem don 3 loai rac an toan (ke ca file .part bo do - loai rac it
ai nghi toi ma co the nang vai GB), va sao luu/nap lai cau hinh qua file
.tar.gz nho vai KB (co chong zip slip, da thu tan cong that).

**Sua loi nginx lam tai file lon len bao 502 Bad Gateway**: khoi tat dem
bo sot dung duong /deployos/os/<id>/len nen anh Windows 5GB bi dem 5GB ra
dia truoc roi het gio 5 phut. Da phu ca os/drivers/ungdung va duong tai
ISO moi.

**Tai lieu**: them 5 muc con thieu - Deployment OS (phan lon nhat cua du
an ma truoc gio khong he co tai lieu), tach ISO, kho luu tru trung tam,
bao tri dung luong/sao luu, va theo doi tien trinh cai dat.

## 0.4.52

**Sua loi that su khien "Bat PXE" luon that bai** - nho thong bao loi
that (0.4.51 moi sua xong) anh Thoai bam lai va thay ro:
`Failed to restart console-pi-pxe.service: Unit console-pi-pxe.service
not found.`

Nguyen nhan: `ui/pxe.py` khai bao `DON_VI_SYSTEMD = "console-pi-pxe"`
nhung file don vi that su duoc tao ra la `dnsmasq-pxe.service` (xem
`systemd/dnsmasq-pxe.service`) - 2 ten khac nhau, dat sai tu dau. Bo
kiem thu truoc do khong bat duoc loi nay vi mock thang ham `bat_pxe()`
thay vi that su goi `systemctl`.

Sua: doi `DON_VI_SYSTEMD = "dnsmasq-pxe"` cho khop dung ten file.

**Kiem chung that BANG DUNG THAO TAC anh Thoai lam** (khong chi doc
code): di het 7 buoc qua HTTP, bam nut "Bat PXE" that su - lan nay thay
`systemctl status dnsmasq-pxe` bao `active (running)`, giao dien hien
dung thong bao xanh "Da bat PXE...", va `eth0` giu nguyen IP
192.168.110.14 (kieu "mang co DHCP" khong dong cham IP cua Pi). Da tat
lai sau khi kiem chung xong. selftest.sh 36 dat, 4 luu y.

## 0.4.51

**Sua loi "bam Bat PXE ma khong thay gi ca"** (anh Thoai bao thang sau khi
bam nut). Kiem tra lai code (khong doan) phat hien 2 loi:

1. Ca 3 route `/deployos/pxe/bat`, `/tat`, `/trich-bootmgr` VUT BO ket qua
   `(ok, msg)` roi redirect thang ve `/deployos/boot` - nguoi dung khong
   bao gio thay duoc thanh cong hay that bai, va con MAT LUON trinh tu
   dang lam (quay ve man hinh chon tu buoc 1).
2. Dong "PXE dang BAT (Pi la {PI_IP})" LUON hien dia chi tinh gia dinh
   192.168.98.1, ke ca khi dang chay o kieu "mang co DHCP" (luc do Pi
   that ra dung IP THAT do DHCP cap, vd 192.168.110.14) - thong tin sai,
   de nham lan khi debug.

**Sua**: dung `flash()` (session) mang thong diep qua redirect, quay VE
DUNG buoc 7 cua chinh trinh tu (giu "ma" qua truong an trong 3 form) thay
vi ve man hinh dau. Dong "dang BAT" gio doc dung dia chi theo kieu dang
chay that (luu trong STATE_FLAG) thay vi gia dinh PI_IP.

**Don don trang thai**: phien lam viec truoc do co chay tay
`systemctl start dnsmasq-pxe` de chan doan (khong qua nut Bat, nen flag
khong duoc ghi) - da dung lai dich vu do, dua he thong ve dung trang thai
"PXE dang tat" nhu giao dien hien thi.

Da kiem chung: 6 phep thu rieng cho loi nay (form co gan dung "ma", bam
that bai hien dung ly do va quay dung ve buoc 7, bam thanh cong hien dung
thong bao mau xanh, thong diep chi hien 1 lan roi tu xoa), dat het. Cong
voi 21+6 phep thu cu van dat. selftest.sh 36 dat, 4 luu y.

## 0.4.50

**Sua loi nghiem trong: kieu boot "mang co DHCP" (proxyDHCP) dung SAI dia
chi mang** - phat hien khi anh Thoai bao muon thu kieu nay truoc tien.

**Loi that (kiem chung bang code, khong doan)**: `ui/pxe.py` dung cung 1
hang so `PI_IP` (192.168.98.1 - dia chi TINH Pi tu dat cho kieu truc_tiep/
mang_khong_dhcp) cho CA kieu "mang co DHCP" - nhung o kieu nay Pi KHONG tu
dat IP, no giu nguyen IP THAT do DHCP cua mang khach cap (vd
192.168.110.14). Hau qua neu khong sua:
  - Dong `dhcp-range=192.168.98.0,proxy` sai hoan toan dai mang that
    (192.168.110.0/24) - proxyDHCP se khong khop dung mang, khong hoat
    dong tu dau.
  - Script iPXE sinh ra tro may dang boot toi `http://192.168.98.1/...` -
    dia chi khong ai lang nghe ca.
  - Con gui ca dong `dhcp-option=3` (gateway gia) khong can thiet trong
    che do proxy.

**Sua**: them `_dia_chi_pi_that(kieu_boot)` va `_mang_that(iface)` doc
THAT dia chi/dai mang hien tai cua eth0 qua `ip -o -4 addr show` khi o
kieu "mang co DHCP", thay vi gia dinh PI_IP. Ca dnsmasq conf lan script
iPXE deu dung ham nay. `bat_pxe()` gio kiem tra som (truoc khi ghi gi ca)
neu doc IP that that bai thi bao ro ly do (chua cam day/chua co DHCP)
thay vi ghi cau hinh sai roi that bai mo ho o buoc sau.

Da kiem chung lai: sinh dung `dhcp-range=192.168.110.0,proxy` va URL
`http://192.168.110.14/...` (dia chi that cua eth0 luc do), `dnsmasq
--test` hop le cho ca 3 kieu boot, khong con dhcp-option=3 gia trong che
do proxy. Bo kiem thu them 7 phep thu rieng cho loi nay, dat het (tong
21 phep thu cho pxe.py). selftest.sh 36 dat, 4 luu y. eth0 khong bi dong
cham trong qua trinh sua/test.

## 0.4.49

**Da co du file BCD - PXE san sang bat that su (4/4 dieu kien)**.

Anh Thoai tai lai ISO Windows 10 (lan truoc bi lo xoa som), lan nay lay
DAY DU 2 file `boot/bcd` (BIOS) va `efi/microsoft/boot/bcd` (UEFI) truoc
khi xoa ISO. Da luu thanh `bcd-bios`/`bcd-uefi` trong thu muc boot.

Kiem chung that: `pxe.trang_thai_chuan_bi()` bao du 4/4 (bootloader iPXE,
wimboot, bootmgr trich tu boot.wim, file BCD) - `san_sang_bat() == True`
lan dau tien. Di het 7 buoc qua HTTP that tren may song xac nhan nut
"Bat PXE ngay" hien dung, kem canh bao cat DHCP tren eth0. selftest.sh
36 dat, 4 luu y (khong doi).

CHUA tu bam "Bat PXE": viec nay cat DHCP tren chinh cong eth0 dang la
duong ket noi cua phien lam viec hien tai (192.168.110.14) - can anh
Thoai tu bam cung luc cam 1 may PC that vao Pi de thu, khong the tu dong
kiem chung buoc nay ma khong co phan cung that.

## 0.4.48

**Phat PXE that (giai doan ke tiep cua Deployment OS)** - tiep noi tab
0.4.45, lam cho muc "Cau hinh PXE cua dnsmasq" trong bang kiem tra san
sang thanh THAT thay vi chi bao "giai doan ke tiep".

**Da lam va kiem chung that tren may:**
- Cai `wimtools` (wimlib) - **dinh chinh so voi ke hoach ban dau**: KHONG
  can may Windows + Windows ADK de xu ly file `.wim`/`.esd` nhu du doan -
  wimlib tren Linux doc/tach/trich xuat truc tiep duoc, kiem chung that
  bang `wiminfo`/`wimlib-imagex export`/`extract` chay that tren Pi.
- Tach `install.wim` (Windows 10 Pro) tu `install.esd` gom 7 phien ban
  trong ISO.
- Tai `iPXE` (goi apt co san) va `wimboot` (du an chinh thuc cung tac gia
  iPXE, qua GitHub API).
- **Phat hien**: `\Windows\Boot\PXE\bootmgr.exe`/`wdsmgfw.efi` (bootmgr
  CHUYEN DUNG cho boot-qua-mang) nam SAN trong `boot.wim`, khong can lay
  tu ISO - da viet ham trich xuat truc tiep, kiem chung that.
- `ui/pxe.py`: cau hinh dnsmasq cho ca 3 kieu boot (truc tiep / mang khong
  DHCP dung DHCP day du; mang co DHCP dung proxyDHCP), nhan dien kien truc
  may (RFC 4578) de phat dung bootloader BIOS/UEFI, chan vong lap vo tan
  qua dhcp-userclass, sinh script iPXE nap wimboot+boot.wim+BCD+bootmgr.
  Kiem chung cu phap ca 3 cau hinh bang `dnsmasq --test` (hop le).
- Duong phuc vu file cho may dich qua HTTP KHONG dang nhap
  (`/deployos/pxeboot/<file>`) - chi mo khi PXE dang that su BAT, kiem thu
  chan vuot thu muc/duoi file la.
- The "San sang PXE" + nut Bat/Tat that trong buoc 7 cua trinh tu.
- Bo kiem thu rieng cho pxe.py: 14 phep thu, dat het.

**Loi that da gap (ghi lai de khong lap lai):**
- Da LO XOA file ISO goc truoc khi kip lay file `BCD` (2 file nho o
  `boot/bcd` va `efi/microsoft/boot/bcd`) - phai nho anh Thoai tai lai ISO.
  Bai hoc: xu ly ISO nguon phai liet ke DAY DU moi thu can trich TRUOC khi
  xoa ban goc, khong xoa theo tung dot.
- Ban dau dat dieu kien hien nut "Bat PXE" phu thuoc viec file
  `/etc/dnsmasq-pxe.conf` da ton tai san - nhung file do CHI duoc tao ra
  KHI bam chinh nut do, tao vong luan quan (nut can thiet bi chinh dieu
  kien cua no khoa). Da sua: bo han kiem tra tinh do, thay bang
  `pxe.trang_thai_chuan_bi()` la nguon su that duy nhat - kiem chung lai
  bang HTTP that: truoc khi sua trang bao 500/khong hien gi, sau khi sua
  hien dung bang trang thai + an dung nut khi chua du dieu kien.

**Con thieu, chan viec bat PXE that**: file `BCD` (can ISO goc, anh Thoai
se tai lai 1 lan nua). **Chua kiem chung duoc** (can phan cung that,
khong gia lap tren Pi): toan bo chuoi boot that tu 1 may PC qua PXE toi
man hinh cai Windows - moi thu o tren moi kiem chung "dung co che, dung
cu phap, dung file", chua "da tan mat thay 1 may boot thanh cong". Chi
tiet day du: docs/ke-hoach-pxe-winpe-tu-dong-cai-windows.md.

selftest.sh: 36 dat, 4 luu y (1 luu y moi ve get_throttled - da xac nhan
khong lien quan, do CPU chay 100% luc nen 15GB du lieu tach WIM truoc do).

## 0.4.47

**Thanh tien trinh khi tai file len + bo duoc 2 lan chep thua** (anh Thoai
bao: "task manager het bao dung luong ben tab network ma trang os van quay
hoai luon, ko biet no toi dau").

**Loi that da gap (chinh anh Thoai gap, 2 loi lien quan nhau):**

1. Tai 1 file 4.6GB mat ~20 phut, xong xuoi thi bi TU CHOI voi thong bao
   "can khoang 10.1 GB trong nhung chi con 10 GB" - thieu dung 0.1GB, va
   phep kiem tra do lai nam o CUOI, sau khi da nhan het file. Cong toi
   cua canh bao dung luong them o ban 0.4.46: no doi GAP DOI dung luong.
2. Suot qua trinh do man hinh chi quay vong tron, khong biet dang toi dau,
   con bao lau. Nhat la doan SAU KHI trinh duyet da gui xong ma may van con
   dang lam viec - nhin y het bi treo.

**Nguyen nhan goc (do that, khong doan)**: moi file tai len phai di qua BA
lan chep tren the nho: (1) nginx nhan tu trinh duyet, dem ra
/var/lib/nginx/body; (2) nginx day sang Flask, Werkzeug ghi ra file tam;
(3) ma cua minh chep tu file tam sang cho luu that. The nho Pi chi ghi
~13 MB/s (da do), nen file 5GB ton ~19 phut chi de chep di chep lai, va
HAI giai doan cuoi xay ra sau khi trinh duyet da gui xong.

**Sua tan goc - du lieu chay THANG mot mach:**
- nginx: `proxy_request_buffering off` cho cac duong tai len (bo lan chep 1)
- Flask: chan tang Werkzeug (`_get_file_stream`) de ghi THANG vao file dich
  duoi dang `<ten>.part`, xong doi ten (bo lan chep 2 va 3)
- Phep kiem tra dung luong chuyen len `before_request` - tu choi NGAY o
  giay dau khi vua nhan header, va chi con doi DUNG BANG kich thuoc file
  (+1GB tho) thay vi gap doi

**Thanh tien trinh that**: hien %, so MB da gui / tong, toc do, thoi gian
con lai, VA so byte da thuc su ghi xuong dia (hoi may qua
`/deployos/tien-do`, khong doan). Co nut Huy tai len. Neu trinh duyet khong
chay JavaScript thi form thuong van gui duoc nhu cu.

**Da kiem chung that tren may:**
- Tai 1 file 3GB qua dung duong nginx: HTTP 200, 245 giay, 12.8 MB/s
- **He so khuech dai dung luong = 1.00 lan** (dinh diem dia tang dung 3000MB
  cho file 3000MB) - truoc khi sua la ~3 lan. Do bang cach theo doi song
  song "dia tang bao nhieu" va "file dich lon bao nhieu": hai so bam sat
  nhau tung giay, chung to khong con ban sao thua nao
- Thanh tien trinh chay that tren man hinh cam ung: "96% - 673.2 MB /
  700.0 MB - 30.6 MB/s - con 1 giay" kem dong "Da ghi xuong dia: 660.2 MB /
  700.0 MB"
- Bo kiem thu rieng cho co che tai len moi: 24 phep thu, dat het (ghi thang
  ra dia dich, khong de lai file tam, tu choi duoi file la ma khong tao
  file nao, trung ten thi doi ten chu khong ghi de, endpoint tien do, chan
  duong dan la, tu choi som khi thieu cho, don file .part bo do nhung giu
  lai cai dang tai)
- selftest.sh: 37 dat, 3 luu y, 0 loi

**Don dep**: xoa kho goi apt cu (thu hoi 500MB). Da kiem tra the nho: 29.72
GB va DA duoc mo rong het co tu truoc (con trong chua chia: 0.01 GB) -
khong con gi de mo rong them.

## 0.4.46

**Sua loi khong tai len duoc file lon hon ~1.9GB** (phat hien khi chuan bi
cho anh Thoai tai bo cai Windows ~5-6GB len qua tab Deployment OS).

**Kiem chung that, khong doan**: tai thu 1 file 2.2GB thi nhan **HTTP 500**
sau khi da gui xong 2.3GB (mat hon 2 phut roi moi bao hong). Vua theo doi
vua thay `/tmp` phinh dan trong luc tai: 35M -> 451M -> 563M -> ... cho toi
khi cham tran.

**Nguyen nhan**: Werkzeug (tang duoi Flask) doc file tai len bang
`SpooledTemporaryFile` - moi file lon hon 500KB deu bi do ra file tam trong
thu muc tam cua Python, mac dinh la `/tmp`. Tren Pi OS `/tmp` la **tmpfs -
nam trong RAM**, chi 1.9GB. Nen file nao lon hon muc do deu chet, va con an
het RAM cua may trong luc do.

Diem dang chu y: tab **Kho file** (`ui/storage.py`) dinh y het loi nay tu
truoc du no da rat can than ghi theo luong ra dia - vi cho nghen nam o tang
Werkzeug PHIA TRUOC, truoc khi ma cua minh duoc chay. Ban sua nay chua luon
cho ca tab do (cung 1 tien trinh).

**Sua**: doi thu muc tam cua ca tien trinh dashboard sang `/var/tmp` (nam
tren the nho, con 20GB) ngay trong `app.py`. Mot cho sua, chua cho moi tab
co tai file len, ke ca tab lam sau nay.

**Them canh bao dung luong thong minh hon** cho tab Deployment OS: file tai
len can GAP DOI dung luong (file tam + ban luu that ton tai cung luc), nen
gio kiem tra truoc theo dung kich thuoc file va bao ro can bao nhieu GB -
thay vi de tai nua chung hang chuc phut roi moi bao het cho.

**Da kiem chung lai bang dung phep thu da lam hong**: cung file 2.2GB do,
truoc khi sua log ghi `POST /deployos/console/file/len 500`, sau khi sua ghi
`POST /deployos/console/file/len 200`, file nam that tren dia, va `/tmp`
dung yen o 32M suot ca qua trinh (khong con an vao RAM).

## 0.4.45

**Tab moi "Deployment OS"** - trien khai he dieu hanh qua mang cho may can
cai lai (theo ke hoach o `docs/ke-hoach-pxe-winpe-tu-dong-cai-windows.md`).

Cau truc dung nhu anh Thoai yeu cau:

- **1. Boot OS**
  - **1.1 Tu lua chon**: trinh tu 7 buoc, moi buoc deu co nut *Tiep theo* va
    *Quay lai* (quay lui khong mat lua chon da dien):
    1. Kieu boot (truc tiep voi client / qua mang khong DHCP / qua mang co
       DHCP - moi kieu deu ghi ro khi nao dung)
    2. Chon OS (Windows 10/11, Ubuntu/Debian) + chon file boot da tai len
    3. Thong tin OS (ten may, username, mat khau, mui gio; o **SSH chi hien
       khi chon Linux**)
    4. Phan chia o dia: tu dong (o so 0) hoac chia tay - bang phan vung sua
       truc tiep, tu doi bo phan vung mac dinh theo OS (Windows GPT: EFI +
       MSR + NTFS; Linux: EFI + swap + ext4), them/bot phan vung duoc
    5. Phan mem (chon tu cac file da tai len o 2.2)
    6. Chinh sua cai dat (chon script da tai len o 2.3 + o nhap lenh them)
    7. Tong ket + **bang kiem tra san sang doc trang thai THAT** cua may
  - **1.2 Kich ban**: chon 1 kich ban da tao san (tu 2.4) la co ngay toan bo
    lua chon, khong phai chon lai tu dau
- **2. Console boot**
  - **2.1 File boot**: tai len .iso/.wim/.esd/.img/.vhd + bootloader iPXE
  - **2.2 Phan mem**: tai len .msi/.exe, moi file dien duoc **tham so cai
    im lang** rieng (vd `teamviewer.exe /S`) - vi moi hang mot kieu, khong
    doan gium duoc
  - **2.3 Script**: tai len .bat / .ps1 / .cmd
  - **2.4 Kich ban**: chay dung trinh tu 7 buoc nhu 1.1 nhung buoc cuoi la
    dat ten de luu lai

**Trung thuc ve trang thai**: phan phuc vu boot that su (dnsmasq PXE, iPXE,
WinPE) la giai doan ke tiep, CHUA dung. Vi vay buoc 7 khong "gia vo" boot -
no doc trang thai that tren may (co file boot chua, co iPXE chua, dnsmasq da
cau hinh PXE chua, co anh WinPE chua khi cai Windows) va noi ro con thieu
gi, dung nguyen tac cua du an.

**An toan**:
- File .exe/.msi/.bat/.ps1/.cmd chi duoc LUU va PHUC VU cho may dich tai ve,
  khong co duong nao chay chung tren chinh con Pi.
- Kich ban co the chua mat khau cua tai khoan se tao tren may dich, nen thu
  muc kich ban de quyen 700 va tung file 600 (tao bang `os.open` voi quyen
  600 ngay tu dau - khong de co khe thoi gian nao file nam do voi quyen rong
  hon).
- O mat khau khong dien san gia tri cu ra HTML (dien san thi mat khau nam
  thang trong ma nguon trang) nhung van giu duoc mat khau khi quay lui/tien
  toi giua cac buoc.
- Moi duong tai ve/xoa deu kiem tra duong dan that (`os.path.realpath`) de
  chan vuot thu muc.

**Da kiem chung that** bang bo kiem thu di het tung buoc nhu nguoi dung
(65 phep thu, dat het): mo tung trang, tai len/xoa/tai ve tung loai file, tu
choi dung duoi file la (.sh), luu tham so cai im lang, di het 7 buoc ca 2
che do, quay lui giu nguyen lua chon, o SSH chi hien voi Linux, bo phan vung
tu doi theo OS, luu/nap/xoa kich ban, quyen file 600/thu muc 700, mat khau
khong lot ra ma nguon, va chan duong dan vuot thu muc.

## 0.4.44

**Sua nguyen nhan THAT SU khien thanh tien trinh kiosk dung im o 90% rat
lau** (anh Thoai bao lai sau ban 0.4.43: "van chua bam sat"). Da kiem
chung that qua journalctl 1 lan khoi dong that (khong doan):

- Flask (dashboard) that su san sang chi sau **~2 giay** ke tu luc
  systemd khoi dong service (ghi mo lai "Running on http://127.0.0.1:5000"
  trong log rat som).
- Nhung request `/healthz` DAU TIEN (tu trang cho kiosk) chi toi noi sau
  **hon 2 PHUT** ke tu luc do.

Nguyen nhan: goi `nginx` mac dinh cua Debian co san
`After=network-online.target ...` va `Wants=network-online.target`, bat
nginx PHAI DOI toi khi `systemd-networkd-wait-online.service` xong (hoac
HET GIO CHO - da xac nhan qua journalctl dong chu "Timeout occurred while
waiting for network connectivity", ~2 phut) moi chiu khoi dong. Trong
suot 2 phut do, ca cong 80 va cong 8880 (kiosk goi vao) CHUA CO AI LANG
NGHE CA - moi request cua trang cho deu bi tu choi ket noi va tu dong thu
lai, thanh tien trinh dung im o % that cuoi cung da ghi truoc do (khong
phai bi treo that, chi la khong ai bao cho no biet ly do that).

nginx cua Console Pi chi lang nghe `0.0.0.0:80` va `127.0.0.1:8880` -
CA HAI kieu bind nay deu khong can bat ky interface mang nao that su co
IP truoc de bat dau chay. Doi network-online.target la thua, chi lam
cham vo ich dung luc thiet bi can dung nhat (moi bat may len).

**Sua**: ghi de `systemd/nginx.service` (toan bo file, khong phai
drop-in bo sung - xem ghi chu chi tiet trong chinh file do ve viec da
thu drop-in truoc va PHAT HIEN drop-in KHONG the xoa duoc `Wants=`/
`After=` da co san tren systemd, chi cong don them chu khong thay the -
kiem chung bang 3 phep thu doc lap tren cac unit rieng truoc khi ket
luan, khong doan). nginx gio chi con `After=network.target
remote-fs.target nss-lookup.target` (thu tu, khong phai cho ket noi
that), khoi dong ngay tu som cung luc voi `console-pi-dashboard.service`.

Da kiem chung lai: `systemctl show nginx -p After -p Wants` xac nhan
khong con `network-online.target`; `nginx -t` hop le; nginx restart
xong van tra dung 302 (cong 80, chua dang nhap) va 200 (cong 8880,
`/healthz`); `selftest.sh` van 37 dat/3 luu y nhu truoc, khong hong gi
them.

## 0.4.43

**Sua loi nghiem trong vua tim ra khi tu tay test 0.4.42**: man hinh cho
kiosk co the CHUYEN TRANG SOM khi nginx da chay nhung Flask (backend that
su) CHUA XONG - dung y het trieu chung goc ("hien trang khong ket noi
duoc") ma toan bo tinh nang nay duoc lam ra de sua.

**Nguyen nhan that (da tu tay mo phong: tat Flask, giu nginx song, xac
nhan nginx tra ve 502 - khong doan)**: `kiosk-loading.html` dung
`fetch(DASH_URL, {mode:"no-cors"})` de kiem tra dashboard san sang. Che do
"no-cors" tra ve response "opaque" - khong doc duoc ma trang thai that su.
Ket qua: `fetch()` van `resolve()` BINH THUONG ke ca khi nhan duoc **502**
(nginx song, Flask chet) y het luc thanh cong that (200) - trang cho
chuyen sang dashboard som, van thay dung trang loi ma tinh nang nay duoc
lam ra de tranh.

**Da sua**: them CORS rieng cho route `/healthz` (`ui/auth.py`) de trang
cho doc duoc bang `fetch()` CHE DO THUONG (khong phai no-cors) va kiem tra
dung `response.ok` - phan biet dung 200 that su voi 502/503. Da kiem
chung lai bang chinh kich ban that bai da tim ra: tat Flask giu nginx
song, xac nhan trang cho **KHONG con chuyen trang som nua**; bat Flask lai
thi tu chuyen dung ngay khi that su san sang (200).

## 0.4.42

**Thanh tien trinh kiosk bam sat he thong THAT, khong con doan theo thoi
gian** (`app.py`, `scripts/kiosk-loading.html`, `scripts/kiosk-start.sh`) -
phan hoi truc tiep: thanh tien trinh 0.4.41 chay den 92% roi dung, bao "mat
nhieu thoi gian hon binh thuong" du dashboard van dang nap binh thuong -
vi ban dau CHI doan % theo thoi gian troi qua, khong biet gi ve viec Flask
that su dang lam gi.

- `app.py` gio ghi **tien do THAT** ra `/run/console-pi-boot-status.json`
  tai tung moc that su trong luc nap: nap khung giao dien (10%) -> nap cac
  cong cu chan doan mang/scapy+cryptography+netmiko (25%, cham nhat) ->
  nap giao dien cac tab (70%) -> khoi dong may chu web (90%). Trang cho tu
  do biet CHINH XAC dang ket o buoc nao, khong con doan.
- `kiosk-loading.html` doc file nay moi 0.8 giay, dung % VA thong diep
  THAT khi co; chi doan theo thoi gian trong vai giay dau (truoc khi
  app.py kip ghi moc dau tien), va gioi han uoc luong o 30% de khong lan
  voi % that. Canh bao "cham hon binh thuong" gio thong minh hon: bao khi
  % THAT khong doi qua 25 giay (thuc su ket o 1 buoc) HOAC qua 75 giay
  tinh chung (an toan cuoi cung), thay vi 1 moc thoi gian co dinh.
- **Loi ky thuat rieng da gap va sua khi lam phan nay**: trang `file://`
  mac dinh KHONG the `fetch()` mot file cuc bo khac (ke ca cung thu muc) -
  da kiem chung that (`TypeError: Failed to fetch`). Them co
  `--allow-file-access-from-files` cho Chromium - da kiem chung lai bang 1
  tien trinh Chromium rieng, fetch file-to-file thanh cong sau khi them
  co. Co nay chi noi long quyen cho trang file:// (duy nhat
  kiosk-loading.html), khong anh huong gi toi http/https.

## 0.4.41

**Man hinh cho co thanh tien trinh luc khoi dong kiosk** (`scripts/kiosk-loading.html`,
`scripts/kiosk-start.sh`) - phan hoi truc tiep: moi lan bat/khoi dong lai
may deu thay trang "127.0.0.1 khong ket noi duoc", phai doi roi tu bam
Reload.

- **Nguyen nhan that**: truoc day script cho Chromium DUNG YEN trong shell
  (vong lap `curl` toi da 60 giay) roi moi mo trinh duyet vao dung
  dashboard. Nhung luc moi khoi dong dia rat ban (hang chuc dich vu cung
  chay, Flask phai nap scapy/cryptography/netmiko/tat ca module nettools),
  doi khi CAN HON 60 GIAY - Chromium da mo va bao loi tu truoc khi Flask
  kip xong. Suot luc cho, man hinh khong co gi bao hieu dang chay hay da
  treo.
- **Da doi cach**: bo han vong lap cho trong shell. Chromium mo NGAY 1
  trang tinh `kiosk-loading.html` (file cuc bo, luon mo duoc ngay lap tuc,
  khong phu thuoc Flask/nginx da chay hay chua) co logo, thanh tien trinh
  % (tang dan theo thoi gian, uoc luong hinh dung chu khong phai % that
  su), va tu kiem tra dashboard bang `fetch()` moi giay. Ngay khi dashboard
  tra loi, tu nhay len 100% va CHUYEN THANG sang dashboard that - khong
  bao gio con thay trang loi nua. Qua 45 giay van chua xong thi hien them
  canh bao + nut "Tai lai trang nay" phong khi that su co su co.
- **Da kiem chung that** (khong doan): dung CDP dieu khien chinh Chromium
  dang chay tren man hinh de kiem tra ca 2 chieu - `fetch()` tu ngu canh
  `file://` sang `http://127.0.0.1:8880` chay duoc, khong bi Chromium chan
  vi ly do bao mat khac-nguon; va thanh tien trinh tang dan dung khi tro
  toi 1 cong khong ton tai (mo phong dashboard chua san sang).

## 0.4.40

**Gia MAC WiFi** (`ui/network.py`, `scripts/wifi-fallback.sh`) - giai
quyet dut diem su co tab 0.4.39: WiFi khach cong ty tu choi ket noi vi
nhan ra MAC thuoc hang Raspberry Pi Foundation (khong phai sai mat khau).

- Tab **WiFi** them khoi "Gia MAC WiFi": bam Bat la doi sang 1 MAC gia CO
  DINH (kieu "locally administered", sinh ngau nhien 1 lan roi dung lai
  moi lan - tranh mang danh gia "hang loat thiet bi la" neu MAC doi lien
  tuc), bam Tat la tra ve MAC that NGAY LAP TUC (doc truc tiep tu EEPROM
  qua `ethtool -P`, khong can tu luu MAC goc o dau ca).
- `wifi-fallback.sh` tu ap dung MAC gia (neu da bat) truoc khi thu ket noi
  WiFi da luu - co hieu luc cho ca lan ket noi dau tien tai diem den moi.
- **Da kiem chung THAT truoc khi lam** (khong doan): doi MAC bang tay tren
  chinh may, goi `networkctl reconfigure` (dung lenh fallback script goi
  moi 2 phut) va cho carrier len/xuong - xac nhan MAC KHONG bi he thong tu
  tra ve MAC goc du co san `MACAddressPolicy=persistent` trong cau hinh
  systemd mac dinh (chinh sach nay chi ap dung luc udev tao interface, khong
  can thiep sau khi da doi MAC bang tay). WiFi tu noi lai binh thuong sau
  khi doi di doi lai.
- Nhac ro tren giao dien: nen **tat lai khi ve nha** neu router nha co dat
  rieng dia chi IP theo MAC that.
- Cap nhat tai lieu muc WiFi giai thich day du su co that + cach dung.

## 0.4.39

**Sua loi that: 2 lan chay wifi-fallback.sh chong lan nhau, lam log bao SAI
"da co IP"** - phat hien khi doc `journalctl` giup anh Thoai luc dem may len
cong ty khong vao duoc WiFi.

Bang chung that trong log: dung luc mot lan chay dang trong vong lap CHO
ket noi WiFi cong ty ("PHS-HO-GUEST"), `wpa_supplicant` bi giet bang
SIGKILL va `hostapd` tu bat len GIUA CHUNG - chi co the la do MOT LAN CHAY
KHAC (do `wifi-fallback.timer` kich hoat moi 2 phut) goi
`ngung_supplicant()`/`bat_ap()` cung luc, vi script goc KHONG CO KHOA nao
ca. Hau qua: lan chay dang cho doc nham dia chi cua chinh vo AP
(`192.168.50.1`, vua duoc `hostapd`/`dnsmasq` gan) tuong la da xin duoc IP
tu WiFi cong ty that, ghi log "Da co IP" HOAN TOAN SAI - trong khi that ra
`wpa_supplicant` chua bao gio ket noi duoc (lien tuc bi tu choi ngay o
buoc lien ket, `CTRL-EVENT-ASSOC-REJECT`, chua tung toi buoc kiem tra mat
khau).

**Da sua**: them `flock` o dau `scripts/wifi-fallback.sh` - neu dang co 1
lan chay khac, THOAT NGAY thay vi chay chong len. Da kiem chung that bang
cach gia lap 2 tien trinh khoi dong cach nhau 1 giay: tien trinh sau tu
nhan ra co khoa va thoat ngay, khong dam vao tien trinh truoc.

**Van con dang dieu tra rieng**: tai sao AP cua cong ty tu choi lien ket
ngay tu buoc dau (khong phai loi sai mat khau - do la mot loai that bai
KHAC, xay ra SOM HON trong qua trinh ket noi). Nghi ngo nhieu nhat la
mang "PHS-HO-GUEST" can dang nhap qua trang web (captive portal) hoac
dang ky MAC truoc voi IT cong ty, hoac dung kieu xac thuc WPA2-Enterprise
(can tai khoan rieng, khong phai 1 mat khau WiFi don gian) - ca hai kieu
nay Console Pi hien CHUA ho tro duoc tu dong. Chua ket luan chac chan,
dang cho them thong tin tu anh Thoai.

## 0.4.38

**Tailscale: hien domain that + nut doi Auth key** (`ui/remote.py`) - phan
hoi truc tiep sau khi anh Thoai ket noi Tailscale thanh cong lan dau.

- Khi da ket noi, khoi Tailscale gio hien **ten mien MagicDNS that**
  (vd `console-pi.tail3d2316.ts.net`) kem link bam vao duoc, giong cach
  khoi Cloudflare da lam - khong can mo Tailscale admin console de tim
  dia chi nua. Lay tu `Self.DNSName` trong `tailscale status --json` -
  da kiem chung that tren chinh may (tailscale da duoc cai va ket noi that
  trong luc lam tinh nang nay).
- Xac nhan va ghi ro trong tai lieu: ten mien VA dia chi IP deu **KHONG
  doi khi khoi dong lai Pi** - ten may (`console-pi`) dat co dinh trong
  code, ten tailnet (`tail3d2316.ts.net`) gan co dinh voi tai khoan, dich
  vu `tailscaled` da duoc bat tu dong luc khoi dong (`systemctl enable`)
  nen tu noi lai dung danh tinh cu.
- **Sua 1 lo hong giao dien**: truoc day khi da luu Auth key thi KHONG co
  cach nao doi sang key khac ma khong bam "Quen thiet bi" truoc (dang xuat
  han, mat ten/dia chi cu). Them khoi an "Authkey het han / muon doi sang
  key khac?" - dan key moi vao la doi ngay, giu nguyen danh tinh thiet bi.

## 0.4.37

**Them Tailscale lam lua chon truy cap tu xa PHU** (`ui/remote.py`) - theo
yeu cau: "them 1 lua chon nua, no la lua chon phu, mac dinh van la
Cloudflare".

- Khoi Tailscale hien ngay duoi khoi Cloudflare tren tab **Truy cap tu
  xa**, ro rang danh nhan "lua chon phu" - Cloudflare khong doi gi, van la
  mac dinh va hien truoc tien.
- Luong dung: Cai (script chinh thuc cua Tailscale, tu nhan dien dung
  phien ban Debian) &rarr; dan Auth key tu Tailscale admin console &rarr;
  Bat/Tat/Quen thiet bi - cung mau giao dien voi khoi Cloudflare da co.
- Khac biet ro voi Cloudflare (da ghi ro tren giao dien va tai lieu):
  Cloudflare cho ra 1 link web ai co link cung vao duoc qua trinh duyet
  bat ky; Tailscale tao mang rieng ao GIUA CAC THIET BI CUA CHINH NGUOI
  DUNG, may nao muon vao cung phai cai app + dang nhap cung tai khoan
  truoc, doi lai vao duoc ca SSH/dich vu khac cua Pi qua IP rieng trong
  mang do, khong chi gioi han trong trang web.
- Doc trang thai qua `tailscale status --json`, da kiem chung logic phan
  tich JSON voi 4 tinh huong (dang chay, chua dang nhap, da tat, JSON
  hong) - khong bia trang thai khi lenh loi hoac thieu truong.
- Authkey luu quyen 600 tai `/etc/tailscale-console-pi-authkey`, cung muc
  bao mat voi token Cloudflare.
- Cap nhat tai lieu muc "Truy cap tu xa" giai thich ro khi nao dung
  Cloudflare, khi nao dung Tailscale.

## 0.4.36

**Loat yeu cau thuc te tu anh Thoai: TFTP tai duoc file, copy/dan trong
Terminal/SSH, sao luu qua cap console, bo Pin, toi uu tablet.**

**1. TFTP - tai file va copy dong lenh** (`nettools/tftp_server.py`):
- Nut **⬇ Tai ve** cho tung file da nhan (truoc day file nam tren dia
  nhung khong co duong nao tai ve tu giao dien web).
- Nut **📋 Copy** ngay canh 2 dong lenh mau (sao luu / nap firmware) - bam
  la copy nguyen dong, khong phai tu bam giu chon chu.

**2. Copy/dan trong khung Terminal va SSH bang chuot** (`ui/soanlenh.py`):
- Nut **📋 Copy vung da chon**: doc lua chon THAT cua xterm.js
  (`term.getSelection()`) - phai **giu phim Shift trong luc keo chuot boi
  den** vi tmux dang bat che do chuot rieng (`mouse on`, giu de cuon lai
  lich su man hinh) nen che di lua chon thong thuong cua trinh duyet; Shift
  la cach xterm.js quy uoc de "vuot qua" ung dung dang giu chuot - da kiem
  chung that bang cach gia lap ca hai truong hop (co Shift lay duoc chu, khong
  Shift thi khong).
- Nut **📄 Copy ca man hinh**: lay toan bo noi dung dang hien qua
  `term.getSelection()` sau khi tu chon het pane (khong can bam giu Shift).
- **LOI THAT DA TIM RA VA SUA CUNG DIP NAY**: `/api/send-keys` (dung boi
  ban phim ao khi go vao Terminal/SSH/Console) goi ham `send_keys()`
  **CHUA TUNG DUOC DINH NGHIA O DAU CA** trong toan bo ma nguon - moi lan
  bam phim ao deu gay loi 500 (NameError) o server, va vkeyboard.js lai
  nuot loi do bang `.catch(()=>{})` nen khong ai thay bao gi, chi thay "go
  hoai khong an". Loi co san tu truoc, khong phai do thay doi gan day. Da
  them ham `send_keys()` that su vao `ui/terminal.py`. Nhan tien phat hien
  va sua them 1 loi bien: ky tu `;` bi chinh tmux hieu nham thanh dau tach
  nhieu lenh (ke ca voi co `-l`), phai thoat thanh `\;` moi gui dung - da
  test toan bo 68 ky tu tren ban phim ao, khong con ky tu nao loi.

**3. Tab moi: Sao luu cau hinh qua cap console** (`nettools/console_backup.py`):
  dung khi thiet bi **mat IP quan ly**, chi con cam duoc day console (TFTP
  luc do vo dung vi can duong mang). Bao thiet bi in `show running-config`
  ra man hinh roi hung lai thanh file, giong bat "session logging" trong
  PuTTY nhung tu dong. Them nut **🔌 Sao luu cau hinh** ngay tren trang
  Console dang mo (theo de nghi cua anh Thoai, thay vi 1 trang tach roi).
  - **LOI THAT DA GAP LUC TEST VOI SWITCH THAT** (anh Thoai gui anh chup man
    hinh): thiet bi con o che do nguoi dung (dau nhac `Switch>`, CHUA go
    `enable`) nen `show running-config` bi tu choi - da them buoc kiem tra
    dau nhac HIEN TAI truoc khi go bat ky lenh nao, bao ro va dung lai neu
    thieu quyen thay vi cu go roi luu ca thong bao loi vao file.
  - Nhan tien sua them 1 loi: `tmux clear-history` (dung o phien ban dau)
    chi xoa BO DEM CUON, KHONG xoa noi dung DANG HIEN TREN MAN HINH - dan
    toi chu cua buoc go lenh truoc bi lan/lap voi ket qua that. Doi sang
    tim dung vi tri SAU lan go lenh cuoi cung, khong phu thuoc viec xoa
    man hinh.

**4. Bo tinh nang "Pin"** (`ui/health.py`, `ui/settings.py`, `ui/api.py`):
  may nay xac nhan chac chan khong co phan cung pin nao doc duoc (da kiem
  chung tu truoc: `i2cdetect` bao nhieu chu khong phai chip that, khong co
  HAT/UPS nao) - de lai muc "Doc pin qua I2C" chi gay roi, da bo hoan toan
  khoi Tong quan va Cai dat.

**5. Toi uu giao dien cho tablet** (`ui/layout.py`):
  menu ben trai dinh vi tri khi cuon trang (sticky), tang kich thuoc vung
  bam cho nut/muc menu, bang du lieu rong tu cuon ngang trong khung rieng
  thay vi day lech ca trang.

**6. Ban phim ao qua lon, che mat man hinh Console** (`nettools/static/vkeyboard.js`):
  da do that bang `wlr-randr` (man RasPad 1280x800, khong doan) va do truc
  tiep tren dich vu that: kich thuoc cu chiem toi ~50% chieu cao man hinh,
  tren trang Console (da bi thu hep san danh cho ban phim) thi cam giac
  "che het". Giam clamp() cho chieu cao/chu tu (40-58px/16-21px) xuong con
  (30-40px/12-16px) - do lai sau khi sua con ~35% man hinh (280px/800px).

## 0.4.35

**Doi tab "YouTube" thanh "Giai tri", them TikTok, bo cach dan link/tim
kiem** - don gian hoa theo yeu cau thuc te sau khi luoi an toan (nut Home
+ ban phim ao tiem qua CDP) da chung minh hoat dong tin cay: khong con can
cach "dan link/nhung iframe" du phong nua.

- Doi ten `src/ui/youtube.py` -> `src/ui/entertainment.py`, route
  `/youtube` -> `/giaitri`, nhan tab thanh "Giai tri".
- Bo hoan toan khung "Phat video theo duong dan" (dan link roi nhung
  iframe) va "Tim kiem nhanh, xem ngay trong trang" (embed
  `listType=search` khong chinh thuc) - chi con 2 nut dieu huong that:
  **🌐 Mo YouTube** va **🎵 Mo TikTok**, ca hai deu duoc luoi an toan cua
  `console-pi-kiosk-helper` bao ve nhu nhau (nut Home + ban phim ao tiem
  qua CDP hoat dong tren BAT KY trang nao, khong rieng gi YouTube).
- Cap nhat tai lieu: muc "📺 Tab YouTube" -> "📺 Tab Giai tri (YouTube,
  TikTok)", gop lai gon hon, bo cac doan noi ve tinh nang da xoa.

## 0.4.34

**Doi nut "🏠 Console Pi" ve goc duoi ben trai** (`scripts/kiosk-helper.py`)
- phan hoi truc tiep: dat o goc tren che mat thanh cong cu/logo cua nhieu
  trang (vd YouTube). Da kiem chung lai tren chinh youtube.com that: nut
  gio nam o day man hinh, khong con chan noi dung phia tren.

**Dang dieu tra: khong nghe duoc am thanh** - da phat hien mot huong moi:
man hinh RasPad chi co DUY NHAT cong HDMI0 dang cam that
(`/sys/class/drm/card1-HDMI-A-1/status` = connected, HDMI-A-2 =
disconnected) - neu loa gan trong vo RasPad nhan am thanh qua chinh cap
HDMI nay (kieu man hinh HDMI tich hop loa, kha bien voi thiet ke RasPad)
thay vi giac 3.5mm nhu gia dinh ban dau, thi phai chinh ngo ra am thanh
mac dinh sang HDMI moi nghe duoc. Da thu doi ngo ra mac dinh sang HDMI
(`wpctl set-default`) va dang cho anh Thoai xac nhan co nghe duoc video
YouTube khong - CHUA ket luan, chua sua vinh vien vao code cho den khi co
xac nhan that.

## 0.4.33

**Sua loi that: ban phim ao khong hien tren chinh trang YouTube** - phan
hoi truc tiep sau 0.4.32 ("em làm sao thì không có âm thanh và không có
bàn phím bấm").

Da dieu tra that tren chinh youtube.com that (khong doan, dung CDP de bat
loi runtime): `renderKb()` trong `scripts/kiosk-helper.py` dung
`kb.innerHTML = ""` de xoa ban phim cu truoc khi ve lai. YouTube ep chinh
sach bao mat **Trusted Types** (CSP `require-trusted-types-for 'script'`)
- chinh sach nay CHAN TUYET DOI moi phep gan `.innerHTML` bang chuoi
thuong (ke ca chuoi rong), nem `TypeError` ngay lap tuc. Loi nay xay ra
NGAY BEN TRONG ham xu ly su kien focus, nen khong bao gio lot ra ngoai de
thay - ban phim am tham khong bao gio kip hien len
(`kb.classList.add("on")` nam ngay sau doan bi loi). Da sua bang cach doi
sang xoa tung phan tu con bang `removeChild` trong vong lap - la DOM API
an toan, khong bi Trusted Types dong toi.

Da kiem chung lai toan bo tren chinh trang youtube.com that (khong phai
trang test cuc bo): bam o tim kiem -> ban phim hien len dung, go "lofi" ->
gia tri o tim kiem dung "lofi", bam xoa -> con "lof". Hoat dong hoan toan
binh thuong.

(Van con dang dieu tra rieng van de am thanh khong nghe duoc - phan mem/
ALSA/PipeWire da xac nhan hoat dong dung toi tan phan cung, dang cho kiem
tra day cap loa vat ly ben trong vo RasPad.)

## 0.4.32

**Ban phim ao GIO DA hien duoc tren chinh trang YouTube that** (o tim
kiem/binh luan/chat) - phan hoi truc tiep: "em thật sự ko thể bật bàn
phím ảo trên trang youtube hả". Ket luan truoc ("khong lam duoc, phai
dung ban phim that/USB/Bluetooth") CHUA DUNG - da sua.

- Doi ten `scripts/kiosk-homebtn.py` -> `scripts/kiosk-helper.py` (va
  service tuong ung `console-pi-kiosk-homebtn` -> `console-pi-kiosk-helper`)
  vi gio lam nhieu hon la chi mot nut Home.
- Them ban phim ao dang HTML/JS thuan (khong phai ban phim ao he thong)
  duoc TIEM qua cung co che CDP dang dung cho nut "Ve Dashboard" - chay
  ben trong chinh trang dang mo nen KHONG can giao thuc layer-shell hay
  quyen he thong nao (khac voi wvkbd/squeekboard da thu va that bai truoc
  do). Ho tro `<input>`, `<textarea>`, va phan tu `contenteditable`
  (dung cho khung binh luan/chat), dung "native value setter" de tuong
  thich voi trang dung framework kieu React.
- Da kiem chung that (khong doan): tiem vao 1 trang test co du 3 loai o
  nhap tren, mo phong dung kieu du lieu cua o tim kiem/binh luan/chat that,
  go chu/xoa/Enter deu hoat dong dung va cac trang do nhan dung su kien
  `input`/`keydown`.
- Chuyen nut "🏠 Console Pi" tu goc duoi len goc tren ben trai man hinh de
  khong de chong len ban phim ao moi hien o duoi man hinh.
- Cap nhat tai lieu va `ui/youtube.py` ghi ro gioi han that con lai (chi
  kiem chung 3 loai o nhap chuan, o nhap dac biet phuc tap hon chua kiem
  chung tung truong hop).

## 0.4.31

**Dua tro lai nut "Mo YouTube" dieu huong that, lan nay voi duong ve dang
tin cay thuc su** - phan hoi truc tiep sau 0.4.30 ("cầm cái này như tablet
lam sao ma dan link, anh can vao youtube nhan vo la vo do luon").

- Nut "🌐 Mo YouTube" quay tro lai, dieu huong thang sang youtube.com that
  (duyet/tim kiem/dang nhap tai khoan binh thuong).
- **Giai phap moi cho duong ve** (thay cho vuot canh man hinh da that bai o
  0.4.29/0.4.30): mot tien trinh nen moi
  (`scripts/kiosk-homebtn.py`, service `console-pi-kiosk-homebtn`) dieu
  khien Chromium tu ben ngoai qua giao thuc DevTools cua chinh no
  (`--remote-debugging-port=9222` trong `kiosk-start.sh` - CHI nghe tren
  127.0.0.1, da xac nhan bang `ss -tlnp` khong lo ra mang ngoai) de TIEM 1
  nut noi "🏠 Console Pi" vao MOI trang duoc tai, bat ke la trang nao. Bam
  vao la ve thang dashboard ngay - khong phu thuoc cu chi cam ung nao nua.
- Da kiem chung THAT (khong doan): dieu huong qua nhieu trang cuc bo khac
  nhau va xac nhan nut van xuat hien moi lan; tat kiosk roi bat lai
  (mo phong Chromium crash/restart) va xac nhan tien trinh nen tu phat
  hien Chromium moi, ket noi lai, dang ky lai thanh cong.
- Nut nay tu an tren chinh cac trang cua Console Pi (da co thanh dieu
  huong rieng, thua nut nay).
- Them `python3-websocket` vao goi cai dat va service moi vao
  `install.sh`/`uninstall.sh` de lan cai moi/go cai deu day du.

## 0.4.30

**Su co that: nguoi dung bi ket cung tren mot website khac, phai remote vao
cuu man hinh.** Sau khi bam nut "Mo YouTube" (them o 0.4.28) va bam tiep 1
lien ket ben trong YouTube, bi dua sang datbike.vn - vuot canh man hinh de
"quay ve dashboard" (giai phap da lam o 0.4.28) KHONG hoat dong, phai chay
`systemctl restart console-pi-kiosk` tu xa moi cuu duoc.

- **Da bo hoan toan nut "Mo YouTube" dieu huong thang** va tat lai
  `--overscroll-history-navigation` ve `0` (mac dinh goc,
  `scripts/kiosk-start.sh`). Nguyen nhan that: co che vuot canh cua
  Chromium chu yeu lam cho touchpad/chuot tren Windows/macOS, tren Linux
  voi man hinh cam ung thuan KHONG duoc trien khai day du/dang tin cay -
  bat flag khong dam bao cu chi chay duoc. Video YouTube gio CHI phat qua
  iframe nhung ngay trong dashboard (nhu ban 0.4.27), khong bao gio dieu
  huong roi trang nua nen khong con nguy co ket cung.
- **Them lop phong thu thu 2**: iframe video gio co `sandbox="allow-scripts
  allow-same-origin allow-presentation"` (KHONG co allow-top-navigation),
  chan tuyet doi kha nang mot video/quang cao ben trong iframe dieu huong
  ca trang dashboard di noi khac - phong truong hop tuong tu xay ra ngay ca
  khi chi con dang nhung (embed).
- Cap nhat lai muc tai lieu "📺 Tab YouTube" ghi ro su co that va ly do doi
  huong.

**Bat am thanh cho video** - may nay truoc gio khong co server am thanh
nao chay (chi co thu vien `libpulse0`, khong co tien trinh phuc vu that)
nen Chromium phat video khong ra tieng. Da cai va bat
`pipewire` + `pipewire-pulse` + `wireplumber` chay theo phien dang nhap
cua nguoi dung kiosk - tu dong khoi dong lai moi lan may boot (cac unit
duoc goi tu dong bat trong `default.target`/`sockets.target` cua chinh goi
cai dat, khong can cau hinh gi them). Ngo ra mac dinh: Built-in Audio
Stereo (giac 3.5mm/loa gan trong cua module Pi, am luong dat 85%) - da
kiem tra that bang `speaker-test` va `pw-play`.

## 0.4.29

**Dieu tra that: vi sao ban phim ao khong hien khi go vao trang YouTube
that** (phan hoi tu anh Thoai sau khi dung nut "Mo YouTube" cua 0.4.28).

- Da kiem chung THAT (khong doan): cai thu 2 ban phim ao he thong pho bien
  cho Linux/kiosk (`wvkbd`, `squeekboard`) va chay thu ngay tren phien man
  hinh kiosk dang song - ca hai deu bao loi ngay "khong co layer shell"
  roi thoat. Nguyen nhan: bo dieu phoi man hinh dung cho kiosk (`cage`) la
  loai toi gian, chi chay dung 1 ung dung toan man hinh, KHONG cai giao
  thuc "wlr-layer-shell" ma moi ban phim ao Wayland tieu chuan can de hien
  de len tren ung dung dang chay - xac nhan bang
  `strings $(which cage) | grep layer_shell` khong ra ket qua. Day la gioi
  han that cua kien truc kiosk dang dung, khong phai loi cua tab YouTube.
  Da go sach 2 goi thu nghiem ngay sau khi kiem tra xong.
- Doi sang compositor khac co ho tro (vd `labwc`/`sway`) co the giai quyet
  duoc ve mat ky thuat, nhung anh huong toi ca co che khoa kiosk hien tai
  (`cage` co chu dich chi cho chay 1 ung dung) - KHONG tu y doi, can dong y
  ro rang truoc vi day la thay doi lon.
- **Giai phap thuc te da them** (`src/ui/youtube.py`): o "Tim va mo ket
  qua" ngay trong khung "Mo YouTube" - go tu khoa bang ban phim ao cua
  chinh Console Pi (van hien binh thuong vi la o nhap cua trang minh), bam
  Tim se mo thang trang ket qua that cua YouTube da dien san tu khoa,
  khong can go gi tren trang YouTube nua cho truong hop tim kiem.
- Rieng go binh luan/chat/dang nhap tai khoan tren chinh YouTube van bat
  buoc phai dung ban phim that - da ghi ro tren giao dien va tro toi tab
  Bluetooth (da ho tro san ghep noi ban phim/chuot qua HID).
- Cap nhat muc tai lieu "📺 Tab YouTube" giai thich day du dieu tra tren.

## 0.4.28

**Tab YouTube: mo YouTube THAT thay vi chi dan link** - phan hoi truc tiep
sau ban 0.4.27 ("khong phai dan link ma anh muon em mo youtube luon").

- Nut moi **"🌐 Mo YouTube"** dieu huong thang sang `https://www.youtube.com`
  - duyet/tim kiem/dang nhap tai khoan binh thuong nhu tren dien thoai,
  khong con gioi han trong khung nhung (embed) nua.
- **Thay doi bat buoc di kem** (`scripts/kiosk-start.sh`): bat lai
  `--overscroll-history-navigation=1` cua Chromium (truoc day dang tat). Ly
  do: man hinh cam ung chay kiosk toan man hinh, KHONG CO thanh dia chi hay
  nut Back - neu dieu huong thang sang youtube.com ma khong co duong nao de
  lui lai thi nguoi dung se bi ket cung tren do, phai khoi dong lai kiosk
  moi ve duoc dashboard. Vuot ngon tay tu sat mep trai man hinh sang phai
  (cu chi lui trang chuan cua Chromium) gio la duong quay ve - da ghi ro
  huong dan ngay tren giao dien vi day khong phai thao tac hien nhien.
- Van giu 2 cach cu (dan link phat ngay trong trang, tim kiem nhanh kieu
  khong chinh thuc) cho truong hop chi muon nghe nhac nen ma khong roi
  dashboard - khong xoa tinh nang cu, chi them lua chon moi len dau.
- Da kiem tra that: nhung ca trang youtube.com/m.youtube.com/trang ket qua
  tim kiem vao iframe deu bi chan boi header `X-Frame-Options: SAMEORIGIN`
  (dung `curl -I` xac nhan, khong doan) - day la gioi han tu phia Google,
  khong co cach nao vuot qua ma khong dung reverse proxy phuc tap va de vo
  (video/CDN cua YouTube nam o nhieu ten mien khac nhau), nen khong lam.

## 0.4.27

**Tab YouTube moi** (`src/ui/youtube.py`) - giai tri luc ranh giua gio lam
viec, theo yeu cau thuc te.

- Dan duong link video (chia se tu dien thoai) hoac go tu khoa de tim -
  video duoc phat NGAY TRONG mot iframe cua chinh trang nay.
- **Co tinh: khong dieu huong thang sang youtube.com day du.** Da kiem tra
  that bang `curl -I`: `www.youtube.com` tra ve header
  `X-Frame-Options: SAMEORIGIN` nen khong nhung duoc; con man hinh cam ung
  gan tren Pi chay trinh duyet o che do kiosk toan man hinh - khong co
  thanh dia chi, khong nut Back, ca cu chi vuot lui cung bi tat
  (`--overscroll-history-navigation=0` trong `kiosk-start.sh`). Neu bam
  thang sang youtube.com se bi ket cung tren do khong co duong quay lai.
  Vi vay video luon o dang nhung (`/embed/<id>`, khong bi chan iframe) ngay
  trong khung dashboard, giu nguyen thanh dieu huong de bam sang tab khac
  bat cu luc nao.
- O tim kiem nhanh dung mot kieu nhung khong chinh thuc cua YouTube
  (`listType=search`) - da ghi ro tren giao dien la co the ngung hoat dong
  neu YouTube thay doi, va luon co duong dan link truc tiep lam phuong an
  chac chan hoat dong.
- Them muc tai lieu "📺 Tab YouTube (giai tri)" trong nhom moi "Giai tri".

## 0.4.26

**Nut "Ket noi" ngay tren bang WiFi da luu** (`src/ui/network.py`) - yeu cau
thuc te: dan network di hien truong hay quay lai cac WiFi da dung qua roi,
truoc day muon noi lai phai go lai SSID + mat khau tu dau trong khung "Ket
noi WiFi moi" moi lan, du Pi da luu san.

- Moi WiFi trong bang "WiFi da luu" gio co them cot **Ket noi**: **🟢 xanh**
  va bam duoc ngay neu mang do co trong lan quet WiFi gan nhat (dang trong
  tam song); **⚪ xam** va khoa lai (thuoc tinh `disabled`) neu khong thay -
  tranh bam nham vao mot mang hien khong co that, gay cho vo ich 20-30 giay
  roi Pi tu dong quay lai AP.
- Bam nut xanh se ket noi thang bang mat khau DA LUU tu truoc, khong bat go
  lai. Route moi `/wifi-connect-saved` doc mat khau tu chinh
  `wpa_supplicant-wlan0.conf` (ham moi `load_saved_wifi_with_psk()`), dung
  lai dung mot luong ket noi (`_switch_worker`) voi nut "Ket noi WiFi moi"
  hien co - khong them logic ket noi moi, chi bot buoc go tay.
- Mang dang ket noi hien "● Dang dung" thay vi nut Ket noi (khong can bam
  lai mang minh dang dung). Khi AP dang bi khoa, tat ca nut Ket noi bi khoa
  kem chu thich ly do - **khong tu dong quet WiFi khi dang khoa AP** de
  tranh lam gian doan song ConsolePi dang phat (quet chu dong tren wlan0
  luc no dang la AP co the gay gian doan song trong choc lat).

## 0.4.25

**Dai tu giao dien cho man hinh cam ung RasPad** (khong doi cau truc/logic
cac trang, chi sua CSS/JS/icon dung chung):

- **Sua icon "bi loi"**: ky tu `⏻` (U+23FB, khoi Unicode "Miscellaneous
  Technical") dung cho tab Nguon dien/nut Tat may KHONG nam trong pham vi
  font Noto Color Emoji mac dinh cua Pi OS Lite - hien thanh o vuong trong
  (tofu) tren man hinh cam ung thay vi bieu tuong that. Da doi sang `⚡`
  (nav + link Tong quan) va `🛑` (nut Tat may) - deu thuoc khoi Emoji chuan
  luon co san. Doi luon icon "Lam moi" tren thanh trang thai tu `🔄` sang
  `🔃` de khong con trung voi icon nut "Khoi dong lai" (de gay nham lan
  giua hai thao tac khac hau qua rat khac nhau).
- **Them trang thai Cloudflare Tunnel vao thanh trang thai chung** (`layout.py`),
  ngang hang voi LAN/WiFi/Bluetooth - truoc day phai vao rieng tab Truy cap
  tu xa moi biet duong ham dang bat hay tat.
- **Toi uu cho cam ung toan bo giao dien**: bo do tre 300ms khi cham
  (`touch-action:manipulation`), them hieu ung bam `:active` cho moi
  nut/lien ket (truoc day chi co `:hover` - khong bao gio kich hoat tren
  cam ung nen nguoi dung khong biet vua cham trung hay chua), tang chieu
  cao toi thieu muc menu len 48px va nut nho (`button.small`) tu 36px len
  40px (duoi muc nay ngon tay nguoi lon de bam nham nut ke ben).
- **Sua loi ban phim ao "phai bam giu moi an"** (`vkeyboard.js`): phim
  chuyen so `?123` va phim viet hoa `⇧` tu ve lai TOAN BO ban phim
  (`render()`) ngay trong luc ngon tay con dang cham xuong - xoa mat chinh
  cai nut dang duoc cham giua chung cu chi, khien trinh duyet cam ung hieu
  nham thanh cu chi bi huy va can giu du lau moi tinh la mot lan cham hop
  le. Da sua bang cach doi hanh dong sang chay o `setTimeout(fn, 0)` - de
  cu chi cham hien tai xu ly xong tren DOM con nguyen roi moi ve lai.
- **Ban phim ao tu co gian theo chieu cao man hinh** (dung CSS `clamp()`
  voi don vi `vh` thay vi px co dinh): truoc day cao co dinh 58px chiem qua
  nhieu dien tich tren man hinh nho (RasPad 7"), gio tu thu nho tren man
  thap nhung khong bao gio duoi 40px chieu cao / 16px chu de van bam trung
  duoc bang ngon tay.

## 0.4.24

**Bao dam giu nhat ky it nhat 60 ngay cho TOAN BO he thong** - yeu cau
thuc te: may dung o cong ty khach khong SSH vao duoc luc do, phai doi ve
nha moi xem lai duoc chuyen gi da xay ra. Truoc day khong co gi dam bao
thoi gian giu lai ca.

**Phat hien quan trong khi lam:** Raspberry Pi OS co san 1 drop-in
(`/usr/lib/systemd/journald.conf.d/40-rpi-volatile-storage.conf`) ep
`Storage=volatile` - nghia la nhat ky he thong (`journalctl`, noi ghi lai
dich vu tunnel/Bluetooth/dashboard khoi dong-dung-loi) **chi nam trong
RAM va MAT SACH moi lan tat may**, khong phai do loi cau hinh cua du an
nay ma la mac dinh cua he dieu hanh de tiet kiem the SD. Thu muc
`/var/log/journal` da ton tai tu truoc (tao thang 6) nhung luon RONG -
day chinh la nguyen nhan that su cua nghi van "log co ve bi mat" tu truoc.

**Da sua:**
- `config/journald-console-pi.conf` (moi) -> `/etc/systemd/journald.conf.d/60-console-pi.conf`:
  ep `Storage=persistent`, `MaxRetentionSec=60day`, `SystemMaxUse=500M`.
  Ten file bat dau bang `60-` de ap dung SAU (de de) file `40-` cua he dieu
  hanh. `install.sh` goi them `journalctl --flush` de ghi journal dang co
  trong RAM xuong dia NGAY, khong phai doi den lan reboot ke tiep.
- `config/logrotate-console-pi`: gop them `console-pi-dhcptest.log` va
  `console-pi-errors.log` vao chung 1 co che xoay vong (`daily`,
  `rotate 60`, `maxsize 5M`, nen lai) - truoc day 2 file nay hoac khong
  duoc xoay vong (`dhcptest.log` moi them o ban 0.4.21, quen dua vao) hoac
  tu xoay vong rieng theo dung luong khong dam bao thoi gian
  (`errors.log`, RotatingFileHandler 2MB x3 ~vai tuan tuy toc do loi).
- `src/ui/errlog.py`: bo `RotatingFileHandler`, chuyen sang ghi them don
  gian - giao het viec xoay vong cho logrotate, tranh 2 co che danh nhau
  tren cung 1 file.
- `install.sh`: tang thoi gian giu nhat ky nginx (`/etc/logrotate.d/nginx`)
  tu 14 len 60 ngay - day la cua ngo mang chinh, loi tunnel/proxy thuong
  the hien o day truoc tien.
- `uninstall.sh` (purge): don lai cau hinh journald 60 ngay khi go cai dat.
- Tai lieu (`/docs`, muc "Nhat ky loi") cap nhat day du danh sach nhat ky
  va cach xem lai theo khoang thoi gian bang `journalctl --since/--until`.

Da kiem tra that tren may dang chay: `journalctl --flush` xac nhan journal
chuyen tu `/run/log/journal` (RAM) sang `/var/log/journal` (dia that);
`logrotate -d` xac nhan cau hinh moi nhan dung ca 6 file; selftest van
39 dat sau khi trien khai.

## 0.4.23

**Tach nut Tat may / Khoi dong lai ra tab rieng "Nguon dien"** - truoc day
hai nut nay nam chung trong tab Tong quan. Ly do: may nay thuong duoc gan
vao vo RasPad, va nguoi dung can mot noi ro rang de tim nut nguon, tach
biet khoi cac thong tin theo doi khac.

Tab moi (`/power`, module `ui/power.py`) giu nguyen hanh vi cu (goi
`health.power_action()`, dung `systemctl --no-block` de HTTP tra loi truoc
khi may that su tat/khoi dong lai), them phan giai thich ro rang ve gioi
han khi gan trong vo RasPad.

**Da kiem tra that (khong bia) kha nang tat hoan toan vo RasPad qua phan
mem:** I2C dang bi tat trong `/boot/firmware/config.txt`
(`dtparam=i2c_arm` bi comment, khong co `/dev/i2c-1`), va khong tim thay
bat ky driver kernel, dtoverlay, hay dich vu he thong nao mang ten
raspad/sunfounder tren may (grep toan bo `systemctl list-unit-files`,
`dmesg`, `lsmod`). Ket luan trung thuc: **khong phat hien duoc kenh dieu
khien nguon nao cua rieng vo RasPad tu phia phan mem** - vo RasPad dung
cong tac nguon vat ly rieng de cat dien toan bo (man hinh + Pi), day la
cach duy nhat de tat hoan toan hien tai. Da ghi ro dieu nay tren giao dien
(`/power`) va trong Tai lieu (muc "Suc khoe thiet bi va nut nguon") thay vi
gia vo co tinh nang khong that su ton tai.

## 0.4.22

**Sua selftest.sh bao nham loi khi co cap console that** - phat hien ngay
sau khi trien khai ban 0.4.21, lan dau tien trong suot qua trinh phat trien
co mot cap console USB that duoc cam vao may luc chay selftest.

**Nguyen nhan:** khoi kiem tra rieng cho tung cong console
(`/dev/ttyUSB*`) tu viet tay, dung `curl http://127.0.0.1/term-console/...`
qua **cong 80** (duong cong cong, LUON doi dang nhap theo dung thiet ke bao
mat) roi mong doi HTTP 200 - chac chan nhan 302. Bai hoc nay da duoc ghi va
sua cho ham dung chung `kiem_trang()` (dung cong 8880, duong kiosk duoc
mien dang nhap) tu truoc, nhung khoi kiem tra console rieng le nay **quen
ap dung**, nen ngu yen chua bao gio bi phat hien vi chua co cap console
that nao duoc cam trong luc test.

**Sua:** doi sang cong 8880, giong `kiem_trang()`. selftest tu **38 dat/1
luu y/1 that bai** len lai **39 dat/1 luu y**, 0 that bai.

## 0.4.21

**Sua loi that gap tai mang cong ty: "Kiem tra toan dien cong mang" bao
nham "khong co gateway hop le" du mang hoan toan binh thuong.** Nguoi dung
bam nut kiem tra, cong cu bao loi va tu choi test Internet/bang thong -
nhung `ping`/`traceroute` lam tay qua CHINH cong do (kem ICMP Redirect that
tu router) lai chay hoan toan binh thuong.

**Nguyen nhan:** mang do khong gui Option 3 (Router) co dien - chi gui
**Option 121 (Classless Static Routes, RFC 3442)**, mot chuan quoc te ngay
cang pho bien o mang doanh nghiep/hien dai. He dieu hanh (Windows/Linux) da
tu biet doc Option 121 tu lau, nhung cong cu nay truoc gio chi biet doc
Option 3 nen ket luan sai "khong co gateway" du du lieu dinh tuyen that su
CO trong goi tin, chi la o option khac.

**Sua:** them ham doc Option 121, uu tien no hon Option 3 dung theo RFC
3442 khi ca hai cung co mat (tim tuyen mac dinh 0.0.0.0/0, lay gateway cua
tuyen do). Da kiem thu voi 4 tinh huong: chi co Option 121 (dung du lieu mo
phong khop chinh xac mang cong ty da gap), chi co Option 3, Option 121 co
nhieu tuyen khong tuyen mac dinh ro rang (lay tuyen dau lam du phong), va
khong co gi ca.

**Them nhat ky rieng cho cong cu nay** (`/var/log/console-pi-dhcptest.log`)
- ghi lai OFFER/ACK that su nhan duoc moi lan bam kiem tra. Ly do: cong cu
nay hay dung o hien truong (mang la, cong ty) dung luc khong the SSH hay
nho su ho tro tu xa - truoc day ket qua chi hien tren man hinh roi mat, ve
nha khong con cach nao xem lai. Cung them 2 dong vao bang "Vi tri file quan
trong" trong tai lieu (`console-pi-dhcptest.log` va `console-pi-errors.log`
tu 0.4.16).

## 0.4.20

**Sua triet de: DNS bi xoa trang khi rut day mang, chi con WiFi.** Ban
0.4.19 them DNS du phong vao TUNG giao dien rieng le (nmcli +ipv4.dns cho
eth0, DNS= trong 12-wlan0.network cho wlan0) - VAN CHUA DU, vi
NetworkManager (ben ghi `/etc/resolv.conf`) chi biet DNS cua eth0 (do no
quan ly), hoan toan khong biet gi ve cau hinh DNS rieng cua wlan0 (do
systemd-networkd quan ly). Ngat eth0 la NetworkManager xoa trang DNS,
khong con dong nameserver nao ca - da tai hien duoc dung loi nay bang cach
ngat that eth0 va quan sat.

**Sua dung goc:** them `/etc/NetworkManager/conf.d/99-consolepi-dns-fallback.conf`
voi cau hinh **global DNS** (`[global-dns]` + `[global-dns-domain-*]`) -
day la cap DNS cua toan bo NetworkManager, AP DUNG BAT KE GIAO DIEN NAO
DANG HOAT DONG, khong phu thuoc giao dien cu the nao con song hay khong.

**Da kiem chung that bang cach ngat han eth0** (dat luoi an toan tu bat lai
sau 90 giay truoc khi thu, tranh mat mang that su):
- `resolv.conf` van con `1.1.1.1`, `8.8.8.8` sau khi ngat eth0
- Phan giai duoc `region1.v2.argotunnel.com`, `cloudflare.com`
- Cloudflare Tunnel van `active`, 0 loi
- Truy cap qua `https://consolepi.home-server.id.vn` tra ve `403` (trang
  Cloudflare Access, KHONG PHAI loi ket noi 502/523) - xac nhan duong
  truyen thong suot end-to-end chi bang WiFi, khong can eth0.

`install.sh` cung cai file nay khi cai lai, khong mat.

## 0.4.19

**TIM RA NGUYEN NHAN THAT cua "cam day mang thi duoc, dung WiFi thi khong"**
- day moi la ly do tunnel fail o cong ty, khong phai giao thuc QUIC (0.4.18
  van dung nhung chua du).

**Van de: DNS ghim cung vao mang cu.** May chu DNS do DHCP cap chi ton tai
TRONG MANG DO. `/etc/resolv.conf` chi co dung 1 dong:
`nameserver 192.168.110.21` - dia chi thuoc mang day o nha. Mang Pi sang noi
khac (hotspot 4G/5G tu dien thoai o cong ty) thi may chu DNS do khong con
lien lac duoc -> khong phan giai duoc bat ky ten mien nao -> cloudflared
khong tim duoc `region1.v2.argotunnel.com` -> **duong ham tu xa chet**. Khop
dung log that sang nay: `Failed to refresh DNS local resolver ... i/o timeout`.

**Sua:** them DNS cong cong `1.1.1.1` + `8.8.8.8` lam du phong cho ca hai
duong:
- `eth0` (NetworkManager): `nmcli con mod ... +ipv4.dns`
- `wlan0` (systemd-networkd): them `DNS=` vao `12-wlan0.network`
- `install.sh` cung dat lai khi cai lai, khong mat.

Da kiem chung sau khi sua: `resolv.conf` co du 3 nameserver, phan giai duoc
`region1.v2.argotunnel.com`, `cloudflare.com`, `github.com`; tunnel van chay
`protocol=http2`, 0 loi.

**selftest.sh: them 2 muc kiem tra** - co DNS du phong khong, va co phan giai
duoc ten mien cua Cloudflare Tunnel khong. Neu sau nay cau hinh bi mat (cai
lai he dieu hanh, doi mang) la biet ngay thay vi doi den luc ra hien truong
moi phat hien. **38 dat / 2 luu y** (truoc la 36/2).

**Con mot bay nua da ghi vao tai lieu:** duong ra qua `eth0` luon duoc uu
tien hon `wlan0` (metric 100 so voi 1024). O cong ty neu cam day mang ma day
bi port-security chan, may van co gang di ra bang day do va chet, du hotspot
WiFi van tot. Cach chac an: **rut han day mang khi dung hotspot dien thoai**.
Kiem tra bang `ip route get 1.1.1.1` - phai thay `dev wlan0`.

## 0.4.18

**1. SUA LOI TUNNEL KHONG CHAY DUOC TREN HOTSPOT DIEN THOAI** (da fail that
o cong ty). Kich ban: khong co WiFi, Bluetooth bi cam, day mang bi
port-security chan - chi con hotspot 4G/5G tu dien thoai.

Nguyen nhan doc duoc tu log that: `write udp [::]:... sendmsg: network is
unreachable`. Cloudflared mac dinh dung **QUIC (chay tren UDP)**, ma mang di
dong rat hay chan/khong on dinh voi UDP; kem theo do la mang di dong thuong
cap IPv6 nhung duong di IPv6 thuc te khong hoat dong.

Sua: ep `--protocol http2` (TCP cong 443, gan nhu luon duoc cho qua vi
khong phan biet duoc voi HTTPS thuong) va `--edge-ip-version 4`. Da kiem
chung that sau khi sua: `cloudflared will use 'http2' as primary protocol`,
ca 2 ket noi deu `protocol=http2`, **0 loi trong 30 giay theo doi lien tuc**.

*Chi tiet ky thuat quan trong*: co `--protocol` da bi ban cloudflared moi
(2026.8.3) AN KHOI `--help` nhung VAN HOAT DONG - kiem chung bang cach so
sanh voi mot co khong ton tai (co la bi tu choi ngay, `--protocol` thi duoc
chap nhan binh thuong). Neu ban tuong lai go han co nay thi phai ghim lai
phien ban cu hon.

**2. HE THONG NHAT KY LOI** - tab moi "Nhat ky loi" tren menu:
- Ghi lai **moi loi Python khong duoc bat** trong dashboard kem traceback
  day du (truoc day chi hien trang loi chung chung roi bien mat khong dau
  vet - o hien truong khong con cach nao biet chuyen gi da xay ra).
- Xem duoc canh bao/loi journal cua tung dich vu chinh ngay tren web,
  khong can nho lenh `journalctl`.
- Tu xoay vong o 2MB (giu 3 ban, toi da ~8MB), khong lo day the nho.

*LOI THAT DA BAT DUOC KHI VIET TINH NANG NAY (truoc khi trien khai)*: cach
lam ban dau la "ghi log roi `raise` lai loi nguyen van" voi y dinh khong doi
hanh vi. Nhung Flask goi `errorhandler(Exception)` o **hai cho** khac nhau,
va `raise` lai o lan goi thu hai se thoat ra ngoai ca tang WSGI - lam
**trinh duyet nhan ket noi bi ngat** thay vi trang loi 500, va con bien
**loi 404 binh thuong thanh 500**. Neu trien khai ban do thi te hon han so
voi truoc khi co tinh nang. Da phat hien qua kiem thu HTTP that (khong phai
test client, vi test client co hanh vi khac) va sua thanh tra ve response
truc tiep, khong `raise` o bat ky nhanh nao.

**3. XOAY VONG NHAT KY (logrotate)** cho cac file log con lai: da do that
`console-pi-fallback.log` ghi 1 dong moi 2 phut va chua tung duoc xoay vong -
sau vai thang dung ngoai hien truong co the len hang tram MB. Day the nho
la mot trong nhung nguyen nhan hong Pi pho bien nhat.

## 0.4.17

**Va lo hong chen co lenh (argument injection) qua dia chi/tai khoan** o 4
noi: Ping/Traceroute, MTU Discovery, Kiem tra TLS, va tab SSH. Ra soat lai
code phat hien, khong phai da gap that.

Mau kiem tra dau vao cu (`[A-Za-z0-9.\-:]`) cho phep dau "-" o **vi tri dau
chuoi**. Voi cong cu goi subprocess dang list (khong `shell=True`) thi
khong chen duoc lenh shell, nhung mot gia tri nhu `--flood` co the bi
`ping` hieu nham la MOT CO LENH thay vi dia chi - va tien trinh Flask nay
chay duoi quyen root nen `ping --flood` se chay duoc that.

**Rieng tab SSH nghiem trong hon nhieu**: host/user o day duoc go THANG
vao mot shell that qua tmux de chay lenh `ssh`. Mot host bat dau bang
`-oProxyCommand=<lenh tuy y>` la ky thuat chen co SSH THAT SU va nguy
hiem - cho phep chay lenh tuy y ngay khi ket noi, hoan toan khong can
dung den cac ky tu `; $ \` & |` da bi chan tu truoc.

Sua bang cach bat buoc **ky tu dau tien phai la chu hoac so**, khong duoc
la dau "-" hay bat ky ky tu dac biet nao khac, o ca 4 noi. Da kiem thu voi
cac chuoi chen thuc te (`-f`, `--flood`, `-oProxyCommand=...`, `-l`,
`-4.4.4.4`) - deu bi chan; dia chi/tai khoan hop le (`8.8.8.8`,
`google.com`, `switch-01.lan`, `fe80::1`) van hoat dong binh thuong qua
kiem thu voi phien tmux that.

## 0.4.16

**Phat hien nghiem trong nhat trong dot ra soat toi nay: tinh nang "Tab
Terminal giong tab SSH" (them o soan lenh, nut Dan tu chon cach dan) o
0.4.6 CHUA BAO GIO DUOC TRIEN KHAI THAT SU len may, du da bao voi nguoi
dung la xong.** Nguyen nhan: luc do khong co quyen sudo nen chi dua lenh
`sudo cp ...` de nguoi dung tu chay, nhung dong lenh do khong duoc thuc
hien (co le bi cuon troi giua luc dang xu ly su co Bluetooth ngay sau do).
Nhung lan sau co sudo lai chi deploy CAC FILE lien quan Bluetooth, khong
kiem tra lai toan bo hang doi deploy con thieu.

Phat hien bang cach **so sanh truc tiep `diff -rq src/ui /opt/console-pi/ui`**
- day nen la buoc kiem tra chuan sau moi phien lam viec dai co xen ke nhieu
chu de, thay vi tin tren tri nho hoi thoai la "da deploy roi". Da deploy du
`soanlenh.py`, `ssh.py`, `terminal.py`, `docs.py` va xac nhan lai qua HTTP
that: ca 2 tab deu co o soan lenh, route `/terminal/paste` va `/ssh/paste`
chay dung.

## 0.4.15

**Da vao duoc mang qua Bluetooth PAN that su tren Windows 11** - ghi lai dung
quy trinh vao tai lieu (thay cho phan canh bao loi truoc do):

1. **Ghep cap phai khoi dong TU PHIA WINDOWS** (Settings -> Bluetooth &
   devices -> Add device), khong phai bam Ghep cap tren Pi truoc.
2. Ghep xong Windows bao "Connected" nhung **CHUA vao mang duoc ngay** - day
   chi la ghep cap Bluetooth thuan tuy.
3. **Buoc quyet dinh**: mo Devices and Printers kieu cu (`control printers`)
   -> chuot phai ConsolePi -> **Connect using -> Access point**.

Da kiem chung that sau buoc 3: giao dien `bnep0` xuat hien trong cau `pan0`,
dnsmasq cap dung IP (`192.168.60.29`) cho may tinh.

Them nhac nho: phai bam **Trust** cho may tinh sau khi xong (nhu da lam voi
ban phim) - thieu buoc nay thi lan sau Bluetooth rot la phai lam lai tu buoc 3
moi lan, khong tu noi lai duoc.

## 0.4.14

**Ghi lai quy trinh ghep ban phim Bluetooth DA THANH CONG that** vao tai lieu
(muc dau tien cua trang Bluetooth), sau nhieu vong debug that tren may cua
nguoi dung:

- Ghep MOI: giu nut Connect LIEN TUC den khi den nhap nhay NHANH, RIENG luc do
  moi bam Ghep cap tren web - bam tre la that bai kieu "khong tim thay" du
  ban phim hoan toan binh thuong.
- Sau khi ghep, ban phim TU DONG ngat sau vai giay khong go gi - day la tinh
  nang tiet kiem pin cua chinh ban phim, khong phai loi, khoa lien ket
  (Bonded) khong mat.
- De NOI LAI (khac voi ghep lai): bam NHANH 1 cai vao nut Connect (KHONG giu
  lau - giu lau vao lai che do ghep MOI, co nguy co lam mat khoa cu).
- **Canh bao quan trong nhat**: TUYET DOI khong bam "Ghep cap lai" khi ban
  phim chi don gian mat ket noi tam thoi (van "da ghep, chua noi") - nut do
  XOA khoa lien ket dang co roi ghep MOI TU DAU, mo lai nguy co that bai neu
  ban phim khong dang o che do ghep cap dung luc do bam.
- Them lenh kiem tra khoa lien ket con luu tren dia hay khong (nguon su that
  cuoi cung, khong phu thuoc bo nho tam cua bluetoothctl):
  `sudo cat /var/lib/bluetooth/*/<mac>/info` - tim muc `[LinkKey]`.

## 0.4.13

**Ban phim Bluetooth bi mat ghep cap** - tim ra do o "🔄 Reset Bluetooth" o
cuoi trang co o tick "Quen tat ca thiet bi da ghep cap". Nguoi dung dang loi
khac (khong vao mang PAN duoc) nen thu bam Reset de "sua dai", vo tinh tick
nham o do va mat luon ban phim da ghep cap thanh cong truoc - phai ghep lai
tu dau oan uong. Xac nhan lai: **phia Pi khong he hong gi** (adapter, Class,
cac dich vu deu binh thuong), ghep lai la duoc ngay.

Sua de khong lap lai: hop `confirm()` gio **doc trang thai o tick truoc khi
hoi** - neu dang tick "Quen tat ca" thi hien canh bao rieng, noi thang se mat
ban phim/chuot/dien thoai va phai ghep lai tu dau, kem ghi ro **loi vao mang
PAN khong lien quan gi den viec nay** (tranh nham tuong reset-quen-het se sua
duoc loi PAN). Truoc day chi co 1 dong canh bao chung chung "Reset Bluetooth?"
du co tick "Quen tat ca" hay khong, de bam qua ma khong doc ky.

## 0.4.12

Sua loi **man hinh Pi hien trang trang "Method Not Allowed"** sau khi thu
ket noi Bluetooth. Bat duoc qua log that: `GET /bt-connect HTTP/1.1" 405`.

NGUYEN NHAN GOC, anh huong CA APP chu khong rieng Bluetooth: rat nhieu route
POST (`bt-connect`, `bt-unpair`, `wifi-*`, `bt-scan`...) hien trang HTML
thang ra sau khi xu ly xong, KHONG chuyen huong. Vi vay dia chi tren trinh
duyet dung nguyen o duong dan POST do sau khi bam nut. Tren man hinh cam
ung, chi can cu chi **keo xuong lam moi (pull-to-refresh)** la trinh duyet
gui lai dung request do nhung bang GET - Flask tu choi (route chi cho
POST), Werkzeug hien trang loi trang boc xau xi, nguoi dung tuong ca
dashboard bi vo.

Sua tan goc (doi het cac route POST sang chuyen huong sau khi xu ly) la
thay doi lon dung vao rat nhieu file, rui ro cao. Thay bang cach an toan
hon: bat loi 405 O TOAN APP (`app.py`), dua nguoi dung ve lai trang truoc
do (doc tu header Referer) thay vi hien trang loi - cho **moi route trong
app**, khong chi Bluetooth. Co kiem tra Referer phai cung goc voi chinh
Pi truoc khi tin, tranh bi dan sang trang la neu header do bi gia mao.

## 0.4.11

**Nut "Ket noi mang (PAN)" lam NGUOC chieu.** Nut nay goi
`Network1.Connect("nap")` - tuc la bao *Pi di XIN mang cua may kia*, trong khi
viec can lam la *may kia xin mang cua Pi*. May Windows chi quang ba **PANU**
(vai tro may xin mang), khong co dich vu NAP, nen BlueZ tra ve
`Operation is not supported` - da do that tren may nguoi dung. Nguoi dung doc
dong loi do khong the biet phai lam gi.

Trong Bluetooth PAN, ben CHO mang (NAP) **khong bao gio tu bat dau ket noi
duoc** - luon phai ben XIN mang (PANU) goi sang. Pi la ben cho mang nen chi
co the ngoi doi. Nay nut kiem tra truoc: neu may kia khong co dich vu NAP thi
noi thang viec can lam **o may do**, thay vi nem ra dong loi kho hieu.

**Tai lieu - cai bay lon nhat tren Windows:** trang *Settings &rarr; Bluetooth
&amp; other devices* (giao dien moi) KHONG HE CO chuc nang PAN - o do ConsolePi
chi hien "Connected" kem moi nut *Remove device*. Phai dung Control Panel kieu
cu (`control printers`, hoac `explorer shell:::{A8A91A66-...}`, hoac qua
`ncpa.cpl`). Da ghi ro ca 3 duong vao tai lieu, kem cach xu ly khi khong thay
dong "Connect using" (Windows luu danh sach dich vu tu luc ghep cap, phai xoa
o ca hai phia roi ghep lai).

Da kiem chung phia Pi hoan toan san sang: `pan0` dung la cau noi, DHCP lang
nghe tren 192.168.60.1, va adapter dang quang ba dung UUID NAP
(`00001116`) - xac nhan qua D-Bus.

## 0.4.10

**Phan biet "da ket noi Bluetooth" voi "da vao mang"** - dung cho gay hieu
nham cho nguoi dung: may ban ghep cap xong, dashboard hien "🟢 dang ket noi"
mau xanh, nhung vao `192.168.60.1` thi khong duoc.

Do tren may that: may ban `DESKTOP-I2O01BN` co `Connected: yes` nhung
**khong he co giao dien `bnep` nao gan vao cau `pan0`, dnsmasq chua cap IP
cho ai**. Tuc la moi ket noi Bluetooth (Windows tu noi ho so am thanh khi
ghep cap xong), chua he vao mang. Pi la ben CHO mang nen **khong the tu ep**
may tinh vao mang - may tinh phai tu chu dong noi vao dich vu NAP.

Nay trang Bluetooth doc dau hieu THAT (co `bnep` trong cau `pan0` + IP da cap
trong file lease cua dnsmasq) va hien 3 trang thai khac nhau cho may tinh/
dien thoai:
- 🟢 **da vao mang** (kem IP da cap)
- 🟡 **co ket noi Bluetooth, CHUA vao mang** - kem huong dan ngay tai cho:
  chuot phai ConsolePi &rarr; Connect using &rarr; Access point
- ⚪ da ghep, chua noi

**Xac nhan: ghep nhieu thiet bi cung luc VAN DUOC.** Do tren may nay: ban
phim (HID) va may ban (PAN) cung ket noi mot luc, khong xung dot.

## 0.4.9

**Da ghep duoc ban phim Bluetooth tren may that** (Samsung `04E8:7021`):
Paired/Bonded/Trusted/Connected deu `yes`, nhan tao ra thiet bi nhap lieu
that (`input: Bluetooth Keyboard`). selftest tu 33 dat/3 luu y len
**36 dat/2 luu y**.

Hai dieu do duoc trong luc ghep, deu di nguoc gia dinh ban dau:

- **Ban phim nay KHONG can go ma nao ca.** Agent khong he duoc BlueZ hoi cau
  nao - no dung kieu ghep "Just Works". Nghia la nguoi dung noi dung: *ban
  phim dau can ghep bang ma so*. Voi ban phim kieu nay, man hinh khong hien
  so gi la BINH THUONG, khong phai loi. (Cac sua o 0.4.7 ve nhanh ma PIN van
  can, nhung danh cho ban phim doi cu hon.)
- **Ban phim mat 116 GIAY moi chiu quang ba** ke tu luc bat dau quet. Cua so
  quet cu 20 giay - va ca muc 60 giay thu o ban sua truoc - **deu khong du**.
  Nay de **150 giay**, kem dem nguoc hien ngay tren trang de nguoi dung biet
  con bao lau. Vi qua trinh dung ngay o buoc quet nen truoc day khong he de
  lai dau vet nao trong log, rat kho lan ra nguyen nhan.

Tai lieu: noi ro nhieu ban phim khong can ma, va nhan manh den phai nhap nhay
NHANH moi la che do ghep cap.

## 0.4.8

Hai loi that lam **khong ghep duoc ban phim Bluetooth**, ca hai deu do dac
tren may that (khong phai doc code suong):

- **Pi tu khai la thiet bi "khong ro loai"**. BlueZ tu sinh class
  `0x420000` - major class = `0x00` (Miscellaneous). Nhieu ban phim Bluetooth
  chi chiu ghep voi host tu khai la MAY TINH, thay "khong ro loai" thi bo qua.
  Nay dat `Class = 0x000100` trong `/etc/bluetooth/main.conf` (khoa nay von co
  san trong file nhung bi chu thich). Da do lai sau khi sua: class thanh
  `0x420100` (major = Computer) va **van giu nguyen bit Networking** nen
  Bluetooth PAN khong he anh huong (pan0 giu nguyen 192.168.60.1). install.sh
  cung dat khoa nay nen cai lai khong mat.

- **Tat quet NGAY TRUOC khi ghep cap**. Luong cu: quet -> thay thiet bi ->
  `scan off` -> `pair`. BlueZ coi thiet bi vua quet duoc ma chua ghep la "tam
  thoi" va xoa khoi danh sach rat nhanh sau khi ngung quet, nen den luc `pair`
  thi bao thang `Device ... not available` du vai giay truoc con thay ro. **Da
  tai hien duoc dung loi nay 2 lan tren may that.** Nay giu quet chay suot ca
  qua trinh pair/trust/connect, chi tat o khoi `finally`.

## 0.4.7

Sua loi ghep cap **ban phim Bluetooth kieu PIN cu** - dung cai lam nguoi dung
thay "vo ly": ban phim doi go mot day so, nhung tren man hinh khong hien so nao.

- **Nhanh PIN kieu cu bi bo quen hoan toan o giao dien.** Agent nhan yeu cau
  `RequestPinCode` (Bluetooth 2.x), tra ve `0000` va ghi trang thai
  `kind="pin"` - nhung trang web CHI co nhanh hien `passkey` va `confirm`,
  khong he co nhanh nao hien `pin`. Ket qua: ban phim dung cho go ma, nguoi
  dung chi thay "dang ghep cap" roi treo den het gio. Nay ca 2 kieu (passkey
  doi moi va PIN kieu cu) deu hien so to ro giua man hinh kem huong dan.
- **Ban phim lien touchpad bi nhan dien nham.** Theo chuan Bluetooth, 2 bit
  loai thiet bi co 4 gia tri: `01` = ban phim, `11` = ban phim lien
  chuot/touchpad. Ban dau chi bat `01` nen loai combo (rat pho bien) bi coi la
  "thiet bi khong go duoc" va bi day sang nhanh ma co dinh, khong hien ma.
  Kiem thu voi cac ma CoD that da bat duoc loi nay truoc khi giao.
- **Ma PIN cho ban phim gio sinh ngau nhien** thay vi co dinh `0000` (an toan
  hon, va van dung cach lam chuan). Rieng thiet bi khong go duoc (tai nghe,
  loa) van giu ma co dinh vi ma cua chung do nha may quy dinh - sinh ngau
  nhien la chac chan hong.
- **Them 2 nhanh trang thai truoc day cung bi bo roi**: `need-passkey` (thiet
  bi doi Pi nhap ma do chinh no hien - ban phim khong dung kieu nay) va
  `cancelled` (thiet bi huy giua chung), deu noi ro ly do thay vi im lang.
- **Agent nay ghi log tung buoc** ra `journalctl -u bt-agent`. Truoc day chi
  in 1 dong luc khoi dong nen ghep cap that bai la khong con dau vet nao de
  lan ra nguyen nhan - da xac nhan dung tren may that.
- Tai lieu: them muc giai thich vi sao ban phim chua ket noi van go duoc ma
  xac thuc (day la cach chuan, Windows/macOS cung vay).

## 0.4.6

**Tab Terminal nay giong tab SSH**: them o soan tap lenh ngay duoi khung
terminal (chon tap lenh tu Thu vien -> sua -> Copy / Dan tu clipboard / Dan vao
terminal), gui bang fetch nen khong tai lai trang va khong dinh hop thoai
"Leave site?". Khung terminal cung cao them (`100vh-330px`).

Khoi soan lenh duoc tach ra `src/ui/soanlenh.py` dung chung cho ca 2 tab - sua
1 lan la ca 2 cung duoc, khong bi lech nhau theo thoi gian. Moi tab giu rieng
noi dung dang soan (soan do o tab SSH khong de len tab Terminal).

**Nut Dan tu chon dung cach dan** dua vao chuong trinh dang chay trong terminal
(`tmux display-message -p '#{pane_current_command}'`):
- Dang o **shell cua Pi** (bash/sh/zsh): dan ca khoi, **khong dong nao chay** -
  an toan cho shell quyen root, nguoi dung bam Enter moi chay.
- Dang **SSH/console vao thiet bi** (ssh, microcom...): gui tung dong, cho
  thiet bi in xong moi gui tiep (khoi roi mat ky tu dau dong), dong cuoi de
  nguoi dung tu bam Enter.

Chon nham cach la hong: dan ca khoi vao thiet bi thi mat chu, con gui tung
dong vao shell quyen root thi tung lenh se CHAY luon. Da kiem chung: bash ->
'bash', chay ssh -> 'ssh', chay python3 -> 'python3'. *Gioi han that da do
duoc:* neu chay mot **script bash** tu no noi chuyen voi thiet bi thi tmux van
bao "bash" nen se dan ca khoi - truong hop hiem, da ghi ro trong tai lieu.

## 0.4.5

**Trang Tai lieu lam lai theo tab** cho de tra, de doc, de tim:
- Cot ben trai la danh sach muc **xep theo nhom** (He thong / Ket noi / Lam viec
  hang ngay / Cong cu mang / Thiet bi & nguon / Su co), bam la mo dung muc do -
  khong con cuon mot trang dai 20 muc.
- **O tim kiem toan van**: go tu khoa thi tung muc hien **so lan xuat hien**, cac
  muc khong khop tu an di, va tu mo muc khop dau tien de thay ket qua ngay.
  Chi muc tim kiem doc tu chinh noi dung dang co tren trang nen **khong lam trang
  nang them**.
- Nut **Xem tat ca** de doc lien mach, dung Ctrl+F cua trinh duyet, hoac in ra giay.
- Giu nguyen duong dan cu kieu `/docs#suco`, va nho muc dang xem lan truoc.
- Muc nao quen xep nhom van hien ra o nhom "Khac" - them muc moi khong so bi mat.

**Cap nhat noi dung tai lieu** cho khop nhung gi vua sua:
- Cach o mat khau tab SSH hoat dong, va vi sao co tinh khong dung `sshpass -p`.
- Vi sao dan tap lenh phai cham (doi thiet bi in xong), va xu ly `--More--`.
- Con lan chuot cuon man hinh (`mouse on`).
- Them 2 su co that vao bang su co: SSH bao "no matching key exchange method
  found" voi thiet bi cu (kem canh bao KHONG duoc them `ssh-dss`), va dan tap
  lenh bi mat ky tu dau dong.
- Sua "6 cong cu mang moi" thanh 5 (Ping lien tuc da bo o 0.4.1).

## 0.4.4

Sua triet de loi **dan tap lenh bi mat ky tu dau dong** tren switch that
(`show inventory` -> `how inventory`). Ban 0.4.3 cho co dinh 0.18s giua cac
dong - VAN MAT CHU, vi `show version` tren switch in ra hang tram dong mat
vai giay, thiet bi con dang in thi dong sau da toi noi.

Nay khong cho theo dong ho nua ma **cho den khi thiet bi thuc su san sang**:
man hinh ngung thay doi 0.5s **va** dong cuoi giong dau nhac (ket thuc bang
`#`, `>`, `$`). Chi "im lang" thoi la chua du - thiet bi cham co the ngung
giua chung roi in tiep. Neu im lang 2.5s ma van khong thay dau nhac thi cung
di tiep, de khong ket lai voi thiet bi co dau nhac la.

Kem theo xu ly **`--More--`** (Cisco chia trang): tu bam Space de thiet bi in
tiep. Trong luc lam da gap them 1 loi cung kieu **ngay trong ma vua viet**:
ban dau chi kiem tra `--More--` khi man hinh CO THAY DOI, nhung thiet bi dung
o `--More--` thi man hinh dung im -> bi cham nham la "da in xong" -> gui dong
ke tiep va ky tu dau tien cua dong do bi thiet bi an lam PHIM BAM sang trang,
mat chu dung y het loi cu. Nay kiem tra o moi vong.

Da kiem chung bang 2 "thiet bi gia" mo phong switch that (loai in cham vai
giay va loai co chia trang `--More--`): ca 2 deu giu nguyen ven tung ky tu,
dong cuoi nam cho bam Enter dung nhu thiet ke.

## 0.4.3

Bon loi thuc te khi dung tab SSH/terminal, moi loi deu do dac lai truoc khi sua:

- **Dan tap lenh bi ROI KY TU DAU DONG** (vi du that: `show interfaces trunk`
  thanh `how interfaces trunk`). Da kiem chung duong dan phia server KHONG cat
  chu (dan vao bash nhan du nguyen van), nen thu pham la ban ca khoi ra 1 luot
  qua nhanh: thiet bi mang khong co dieu khien luong o CLI, trong luc con dang
  echo dong truoc thi ky tu dau dong sau bi mat. Nay **gui tung dong mot, giai
  lao 0.18s giua cac dong**; dong CUOI khong bam Enter de con doc lai.
- **Hoi "Leave site?" moi lan bam Ket noi / Dan**. Hai nut do truoc day la form
  POST binh thuong nen ca trang tai lai, ma ttyd co dang ky canh bao truoc khi
  roi trang. Nay **gui bang fetch, khong tai lai trang** - khung terminal giu
  nguyen phien, khong con hop thoai. Neu JS loi thi form van chay nhu cu
  (khong mat duong lui). Kem theo bat `disableLeaveAlert` cho ttyd.
- **Lan con lan chuot len lai chay cac lenh cu**: tmux chua bat chuot nen banh
  xe bi dich thanh phim Mui ten (= goi lai lich su lenh). Nay bat `mouse on`
  cho tmux -> banh xe cuon dung lich su man hinh.
- **Khung terminal nho, phan tren nhieu chu thua**: bo tieu de danh so va cac
  doan giai thich dai, gop o nhap thanh 1 hang; khung terminal tu `100vh-470px`
  len `100vh-330px` (cao them ~140px).

## 0.4.2

**Thu vien lenh** - bo tri lai cho de nhin, de tim:
- Them **o tim kiem** loc tuc thi theo ten + mo ta + the + noi dung lenh.
- Them **nut the (tag)** bam 1 cai la loc ngay - dung duoc khi khong co ban phim.
- Danh sach chuyen thanh **luoi the**, moi tap lenh 1 the gon; form "Them tap
  lenh moi" thu gon xuong duoi (truoc day choan het phan tren, vao trang khong
  thay ngay thu vien de tim).

**Tab SSH** - lam lai theo dung cach lam viec thuc te:
- Them **o mat khau** dien san. Mat khau duoc go vao terminal DUNG LUC thiet bi
  hoi (doi bang `tmux capture-pane` toi khi thay dau nhac), nen khong hien tren
  man hinh, khong vao `ps`, khong vao lich su lenh - **khac han `sshpass -p`**
  von dat mat khau tho ngay tren dong lenh. Qua 12 giay khong thay dau nhac thi
  bao that la khong thay, khong im lang coi nhu xong.
- Them **o soan tap lenh** ngay duoi khung terminal: chon tap lenh tu Thu vien →
  sua IP/ten → **Copy** / **Dan tu clipboard** / **Dan vao terminal** (dan xong
  khong tu bam Enter). Noi dung dang soan duoc giu lai khi tai lai trang.
- **Bo "chay hang loat"** (trung vai tro voi cong cu Netmiko Config ben Network
  Tools).

**2 lo hong that duoc va trong lan sua nay** (phat hien bang kiem thu, khong
phai doc code suong):
- **Chen lenh qua o dia chi/tai khoan**: dia chi va tai khoan truoc day duoc
  ghep thang vao 1 dong lenh chay trong terminal QUYEN ROOT ma khong loc gi -
  nhap `1.1.1.1; rm -rf /` la chay that. Nay chan bang bieu thuc chinh quy.
- **Chen ma qua noi dung thu vien lenh**: noi dung tap lenh duoc nhung vao the
  `<script>` cua trang SSH. Chi thay `</` bang `<\/` la CHUA DU - mot tap lenh
  chua `<script>` van lot nguyen ven, ma theo chuan HTML thi gap `<script` ben
  trong the script se day bo phan tich sang trang thai dac biet khien the
  `</script>` ke tiep khong con dong the nua. Nay ma hoa ca `< > &` thanh
  `< > &`.

## 0.4.1

Bo tinh nang **Ping lien tuc (do thi song)** (`/nettools/ping-monitor`) da
them o 0.4.0 - danh gia thuc te khong huu dung du da sua 2 loi that (silent-
rejection khi bam Bat dau, va endpoint `/data` bi Cloudflare Worker rieng
cua nguoi dung tra ve 404 khi truy cap tu xa). Go het module, route, muc
tai lieu, dong nhac trong README - khong de sot code chet.

## 0.4.0

Them 6 cong cu chan doan mang moi, tat ca da kiem chung bang do dac that
tren phan cung (khong chi doc code) - danh sach chi tiet o phan "Loi da
phat hien va sua trong luc lam" ben duoi cho biet nhung gi khong nhu du
tinh ban dau va cach sua.

### Tinh nang moi
- **MTU Discovery** (`/nettools/mtu`): tim MTU that toi 1 dia chi bang ping
  DF nhi phan. Khi mot router bao thang ICMP "Frag needed" thi dung ngay
  ket qua do (dang tin cay nhat). Canh bao nguyen nhan pho bien khi MTU
  duoi 1500 (PPPoE ~1492, VPN/GRE/IPsec ~1400-1436). Da kiem chung tren
  chinh mang nha: phat hien dung MTU 1492 (PPPoE that) toi 8.8.8.8, va
  1500 sach toi gateway cung subnet
- **Kiem tra DNS** (`/nettools/dns-check`): doi chieu 1 ten mien qua DNS he
  thong + Google/Cloudflare/Quad9, dung scapy dung goi UDP/53 qua socket
  thuong (khong can quyen root). Canh bao lech ket qua kem chu thich CDN
  de khong bao gia
- **Kiem tra chung chi TLS** (`/nettools/tls-check`): xem chi tiet + tinh
  trang tin cay chung chi HTTPS quan tri (switch/router/iLO). Luon phan
  biet ro "lay duoc de xem" va "duoc he thong tin cay" - khong bao gio
  hien banner "hop le" cho chung chi tu ky/het han/sai ten
- **Ping lien tuc kem do thi song** (`/nettools/ping-monitor`): theo doi
  rot goi thoi gian thuc khi rung/cam lai day, do thi canvas tu ve tay
  (khong thu vien ngoai). Tu dong dung sau toi da 30 phut
- **So do mang 1 doan** (`/nettools/topology`): ghep ARP Scan + LLDP/CDP co
  san thanh so do Pi → switch → cac host. Noi ro gioi han chi 1 doan mang,
  khong ve duoc nhieu switch noi tiep
- **May chu TFTP** (`/nettools/tftp`): bat/tat TFTP de `copy running-config
  tftp://` (sao luu config len Pi) va `copy tftp://.../firmware.bin flash:`
  (nap firmware). Mac dinh TAT, chi lang nghe tren eth0

### Loi da phat hien va sua trong luc lam (khong doan, do dac that)
- **TFTP: du dinh ban dau dung dnsmasq (da co san, khong can cai them) la
  SAI.** Doc ky tai lieu dnsmasq moi phat hien TFTP tich hop san cua no
  CHI HO TRO DOC, khong ho tro GHI - nghia la lenh quan trong nhat (switch
  ghi config len Pi) se khong bao gio chay duoc. Sua bang cach dung
  `tftpd-hpa` (them 1 goi moi, co `--create` de ho tro ghi), va tat ngay
  dich vu mac dinh cua goi nay sau khi cai (no tu bat luc cai dat - di
  nguoc nguyen tac khong tu bat dich vu mang khong xac thuc)
- **DNS check qua scapy `sr1()` can quyen root** (raw socket) - doi sang
  dung lop DNS/DNSQR cua scapy CHI DE DUNG GOI TIN, gui/nhan qua socket UDP
  thuong (`socket.SOCK_DGRAM`) - vua khong can quyen root, vua nhanh hon
- **TLS check voi CERT_NONE**: `ssl.getpeercert()` chuan tra ve RONG khi
  tat xac thuc (gioi han da biet cua thu vien chuan) - phai lay dang nhi
  phan roi phan tich bang `cryptography` (da co san trong du an)

### Don dep
- Xoa `iperf3` khoi danh sach goi cai dat (con sot tu tinh nang da bo o
  ban 0.3.1, khong con noi nao dung den)

## 0.3.1

Vong nay sua mot **lo hong bao mat nghiem trong**, gop hai cong cu chan
doan lam mot, va sua nhieu loi phat hien duoc trong luc kiem thu that tren
may (khong phai doan - tat ca deu do dac/tai hien duoc).

### Bao mat (quan trong - nen cap nhat ngay neu dang dung Cloudflare Tunnel)
- **Nguoi di qua Cloudflare Tunnel bi cham nham la man hinh gan tai cho,
  vao thang dashboard va terminal quyen root khong can dang nhap.** Dieu
  kien mien dang nhap truoc day dua vao dia chi IP (`127.0.0.1`), nhung
  `cloudflared` chay ngay tren Pi va cung goi vao dia chi do. Da sua bang
  cach chuyen sang phan biet theo CONG: cong 80 (LAN/WiFi/Cloudflare) luon
  doi dang nhap, cong 8880 (chi loopback) danh rieng cho man hinh kiosk.
  `selftest.sh` co them chot chan mo phong dung kieu tan cong nay.

### Tinh nang moi
- **Duong vao danh cho may/AI** (`GET /ai`, `/api/system`,
  `/api/console/<dev>/read|send`): dua thiet bi toi diem xa va nho mot AI
  o dau khac dieu khien giup. Mac dinh tat, tu tao token trong tab *Truy
  cap tu xa*, hai muc quyen (chi doc / day du), token chi hien mot lan.
- **Kiem tra toan dien cong mang** (gop DHCP Testing + Kiem tra cong vat ly
  thanh MOT nut bam): toc do/duplex that, thong ke loi duong truyen, PoE,
  DHCP, va neu co IP thi tu dong kiem tra ra Internet (ping 8.8.8.8, ping
  google.com, mo web that) + do bang thong qua Cloudflare Speed Test -
  khong can iperf3 hay may thu hai. Da bo tinh nang do cap TDR (`ethtool
  --test`) vi chip mang tren Raspberry Pi khong ho tro - thay vi hien ket
  qua sai thi bo han, khong con nhac den trong giao dien lan tai lieu.
- Cho phep bat/tat ban phim ao tren trang truy cap tu xa (truoc day chi co
  o man hinh gan tai cho).
- Doc pin an toan hai muc (kernel/UPower luon bat; UPS HAT qua I2C phai tu
  bat trong Cai dat, vi do dia chi I2C mu de cho ket qua gia).

### Loi da sua (phat hien va kiem chung bang do dac that)
- **LLDP/CDP Discovery** hien ten thiet bi la "?" va Mgmt IP la "-" moi
  lan, ke ca khi router/switch quang ba day du - ham phan tich JSON gia
  dinh sai cau truc du lieu that su cua `lldpcli`.
- **Ghep cap Bluetooth "hong mot nua"**: thiet bi bao `Connected: yes`
  nhung khong `Bonded`, khien ban phim khong go duoc gi ma giao dien van
  hien "dang ket noi" mau xanh. Them kiem tra `Bonded` rieng, nut "Ghep
  cap lai" tu xoa ban ghi cu truoc khi ghep lai.
- **DHCP Testing tren wlan0 khong bao gio nhan duoc OFFER**: goi tin co
  hai dia chi MAC mau thuan nhau (Ethernet header vs BOOTP chaddr) khien
  AP WiFi im lang khong tra loi. Sua xong: 5/5 lan thu deu thanh cong.
- **Kiem tra Internet qua DHCP bao "That bai" gia**: khi OFFER tra ve
  trung IP da co san tren cong (rat hay gap khi test tren chinh cong quan
  tri), va khi mot router WiFi co tuyen duong rieng cho dung 8.8.8.8 danh
  cuop goi tin sang cong khac.

## 0.3.0

Vong nay tap trung vao **do tin cay**. Thiet bi nay duoc dung khi switch/router
DA hong - khong the vua sua mang vua sua con Pi. Nhieu loi duoi day chi lo ra
dung luc can phuc hoi nhat, nen deu duoc kiem chung bang do dac that.

### Loi nghiem trong da sua
- **`install.sh` dung giua chung ma khong bao loi.** Vong lap chep script gap
  thu muc `__pycache__`, `install` bao loi, `set -e` dung ca ban cai - nua sau
  khong bao gio chay. Nay chi chep FILE.
- **WiFi ket noi duoc nhung khong bao gio co IP.** `KeepConfiguration=yes` lam
  systemd-networkd coi lease DHCP la "critical"; khi dia chi bi xoa no TU CHOI
  xin lai. Doi sang `KeepConfiguration=static`.
- **Reboot la mat WiFi.** `install.sh` mask `wpa_supplicant` toan cuc nhung
  khong bat dich vu thay the. May van chay chi vi tien trinh tu lan boot cu con
  song. Nay bat `wpa_supplicant@wlan0`.
- **Duong phuc hoi WiFi chua bao gio chay duoc.** `wifi-fallback.service` la
  `Type=oneshot`, systemd giet luon `wpa_supplicant -B` ma script vua sinh ra.
  Nay dung unit `wpa_supplicant@wlan0`.
- **Mot lan quet WiFi that bai lam Pi nhay sang AP,** cat dut ket noi dang dung.
  Nay quet 3 lan va phan biet "quet loi" voi "khong co WiFi quen".
- **Pi bi ghim o che do AP mai mai** khi co thiet bi la bam vao. Nay chi giu toi
  da 5 vong (10 phut).
- **Chuyen AP -> client: associate xong nhung khong co IP.** `networkctl
  reconfigure` goi truoc khi associate xong thi khong bao gio xin duoc dia chi.
  Nay doi `wpa_state=COMPLETED`. Do duoc: chu trinh hoan tat trong **17 giay**.
- **Rot WiFi sau mot luc.** `power_save` dang bat: card ngu, router mat lien lac,
  nhung IP van con tren interface nen nhin vao tuong mang van tot. Nay tat vinh
  vien bang udev rule.
- **File chua mat khau WiFi va mat khau AP doc duoc boi moi tai khoan** (644).
  `install.sh` chi `chmod 600` luc tao moi. Nay siet quyen o moi lan cai.

### Tinh nang moi
- **Nhan moi loai cap console.** Truoc day chi quet `/dev/ttyUSB*` nen bo sot cap
  Cisco USB Console (CDC-ACM, `/dev/ttyACM*`). Nay nhan ca hai ho, cap cong rieng
  (8001-8004 / 8005-8008), kem udev rule tu khoi dong cho cap chua tung thay.
  Dashboard hien ten chip.
- **Suc khoe thiet bi**: canh bao sut ap, nhiet do CPU, tai, RAM, dia, thoi gian
  chay. Nut **Tat may / Khoi dong lai** co xac nhan.
- **Kho file** (`/storage`): mang theo ISO, firmware, cau hinh. Ghi theo luong ra
  dia (khong nap vao RAM), uu tien USB, chan khi sap day, kem SHA256.
  nginx nang gioi han 64m -> 8g.
- **Cam thang thiet bi** (`/direct`): Pi thanh mang mini `192.168.99.1` co DHCP,
  quet ARP tim iLO/iDRAC/IPMI, nhan dien hang qua OUI, mo thang giao dien web.
  Quet duoc ca dai IP tinh tu nhap.
- **Truy cap tu xa** (`/remote`): Cloudflare Tunnel - khong can mo port, khong
  can IP tinh, chay duoc sau 4G. Token luu quyen 600.
- **Nut ngat WiFi**, canh bao neu dang truy cap qua chinh WiFi do.
- **Phan loai Bluetooth dung**: giai ma Class of Device + UUID dich vu thay vi
  chi dua vao `Icon`. Nut ket noi khop dung ho so (PAN cho may tinh/dien thoai,
  HID cho ban phim/chuot). `ReconnectUUIDs` cho thiet bi da ghep tu noi lai.
- **Hieu ung cho**: nut chuyen sang trang thai dang chay va tu khoa, kem vach
  tien do tren cung - mot co che chung (`data-busy`) cho moi trang.
- **`scripts/selftest.sh`**: kiem tra toan bo he thong va ba kich ban quan trong.
  Ma thoat 0 = tat ca dat.
- Mau khi go lenh: bat `colored-stats`, `colored-completion-prefix`, mau cho
  trang `man`. `install.sh` xoa phien tmux cu de cau hinh moi duoc ap dung -
  thieu buoc nay thi cai xong khong thay gi doi.

### Tai lieu
- Them 5 muc moi va **10 su co** vao trang Tai lieu trong dashboard, moi su co
  ghi ro trieu chung / nguyen nhan / cach sua va cach kiem tra.

### Don dep
- Xoa import thua trong `ui/ssh.py`, `ui/commands.py`, `ui/terminal.py`,
  `nettools/ifthen.py`
- Moi trang tai duoi 50ms; Flask dung 3MB RAM

## 0.2.1

### Toi uu hieu nang
- Trang WiFi: **2.865s -> 0.015s** (nhanh hon ~190 lan). Truoc day quet WiFi
  dong bo moi lan tai trang; gio quet o luong nen va nho ket qua 45 giay,
  co nut "Quet lai" khi can du lieu moi
- Trang chu: 0.170s -> 0.051s. Gop 8 lenh `systemctl is-active` thanh 1
- Thanh trang thai: doc IP bang `ioctl` thay vi goi lenh `ip` (khong spawn
  tien trinh), them cache 4 giay
- Chromium tu dieu chinh theo RAM: may duoi 1.5GB (Pi 3, Pi Zero 2W) gioi han
  so tien trinh render va bo nho JS; may duoi 3GB gioi han vua phai

### Mau sac terminal
- Bang mau tuong phan cao dung chung cho ca 3 khung terminal
- Shell co mau san: dau nhac, `ls`, `grep`, va lenh mang qua `grc`
  (ping, traceroute, ip, ss, netstat, nmap, tcpdump, mtr, dig)
- Bo mau rieng cho output thiet bi Cisco (`grc-cisco.conf`)
- Ket qua chay lenh hang loat tren web duoc to mau: do=loi, xanh la=tot,
  vang=canh bao, xanh nhat=IP, xanh duong=MAC, tim=ten cong
- Loi tat: `ports`, `myip`, `routes`, `serial`, `logs`

## 0.2.0

Bản đầu tiên đóng gói được để cài lên máy khác.

### Thêm mới
- **Giao diện mới**: thanh điều hướng trái + thanh trạng thái mạng luôn hiện
  IP của cả 3 giao diện (LAN / WiFi / Bluetooth), tự làm mới mỗi 30 giây
- **Đăng nhập** bằng tài khoản Linux qua PAM
- **Terminal local** và **SSH** (tương tác + chạy hàng loạt) qua ttyd + tmux
- **Thư viện lệnh** — thêm/sửa/xoá, sẵn 5 tập lệnh Cisco, dán được vào terminal
- **Trang Tài liệu** tra cứu ngoại tuyến ngay trên thiết bị
- **nginx** làm cổng trung gian — mọi thứ chung cổng 80
- **Bàn phím ảo** cho màn hình cảm ứng, gõ được cả vào terminal
- **Bluetooth**: quét + ghép cặp bàn phím/chuột, kèm PAN
- **Nút xoay màn hình** trong tab Cài đặt
- `install.sh` cài một lệnh, tự phát hiện có màn hình hay không

### Sửa lỗi đáng chú ý
- `ttyd` chạy `Type=oneshot` nên systemd không giám sát — ttyd chết vẫn báo
  `active`. Đã thay bằng template unit có `Restart=always`
- systemd-networkd xoá mất IP tĩnh của AP sau khi bật — thêm
  `KeepConfiguration=yes`
- Đăng ký NAP của Bluetooth bị huỷ ngay khi script thoát (D-Bus gắn với vòng
  đời tiến trình) — chuyển sang daemon chạy thường trú
- `srp()` của scapy không bắt được DHCPOFFER — chuyển sang `sniff()` + `sendp()`
- Bàn phím ảo: `preventDefault()` trên `touchstart` chặn luôn sự kiện click —
  chuyển sang `pointerdown`
- Toạ độ cảm ứng không tự xoay theo màn hình — cần ma trận hiệu chỉnh khớp
  hướng, và `install.sh` từng tự ghi đè mất ma trận đúng
