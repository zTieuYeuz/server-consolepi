# A5 - Sao luu / Khoi phuc (25/10/2026)

- `ui/saoluu.py`: tao_goi / tao_luong (tai ve dang luong) / kiem_goi / khoi_phuc / hau_khoi_phuc. Chi cho BO CUC MOI.
- Che do `cauhinh` (config, secrets, pki, data, deploy/kichban, deploy/apps/_thongtin.json, schema_version) va `toanbo` (them deploy/, storage/).
- Goi .tar.gz co manifest CUOI (san pham, dinh dang, phien ban ma, schema, tung file + byte + sha256). Kiem het truoc khi dung toi du lieu;
  chan ten nguy hiem (../, tuyet doi, ngoai pham vi), link, file la, goi tu du lieu moi hon ma.
- Khoi phuc: tu sao luu trang thai hien tai thanh goi cung dinh dang (backups/truoc-khoiphuc-*), giai ra thu muc tam, doi nguyen tu,
  loi giua chung thi tra ve nhu cu. Thu muc tam (data/trienkhai/cache) khong nam trong goi nhung duoc giu lai.
- Giao dien: Cai dat > Sao luu & Khoi phuc (2 nut tai ve, tai len -> kiem -> xac nhan -> khoi phuc -> tu khoi dong lai dich vu).
  Lenh: `scripts/saoluu.py tao [--toan-bo] | kiem FILE | khoi-phuc FILE`.
- Thu that tren .30 (goi cauhinh 31 file/7MB): chuyen di toan bo config/secrets/pki/data/kichban -> khoi phuc -> `diff -r` GIONG HET,
  96 trang giong truoc, agent .33 tu noi lai sau ~75 giay, Samba/nginx dong bo. Bai hoc tu lan thu do: khi du lieu trong, dashboard tu
  sinh CA moi (uem_pki.nap_lai_neu_doi) va nginx nap CA moi -> khoi phuc phai nap lai nginx (da co trong hau_khoi_phuc).
  Mat luon schema_version.json van khoi phuc duoc (da sua sau lan thu 1 that bai).
CHUA: sao luu `toanbo` tren du lieu that nhieu GB (chi test don vi); khoi phuc qua trinh duyet that tren .30 (da thu bang CLI + Flask test client);
  may chua o bo cuc moi dung the cu (baotri.py).
