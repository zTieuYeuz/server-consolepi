# Bao cao kiem thu Console System 2.0.0 (25/10/2026) - CHUA phat hanh

Ban dung de anh Thoai tu test tay. Chua len Drive/docs/GitHub.

## Ban dung (tren may build)
- ISO amd64: `/build/console-system/live-image-amd64.hybrid.iso` (sha256 1ebf7def...a49b296), 1.424.670.720 byte. i386: BO (khong dung 2.0).
- Anh Pi: `/build/pi/ConsoleSystem-2.0.0-raspberrypi.img.xz` (sha256 1b041946...3176baf), `xz -t` OK.
- Nguon: nhanh `v2` repo `/root/repos-tu-pi/consolepi-toolkit` (VERSION 2.0.0).

## Ket qua
| Hang muc | Ket qua |
|---|---|
| pytest (hop dong route 333, 96 trang, golden 48 file, 75 hanh vi, cap nhat, sao luu, kien truc...) | 284 dat, 61 bo qua |
| Bo kiem cu thu-uem 301 / thu-trienkhai 80 / thu-nhat-ky 33 | 301/301, 80/80, 33/33 |
| Test trinh duyet (CDP): ban phim ao 24, nhat ky UI 48, nhom phien 13 | 24/24, 48/48, 13/13 |
| ruff, import-linter, Python 3.11 cu phap, bandit | sach / dat (tools/ci.sh XANH, phu core 77%) |
| ISO cai that trong may ao UEFI + bang kiem `kiem-tra-may-da-cai.sh` | **62/62 dat** (gom: dich vu moi ten, PKI+mTLS 8443 sinh luc khoi dong dau, khong CA/khoa trong ISO, MSI/script agent, driver, phuc hoi cap nhat da bat) |
| Cap nhat that TRONG may ao cai tu ISO (kenh thu-nghiem qua LAN, khoa that) 2.0.0 -> 2.0.1 | XONG (chu ky, giai ma, 390 file, migration, doi ban, khoi dong lai, suc khoe) |
| Anh Pi: giai nen + gan loop: version 2.0.0, dich vu moi ten da bat, bi mat/PKI rong, khong khoa SSH, tools co quyen chay | dat. CHUA khoi dong tren the that |
| Pi .14 (that) chuyen len 2.0.0 (bo cuc moi + doi ten dich vu), khong reboot | dat (trang 200, dich vu chay); co sao luu + duong lui |
| .30: nang cap/ha cap that voi khoa that + doi ten dich vu | dat |

## Loi that tim ra khi kiem thu va DA SUA
1. Script dung cay ISO nap `phathanh.py` sai cach sau khi tach goi (B2) -> build chet.
2. `dung-anh-pi.sh` mac dinh lay cay MA CU `/root/consolepi-toolkit` (1.9.5) -> anh Pi dung tu ma cu; nay tro vao repo, xoa bi mat/PKI cua bo cuc moi.
3. `tools/cai-agent-tls.sh`, `cai-vnc.sh` (644 trong repo) khong chay duoc trong ban phat hanh -> PKI/mTLS 8443 khong tao luc khoi dong dau tren ISO. Nay ban phat hanh dat quyen chay cho scripts/ va tools/cai-*.sh (+test).
4. Dich vu `console-system-nang-cap-phuc-hoi` (phuc hoi sau mat dien) TAT tren may cai tu ISO; nay bat trong hook + bang kiem.
5. Chuyen ten dich vu tren may cu: lan dau con dich vu bi dung khong chay lai -> sua + test.
6. Bang kiem ISO dung duong dan cu (/var/lib/console-pi) -> cap nhat theo bo cuc 2.0.

## CHUA kiem / han che
- Anh Pi chua boot tren the/Pi that (chi kiem noi dung + build trong chroot). Lan khoi dong dau tren Pi chay lai install.sh de sinh bi mat.
- ISO chua thu BIOS Legacy / NVMe / RAID tren may that; chua thu USB that. Cai Windows qua PXE chua thu lai that (golden + test xac nhan dau ra khong doi).
- Hai test CDP terminal (chuot, focus) can terminal song tren Pi that - chua chay.
- Trang `/cap-nhat` voi kenh "on-dinh": kho tra "chua co danh muc" cho toi khi anh phat hanh (dung thiet ke).
- 3 may ao test da dang ky vao KHO THAT trong luc thu (ten may `console-system`): can anh xoa tren trang Ket noi Console System cua kho (token bat dau 2526fc, 900b2f, 2bb9ea).
