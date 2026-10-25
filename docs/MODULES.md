# Muc luc module (TU DONG SINH - khong sua tay)

Sinh boi `tools/tao-tai-lieu-module.py` tu docstring dau moi file. Kien truc va quy tac: xem `KIEN-TRUC.md`; thuat ngu: `TU-DIEN.md`.

## `consolesystem/core`

| File | Dong | Vai tro |
|---|---:|---|
| `cauhinh.py` | 42 | config.json cua may (mat khau terminal, xoay man hinh, tuy chon...) - quyen 0600, ghi nguyen tu, khong am tham mat khi file hong. |
| `dichuyen.py` | 402 | Khung MIGRATION co so phien ban cho thu muc du lieu (2.0, buoc A2). |
| `duongdan.py` | 175 | Console Pi - NOI DUY NHAT khai bao duong dan. |
| `errlog.py` | 181 | Console Pi - Nhat ky loi tap trung |
| `esc.py` | 35 | Thoat ky tu dac biet khi nhung chuoi vao HTML/XML. Truoc day co 12 ban `_esc` rai trong ui/ voi 4 HANH VI KHAC NHAU nhe |
| `lenh.py` | 53 | Chay lenh he thong AN TOAN: luon co timeout, khong bao gio nem ngoai le (tru khi check=True), tra ket qua co cau truc. |
| `magic_packet.py` | 129 | Gui goi tin danh thuc (Wake-on-LAN magic packet) - dich vu dung chung (tach tu wol.py o B3): chuan hoa MAC, liet ke card, gui 3 kieu. |
| `nhatky.py` | 39 | Nhat ky dung chung: ghi ra stderr de systemd/journald gom (`journalctl -u console-pi-dashboard`). Dinh dang giu kieu '[ten] noi dung'. |
| `phancung.py` | 321 | Console Pi - Nhan biet phan cung: cong mang nao, may gi, nhiet do o dau. |
| `phathanh.py` | 381 | Ban phat hanh (releases/) + `current` + console-system-apply (2.0, buoc A6). |
| `sqlite.py` | 86 | Ket noi SQLite dung chung (B1b): MOT file `console.db` cho du lieu LON va TANG DAN (bao cao may, lich su tac vu, trang thai chay...). |
| `store.py` | 154 | Kho du lieu JSON NGUYEN TU va KHONG BAO GIO am tham mat du lieu (B1; xem KE-HOACH-2.0 muc B2b). |
| `store_sqlite.py` | 209 | KhoSqlite: cung giao dien doc()/ghi()/sua() nhu KhoJson nhung luu trong SQLite, CHI GHI PHAN DOI (B1b). |
| `taisan.py` | 12 | Doc TAI NGUYEN van ban (HTML/CSS/JS/PowerShell...) da tach ra khoi ma Python (B6): file nam o `consolesystem/assets/<duong dan>`. |
| `tk_dulieu.py` | 220 | Trien khai phan mem - LOP DU LIEU (may, nhom may, tai khoan ma hoa, nhom tai nguyen, lich, kich ban). |
| `token_tai.py` | 28 | Token tai file 1 lan cho may dich (Trien khai phan mem / Quan ly may tram) - tach tu tk_dongco.py o B3 de web.auth khong phai import tk_dongco. Trang thai nam t |

## `consolesystem/core/capnhat`

| File | Dong | Vai tro |
|---|---:|---|
| `danhmuc.py` | 63 | DANH MUC PHIEN BAN (C1): kho ky danh sach cac ban dang phat hanh cua tung kenh; may khach hoi dinh ky va chi tin danh muc: |
| `goi.py` | 322 | GOI CAP NHAT .cspkg (C1). |
| `khoa.py` | 190 | KHOA KY (C0). Ed25519; khoa RIENG duoc ma hoa bang mat khau (scrypt + AES-256-GCM) khi cat xuong dia; may khach chi giu khoa CONG KHAI. |
| `khoa_lenh.py` | 229 | KHOA / MO KHOA MAY BAN TU DONG (C6). |
| `may.py` | 238 | PHIA MAY KHACH cua he thong cap nhat (C3): cau hinh, hoi kho moi 24 gio, kiem danh muc, nho trang thai, bao "co ban moi" cho chuong. |
| `nangcap.py` | 587 | BO NANG CAP / HA CAP (C4, C5): may trang thai BEN VUNG chay TACH KHOI giao dien (don vi systemd rieng), moi buoc ghi ra dia TRUOC khi lam |
| `nguyenven.py` | 115 | CHONG CHINH SUA (C6): doi chieu TUNG FILE chuong trinh dang chay voi bang bam DA KY cua nha phat hanh. |

## `consolesystem/features/backup`

