# B1b - du lieu lon sang SQLite (25/10/2026)

- `consolesystem/core/sqlite.py`: console.db (WAL, synchronous=NORMAL, busy_timeout 60s), ket noi theo luong, `lam_moi()` (sau khoi phuc), `snapshot()` (API backup).
  File hong -> cach ly `.hong-*`, canh bao, tao moi.
- `consolesystem/core/store_sqlite.py`: KhoSqlite cung giao dien doc/ghi/sua nhu KhoJson. CHI GHI PHAN DOI: list co id duy nhat -> khoa theo id; list khong id -> theo vi tri;
  dict -> khoa cap 1. Them cuoi/sua/xoa 1 muc = 1 dong (test: sua 1 may trong 300 = 1 dong; 120 thao tac ngau nhien cho ket qua GIONG HET KhoJson).
  `sua()` la MOT giao dich (BEGIN IMMEDIATE) -> an toan nhieu tien trinh. Nhap JSON cu tu dong lan dau (kiem lai, doi ten `.da-chuyen-*`, khong xoa), re-check trong giao dich.
- 5 kho chuyen: may, chay, uem_tac_vu, uem_trien_khai, uem_profile_tt (tk_dulieu.KhoLon). Cac kho nho/cau hinh giu JSON. `CS_KHO_JSON=1` ep dung JSON.
- Hoan tac / chan doan: `scripts/kho.py ds | xuat TEN | xuat-het THU_MUC` (roi dat JSON vao data/trienkhai/ va CS_KHO_JSON=1).
- A5: goi sao luu dung ban chup nhat quan cua DB (khong chep -wal/-shm/-journal); khoi phuc goi `lam_moi()`. Sao luu tolerate tep tam bien mat (loi that tim ra bang test do chay song song).
- A3: chuyen bo cuc tu choi khi console.db-wal chua gop (phai dung dich vu).
Thu that tren .30: nhap may.json/chay.json/uem_tac_vu.json (file goc giu `.da-chuyen-*`), 96 trang giong het, agent .33 ve binh thuong,
goi sao luu 32 file co console.db, pha (xoa het may) -> khoi phuc CLI -> kho giong het.
CHUA: do toc do tren 300 may that; kho nho van JSON; UI hien canh_bao(); SQLite cho nhat ky/lich su cai dat (lichsu.py) chua chuyen.
