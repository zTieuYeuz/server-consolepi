# Phan C - C0 (khoa ky) + C1 (goi .cspkg, danh muc) (25/10/2026)

Ma: `src/consolesystem/core/capnhat/{khoa,goi,danhmuc}.py` (chi dung thu vien chuan + `cryptography`, khong flask). Cong cu: `tools/tao-khoa-ky.py`, `tools/phat-hanh-ky.py`, `tools/kiem-goi.py`.
Test: `tests/test_capnhat.py` (45 test, gom ma tran tan cong).

## Khoa (C0)
- Ed25519; 3 VAI TRO tach rieng: **goc** (cat ngoai tuyen, chi ky "tai lieu tin cay"), **phat-hanh** (ky goi + danh muc), **lenh-khoa** (ky lenh khoa/mo khoa, C6).
- Khoa rieng luu `<vai_tro>.khoa-rieng.json` (0600), ma hoa **scrypt (N=2^15) + AES-256-GCM**, AAD gan vai tro; khong ghi de khoa da co.
- Mat khau: bien moi truong `CS_KHOA_MAT_KHAU_<VAI_TRO>` / `CS_KHOA_MAT_KHAU` hoac o nhap an; KHONG qua tham so dong lenh.
- May khach chi giu **khoa cong khai goc**. Tai lieu tin cay (khoa goc ky) liet ke khoa phat-hanh/lenh-khoa con hieu luc: co **so_hieu chi tang**, **het han**, khoang hieu luc tung khoa -> thay khoa khong phai cai lai may.

## Goi (C1)
`MAGIC | dau (JSON chuan, da ky Ed25519) | chu ky | khoi AES-256-GCM 1 MiB` ; tai trong = tar.gz xac dinh cua `releases/<ban>/`. Nonce = tien to(8)+chi so khoi, AAD = sha256(dau)+chi so+co khoi cuoi.
Manifest: phien ban, so_phat_hanh, kien truc, kenh, ban_truoc_bat_buoc, ghi chu, can khoi dong lai, migration, ban_toi_thieu_ha_cap, sha256 TUNG FILE.
Thu tu kiem: chu ky dau -> dieu kien cai (kien truc, kenh, so_phat_hanh CHI TANG, ban truoc bat buoc = TUAN TU, khong nhay cap; ha cap chi khi duoc phep) -> giai ma (tag tung khoi)
-> sha256 tai trong -> giai nen an toan (ten, khong link/thiet bi, quyen chuan hoa, tran dung luong) -> sha256 tung file = manifest, khong thieu/thua.
Danh muc phien ban ky boi khoa phat-hanh: **het han ngan** (chong dong bang), **so_hieu khong lui**, khong tuong lai, dung kenh; `ban_ke_tiep` chi tra ban len tuan tu.

## Da thu (tat ca bi CHAN): sua 1 byte o magic/dau/chu ky/khoi dau-giua-cuoi; cat cut; du lieu thua; doi thu tu khoi; ghep khoi tu goi khac; sai khoa goi; chu ky cua khoa la / khoa lenh-khoa;
phat lai ban cu; nhay cap; sai kien truc/kenh; ten tar nguy hiem; link/thiet bi; file la ngoai manifest (ke ca khi co khoa goi + khoa ky); thieu file; sai ma bam; setuid; danh muc het han/tuong lai/lui/sai kenh/sai khoa.
Hieu nang: goi 168 MB dong goi 6.9 s, kiem+giai ma+giai nen 1.8 s, RSS dinh 64 MB (streaming).

## CHUA lam (can anh quyet / giai doan sau)
- **Chua tao KHOA THAT.** Can anh dat mat khau (>=12 ky tu) cho tung khoa va chon noi cat: may build (ma hoa) + thu muc Drive rieng (khong share) + ban in ngoai tuyen cho khoa goc.
- Khoa giai ma goi RIENG TUNG MAY (kho cap luc dang ky) va "boc khoa goi" theo may: C2 (kho).
- C2 kho (repo kho-console-pi, may .34), C3 may khach (chuong, tab), C4 bo nang cap, C5 ha cap, C6 chong chinh sua/khoa, C7 thu toan dien.
