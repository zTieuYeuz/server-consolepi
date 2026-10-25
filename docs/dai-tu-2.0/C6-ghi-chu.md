# C6 - chong chinh sua + khoa/mo khoa ban tu dong + dieu khoan (25/10/2026)

## Chong chinh sua (`core/capnhat/nguyenven.py`)
- Khi cai goi, giu lai phan dau goi (manifest co bang bam TUNG FILE + chu ky Ed25519) trong `updates/chu-ky/<ban>.json`.
- `kiem()`: xac minh lai chu ky bang khoa tin cay (goc nhung trong ma -> tai lieu tin cay -> khoa phat-hanh), roi bam lai `releases/<ban>` so voi manifest.
  Ket qua: `ok` | `chua-ky` (cai tay/dev, khong phai loi) | `lech` | `khong-xac-minh` (tai lieu tin cay het han nhung bam van khop).
- Tac dung: NANG CAP bi chan khi `lech` (ha cap van duoc - la duong thoat); kiem moi 6 gio + khi bam "Kiem tra ngay"; the "Chong chinh sua" tren tab Cap nhat; bao kho `lech-ma-bam` dung MOT lan -> kho ghi vao danh sach "May nghi ngo".
- Thu: sua/xoa/them file, sua ca file lan RELEASE.json (kiem cu `kiem_ban` bi lua, kiem co chu ky thi khong), sua chu ky luu, tai lieu tin cay het han.
- GIOI HAN: root sua duoc ca ma kiem tra lan xoa chu ky. Khong phai ranh gioi chong root; la phat hien thay doi + chan cap nhat len he thong khong tin cay.

## Khoa / mo khoa (`core/capnhat/khoa_lenh.py`, `tools/ky-lenh-khoa.py`, kho `capnhat.py`)
1. May bao `lech-ma-bam` -> kho liet ke trong "May nghi ngo" kem `token_bam` (16 ky tu dau sha256(token)).
2. Chu may DUYET bang cach ky lenh tren may build: `ky-lenh-khoa.py khoa --khoa DIR --token-bam HEX --so-thu-tu N --ra lenh.json` (mat khau khoa `lenh-khoa` qua bien moi truong/o nhap an), in MA MO KHOA mot lan; roi `nap-ban.py lenh lenh.json` tren kho.
3. May hoi danh muc -> nhan lenh -> kiem chu ky (khoa lenh-khoa trong tai lieu tin cay), dung may (token_bam), con han (toi da 14 ngay), `so_thu_tu` tang dan va id chua dung (chong phat lai) -> khoa:
   ma hoa CHI bi mat nho (<=64KB: khoa flask, kho-trungtam.json, samba, cf-access, khoa-may, trienkhai.khoa) bang khoa ngau nhien KS, boc KS cho khoa cong khai X25519 trong lenh roi QUEN KS; ghi truoc (blob + trang thai `dang-khoa`) roi moi xoa ban ro (mat dien giua chung -> hoan tat luc khoi dong).
4. Web chi con man hinh "May bi khoa" (HTTP 423) + o nhap ma; /healthz, /static, agent, PXE khong bi dong. Console: `console-system-mo-khoa.py mo`.
5. MA MO KHOA 160 bit = HKDF(khoa lenh-khoa rieng, id lenh): chu may TINH LAI OFFLINE (`tinh-ma`). Kho chi giu khoa cong khai P, khong suy ra duoc ma; moi lenh P moi -> ma dung MOT lan; khong co kenh mo tu xa.
- GIOI HAN: khong khoa duoc o dia/du lieu lon; ai co root + dang giu may truoc khi lenh toi van lay duoc ban ro; ngat mang thi khong nhan lenh; mat ma + khoa lenh-khoa = mat bi mat da khoa. Khoa o SSD khong dam bao xoa that (ghi de truoc khi xoa chi la no luc).

## Dieu khoan
Man hinh dong y o lan dau mo tab Cap nhat (hash noi dung; doi dieu khoan = hoi lai). Da them muc 5 (chong chinh sua) va 6 (khoa may).

## Thu
`tests/test_chongsua_khoa.py` (23 test, gom kich ban web `web_khoa_kichban.py`) + kho `tests/test_capnhat.py` (12). Chua thu khoa that tren .30 (se lam khi anh ra khoa lenh-khoa that).