| File | Dong | Vai tro |
|---|---:|---|
| `saoluu.py` | 432 | Sao luu / Khoi phuc 2.0 (buoc A5) - chi cho BO CUC MOI (/var/lib/console-system, xem duongdan.py/dichuyen.py). |

## `consolesystem/features/deploy_os`

| File | Dong | Vai tro |
|---|---:|---|
| `datten.py` | 232 | Cach dat TEN MAY khi cai Windows qua mang (Deployment OS) - them 1.9.4. |
| `deployos.py` | 105 | Console Pi - Tab "Deployment OS" (trien khai he dieu hanh qua mang) |
| `doodia.py` | 407 | Console Pi - DO O DIA cua may khach qua PXE (CHI DOC, KHONG xoa gi). |
| `dos_chung.py` | 334 | Deploy OS - tien ich chung: duong dan an toan, liet ke file, luu tai len, ten khong dau. |
| `dos_driver.py` | 254 | Deploy OS - DRIVER: goi driver, chon cho boot, khop model, giai nen. |
| `dos_font.py` | 268 | Deploy OS - kho FONT (bo font): tao/xoa/them font, giai nen zip. |
| `dos_giaodien.py` | 186 | Deploy OS - thanh tab dung chung (tabs_deployos), ngu canh Trien khai, JS tai font, bao cao o dia. |
| `dos_hangso.py` | 108 | Deploy OS - hang so dung chung: duoi file cho phep, danh sach OS, mui gio, ngon ngu, ban phim, ten cac buoc wizard. |
| `dos_kichban.py` | 449 | Deploy OS - KICH BAN (task sequence): luu/doc/xoa, wizard, cau hinh mac dinh, kiem tra san sang, phan vung mac dinh. |
| `dos_os.py` | 143 | Deploy OS - he dieu hanh (anh WIM/ISO/SxS): liet ke, tao, xoa, chi so ban Pro. |
| `dos_phanmem.py` | 283 | Deploy OS - danh muc PHAN MEM (.exe/.msi) va UNG DUNG nhieu file: doc/ghi thong tin, tham so cai im lang, giai nen, xoa. |
| `dos_tomtat.py` | 166 | Deploy OS - tom tat kich ban cho giao dien (ten OS, tom tat day du, o tom tat, mo ta ngan). |
| `dosui_caidat.py` | 283 | Tach tu deployos.py (B4). |
| `dosui_chung.py` | 110 | Tach tu deployos.py (B4). |
| `dosui_console.py` | 494 | Tach tu deployos.py (B4). |
| `dosui_driver.py` | 344 | Tach tu deployos.py (B4). |
| `dosui_font.py` | 166 | Tach tu deployos.py (B4). |
| `dosui_kho.py` | 747 | Tach tu deployos.py (B4). |
| `dosui_kichban.py` | 1517 | Tach tu deployos.py (B4). |
| `dosui_o_dia.py` | 69 | Tach tu deployos.py (B4). |
| `dosui_os.py` | 369 | Tach tu deployos.py (B4). |
| `dosui_tiendo.py` | 54 | Tach tu deployos.py (B4). |
| `dosui_ungdung.py` | 258 | Tach tu deployos.py (B4). |
| `fontinfo.py` | 229 | Console Pi - Doc thong tin font (.ttf / .otf / .ttc / .otc) de quan ly "bo font |
| `goidriver.py` | 310 | Console Pi - GOI DRIVER PHO BIEN cho anh boot (WinPE). |
| `gopy.py` | 392 | Console Pi - tab GOP Y (26/09/2026, anh Thoai: "them 1 tab gop y ben trai, |
| `isotach.py` | 566 | Console Pi - Tu dong tach boot.wim / install.wim tu file ISO Windows. |
| `khotrungtam.py` | 694 | Console Pi - ket noi toi "Kho luu tru trung tam" (kho-console-pi), du an |
| `lichsu.py` | 391 | Console System - LICH SU CAI DAT tung may (bien ban ban giao). |
| `pxe.py` | 1085 | Console Pi - Phat PXE that (giai doan ke tiep cua Deployment OS) |
| `pxemenu.py` | 510 | Console Pi - MENU PXE: may khach boot qua mang thay menu de TU CHON kich ban. |
| `sansang.py` | 359 | Console System - KIEM TRA SAN SANG truoc khi cai qua mang (~5 giay). |
| `tenmay.py` | 52 | Chu "Pi" trong cau chu hien cho nguoi dung. |
| `tiendo.py` | 394 | Console Pi - THEO DOI TIEN TRINH cai dat tren may dich (thoi gian thuc). |
| `un_baocao.py` | 392 | Unattend - script bao cao tong ket cuoi + lenh kiem tra card mang/o dia. |
| `un_chonodia.py` | 335 | Unattend - chon o cai Windows (tu dong/tay), diskpart. |
| `un_deploycmd.py` | 624 | Unattend - deploy.cmd (kieu MDT) va cac lenh WinPE: chep app/script, dat ten, bao lich su. |
| `un_goapp_font.py` | 293 | Unattend - go app rac, cai font/ung dung/script/driver offline, .NET 3.5. |
| `un_hangso.py` | 226 | Unattend - hang so Samba va ham dung chung nho (mat khau kho, driverpaths, credentials). |
| `un_iso.py` | 256 | Unattend - ISO tu dong / dia mem ao chua autounattend. |
| `un_kiemtra.py` | 336 | Unattend - bang kiem tra sau cai (muc kiem, lenh reg, buoc nguoi dung). |
| `un_nhung.py` | 141 | Unattend - bo file nhung vao WinPE (sinh_file_nhung, ghi_file_nhung, wim driver). |
| `un_offline.py` | 306 | Unattend - unattend.xml offline (specialize/firstlogon), ho so mac dinh, tat hoi mang. |
| `un_tientrinh.py` | 439 | Unattend - script PowerShell DIEU PHOI sau dang nhap + cua so tien trinh. |
| `un_tuychon.py` | 389 | Unattend - danh sach TUY CHON Windows (registry/lenh) va domain. |
| `un_xml.py` | 195 | Unattend - autounattend.xml: dia Windows (chia o), sinh_autounattend_xml. |
| `unattend.py` | 227 | Console Pi - Tu dong hoa Windows Setup (autounattend.xml) cho Deployment OS |
| `winperieng.py` | 534 | Console Pi - WINPE RIENG trong menu PXE (Sergei Strelec, Hiren's BootCD PE, ban |
| `wol.py` | 236 | Console System - BAT MAY TU XA (Wake-on-LAN) hang loat. |

## `consolesystem/features/files`

| File | Dong | Vai tro |
|---|---:|---|
| `baotri.py` | 280 | Console Pi - Bao tri: don dung luong va sao luu cau hinh. |
| `storage.py` | 364 | Console Pi - Kho file cai dat (ISO / firmware / image). |

## `consolesystem/features/logs`

| File | Dong | Vai tro |
|---|---:|---|
| `logs.py` | 363 | Console System - Trang "Nhat ky" (yeu cau: "phai co he thong log lai ghi |

## `consolesystem/features/network`

| File | Dong | Vai tro |
|---|---:|---|
| `direct.py` | 350 | Console Pi - Che do cam thang thiet bi (iLO / iDRAC / switch quan ly). |
| `network.py` | 1741 | Console Pi - Quan ly WiFi / AP / Bluetooth |
| `remote.py` | 617 | Console Pi - Truy cap tu xa qua Cloudflare Tunnel (mac dinh) hoac Tailscale |

## `consolesystem/features/power`

| File | Dong | Vai tro |
|---|---:|---|
| `entertainment.py` | 80 | Console Pi - Tab Giai tri (YouTube, TikTok...) luc ranh giua gio lam viec |
| `power.py` | 76 | Console Pi - Tab rieng: Tắt máy / Khởi động lại |

## `consolesystem/features/settings`

| File | Dong | Vai tro |
|---|---:|---|
| `settings.py` | 578 | Console Pi - Tab Cai dat (yeu cau so 3: nut xoay man hinh) |

## `consolesystem/features/software_deploy`

| File | Dong | Vai tro |
|---|---:|---|
| `tk_trang.py` | 1047 | Trien khai phan mem - GIAO DIEN. Cac tab: Tai nguyen / Kho trung tam (dung chung voi Deployment OS, chi bo He dieu hanh / |

## `consolesystem/features/terminal`

| File | Dong | Vai tro |
|---|---:|---|
| `commands.py` | 486 | Console Pi - Thu vien lenh (yeu cau so 6) |
| `phien.py` | 481 | Console System - PHIEN KET NOI kieu MobaXterm (27/09/2026, anh Thoai: "lam lai |
| `soanlenh.py` | 134 | Console Pi - Cac khoi dung chung quanh khung terminal (Terminal / SSH / |
| `ssh.py` | 248 | Console Pi - Tab SSH |
| `terminal.py` | 198 | Console Pi - Terminal local (yeu cau so 5) va SSH tuong tac (mot phan yeu cau 7) |

## `consolesystem/features/uem`

| File | Dong | Vai tro |
|---|---:|---|
| `uem_agent.py` | 670 | Quan ly may tram - AGENT v2 cho Windows (mo phong agent cua OpenUEM; khac cach lam: dich vu C# bien dich tai cho + HTTPS mTLS thay cho Go + NATS). |
| `uem_agent_cs.py` | 29 | Ma nguon C# cua AGENT Console System (dich vu Windows). KHONG co file .exe san: ma nay duoc BIEN DICH NGAY TREN MAY WINDOWS luc cai |
| `uem_agent_goi.py` | 322 | Quan ly may tram - AGENT: tao FILE CAI (MSI hoac script PowerShell) co san dia chi Console System + ma ghi danh. |
| `uem_agent_trang.py` | 391 | Quan ly may tram - AGENT: cac duong HTTPS (mTLS) cho agent, tab Agent cua may va muc Quan tri, Agent. |
| `uem_baocao.py` | 173 | Quan ly may tram - THU THAP BAO CAO may (tuong duong "agent report" cua OpenUEM, nhung khong can agent). |
| `uem_buoc.py` | 365 | Quan ly may tram - CAC LOAI TAC VU (task) cua Profile, mo phong cac task Windows cua OpenUEM |
| `uem_dulieu.py` | 71 | Quan ly may tram (UEM) - lop du lieu. Mo phong cac chuc nang cua OpenUEM (open-uem, Apache 2.0): kiem ke, bao mat, |
| `uem_ketnoi.py` | 46 | Quan ly may tram - DIEM KET NOI DUY NHAT toi 1 may Windows. Moi noi can chay PowerShell tren may goi ket_noi(m): |
| `uem_pki.py` | 375 | Quan ly may tram - HA TANG KHOA CONG KHAI (PKI) cho agent, de agent noi chuyen bang mTLS nhu agent cua OpenUEM: |
| `uem_profiles.py` | 305 | Quan ly may tram - PROFILES (mo phong Profiles cua OpenUEM: openuem-console .../profiles.go + tasks.go). |
| `uem_trang.py` | 531 | Quan ly may tram (UEM) - GIAO DIEN CHINH: khung, Tong quan (Dashboard), Danh sach may, Chi tiet may (cac tab). |
| `uem_trang_b.py` | 1254 | Quan ly may tram (UEM) - GIAO DIEN PHAN 2: Phan mem, Bao mat, Trien khai (WinGet), Profiles, Bao cao, Quan tri, Chua ho tro, |
| `uem_trienkhai.py` | 96 | Quan ly may tram - TRIEN KHAI WinGet hang loat (mo phong menu Deploy cua OpenUEM: DeployInstall / DeployUninstall / |
| `uem_vnc.py` | 560 | Quan ly may tram - DIEU KHIEN TU XA bang VNC ngay trong trinh duyet (noVNC), mo phong "Remote assistance" cua OpenUEM. |
| `uem_winget.py` | 139 | Danh muc goi WinGet de TIM PHAN MEM (giong OpenUEM: openuem-console .../software_package.go DownloadWingetDB + UpdateWingetApps): |

## `consolesystem/features/updates`

| File | Dong | Vai tro |
|---|---:|---|
| `capnhat_ui.py` | 313 | Tab CAP NHAT (C3/C4/C5): trang thai + nut Kiem tra ngay, thong tin ban moi, xac nhan (mien tru + go chu), tien do truc tiep, ha cap, lich su, |
| `thuc_te.py` | 152 | Noi bo nang cap voi HE THONG THAT: kho trung tam, systemd, nginx, sao luu/khoi phuc, kiem suc khoe. Moi ham la mot HOOK cua MoiNangCap |

## `consolesystem/integrations`

| File | Dong | Vai tro |
|---|---:|---|
| `cloudflare.py` | 28 | Cloudflare Tunnel: trang thai (da cai, co token, dang chay) - tach tu remote.py o B3 de layout/web khong phai import tinh nang remote. |
| `kho_capnhat.py` | 85 | Ket noi toi kho trung tam cho viec CAP NHAT (C3/C4): hoi danh muc, tai goi (tai tiep bang Range), lay khoa goi, bao ket qua. |
| `tk_dongco.py` | 820 | Trien khai phan mem - DONG CO CHAY (WinRM) + BO LAP LICH. |

## `consolesystem/web`

| File | Dong | Vai tro |
|---|---:|---|
| `auth.py` | 394 | Console Pi - Dang nhap bang tai khoan Linux cua chinh may (qua PAM) |
| `css_tk.py` | 5 | CSS dung chung cua cac trang Trien khai phan mem va Quan ly may tram (tach tu tk_trang.py o B3 de uem khong phai import software_deploy). |
| `docs.py` | 53 | Console System - trang "Tai lieu" tren may. |
| `gioithieu.py` | 118 | Console System - nhan dien thuong hieu zTieuYeuz + phan "Gioi thieu". |
| `health.py` | 223 | Console Pi - Suc khoe he thong va nut nguon. |
| `home.py` | 807 | Console Pi - Trang Tong quan (yeu cau so 2 va 4) |
| `layout.py` | 1004 | Console Pi - Khung giao dien dung chung (thanh dieu huong trai + noi dung phai) |
| `ph_icons.py` | 29 | Icon Phosphor (MIT, https://phosphoricons.com) dang "regular", nhung san de khong can Internet. |
